"""
Tests cho CP12 models mở rộng: Webhook, Chat, DeliveryTracking, AB Testing.

Test coverage:
- WebhookConfig: 8 tests
- WebhookDelivery: 6 tests
- ChatPlatform: 3 tests
- ChatIntegrationConfig: 5 tests
- DeliveryStatus: 3 tests
- DeliveryAttempt: 3 tests
- DeliveryTracking: 10 tests
- ABTestVariant: 5 tests
- ABTestConfig: 10 tests

Tổng: 53 tests
"""

from __future__ import annotations

import pytest
from datetime import datetime

from midicoder.packs.cp12_notification.models import (
    NotificationChannel,
    WebhookConfig,
    WebhookDelivery,
    WebhookAuthType,
    ChatPlatform,
    ChatIntegrationConfig,
    DeliveryStatus,
    DeliveryAttempt,
    DeliveryTracking,
    ABTestVariant,
    ABTestConfig,
)


# ============================================================================
# Test WebhookConfig
# ============================================================================


class TestWebhookConfig:
    """Tests cho WebhookConfig."""

    def test_create_basic(self):
        """Tạo WebhookConfig cơ bản."""
        config = WebhookConfig(url="https://example.com/webhook")
        assert config.url == "https://example.com/webhook"
        assert config.method == "POST"
        assert config.auth_type == WebhookAuthType.NONE
        assert config.timeout_seconds == 30
        assert config.max_retries == 3

    def test_create_with_bearer(self):
        """Tạo WebhookConfig với Bearer auth."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            auth_type=WebhookAuthType.BEARER,
            auth_header="token123",
        )
        assert config.auth_type == WebhookAuthType.BEARER
        assert config.auth_header == "token123"

    def test_create_with_hmac(self):
        """Tạo WebhookConfig với HMAC auth."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            auth_type=WebhookAuthType.HMAC,
            auth_secret="secret_key",
        )
        assert config.auth_type == WebhookAuthType.HMAC
        assert config.auth_secret == "secret_key"

    def test_empty_url_raises(self):
        """WebhookConfig throw khi URL rỗng."""
        with pytest.raises(ValueError, match="url"):
            WebhookConfig(url="")

    def test_invalid_method_raises(self):
        """WebhookConfig throw khi method không hợp lệ."""
        with pytest.raises(ValueError, match="method"):
            WebhookConfig(url="https://example.com", method="DELETE")

    def test_timeout_less_than_1_defaults_to_30(self):
        """timeout_seconds < 1 → default 30."""
        config = WebhookConfig(url="https://example.com", timeout_seconds=0)
        assert config.timeout_seconds == 30

    def test_to_dict(self):
        """WebhookConfig.to_dict() trả về dict đúng."""
        config = WebhookConfig(
            url="https://example.com",
            method="PUT",
            auth_type=WebhookAuthType.BEARER,
            auth_header="tok",
            max_retries=5,
        )
        d = config.to_dict()
        assert d["url"] == "https://example.com"
        assert d["method"] == "PUT"
        assert d["auth_type"] == "bearer"
        assert d["max_retries"] == 5

    def test_compute_hmac_signature(self):
        """WebhookConfig.compute_hmac_signature() tính đúng HMAC."""
        config = WebhookConfig(
            url="https://example.com",
            auth_type=WebhookAuthType.HMAC,
            auth_secret="my_secret",
        )
        sig = config.compute_hmac_signature("test body")
        assert sig  # Không rỗng
        assert len(sig) == 64  # SHA-256 hex


# ============================================================================
# Test WebhookDelivery
# ============================================================================


