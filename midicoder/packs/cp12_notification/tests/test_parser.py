"""
Tests cho CP12 Notification Parser.

Test coverage:
- parse_notifications: 4 tests
- parse_channels: 4 tests
- parse_providers: 4 tests

Tổng: 12 tests
"""

from __future__ import annotations

import yaml
import pytest


# ============================================================================
# Test parse_notifications
# ============================================================================


class TestParseNotifications:
    """Tests cho parse_notifications function."""

    def test_parse_single_notification(self):
        """Parse một notification template."""
        from midicoder.packs.cp12_notification.parser import parse_notifications
        from midicoder.packs.cp12_notification.models import NotificationChannel

        data = {
            "notifications": [
                {
                    "template_id": "welcome_email",
                    "channel": "email",
                    "subject": "Chào {{name}}",
                    "body_html": "<h1>{{name}}</h1>",
                    "variables": ["name"],
                }
            ]
        }
        templates = parse_notifications(data)
        assert len(templates) == 1
        assert templates[0].template_id == "welcome_email"
        assert templates[0].channel == NotificationChannel.EMAIL

    def test_parse_multiple_notifications(self):
        """Parse nhiều notification templates."""
        from midicoder.packs.cp12_notification.parser import parse_notifications

        data = {
            "notifications": [
                {"template_id": "welcome", "channel": "email", "subject": "Hi"},
                {"template_id": "order_sms", "channel": "sms", "body_text": "Đơn hàng nhận"},
            ]
        }
        templates = parse_notifications(data)
        assert len(templates) == 2
        assert templates[0].template_id == "welcome"
        assert templates[1].template_id == "order_sms"

    def test_parse_from_yaml_string(self):
        """Parse notifications từ YAML string."""
        from midicoder.packs.cp12_notification.parser import parse_notifications

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

    def test_parse_empty_notifications(self):
        """Parse khi không có notifications."""
        from midicoder.packs.cp12_notification.parser import parse_notifications

        data = {}
        templates = parse_notifications(data)
        assert len(templates) == 0


# ============================================================================
# Test parse_channels
# ============================================================================


class TestParseChannels:
    """Tests cho parse_channels function."""

    def test_parse_channels_dict(self):
        """Parse channels với dict config."""
        from midicoder.packs.cp12_notification.parser import parse_channels

        data = {
            "channels": {
                "email": {"rate_limit": 100, "enabled": True},
                "sms": {"rate_limit": 10, "enabled": True},
            }
        }
        config = parse_channels(data)
        assert len(config) == 2
        assert config["email"]["rate_limit"] == 100

    def test_parse_channels_boolean(self):
        """Parse channels với boolean value."""
        from midicoder.packs.cp12_notification.parser import parse_channels

        data = {
            "channels": {
                "email": True,
                "sms": False,
            }
        }
        config = parse_channels(data)
        assert config["email"]["enabled"] is True
        assert config["sms"]["enabled"] is False

    def test_parse_channels_from_yaml(self):
        """Parse channels từ YAML string."""
        from midicoder.packs.cp12_notification.parser import parse_channels

        yaml_str = """
channels:
  email: true
  sms: false
"""
        data = yaml.safe_load(yaml_str)
        config = parse_channels(data)
        assert config["email"]["enabled"] is True

    def test_parse_empty_channels(self):
        """Parse khi không có channels."""
        from midicoder.packs.cp12_notification.parser import parse_channels

        data = {}
        config = parse_channels(data)
        assert len(config) == 0


# ============================================================================
# Test parse_providers
# ============================================================================


class TestParseProviders:
    """Tests cho parse_providers function."""

    def test_parse_providers(self):
        """Parse providers từ YAML."""
        from midicoder.packs.cp12_notification.parser import parse_notifications
        from midicoder.packs.cp12_notification.parser import parse_providers
        from midicoder.packs.cp12_notification.models import NotificationChannel

        data = {
            "providers": [
                {"provider_id": "sendgrid", "channel": "email", "priority": 1},
                {"provider_id": "twilio", "channel": "sms", "priority": 1},
            ]
        }
        providers = parse_providers(data)
        assert len(providers) == 2
        assert providers[0].provider_id == "sendgrid"
        assert providers[1].channel == NotificationChannel.SMS

    def test_parse_providers_sorted_by_priority(self):
        """Providers được sắp xếp theo priority."""
        from midicoder.packs.cp12_notification.parser import parse_providers

        data = {
            "providers": [
                {"provider_id": "backup", "channel": "email", "priority": 10},
                {"provider_id": "primary", "channel": "email", "priority": 1},
            ]
        }
        providers = parse_providers(data)
        assert providers[0].provider_id == "primary"
        assert providers[1].provider_id == "backup"

    def test_parse_providers_from_yaml(self):
        """Parse providers từ YAML string."""
        from midicoder.packs.cp12_notification.parser import parse_providers

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

    def test_parse_empty_providers(self):
        """Parse khi không có providers."""
        from midicoder.packs.cp12_notification.parser import parse_providers

        data = {}
        providers = parse_providers(data)
        assert len(providers) == 0
