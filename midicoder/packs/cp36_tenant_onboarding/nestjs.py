# coding: utf-8
"""
NestJS Emitter cho CP36: Tenant Onboarding & Subscription.

Module này render Jinja2 templates để sinh onboarding & subscription code
cho NestJS stack.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp36_tenant_onboarding.models import (
    OnboardingIR,
    SubscriptionPlan,
    BillingCycle,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "TenantOnboardingNestJSEmitter",
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


class TenantOnboardingNestJSEmitter:
    """Emitter cho NestJS stack — CP36 Tenant Onboarding & Subscription.

    Render templates từ `stacks/nestjs/cp36_tenant_onboarding/`
    để sinh tenant onboarding code.

    Ví dụ:
        >>> emitter = TenantOnboardingNestJSEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(onboarding_ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            FileNotFoundError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp36_tenant_onboarding"

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
        config: OnboardingIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit tenant onboarding code cho NestJS.

        Sinh 9 files:
        - registration.entity.ts
        - subscription.entity.ts
        - registration-dto.ts
        - subscription-dto.ts
        - onboarding.module.ts
        - registration.service.ts
        - subscription.service.ts
        - registration.controller.ts
        - subscription.controller.ts

        Args:
            config: OnboardingIR chứa cấu hình onboarding.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(config)

        files: list[GeneratedFile] = []

        # registration.entity.ts
        if self._template_exists("registration.entity.ts.jinja2"):
            content = self._render("registration.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/entities/registration.entity.ts",
                content=content,
            ))

        # subscription.entity.ts
        if self._template_exists("subscription.entity.ts.jinja2"):
            content = self._render("subscription.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/entities/subscription.entity.ts",
                content=content,
            ))

        # registration-dto.ts
        if self._template_exists("registration-dto.ts.jinja2"):
            content = self._render("registration-dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/dtos/registration-dto.ts",
                content=content,
            ))

        # subscription-dto.ts
        if self._template_exists("subscription-dto.ts.jinja2"):
            content = self._render("subscription-dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/dtos/subscription-dto.ts",
                content=content,
            ))

        # onboarding.module.ts
        if self._template_exists("onboarding.module.ts.jinja2"):
            content = self._render("onboarding.module.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/onboarding.module.ts",
                content=content,
            ))

        # registration.service.ts
        if self._template_exists("registration.service.ts.jinja2"):
            content = self._render("registration.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/services/registration.service.ts",
                content=content,
            ))

        # subscription.service.ts
        if self._template_exists("subscription.service.ts.jinja2"):
            content = self._render("subscription.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/services/subscription.service.ts",
                content=content,
            ))

        # registration.controller.ts
        if self._template_exists("registration.controller.ts.jinja2"):
            content = self._render("registration.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/controllers/registration.controller.ts",
                content=content,
            ))

        # subscription.controller.ts
        if self._template_exists("subscription.controller.ts.jinja2"):
            content = self._render("subscription.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/onboarding/controllers/subscription.controller.ts",
                content=content,
            ))

        return files

    def _build_context(self, config: OnboardingIR) -> dict[str, Any]:
        """Xây dựng template context từ OnboardingIR.

        Args:
            config: OnboardingIR input.

        Returns:
            Dict context cho Jinja2.
        """
        plans_list = [
            {
                "plan": pc.plan.value,
                "monthly_price": str(pc.monthly_price),
                "yearly_price": str(pc.yearly_price),
                "features": pc.features,
                "max_users": pc.max_users,
                "max_storage_gb": pc.max_storage_gb,
            }
            for pc in config.plans
        ]

        return {
            "plans": plans_list,
            "default_trial_days": config.default_trial_days,
            "require_admin_approval": config.require_admin_approval,
            "auto_start_trial": config.auto_start_trial,
            "verification_token_expiry_hours": config.verification_token_expiry_hours,
            "plan_count": len(config.plans),
            "subscription_plans": [
                SubscriptionPlan.FREE.value,
                SubscriptionPlan.STARTER.value,
                SubscriptionPlan.PROFESSIONAL.value,
                SubscriptionPlan.ENTERPRISE.value,
            ],
            "registration_statuses": [
                "pending",
                "verified",
                "rejected",
                "cancelled",
            ],
            "subscription_statuses": [
                "trial",
                "active",
                "past_due",
                "cancelled",
                "expired",
            ],
            "billing_cycles": [
                BillingCycle.MONTHLY.value,
                BillingCycle.YEARLY.value,
            ],
        }

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
                ErrorCode.CP36_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template not found: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP36_RENDER_FAILED,
                template=template_name,
                reason=f"Failed to render template {template_name}: {e}",
            )
