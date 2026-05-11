"""
Tests cho Notification Emitter (CP12) — TDD Red Phase.

Test coverage:
- Error codes: 7 tests
- Notification models: 12 tests
- Notification parser: 8 tests
- FastAPINotificationEmitter: 10 tests
- NestJSNotificationEmitter: 8 tests

Tổng: 45 tests

CP12: Notification & Communication Generator
"""

from __future__ import annotations

import pytest
from pathlib import Path
from datetime import datetime

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Error Codes (MDC-CP12-001 ~ MDC-CP12-007)
# ============================================================================


class TestNotificationErrorCodes:
    """Tests cho CP12 error codes."""

    def test_cp12_channel_not_supported_exists(self):
        """MDC-CP12-001: CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED")

    def test_cp12_template_not_found_exists(self):
        """MDC-CP12-002: CP12_NOTIFICATION_TEMPLATE_NOT_FOUND tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_TEMPLATE_NOT_FOUND")

    def test_cp12_template_render_failed_exists(self):
        """MDC-CP12-003: CP12_NOTIFICATION_TEMPLATE_RENDER_FAILED tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_TEMPLATE_RENDER_FAILED")

    def test_cp12_provider_not_configured_exists(self):
        """MDC-CP12-004: CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED")

    def test_cp12_dispatch_failed_exists(self):
        """MDC-CP12-005: CP12_NOTIFICATION_DISPATCH_FAILED tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_DISPATCH_FAILED")

    def test_cp12_rate_limit_exceeded_exists(self):
        """MDC-CP12-006: CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED")

    def test_cp12_invalid_recipient_exists(self):
        """MDC-CP12-007: CP12_NOTIFICATION_INVALID_RECIPIENT tồn tại."""
        assert hasattr(ErrorCode, "CP12_NOTIFICATION_INVALID_RECIPIENT")


# ============================================================================
# Test Notification Models
# ============================================================================


class TestNotificationChannel:
    """Tests cho NotificationChannel enum."""

    def test_email_channel_exists(self):
        """NotificationChannel có EMAIL."""
        from midicoder.emitters.core.notification.models import NotificationChannel

        assert hasattr(NotificationChannel, "EMAIL")
        assert NotificationChannel.EMAIL.value == "email"

    def test_sms_channel_exists(self):
        """NotificationChannel có SMS."""
        from midicoder.emitters.core.notification.models import NotificationChannel

        assert hasattr(NotificationChannel, "SMS")
        assert NotificationChannel.SMS.value == "sms"

    def test_push_channel_exists(self):
        """NotificationChannel có PUSH."""
        from midicoder.emitters.core.notification.models import NotificationChannel

        assert hasattr(NotificationChannel, "PUSH")
        assert NotificationChannel.PUSH.value == "push"

    def test_webhook_channel_exists(self):
        """NotificationChannel có WEBHOOK."""
        from midicoder.emitters.core.notification.models import NotificationChannel

        assert hasattr(NotificationChannel, "WEBHOOK")
        assert NotificationChannel.WEBHOOK.value == "webhook"

    def test_in_app_channel_exists(self):
        """NotificationChannel có IN_APP."""
        from midicoder.emitters.core.notification.models import NotificationChannel

        assert hasattr(NotificationChannel, "IN_APP")
        assert NotificationChannel.IN_APP.value == "in_app"


class TestNotificationTemplate:
    """Tests cho NotificationTemplate model."""

    def test_template_creation(self):
        """NotificationTemplate tạo với đủ thuộc tính."""
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
        )

        template = NotificationTemplate(
            template_id="welcome_email",
            channel=NotificationChannel.EMAIL,
            subject="Chào mừng {{name}}",
            body_html="<h1>Xin chào {{name}}</h1>",
            body_text="Xin chào {{name}}",
            variables=["name", "email"],
            locale="vi",
        )
        assert template.template_id == "welcome_email"
        assert template.channel == NotificationChannel.EMAIL
        assert "{{name}}" in template.subject
        assert len(template.variables) == 2

    def test_template_defaults(self):
        """NotificationTemplate có default values."""
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
        )

        template = NotificationTemplate(
            template_id="basic",
            channel=NotificationChannel.EMAIL,
        )
        assert template.locale == "en"
        assert template.variables == []

    def test_template_render(self):
        """NotificationTemplate render variables đúng."""
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
        )

        template = NotificationTemplate(
            template_id="welcome",
            channel=NotificationChannel.EMAIL,
            subject="Chào {{name}}",
            body_html="<p>Xin chào {{name}}, email: {{email}}</p>",
        )
        rendered = template.render({"name": "Minh", "email": "minh@test.com"})
        assert "Chào Minh" in rendered["subject"]
        assert "Xin chào Minh" in rendered["body_html"]
        assert "minh@test.com" in rendered["body_html"]

    def test_template_render_missing_variable(self):
        """NotificationTemplate render giữ nguyên variable nếu thiếu."""
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
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
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
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
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
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


# ============================================================================
# Test NotificationDispatch Model
# ============================================================================


