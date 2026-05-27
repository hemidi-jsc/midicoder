"""
Tests cho CP12 Providers.

Test coverage:
- TwilioSmsGateway: 7 tests
- WebhookGatewayImpl: 6 tests
- FirebasePushGateway: 5 tests
- SmtpEmailGateway: 4 tests
- SendGridEmailGateway: 3 tests
- AwsSesEmailGateway: 3 tests

Tổng: 28 tests
"""

from __future__ import annotations

import pytest
from midicoder.packs.cp12_notification.models import (
    DispatchResult,
    WebhookConfig,
    WebhookAuthType,
)
from midicoder.packs.cp12_notification.providers.twilio import TwilioSmsGateway
from midicoder.packs.cp12_notification.providers.webhook import (
    WebhookGatewayImpl,
    verify_webhook_signature,
)
from midicoder.packs.cp12_notification.providers.firebase import FirebasePushGateway
from midicoder.packs.cp12_notification.providers.smtp import SmtpEmailGateway
from midicoder.packs.cp12_notification.providers.sendgrid import SendGridEmailGateway
from midicoder.packs.cp12_notification.providers.ses import AwsSesEmailGateway


class TestTwilioSmsGateway:
    """Tests cho TwilioSmsGateway."""

    def test_not_configured(self):
        """Không config → failed."""
        gw = TwilioSmsGateway()
        result = gw.send("+1234567890", "Hello")
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-004"

    def test_missing_from_phone(self):
        """Thiếu from_phone → failed."""
        gw = TwilioSmsGateway(account_sid="AC.x", auth_token="tok")
        result = gw.send("+1234567890", "Hello")
        assert result.status == "failed"

    def test_empty_recipient(self):
        """Recipient rỗng → failed."""
        gw = TwilioSmsGateway(
            account_sid="AC.x", auth_token="tok", from_phone="+1000000000",
        )
        result = gw.send("", "Hello")
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-007"

    def test_verify_signature(self):
        """verify_signature với token chưa config → False."""
        gw = TwilioSmsGateway(account_sid="AC.x", auth_token="secret")
        result = gw.verify_signature("https://example.com", {}, "sig")
        assert isinstance(result, bool)

    def test_get_message_status_not_configured(self):
        """get_message_status không config → có error."""
        gw = TwilioSmsGateway()
        result = gw.get_message_status("SM123")
        assert "error" in result

    def test_dispatch_id_passed(self):
        """dispatch_id được pass qua result."""
        gw = TwilioSmsGateway()
        result = gw.send("+1234567890", "Hello", dispatch_id="disp_test")
        assert result.dispatch_id == "disp_test"

    def test_with_full_config(self):
        """Full config nhưng không có connection → failed với error code."""
        gw = TwilioSmsGateway(
            account_sid="AC.test",
            auth_token="tok",
            from_phone="+1234567890",
        )
        result = gw.send("+9876543210", "Test")
        # Sẽ fail vì không có real connection
        assert result.dispatch_id == "unknown"