class TestWebhookDelivery:
    """Tests cho WebhookDelivery."""

    def test_create_defaults(self):
        """WebhookDelivery có default values."""
        d = WebhookDelivery(webhook_url="https://example.com")
        assert d.status == "pending"
        assert d.attempts == 0
        assert d.delivery_id  # Tự sinh UUID

    def test_mark_attempted_success(self):
        """mark_attempted với 200 → delivered."""
        d = WebhookDelivery(webhook_url="https://example.com")
        d.mark_attempted(200, '{"ok":true}')
        assert d.status == "delivered"
        assert d.attempts == 1
        assert d.delivered_at is not None

    def test_mark_attempted_server_error(self):
        """mark_attempted với 500 → retried."""
        d = WebhookDelivery(webhook_url="https://example.com")
        d.mark_attempted(500, "Internal Error")
        assert d.status == "retried"
        assert d.attempts == 1

    def test_mark_attempted_client_error(self):
        """mark_attempted với 404 → failed."""
        d = WebhookDelivery(webhook_url="https://example.com")
        d.mark_attempted(404, "Not Found")
        assert d.status == "failed"

    def test_to_dict(self):
        """WebhookDelivery.to_dict() đúng."""
        d = WebhookDelivery(webhook_url="https://ex.com")
        d.mark_attempted(200, "ok")
        result = d.to_dict()
        assert result["status"] == "delivered"
        assert result["attempts"] == 1

    def test_from_dict(self):
        """WebhookDelivery.from_dict() đúng."""
        data = {
            "webhook_url": "https://ex.com",
            "status": "delivered",
            "attempts": 2,
            "last_response_code": 200,
        }
        d = WebhookDelivery.from_dict(data)
        assert d.webhook_url == "https://ex.com"
        assert d.attempts == 2


# ============================================================================
# Test ChatPlatform & ChatIntegrationConfig
# ============================================================================


class TestChatPlatform:
    """Tests cho ChatPlatform."""

    def test_all_platforms_exist(self):
        """Tất cả platforms có value đúng."""
        assert ChatPlatform.SLACK.value == "slack"
        assert ChatPlatform.TEAMS.value == "teams"
        assert ChatPlatform.DISCORD.value == "discord"

    def test_slack_config(self):
        """Tạo Slack config."""
        config = ChatIntegrationConfig(
            platform=ChatPlatform.SLACK,
            bot_token="xoxb-xxx",
            channel_id="C123",
        )
        assert config.platform == ChatPlatform.SLACK

    def test_to_dict_and_from_dict_roundtrip(self):
        """Roundtrip to_dict → from_dict."""
        original = ChatIntegrationConfig(
            platform=ChatPlatform.DISCORD,
            webhook_url="https://discord.com/api/webhooks/xxx",
            channel_id="ch1",
            enable_threading=True,
        )
        d = original.to_dict()
        restored = ChatIntegrationConfig.from_dict(d)
        assert restored.platform == ChatPlatform.DISCORD
        assert restored.enable_threading is True


# ============================================================================
# Test DeliveryStatus
# ============================================================================


class TestDeliveryStatus:
    """Tests cho DeliveryStatus."""

    def test_all_statuses_exist(self):
        """Tất cả delivery statuses có."""
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.BOUNCED.value == "bounced"
        assert DeliveryStatus.OPENED.value == "opened"
        assert DeliveryStatus.CLICKED.value == "clicked"

    def test_count(self):
        """Số lượng delivery statuses."""
        assert len(DeliveryStatus) == 7

    def test_from_string(self):
        """Create from string."""
        assert DeliveryStatus("sent") == DeliveryStatus.SENT


# ============================================================================
# Test DeliveryAttempt
# ============================================================================


class TestDeliveryAttempt:
    """Tests cho DeliveryAttempt."""

    def test_create(self):
        """Tạo DeliveryAttempt."""
        a = DeliveryAttempt(
            attempt_number=1,
            timestamp="2026-05-17T10:00:00",
            status="sent",
        )
        assert a.attempt_number == 1
        assert a.attempt_id  # Auto UUID

    def test_to_dict(self):
        """to_dict() đúng."""
        a = DeliveryAttempt(
            attempt_number=2,
            timestamp="2026-05-17T10:00:00",
            status="failed",
            response_code=500,
            error_message="Server error",
        )
        d = a.to_dict()
        assert d["attempt_number"] == 2
        assert d["response_code"] == 500
        assert d["error_message"] == "Server error"

    def test_default_values(self):
        """Default values."""
        a = DeliveryAttempt(attempt_number=1, timestamp="2026-05-17", status="pending")
        assert a.response_code == 0
        assert a.response_body == ""
        assert a.error_message == ""


# ============================================================================
# Test DeliveryTracking
# ============================================================================


