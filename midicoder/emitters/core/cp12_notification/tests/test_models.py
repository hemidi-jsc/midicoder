"""
Tests cho CP12 Notification Models.

Test coverage:
- NotificationChannel enum: 5 tests
- NotificationTemplate model: 10 tests
- NotificationDispatch model: 10 tests
- NotificationProvider model: 6 tests
- DispatchResult model: 5 tests

Tổng: 36 tests
"""

from __future__ import annotations

import pytest


# ============================================================================
# Test NotificationChannel Enum
# ============================================================================


class TestNotificationChannel:
    """Tests cho NotificationChannel enum."""

    def test_email_channel_exists(self):
        """NotificationChannel có EMAIL value."""
        from midicoder.emitters.core.cp12_notification.models import NotificationChannel

        assert NotificationChannel.EMAIL.value == "email"

    def test_sms_channel_exists(self):
        """NotificationChannel có SMS value."""
        from midicoder.emitters.core.cp12_notification.models import NotificationChannel

        assert NotificationChannel.SMS.value == "sms"

    def test_push_channel_exists(self):
        """NotificationChannel có PUSH value."""
        from midicoder.emitters.core.cp12_notification.models import NotificationChannel

        assert NotificationChannel.PUSH.value == "push"

    def test_webhook_channel_exists(self):
        """NotificationChannel có WEBHOOK value."""
        from midicoder.emitters.core.cp12_notification.models import NotificationChannel

        assert NotificationChannel.WEBHOOK.value == "webhook"

    def test_in_app_channel_exists(self):
        """NotificationChannel có IN_APP value."""
        from midicoder.emitters.core.cp12_notification.models import NotificationChannel

        assert NotificationChannel.IN_APP.value == "in_app"


# ============================================================================
# Test NotificationTemplate Model
# ============================================================================


class TestNotificationTemplate:
    """Tests cho NotificationTemplate data model."""

    def test_template_creation(self):
        """NotificationTemplate có thể tạo với đủ thuộc tính."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="welcome_email",
            channel=NotificationChannel.EMAIL,
            subject="Chào mừng {{name}}",
            body_html="<h1>Xin chào {{name}}</h1>",
            body_text="Xin chào {{name}}",
            variables=["name"],
            locale="vi",
        )
        assert template.template_id == "welcome_email"
        assert template.channel == NotificationChannel.EMAIL
        assert template.locale == "vi"
        assert len(template.variables) == 1

    def test_template_defaults(self):
        """NotificationTemplate có default values."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="basic",
            channel=NotificationChannel.EMAIL,
        )
        assert template.subject == ""
        assert template.body_html == ""
        assert template.variables == []
        assert template.locale == "en"

    def test_template_empty_id_raises(self):
        """NotificationTemplate throw khi template_id rỗng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        with pytest.raises(ValueError, match="template_id"):
            NotificationTemplate(
                template_id="",
                channel=NotificationChannel.EMAIL,
            )

    def test_template_render(self):
        """NotificationTemplate.render() thay thế variables đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="welcome",
            channel=NotificationChannel.EMAIL,
            subject="Chào {{name}}",
            body_html="<p>Xin chào {{name}}</p>",
        )
        rendered = template.render({"name": "Minh"})
        assert rendered["subject"] == "Chào Minh"
        assert rendered["body_html"] == "<p>Xin chào Minh</p>"

    def test_template_render_missing_variable(self):
        """NotificationTemplate.render() giữ nguyên variable nếu thiếu."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="test",
            channel=NotificationChannel.EMAIL,
            body_html="{{name}} - {{missing}}",
        )
        rendered = template.render({"name": "Test"})
        assert "Test" in rendered["body_html"]
        assert "{{missing}}" in rendered["body_html"]

    def test_template_to_dict(self):
        """NotificationTemplate.to_dict() trả về dict đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="t1",
            channel=NotificationChannel.SMS,
            body_text="Xin chào {{name}}",
            locale="vi",
        )
        d = template.to_dict()
        assert d["template_id"] == "t1"
        assert d["channel"] == "sms"
        assert d["locale"] == "vi"

    def test_template_from_dict(self):
        """NotificationTemplate.from_dict() tạo object đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        data = {
            "template_id": "t1",
            "channel": "email",
            "subject": "Test",
            "body_html": "<p>{{name}}</p>",
            "locale": "vi",
        }
        template = NotificationTemplate.from_dict(data)
        assert template.template_id == "t1"
        assert template.channel == NotificationChannel.EMAIL
        assert template.locale == "vi"

    def test_template_render_multiple_variables(self):
        """NotificationTemplate.render() xử lý nhiều variables."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="order",
            channel=NotificationChannel.EMAIL,
            body_html="Đơn {{order_id}} của {{name}}, tổng: {{total}}",
        )
        rendered = template.render({
            "name": "Minh",
            "order_id": "ORD-001",
            "total": "100,000 VND",
        })
        assert "ORD-001" in rendered["body_html"]
        assert "Minh" in rendered["body_html"]
        assert "100,000 VND" in rendered["body_html"]

    def test_template_render_replaces_all_fields(self):
        """NotificationTemplate.render() thay thế trong cả subject, body_html, body_text."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            template_id="t1",
            channel=NotificationChannel.EMAIL,
            subject="Chào {{name}}",
            body_html="<b>{{name}}</b>",
            body_text="Chào {{name}}",
        )
        rendered = template.render({"name": "A"})
        assert rendered["subject"] == "Chào A"
        assert rendered["body_html"] == "<b>A</b>"
        assert rendered["body_text"] == "Chào A"

    def test_template_with_all_channels(self):
        """NotificationTemplate hoạt động với tất cả channels."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationTemplate,
        )

        for ch in NotificationChannel:
            t = NotificationTemplate(template_id=f"t_{ch}", channel=ch)
            assert t.channel == ch


