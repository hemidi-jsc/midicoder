# coding: utf-8
"""
Kiểm tra mô-đun parser cho CP40 — Webhook & Outbound Integration Hub.

Bao gồm các tests cho:
- WebhookIR: empty, with data, to_dict/from_dict roundtrip
- parse_subscriptions: từ key 'subscriptions', từ key 'webhooks', empty
- parse_dispatches: từ key 'dispatches', từ key 'deliveries', empty
- parse_to_ir: full data, empty data
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_webhook.parser import (
    WebhookIR,
    parse_dispatches,
    parse_subscriptions,
    parse_to_ir,
)


# ===========================================================================
# Test WebhookIR
# ===========================================================================


class TestWebhookIR:
    """Kiểm tra WebhookIR — tạo, serialize, deserialize."""

    def test_webhook_ir_empty(self):
        ir = WebhookIR()
        assert len(ir.subscriptions) == 0
        assert len(ir.dispatches) == 0
        assert ir.redis_url == ""

    def test_webhook_ir_to_dict_empty(self):
        ir = WebhookIR()
        d = ir.to_dict()
        assert d["subscriptions"] == []
        assert d["dispatches"] == []
        assert d["redis_url"] == ""

    def test_webhook_ir_with_data(self):
        from midicoder.packs.cp_full_webhook.models import (
            WebhookDispatch,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/hook",
            status=WebhookStatus.ACTIVE,
        )
        disp = WebhookDispatch(
            dispatch_id="disp_001",
            subscription_id="wh_001",
            event_type="order.created",
        )
        ir = WebhookIR(
            subscriptions=[sub],
            dispatches=[disp],
            redis_url="redis://localhost:6379/0",
        )
        assert len(ir.subscriptions) == 1
        assert len(ir.dispatches) == 1
        assert ir.redis_url == "redis://localhost:6379/0"

    def test_webhook_ir_to_dict_with_data(self):
        from midicoder.packs.cp_full_webhook.models import (
            WebhookDispatch,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/hook",
            status=WebhookStatus.ACTIVE,
        )
        ir = WebhookIR(subscriptions=[sub], redis_url="redis://localhost:6379/1")
        d = ir.to_dict()
        assert len(d["subscriptions"]) == 1
        assert d["subscriptions"][0]["subscription_id"] == "wh_001"
        assert d["redis_url"] == "redis://localhost:6379/1"

    def test_webhook_ir_from_dict_roundtrip(self):
        from midicoder.packs.cp_full_webhook.models import (
            WebhookDispatch,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_rt",
            event_type="test.event",
            url="https://example.com/rt",
            status=WebhookStatus.ACTIVE,
        )
        disp = WebhookDispatch(
            dispatch_id="disp_rt",
            subscription_id="wh_rt",
            event_type="test.event",
        )
        ir = WebhookIR(
            subscriptions=[sub],
            dispatches=[disp],
            redis_url="redis://localhost:6379/2",
        )
        d = ir.to_dict()
        restored = WebhookIR.from_dict(d)
        assert len(restored.subscriptions) == 1
        assert restored.subscriptions[0].subscription_id == "wh_rt"
        assert len(restored.dispatches) == 1
        assert restored.dispatches[0].dispatch_id == "disp_rt"
        assert restored.redis_url == "redis://localhost:6379/2"

    def test_webhook_ir_from_dict_empty(self):
        restored = WebhookIR.from_dict({})
        assert len(restored.subscriptions) == 0
        assert len(restored.dispatches) == 0
        assert restored.redis_url == ""


# ===========================================================================
# Test parse_subscriptions
# ===========================================================================


class TestParseSubscriptions:
    """Kiểm tra parse_subscriptions — nhiều key, alias, empty."""

    def test_parse_subscriptions_from_subscriptions_key(self):
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                    "url": "https://example.com/hook",
                }
            ]
        }
        result = parse_subscriptions(data)
        assert len(result) == 1
        assert result[0].subscription_id == "wh_001"
        assert result[0].event_type == "order.created"

    def test_parse_subscriptions_from_webhooks_key(self):
        data = {
            "webhooks": [
                {
                    "subscription_id": "wh_002",
                    "event_type": "payment.completed",
                    "url": "https://example.com/pay",
                }
            ]
        }
        result = parse_subscriptions(data)
        assert len(result) == 1
        assert result[0].subscription_id == "wh_002"

    def test_parse_subscriptions_empty(self):
        data = {}
        result = parse_subscriptions(data)
        assert len(result) == 0

    def test_parse_subscriptions_with_hmac_auth(self):
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_hmac",
                    "event_type": "order.created",
                    "url": "https://example.com/hook",
                    "auth_config": {
                        "auth_type": "hmac",
                        "header_name": "X-Webhook-Signature",
                        "secret": "whsec_secret",
                        "algorithm": "sha256",
                    },
                }
            ]
        }
        result = parse_subscriptions(data)
        assert len(result) == 1
        from midicoder.packs.cp_full_webhook.models import WebhookAuthType
        assert result[0].auth_config.auth_type == WebhookAuthType.HMAC
        assert result[0].auth_config.header_name == "X-Webhook-Signature"
        assert result[0].auth_config.secret == "whsec_secret"

    def test_parse_subscriptions_with_auth_alias_key(self):
        """Kiểm tra alias key 'auth' thay cho 'auth_config'."""
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_auth_alias",
                    "event_type": "test.event",
                    "url": "https://example.com/hook",
                    "auth": {
                        "auth_type": "bearer",
                        "secret": "tok_123",
                    },
                }
            ]
        }
        result = parse_subscriptions(data)
        assert len(result) == 1
        from midicoder.packs.cp_full_webhook.models import WebhookAuthType
        assert result[0].auth_config.auth_type == WebhookAuthType.BEARER

    def test_parse_subscriptions_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'subscription_id'."""
        data = {
            "subscriptions": [
                {
                    "id": "wh_alias_id",
                    "event_type": "test.event",
                    "url": "https://example.com/hook",
                }
            ]
        }
        result = parse_subscriptions(data)
        assert result[0].subscription_id == "wh_alias_id"

    def test_parse_subscriptions_with_event_alias(self):
        """Kiểm tra alias key 'event' thay cho 'event_type'."""
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_evt",
                    "event": "order.updated",
                    "url": "https://example.com/hook",
                }
            ]
        }
        result = parse_subscriptions(data)
        assert result[0].event_type == "order.updated"

    def test_parse_subscriptions_multiple(self):
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                    "url": "https://example.com/hook1",
                },
                {
                    "subscription_id": "wh_002",
                    "event_type": "payment.completed",
                    "url": "https://example.com/hook2",
                },
            ]
        }
        result = parse_subscriptions(data)
        assert len(result) == 2
        assert result[0].subscription_id == "wh_001"
        assert result[1].subscription_id == "wh_002"


