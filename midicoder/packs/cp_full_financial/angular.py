"""
Angular Emitter cho CP33: Financial Engine.

Module này render Jinja2 templates để sinh financial UI components
cho Angular stack.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FinancialAngularEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class FinancialAngularEmitter:
    """Emitter cho Angular stack — CP33 Financial Engine.

    Render templates từ `stacks/angular/cp_full_financial/`
    để sinh financial UI components.

    Ví dụ:
        >>> emitter = FinancialAngularEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> files = emitter.emit(financial_config, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_financial"

        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self.template_dir}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        financial_config: dict[str, Any],
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit financial UI components cho Angular.

        Args:
            financial_config: Cấu hình tài chính với keys: currencies, accounts, base_currency.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = {
            "currencies": financial_config.get("currencies", []),
            "accounts": financial_config.get("accounts", []),
            "base_currency": financial_config.get("base_currency", "USD"),
            "currency_count": len(financial_config.get("currencies", [])),
            "account_count": len(financial_config.get("accounts", [])),
        }

        files: list[GeneratedFile] = []

        # ledger-dashboard.component.ts
        if self._template_exists("ledger-dashboard.component.ts.jinja2"):
            content = self._render("ledger-dashboard.component.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/app/financial/components/ledger-dashboard.component.ts",
                content=content,
            ))

        # transaction-detail.component.ts
        if self._template_exists("transaction-detail.component.ts.jinja2"):
            content = self._render("transaction-detail.component.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/app/financial/components/transaction-detail.component.ts",
                content=content,
            ))

        return files

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một template.

        Args:
            template_name: Tên template file.
            context: Template context.

        Returns:
            Rendered string.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render lỗi.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F21_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template not found: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F21_RENDER_FAILED,
                template=template_name,
                reason=f"Failed to render template {template_name}: {e}",
            )
