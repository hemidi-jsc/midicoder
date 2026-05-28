# coding: utf-8
"""Tests cho CP59 — Tenant Billing & Invoicing models."""

from datetime import datetime, timezone

import pytest
from midicoder.packs.cp_full_tenant_billing.models import (
    BillingCycle,
    BillingPlan,
    CaptureMode,
    CycleType,
    GatewayProvider,
    InvoiceConfig,
    InvoiceStatus,
    MetricName,
    PaymentGatewayConfig,
    PlanTier,
    UsageMeter,
)


# =============================================================================
# Enums
# =============================================================================

class TestPlanTier:
    def test_enum_values(self):
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.PROFESSIONAL.value == "professional"
        assert PlanTier.ENTERPRISE.value == "enterprise"

    def test_enum_count(self):
        assert len(PlanTier) == 4


class TestCycleType:
    def test_enum_values(self):
        assert CycleType.MONTHLY.value == "monthly"
        assert CycleType.QUARTERLY.value == "quarterly"
        assert CycleType.ANNUAL.value == "annual"

    def test_enum_count(self):
        assert len(CycleType) == 3


class TestInvoiceStatus:
    def test_enum_values(self):
        assert InvoiceStatus.DRAFT.value == "draft"
        assert InvoiceStatus.SENT.value == "sent"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.OVERDUE.value == "overdue"
        assert InvoiceStatus.VOID.value == "void"

    def test_enum_count(self):
        assert len(InvoiceStatus) == 5


class TestMetricName:
    def test_enum_values(self):
        assert MetricName.API_CALLS.value == "api_calls"
        assert MetricName.STORAGE_GB.value == "storage_gb"
        assert MetricName.USERS.value == "users"
        assert MetricName.BANDWIDTH_GB.value == "bandwidth_gb"

    def test_enum_count(self):
        assert len(MetricName) == 4


class TestGatewayProvider:
    def test_enum_values(self):
        assert GatewayProvider.STRIPE.value == "stripe"
        assert GatewayProvider.PAYPAL.value == "paypal"
        assert GatewayProvider.ADYEN.value == "adyen"

    def test_enum_count(self):
        assert len(GatewayProvider) == 3


class TestCaptureMode:
    def test_enum_values(self):
        assert CaptureMode.AUTOMATIC.value == "automatic"
        assert CaptureMode.MANUAL.value == "manual"

    def test_enum_count(self):
        assert len(CaptureMode) == 2


# =============================================================================
# BillingPlan
# =============================================================================

class TestBillingPlan:
    def test_creation_with_defaults(self):
        bp = BillingPlan(id="bp-1", name="Free", tier=PlanTier.FREE)
        assert bp.id == "bp-1"
        assert bp.monthly_price == 0
        assert bp.annual_price == 0
        assert bp.created_at is not None
        assert bp.updated_at is not None

    def test_creation_with_all_fields(self):
        bp = BillingPlan(
            id="bp-2", name="Pro", tier=PlanTier.PROFESSIONAL,
            monthly_price=4999, annual_price=49990,
            features=["feature1"], usage_limits={"api_calls": 10000},
        )
        assert bp.monthly_price == 4999
        assert bp.features == ["feature1"]

    def test_annual_savings_percentage(self):
        bp = BillingPlan(id="bp-3", name="Savings", tier=PlanTier.STARTER, monthly_price=1000, annual_price=10000)
        assert bp.annual_savings_percentage > 0

    def test_annual_savings_zero_monthly(self):
        bp = BillingPlan(id="bp-4", name="Free", tier=PlanTier.FREE, monthly_price=0, annual_price=0)
        assert bp.annual_savings_percentage == 0.0

    def test_to_dict(self):
        bp = BillingPlan(id="bp-5", name="Test", tier=PlanTier.STARTER, monthly_price=500)
        d = bp.to_dict()
        assert d["id"] == "bp-5"
        assert d["tier"] == "starter"
        assert d["monthly_price"] == 500

    def test_from_dict(self):
        data = {"id": "bp-6", "name": "FromDict", "tier": "enterprise", "monthly_price": 9999}
        bp = BillingPlan.from_dict(data)
        assert bp.tier == PlanTier.ENTERPRISE
        assert bp.monthly_price == 9999

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            BillingPlan(id="", name="x", tier=PlanTier.FREE)

    def test_validation_error_negative_monthly_price(self):
        with pytest.raises(Exception):
            BillingPlan(id="bp-7", name="x", tier=PlanTier.FREE, monthly_price=-1)

    def test_validation_error_negative_annual_price(self):
        with pytest.raises(Exception):
            BillingPlan(id="bp-8", name="x", tier=PlanTier.FREE, annual_price=-1)

    def test_roundtrip(self):
        original = BillingPlan(
            id="rt-bp", name="rt", tier=PlanTier.PROFESSIONAL,
            monthly_price=4999, annual_price=49990,
        )
        d = original.to_dict()
        restored = BillingPlan.from_dict(d)
        assert restored.id == original.id
        assert restored.tier == original.tier
        assert restored.monthly_price == original.monthly_price


