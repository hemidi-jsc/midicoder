# coding: utf-8
"""
Tests cho CP45 models — Payment Gateway Abstraction.

Bao phủ:
- TestCP45ErrorCodes: 10 error codes
- TestPaymentGatewayType: 3 providers
- TestPaymentMethodType: 4 loại
- TestPaymentMethodStatus: 3 trạng thái
- TestPaymentStatus: 6 trạng thái (state machine)
- TestRefundStatus: 4 trạng thái
- TestPaymentGatewayConfig: tạo, validate, to_dict, from_dict
- TestPaymentMethod: tạo, validate, is_usable, to_dict, from_dict
- TestPaymentTransaction: tạo, validate, amount_decimal, can_refund, can_cancel
- TestPaymentRefund: tạo, validate, amount_decimal, to_dict, from_dict
- TestPaymentEngine: toàn bộ engine methods

Tổng: ~110 tests
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from midicoder.emitters.core.cp45_payment.models import (
    PaymentEngine,
    PaymentGatewayConfig,
    PaymentGatewayType,
    PaymentMethod,
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    RefundStatus,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Error Codes
# ===========================================================================


class TestCP45ErrorCodes:
    """Test 10 error codes của CP45."""

    def test_payment_gateway_not_found_code(self):
        assert ErrorCode.CP45_PAYMENT_GATEWAY_NOT_FOUND.value == "MDC-CP45-001"

    def test_payment_method_not_found_code(self):
        assert ErrorCode.CP45_PAYMENT_METHOD_NOT_FOUND.value == "MDC-CP45-002"

    def test_payment_processing_failed_code(self):
        assert ErrorCode.CP45_PAYMENT_PROCESSING_FAILED.value == "MDC-CP45-003"

    def test_invalid_payment_amount_code(self):
        assert ErrorCode.CP45_INVALID_PAYMENT_AMOUNT.value == "MDC-CP45-004"

    def test_payment_idempotency_conflict_code(self):
        assert ErrorCode.CP45_PAYMENT_IDEMPOTENCY_CONFLICT.value == "MDC-CP45-005"

    def test_refund_amount_exceeds_original_code(self):
        assert ErrorCode.CP45_REFUND_AMOUNT_EXCEEDS_ORIGINAL.value == "MDC-CP45-006"

    def test_refund_not_allowed_code(self):
        assert ErrorCode.CP45_REFUND_NOT_ALLOWED.value == "MDC-CP45-007"

    def test_webhook_signature_invalid_code(self):
        assert ErrorCode.CP45_WEBHOOK_SIGNATURE_INVALID.value == "MDC-CP45-008"

    def test_payment_gateway_timeout_code(self):
        assert ErrorCode.CP45_PAYMENT_GATEWAY_TIMEOUT.value == "MDC-CP45-009"

    def test_payment_method_expired_code(self):
        assert ErrorCode.CP45_PAYMENT_METHOD_EXPIRED.value == "MDC-CP45-010"


# ===========================================================================
# Enums
# ===========================================================================


class TestPaymentGatewayType:
    def test_stripe(self):
        assert PaymentGatewayType.STRIPE.value == "stripe"

    def test_vnpay(self):
        assert PaymentGatewayType.VNPay.value == "vnpay"

    def test_momo(self):
        assert PaymentGatewayType.MOMO.value == "momo"


class TestPaymentMethodType:
    def test_credit_card(self):
        assert PaymentMethodType.CREDIT_CARD.value == "credit_card"

    def test_bank_transfer(self):
        assert PaymentMethodType.BANK_TRANSFER.value == "bank_transfer"

    def test_ewallet(self):
        assert PaymentMethodType.EWALLET.value == "ewallet"

    def test_qr_code(self):
        assert PaymentMethodType.QR_CODE.value == "qr_code"


class TestPaymentMethodStatus:
    def test_active(self):
        assert PaymentMethodStatus.ACTIVE.value == "active"

    def test_expired(self):
        assert PaymentMethodStatus.EXPIRED.value == "expired"

    def test_suspended(self):
        assert PaymentMethodStatus.SUSPENDED.value == "suspended"


class TestPaymentStatus:
    def test_pending(self):
        assert PaymentStatus.PENDING.value == "pending"

    def test_processing(self):
        assert PaymentStatus.PROCESSING.value == "processing"

    def test_completed(self):
        assert PaymentStatus.COMPLETED.value == "completed"

    def test_failed(self):
        assert PaymentStatus.FAILED.value == "failed"

    def test_refunded(self):
        assert PaymentStatus.REFUNDED.value == "refunded"

    def test_cancelled(self):
        assert PaymentStatus.CANCELLED.value == "cancelled"


class TestRefundStatus:
    def test_pending(self):
        assert RefundStatus.PENDING.value == "pending"

    def test_processing(self):
        assert RefundStatus.PROCESSING.value == "processing"

    def test_completed(self):
        assert RefundStatus.COMPLETED.value == "completed"

    def test_failed(self):
        assert RefundStatus.FAILED.value == "failed"


# ===========================================================================
# PaymentGatewayConfig
# ===========================================================================


class TestPaymentGatewayConfig:
    def test_create_valid_config(self):
        config = PaymentGatewayConfig(
            config_id="stripe_prod",
            gateway_type=PaymentGatewayType.STRIPE,
            api_key="sk_test_1234",
        )
        assert config.config_id == "stripe_prod"
        assert config.is_sandbox is True
        assert config.is_enabled is True

    def test_empty_config_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentGatewayConfig(config_id="", gateway_type=PaymentGatewayType.STRIPE)

    def test_invalid_timeout_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentGatewayConfig(
                config_id="test",
                gateway_type=PaymentGatewayType.STRIPE,
                timeout_seconds=0,
            )

    def test_masked_api_key_short(self):
        config = PaymentGatewayConfig(
            config_id="test",
            gateway_type=PaymentGatewayType.STRIPE,
            api_key="abc",
        )
        assert config.masked_api_key == "****"

    def test_masked_api_key_long(self):
        config = PaymentGatewayConfig(
            config_id="test",
            gateway_type=PaymentGatewayType.STRIPE,
            api_key="sk_test_1234567890",
        )
        assert config.masked_api_key == "****7890"
        assert "sk_test" not in config.masked_api_key

    def test_to_dict(self):
        config = PaymentGatewayConfig(
            config_id="stripe_test",
            gateway_type=PaymentGatewayType.VNPay,
            api_key="sk_test_key123",
            is_sandbox=False,
        )
        d = config.to_dict()
        assert d["config_id"] == "stripe_test"
        assert d["gateway_type"] == "vnpay"
        assert d["is_sandbox"] is False
        assert d["api_secret"] == "****"

    def test_from_dict(self):
        data = {
            "config_id": "momo_test",
            "gateway_type": "momo",
            "timeout_seconds": 60,
            "is_enabled": False,
        }
        config = PaymentGatewayConfig.from_dict(data)
        assert config.gateway_type == PaymentGatewayType.MOMO
        assert config.timeout_seconds == 60
        assert config.is_enabled is False

    def test_roundtrip(self):
        config = PaymentGatewayConfig(
            config_id="test_roundtrip",
            gateway_type=PaymentGatewayType.STRIPE,
            api_key="sk_test_key",
            is_sandbox=True,
        )
        restored = PaymentGatewayConfig.from_dict(config.to_dict())
        assert restored.config_id == config.config_id
        assert restored.gateway_type == config.gateway_type


# ===========================================================================
# PaymentMethod
# ===========================================================================


class TestPaymentMethod:
    def test_create_valid_method(self):
        method = PaymentMethod(
            method_id="pm_001",
            user_id="user_001",
            method_type=PaymentMethodType.CREDIT_CARD,
            last4="4242",
        )
        assert method.method_id == "pm_001"
        assert method.status == PaymentMethodStatus.ACTIVE
        assert method.is_default is False
        assert method.is_usable is True

    def test_empty_method_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentMethod(method_id="", user_id="user_001", method_type=PaymentMethodType.CREDIT_CARD)

    def test_empty_user_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentMethod(method_id="pm_001", user_id="", method_type=PaymentMethodType.CREDIT_CARD)

    def test_is_usable_when_active(self):
        method = PaymentMethod(
            method_id="pm_001", user_id="u1",
            method_type=PaymentMethodType.CREDIT_CARD,
            status=PaymentMethodStatus.ACTIVE,
        )
        assert method.is_usable is True

    def test_is_usable_when_expired(self):
        method = PaymentMethod(
            method_id="pm_001", user_id="u1",
            method_type=PaymentMethodType.CREDIT_CARD,
            status=PaymentMethodStatus.EXPIRED,
        )
        assert method.is_usable is False

    def test_is_usable_when_suspended(self):
        method = PaymentMethod(
            method_id="pm_001", user_id="u1",
            method_type=PaymentMethodType.CREDIT_CARD,
            status=PaymentMethodStatus.SUSPENDED,
        )
        assert method.is_usable is False

    def test_to_dict(self):
        method = PaymentMethod(
            method_id="pm_001",
            user_id="user_001",
            method_type=PaymentMethodType.EWALLET,
            is_default=True,
        )
        d = method.to_dict()
        assert d["method_type"] == "ewallet"
        assert d["is_default"] is True
        assert d["status"] == "active"

    def test_from_dict(self):
        data = {
            "method_id": "pm_001",
            "user_id": "user_001",
            "method_type": "bank_transfer",
            "gateway_type": "vnpay",
            "is_default": True,
        }
        method = PaymentMethod.from_dict(data)
        assert method.method_type == PaymentMethodType.BANK_TRANSFER
        assert method.gateway_type == PaymentGatewayType.VNPay

    def test_roundtrip(self):
        method = PaymentMethod(
            method_id="pm_rt", user_id="u1",
            method_type=PaymentMethodType.QR_CODE,
            gateway_type=PaymentGatewayType.MOMO,
            is_default=True,
            last4="9999",
        )
        restored = PaymentMethod.from_dict(method.to_dict())
        assert restored.method_id == method.method_id
        assert restored.method_type == method.method_type


# ===========================================================================
# PaymentTransaction
# ===========================================================================


class TestPaymentTransaction:
    def test_create_valid_transaction(self):
        tx = PaymentTransaction(
            transaction_id="tx_001",
            user_id="user_001",
            payment_method_id="pm_001",
            amount=10000,
            currency="VND",
        )
        assert tx.transaction_id == "tx_001"
        assert tx.status == PaymentStatus.PENDING
        assert tx.amount_decimal == 100.0

    def test_empty_transaction_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentTransaction(transaction_id="", user_id="u1", payment_method_id="pm1", amount=100)

    def test_negative_amount_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentTransaction(
                transaction_id="tx_neg",
                user_id="u1",
                payment_method_id="pm1",
                amount=-100,
            )

    def test_zero_amount_is_valid(self):
        tx = PaymentTransaction(
            transaction_id="tx_zero", user_id="u1",
            payment_method_id="pm1", amount=0,
        )
        assert tx.amount == 0

    def test_can_refund_when_completed(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.COMPLETED,
        )
        assert tx.can_refund is True

    def test_can_refund_when_processing(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.PROCESSING,
        )
        assert tx.can_refund is True

    def test_cannot_refund_when_failed(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.FAILED,
        )
        assert tx.can_refund is False

    def test_cannot_refund_when_refunded(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.REFUNDED,
        )
        assert tx.can_refund is False

    def test_can_cancel_when_pending(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.PENDING,
        )
        assert tx.can_cancel is True

    def test_cannot_cancel_when_completed(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=100,
            status=PaymentStatus.COMPLETED,
        )
        assert tx.can_cancel is False

    def test_to_dict(self):
        tx = PaymentTransaction(
            transaction_id="tx_001", user_id="u1",
            payment_method_id="pm1", amount=50000,
            currency="USD", idempotency_key="idem_123",
        )
        d = tx.to_dict()
        assert d["amount"] == 50000
        assert d["currency"] == "USD"
        assert d["idempotency_key"] == "idem_123"
        assert d["gateway_type"] == "stripe"

    def test_from_dict(self):
        data = {
            "transaction_id": "tx_from",
            "user_id": "u1",
            "amount": 10000,
            "currency": "EUR",
            "status": "completed",
            "gateway_type": "vnpay",
        }
        tx = PaymentTransaction.from_dict(data)
        assert tx.amount == 10000
        assert tx.currency == "EUR"
        assert tx.status == PaymentStatus.COMPLETED
        assert tx.gateway_type == PaymentGatewayType.VNPay


# ===========================================================================
# PaymentRefund
# ===========================================================================


class TestPaymentRefund:
    def test_create_valid_refund(self):
        refund = PaymentRefund(
            refund_id="rf_001",
            transaction_id="tx_001",
            user_id="user_001",
            amount=5000,
            reason="Khách hàng yêu cầu",
        )
        assert refund.status == RefundStatus.PENDING
        assert refund.amount_decimal == 50.0

    def test_empty_refund_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentRefund(refund_id="", transaction_id="tx1", user_id="u1", amount=100)

    def test_empty_transaction_id_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentRefund(refund_id="rf_001", transaction_id="", user_id="u1", amount=100)

    def test_negative_amount_raises_error(self):
        with pytest.raises(MidicoderError):
            PaymentRefund(refund_id="rf_001", transaction_id="tx1", user_id="u1", amount=-50)

    def test_to_dict(self):
        refund = PaymentRefund(
            refund_id="rf_001", transaction_id="tx_001",
            user_id="u1", amount=10000, currency="USD",
            reason="Sai đơn hàng",
        )
        d = refund.to_dict()
        assert d["amount"] == 10000
        assert d["currency"] == "USD"
        assert d["reason"] == "Sai đơn hàng"

    def test_from_dict(self):
        data = {
            "refund_id": "rf_from",
            "transaction_id": "tx_001",
            "user_id": "u1",
            "amount": 5000,
            "status": "completed",
        }
        refund = PaymentRefund.from_dict(data)
        assert refund.amount == 5000
        assert refund.status == RefundStatus.COMPLETED


# ===========================================================================
# PaymentEngine
# ===========================================================================


class TestPaymentEngine:
    def test_create_engine(self):
        engine = PaymentEngine()
        assert engine.gateways == {}
        assert engine.methods == {}
        assert engine.transactions == {}
        assert engine.refunds == {}
        assert engine.idempotency_keys == {}

    # -- Gateway Management --
    def test_register_gateway(self):
        engine = PaymentEngine()
        config = PaymentGatewayConfig(config_id="stripe", gateway_type=PaymentGatewayType.STRIPE)
        result = engine.register_gateway(config)
        assert result.config_id == "stripe"
        assert "stripe" in engine.gateways

    def test_get_gateway(self):
        engine = PaymentEngine()
        config = PaymentGatewayConfig(config_id="vnpay", gateway_type=PaymentGatewayType.VNPay)
        engine.register_gateway(config)
        result = engine.get_gateway("vnpay")
        assert result.gateway_type == PaymentGatewayType.VNPay

    def test_get_gateway_not_found(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.get_gateway("nonexistent")

    def test_get_enabled_gateways(self):
        engine = PaymentEngine()
        engine.register_gateway(PaymentGatewayConfig(config_id="s1", gateway_type=PaymentGatewayType.STRIPE, is_enabled=True))
        engine.register_gateway(PaymentGatewayConfig(config_id="s2", gateway_type=PaymentGatewayType.VNPay, is_enabled=False))
        enabled = engine.get_enabled_gateways()
        assert len(enabled) == 1

    # -- Payment Method Management --
    def test_add_payment_method(self):
        engine = PaymentEngine()
        method = PaymentMethod(method_id="pm_001", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD)
        engine.add_payment_method(method)
        assert "pm_001" in engine.methods

    def test_get_payment_method(self):
        engine = PaymentEngine()
        method = PaymentMethod(method_id="pm_001", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD)
        engine.add_payment_method(method)
        result = engine.get_payment_method("pm_001")
        assert result.method_id == "pm_001"

    def test_get_payment_method_not_found(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.get_payment_method("nonexistent")

    def test_get_user_payment_methods(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD))
        engine.add_payment_method(PaymentMethod(method_id="pm2", user_id="u1", method_type=PaymentMethodType.EWALLET))
        engine.add_payment_method(PaymentMethod(method_id="pm3", user_id="u2", method_type=PaymentMethodType.CREDIT_CARD))
        methods = engine.get_user_payment_methods("u1")
        assert len(methods) == 2

    def test_get_default_payment_method(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        default = engine.get_default_payment_method("u1")
        assert default.method_id == "pm1"

    def test_get_default_payment_method_none(self):
        engine = PaymentEngine()
        default = engine.get_default_payment_method("u1")
        assert default is None

    def test_set_default_payment_method(self):
        engine = PaymentEngine()
        pm1 = PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True)
        pm2 = PaymentMethod(method_id="pm2", user_id="u1", method_type=PaymentMethodType.EWALLET)
        engine.add_payment_method(pm1)
        engine.add_payment_method(pm2)
        engine.set_default_payment_method("u1", "pm2")
        assert pm2.is_default is True
        assert pm1.is_default is False

    def test_suspend_payment_method(self):
        engine = PaymentEngine()
        method = PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD)
        engine.add_payment_method(method)
        result = engine.suspend_payment_method("pm1")
        assert result.status == PaymentMethodStatus.SUSPENDED

    # -- Payment Processing --
    def test_process_payment_success(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        tx = engine.process_payment("u1", 10000, "VND")
        assert tx.amount == 10000
        assert tx.status == PaymentStatus.COMPLETED
        assert tx.gateway_provider_ref

    def test_process_payment_zero_amount_fails(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.process_payment("u1", 0, "VND")

    def test_process_payment_negative_amount_fails(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.process_payment("u1", -100, "VND")

    def test_process_payment_idempotency_conflict(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        engine.process_payment("u1", 100, "VND", idempotency_key="idem_1")
        with pytest.raises(MidicoderError):
            engine.process_payment("u1", 100, "VND", idempotency_key="idem_1")

    def test_process_payment_with_idempotency_key(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        tx = engine.process_payment("u1", 100, "VND", idempotency_key="idem_1")
        assert "idem_1" in engine.idempotency_keys
        assert engine.idempotency_keys["idem_1"] == tx.transaction_id

    def test_process_payment_no_default_method_fails(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.process_payment("u1", 100, "VND")

    def test_process_payment_method_expired_fails(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, status=PaymentMethodStatus.EXPIRED, is_default=True))
        with pytest.raises(MidicoderError):
            engine.process_payment("u1", 100, "VND")

    def test_get_transaction(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        tx = engine.process_payment("u1", 100, "VND")
        result = engine.get_transaction(tx.transaction_id)
        assert result.transaction_id == tx.transaction_id

    def test_get_user_transactions(self):
        engine = PaymentEngine()
        engine.add_payment_method(PaymentMethod(method_id="pm1", user_id="u1", method_type=PaymentMethodType.CREDIT_CARD, is_default=True))
        engine.process_payment("u1", 100, "VND")
        engine.process_payment("u1", 200, "VND")
        txs = engine.get_user_transactions("u1")
        assert len(txs) == 2

    def test_cancel_payment(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=100, status=PaymentStatus.PENDING)
        engine.transactions["tx_001"] = tx
        result = engine.cancel_payment("tx_001")
        assert result.status == PaymentStatus.CANCELLED

    def test_cancel_completed_payment_fails(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=100, status=PaymentStatus.COMPLETED)
        engine.transactions["tx_001"] = tx
        with pytest.raises(MidicoderError):
            engine.cancel_payment("tx_001")

    # -- Refund Processing --
    def test_create_refund_full(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=10000, status=PaymentStatus.COMPLETED)
        engine.transactions["tx_001"] = tx
        refund = engine.create_refund("tx_001")
        assert refund.amount == 10000
        assert refund.status == RefundStatus.COMPLETED
        assert tx.status == PaymentStatus.REFUNDED

    def test_create_refund_partial(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=10000, status=PaymentStatus.COMPLETED)
        engine.transactions["tx_001"] = tx
        refund = engine.create_refund("tx_001", amount=5000)
        assert refund.amount == 5000
        assert tx.status == PaymentStatus.COMPLETED  # không đổi vì partial refund

    def test_create_refund_exceeds_original_fails(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=10000, status=PaymentStatus.COMPLETED)
        engine.transactions["tx_001"] = tx
        with pytest.raises(MidicoderError):
            engine.create_refund("tx_001", amount=20000)

    def test_create_refund_on_failed_transaction_fails(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=10000, status=PaymentStatus.FAILED)
        engine.transactions["tx_001"] = tx
        with pytest.raises(MidicoderError):
            engine.create_refund("tx_001")

    def test_get_refund(self):
        engine = PaymentEngine()
        refund = PaymentRefund(refund_id="rf_001", transaction_id="tx_001", user_id="u1", amount=100)
        engine.refunds["rf_001"] = refund
        result = engine.get_refund("rf_001")
        assert result.refund_id == "rf_001"

    def test_get_transaction_refunds(self):
        engine = PaymentEngine()
        engine.refunds["rf1"] = PaymentRefund(refund_id="rf1", transaction_id="tx_001", user_id="u1", amount=100)
        engine.refunds["rf2"] = PaymentRefund(refund_id="rf2", transaction_id="tx_001", user_id="u1", amount=50)
        refunds = engine.get_transaction_refunds("tx_001")
        assert len(refunds) == 2

    # -- Webhook --
    def test_verify_webhook_signature_valid(self):
        engine = PaymentEngine()
        result = engine.verify_webhook_signature(PaymentGatewayType.STRIPE, "payload", "sig_123", "ts_123")
        assert result is True

    def test_verify_webhook_signature_empty_fails(self):
        engine = PaymentEngine()
        with pytest.raises(MidicoderError):
            engine.verify_webhook_signature(PaymentGatewayType.STRIPE, "payload", "", "ts_123")

    def test_handle_webhook_payment_succeeded(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=100, status=PaymentStatus.PROCESSING)
        engine.transactions["tx_001"] = tx
        result = engine.handle_webhook(PaymentGatewayType.STRIPE, "payment.succeeded", {"transaction_id": "tx_001"})
        assert result.status == PaymentStatus.COMPLETED

    def test_handle_webhook_payment_failed(self):
        engine = PaymentEngine()
        tx = PaymentTransaction(transaction_id="tx_001", user_id="u1", payment_method_id="pm1", amount=100, status=PaymentStatus.PROCESSING)
        engine.transactions["tx_001"] = tx
        result = engine.handle_webhook(PaymentGatewayType.STRIPE, "payment.failed", {"transaction_id": "tx_001"})
        assert result.status == PaymentStatus.FAILED

    def test_handle_webhook_refund_completed(self):
        engine = PaymentEngine()
        refund = PaymentRefund(refund_id="rf_001", transaction_id="tx_001", user_id="u1", amount=100, status=RefundStatus.PROCESSING)
        engine.refunds["rf_001"] = refund
        result = engine.handle_webhook(PaymentGatewayType.STRIPE, "refund.completed", {"refund_id": "rf_001"})
        assert result.status == RefundStatus.COMPLETED

    # -- Statistics --
    def test_get_user_total_spent(self):
        engine = PaymentEngine()
        engine.transactions["tx1"] = PaymentTransaction(transaction_id="tx1", user_id="u1", payment_method_id="pm1", amount=10000, status=PaymentStatus.COMPLETED)
        engine.transactions["tx2"] = PaymentTransaction(transaction_id="tx2", user_id="u1", payment_method_id="pm1", amount=5000, status=PaymentStatus.COMPLETED)
        engine.transactions["tx3"] = PaymentTransaction(transaction_id="tx3", user_id="u1", payment_method_id="pm1", amount=3000, status=PaymentStatus.FAILED)
        total = engine.get_user_total_spent("u1")
        assert total == 15000

    def test_get_user_total_refunded(self):
        engine = PaymentEngine()
        engine.refunds["rf1"] = PaymentRefund(refund_id="rf1", transaction_id="tx1", user_id="u1", amount=5000, status=RefundStatus.COMPLETED)
        total = engine.get_user_total_refunded("u1")
        assert total == 5000
