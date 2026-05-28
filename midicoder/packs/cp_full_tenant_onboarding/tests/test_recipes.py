# coding: utf-8
"""
Unit tests cho CP36 — Recipes.

Test cac recipes: self_service_saas, enterprise_b2b.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from decimal import Decimal

from midicoder.packs.cp_full_tenant_onboarding.recipes import (
    self_service_saas_recipe,
    enterprise_b2b_recipe,
)
from midicoder.packs.cp_full_tenant_onboarding.models import (
    OnboardingIR,
    PlanConfig,
    SubscriptionPlan,
    BillingCycle,
)


# ===========================================================================
# Test Self-Service SaaS Recipe
# ===========================================================================


class TestSelfServiceSaasRecipe:
    """Test recipe self_service_saas_recipe."""

    def test_returns_onboarding_ir(self) -> None:
        """Recipe tra ve OnboardingIR."""
        ir = self_service_saas_recipe()
        assert isinstance(ir, OnboardingIR)

    def test_has_four_plans(self) -> None:
        """Co 4 plans: free, starter, professional, enterprise."""
        ir = self_service_saas_recipe()
        assert len(ir.plans) == 4
        plan_names = [p.plan for p in ir.plans]
        assert SubscriptionPlan.FREE in plan_names
        assert SubscriptionPlan.STARTER in plan_names
        assert SubscriptionPlan.PROFESSIONAL in plan_names
        assert SubscriptionPlan.ENTERPRISE in plan_names

    def test_no_admin_approval(self) -> None:
        """Khong yeu cau admin approval."""
        ir = self_service_saas_recipe()
        assert ir.require_admin_approval is False

    def test_auto_start_trial(self) -> None:
        """Tu dong bat dau trial."""
        ir = self_service_saas_recipe()
        assert ir.auto_start_trial is True

    def test_default_trial_days(self) -> None:
        """Mac dinh 14 ngay trial."""
        ir = self_service_saas_recipe()
        assert ir.default_trial_days == 14

    def test_custom_trial_days(self) -> None:
        """Co the set so ngay trial khac."""
        ir = self_service_saas_recipe(trial_days=30)
        assert ir.default_trial_days == 30

    def test_free_plan_price_zero(self) -> None:
        """Free plan co gia = 0."""
        ir = self_service_saas_recipe()
        free_plan = ir.get_plan_config(SubscriptionPlan.FREE)
        assert free_plan is not None
        assert free_plan.monthly_price == Decimal("0")
        assert free_plan.yearly_price == Decimal("0")

    def test_starter_default_price(self) -> None:
        """Gia starter mac dinh chinh xac."""
        ir = self_service_saas_recipe()
        starter = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert starter is not None
        assert starter.monthly_price == Decimal("29.99")
        assert starter.yearly_price == Decimal("299.99")

    def test_custom_pricing(self) -> None:
        """Co the custom pricing."""
        ir = self_service_saas_recipe(
            starter_monthly=Decimal("19.99"),
            starter_yearly=Decimal("199.99"),
        )
        starter = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert starter is not None
        assert starter.monthly_price == Decimal("19.99")
        assert starter.yearly_price == Decimal("199.99")

    def test_plans_have_features(self) -> None:
        """Plans co danh sach features."""
        ir = self_service_saas_recipe()
        for plan in ir.plans:
            assert isinstance(plan.features, list)
            assert len(plan.features) > 0

    def test_plan_limits_increase(self) -> None:
        """Cap plan cao hon co nhieu users/storage hon."""
        ir = self_service_saas_recipe()
        free = ir.get_plan_config(SubscriptionPlan.FREE)
        starter = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert free is not None and starter is not None
        assert starter.max_users > free.max_users
        assert starter.max_storage_gb > free.max_storage_gb

    def test_token_expiry(self) -> None:
        """Token expiry 24 gio."""
        ir = self_service_saas_recipe()
        assert ir.verification_token_expiry_hours == 24

    def test_get_plan_price_monthly(self) -> None:
        """Lay gia monthly chinh xac."""
        ir = self_service_saas_recipe()
        price = ir.get_plan_price(SubscriptionPlan.PROFESSIONAL, BillingCycle.MONTHLY)
        assert price == Decimal("99.99")

    def test_get_plan_price_yearly(self) -> None:
        """Lay gia yearly chinh xac."""
        ir = self_service_saas_recipe()
        price = ir.get_plan_price(SubscriptionPlan.ENTERPRISE, BillingCycle.YEARLY)
        assert price == Decimal("4999.99")


# ===========================================================================
# Test Enterprise B2B Recipe
# ===========================================================================


class TestEnterpriseB2bRecipe:
    """Test recipe enterprise_b2b_recipe."""

    def test_returns_onboarding_ir(self) -> None:
        """Recipe tra ve OnboardingIR."""
        ir = enterprise_b2b_recipe()
        assert isinstance(ir, OnboardingIR)

    def test_has_three_plans(self) -> None:
        """Co 3 plans: starter, professional, enterprise (khong co free)."""
        ir = enterprise_b2b_recipe()
        assert len(ir.plans) == 3
        plan_names = [p.plan for p in ir.plans]
        assert SubscriptionPlan.FREE not in plan_names
        assert SubscriptionPlan.STARTER in plan_names
        assert SubscriptionPlan.PROFESSIONAL in plan_names
        assert SubscriptionPlan.ENTERPRISE in plan_names

    def test_requires_admin_approval(self) -> None:
        """Yeu cau admin approval."""
        ir = enterprise_b2b_recipe()
        assert ir.require_admin_approval is True

    def test_no_auto_trial(self) -> None:
        """Khong co auto start trial."""
        ir = enterprise_b2b_recipe()
        assert ir.auto_start_trial is False

    def test_zero_trial_days(self) -> None:
        """So ngay trial = 0."""
        ir = enterprise_b2b_recipe()
        assert ir.default_trial_days == 0

    def test_longer_token_expiry(self) -> None:
        """Token expiry 72 gio (3 ngay) cho enterprise."""
        ir = enterprise_b2b_recipe()
        assert ir.verification_token_expiry_hours == 72

    def test_higher_default_prices(self) -> None:
        """Gia enterprise cao hon SaaS."""
        ir = enterprise_b2b_recipe()
        starter = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert starter is not None
        assert starter.monthly_price == Decimal("199.99")

    def test_custom_pricing(self) -> None:
        """Co the custom pricing."""
        ir = enterprise_b2b_recipe(
            starter_monthly=Decimal("299.99"),
            starter_yearly=Decimal("2999.99"),
        )
        starter = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert starter is not None
        assert starter.monthly_price == Decimal("299.99")

    def test_higher_limits(self) -> None:
        """Enterprise co limits cao hon SaaS."""
        saas_ir = self_service_saas_recipe()
        b2b_ir = enterprise_b2b_recipe()

        saas_enterprise = saas_ir.get_plan_config(SubscriptionPlan.ENTERPRISE)
        b2b_enterprise = b2b_ir.get_plan_config(SubscriptionPlan.ENTERPRISE)

        assert saas_enterprise is not None and b2b_enterprise is not None
        assert b2b_enterprise.max_users > saas_enterprise.max_users
        assert b2b_enterprise.max_storage_gb > saas_enterprise.max_storage_gb

    def test_plans_have_enterprise_features(self) -> None:
        """Plans co features phuc vu doanh nghiep."""
        ir = enterprise_b2b_recipe()
        for plan in ir.plans:
            assert isinstance(plan.features, list)
            assert len(plan.features) > 0
            # Moi plan phai co audit_log
            assert "audit_log" in plan.features

    def test_validate_passes(self) -> None:
        """Validate IR khong throw loi."""
        ir = enterprise_b2b_recipe()
        ir.validate()  # khong throw
