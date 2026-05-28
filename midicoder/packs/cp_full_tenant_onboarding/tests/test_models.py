# coding: utf-8
"""
Unit tests cho CP36 — Tenant Onboarding & Subscription Models.

Test các dataclass:
- SubscriptionPlan, RegistrationStatus, SubscriptionStatus, BillingCycle (enums)
- TenantRegistration: validation, to_dict, from_dict
- TenantSubscription: validation, to_dict, from_dict
- OnboardingIR: validation, getter methods

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from midicoder.packs.cp_full_tenant_onboarding.models import (
    SubscriptionPlan,
    RegistrationStatus,
    SubscriptionStatus,
    BillingCycle,
    TenantRegistration,
    TenantSubscription,
    OnboardingIR,
)
from midicoder.errors import MidicoderError


# ===========================================================================
# Test Enums
# ===========================================================================


class TestSubscriptionPlan:
    """Test enum SubscriptionPlan."""

    def test_plan_values(self) -> None:
        """Kiem tra cac gia tri plan."""
        assert SubscriptionPlan.FREE.value == "free"
        assert SubscriptionPlan.STARTER.value == "starter"
        assert SubscriptionPlan.PROFESSIONAL.value == "professional"
        assert SubscriptionPlan.ENTERPRISE.value == "enterprise"

    def test_plan_from_string(self) -> None:
        """Kiem tra tao plan tu string."""
        assert SubscriptionPlan("free") == SubscriptionPlan.FREE
        assert SubscriptionPlan("starter") == SubscriptionPlan.STARTER
        assert SubscriptionPlan("professional") == SubscriptionPlan.PROFESSIONAL
        assert SubscriptionPlan("enterprise") == SubscriptionPlan.ENTERPRISE


class TestRegistrationStatus:
    """Test enum RegistrationStatus."""

    def test_status_values(self) -> None:
        """Kiem tra cac gia tri status."""
        assert RegistrationStatus.PENDING.value == "pending"
        assert RegistrationStatus.VERIFIED.value == "verified"
        assert RegistrationStatus.REJECTED.value == "rejected"
        assert RegistrationStatus.CANCELLED.value == "cancelled"


class TestSubscriptionStatus:
    """Test enum SubscriptionStatus."""

    def test_status_values(self) -> None:
        """Kiem tra cac gia tri subscription status."""
        assert SubscriptionStatus.TRIAL.value == "trial"
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.CANCELLED.value == "cancelled"
        assert SubscriptionStatus.EXPIRED.value == "expired"


class TestBillingCycle:
    """Test enum BillingCycle."""

    def test_cycle_values(self) -> None:
        """Kiem tra cac gia tri billing cycle."""
        assert BillingCycle.MONTHLY.value == "monthly"
        assert BillingCycle.YEARLY.value == "yearly"


# ===========================================================================
# Test TenantRegistration
# ===========================================================================


class TestTenantRegistration:
    """Test dataclass TenantRegistration."""

    def _make_valid(self, **kwargs) -> TenantRegistration:
        """Tao TenantRegistration hop le de test."""
        defaults = {
            "email": "test@example.com",
            "company_name": "Test Company",
            "plan": SubscriptionPlan.FREE,
            "trial_days": 14,
            "status": RegistrationStatus.PENDING,
            "verification_token": "abc123token",
            "tenant_id": str(uuid4()),
        }
        defaults.update(kwargs)
        return TenantRegistration(**defaults)

    def test_create_valid_registration(self) -> None:
        """Tao registration hop le thanh cong."""
        reg = self._make_valid()
        assert reg.email == "test@example.com"
        assert reg.company_name == "Test Company"
        assert reg.plan == SubscriptionPlan.FREE
        assert reg.trial_days == 14
        assert reg.status == RegistrationStatus.PENDING

    def test_empty_email_raises(self) -> None:
        """Email trong throw loi MDC-CP36-001."""
        with pytest.raises(MidicoderError) as exc_info:
            self._make_valid(email="")
        assert "CP36_EMPTY_EMAIL" in str(exc_info.value) or "MDC-CP36-001" in str(exc_info.value)

    def test_invalid_email_format_raises(self) -> None:
        """Email khong hop le throw loi MDC-CP36-002."""
        with pytest.raises(MidicoderError) as exc_info:
            self._make_valid(email="not-an-email")
        assert "CP36_INVALID_EMAIL" in str(exc_info.value) or "MDC-CP36-002" in str(exc_info.value)

    def test_empty_company_name_raises(self) -> None:
        """Ten cong ty trong throw loi MDC-CP36-005."""
        with pytest.raises(MidicoderError) as exc_info:
            self._make_valid(company_name="")
        assert "CP36_EMPTY_COMPANY_NAME" in str(exc_info.value) or "MDC-CP36-005" in str(exc_info.value)

    def test_invalid_trial_days_raises(self) -> None:
        """So ngay trial am throw loi MDC-CP36-013."""
        with pytest.raises(MidicoderError) as exc_info:
            self._make_valid(trial_days=-1)
        assert "CP36_INVALID_TRIAL_DAYS" in str(exc_info.value) or "MDC-CP36-013" in str(exc_info.value)

    def test_zero_trial_days_is_valid(self) -> None:
        """So ngay trial bang 0 la hop le (khong co trial)."""
        reg = self._make_valid(trial_days=0)
        assert reg.trial_days == 0

    def test_to_dict(self) -> None:
        """Chuyen sang dict thanh cong."""
        reg = self._make_valid()
        d = reg.to_dict()
        assert d["email"] == "test@example.com"
        assert d["company_name"] == "Test Company"
        assert d["plan"] == "free"
        assert d["trial_days"] == 14
        assert d["status"] == "pending"

    def test_from_dict_roundtrip(self) -> None:
        """from_dict -> to_dict roundtrip."""
        reg = self._make_valid()
        d = reg.to_dict()
        reg2 = TenantRegistration.from_dict(d)
        assert reg2.email == reg.email
        assert reg2.company_name == reg.company_name
        assert reg2.plan == reg.plan
        assert reg2.trial_days == reg.trial_days
        assert reg2.status == reg.status

    def test_compute_expiry_date(self) -> None:
        """Tinh ngay het han trial chinh xac."""
        now = datetime.now(timezone.utc)
        reg = self._make_valid()
        reg.created_at = now
        expiry = reg.compute_expiry_date()
        expected = now + timedelta(days=14)
        assert abs((expiry - expected).total_seconds()) < 1

    def test_compute_expiry_zero_trial(self) -> None:
        """Trial = 0 => expiry = created_at."""
        now = datetime.now(timezone.utc)
        reg = self._make_valid(trial_days=0)
        reg.created_at = now
        expiry = reg.compute_expiry_date()
        assert expiry == now

    def test_is_trial_expired_true(self) -> None:
        """Trial het hạn trả về True."""
        reg = self._make_valid(trial_days=1)
        reg.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        assert reg.is_trial_expired() is True

    def test_is_trial_expired_false(self) -> None:
        """Trial chua het hạn trả về False."""
        reg = self._make_valid(trial_days=14)
        reg.created_at = datetime.now(timezone.utc)
        assert reg.is_trial_expired() is False

    def test_is_verified_true(self) -> None:
        """Da xac minh tra ve True."""
        reg = self._make_valid(status=RegistrationStatus.VERIFIED)
        assert reg.is_verified is True

    def test_is_verified_false(self) -> None:
        """Chua xac minh tra ve False."""
        reg = self._make_valid(status=RegistrationStatus.PENDING)
        assert reg.is_verified is False


# ===========================================================================
# Test TenantSubscription
# ===========================================================================


class TestTenantSubscription:
    """Test dataclass TenantSubscription."""

    def _make_valid(self, **kwargs) -> TenantSubscription:
        """Tao TenantSubscription hop le de test."""
        defaults = {
            "tenant_id": str(uuid4()),
            "plan": SubscriptionPlan.STARTER,
            "billing_cycle": BillingCycle.MONTHLY,
            "status": SubscriptionStatus.ACTIVE,
            "price": Decimal("29.99"),
            "currency": "USD",
        }
        defaults.update(kwargs)
        return TenantSubscription(**defaults)

    def test_create_valid_subscription(self) -> None:
        """Tao subscription hop le thanh cong."""
        sub = self._make_valid()
        assert sub.plan == SubscriptionPlan.STARTER
        assert sub.billing_cycle == BillingCycle.MONTHLY
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.price == Decimal("29.99")
        assert sub.currency == "USD"

    def test_empty_tenant_id_raises(self) -> None:
        """Tenant ID trong throw loi."""
        with pytest.raises(MidicoderError):
            self._make_valid(tenant_id="")

    def test_negative_price_raises(self) -> None:
        """Gia tri am throw loi."""
        with pytest.raises(MidicoderError) as exc_info:
            self._make_valid(price=Decimal("-10"))
        assert "CP36" in str(exc_info.value) or "MDC-CP36" in str(exc_info.value) or "PRICE" in str(exc_info.value).upper()

    def test_zero_price_for_free_plan(self) -> None:
        """Plan free cho phep price = 0."""
        sub = self._make_valid(plan=SubscriptionPlan.FREE, price=Decimal("0"))
        assert sub.price == Decimal("0")
        assert sub.plan == SubscriptionPlan.FREE

    def test_to_dict(self) -> None:
        """Chuyen sang dict thanh cong."""
        sub = self._make_valid()
        d = sub.to_dict()
        assert d["plan"] == "starter"
        assert d["billing_cycle"] == "monthly"
        assert d["status"] == "active"
        assert d["currency"] == "USD"

    def test_from_dict_roundtrip(self) -> None:
        """from_dict -> to_dict roundtrip."""
        sub = self._make_valid()
        d = sub.to_dict()
        sub2 = TenantSubscription.from_dict(d)
        assert sub2.plan == sub.plan
        assert sub2.billing_cycle == sub.billing_cycle
        assert sub2.status == sub.status
        assert sub2.currency == sub.currency

    def test_is_active_true(self) -> None:
        """Subscription active tra ve True."""
        sub = self._make_valid(status=SubscriptionStatus.ACTIVE)
        assert sub.is_active is True

    def test_is_active_false(self) -> None:
        """Subscription cancelled tra ve False cho is_active."""
        sub = self._make_valid(status=SubscriptionStatus.CANCELLED)
        assert sub.is_active is False

    def test_is_trial_true(self) -> None:
        """Subscription trial tra ve True."""
        sub = self._make_valid(status=SubscriptionStatus.TRIAL)
        assert sub.is_trial is True

    def test_can_upgrade(self) -> None:
        """Co the upgrade tu free -> starter."""
        sub = self._make_valid(plan=SubscriptionPlan.FREE, status=SubscriptionStatus.ACTIVE)
        assert sub.can_upgrade(SubscriptionPlan.STARTER) is True

    def test_cannot_upgrade_to_same_plan(self) -> None:
        """Khong upgrade sang cung plan."""
        sub = self._make_valid(plan=SubscriptionPlan.STARTER, status=SubscriptionStatus.ACTIVE)
        assert sub.can_upgrade(SubscriptionPlan.STARTER) is False

    def test_cannot_upgrade_cancelled(self) -> None:
        """Khong upgrade subscription da cancel."""
        sub = self._make_valid(plan=SubscriptionPlan.FREE, status=SubscriptionStatus.CANCELLED)
        assert sub.can_upgrade(SubscriptionPlan.PROFESSIONAL) is False

    def test_is_free_plan(self) -> None:
        """Plan free tra ve True cho requires_payment = False."""
        sub = self._make_valid(plan=SubscriptionPlan.FREE)
        assert sub.requires_payment is False

    def test_paid_plan_requires_payment(self) -> None:
        """Plan paid tra ve True cho requires_payment."""
        sub = self._make_valid(plan=SubscriptionPlan.STARTER)
        assert sub.requires_payment is True


# ===========================================================================
# Test OnboardingIR
# ===========================================================================


class TestOnboardingIR:
    """Test dataclass OnboardingIR."""

    def test_create_empty_ir(self) -> None:
        """Tao OnboardingIR trong."""
        ir = OnboardingIR()
        assert ir.plans == []
        assert ir.default_trial_days == 14
        assert ir.require_admin_approval is False
        assert ir.auto_start_trial is True

    def test_set_default_trial_days(self) -> None:
        """Set so ngay trial mac dinh."""
        ir = OnboardingIR(default_trial_days=30)
        assert ir.default_trial_days == 30

    def test_invalid_default_trial_days(self) -> None:
        """So ngay trial am khong hop le."""
        with pytest.raises(MidicoderError):
            OnboardingIR(default_trial_days=-5)

    def test_get_plan_price(self) -> None:
        """Lay gia cua plan."""
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        ir = OnboardingIR(
            plans=[
                PlanConfig(plan=SubscriptionPlan.STARTER, monthly_price=Decimal("29.99"), yearly_price=Decimal("299.99")),
            ]
        )
        price = ir.get_plan_price(SubscriptionPlan.STARTER, BillingCycle.MONTHLY)
        assert price == Decimal("29.99")

    def test_get_plan_price_not_found(self) -> None:
        """Plan khong ton tai tra ve None."""
        ir = OnboardingIR()
        price = ir.get_plan_price(SubscriptionPlan.ENTERPRISE, BillingCycle.MONTHLY)
        assert price is None

    def test_get_plan_price_yearly(self) -> None:
        """Lay gia yearly."""
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        ir = OnboardingIR(
            plans=[
                PlanConfig(plan=SubscriptionPlan.PROFESSIONAL, monthly_price=Decimal("99.99"), yearly_price=Decimal("999.99")),
            ]
        )
        price = ir.get_plan_price(SubscriptionPlan.PROFESSIONAL, BillingCycle.YEARLY)
        assert price == Decimal("999.99")

    def test_validate_no_error(self) -> None:
        """Validate IR hop le khong throw."""
        ir = OnboardingIR()
        ir.validate()  # khong throw

    def test_to_dict_from_dict(self) -> None:
        """Roundtrip to_dict/from_dict."""
        ir = OnboardingIR(
            default_trial_days=30,
            require_admin_approval=True,
            auto_start_trial=False,
        )
        d = ir.to_dict()
        ir2 = OnboardingIR.from_dict(d)
        assert ir2.default_trial_days == 30
        assert ir2.require_admin_approval is True
        assert ir2.auto_start_trial is False

    def test_validate_free_plan_with_price_raises(self) -> None:
        """Free plan co gia > 0 throw loi validate."""
        from midicoder.errors import MidicoderError
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        ir = OnboardingIR(
            plans=[
                PlanConfig(plan=SubscriptionPlan.FREE, monthly_price=Decimal("10")),
            ]
        )
        with pytest.raises(MidicoderError):
            ir.validate()

    def test_get_plan_config_found(self) -> None:
        """Lay plan config ton tai tra ve PlanConfig."""
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        ir = OnboardingIR(
            plans=[
                PlanConfig(plan=SubscriptionPlan.STARTER, monthly_price=Decimal("29.99")),
            ]
        )
        pc = ir.get_plan_config(SubscriptionPlan.STARTER)
        assert pc is not None
        assert pc.plan == SubscriptionPlan.STARTER

    def test_get_plan_config_not_found(self) -> None:
        """Lay plan config khong ton tai tra ve None."""
        ir = OnboardingIR()
        pc = ir.get_plan_config(SubscriptionPlan.ENTERPRISE)
        assert pc is None

    def test_token_expiry_less_than_one(self) -> None:
        """Token expiry < 1 duoc set ve 24."""
        ir = OnboardingIR(verification_token_expiry_hours=0)
        assert ir.verification_token_expiry_hours == 24


# ===========================================================================
# Test PlanConfig
# ===========================================================================


class TestPlanConfig:
    """Test dataclass PlanConfig."""

    def test_to_dict(self) -> None:
        """Chuyen PlanConfig sang dict."""
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        pc = PlanConfig(
            plan=SubscriptionPlan.STARTER,
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features=["api", "dashboard"],
            max_users=25,
            max_storage_gb=50,
        )
        d = pc.to_dict()
        assert d["plan"] == "starter"
        assert d["monthly_price"] == "29.99"
        assert d["features"] == ["api", "dashboard"]

    def test_from_dict_roundtrip(self) -> None:
        """Roundtrip from_dict/to_dict."""
        from midicoder.packs.cp_full_tenant_onboarding.models import PlanConfig
        pc = PlanConfig(
            plan=SubscriptionPlan.PROFESSIONAL,
            monthly_price=Decimal("99.99"),
            features=["analytics"],
        )
        d = pc.to_dict()
        pc2 = PlanConfig.from_dict(d)
        assert pc2.plan == pc.plan
        assert pc2.monthly_price == pc.monthly_price
        assert pc2.features == pc.features
