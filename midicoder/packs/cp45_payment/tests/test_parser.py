# coding: utf-8
"""
Tests cho CP45 parser — Payment Gateway Abstraction.
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp45_payment.parser import (
    PaymentIR,
    parse_gateways,
    parse_payment_config,
    parse_payment_methods,
    parse_to_ir,
)
from midicoder.packs.cp45_payment.models import (
    PaymentGatewayType,
    PaymentMethodType,
)


class TestParseGateways:
    def test_parse_empty(self):
        gateways = parse_gateways({})
        assert gateways == []

    def test_parse_with_gateways_key(self):
        data = {"gateways": [{"config_id": "g1", "gateway_type": "stripe"}]}
        gateways = parse_gateways(data)
        assert len(gateways) == 1
        assert gateways[0].config_id == "g1"

    def test_parse_with_payment_gateways_key(self):
        data = {"payment_gateways": [{"config_id": "g1", "gateway_type": "vnpay"}]}
        gateways = parse_gateways(data)
        assert len(gateways) == 1
        assert gateways[0].gateway_type == PaymentGatewayType.VNPay

    def test_parse_multiple_gateways(self):
        data = {
            "gateways": [
                {"config_id": "g1", "gateway_type": "stripe", "is_sandbox": True},
                {"config_id": "g2", "gateway_type": "vnpay", "is_sandbox": False},
                {"config_id": "g3", "gateway_type": "momo"},
            ]
        }
        gateways = parse_gateways(data)
        assert len(gateways) == 3


class TestParsePaymentMethods:
    def test_parse_empty(self):
        methods = parse_payment_methods({})
        assert methods == []

    def test_parse_with_payment_methods_key(self):
        data = {"payment_methods": [{"method_id": "m1", "user_id": "u1", "method_type": "credit_card"}]}
        methods = parse_payment_methods(data)
        assert len(methods) == 1
        assert methods[0].method_id == "m1"

    def test_parse_with_methods_key(self):
        data = {"methods": [{"method_id": "m1", "user_id": "u1", "method_type": "ewallet"}]}
        methods = parse_payment_methods(data)
        assert len(methods) == 1
        assert methods[0].method_type == PaymentMethodType.EWALLET


class TestParsePaymentConfig:
    def test_parse_defaults(self):
        config = parse_payment_config({})
        assert config["default_gateway"] == "stripe"
        assert config["default_currency"] == "VND"
        assert config["enable_idempotency"] is True
        assert config["enable_refunds"] is True
        assert config["enable_webhooks"] is True
        assert config["enable_audit"] is True

    def test_parse_custom(self):
        data = {
            "default_gateway": "vnpay",
            "default_currency": "USD",
            "enable_idempotency": False,
            "enable_refunds": False,
            "max_refund_percentage": 50,
        }
        config = parse_payment_config(data)
        assert config["default_gateway"] == "vnpay"
        assert config["default_currency"] == "USD"
        assert config["enable_idempotency"] is False
        assert config["enable_refunds"] is False
        assert config["max_refund_percentage"] == 50


class TestParseToIR:
    def test_parse_empty(self):
        ir = parse_to_ir({})
        assert ir.gateways == []
        assert ir.default_gateway == PaymentGatewayType.STRIPE
        assert ir.default_currency == "VND"

    def test_parse_full(self):
        data = {
            "gateways": [
                {"config_id": "g1", "gateway_type": "stripe"},
                {"config_id": "g2", "gateway_type": "vnpay"},
            ],
            "payment_methods": [
                {"method_id": "m1", "user_id": "u1", "method_type": "credit_card"},
            ],
            "default_gateway": "stripe",
            "default_currency": "EUR",
            "enable_idempotency": True,
            "enable_refunds": True,
            "enable_webhooks": True,
        }
        ir = parse_to_ir(data)
        assert len(ir.gateways) == 2
        assert len(ir.payment_methods) == 1
        assert ir.default_currency == "EUR"
        assert ir.enable_idempotency is True


class TestPaymentIR:
    def test_create_default(self):
        ir = PaymentIR()
        assert ir.default_gateway == PaymentGatewayType.STRIPE
        assert ir.enable_idempotency is True
        assert ir.enable_refunds is True

    def test_to_dict(self):
        ir = PaymentIR(
            default_gateway=PaymentGatewayType.VNPay,
            default_currency="USD",
            enable_idempotency=False,
        )
        d = ir.to_dict()
        assert d["default_gateway"] == "vnpay"
        assert d["default_currency"] == "USD"
        assert d["enable_idempotency"] is False

    def test_from_dict(self):
        data = {
            "default_gateway": "momo",
            "default_currency": "JPY",
            "enable_webhooks": False,
            "max_refund_percentage": 75,
        }
        ir = PaymentIR.from_dict(data)
        assert ir.default_gateway == PaymentGatewayType.MOMO
        assert ir.default_currency == "JPY"
        assert ir.enable_webhooks is False
        assert ir.max_refund_percentage == 75

    def test_roundtrip(self):
        ir = PaymentIR(
            default_gateway=PaymentGatewayType.STRIPE,
            default_currency="VND",
            enable_idempotency=True,
            enable_refunds=True,
            enable_webhooks=True,
            max_refund_percentage=100,
        )
        restored = PaymentIR.from_dict(ir.to_dict())
        assert restored.default_gateway == ir.default_gateway
        assert restored.default_currency == ir.default_currency