# =============================================================================
# BillingCycle
# =============================================================================

class TestBillingCycle:
    def test_creation_with_defaults(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        bc = BillingCycle(id="bc-1", type=CycleType.MONTHLY, start_date=now, end_date=future)
        assert bc.id == "bc-1"
        assert bc.auto_renew is True

    def test_creation_with_all_fields(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        bc = BillingCycle(
            id="bc-2", type=CycleType.ANNUAL, start_date=now, end_date=future,
            auto_renew=False, metadata={"key": "val"},
        )
        assert bc.auto_renew is False
        assert bc.metadata == {"key": "val"}

    def test_is_expired(self):
        past_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        past_end = datetime(2024, 2, 1, tzinfo=timezone.utc)
        bc = BillingCycle(id="bc-3", type=CycleType.MONTHLY, start_date=past_start, end_date=past_end)
        assert bc.is_expired is True

    def test_to_dict(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        bc = BillingCycle(id="bc-4", type=CycleType.QUARTERLY, start_date=now, end_date=future)
        d = bc.to_dict()
        assert d["type"] == "quarterly"
        assert d["auto_renew"] is True

    def test_from_dict(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        data = {
            "id": "bc-5", "type": "annual",
            "start_date": now.isoformat(), "end_date": future.isoformat(),
        }
        bc = BillingCycle.from_dict(data)
        assert bc.type == CycleType.ANNUAL

    def test_validation_error_empty_id(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(Exception):
            BillingCycle(id="", type=CycleType.MONTHLY, start_date=now, end_date=future)

    def test_validation_error_end_before_start(self):
        now = datetime.now(timezone.utc)
        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(Exception):
            BillingCycle(id="bc-6", type=CycleType.MONTHLY, start_date=now, end_date=past)

    def test_roundtrip(self):
        now = datetime.now(timezone.utc)
        future = datetime(2027, 6, 1, tzinfo=timezone.utc)
        original = BillingCycle(
            id="rt-bc", type=CycleType.MONTHLY, start_date=now, end_date=future,
            auto_renew=False,
        )
        d = original.to_dict()
        restored = BillingCycle.from_dict(d)
        assert restored.id == original.id
        assert restored.type == original.type
        assert restored.auto_renew == original.auto_renew


# =============================================================================
# InvoiceConfig
# =============================================================================

class TestInvoiceConfig:
    def test_creation_with_defaults(self):
        ic = InvoiceConfig(id="ic-1", tenant_id="t1", plan_id="p1", amount=1000)
        assert ic.id == "ic-1"
        assert ic.currency == "USD"
        assert ic.status == InvoiceStatus.DRAFT
        assert ic.created_at is not None

    def test_creation_with_all_fields(self):
        future = datetime(2027, 1, 1, tzinfo=timezone.utc)
        ic = InvoiceConfig(
            id="ic-2", tenant_id="t2", plan_id="p2", amount=5000,
            currency="VND", status=InvoiceStatus.SENT, due_date=future,
            line_items=[{"desc": "Pro Plan", "amount": 5000}],
        )
        assert ic.currency == "VND"
        assert ic.status == InvoiceStatus.SENT
        assert len(ic.line_items) == 1

    def test_amount_decimal(self):
        ic = InvoiceConfig(id="ic-3", tenant_id="t", plan_id="p", amount=1500)
        assert ic.amount_decimal == 15.0

    def test_can_send_draft(self):
        ic = InvoiceConfig(id="ic-4", tenant_id="t", plan_id="p", amount=100, status=InvoiceStatus.DRAFT)
        assert ic.can_send is True

    def test_can_send_not_draft(self):
        ic = InvoiceConfig(id="ic-5", tenant_id="t", plan_id="p", amount=100, status=InvoiceStatus.SENT)
        assert ic.can_send is False

    def test_can_void_draft(self):
        ic = InvoiceConfig(id="ic-6", tenant_id="t", plan_id="p", amount=100, status=InvoiceStatus.DRAFT)
        assert ic.can_void is True

    def test_can_void_not_draft_or_sent(self):
        ic = InvoiceConfig(id="ic-7", tenant_id="t", plan_id="p", amount=100, status=InvoiceStatus.PAID)
        assert ic.can_void is False

    def test_to_dict(self):
        ic = InvoiceConfig(id="ic-8", tenant_id="t", plan_id="p", amount=1000)
        d = ic.to_dict()
        assert d["id"] == "ic-8"
        assert d["status"] == "draft"

    def test_from_dict(self):
        data = {
            "id": "ic-9", "tenant_id": "t", "plan_id": "p",
            "amount": 2000, "currency": "EUR", "status": "sent",
        }
        ic = InvoiceConfig.from_dict(data)
        assert ic.currency == "EUR"
        assert ic.status == InvoiceStatus.SENT

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            InvoiceConfig(id="", tenant_id="t", plan_id="p", amount=100)

    def test_validation_error_empty_tenant_id(self):
        with pytest.raises(Exception):
            InvoiceConfig(id="ic-10", tenant_id="", plan_id="p", amount=100)

    def test_validation_error_negative_amount(self):
        with pytest.raises(Exception):
            InvoiceConfig(id="ic-11", tenant_id="t", plan_id="p", amount=-1)

    def test_roundtrip(self):
        original = InvoiceConfig(
            id="rt-ic", tenant_id="t1", plan_id="p1", amount=3000,
            currency="VND", line_items=[{"desc": "item"}],
        )
        d = original.to_dict()
        restored = InvoiceConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.tenant_id == original.tenant_id
        assert restored.amount == original.amount
        assert restored.currency == original.currency


# =============================================================================
# UsageMeter
# =============================================================================

class TestUsageMeter:
    def test_creation_with_defaults(self):
        um = UsageMeter(id="um-1", metric_name=MetricName.API_CALLS)
        assert um.unit_price == 0
        assert um.billing_period == "monthly"

    def test_creation_with_all_fields(self):
        um = UsageMeter(
            id="um-2", metric_name=MetricName.STORAGE_GB, unit_price=50,
            billing_period="annual", threshold_alerts=[50, 80, 100],
        )
        assert um.unit_price == 50
        assert 80 in um.threshold_alerts

    def test_calculate_cost(self):
        um = UsageMeter(id="um-3", metric_name=MetricName.API_CALLS, unit_price=10)
        assert um.calculate_cost(100) == 1000

    def test_calculate_cost_zero(self):
        um = UsageMeter(id="um-4", metric_name=MetricName.API_CALLS, unit_price=0)
        assert um.calculate_cost(100) == 0

    def test_get_alert_level_below(self):
        um = UsageMeter(id="um-5", metric_name=MetricName.API_CALLS, threshold_alerts=[80, 100])
        assert um.get_alert_level(10, 100) is None

    def test_get_alert_level_above(self):
        um = UsageMeter(id="um-6", metric_name=MetricName.API_CALLS, threshold_alerts=[80, 100])
        result = um.get_alert_level(90, 100)
        assert result is not None

    def test_get_alert_level_zero_limit(self):
        um = UsageMeter(id="um-7", metric_name=MetricName.API_CALLS, threshold_alerts=[80])
        assert um.get_alert_level(10, 0) is None

    def test_to_dict(self):
        um = UsageMeter(id="um-8", metric_name=MetricName.USERS, unit_price=100)
        d = um.to_dict()
        assert d["metric_name"] == "users"
        assert d["unit_price"] == 100

    def test_from_dict(self):
        data = {"id": "um-9", "metric_name": "bandwidth_gb", "unit_price": 25}
        um = UsageMeter.from_dict(data)
        assert um.metric_name == MetricName.BANDWIDTH_GB
        assert um.unit_price == 25

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            UsageMeter(id="", metric_name=MetricName.API_CALLS)

    def test_validation_error_negative_unit_price(self):
        with pytest.raises(Exception):
            UsageMeter(id="um-10", metric_name=MetricName.API_CALLS, unit_price=-1)

    def test_roundtrip(self):
        original = UsageMeter(
            id="rt-um", metric_name=MetricName.STORAGE_GB, unit_price=10,
            threshold_alerts=[50, 80],
        )
        d = original.to_dict()
        restored = UsageMeter.from_dict(d)
        assert restored.id == original.id
        assert restored.metric_name == original.metric_name
        assert restored.unit_price == original.unit_price


# =============================================================================
# PaymentGatewayConfig
# =============================================================================

class TestPaymentGatewayConfig:
    def test_creation_with_defaults(self):
        pgc = PaymentGatewayConfig(id="pgc-1", provider=GatewayProvider.STRIPE)
        assert pgc.is_enabled is True
        assert pgc.is_sandbox is True
        assert pgc.currencies == ["USD"]

    def test_creation_with_all_fields(self):
        pgc = PaymentGatewayConfig(
            id="pgc-2", provider=GatewayProvider.PAYPAL,
            api_key_ref="pk_live_xxxxx", webhook_secret="whsec_123",
            currencies=["USD", "EUR", "VND"], capture_mode=CaptureMode.MANUAL,
            is_enabled=False, is_sandbox=False,
        )
        assert len(pgc.currencies) == 3
        assert pgc.is_enabled is False

    def test_masked_api_key_ref(self):
        pgc = PaymentGatewayConfig(id="pgc-3", provider=GatewayProvider.STRIPE, api_key_ref="pk_live_abc123")
        assert pgc.masked_api_key_ref.startswith("****")

    def test_masked_api_key_ref_short(self):
        pgc = PaymentGatewayConfig(id="pgc-4", provider=GatewayProvider.STRIPE, api_key_ref="abcd")
        assert pgc.masked_api_key_ref == "****"

    def test_to_dict_masks_secrets(self):
        pgc = PaymentGatewayConfig(
            id="pgc-5", provider=GatewayProvider.STRIPE,
            api_key_ref="pk_live_xxx", webhook_secret="secret",
        )
        d = pgc.to_dict()
        assert d["webhook_secret"] == "****"
        assert d["api_key_ref"].startswith("****")

    def test_from_dict(self):
        data = {
            "id": "pgc-6", "provider": "adyen", "currencies": ["VND"],
            "capture_mode": "manual", "is_sandbox": False,
        }
        pgc = PaymentGatewayConfig.from_dict(data)
        assert pgc.provider == GatewayProvider.ADYEN
        assert pgc.is_sandbox is False

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            PaymentGatewayConfig(id="", provider=GatewayProvider.STRIPE)

    def test_roundtrip(self):
        original = PaymentGatewayConfig(
            id="rt-pgc", provider=GatewayProvider.STRIPE,
            currencies=["USD", "VND"], is_sandbox=False,
        )
        d = original.to_dict()
        restored = PaymentGatewayConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.provider == original.provider
        assert restored.is_sandbox == original.is_sandbox
