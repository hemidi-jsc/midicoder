# coding: utf-8
"""
Unit tests cho CP36 — Parser.

Test OnboardingParser parse DSL dict → OnboardingIR.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from decimal import Decimal

from midicoder.packs.cp36_tenant_onboarding.parser import (
    OnboardingParser,
    parse_onboarding_dsl,
)
from midicoder.packs.cp36_tenant_onboarding.models import (
    SubscriptionPlan,
    BillingCycle,
    OnboardingIR,
    PlanConfig,
)
from midicoder.errors import MidicoderError


# ===========================================================================
# Test OnboardingParser
# ===========================================================================


class TestOnboardingParser:
    """Test class OnboardingParser."""

    def test_parse_minimal_dsl(self) -> None:
        """Parse DSL tối thiểu tra ve OnboardingIR mac dinh."""
        dsl = {}
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert isinstance(ir, OnboardingIR)
        assert ir.default_trial_days == 14
        assert ir.require_admin_approval is False
        assert ir.auto_start_trial is True
        assert ir.plans == []

    def test_parse_full_dsl(self) -> None:
        """Parse DSL day du tra ve OnboardingIR hoan chinh."""
        dsl = {
            "default_trial_days": 30,
            "require_admin_approval": True,
            "auto_start_trial": False,
            "verification_token_expiry_hours": 48,
            "plans": [
                {
                    "plan": "starter",
                    "monthly_price": "29.99",
                    "yearly_price": "299.99",
                    "features": ["api", "dashboard"],
                    "max_users": 25,
                    "max_storage_gb": 50,
                },
                {
                    "plan": "professional",
                    "monthly_price": "99.99",
                    "yearly_price": "999.99",
                    "features": ["api", "dashboard", "analytics", "priority_support"],
                    "max_users": 100,
                    "max_storage_gb": 200,
                },
            ],
        }
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert ir.default_trial_days == 30
        assert ir.require_admin_approval is True
        assert ir.auto_start_trial is False
        assert ir.verification_token_expiry_hours == 48
        assert len(ir.plans) == 2

        starter = ir.plans[0]
        assert starter.plan == SubscriptionPlan.STARTER
        assert starter.monthly_price == Decimal("29.99")
        assert starter.yearly_price == Decimal("299.99")
        assert starter.features == ["api", "dashboard"]
        assert starter.max_users == 25
        assert starter.max_storage_gb == 50

        professional = ir.plans[1]
        assert professional.plan == SubscriptionPlan.PROFESSIONAL

    def test_parse_free_plan(self) -> None:
        """Parse free plan co gia = 0."""
        dsl = {
            "plans": [
                {
                    "plan": "free",
                    "monthly_price": "0",
                    "yearly_price": "0",
                    "max_users": 5,
                    "max_storage_gb": 5,
                }
            ]
        }
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert len(ir.plans) == 1
        assert ir.plans[0].plan == SubscriptionPlan.FREE
        assert ir.plans[0].monthly_price == Decimal("0")

    def test_parse_invalid_plan_raises(self) -> None:
        """Parse plan khong hop le throw loi."""
        dsl = {
            "plans": [
                {"plan": "invalid_plan", "monthly_price": "10"}
            ]
        }
        parser = OnboardingParser(dsl)
        with pytest.raises(MidicoderError):
            parser.parse()

    def test_parse_negative_trial_days_raises(self) -> None:
        """Parse so ngay trial am throw loi."""
        dsl = {"default_trial_days": -5}
        parser = OnboardingParser(dsl)
        with pytest.raises(MidicoderError):
            parser.parse()

    def test_parse_with_dependencies(self) -> None:
        """Parse DSL voi dependencies check."""
        dsl = {
            "depends_on": ["CP02", "CP03", "CP12", "CP33"],
            "default_trial_days": 14,
        }
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert ir.default_trial_days == 14
        # dependencies duoc parse nhung khong anh huong den IR

    def test_parse_empty_plans_list(self) -> None:
        """Parse danh sach plan trong tra ve list trong."""
        dsl = {"plans": []}
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert ir.plans == []

    def test_parse_plan_with_defaults(self) -> None:
        """Parse plan khong co features/users mac dinh."""
        dsl = {
            "plans": [
                {"plan": "enterprise", "monthly_price": "499.99", "yearly_price": "4999.99"}
            ]
        }
        parser = OnboardingParser(dsl)
        ir = parser.parse()

        assert len(ir.plans) == 1
        assert ir.plans[0].plan == SubscriptionPlan.ENTERPRISE
        assert ir.plans[0].monthly_price == Decimal("499.99")
        assert ir.plans[0].features == []
        assert ir.plans[0].max_users == 10
        assert ir.plans[0].max_storage_gb == 10


# ===========================================================================
# Test module-level convenience function
# ===========================================================================


class TestParseOnboardingDsl:
    """Test module-level parse function."""

    def test_parse_onboarding_dsl_returns_ir(self) -> None:
        """parse_onboarding_dsl tra ve OnboardingIR."""
        dsl = {
            "default_trial_days": 21,
            "plans": [
                {"plan": "free", "monthly_price": "0", "yearly_price": "0"}
            ]
        }
        ir = parse_onboarding_dsl(dsl)

        assert isinstance(ir, OnboardingIR)
        assert ir.default_trial_days == 21
        assert len(ir.plans) == 1

    def test_parse_onboarding_dsl_empty_dict(self) -> None:
        """parse_onboarding_dsl voi dict trong tra ve IR mac dinh."""
        ir = parse_onboarding_dsl({})

        assert isinstance(ir, OnboardingIR)
        assert ir.default_trial_days == 14
