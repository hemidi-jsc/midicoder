"""
Tests cho CP12 Recipes.

Test coverage:
- SMTPEmailRecipe: 3 tests
- SendGridEmailRecipe: 2 tests
- SESEmailRecipe: 2 tests
- TwilioSMSRecipe: 4 tests
- FCMRecipe: 3 tests
- WebhookRecipe: 5 tests
- DeliveryTrackingRecipe: 2 tests
- ABTestRecipe: 6 tests

Tổng: 27 tests
"""

from __future__ import annotations

import pytest
from midicoder.packs.cp_full_notification.models import (
    NotificationChannel,
    WebhookAuthType,
)
from midicoder.packs.cp_full_notification.recipes import (
    SMTPEmailRecipe,
    SendGridEmailRecipe,
    SESEmailRecipe,
    TwilioSMSRecipe,
    FCMRecipe,
    WebhookRecipe,
    DeliveryTrackingRecipe,
    ABTestRecipe,
)


class TestSMTPEmailRecipe:
    """Tests cho SMTPEmailRecipe."""

    def test_build_provider(self):
        """Build provider đúng config."""
        r = SMTPEmailRecipe(host="smtp.gmail.com", port=587, from_email="from@test.com")
        p = r.build_provider()
        assert p.provider_id == "smtp_default"
        assert p.channel == NotificationChannel.EMAIL
        assert p.config["host"] == "smtp.gmail.com"

    def test_provider_enabled(self):
        """Provider enabled=True."""
        r = SMTPEmailRecipe()
        p = r.build_provider()
        assert p.enabled is True

    def test_custom_provider_id(self):
        """Custom provider_id."""
        r = SMTPEmailRecipe(provider_id="custom_smtp")
        p = r.build_provider()
        assert p.provider_id == "custom_smtp"


class TestSendGridEmailRecipe:
    """Tests cho SendGridEmailRecipe."""

    def test_with_api_key(self):
        """Có API key → enabled."""
        r = SendGridEmailRecipe(api_key="SG.xxx")
        p = r.build_provider()
        assert p.enabled is True
        assert p.config["type"] == "sendgrid"

    def test_without_api_key(self):
        """Không API key → disabled."""
        r = SendGridEmailRecipe()
        p = r.build_provider()
        assert p.enabled is False


class TestSESEmailRecipe:
    """Tests cho SESEmailRecipe."""

    def test_with_credentials(self):
        """Có credentials → enabled."""
        r = SESEmailRecipe(aws_access_key="AKIA", aws_secret_key="sk")
        p = r.build_provider()
        assert p.enabled is True
        assert p.config["region"] == "us-east-1"

    def test_without_credentials(self):
        """Thiếu credentials → disabled."""
        r = SESEmailRecipe()
        p = r.build_provider()
        assert p.enabled is False


class TestTwilioSMSRecipe:
    """Tests cho TwilioSMSRecipe."""

    def test_build_provider_full(self):
        """Full config → enabled."""
        r = TwilioSMSRecipe(
            account_sid="AC.x", auth_token="tok", from_phone="+1234567890",
        )
        p = r.build_provider()
        assert p.enabled is True
        assert p.config["type"] == "twilio"

    def test_build_provider_incomplete(self):
        """Thiếu from_phone → disabled."""
        r = TwilioSMSRecipe(account_sid="AC.x", auth_token="tok")
        p = r.build_provider()
        assert p.enabled is False

    def test_welcome_template(self):
        """Build welcome SMS template."""
        r = TwilioSMSRecipe()
        t = r.build_welcome_template()
        assert t.template_id == "sms_welcome"
        assert t.channel == NotificationChannel.SMS
        assert "name" in t.variables

    def test_verification_template(self):
        """Build verification template."""
        r = TwilioSMSRecipe()
        t = r.build_verification_template()
        assert t.template_id == "sms_verification"
        assert "code" in t.variables


class TestFCMRecipe:
    """Tests cho FCMRecipe."""

    def test_with_access_token(self):
        """Có access_token → enabled."""
        r = FCMRecipe(project_id="proj", access_token="ya29.xxx")
        p = r.build_provider()
        assert p.enabled is True

    def test_with_credentials_path(self):
        """Có credentials_path → enabled."""
        r = FCMRecipe(project_id="proj", credentials_path="/path/to/creds.json")
        p = r.build_provider()
        assert p.enabled is True

    def test_order_update_template(self):
        """Build order update template."""
        r = FCMRecipe()
        t = r.build_order_update_template()
        assert t.channel == NotificationChannel.PUSH


