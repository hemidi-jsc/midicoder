"""
Template Engine Module.

Module này cung cấp:
- TemplateRenderer: Render templates với variable interpolation, nested vars, filters
- TemplateValidator: Validate template syntax và kiểm tra required variables
- RenderedTemplate: Result object sau khi render

Support:
- Simple variables: {{name}}
- Nested variables: {{user.name}}, {{order.items.0.price}}
- Filters: {{price|currency}}, {{name|uppercase}}, {{date|format:'%Y-%m-%d'}}

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from midicoder.emitters.core.notification.models import NotificationTemplate


# ============================================================================
# Built-in Filters
# ============================================================================

# Filter registry: filter_name -> callable
_FILTER_REGISTRY: dict[str, Any] = {}


def _register_filter(name: str, func: Any) -> None:
    """Đăng ký filter vào registry."""
    _FILTER_REGISTRY[name] = func


def _filter_currency(value: Any) -> str:
    """Filter currency: định dạng số thành tiền VND."""
    try:
        num = float(str(value).replace(",", ""))
        return f"{num:,.0f} VND"
    except (ValueError, TypeError):
        return str(value)


def _filter_uppercase(value: Any) -> str:
    """Filter uppercase: chuyển string thành chữ hoa."""
    return str(value).upper()


def _filter_lowercase(value: Any) -> str:
    """Filter lowercase: chuyển string thành chữ thường."""
    return str(value).lower()


def _filter_format(value: Any, format_str: str) -> str:
    """Filter format: định dạng datetime theo format string."""
    if isinstance(value, datetime):
        return value.strftime(format_str)
    return str(value)


def _filter_default(value: Any, default_value: str) -> str:
    """Filter default: trả về default_value nếu value rỗng."""
    if not value or (isinstance(value, str) and not value.strip()):
        return default_value
    return str(value)


# Đăng ký built-in filters
_register_filter("currency", _filter_currency)
_register_filter("uppercase", _filter_uppercase)
_register_filter("lowercase", _filter_lowercase)
_register_filter("format", _filter_format)
_register_filter("default", _filter_default)


# ============================================================================
# RenderedTemplate Model
# ============================================================================


@dataclass
class RenderedTemplate:
    """
    Kết quả sau khi render template.

    Attributes:
        template_id: ID của template đã render
        subject: Subject line đã render
        body_html: HTML body đã render
        body_text: Plain text body đã render
    """

    template_id: str
    subject: str
    body_html: str
    body_text: str

    def to_dict(self) -> dict[str, str]:
        """Chuyển RenderedTemplate sang dictionary."""
        return {
            "template_id": self.template_id,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
        }


# ============================================================================
# TemplateRenderer
# ============================================================================

# Pattern cho variable: {{name}}, {{user.name}}, {{price|currency}}, {{date|format:'%Y-%m-%d'}}
_VARIABLE_PATTERN = re.compile(
    r"\{\{([^}]+)\}\}"  # {{...}}
)


class TemplateRenderer:
    """
    Engine render templates với variable interpolation và filter support.

    Support:
    - Simple variables: {{name}}
    - Nested variables: {{user.name}}, {{order.items.0.price}}
    - Filters: {{price|currency}}, {{name|uppercase}}
    - Filter với args: {{date|format:'%Y-%m-%d'}}, {{name|default:'N/A'}}

    Example:
        >>> renderer = TemplateRenderer()
        >>> result = renderer.render_string("Xin chào {{name|uppercase}}!", {"name": "minh"})
        >>> print(result)
        Xin chào MINH!
    """

    def render_string(self, template: str, data: dict[str, Any]) -> str:
        """
        Render string template với variable interpolation.

        Thay thế các {{variable}} trong template bằng values từ data dict.
        Support nested variables và filters.

        Args:
            template: Template string chứa {{variable}} placeholders
            data: Dictionary chứa variable values

        Returns:
            Template string đã render
        """
        def _replace_var(match: re.Match) -> str:
            """Thay thế một variable match bằng giá trị tương ứng."""
            expression = match.group(1).strip()

            # Parse filter (nếu có)
            filter_name = None
            filter_arg = None
            var_name = expression

            if "|" in expression:
                parts = expression.split("|", 1)
                var_name = parts[0].strip()
                filter_expr = parts[1].strip()

                # Parse filter args: format:'%Y-%m-%d' hoặc default:'N/A'
                if ":" in filter_expr:
                    filter_parts = filter_expr.split(":", 1)
                    filter_name = filter_parts[0].strip()
                    filter_arg = filter_parts[1].strip().strip("'\"")
                else:
                    filter_name = filter_expr

            # Resolve variable value từ data (support nested)
            value = self._resolve_variable(var_name, data)

            # Nếu không resolve được, giữ nguyên template
            if value is _UNRESOLVED:
                return match.group(0)

            # Apply filter (nếu có)
            if filter_name and filter_name in _FILTER_REGISTRY:
                try:
                    if filter_arg is not None:
                        value = _FILTER_REGISTRY[filter_name](value, filter_arg)
                    else:
                        value = _FILTER_REGISTRY[filter_name](value)
                except (ValueError, TypeError, KeyError):
                    # Filter fail -> giữ nguyên template
                    return match.group(0)
            elif filter_name:
                # Filter không tồn tại trong registry -> giữ nguyên
                return match.group(0)

            return str(value)

        return _VARIABLE_PATTERN.sub(_replace_var, template)

    def render(
        self,
        template: NotificationTemplate,
        data: dict[str, Any],
    ) -> RenderedTemplate:
        """
        Render NotificationTemplate hoàn chỉnh.

        Render subject, body_html, body_text với variable values.

        Args:
            template: NotificationTemplate cần render
            data: Dictionary chứa variable values

        Returns:
            RenderedTemplate với subject, body_html, body_text đã render
        """
        return RenderedTemplate(
            template_id=template.template_id,
            subject=self.render_string(template.subject, data),
            body_html=self.render_string(template.body_html, data),
            body_text=self.render_string(template.body_text, data),
        )

    def _resolve_variable(
        self,
        var_name: str,
        data: dict[str, Any],
    ) -> Any:
        """
        Resolve variable name thành value, support nested access.

        Support:
        - Simple: "name" -> data["name"]
        - Nested: "user.name" -> data["user"]["name"]
        - Index: "items.0.name" -> data["items"][0]["name"]

        Args:
            var_name: Tên variable (có thể nested)
            data: Data dictionary

        Returns:
            Value của variable, hoặc _UNRESOLVED nếu không tìm thấy
        """
        parts = var_name.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return _UNRESOLVED
            elif isinstance(current, (list, tuple)):
                # Support index access: "items.0.name"
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    return _UNRESOLVED
            else:
                return _UNRESOLVED

        return current


# Sentinel value cho unresolved variables
class _UnresolvedSentinel:
    """Sentinel object đánh dấu variable không thể resolve."""
    __slots__ = ()

    def __repr__(self) -> str:
        return "<UNRESOLVED>"


_UNRESOLVED = _UnresolvedSentinel()


# ============================================================================
# TemplateValidator
# ============================================================================

# Pattern để extract variables (cả có và không có filter)
_EXTRACT_VAR_PATTERN = re.compile(r"\{\{([^}|]+)(?:\|[^}]*)?\}\}")


class TemplateValidator:
    """
    Validator cho notification templates.

    Cung cấp:
    - validate_syntax(): Kiểm tra syntax errors (unclosed variables, ...)
    - extract_variables(): Extract danh sách variables từ template
    - validate_payload(): Kiểm tra payload có đầy đủ required variables

    Example:
        >>> validator = TemplateValidator()
        >>> errors = validator.validate_syntax("Xin chào {{name}")
        >>> print(errors)
        ['Variable không đóng: {{name']
    """

    def validate_syntax(self, template: str) -> list[str]:
        """
        Validate template syntax.

        Kiểm tra các lỗi:
        - Variable không đóng ({{name thay vì {{name}})
        - Pattern không hợp lệ

        Args:
            template: Template string cần validate

        Returns:
            List of error messages (empty = valid)
        """
        errors: list[str] = []

        # Kiểm tra unclosed variables: có {{ nhưng không có }}, tương ứng
        open_count = template.count("{{")
        close_count = template.count("}}")

        if open_count != close_count:
            errors.append(
                f"Syntax error: Số lượng {{ {{ không khớp }} }} "
                f"(mở: {open_count}, đóng: {close_count}). "
                "Kiểm tra biến không đóng (unclosed variable)."
            )

        # Kiểm tra các unclosed patterns cụ thể
        unclosed_pattern = re.compile(r"\{\{[^}]*$")
        if unclosed_pattern.search(template):
            # Tìm variable cụ thể bị unclosed
            match = unclosed_pattern.search(template)
            if match:
                errors.append(
                    f"Variable không đóng (unclosed): '{match.group(0)}'. "
                    f"Hãy đóng bằng }} }}"
                )

        # Kiểm tra invalid filters
        full_var_pattern = re.compile(r"\{\{([^}]+)\}\}")
        for match in full_var_pattern.finditer(template):
            expression = match.group(1).strip()
            if "|" in expression:
                parts = expression.split("|", 1)
                filter_expr = parts[1].strip()
                filter_name = filter_expr.split(":")[0].strip()

                if filter_name not in _FILTER_REGISTRY and filter_name:
                    errors.append(
                        f"Filter không hợp lệ: '{filter_name}'. "
                        f"Filters hỗ trợ: {', '.join(sorted(_FILTER_REGISTRY.keys()))}"
                    )

        return errors

    def extract_variables(self, template: str) -> list[str]:
        """
        Extract danh sách variable names từ template string.

        Parse template và trả về list của variable names (loại bỏ filter part).

        Args:
            template: Template string

        Returns:
            List of variable names
        """
        variables: list[str] = []

        for match in _EXTRACT_VAR_PATTERN.finditer(template):
            var_expr = match.group(1).strip()
            # Loại bỏ filter part (nếu có)
            if "|" in var_expr:
                var_name = var_expr.split("|")[0].strip()
            else:
                var_name = var_expr

            if var_name and var_name not in variables:
                variables.append(var_name)

        return variables

    def validate_payload(
        self,
        template_string: str,
        payload: dict[str, Any],
        required_variables: list[str] | None = None,
    ) -> list[str]:
        """
        Validate payload có đầy đủ required variables.

        Kiểm tra xem payload dict có chứa tất cả các variables
        được yêu cầu bởi template không.

        Args:
            template_string: Template string (để extract variables)
            payload: Payload dict chứa variable values
            required_variables: List required variables (nếu None, extract từ template)

        Returns:
            List of error messages (empty = valid)
        """
        errors: list[str] = []

        # Nếu không cung cấp required_variables, extract từ template
        if required_variables is None:
            required_variables = self.extract_variables(template_string)

        # Kiểm tra mỗi required variable có trong payload
        for var_name in required_variables:
            # Support nested: check top-level key
            top_key = var_name.split(".")[0]

            if top_key not in payload:
                errors.append(
                    f"Thiếu required variable: '{var_name}'. "
                    f"Key '{top_key}' không có trong payload."
                )

        return errors


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "TemplateRenderer",
    "TemplateValidator",
    "RenderedTemplate",
    "_FILTER_REGISTRY",
    "_register_filter",
]