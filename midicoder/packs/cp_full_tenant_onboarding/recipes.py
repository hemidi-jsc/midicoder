# coding: utf-8
"""
Recipes cho CP36 — Tenant Onboarding & Subscription.

Mỗi recipe là một cách gán giá trị cụ thể vào pattern vocabulary —
không phải domain-specific macro, không nested recipe.

Recipe = 1 level duy nhất, gọi trực tiếp tới models.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from decimal import Decimal

from midicoder.packs.cp_full_tenant_onboarding.models import (
    BillingCycle,
    OnboardingIR,
    PlanConfig,
    SubscriptionPlan,
)


# ===========================================================================
# Self-Service SaaS Recipe
# ===========================================================================


def self_service_saas_recipe(
    trial_days: int = 14,
    starter_monthly: Decimal = Decimal("29.99"),
    starter_yearly: Decimal = Decimal("299.99"),
    professional_monthly: Decimal = Decimal("99.99"),
    professional_yearly: Decimal = Decimal("999.99"),
    enterprise_monthly: Decimal = Decimal("499.99"),
    enterprise_yearly: Decimal = Decimal("4999.99"),
) -> OnboardingIR:
    """
    Recipe cho self-service SaaS onboarding.

    - Email verify tu dong (khong can admin approve)
    - Trial 14 ngay tu dong bat dau sau verification
    - Self-serve checkout: tenant co the chon plan va thanh toan
    - Plans co gia cu the, co the tinh prorate

    Args:
        trial_days: So ngay trial mac dinh
        starter_monthly: Gia starter hang thang
        starter_yearly: Gia starter hang nam
        professional_monthly: Gia professional hang thang
        professional_yearly: Gia professional hang nam
        enterprise_monthly: Gia enterprise hang thang
        enterprise_yearly: Gia enterprise hang nam

    Returns:
        OnboardingIR cau hinh xong cho self-service SaaS
    """
    return OnboardingIR(
        plans=[
            PlanConfig(
                plan=SubscriptionPlan.FREE,
                monthly_price=Decimal("0"),
                yearly_price=Decimal("0"),
                features=["basic_api", "dashboard"],
                max_users=5,
                max_storage_gb=5,
            ),
            PlanConfig(
                plan=SubscriptionPlan.STARTER,
                monthly_price=starter_monthly,
                yearly_price=starter_yearly,
                features=["api", "dashboard", "email_support"],
                max_users=25,
                max_storage_gb=50,
            ),
            PlanConfig(
                plan=SubscriptionPlan.PROFESSIONAL,
                monthly_price=professional_monthly,
                yearly_price=professional_yearly,
                features=["api", "dashboard", "analytics", "priority_support", "ssso"],
                max_users=100,
                max_storage_gb=200,
            ),
            PlanConfig(
                plan=SubscriptionPlan.ENTERPRISE,
                monthly_price=enterprise_monthly,
                yearly_price=enterprise_yearly,
                features=["api", "dashboard", "analytics", "dedicated_support", "sso", "custom_integrations", "sla"],
                max_users=1000,
                max_storage_gb=1000,
            ),
        ],
        default_trial_days=trial_days,
        require_admin_approval=False,
        auto_start_trial=True,
        verification_token_expiry_hours=24,
    )


# ===========================================================================
# Enterprise B2B Recipe
# ===========================================================================


def enterprise_b2b_recipe(
    starter_monthly: Decimal = Decimal("199.99"),
    starter_yearly: Decimal = Decimal("1999.99"),
    professional_monthly: Decimal = Decimal("499.99"),
    professional_yearly: Decimal = Decimal("4999.99"),
    enterprise_monthly: Decimal = Decimal("999.99"),
    enterprise_yearly: Decimal = Decimal("9999.99"),
) -> OnboardingIR:
    """
    Recipe cho enterprise B2B onboarding.

    - Admin approve bat buoc truoc khi tenant duoc hoat dong
    - Khong co trial period — sales-led onboarding
    - Custom pricing: gia duoc dao tao boi sales team
    - Features day du hon, phuc vu doanh nghiep lon

    Args:
        starter_monthly: Gia starter hang thang
        starter_yearly: Gia starter hang nam
        professional_monthly: Gia professional hang thang
        professional_yearly: Gia professional hang nam
        enterprise_monthly: Gia enterprise hang thang
        enterprise_yearly: Gia enterprise hang nam

    Returns:
        OnboardingIR cau hinh xong cho enterprise B2B
    """
    return OnboardingIR(
        plans=[
            PlanConfig(
                plan=SubscriptionPlan.STARTER,
                monthly_price=starter_monthly,
                yearly_price=starter_yearly,
                features=["api", "dashboard", "dedicated_support", "audit_log"],
                max_users=50,
                max_storage_gb=100,
            ),
            PlanConfig(
                plan=SubscriptionPlan.PROFESSIONAL,
                monthly_price=professional_monthly,
                yearly_price=professional_yearly,
                features=["api", "dashboard", "analytics", "dedicated_support", "sso", "audit_log", "custom_reporting"],
                max_users=200,
                max_storage_gb=500,
            ),
            PlanConfig(
                plan=SubscriptionPlan.ENTERPRISE,
                monthly_price=enterprise_monthly,
                yearly_price=enterprise_yearly,
                features=["api", "dashboard", "analytics", "dedicated_support", "sso", "audit_log", "custom_reporting", "custom_integrations", "sla_99_9", "on_premise_option"],
                max_users=10000,
                max_storage_gb=10000,
            ),
        ],
        default_trial_days=0,
        require_admin_approval=True,
        auto_start_trial=False,
        verification_token_expiry_hours=72,
    )


__all__ = [
    "self_service_saas_recipe",
    "enterprise_b2b_recipe",
]
