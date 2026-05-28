# coding: utf-8
"""
Test cases cho recipes của CP16.

Kiểm tra tất cả recipe factory functions trả về đúng model với giá trị mặc định.
"""

import pytest

from midicoder.packs.cp_full_monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    EscalationPolicy,
    HealthCheck,
    HealthCheckType,
    NotificationChannel,
    NotificationChannelType,
    Panel,
    SLIDefinition,
    SLIMetricType,
    SLOBurnRate,
    SLOTracking,
)
from midicoder.packs.cp_full_monitoring.recipes import (
    # Health check recipes
    liveness_check,
    readiness_check,
    custom_health_check,
    # Dashboard recipes
    system_dashboard,
    api_dashboard,
    # Alert recipes
    high_error_rate_alert,
    high_latency_alert,
    low_availability_alert,
    high_cpu_alert,
    high_memory_alert,
    # SLI recipes
    availability_sli,
    latency_sli,
    error_rate_sli,
    # Notification channel recipes
    email_channel,
    slack_channel,
    pagerduty_channel,
    webhook_channel,
    # Escalation policy recipes
    standard_escalation,
    critical_escalation,
    # SLO tracking recipes
    availability_slo,
    latency_slo,
    high_reliability_slo,
)


# ===========================================================================
# Health Check Recipe Tests
# ===========================================================================


class TestHealthCheckRecipes:
    """Test health check recipe functions."""

    def test_liveness_check_defaults(self):
        hc = liveness_check()
        assert isinstance(hc, HealthCheck)
        assert hc.check_type == HealthCheckType.LIVENESS
        assert hc.path == "/health/live"
        assert hc.interval_seconds == 10
        assert hc.tags["probe"] == "liveness"

    def test_liveness_check_custom_name(self):
        hc = liveness_check(name="my-liveness", path="/healthz")
        assert hc.name == "my-liveness"
        assert hc.path == "/healthz"

    def test_readiness_check_defaults(self):
        hc = readiness_check()
        assert isinstance(hc, HealthCheck)
        assert hc.check_type == HealthCheckType.READINESS
        assert hc.path == "/health/ready"
        assert hc.unhealthy_threshold == 2

    def test_custom_health_check(self):
        hc = custom_health_check(name="queue", path="/health/queue", tags={"comp": "mq"})
        assert isinstance(hc, HealthCheck)
        assert hc.check_type == HealthCheckType.CUSTOM
        assert hc.tags == {"comp": "mq"}


# ===========================================================================
# Dashboard Recipe Tests
# ===========================================================================


class TestDashboardRecipes:
    """Test dashboard recipe functions."""

    def test_system_dashboard(self):
        dp = system_dashboard()
        assert isinstance(dp, DashboardProfile)
        assert dp.dashboard_type == DashboardType.SYSTEM
        assert len(dp.panels) == 4
        panel_names = [p.name for p in dp.panels]
        assert "cpu_usage" in panel_names
        assert "memory_usage" in panel_names
        assert "disk_usage" in panel_names
        assert "load_average" in panel_names

    def test_system_dashboard_custom_refresh(self):
        dp = system_dashboard(refresh_interval_seconds=60)
        assert dp.refresh_interval_seconds == 60

    def test_api_dashboard(self):
        dp = api_dashboard()
        assert isinstance(dp, DashboardProfile)
        assert dp.dashboard_type == DashboardType.API
        assert len(dp.panels) == 5
        panel_names = [p.name for p in dp.panels]
        assert "request_rate" in panel_names
        assert "p99_latency" in panel_names


# ===========================================================================
# Alert Recipe Tests
# ===========================================================================


class TestAlertRecipes:
    """Test alert recipe functions."""

    def test_high_error_rate_alert(self):
        ar = high_error_rate_alert()
        assert isinstance(ar, AlertRule)
        assert ar.condition == AlertCondition.GREATER_THAN
        assert ar.severity == AlertSeverity.CRITICAL
        assert ar.name == "high_error_rate"

    def test_high_error_rate_alert_custom(self):
        ar = high_error_rate_alert(metric_name="custom_errors", threshold=50.0)
        assert ar.metric_name == "custom_errors"
        assert ar.threshold == 50.0

    def test_high_latency_alert(self):
        ar = high_latency_alert()
        assert isinstance(ar, AlertRule)
        assert ar.severity == AlertSeverity.WARNING
        assert ar.name == "high_latency_p99"

    def test_low_availability_alert(self):
        ar = low_availability_alert()
        assert isinstance(ar, AlertRule)
        assert ar.condition == AlertCondition.LESS_THAN
        assert ar.severity == AlertSeverity.CRITICAL

    def test_high_cpu_alert(self):
        ar = high_cpu_alert(threshold=80.0)
        assert isinstance(ar, AlertRule)
        assert ar.threshold == 80.0

    def test_high_memory_alert(self):
        ar = high_memory_alert()
        assert isinstance(ar, AlertRule)
        assert ar.name == "high_memory_usage"


