# coding: utf-8
"""
Parser cho CP36 — Tenant Onboarding & Subscription.

Parse DSL dict sang OnboardingIR.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from midicoder.packs.cp36_tenant_onboarding.models import (
    BillingCycle,
    OnboardingIR,
    PlanConfig,
    SubscriptionPlan,
)


class OnboardingParser:
    """
    Parser để chuyển đổi DSL dict sang OnboardingIR.

    Parse cấu hình onboarding từ DSL, bao gồm:
    - Plan configs (pricing, features, limits)
    - Trial settings (default days, auto-start)
    - Approval policy (admin approval requirement)
    - Token expiry settings
    """

    def __init__(self, dsl: dict[str, Any]) -> None:
        """
        Khởi tạo OnboardingParser.

        Args:
            dsl: DSL dict từ contract YAML
        """
        self.dsl = dsl

    def parse(self) -> OnboardingIR:
        """
        Parse DSL dict sang OnboardingIR.

        Returns:
            OnboardingIR đã được parse hoàn chỉnh

        Raises:
            MidicoderError: Nếu DSL không hợp lệ
        """
        plans = self._parse_plans()
        default_trial_days = self.dsl.get("default_trial_days", 14)
        require_admin_approval = self.dsl.get("require_admin_approval", False)
        auto_start_trial = self.dsl.get("auto_start_trial", True)
        token_expiry = self.dsl.get("verification_token_expiry_hours", 24)

        return OnboardingIR(
            plans=plans,
            default_trial_days=default_trial_days,
            require_admin_approval=require_admin_approval,
            auto_start_trial=auto_start_trial,
            verification_token_expiry_hours=token_expiry,
        )

    def _parse_plans(self) -> list[PlanConfig]:
        """
        Parse danh sách plan configs từ DSL.

        Returns:
            Danh sách PlanConfig
        """
        plans_data = self.dsl.get("plans", [])
        plans: list[PlanConfig] = []

        for pdata in plans_data:
            plan = self._parse_plan(pdata)
            plans.append(plan)

        return plans

    def _parse_plan(self, data: dict[str, Any]) -> PlanConfig:
        """
        Parse một plan config từ DSL.

        Args:
            data: Dict chứa thông tin plan

        Returns:
            PlanConfig đã parse
        """
        plan_str = data.get("plan", "free")
        try:
            plan = SubscriptionPlan(plan_str)
        except ValueError:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.CP36_INVALID_PLAN,
                plan=plan_str,
                message=f"Plan không hợp lệ: {plan_str}"
            )

        return PlanConfig(
            plan=plan,
            monthly_price=Decimal(str(data.get("monthly_price", "0"))),
            yearly_price=Decimal(str(data.get("yearly_price", "0"))),
            features=data.get("features", []),
            max_users=data.get("max_users", 10),
            max_storage_gb=data.get("max_storage_gb", 10),
        )


def parse_onboarding_dsl(dsl: dict[str, Any]) -> OnboardingIR:
    """
    Convenience function để parse DSL dict sang OnboardingIR.

    Args:
        dsl: DSL dict từ contract YAML

    Returns:
        OnboardingIR đã parse
    """
    parser = OnboardingParser(dsl)
    return parser.parse()
