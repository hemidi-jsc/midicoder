# coding: utf-8
"""
Angular Emitter cho CP36: Tenant Onboarding & Subscription.

Module này render Jinja2 templates để sinh onboarding UI components
cho Angular stack.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_tenant_onboarding.models import (
    OnboardingIR,
    SubscriptionPlan,
    BillingCycle,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "TenantOnboardingAngularEmitter",
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


class TenantOnboardingAngularEmitter:
    """Emitter cho Angular stack — CP36 Tenant Onboarding & Subscription.

    Render templates từ `stacks/angular/cp_full_tenant_onboarding/`
    để sinh onboarding UI components bao gồm:
    - RegistrationFormComponent: Form đăng ký tenant mới
    - SubscriptionPanelComponent: Bảng quản lý subscription
    - TrialBannerComponent: Banner thông báo trial
    - OnboardingService: Service HTTP cho onboarding

    Ví dụ:
        >>> emitter = TenantOnboardingAngularEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = OnboardingIR(plans=[...], default_trial_days=14)
        >>> files = emitter.emit(ir)
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

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

    def emit(self, config: OnboardingIR) -> dict[str, str]:
        """Emit onboarding UI components cho Angular.

        Sinh 4 files:
        - registration-form.component.ts
        - subscription-panel.component.ts
        - trial-banner.component.ts
        - onboarding.service.ts

        Args:
            config: OnboardingIR chứa cấu hình plans, trial, approval.

        Returns:
            Dict mapping từ output path đến nội dung file.
        """
        # Xây dựng context từ OnboardingIR
        plans_list = []
        for pc in config.plans:
            plans_list.append({
                "plan": pc.plan.value,
                "label": self._plan_label(pc.plan),
                "monthly_price": str(pc.monthly_price),
                "yearly_price": str(pc.yearly_price),
                "features": pc.features,
                "max_users": pc.max_users,
                "max_storage_gb": pc.max_storage_gb,
            })

        context: dict[str, Any] = {
            "plans": plans_list,
            "plan_count": len(config.plans),
            "default_trial_days": config.default_trial_days,
            "require_admin_approval": config.require_admin_approval,
            "auto_start_trial": config.auto_start_trial,
            "verification_token_expiry_hours": config.verification_token_expiry_hours,
        }

        result: dict[str, str] = {}

        # registration-form.component.ts
        if self._template_exists("registration-form.component.ts.jinja2"):
            content = self._render("registration-form.component.ts.jinja2", context)
            result[
                "src/app/onboarding/components/registration-form.component.ts"
            ] = content

        # subscription-panel.component.ts
        if self._template_exists("subscription-panel.component.ts.jinja2"):
            content = self._render("subscription-panel.component.ts.jinja2", context)
            result[
                "src/app/onboarding/components/subscription-panel.component.ts"
            ] = content

        # trial-banner.component.ts
        if self._template_exists("trial-banner.component.ts.jinja2"):
            content = self._render("trial-banner.component.ts.jinja2", context)
            result[
                "src/app/onboarding/components/trial-banner.component.ts"
            ] = content

        # onboarding.service.ts
        if self._template_exists("onboarding.service.ts.jinja2"):
            content = self._render("onboarding.service.ts.jinja2", context)
            result[
                "src/app/onboarding/services/onboarding.service.ts"
            ] = content

        return result

    def _plan_label(self, plan: SubscriptionPlan) -> str:
        """Trả về label hiển thị cho plan.

        Args:
            plan: SubscriptionPlan enum.

        Returns:
            Label tiếng Việt.
        """
        labels = {
            SubscriptionPlan.FREE: "Miễn Phí",
            SubscriptionPlan.STARTER: "Starter",
            SubscriptionPlan.PROFESSIONAL: "Professional",
            SubscriptionPlan.ENTERPRISE: "Enterprise",
        }
        return labels.get(plan, plan.value)

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
                reason=f"Jinja2 template not found: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F14_RENDER_FAILED,
                template=template_name,
                reason=f"Failed to render template {template_name}: {e}",
            )