# ============================================================================
# Test NotificationDispatch Model
# ============================================================================


class TestNotificationDispatch:
    """Tests cho NotificationDispatch data model."""

    def test_dispatch_creation(self):
        """NotificationDispatch có thể tạo với đủ thuộc tính."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="welcome_email",
            recipient="user@example.com",
            channel=NotificationChannel.EMAIL,
            payload={"name": "Minh"},
        )
        assert dispatch.dispatch_id == "disp_001"
        assert dispatch.status == "pending"
        assert dispatch.recipient == "user@example.com"

    def test_dispatch_empty_id_raises(self):
        """NotificationDispatch throw khi dispatch_id rỗng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        with pytest.raises(ValueError, match="dispatch_id"):
            NotificationDispatch(
                dispatch_id="",
                template_ref="t1",
                recipient="a@b.com",
                channel=NotificationChannel.EMAIL,
            )

    def test_dispatch_empty_recipient_raises(self):
        """NotificationDispatch throw khi recipient rỗng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        with pytest.raises(ValueError, match="recipient"):
            NotificationDispatch(
                dispatch_id="d1",
                template_ref="t1",
                recipient="",
                channel=NotificationChannel.EMAIL,
            )

    def test_dispatch_mark_sent(self):
        """NotificationDispatch.mark_sent() cập nhật status."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="welcome",
            recipient="test@test.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_sent()
        assert dispatch.status == "sent"
        assert dispatch.sent_at is not None

    def test_dispatch_mark_failed(self):
        """NotificationDispatch.mark_failed() cập nhật status và error."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="t1",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_failed("Server error")
        assert dispatch.status == "failed"
        assert dispatch.error_message == "Server error"

    def test_dispatch_mark_bounced(self):
        """NotificationDispatch.mark_bounced() cập nhật status."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="t1",
            recipient="invalid@test.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_bounced("Mailbox not found")
        assert dispatch.status == "bounced"
        assert dispatch.error_message == "Mailbox not found"

    def test_dispatch_to_dict(self):
        """NotificationDispatch.to_dict() trả về dict đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="test",
            recipient="a@b.com",
            channel=NotificationChannel.SMS,
            payload={"key": "val"},
        )
        d = dispatch.to_dict()
        assert d["dispatch_id"] == "disp_001"
        assert d["status"] == "pending"
        assert d["channel"] == "sms"

    def test_dispatch_to_dict_with_sent_at(self):
        """NotificationDispatch.to_dict() bao gồm sent_at khi đã gửi."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="t1",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_sent()
        d = dispatch.to_dict()
        assert "sent_at" in d
        assert d["status"] == "sent"

    def test_dispatch_to_dict_with_error(self):
        """NotificationDispatch.to_dict() bao gồm error_message khi failed."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="t1",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_failed("error")
        d = dispatch.to_dict()
        assert d["error_message"] == "error"

    def test_dispatch_defaults(self):
        """NotificationDispatch có default values."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationDispatch,
        )

        dispatch = NotificationDispatch(
            dispatch_id="d1",
            template_ref="t1",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        assert dispatch.status == "pending"
        assert dispatch.payload == {}
        assert dispatch.sent_at is None


# ============================================================================
# Test NotificationProvider Model
# ============================================================================


class TestNotificationProvider:
    """Tests cho NotificationProvider data model."""

    def test_provider_creation(self):
        """NotificationProvider có thể tạo với config."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        provider = NotificationProvider(
            provider_id="sendgrid_prod",
            channel=NotificationChannel.EMAIL,
            config={"api_key": "SG.xxx", "from_email": "noreply@test.com"},
            enabled=True,
            priority=1,
        )
        assert provider.provider_id == "sendgrid_prod"
        assert provider.enabled is True
        assert provider.priority == 1

    def test_provider_empty_id_raises(self):
        """NotificationProvider throw khi provider_id rỗng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        with pytest.raises(ValueError, match="provider_id"):
            NotificationProvider(
                provider_id="",
                channel=NotificationChannel.EMAIL,
            )

    def test_provider_defaults(self):
        """NotificationProvider có default values."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        provider = NotificationProvider(
            provider_id="default_sms",
            channel=NotificationChannel.SMS,
        )
        assert provider.enabled is True
        assert provider.priority == 99
        assert provider.config == {}

    def test_provider_to_dict(self):
        """NotificationProvider.to_dict() trả về dict đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        provider = NotificationProvider(
            provider_id="twilio_test",
            channel=NotificationChannel.SMS,
            config={"account_sid": "AC.xxx"},
            enabled=False,
            priority=5,
        )
        d = provider.to_dict()
        assert d["provider_id"] == "twilio_test"
        assert d["channel"] == "sms"
        assert d["enabled"] is False

    def test_provider_from_dict(self):
        """NotificationProvider.from_dict() tạo object đúng."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        data = {
            "provider_id": "twilio_test",
            "channel": "sms",
            "config": {"account_sid": "AC.xxx"},
            "enabled": False,
            "priority": 5,
        }
        provider = NotificationProvider.from_dict(data)
        assert provider.provider_id == "twilio_test"
        assert provider.channel == NotificationChannel.SMS
        assert provider.enabled is False
        assert provider.priority == 5

    def test_provider_with_push_channel(self):
        """NotificationProvider hoạt động với PUSH channel."""
        from midicoder.emitters.core.cp12_notification.models import (
            NotificationChannel,
            NotificationProvider,
        )

        provider = NotificationProvider(
            provider_id="firebase_prod",
            channel=NotificationChannel.PUSH,
            config={"credentials_path": "/path/to/creds.json"},
        )
        assert provider.channel == NotificationChannel.PUSH


# ============================================================================
# Test DispatchResult Model
# ============================================================================


class TestDispatchResult:
    """Tests cho DispatchResult data model."""

    def test_result_sent(self):
        """DispatchResult với status sent."""
        from midicoder.emitters.core.cp12_notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_001",
            status="sent",
            provider_response={"message_id": "msg_123"},
        )
        assert result.status == "sent"
        assert result.provider_response == {"message_id": "msg_123"}

    def test_result_failed(self):
        """DispatchResult với status failed và error_code."""
        from midicoder.emitters.core.cp12_notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_002",
            status="failed",
            error_code="MDC-CP12-005",
        )
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-005"

    def test_result_to_dict_with_response(self):
        """DispatchResult.to_dict() bao gồm provider_response."""
        from midicoder.emitters.core.cp12_notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_001",
            status="sent",
            provider_response={"message_id": "msg_123"},
        )
        d = result.to_dict()
        assert d["provider_response"] == {"message_id": "msg_123"}

    def test_result_to_dict_without_response(self):
        """DispatchResult.to_dict() không bao gồm None fields."""
        from midicoder.emitters.core.cp12_notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_003",
            status="pending",
        )
        d = result.to_dict()
        assert "provider_response" not in d
        assert "error_code" not in d

    def test_result_defaults(self):
        """DispatchResult có default values."""
        from midicoder.emitters.core.cp12_notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="d1",
            status="pending",
        )
        assert result.provider_response is None
        assert result.error_code is None