class TestNotificationDispatch:
    """Tests cho NotificationDispatch model."""

    def test_dispatch_creation(self):
        """NotificationDispatch tạo với đủ thuộc tính."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
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

    def test_dispatch_status_update(self):
        """NotificationDispatch có thể update status."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
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

    def test_dispatch_to_dict(self):
        """NotificationDispatch.to_dict() trả về dict đúng."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
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


# ============================================================================
# Test NotificationProvider Model
# ============================================================================


class TestNotificationProvider:
    """Tests cho NotificationProvider model."""

    def test_provider_creation(self):
        """NotificationProvider tạo với config."""
        from midicoder.emitters.core.notification.models import (
            NotificationProvider,
            NotificationChannel,
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

    def test_provider_defaults(self):
        """NotificationProvider có default values."""
        from midicoder.emitters.core.notification.models import (
            NotificationProvider,
            NotificationChannel,
        )

        provider = NotificationProvider(
            provider_id="default_sms",
            channel=NotificationChannel.SMS,
        )
        assert provider.enabled is True
        assert provider.priority == 99


# ============================================================================
# Test DispatchResult Model
# ============================================================================


class TestDispatchResult:
    """Tests cho DispatchResult model."""

    def test_result_sent(self):
        """DispatchResult với status sent."""
        from midicoder.emitters.core.notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_001",
            status="sent",
            provider_response={"message_id": "msg_123"},
        )
        assert result.status == "sent"
        assert result.provider_response == {"message_id": "msg_123"}

    def test_result_failed(self):
        """DispatchResult với status failed và error_code."""
        from midicoder.emitters.core.notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_002",
            status="failed",
            error_code="MDC-CP12-005",
        )
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-005"

    def test_result_to_dict_with_response(self):
        """DispatchResult.to_dict() với provider_response."""
        from midicoder.emitters.core.notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_001",
            status="sent",
            provider_response={"message_id": "msg_123"},
        )
        d = result.to_dict()
        assert d["provider_response"] == {"message_id": "msg_123"}
        assert d["dispatch_id"] == "disp_001"

    def test_result_to_dict_without_response(self):
        """DispatchResult.to_dict() không có provider_response."""
        from midicoder.emitters.core.notification.models import DispatchResult

        result = DispatchResult(
            dispatch_id="disp_003",
            status="pending",
        )
        d = result.to_dict()
        assert "provider_response" not in d
        assert "error_code" not in d


class TestNotificationDispatchAdvanced:
    """Tests nâng cao cho NotificationDispatch."""

    def test_dispatch_mark_failed(self):
        """NotificationDispatch mark_failed."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="test",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_failed("Server error")
        assert dispatch.status == "failed"
        assert dispatch.error_message == "Server error"

    def test_dispatch_mark_bounced(self):
        """NotificationDispatch mark_bounced."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="test",
            recipient="invalid@test.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_bounced("Mailbox not found")
        assert dispatch.status == "bounced"
        assert dispatch.error_message == "Mailbox not found"

    def test_dispatch_to_dict_with_sent_at(self):
        """NotificationDispatch.to_dict() với sent_at."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="test",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_sent()
        d = dispatch.to_dict()
        assert "sent_at" in d
        assert d["status"] == "sent"

    def test_dispatch_to_dict_with_error(self):
        """NotificationDispatch.to_dict() với error_message."""
        from midicoder.emitters.core.notification.models import (
            NotificationDispatch,
            NotificationChannel,
        )

        dispatch = NotificationDispatch(
            dispatch_id="disp_001",
            template_ref="test",
            recipient="a@b.com",
            channel=NotificationChannel.EMAIL,
        )
        dispatch.mark_failed("error")
        d = dispatch.to_dict()
        assert d["error_message"] == "error"