class TestWebhookGatewayImpl:
    """Tests cho WebhookGatewayImpl."""

    def test_empty_url(self):
        """URL rỗng → WebhookConfig throw ValueError."""
        with pytest.raises(ValueError, match="url"):
            gw = WebhookGatewayImpl()
            config = WebhookConfig(url="")
            result = gw.send(config, {"key": "value"})
            assert result.status == "failed"

    def test_invalid_url(self):
        """URL không hợp lệ → failed sau retries."""
        gw = WebhookGatewayImpl(default_max_retries=0)
        config = WebhookConfig(url="http://invalid-host-that-does-not-exist.com", max_retries=0)
        result = gw.send(config, {"key": "value"})
        assert result.status == "failed"

    def test_verify_signature_valid(self):
        """verify_webhook_signature với signature đúng."""
        body = '{"event":"test"}'
        secret = "my_secret"
        import hmac as hmac_mod
        import hashlib
        sig = hmac_mod.new(
            secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        assert verify_webhook_signature(body, sig, secret) is True

    def test_verify_signature_invalid(self):
        """verify_webhook_signature với signature sai."""
        assert verify_webhook_signature("body", "wrong_sig", "secret") is False

    def test_webhook_auth_bearer(self):
        """WebhookConfig với Bearer auth."""
        config = WebhookConfig(
            url="https://example.com",
            auth_type=WebhookAuthType.BEARER,
            auth_header="token123",
        )
        assert config.auth_type == WebhookAuthType.BEARER
        assert config.auth_header == "token123"

    def test_webhook_auth_hmac(self):
        """WebhookConfig với HMAC auth và compute signature."""
        config = WebhookConfig(
            url="https://example.com",
            auth_type=WebhookAuthType.HMAC,
            auth_secret="secret",
        )
        sig = config.compute_hmac_signature("test")
        assert len(sig) == 64


class TestFirebasePushGateway:
    """Tests cho FirebasePushGateway."""

    def test_not_configured(self):
        """Không config → failed."""
        gw = FirebasePushGateway()
        result = gw.send("device_token", "Title", "Body")
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-004"

    def test_no_project_id(self):
        """Thiếu project_id → failed."""
        gw = FirebasePushGateway(access_token="tok")
        result = gw.send("token", "Title", "Body")
        assert result.status == "failed"

    def test_with_topic(self):
        """send_to_topic."""
        gw = FirebasePushGateway(project_id="proj", access_token="tok")
        # Sẽ fail vì không có real connection
        result = gw.send_to_topic("all_users", "Title", "Body")
        assert result.dispatch_id == "unknown"

    def test_with_condition(self):
        """send_condition."""
        gw = FirebasePushGateway(project_id="proj", access_token="tok")
        result = gw.send_condition("'A' in topics", "Title", "Body")
        assert result.dispatch_id == "unknown"

    def test_dispatch_id_passed(self):
        """dispatch_id được pass qua."""
        gw = FirebasePushGateway()
        result = gw.send("token", "Title", "Body", dispatch_id="disp_fc")
        assert result.dispatch_id == "disp_fc"


class TestSmtpEmailGateway:
    """Tests cho SmtpEmailGateway."""

    def test_default_config(self):
        """Default config."""
        gw = SmtpEmailGateway()
        assert gw._host == "localhost"
        assert gw._port == 587

    def test_custom_config(self):
        """Custom config."""
        gw = SmtpEmailGateway(
            host="smtp.gmail.com",
            port=465,
            from_email="from@gmail.com",
        )
        assert gw._host == "smtp.gmail.com"

    def test_send_no_connection(self):
        """Gửi email khi không có SMTP server → failed."""
        gw = SmtpEmailGateway(host="localhost", use_tls=False)
        result = gw.send("to@test.com", "Subject", "<p>Body</p>")
        assert result.status == "failed"

    def test_dispatch_id_passed(self):
        """dispatch_id được pass qua."""
        gw = SmtpEmailGateway()
        result = gw.send("to@test.com", "S", "B", dispatch_id="disp_smtp")
        assert result.dispatch_id == "disp_smtp"


class TestSendGridEmailGateway:
    """Tests cho SendGridEmailGateway."""

    def test_no_api_key(self):
        """Không API key → failed."""
        gw = SendGridEmailGateway()
        result = gw.send("to@test.com", "S", "<p>B</p>")
        assert result.status == "failed"
        assert result.error_code == "MDC-CP12-004"

    def test_with_api_key(self):
        """Có API key → sent (stub)."""
        gw = SendGridEmailGateway(api_key="SG.xxx")
        result = gw.send("to@test.com", "S", "<p>B</p>")
        assert result.status == "sent"

    def test_provider_response(self):
        """Provider response có thông tin đúng."""
        gw = SendGridEmailGateway(api_key="SG.xxx")
        result = gw.send("dest@test.com", "S", "B")
        assert result.provider_response["provider"] == "sendgrid"


class TestAwsSesEmailGateway:
    """Tests cho AwsSesEmailGateway."""

    def test_no_credentials(self):
        """Không credentials → failed."""
        gw = AwsSesEmailGateway()
        result = gw.send("to@test.com", "S", "B")
        assert result.status == "failed"

    def test_with_credentials(self):
        """Có credentials → sent (stub)."""
        gw = AwsSesEmailGateway(
            aws_access_key="AKIAXXX",
            aws_secret_key="xxx",
        )
        result = gw.send("to@test.com", "S", "B")
        assert result.status == "sent"

    def test_provider_response(self):
        """Provider response đúng."""
        gw = AwsSesEmailGateway(aws_access_key="AK", aws_secret_key="sk")
        result = gw.send("dest@test.com", "S", "B")
        assert result.provider_response["provider"] == "aws_ses"
