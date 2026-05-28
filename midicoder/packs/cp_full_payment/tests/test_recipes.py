# coding: utf-8
"""
Tests cho CP45 recipes — Payment Gateway Abstraction.
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_payment.recipes import (
    RecipeOutput,
    basic_payment_recipe,
    full_payment_recipe,
)
from midicoder.packs.cp_full_payment.models import (
    PaymentGatewayType,
)


class TestRecipeOutput:
    def test_create(self):
        from midicoder.packs.cp_full_payment.parser import PaymentIR
        output = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=PaymentIR(),
            raw_data={},
        )
        assert output.name == "test"

    def test_to_dict(self):
        from midicoder.packs.cp_full_payment.parser import PaymentIR
        output = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=PaymentIR(),
            raw_data={"key": "value"},
        )
        d = output.to_dict()
        assert d["name"] == "test"
        assert d["raw_data"]["key"] == "value"


class TestBasicPaymentRecipe:
    def test_returns_recipe_output(self):
        result = basic_payment_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        result = basic_payment_recipe()
        assert result.name == "basic_payment_recipe"

    def test_description(self):
        result = basic_payment_recipe()
        assert "Stripe" in result.description or "stripe" in result.description

    def test_has_one_gateway(self):
        result = basic_payment_recipe()
        assert len(result.ir.gateways) == 1

    def test_gateway_type_stripe(self):
        result = basic_payment_recipe()
        assert result.ir.gateways[0].gateway_type == PaymentGatewayType.STRIPE

    def test_default_currency_vnd(self):
        result = basic_payment_recipe()
        assert result.ir.default_currency == "VND"

    def test_enable_idempotency(self):
        result = basic_payment_recipe()
        assert result.ir.enable_idempotency is True

    def test_refunds_disabled(self):
        result = basic_payment_recipe()
        assert result.ir.enable_refunds is False

    def test_webhooks_disabled(self):
        result = basic_payment_recipe()
        assert result.ir.enable_webhooks is False

    def test_audit_enabled(self):
        result = basic_payment_recipe()
        assert result.ir.enable_audit is True


class TestFullPaymentRecipe:
    def test_returns_recipe_output(self):
        result = full_payment_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        result = full_payment_recipe()
        assert result.name == "full_payment_recipe"

    def test_has_three_gateways(self):
        result = full_payment_recipe()
        assert len(result.ir.gateways) == 3

    def test_gateway_types(self):
        result = full_payment_recipe()
        types = {g.gateway_type for g in result.ir.gateways}
        assert PaymentGatewayType.STRIPE in types
        assert PaymentGatewayType.VNPay in types
        assert PaymentGatewayType.MOMO in types

    def test_all_features_enabled(self):
        result = full_payment_recipe()
        assert result.ir.enable_idempotency is True
        assert result.ir.enable_refunds is True
        assert result.ir.enable_webhooks is True
        assert result.ir.enable_audit is True

    def test_max_refund_percentage(self):
        result = full_payment_recipe()
        assert result.ir.max_refund_percentage == 100

    def test_idempotency_ttl(self):
        result = full_payment_recipe()
        assert result.ir.idempotency_ttl_seconds == 3600