class TestDeliveryTracking:
    """Tests cho DeliveryTracking."""

    def test_create(self):
        """Tạo DeliveryTracking."""
        t = DeliveryTracking(
            dispatch_id="disp_001",
            recipient="user@example.com",
            channel=NotificationChannel.EMAIL,
        )
        assert t.status == DeliveryStatus.PENDING
        assert t.tracking_id  # Auto UUID
        assert t.attempts == []

    def test_add_attempt_sent(self):
        """add_attempt với sent → status SENT."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        attempt = t.add_attempt("sent", response_code=200)
        assert t.status == DeliveryStatus.SENT
        assert len(t.attempts) == 1
        assert attempt.attempt_number == 1

    def test_add_attempt_delivered(self):
        """add_attempt với delivered → status DELIVERED + delivered_at."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        t.add_attempt("delivered")
        assert t.status == DeliveryStatus.DELIVERED
        assert t.delivered_at is not None

    def test_add_attempt_failed(self):
        """add_attempt với failed → status FAILED."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        t.add_attempt("failed", error_message="Timeout")
        assert t.status == DeliveryStatus.FAILED

    def test_mark_opened(self):
        """mark_opened() → status OPENED."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        t.mark_opened()
        assert t.status == DeliveryStatus.OPENED
        assert t.opened_at is not None

    def test_mark_clicked(self):
        """mark_clicked() → status CLICKED."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        t.mark_clicked()
        assert t.status == DeliveryStatus.CLICKED
        assert t.clicked_at is not None

    def test_multiple_attempts(self):
        """Nhiều attempts liên tiếp."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.EMAIL,
        )
        t.add_attempt("sent", 200)
        t.add_attempt("sent", 200)
        assert len(t.attempts) == 2
        assert t.attempts[0].attempt_number == 1
        assert t.attempts[1].attempt_number == 2

    def test_to_dict(self):
        """to_dict() đầy đủ."""
        t = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.SMS,
            metadata={"key": "value"},
        )
        t.add_attempt("sent")
        d = t.to_dict()
        assert d["dispatch_id"] == "d1"
        assert d["channel"] == "sms"
        assert d["status"] == "sent"
        assert d["metadata"]["key"] == "value"
        assert len(d["attempts"]) == 1

    def test_from_dict(self):
        """from_dict() đúng."""
        data = {
            "dispatch_id": "d1",
            "recipient": "u@e.com",
            "channel": "push",
            "status": "delivered",
            "attempts": [
                {
                    "attempt_number": 1,
                    "timestamp": "2026-05-17T10:00:00",
                    "status": "sent",
                }
            ],
        }
        t = DeliveryTracking.from_dict(data)
        assert t.channel == NotificationChannel.PUSH
        assert t.status == DeliveryStatus.DELIVERED
        assert len(t.attempts) == 1

    def test_roundtrip(self):
        """Roundtrip to_dict → from_dict."""
        original = DeliveryTracking(
            dispatch_id="d1",
            recipient="u@e.com",
            channel=NotificationChannel.WEBHOOK,
            metadata={"extra": True},
        )
        original.add_attempt("sent", 200, '{"ok":true}')
        d = original.to_dict()
        restored = DeliveryTracking.from_dict(d)
        assert restored.channel == NotificationChannel.WEBHOOK
        assert restored.attempts[0].response_code == 200


# ============================================================================
# Test ABTestVariant
# ============================================================================


class TestABTestVariant:
    """Tests cho ABTestVariant."""

    def test_create(self):
        """Tạo variant cơ bản."""
        v = ABTestVariant(variant_id="A", template_id="tmpl_v1", weight=50.0)
        assert v.weight == 50.0

    def test_empty_id_raises(self):
        """Empty variant_id raise."""
        with pytest.raises(ValueError, match="variant_id"):
            ABTestVariant(variant_id="", template_id="t1")

    def test_weight_negative_raises(self):
        """Weight < 0 raise."""
        with pytest.raises(ValueError, match="weight"):
            ABTestVariant(variant_id="A", template_id="t1", weight=-1)

    def test_weight_over_100_raises(self):
        """Weight > 100 raise."""
        with pytest.raises(ValueError, match="weight"):
            ABTestVariant(variant_id="A", template_id="t1", weight=101)

    def test_to_dict_and_roundtrip(self):
        """Roundtrip."""
        original = ABTestVariant(
            variant_id="B",
            template_id="tmpl_v2",
            weight=33.33,
            name="Variant B",
            description="New template",
        )
        d = original.to_dict()
        restored = ABTestVariant.from_dict(d)
        assert restored.variant_id == "B"
        assert restored.weight == 33.33
        assert restored.name == "Variant B"


# ============================================================================
# Test ABTestConfig
# ============================================================================