class TestWebhookRecipe:
    """Tests cho WebhookRecipe."""

    def test_basic(self):
        """Build basic config."""
        r = WebhookRecipe(url="https://example.com/webhook")
        c = r.build_config()
        assert c.url == "https://example.com/webhook"
        assert c.auth_type == WebhookAuthType.NONE

    def test_with_bearer(self):
        """with_bearer factory."""
        r = WebhookRecipe.with_bearer("https://example.com", "token123")
        c = r.build_config()
        assert c.auth_type == WebhookAuthType.BEARER
        assert c.auth_header == "token123"

    def test_with_hmac(self):
        """with_hmac factory."""
        r = WebhookRecipe.with_hmac("https://example.com", "secret")
        c = r.build_config()
        assert c.auth_type == WebhookAuthType.HMAC
        assert c.auth_secret == "secret"

    def test_with_basic_auth(self):
        """with_basic factory."""
        r = WebhookRecipe.with_basic("https://example.com", "user:pass")
        c = r.build_config()
        assert c.auth_type == WebhookAuthType.BASIC

    def test_custom_options(self):
        """Custom timeout, retries."""
        r = WebhookRecipe(
            url="https://example.com",
            timeout_seconds=60,
            max_retries=5,
        )
        c = r.build_config()
        assert c.timeout_seconds == 60
        assert c.max_retries == 5


class TestDeliveryTrackingRecipe:
    """Tests cho DeliveryTrackingRecipe."""

    def test_create_tracking(self):
        """Create delivery tracking."""
        r = DeliveryTrackingRecipe(dispatch_id="disp_001")
        t = r.create("user@example.com", NotificationChannel.EMAIL)
        assert t.dispatch_id == "disp_001"
        assert t.channel == NotificationChannel.EMAIL

    def test_with_metadata(self):
        """With metadata."""
        r = DeliveryTrackingRecipe(
            dispatch_id="d1",
            metadata={"campaign": "welcome"},
        )
        t = r.create("u@e.com", NotificationChannel.EMAIL)
        assert t.metadata["campaign"] == "welcome"


class TestABTestRecipe:
    """Tests cho ABTestRecipe."""

    def test_build_two_variants(self):
        """Build 2 variants 50/50."""
        r = ABTestRecipe(name="Test", channel=NotificationChannel.EMAIL)
        r.add_variant("A", "tmpl_a", weight=50.0)
        r.add_variant("B", "tmpl_b", weight=50.0)
        config = r.build()
        assert len(config.variants) == 2
        assert config.name == "Test"

    def test_build_three_variants(self):
        """Build 3 variants 33/33/34."""
        r = ABTestRecipe(name="Test", channel=NotificationChannel.EMAIL)
        r.add_variant("A", "t1", weight=33.33)
        r.add_variant("B", "t2", weight=33.33)
        r.add_variant("C", "t3", weight=33.34)
        config = r.build()
        assert len(config.variants) == 3

    def test_less_than_two_variants_raises(self):
        """Ít hơn 2 variants raise."""
        r = ABTestRecipe(name="Test", channel=NotificationChannel.EMAIL)
        r.add_variant("A", "t1", weight=100)
        with pytest.raises(ValueError, match="ít nhất 2"):
            r.build()

    def test_weight_not_100_raises(self):
        """Total weight != 100 raise."""
        r = ABTestRecipe(name="Test", channel=NotificationChannel.EMAIL)
        r.add_variant("A", "t1", weight=60)
        r.add_variant("B", "t2", weight=60)
        with pytest.raises(ValueError, match="100"):
            r.build()

    def test_simple_email_test_factory(self):
        """simple_email_test factory."""
        config = ABTestRecipe.simple_email_test(
            "Welcome Test", "welcome_v1", "welcome_v2"
        )
        assert len(config.variants) == 2
        assert config.channel == NotificationChannel.EMAIL

    def test_three_way_test_factory(self):
        """three_way_test factory."""
        config = ABTestRecipe.three_way_test(
            "Test", NotificationChannel.PUSH, "t1", "t2", "t3"
        )
        assert len(config.variants) == 3
        assert config.metric == "click_rate"
