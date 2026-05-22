# coding: utf-8
"""
Kiểm tra mô-đun models cho CP40 — Webhook & Outbound Integration Hub.

Bao gồm các tests cho:
- Enums: WebhookAuthType, WebhookStatus, DispatchStatus
- WebhookAuthConfig: tạo, validate, to_dict/from_dict
- WebhookSubscription: tạo, validate URL/method, to_dict/from_dict
- WebhookDispatch: tạo, to_dict/from_dict
- WebhookDeliveryAttempt: tạo, to_dict/from_dict
- RetryPolicy: get_delay (exponential backoff), should_retry
- WebhookDispatcher: subscribe, dispatch, HMAC, headers
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP40
# ===========================================================================


class TestCP40ErrorCodes:
    """Kiểm tra các mã lỗi CP40 đã được định nghĩa đúng."""

    def test_cp40_subscription_not_found_code(self):
        assert ErrorCode.CP40_WEBHOOK_SUBSCRIPTION_NOT_FOUND == "MDC-CP40-001"

    def test_cp40_duplicate_subscription_code(self):
        assert ErrorCode.CP40_WEBHOOK_DUPLICATE_SUBSCRIPTION == "MDC-CP40-002"

    def test_cp40_dispatch_failed_code(self):
        assert ErrorCode.CP40_WEBHOOK_DISPATCH_FAILED == "MDC-CP40-003"

    def test_cp40_invalid_url_code(self):
        assert ErrorCode.CP40_WEBHOOK_INVALID_URL == "MDC-CP40-004"

    def test_cp40_auth_config_invalid_code(self):
        assert ErrorCode.CP40_WEBHOOK_AUTH_CONFIG_INVALID == "MDC-CP40-005"


# ===========================================================================
# Test WebhookAuthType Enum
# ===========================================================================


class TestWebhookAuthType:
    """Kiểm tra các giá trị của enum WebhookAuthType."""

    def test_auth_type_none_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookAuthType
        assert WebhookAuthType.NONE.value == "none"

    def test_auth_type_bearer_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookAuthType
        assert WebhookAuthType.BEARER.value == "bearer"

    def test_auth_type_basic_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookAuthType
        assert WebhookAuthType.BASIC.value == "basic"

    def test_auth_type_hmac_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookAuthType
        assert WebhookAuthType.HMAC.value == "hmac"

    def test_auth_type_from_string(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookAuthType
        assert WebhookAuthType("hmac") == WebhookAuthType.HMAC


# ===========================================================================
# Test WebhookStatus Enum
# ===========================================================================


class TestWebhookStatus:
    """Kiểm tra các giá trị của enum WebhookStatus."""

    def test_status_active_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookStatus
        assert WebhookStatus.ACTIVE.value == "active"

    def test_status_inactive_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookStatus
        assert WebhookStatus.INACTIVE.value == "inactive"

    def test_status_paused_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookStatus
        assert WebhookStatus.PAUSED.value == "paused"

    def test_status_failed_value(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookStatus
        assert WebhookStatus.FAILED.value == "failed"


# ===========================================================================
# Test DispatchStatus Enum
# ===========================================================================


class TestDispatchStatus:
    """Kiểm tra các giá trị của enum DispatchStatus."""

    def test_dispatch_status_pending_value(self):
        from midicoder.emitters.core.cp40_webhook.models import DispatchStatus
        assert DispatchStatus.PENDING.value == "pending"

    def test_dispatch_status_dispatching_value(self):
        from midicoder.emitters.core.cp40_webhook.models import DispatchStatus
        assert DispatchStatus.DISPATCHING.value == "dispatching"

    def test_dispatch_status_delivered_value(self):
        from midicoder.emitters.core.cp40_webhook.models import DispatchStatus
        assert DispatchStatus.DELIVERED.value == "delivered"

    def test_dispatch_status_failed_value(self):
        from midicoder.emitters.core.cp40_webhook.models import DispatchStatus
        assert DispatchStatus.FAILED.value == "failed"

    def test_dispatch_status_retrying_value(self):
        from midicoder.emitters.core.cp40_webhook.models import DispatchStatus
        assert DispatchStatus.RETRYING.value == "retrying"


# ===========================================================================
# Test WebhookAuthConfig
# ===========================================================================


class TestWebhookAuthConfig:
    """Kiểm tra WebhookAuthConfig — tạo, validate, serialize."""

    def test_create_none_auth(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(auth_type=WebhookAuthType.NONE)
        assert config.auth_type == WebhookAuthType.NONE
        assert config.secret == ""

    def test_create_bearer_auth_with_secret(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(
            auth_type=WebhookAuthType.BEARER,
            secret="my_token_123",
        )
        assert config.auth_type == WebhookAuthType.BEARER
        assert config.secret == "my_token_123"

    def test_create_bearer_auth_without_secret_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        with pytest.raises(MidicoderError):
            WebhookAuthConfig(auth_type=WebhookAuthType.BEARER)

    def test_create_bearer_auth_with_empty_secret_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        with pytest.raises(MidicoderError):
            WebhookAuthConfig(auth_type=WebhookAuthType.BEARER, secret="")

    def test_create_hmac_auth_with_secret(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(
            auth_type=WebhookAuthType.HMAC,
            header_name="X-Webhook-Signature",
            secret="hmac_secret",
            algorithm="sha256",
        )
        assert config.auth_type == WebhookAuthType.HMAC
        assert config.algorithm == "sha256"

    def test_create_basic_auth_with_secret(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(
            auth_type=WebhookAuthType.BASIC,
            secret="user:pass",
        )
        assert config.auth_type == WebhookAuthType.BASIC
        assert config.secret == "user:pass"

    def test_auth_config_to_dict(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(
            auth_type=WebhookAuthType.HMAC,
            header_name="X-Signature",
            secret="sec",
            algorithm="sha512",
        )
        d = config.to_dict()
        assert d["auth_type"] == "hmac"
        assert d["header_name"] == "X-Signature"
        assert d["algorithm"] == "sha512"

    def test_auth_config_from_dict_roundtrip(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        config = WebhookAuthConfig(
            auth_type=WebhookAuthType.BEARER,
            header_name="Authorization",
            secret="token_val",
            algorithm="sha256",
        )
        d = config.to_dict()
        restored = WebhookAuthConfig.from_dict(d)
        assert restored.auth_type == WebhookAuthType.BEARER
        assert restored.header_name == "Authorization"
        assert restored.secret == "token_val"
        assert restored.algorithm == "sha256"

    def test_auth_config_from_dict_none_roundtrip(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
        )
        data = {"auth_type": "none", "header_name": "Authorization", "secret": "", "algorithm": "sha256"}
        config = WebhookAuthConfig.from_dict(data)
        assert config.auth_type == WebhookAuthType.NONE


# ===========================================================================
# Test WebhookSubscription
# ===========================================================================


class TestWebhookSubscription:
    """Kiểm tra WebhookSubscription — tạo, validate, serialize."""

    def test_create_valid_subscription(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/webhook",
        )
        assert sub.subscription_id == "wh_001"
        assert sub.event_type == "order.created"
        assert sub.url == "https://example.com/webhook"
        assert sub.http_method == "POST"

    def test_create_subscription_with_invalid_url_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        with pytest.raises(MidicoderError):
            WebhookSubscription(
                subscription_id="wh_bad",
                event_type="order.created",
                url="not-a-valid-url",
            )

    def test_create_subscription_with_empty_url_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        with pytest.raises(MidicoderError):
            WebhookSubscription(
                subscription_id="wh_bad",
                event_type="order.created",
                url="",
            )

    def test_create_subscription_with_invalid_http_method_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        with pytest.raises(MidicoderError):
            WebhookSubscription(
                subscription_id="wh_bad",
                event_type="order.created",
                url="https://example.com/webhook",
                http_method="DELETE",
            )

    def test_create_subscription_with_empty_subscription_id_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        with pytest.raises(MidicoderError):
            WebhookSubscription(
                subscription_id="",
                event_type="order.created",
                url="https://example.com/webhook",
            )

    def test_create_subscription_with_empty_event_type_raises(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        with pytest.raises(MidicoderError):
            WebhookSubscription(
                subscription_id="wh_001",
                event_type="",
                url="https://example.com/webhook",
            )

    def test_subscription_auto_timestamps(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/webhook",
        )
        assert sub.created_at is not None
        assert sub.updated_at is not None

    def test_subscription_with_put_method(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.updated",
            url="https://example.com/webhook",
            http_method="PUT",
        )
        assert sub.http_method == "PUT"

    def test_subscription_with_patch_method(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.partial",
            url="https://example.com/webhook",
            http_method="PATCH",
        )
        assert sub.http_method == "PATCH"

    def test_subscription_with_custom_status(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/webhook",
            status=WebhookStatus.PAUSED,
            tenant_id="tenant_1",
            tags=["test", "webhook"],
        )
        assert sub.status == WebhookStatus.PAUSED
        assert sub.tenant_id == "tenant_1"
        assert "test" in sub.tags

    def test_subscription_to_dict(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/webhook",
        )
        d = sub.to_dict()
        assert d["subscription_id"] == "wh_001"
        assert d["event_type"] == "order.created"
        assert d["http_method"] == "POST"
        assert d["status"] == "active"
        assert d["auth_config"]["auth_type"] == "none"
        assert "created_at" in d

    def test_subscription_to_dict_from_dict_roundtrip(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_rt",
            event_type="payment.completed",
            url="https://example.com/pay",
            http_method="POST",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.BEARER,
                secret="tok",
            ),
            retry_policy={"max_retries": 5, "base_delay": 2.0, "max_delay": 120.0},
            rate_limit_rpm=120,
            status=WebhookStatus.ACTIVE,
            tenant_id="t1",
            tags=["payment"],
        )
        d = sub.to_dict()
        restored = WebhookSubscription.from_dict(d)
        assert restored.subscription_id == "wh_rt"
        assert restored.event_type == "payment.completed"
        assert restored.url == "https://example.com/pay"
        assert restored.http_method == "POST"
        assert restored.auth_config.auth_type == WebhookAuthType.BEARER
        assert restored.auth_config.secret == "tok"
        assert restored.retry_policy["max_retries"] == 5
        assert restored.rate_limit_rpm == 120
        assert restored.status == WebhookStatus.ACTIVE
        assert restored.tenant_id == "t1"
        assert "payment" in restored.tags

    def test_subscription_from_dict_without_auth_config(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthType,
            WebhookSubscription,
        )
        data = {
            "subscription_id": "wh_noauth",
            "event_type": "test.event",
            "url": "https://example.com/test",
            "http_method": "POST",
            "auth_config": {},
            "payload_template": {},
            "retry_policy": {"max_retries": 3, "base_delay": 1.0, "max_delay": 60.0},
            "rate_limit_rpm": 60,
            "status": "active",
            "tenant_id": None,
            "tags": [],
        }
        sub = WebhookSubscription.from_dict(data)
        assert sub.subscription_id == "wh_noauth"
        assert sub.auth_config.auth_type == WebhookAuthType.NONE


# ===========================================================================
# Test WebhookDispatch
# ===========================================================================


class TestWebhookDispatch:
    """Kiểm tra WebhookDispatch — tạo, serialize."""

    def test_create_dispatch(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            DispatchStatus,
            WebhookDispatch,
        )
        d = WebhookDispatch(
            dispatch_id="disp_001",
            subscription_id="wh_001",
            event_type="order.created",
            payload={"key": "value"},
        )
        assert d.dispatch_id == "disp_001"
        assert d.status == DispatchStatus.PENDING
        assert d.attempts == 0

    def test_dispatch_auto_timestamp(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatch
        d = WebhookDispatch(
            dispatch_id="disp_001",
            subscription_id="wh_001",
            event_type="order.created",
        )
        assert d.created_at is not None
        assert d.delivered_at is None

    def test_dispatch_to_dict(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatch
        d = WebhookDispatch(
            dispatch_id="disp_002",
            subscription_id="wh_002",
            event_type="test.event",
            payload={"order_id": "123"},
        )
        dct = d.to_dict()
        assert dct["dispatch_id"] == "disp_002"
        assert dct["status"] == "pending"
        assert dct["payload"]["order_id"] == "123"
        assert "created_at" in dct

    def test_dispatch_to_dict_from_dict_roundtrip(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            DispatchStatus,
            WebhookDispatch,
        )
        d = WebhookDispatch(
            dispatch_id="disp_rt",
            subscription_id="wh_rt",
            event_type="payment.done",
            payload={"amount": 100},
            status=DispatchStatus.DELIVERED,
            attempts=2,
        )
        dct = d.to_dict()
        restored = WebhookDispatch.from_dict(dct)
        assert restored.dispatch_id == "disp_rt"
        assert restored.status == DispatchStatus.DELIVERED
        assert restored.attempts == 2
        assert restored.payload["amount"] == 100


# ===========================================================================
# Test WebhookDeliveryAttempt
# ===========================================================================


class TestWebhookDeliveryAttempt:
    """Kiểm tra WebhookDeliveryAttempt — tạo, serialize."""

    def test_create_attempt(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDeliveryAttempt
        a = WebhookDeliveryAttempt(
            attempt_id="att_001",
            dispatch_id="disp_001",
            response_code=200,
            response_body="{}",
        )
        assert a.attempt_id == "att_001"
        assert a.response_code == 200

    def test_attempt_auto_timestamp(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDeliveryAttempt
        a = WebhookDeliveryAttempt(
            attempt_id="att_002",
            dispatch_id="disp_002",
        )
        assert a.timestamp is not None

    def test_attempt_to_dict(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDeliveryAttempt
        a = WebhookDeliveryAttempt(
            attempt_id="att_003",
            dispatch_id="disp_003",
            response_code=500,
            error="Internal Server Error",
        )
        dct = a.to_dict()
        assert dct["attempt_id"] == "att_003"
        assert dct["response_code"] == 500
        assert dct["error"] == "Internal Server Error"
        assert "timestamp" in dct

    def test_attempt_to_dict_from_dict_roundtrip(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDeliveryAttempt
        a = WebhookDeliveryAttempt(
            attempt_id="att_rt",
            dispatch_id="disp_rt",
            response_code=429,
            response_body="rate limited",
            error="Too Many Requests",
        )
        dct = a.to_dict()
        restored = WebhookDeliveryAttempt.from_dict(dct)
        assert restored.attempt_id == "att_rt"
        assert restored.response_code == 429
        assert restored.response_body == "rate limited"
        assert restored.error == "Too Many Requests"


# ===========================================================================
# Test RetryPolicy
# ===========================================================================


class TestRetryPolicy:
    """Kiểm tra RetryPolicy — exponential backoff và should_retry."""

    def test_get_delay_attempt_zero_equals_base(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0)
        assert policy.get_delay(0) == 1.0

    def test_get_delay_attempt_one_equals_base_times_two(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0)
        assert policy.get_delay(1) == 2.0

    def test_get_delay_attempt_two_equals_base_times_four(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0)
        assert policy.get_delay(2) == 4.0

    def test_get_delay_capped_at_max_delay(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0, backoff_multiplier=2.0)
        assert policy.get_delay(10) == 10.0

    def test_should_retry_5xx_returns_true(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, 500) is True

    def test_should_retry_503_returns_true(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, 503) is True

    def test_should_retry_429_returns_true(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, 429) is True

    def test_should_retry_4xx_returns_false(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, 400) is False

    def test_should_retry_404_returns_false(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, 404) is False

    def test_should_retry_max_retries_exceeded_returns_false(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(3, 500) is False

    def test_should_retry_network_error_returns_true(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, None) is True

    def test_retry_policy_default_values(self):
        from midicoder.emitters.core.cp40_webhook.models import RetryPolicy
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.backoff_multiplier == 2.0


# ===========================================================================
# Test WebhookDispatcher
# ===========================================================================


class TestWebhookDispatcher:
    """Kiểm tra WebhookDispatcher — subscribe, dispatch, HMAC, headers."""

    def _make_subscription(self, sid: str, etype: str, url: str = "https://example.com/hook",
                           status=None) -> "WebhookSubscription":
        from midicoder.emitters.core.cp40_webhook.models import WebhookSubscription, WebhookStatus
        return WebhookSubscription(
            subscription_id=sid,
            event_type=etype,
            url=url,
            status=status or WebhookStatus.ACTIVE,
        )

    def test_add_subscription(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher, WebhookSubscription, WebhookStatus
        dispatcher = WebhookDispatcher()
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/hook",
            status=WebhookStatus.ACTIVE,
        )
        dispatcher.add_subscription(sub)
        assert "wh_001" in dispatcher.subscriptions

    def test_remove_subscription(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher, WebhookSubscription, WebhookStatus
        dispatcher = WebhookDispatcher()
        sub = WebhookSubscription(
            subscription_id="wh_001",
            event_type="order.created",
            url="https://example.com/hook",
            status=WebhookStatus.ACTIVE,
        )
        dispatcher.add_subscription(sub)
        assert dispatcher.remove_subscription("wh_001") is True
        assert "wh_001" not in dispatcher.subscriptions

    def test_remove_nonexistent_subscription(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        assert dispatcher.remove_subscription("not_found") is False

    def test_get_subscriptions_by_event_matching(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "order.created"))
        dispatcher.add_subscription(self._make_subscription("wh_002", "order.created"))
        dispatcher.add_subscription(self._make_subscription("wh_003", "payment.completed"))
        results = dispatcher.get_subscriptions_by_event("order.created")
        assert len(results) == 2

    def test_get_subscriptions_by_event_filters_inactive(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher, WebhookStatus
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "order.created"))
        dispatcher.add_subscription(self._make_subscription("wh_002", "order.created", status=WebhookStatus.INACTIVE))
        results = dispatcher.get_subscriptions_by_event("order.created")
        assert len(results) == 1
        assert results[0].subscription_id == "wh_001"

    def test_get_subscriptions_by_event_empty(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        results = dispatcher.get_subscriptions_by_event("nonexistent")
        assert len(results) == 0

    def test_dispatch_event_creates_dispatches(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "order.created"))
        ids = dispatcher.dispatch_event("order.created", {"order_id": "123"})
        assert len(ids) == 1
        assert dispatcher.dispatches[ids[0]].subscription_id == "wh_001"

    def test_dispatch_event_returns_dispatch_ids(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "order.created"))
        dispatcher.add_subscription(self._make_subscription("wh_002", "order.created"))
        ids = dispatcher.dispatch_event("order.created", {"data": "val"})
        assert len(ids) == 2
        assert ids[0] != ids[1]

    def test_dispatch_event_no_matching_subscriptions(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "payment.completed"))
        ids = dispatcher.dispatch_event("order.created", {})
        assert len(ids) == 0

    def test_dispatch_event_payload_contains_event_data(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        dispatcher.add_subscription(self._make_subscription("wh_001", "order.created"))
        ids = dispatcher.dispatch_event("order.created", {"order_id": "456"})
        dispatch = dispatcher.dispatches[ids[0]]
        assert "data" in dispatch.payload

    def test_compute_hmac_signature(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        sig = dispatcher.compute_hmac_signature({"key": "value"}, "secret_key", "sha256")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest

    def test_compute_hmac_signature_deterministic(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        payload = {"a": 1, "b": 2}
        sig1 = dispatcher.compute_hmac_signature(payload, "secret", "sha256")
        sig2 = dispatcher.compute_hmac_signature(payload, "secret", "sha256")
        assert sig1 == sig2

    def test_compute_hmac_signature_different_secrets(self):
        from midicoder.emitters.core.cp40_webhook.models import WebhookDispatcher
        dispatcher = WebhookDispatcher()
        sig1 = dispatcher.compute_hmac_signature({"k": "v"}, "secret_a", "sha256")
        sig2 = dispatcher.compute_hmac_signature({"k": "v"}, "secret_b", "sha256")
        assert sig1 != sig2

    def test_build_headers_contains_base_headers(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
            WebhookDispatch,
            WebhookDispatcher,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_h",
            event_type="test",
            url="https://example.com/h",
            auth_config=WebhookAuthConfig(auth_type=WebhookAuthType.NONE),
            status=WebhookStatus.ACTIVE,
        )
        disp = WebhookDispatch(dispatch_id="d_001", subscription_id="wh_h", event_type="test")
        dispatcher = WebhookDispatcher()
        headers = dispatcher.get_build_headers(sub, disp)
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Dispatch-ID"] == "d_001"
        assert "X-Webhook-Timestamp" in headers

    def test_build_headers_bearer(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
            WebhookDispatch,
            WebhookDispatcher,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_bearer",
            event_type="test",
            url="https://example.com/h",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.BEARER,
                header_name="Authorization",
                secret="my_token",
            ),
            status=WebhookStatus.ACTIVE,
        )
        disp = WebhookDispatch(dispatch_id="d_002", subscription_id="wh_bearer", event_type="test")
        dispatcher = WebhookDispatcher()
        headers = dispatcher.get_build_headers(sub, disp)
        assert headers["Authorization"] == "Bearer my_token"

    def test_build_headers_hmac(self):
        from midicoder.emitters.core.cp40_webhook.models import (
            WebhookAuthConfig,
            WebhookAuthType,
            WebhookDispatch,
            WebhookDispatcher,
            WebhookSubscription,
            WebhookStatus,
        )
        sub = WebhookSubscription(
            subscription_id="wh_hmac",
            event_type="test",
            url="https://example.com/h",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                header_name="X-Webhook-Signature",
                secret="hmac_secret",
                algorithm="sha256",
            ),
            status=WebhookStatus.ACTIVE,
        )
        disp = WebhookDispatch(
            dispatch_id="d_003",
            subscription_id="wh_hmac",
            event_type="test",
            payload={"data": "test"},
        )
        dispatcher = WebhookDispatcher()
        headers = dispatcher.get_build_headers(sub, disp)
        assert "X-Webhook-Signature" in headers
        assert len(headers["X-Webhook-Signature"]) == 64
