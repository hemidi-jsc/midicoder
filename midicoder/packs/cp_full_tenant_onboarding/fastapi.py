"""
FastAPI Emitter cho CP36: Tenant Onboarding & Subscription.

Module này render Jinja2 templates để sinh tenant onboarding code
cho FastAPI stack, bao gồm registration, subscription, events.

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
    "TenantOnboardingFastAPIEmitter",
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


class TenantOnboardingFastAPIEmitter:
    """Emitter cho FastAPI stack — CP36 Tenant Onboarding & Subscription.

    Render templates từ `stacks/fastapi/cp_full_tenant_onboarding/`
    để sinh tenant onboarding code, bao gồm models, schemas, services,
    routers, và events.

    Ví dụ:
        >>> emitter = TenantOnboardingFastAPIEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(onboarding_config, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_tenant_onboarding"

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
        onboarding_config: dict[str, Any],
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit tenant onboarding code cho FastAPI.

        Args:
            onboarding_config: Cấu hình onboarding với keys: plans,
                default_trial_days, require_admin_approval,
                auto_start_trial, verification_token_expiry_hours.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = {
            "plans": onboarding_config.get("plans", []),
            "default_trial_days": onboarding_config.get("default_trial_days", 14),
            "require_admin_approval": onboarding_config.get("require_admin_approval", False),
            "auto_start_trial": onboarding_config.get("auto_start_trial", True),
            "verification_token_expiry_hours": onboarding_config.get("verification_token_expiry_hours", 24),
            "plan_count": len(onboarding_config.get("plans", [])),
        }

        files: list[GeneratedFile] = []

        # __init__.py
        if self._template_exists("__init__.py.jinja2"):
            content = self._render("__init__.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/__init__.py",
                content=content,
            ))

        # registration_model.py
        if self._template_exists("registration_model.py.jinja2"):
            content = self._render("registration_model.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/models/registration_model.py",
                content=content,
            ))

        # subscription_model.py
        if self._template_exists("subscription_model.py.jinja2"):
            content = self._render("subscription_model.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/models/subscription_model.py",
                content=content,
            ))

        # registration_schema.py
        if self._template_exists("registration_schema.py.jinja2"):
            content = self._render("registration_schema.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/schemas/registration_schema.py",
                content=content,
            ))

        # subscription_schema.py
        if self._template_exists("subscription_schema.py.jinja2"):
            content = self._render("subscription_schema.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/schemas/subscription_schema.py",
                content=content,
            ))

        # registration_service.py
        if self._template_exists("registration_service.py.jinja2"):
            content = self._render("registration_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/services/registration_service.py",
                content=content,
            ))

        # subscription_service.py
        if self._template_exists("subscription_service.py.jinja2"):
            content = self._render("subscription_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/services/subscription_service.py",
                content=content,
            ))

        # registration_router.py
        if self._template_exists("registration_router.py.jinja2"):
            content = self._render("registration_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/routers/registration_router.py",
                content=content,
            ))

        # subscription_router.py
        if self._template_exists("subscription_router.py.jinja2"):
            content = self._render("subscription_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/routers/subscription_router.py",
                content=content,
            ))

        # onboarding_events.py
        if self._template_exists("onboarding_events.py.jinja2"):
            content = self._render("onboarding_events.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/onboarding/events/onboarding_events.py",
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
                ErrorCode.MDC-F14_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F14_RENDER_FAILED,
                template=template_name,
                reason=f"Render template thất bại {template_name}: {e}",
            )
