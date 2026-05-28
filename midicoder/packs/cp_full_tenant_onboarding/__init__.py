# coding: utf-8
"""
CP36: Tenant Onboarding & Subscription Generator.

Cung cấp 4 capabilities:
- tenant_register: Đăng ký tenant mới qua email
- tenant_verify: Xác minh tenant (token-based + admin approval)
- trial_manage: Quản lý trial period
- subscription_manage: Quản lý subscription (activate, update, cancel)

Support 4 stacks: FastAPI, NestJS, React, Angular.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp_full_tenant_onboarding.models import (
    SubscriptionPlan,
    RegistrationStatus,
    SubscriptionStatus,
    BillingCycle,
    TenantRegistration,
    TenantSubscription,
    PlanConfig,
    OnboardingIR,
)
from midicoder.packs.cp_full_tenant_onboarding.parser import (
    OnboardingParser,
    parse_onboarding_dsl,
)
from midicoder.packs.cp_full_tenant_onboarding.recipes import (
    self_service_saas_recipe,
    enterprise_b2b_recipe,
)
from midicoder.packs.cp_full_tenant_onboarding.fastapi import (
    TenantOnboardingFastAPIEmitter,
    GeneratedFile,
)
from midicoder.packs.cp_full_tenant_onboarding.nestjs import (
    TenantOnboardingNestJSEmitter,
)
from midicoder.packs.cp_full_tenant_onboarding.angular import (
    TenantOnboardingAngularEmitter,
)
from midicoder.packs.cp_full_tenant_onboarding.react import (
    TenantOnboardingReactEmitter,
)

__all__ = [
    # Enums
    "SubscriptionPlan",
    "RegistrationStatus",
    "SubscriptionStatus",
    "BillingCycle",
    # Models
    "TenantRegistration",
    "TenantSubscription",
    "PlanConfig",
    "OnboardingIR",
    # Parser
    "OnboardingParser",
    "parse_onboarding_dsl",
    # Recipes
    "self_service_saas_recipe",
    "enterprise_b2b_recipe",
    # Emitters
    "TenantOnboardingFastAPIEmitter",
    "TenantOnboardingNestJSEmitter",
    "TenantOnboardingAngularEmitter",
    "TenantOnboardingReactEmitter",
    "GeneratedFile",
]