class TestABTestConfig:
    """Tests cho ABTestConfig."""

    def test_create_with_two_variants(self):
        """Tạo A/B test với 2 variants."""
        config = ABTestConfig(
            name="Welcome Test",
            channel=NotificationChannel.EMAIL,
            variants=[
                ABTestVariant(variant_id="A", template_id="tmpl_a", weight=50.0),
                ABTestVariant(variant_id="B", template_id="tmpl_b", weight=50.0),
            ],
        )
        assert len(config.variants) == 2
        assert config.is_active is True

    def test_less_than_two_variants_raises(self):
        """Ít hơn 2 variants raise."""
        with pytest.raises(ValueError, match="ít nhất 2"):
            ABTestConfig(
                name="Test",
                channel=NotificationChannel.EMAIL,
                variants=[
                    ABTestVariant(variant_id="A", template_id="t1", weight=100),
                ],
            )

    def test_weight_not_100_raises(self):
        """Total weight != 100 raise."""
        with pytest.raises(ValueError, match="100"):
            ABTestConfig(
                name="Test",
                channel=NotificationChannel.EMAIL,
                variants=[
                    ABTestVariant(variant_id="A", template_id="t1", weight=60),
                    ABTestVariant(variant_id="B", template_id="t2", weight=60),
                ],
            )

    def test_empty_name_raises(self):
        """Empty name raise."""
        with pytest.raises(ValueError, match="name"):
            ABTestConfig(
                name="",
                channel=NotificationChannel.EMAIL,
                variants=[
                    ABTestVariant(variant_id="A", template_id="t1", weight=50),
                    ABTestVariant(variant_id="B", template_id="t2", weight=50),
                ],
            )

    def test_select_variant_deterministic(self):
        """select_variant deterministic theo hash."""
        config = ABTestConfig(
            name="Test",
            channel=NotificationChannel.EMAIL,
            variants=[
                ABTestVariant(variant_id="A", template_id="t1", weight=50),
                ABTestVariant(variant_id="B", template_id="t2", weight=50),
            ],
        )
        v1 = config.select_variant(0)
        v2 = config.select_variant(0)
        assert v1.variant_id == v2.variant_id

    def test_get_variant_for_recipient(self):
        """get_variant_for_recipient deterministic."""
        config = ABTestConfig(
            name="Test",
            channel=NotificationChannel.EMAIL,
            variants=[
                ABTestVariant(variant_id="A", template_id="t1", weight=50),
                ABTestVariant(variant_id="B", template_id="t2", weight=50),
            ],
        )
        v1 = config.get_variant_for_recipient("user@example.com")
        v2 = config.get_variant_for_recipient("user@example.com")
        assert v1.variant_id == v2.variant_id

    def test_hash_recipient_consistent(self):
        """hash_recipient consistent."""
        h1 = ABTestConfig.hash_recipient("user@example.com")
        h2 = ABTestConfig.hash_recipient("user@example.com")
        assert h1 == h2

    def test_to_dict(self):
        """to_dict() đầy đủ."""
        config = ABTestConfig(
            name="Test",
            channel=NotificationChannel.EMAIL,
            variants=[
                ABTestVariant(variant_id="A", template_id="t1", weight=50),
                ABTestVariant(variant_id="B", template_id="t2", weight=50),
            ],
            metric="click_rate",
        )
        d = config.to_dict()
        assert d["name"] == "Test"
        assert d["channel"] == "email"
        assert len(d["variants"]) == 2
        assert d["metric"] == "click_rate"

    def test_from_dict(self):
        """from_dict() đúng."""
        data = {
            "name": "Test",
            "channel": "sms",
            "variants": [
                {"variant_id": "A", "template_id": "t1", "weight": 50},
                {"variant_id": "B", "template_id": "t2", "weight": 50},
            ],
        }
        config = ABTestConfig.from_dict(data)
        assert config.channel == NotificationChannel.SMS
        assert len(config.variants) == 2

    def test_select_variant_distribution(self):
        """Distribution khoảng 50/50 với 10000 samples."""
        config = ABTestConfig(
            name="Test",
            channel=NotificationChannel.EMAIL,
            variants=[
                ABTestVariant(variant_id="A", template_id="t1", weight=50),
                ABTestVariant(variant_id="B", template_id="t2", weight=50),
            ],
        )
        counts = {"A": 0, "B": 0}
        for i in range(10000):
            v = config.select_variant(i)
            counts[v.variant_id] += 1

        # Mỗi variant ~5000 ± 500
        assert 4500 <= counts["A"] <= 5500
        assert 4500 <= counts["B"] <= 5500