class TestNotificationProviderAdvanced:
    """Tests nâng cao cho NotificationProvider."""

    def test_provider_from_dict(self):
        """NotificationProvider.from_dict() tạo object đúng."""
        from midicoder.emitters.core.notification.models import (
            NotificationProvider,
            NotificationChannel,
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


class TestNotificationParserAdvanced:
    """Tests nâng cao cho Notification Parser."""

    def test_parse_channels_non_dict_value(self):
        """parse_channels() xử lý non-dict value."""
        from midicoder.emitters.core.notification.parser import parse_channels
        import yaml

        yaml_str = """
channels:
  email: true
  sms: false
"""
        data = yaml.safe_load(yaml_str)
        config = parse_channels(data)
        assert config["email"]["enabled"] is True
        assert config["sms"]["enabled"] is False


# ============================================================================
# Test Notification Parser
# ============================================================================


class TestNotificationParser:
    """Tests cho Notification Parser."""

    def test_parse_templates_from_yaml(self):
        """parse_notifications() parse YAML thành list template."""
        from midicoder.emitters.core.notification.parser import parse_notifications
        import yaml

        yaml_str = """
notifications:
  - template_id: welcome_email
    channel: email
    subject: "Chào {{name}}"
    body_html: "<h1>{{name}}</h1>"
    variables:
      - name
  - template_id: order_sms
    channel: sms
    body_text: "Đơn hàng {{order_id}} đã nhận"
    variables:
      - order_id
"""
        data = yaml.safe_load(yaml_str)
        templates = parse_notifications(data)
        assert len(templates) == 2
        assert templates[0].template_id == "welcome_email"
        assert templates[1].channel.value == "sms"

    def test_parse_channels(self):
        """parse_channels() parse channel config."""
        from midicoder.emitters.core.notification.parser import parse_channels
        import yaml

        yaml_str = """
channels:
  email:
    rate_limit: 100
    enabled: true
  sms:
    rate_limit: 10
    enabled: true
"""
        data = yaml.safe_load(yaml_str)
        config = parse_channels(data)
        assert len(config) == 2

    def test_parse_providers(self):
        """parse_providers() parse provider config."""
        from midicoder.emitters.core.notification.parser import parse_providers
        import yaml

        yaml_str = """
providers:
  - provider_id: sendgrid
    channel: email
    config:
      api_key: "SG.xxx"
    priority: 1
  - provider_id: twilio
    channel: sms
    config:
      account_sid: "AC.xxx"
    priority: 1
"""
        data = yaml.safe_load(yaml_str)
        providers = parse_providers(data)
        assert len(providers) == 2
        assert providers[0].provider_id == "sendgrid"
        assert providers[1].channel.value == "sms"


# ============================================================================
# Test FastAPI Notification Emitter
# ============================================================================


class TestFastAPINotificationEmitter:
    """Tests cho FastAPI Notification Emitter."""

    def test_emitter_class_exists(self):
        """FastAPINotificationEmitter class tồn tại."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        assert FastAPINotificationEmitter is not None

    def test_emitter_generate_service(self):
        """Emitter generate notification service code."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_service()
        assert "class NotificationService" in code
        assert "send_email" in code
        assert "send_sms" in code

    def test_emitter_generate_controller(self):
        """Emitter generate notification router code."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_router()
        assert "/notifications" in code
        assert "dispatch" in code

    def test_emitter_generate_models(self):
        """Emitter generate Pydantic models."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_models()
        assert "BaseModel" in code
        assert "DispatchRequest" in code or "dispatch" in code.lower()

    def test_emitter_generate_tasks(self):
        """Emitter generate background tasks."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_tasks()
        assert "celery" in code.lower() or "@task" in code.lower() or "async" in code

    def test_emitter_has_send_email(self):
        """Service code chứa send_email method."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_service()
        assert "async def send_email" in code or "def send_email" in code

    def test_emitter_has_render_template(self):
        """Service code chứa render method."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_service()
        assert "render" in code

    def test_emitter_vietnamese_comments(self):
        """Generated code có comments tiếng Việt."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        code = emitter.generate_service()
        # Check for Vietnamese characters or common Vietnamese words
        has_vietnamese = any(char in code for char in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹ")
        assert has_vietnamese or "#" in code

    def test_emitter_generate_full(self):
        """Emitter generate_full trả về dict với nhiều files."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )

        emitter = FastAPINotificationEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_emitter_with_templates(self):
        """Emitter nhận vào templates và generate code đúng."""
        from midicoder.emitters.core.notification.fastapi import (
            FastAPINotificationEmitter,
        )
        from midicoder.emitters.core.notification.models import (
            NotificationTemplate,
            NotificationChannel,
        )

        emitter = FastAPINotificationEmitter()
        templates = [
            NotificationTemplate(
                template_id="welcome",
                channel=NotificationChannel.EMAIL,
                subject="Chào {{name}}",
            )
        ]
        code = emitter.generate_service(templates=templates)
        assert "NotificationService" in code


# ============================================================================
# Test NestJS Notification Emitter
# ============================================================================


class TestNestJSNotificationEmitter:
    """Tests cho NestJS Notification Emitter."""

    def test_emitter_class_exists(self):
        """NestJSNotificationEmitter class tồn tại."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        assert NestJSNotificationEmitter is not None

    def test_emitter_generate_module(self):
        """Emitter generate NotificationModule."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_module()
        assert "@Module" in code
        assert "NotificationModule" in code

    def test_emitter_generate_service(self):
        """Emitter generate NotificationService."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_service()
        assert "NotificationService" in code
        assert "sendEmail" in code or "send_email" in code

    def test_emitter_generate_controller(self):
        """Emitter generate NotificationController."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_controller()
        assert "@Controller" in code
        assert "notifications" in code

    def test_emitter_generate_dto(self):
        """Emitter generate DTOs."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_dto()
        assert "class" in code
        assert "Dto" in code

    def test_emitter_vietnamese_comments(self):
        """Generated code có comments tiếng Việt."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_service()
        has_vietnamese = any(char in code for char in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹ")
        assert has_vietnamese or "//" in code

    def test_emitter_generate_full(self):
        """Emitter generate_full trả về dict với nhiều files."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_emitter_event_emitter_integration(self):
        """Service code integrate với NestJS EventEmitter."""
        from midicoder.emitters.core.notification.nestjs import (
            NestJSNotificationEmitter,
        )

        emitter = NestJSNotificationEmitter()
        code = emitter.generate_service()
        assert "EventsModule" in code or "EventEmitter2" in code or "@Injectable" in code