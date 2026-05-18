# coding: utf-8
"""
Test cases cho các models mới của CP16.

Kiểm tra:
- HealthCheck: tạo hợp lệ, validation (name rỗng, path sai, interval < 5, timeout < 1), to_dict/from_dict
- NotificationChannel: tạo hợp lệ, validation (name rỗng, endpoint rỗng), to_dict/from_dict
- EscalationPolicy: tạo hợp lệ, validation (name rỗng, timeout < 60), to_dict/from_dict
- SLOTracking: tạo hợp lệ, validation (name rỗng, target <= 0, budget < 3600), to_dict/from_dict
- SLOBurnRate: enum values
- HealthCheckType: enum values
- NotificationChannelType: enum values
"""

import pytest

from midicoder.emitters.core.cp16_monitoring.models import (
    EscalationPolicy,
    HealthCheck,
    HealthCheckType,
    NotificationChannel,
    NotificationChannelType,
    SLOBurnRate,
    SLOTracking,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestHealthCheckType:
    """Test HealthCheckType enum."""

    def test_liveness_value(self):
        assert HealthCheckType.LIVENESS.value == "liveness"

    def test_readiness_value(self):
        assert HealthCheckType.READINESS.value == "readiness"

    def test_custom_value(self):
        assert HealthCheckType.CUSTOM.value == "custom"

    def test_total_count(self):
        assert len(HealthCheckType) == 3


class TestNotificationChannelType:
    """Test NotificationChannelType enum."""

    def test_email_value(self):
        assert NotificationChannelType.EMAIL.value == "email"

    def test_slack_value(self):
        assert NotificationChannelType.SLACK.value == "slack"

    def test_webhook_value(self):
        assert NotificationChannelType.WEBHOOK.value == "webhook"

    def test_pagerduty_value(self):
        assert NotificationChannelType.PAGERDUTY.value == "pagerduty"

    def test_opsgenie_value(self):
        assert NotificationChannelType.OPSGENIE.value == "opsgenie"

    def test_total_count(self):
        assert len(NotificationChannelType) == 5


class TestSLOBurnRate:
    """Test SLOBurnRate enum."""

    def test_one_hour_value(self):
        assert SLOBurnRate.ONE_HOUR.value == "1h"

    def test_six_hour_value(self):
        assert SLOBurnRate.SIX_HOUR.value == "6h"

    def test_twelve_hour_value(self):
        assert SLOBurnRate.TWELVE_HOUR.value == "12h"

    def test_two_day_value(self):
        assert SLOBurnRate.TWO_DAY.value == "2d"

    def test_seven_day_value(self):
        assert SLOBurnRate.SEVEN_DAY.value == "7d"

    def test_total_count(self):
        assert len(SLOBurnRate) == 5


# ===========================================================================
# HealthCheck Tests
# ===========================================================================


class TestHealthCheck:
    """Test HealthCheck dataclass."""

    def test_create_liveness_check(self):
        hc = HealthCheck(name="api-liveness")
        assert hc.name == "api-liveness"
        assert hc.check_type == HealthCheckType.LIVENESS
        assert hc.path == "/health"
        assert hc.interval_seconds == 10
        assert hc.timeout_seconds == 5
        assert hc.unhealthy_threshold == 3

    def test_create_readiness_check(self):
        hc = HealthCheck(
            name="api-readiness",
            check_type=HealthCheckType.READINESS,
            path="/health/ready",
            interval_seconds=15,
            timeout_seconds=3,
        )
        assert hc.check_type == HealthCheckType.READINESS
        assert hc.path == "/health/ready"
        assert hc.interval_seconds == 15

    def test_create_custom_check(self):
        hc = HealthCheck(
            name="queue-check",
            check_type=HealthCheckType.CUSTOM,
            path="/health/queue",
            tags={"component": "rabbitmq"},
        )
        assert hc.check_type == HealthCheckType.CUSTOM
        assert hc.tags == {"component": "rabbitmq"}

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            HealthCheck(name="")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_HEALTH_CHECK_NAME

    def test_whitespace_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            HealthCheck(name="   ")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_HEALTH_CHECK_NAME

    def test_invalid_path_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            HealthCheck(name="test", path="health")
        assert exc_info.value.code == ErrorCode.CP16_INVALID_HEALTH_CHECK_PATH

    def test_interval_less_than_5_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            HealthCheck(name="test", interval_seconds=3)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_timeout_less_than_1_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            HealthCheck(name="test", timeout_seconds=0)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_to_dict(self):
        hc = HealthCheck(name="api", check_type=HealthCheckType.READINESS, path="/ready")
        d = hc.to_dict()
        assert d["name"] == "api"
        assert d["check_type"] == "readiness"
        assert d["path"] == "/ready"

    def test_from_dict(self):
        d = {"name": "test", "check_type": "custom", "path": "/custom", "interval_seconds": 20}
        hc = HealthCheck.from_dict(d)
        assert hc.name == "test"
        assert hc.check_type == HealthCheckType.CUSTOM
        assert hc.interval_seconds == 20

    def test_roundtrip(self):
        original = HealthCheck(name="rt", check_type=HealthCheckType.LIVENESS, path="/live", interval_seconds=10)
        restored = HealthCheck.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.check_type == original.check_type
        assert restored.path == original.path


# ===========================================================================
# NotificationChannel Tests
# ===========================================================================


class TestNotificationChannel:
    """Test NotificationChannel dataclass."""

    def test_create_email_channel(self):
        ch = NotificationChannel(
            name="team-email",
            channel_type=NotificationChannelType.EMAIL,
            endpoint="team@example.com",
        )
        assert ch.channel_type == NotificationChannelType.EMAIL
        assert ch.enabled is True

    def test_create_slack_channel(self):
        ch = NotificationChannel(
            name="ops-slack",
            channel_type=NotificationChannelType.SLACK,
            endpoint="https://hooks.slack.com/xxx",
            severity_filter=["critical"],
        )
        assert ch.severity_filter == ["critical"]

    def test_create_pagerduty_channel(self):
        ch = NotificationChannel(
            name="pd-critical",
            channel_type=NotificationChannelType.PAGERDUTY,
            endpoint="integration-key",
            enabled=False,
        )
        assert ch.enabled is False

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            NotificationChannel(name="", channel_type=NotificationChannelType.EMAIL, endpoint="x@x.com")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_ALERT_NAME

    def test_empty_endpoint_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            NotificationChannel(name="test", channel_type=NotificationChannelType.EMAIL, endpoint="")
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_whitespace_endpoint_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            NotificationChannel(name="test", channel_type=NotificationChannelType.EMAIL, endpoint="   ")
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_to_dict(self):
        ch = NotificationChannel(name="e", channel_type=NotificationChannelType.EMAIL, endpoint="a@b.com")
        d = ch.to_dict()
        assert d["name"] == "e"
        assert d["channel_type"] == "email"
        assert d["enabled"] is True

    def test_from_dict(self):
        d = {"name": "slack", "channel_type": "slack", "endpoint": "https://x.com", "enabled": False}
        ch = NotificationChannel.from_dict(d)
        assert ch.name == "slack"
        assert ch.channel_type == NotificationChannelType.SLACK
        assert ch.enabled is False

    def test_roundtrip(self):
        original = NotificationChannel(
            name="rt", channel_type=NotificationChannelType.WEBHOOK, endpoint="https://webhook.com",
            severity_filter=["critical", "warning"], enabled=True,
        )
        restored = NotificationChannel.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.channel_type == original.channel_type
        assert restored.severity_filter == original.severity_filter


# ===========================================================================
# EscalationPolicy Tests
# ===========================================================================


class TestEscalationPolicy:
    """Test EscalationPolicy dataclass."""

    def test_create_standard_escalation(self):
        ep = EscalationPolicy(name="standard", levels=["L1", "L2", "L3"])
        assert ep.levels == ["L1", "L2", "L3"]
        assert ep.timeout_seconds == 300

    def test_create_with_channels(self):
        ep = EscalationPolicy(
            name="with-channels",
            levels=["primary", "secondary"],
            timeout_seconds=120,
            channels=["email", "pagerduty"],
        )
        assert ep.channels == ["email", "pagerduty"]
        assert ep.timeout_seconds == 120

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            EscalationPolicy(name="")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_ESCALATION_NAME

    def test_whitespace_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            EscalationPolicy(name="   ")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_ESCALATION_NAME

    def test_timeout_less_than_60_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            EscalationPolicy(name="test", timeout_seconds=30)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_to_dict(self):
        ep = EscalationPolicy(name="s", levels=["a", "b"], timeout_seconds=120, channels=["c"])
        d = ep.to_dict()
        assert d["name"] == "s"
        assert d["levels"] == ["a", "b"]
        assert d["channels"] == ["c"]

    def test_from_dict(self):
        d = {"name": "e", "levels": ["x", "y"], "timeout_seconds": 60, "channels": ["z"]}
        ep = EscalationPolicy.from_dict(d)
        assert ep.name == "e"
        assert ep.levels == ["x", "y"]

    def test_roundtrip(self):
        original = EscalationPolicy(name="rt", levels=["l1"], timeout_seconds=180, channels=["ch"])
        restored = EscalationPolicy.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.levels == original.levels
        assert restored.timeout_seconds == original.timeout_seconds


# ===========================================================================
# SLOTracking Tests
# ===========================================================================


class TestSLOTracking:
    """Test SLOTracking dataclass."""

    def test_create_availability_slo(self):
        slo = SLOTracking(name="api-slo", sli_name="api-avail", target_percentage=99.9)
        assert slo.name == "api-slo"
        assert slo.sli_name == "api-avail"
        assert slo.target_percentage == 99.9
        assert slo.burn_rate == SLOBurnRate.SEVEN_DAY

    def test_create_with_all_fields(self):
        slo = SLOTracking(
            name="strict",
            sli_name="latency",
            target_percentage=99.0,
            budget_period_seconds=86400,
            burn_rate=SLOBurnRate.ONE_HOUR,
            fast_burn_threshold=10.0,
            slow_burn_threshold=0.5,
            pages_enabled=False,
        )
        assert slo.burn_rate == SLOBurnRate.ONE_HOUR
        assert slo.pages_enabled is False

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="", sli_name="x", target_percentage=99.9)
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_SLO_NAME

    def test_whitespace_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="   ", sli_name="x", target_percentage=99.9)
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_SLO_NAME

    def test_zero_target_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="test", sli_name="x", target_percentage=0)
        assert exc_info.value.code == ErrorCode.CP16_INVALID_SLO_TARGET

    def test_negative_target_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="test", sli_name="x", target_percentage=-1)
        assert exc_info.value.code == ErrorCode.CP16_INVALID_SLO_TARGET

    def test_over_100_target_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="test", sli_name="x", target_percentage=101)
        assert exc_info.value.code == ErrorCode.CP16_INVALID_SLO_TARGET

    def test_budget_less_than_3600_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SLOTracking(name="test", sli_name="x", target_percentage=99.9, budget_period_seconds=1800)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_to_dict(self):
        slo = SLOTracking(name="s", sli_name="api", target_percentage=99.9, burn_rate=SLOBurnRate.ONE_HOUR)
        d = slo.to_dict()
        assert d["name"] == "s"
        assert d["sli_name"] == "api"
        assert d["burn_rate"] == "1h"

    def test_from_dict(self):
        d = {
            "name": "rt", "sli_name": "avail", "target_percentage": 99.99,
            "budget_period_seconds": 2592000, "burn_rate": "1h",
            "fast_burn_threshold": 14.4, "slow_burn_threshold": 1.0, "pages_enabled": True,
        }
        slo = SLOTracking.from_dict(d)
        assert slo.name == "rt"
        assert slo.burn_rate == SLOBurnRate.ONE_HOUR

    def test_roundtrip(self):
        original = SLOTracking(name="rt", sli_name="s", target_percentage=99.0, burn_rate=SLOBurnRate.TWO_DAY)
        restored = SLOTracking.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.burn_rate == original.burn_rate
        assert restored.target_percentage == original.target_percentage