# ===========================================================================
# SLI Recipe Tests
# ===========================================================================


class TestSLIRecipes:
    """Test SLI recipe functions."""

    def test_availability_sli(self):
        sli = availability_sli()
        assert isinstance(sli, SLIDefinition)
        assert sli.metric_type == SLIMetricType.AVAILABILITY
        assert sli.target == 0.999
        assert sli.window_seconds == 86400

    def test_availability_sli_custom(self):
        sli = availability_sli(target=0.9999)
        assert sli.target == 0.9999

    def test_latency_sli(self):
        sli = latency_sli()
        assert isinstance(sli, SLIDefinition)
        assert sli.metric_type == SLIMetricType.LATENCY
        assert sli.target == 500.0

    def test_error_rate_sli(self):
        sli = error_rate_sli()
        assert isinstance(sli, SLIDefinition)
        assert sli.metric_type == SLIMetricType.ERROR_RATE
        assert sli.target == 0.01


# ===========================================================================
# Notification Channel Recipe Tests
# ===========================================================================


class TestNotificationChannelRecipes:
    """Test notification channel recipe functions."""

    def test_email_channel(self):
        ch = email_channel()
        assert isinstance(ch, NotificationChannel)
        assert ch.channel_type == NotificationChannelType.EMAIL
        assert ch.name == "team-email"

    def test_email_channel_custom(self):
        ch = email_channel(email="ops@company.com", severity_filter=["critical"])
        assert ch.endpoint == "ops@company.com"
        assert ch.severity_filter == ["critical"]

    def test_slack_channel(self):
        ch = slack_channel()
        assert isinstance(ch, NotificationChannel)
        assert ch.channel_type == NotificationChannelType.SLACK

    def test_pagerduty_channel(self):
        ch = pagerduty_channel()
        assert isinstance(ch, NotificationChannel)
        assert ch.channel_type == NotificationChannelType.PAGERDUTY
        assert ch.severity_filter == ["critical"]

    def test_webhook_channel(self):
        ch = webhook_channel(name="my-webhook", url="https://example.com/hook")
        assert isinstance(ch, NotificationChannel)
        assert ch.channel_type == NotificationChannelType.WEBHOOK
        assert ch.endpoint == "https://example.com/hook"


# ===========================================================================
# Escalation Policy Recipe Tests
# ===========================================================================


class TestEscalationPolicyRecipes:
    """Test escalation policy recipe functions."""

    def test_standard_escalation(self):
        ep = standard_escalation()
        assert isinstance(ep, EscalationPolicy)
        assert ep.name == "standard-escalation"
        assert ep.levels == ["L1-oncall", "L2-engineering", "L3-management"]
        assert ep.timeout_seconds == 300

    def test_standard_escalation_custom(self):
        ep = standard_escalation(channels=["email", "slack"])
        assert ep.channels == ["email", "slack"]

    def test_critical_escalation(self):
        ep = critical_escalation()
        assert isinstance(ep, EscalationPolicy)
        assert ep.name == "critical-escalation"
        assert ep.timeout_seconds == 120
        assert "vp-engineering" in ep.levels


# ===========================================================================
# SLO Tracking Recipe Tests
# ===========================================================================


class TestSLOTrackingRecipes:
    """Test SLO tracking recipe functions."""

    def test_availability_slo(self):
        slo = availability_slo()
        assert isinstance(slo, SLOTracking)
        assert slo.name == "API Availability SLO"
        assert slo.target_percentage == 99.9
        assert slo.burn_rate == SLOBurnRate.SEVEN_DAY
        assert slo.pages_enabled is True

    def test_availability_slo_custom(self):
        slo = availability_slo(target_percentage=99.99)
        assert slo.target_percentage == 99.99

    def test_latency_slo(self):
        slo = latency_slo()
        assert isinstance(slo, SLOTracking)
        assert slo.target_percentage == 99.0
        assert slo.pages_enabled is False

    def test_high_reliability_slo(self):
        slo = high_reliability_slo()
        assert isinstance(slo, SLOTracking)
        assert slo.target_percentage == 99.99
        assert slo.burn_rate == SLOBurnRate.ONE_HOUR
        assert slo.pages_enabled is True
