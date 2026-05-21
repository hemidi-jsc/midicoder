# coding: utf-8
"""
React Emitter cho CP36: Tenant Onboarding & Subscription.

Module này render Jinja2 templates để sinh onboarding UI components
cho React stack, bao gồm:
- RegistrationForm: Form đăng ký tenant mới
- SubscriptionPanel: Bảng quản lý subscription
- TrialBanner: Banner đếm ngược trial
- useOnboarding: Custom React hook

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp36_tenant_onboarding.models import (
    OnboardingIR,
    PlanConfig,
    SubscriptionPlan,
    BillingCycle,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "TenantOnboardingReactEmitter",
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


class TenantOnboardingReactEmitter:
    """Emitter cho React stack — CP36 Tenant Onboarding & Subscription.

    Render templates từ `stacks/react/core/cp36_tenant_onboarding/`
    để sinh onboarding UI components.

    Ví dụ:
        >>> emitter = TenantOnboardingReactEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = OnboardingIR(plans=[...])
        >>> files = emitter.emit(ir)
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/core/`.

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại.
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

    def emit(self, config: OnboardingIR) -> dict[str, str]:
        """Emit onboarding UI components cho React.

        Args:
            config: OnboardingIR chứa plans, trial settings, và policy.

        Returns:
            Dict mapping đường dẫn file đến nội dung.
        """
        # Xây dựng context từ OnboardingIR
        plans_list = []
        for pc in config.plans:
            plans_list.append({
                "plan": pc.plan.value,
                "label": pc.plan.value.capitalize(),
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

        # RegistrationForm.tsx
        if self._template_exists("RegistrationForm.tsx.jinja2"):
            content = self._render("RegistrationForm.tsx.jinja2", context)
            result["src/onboarding/components/RegistrationForm.tsx"] = content

        # SubscriptionPanel.tsx
        if self._template_exists("SubscriptionPanel.tsx.jinja2"):
            content = self._render("SubscriptionPanel.tsx.jinja2", context)
            result["src/onboarding/components/SubscriptionPanel.tsx"] = content

        # TrialBanner.tsx
        if self._template_exists("TrialBanner.tsx.jinja2"):
            content = self._render("TrialBanner.tsx.jinja2", context)
            result["src/onboarding/components/TrialBanner.tsx"] = content

        # useOnboarding.ts
        if self._template_exists("useOnboarding.ts.jinja2"):
            content = self._render("useOnboarding.ts.jinja2", context)
            result["src/onboarding/hooks/useOnboarding.ts"] = content

        return result

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