# ===========================================================================
# Test parse_dispatches
# ===========================================================================


class TestParseDispatches:
    """Kiểm tra parse_dispatches — nhiều key, alias, empty."""

    def test_parse_dispatches_from_dispatches_key(self):
        data = {
            "dispatches": [
                {
                    "dispatch_id": "disp_001",
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                    "payload": {"order_id": "123"},
                }
            ]
        }
        result = parse_dispatches(data)
        assert len(result) == 1
        assert result[0].dispatch_id == "disp_001"
        assert result[0].subscription_id == "wh_001"

    def test_parse_dispatches_from_deliveries_key(self):
        data = {
            "deliveries": [
                {
                    "dispatch_id": "disp_002",
                    "subscription_id": "wh_002",
                    "event_type": "payment.completed",
                }
            ]
        }
        result = parse_dispatches(data)
        assert len(result) == 1
        assert result[0].dispatch_id == "disp_002"

    def test_parse_dispatches_empty(self):
        data = {}
        result = parse_dispatches(data)
        assert len(result) == 0

    def test_parse_dispatches_with_status(self):
        from midicoder.packs.cp_full_webhook.models import DispatchStatus
        data = {
            "dispatches": [
                {
                    "dispatch_id": "disp_del",
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                    "status": "delivered",
                    "attempts": 2,
                }
            ]
        }
        result = parse_dispatches(data)
        assert result[0].status == DispatchStatus.DELIVERED
        assert result[0].attempts == 2

    def test_parse_dispatches_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'dispatch_id'."""
        data = {
            "dispatches": [
                {
                    "id": "disp_alias",
                    "subscription_id": "wh_001",
                    "event_type": "test.event",
                }
            ]
        }
        result = parse_dispatches(data)
        assert result[0].dispatch_id == "disp_alias"


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Kiểm tra parse_to_ir — full data, empty data."""

    def test_parse_to_ir_full_data(self):
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                    "url": "https://example.com/hook",
                }
            ],
            "dispatches": [
                {
                    "dispatch_id": "disp_001",
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                }
            ],
            "redis_url": "redis://localhost:6379/0",
        }
        ir = parse_to_ir(data)
        assert len(ir.subscriptions) == 1
        assert len(ir.dispatches) == 1
        assert ir.redis_url == "redis://localhost:6379/0"
        assert ir.subscriptions[0].subscription_id == "wh_001"
        assert ir.dispatches[0].dispatch_id == "disp_001"

    def test_parse_to_ir_empty_data(self):
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.subscriptions) == 0
        assert len(ir.dispatches) == 0
        assert ir.redis_url == ""

    def test_parse_to_ir_only_subscriptions(self):
        data = {
            "subscriptions": [
                {
                    "subscription_id": "wh_only",
                    "event_type": "test.event",
                    "url": "https://example.com/hook",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.subscriptions) == 1
        assert len(ir.dispatches) == 0

    def test_parse_to_ir_only_dispatches(self):
        data = {
            "dispatches": [
                {
                    "dispatch_id": "disp_only",
                    "subscription_id": "wh_001",
                    "event_type": "order.created",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.subscriptions) == 0
        assert len(ir.dispatches) == 1
        assert ir.dispatches[0].dispatch_id == "disp_only"

    def test_parse_to_ir_webhooks_alias(self):
        """Kiểm tra parse_to_ir sử dụng alias 'webhooks' cho subscriptions."""
        data = {
            "webhooks": [
                {
                    "subscription_id": "wh_alias",
                    "event_type": "order.created",
                    "url": "https://example.com/hook",
                }
            ],
            "deliveries": [
                {
                    "dispatch_id": "del_001",
                    "subscription_id": "wh_alias",
                    "event_type": "order.created",
                }
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.subscriptions) == 1
        assert len(ir.dispatches) == 1
