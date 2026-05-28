# coding: utf-8
"""
Test cases cho CP16 API & System Monitoring Parser.

Kiểm tra:
- MonitoringParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid types, invalid enums
- Edge cases: Empty input, missing sections, default values

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_monitoring.parser import MonitoringParser
from midicoder.packs.cp_full_monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    Panel,
    SLIDefinition,
    SLIMetricType,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestMonitoringParser:
    """Test suite cho MonitoringParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = MonitoringParser()

    # =========================================================================
    # Empty / whitespace input
    # =========================================================================

    def test_parse_empty_string_returns_empty_dicts(self):
        """Kiểm tra parse string rỗng trả về dict rỗng cho tất cả sections."""
        result = self.parser.parse("")
        assert result == {
            "dashboards": [], "alerts": [], "slis": [],
            "health_checks": [], "notification_channels": [],
            "escalation_policies": [], "slo_tracking": [],
        }

    def test_parse_whitespace_only_returns_empty_dicts(self):
        """Kiểm tra parse whitespace trả về dict rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert result == {
            "dashboards": [], "alerts": [], "slis": [],
            "health_checks": [], "notification_channels": [],
            "escalation_policies": [], "slo_tracking": [],
        }

    def test_parse_comment_only_returns_empty_dicts(self):
        """Kiểm tra parse chỉ có comment YAML trả về dict rỗng."""
        dsl = """
# Chỉ có comment
# Không có dữ liệu
"""
        result = self.parser.parse(dsl)
        assert result == {
            "dashboards": [], "alerts": [], "slis": [],
            "health_checks": [], "notification_channels": [],
            "escalation_policies": [], "slo_tracking": [],
        }

    # =========================================================================
    # Valid dashboards section
    # =========================================================================

    def test_parse_single_dashboard_with_panels(self):
        """Kiểm tra parse dashboard hợp lệ với panels."""
        dsl = """
dashboards:
  - name: api-overview
    type: api
    refresh_interval_seconds: 15
    panels:
      - name: request_rate
        metric_name: http_requests_total
        panel_type: counter
      - name: error_rate
        metric_name: http_errors_total
        panel_type: gauge
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 1
        assert len(result["alerts"]) == 0
        assert len(result["slis"]) == 0

        dashboard = result["dashboards"][0]
        assert isinstance(dashboard, DashboardProfile)
        assert dashboard.name == "api-overview"
        assert dashboard.dashboard_type == DashboardType.API
        assert dashboard.refresh_interval_seconds == 15
        assert len(dashboard.panels) == 2

        # Kiểm tra panel đầu tiên
        panel = dashboard.panels[0]
        assert isinstance(panel, Panel)
        assert panel.name == "request_rate"
        assert panel.metric_name == "http_requests_total"
        assert panel.panel_type == "counter"

        # Kiểm tra panel thứ hai
        panel2 = dashboard.panels[1]
        assert panel2.name == "error_rate"
        assert panel2.metric_name == "http_errors_total"
        assert panel2.panel_type == "gauge"

    def test_parse_dashboard_with_defaults(self):
        """Kiểm tra parse dashboard chỉ có name, các field còn lại dùng default."""
        dsl = """
dashboards:
  - name: minimal-dashboard
"""
        result = self.parser.parse(dsl)
        dashboard = result["dashboards"][0]
        assert dashboard.name == "minimal-dashboard"
        assert dashboard.dashboard_type == DashboardType.SYSTEM
        assert dashboard.refresh_interval_seconds == 30
        assert dashboard.panels == []
        assert dashboard.description == ""

    def test_parse_dashboard_type_system(self):
        """Kiểm tra parse dashboard type system."""
        dsl = """
dashboards:
  - name: system-monitor
    type: system
"""
        result = self.parser.parse(dsl)
        dashboard = result["dashboards"][0]
        assert dashboard.dashboard_type == DashboardType.SYSTEM

    def test_parse_dashboard_type_business(self):
        """Kiểm tra parse dashboard type business."""
        dsl = """
dashboards:
  - name: business-overview
    type: business
"""
        result = self.parser.parse(dsl)
        dashboard = result["dashboards"][0]
        assert dashboard.dashboard_type == DashboardType.BUSINESS

    def test_parse_dashboard_all_panel_types(self):
        """Kiểm tra parse dashboard với các loại panel khác nhau."""
        dsl = """
dashboards:
  - name: multi-panel
    type: api
    panels:
      - name: counter_panel
        metric_name: req_count
        panel_type: counter
      - name: gauge_panel
        metric_name: cpu_usage
        panel_type: gauge
      - name: histogram_panel
        metric_name: latency
        panel_type: histogram
      - name: table_panel
        metric_name: log_entries
        panel_type: table
"""
        result = self.parser.parse(dsl)
        panels = result["dashboards"][0].panels
        assert len(panels) == 4
        assert panels[0].panel_type == "counter"
        assert panels[1].panel_type == "gauge"
        assert panels[2].panel_type == "histogram"
        assert panels[3].panel_type == "table"

    # =========================================================================
    # Valid alerts section
    # =========================================================================

    def test_parse_single_alert_rule(self):
        """Kiểm tra parse alert rule hợp lệ."""
        dsl = """
alerts:
  - name: high_error_rate
    metric_name: http_errors_total
    condition: greater_than
    threshold: 100
    severity: critical
    evaluation_interval: 30
"""
        result = self.parser.parse(dsl)
        assert len(result["alerts"]) == 1
        assert len(result["dashboards"]) == 0
        assert len(result["slis"]) == 0

        alert = result["alerts"][0]
        assert isinstance(alert, AlertRule)
        assert alert.name == "high_error_rate"
        assert alert.metric_name == "http_errors_total"
        assert alert.condition == AlertCondition.GREATER_THAN
        assert alert.threshold == 100
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.evaluation_interval == 30

    def test_parse_all_alert_conditions(self):
        """Kiểm tra parse tất cả alert conditions."""
        dsl = """
alerts:
  - name: alert_gt
    metric_name: metric1
    condition: greater_than
    threshold: 10
    severity: warning
  - name: alert_lt
    metric_name: metric2
    condition: less_than
    threshold: 5
    severity: warning
  - name: alert_eq
    metric_name: metric3
    condition: equals
    threshold: 0
    severity: warning
  - name: alert_ne
    metric_name: metric4
    condition: not_equals
    threshold: 1
    severity: warning
"""
        result = self.parser.parse(dsl)
        assert len(result["alerts"]) == 4
        assert result["alerts"][0].condition == AlertCondition.GREATER_THAN
        assert result["alerts"][1].condition == AlertCondition.LESS_THAN
        assert result["alerts"][2].condition == AlertCondition.EQUALS
        assert result["alerts"][3].condition == AlertCondition.NOT_EQUALS

    def test_parse_all_alert_severities(self):
        """Kiểm tra parse tất cả alert severities."""
        dsl = """
alerts:
  - name: critical_alert
    metric_name: m1
    condition: greater_than
    threshold: 100
    severity: critical
  - name: warning_alert
    metric_name: m2
    condition: greater_than
    threshold: 50
    severity: warning
  - name: info_alert
    metric_name: m3
    condition: greater_than
    threshold: 10
    severity: info
"""
        result = self.parser.parse(dsl)
        assert result["alerts"][0].severity == AlertSeverity.CRITICAL
        assert result["alerts"][1].severity == AlertSeverity.WARNING
        assert result["alerts"][2].severity == AlertSeverity.INFO

    def test_parse_alert_with_defaults(self):
        """Kiểm tra parse alert với default values."""
        dsl = """
alerts:
  - name: minimal-alert
    metric_name: test_metric
    condition: greater_than
    threshold: 1
"""
        result = self.parser.parse(dsl)
        alert = result["alerts"][0]
        assert alert.name == "minimal-alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.evaluation_interval == 30

    # =========================================================================
    # Valid SLIs section
    # =========================================================================

    def test_parse_single_sli_availability(self):
        """Kiểm tra parse SLI availability hợp lệ."""
        dsl = """
slis:
  - name: api-availability
    metric_type: availability
    metric_name: service_availability
    target: 0.999
    window_seconds: 86400
"""
        result = self.parser.parse(dsl)
        assert len(result["slis"]) == 1

        sli = result["slis"][0]
        assert isinstance(sli, SLIDefinition)
        assert sli.name == "api-availability"
        assert sli.metric_type == SLIMetricType.AVAILABILITY
        assert sli.metric_name == "service_availability"
        assert sli.target == 0.999
        assert sli.window_seconds == 86400

    def test_parse_sli_latency(self):
        """Kiểm tra parse SLI latency."""
        dsl = """
slis:
  - name: api-latency-p99
    metric_type: latency
    metric_name: http_request_duration_seconds
    target: 500
    window_seconds: 3600
"""
        result = self.parser.parse(dsl)
        sli = result["slis"][0]
        assert sli.metric_type == SLIMetricType.LATENCY
        assert sli.target == 500

    def test_parse_sli_error_rate(self):
        """Kiểm tra parse SLI error_rate."""
        dsl = """
slis:
  - name: api-error-rate
    metric_type: error_rate
    metric_name: http_error_rate
    target: 0.01
    window_seconds: 1800
"""
        result = self.parser.parse(dsl)
        sli = result["slis"][0]
        assert sli.metric_type == SLIMetricType.ERROR_RATE
        assert sli.target == 0.01

    # =========================================================================
    # Full DSL with all 3 sections
    # =========================================================================

    def test_parse_full_dsl_all_sections(self):
        """Kiểm tra parse DSL đầy đủ với cả 3 sections."""
        dsl = """
dashboards:
  - name: api-overview
    type: api
    refresh_interval_seconds: 15
    panels:
      - name: request_rate
        metric_name: http_requests_total
        panel_type: counter
      - name: error_rate
        metric_name: http_errors_total
        panel_type: gauge
alerts:
  - name: high_error_rate
    metric_name: http_errors_total
    condition: greater_than
    threshold: 100
    severity: critical
    evaluation_interval: 30
  - name: low_availability
    metric_name: service_availability
    condition: less_than
    threshold: 0.99
    severity: warning
    evaluation_interval: 60
slis:
  - name: api-availability
    metric_type: availability
    metric_name: service_availability
    target: 0.999
    window_seconds: 86400
  - name: api-latency-p99
    metric_type: latency
    metric_name: http_request_duration_seconds
    target: 500
    window_seconds: 3600
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 1
        assert len(result["alerts"]) == 2
        assert len(result["slis"]) == 2

        # Verify dashboard
        assert result["dashboards"][0].dashboard_type == DashboardType.API
        assert result["dashboards"][0].refresh_interval_seconds == 15

        # Verify alerts
        assert result["alerts"][0].severity == AlertSeverity.CRITICAL
        assert result["alerts"][1].condition == AlertCondition.LESS_THAN

        # Verify SLIs
        assert result["slis"][0].metric_type == SLIMetricType.AVAILABILITY
        assert result["slis"][1].target == 500

    # =========================================================================
    # Invalid YAML
    # =========================================================================

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw error."""
        invalid_yaml = """
dashboards:
  - name: test
    type: [invalid yaml
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra parse YAML list (không phải mapping) throw error."""
        list_yaml = """
- item1
- item2
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(list_yaml)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    # =========================================================================
    # Invalid enum values
    # =========================================================================

    def test_parse_invalid_dashboard_type_raises_error(self):
        """Kiểm tra dashboard type không hợp lệ throw error."""
        dsl = """
dashboards:
  - name: bad-dashboard
    type: invalid_type
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_invalid_alert_condition_raises_error(self):
        """Kiểm tra alert condition không hợp lệ throw error."""
        dsl = """
alerts:
  - name: bad-alert
    metric_name: test_metric
    condition: invalid_condition
    threshold: 100
    severity: warning
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_INVALID_ALERT_CONDITION

    def test_parse_invalid_alert_severity_raises_error(self):
        """Kiểm tra alert severity không hợp lệ throw error."""
        dsl = """
alerts:
  - name: bad-alert
    metric_name: test_metric
    condition: greater_than
    threshold: 100
    severity: fatal
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_INVALID_ALERT_SEVERITY

    def test_parse_invalid_sli_metric_type_raises_error(self):
        """Kiểm tra SLI metric type không hợp lệ throw error."""
        dsl = """
slis:
  - name: bad-sli
    metric_type: throughput
    metric_name: test_metric
    target: 0.99
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_INVALID_SLI_METRIC_TYPE

    # =========================================================================
    # Missing sections
    # =========================================================================

    def test_parse_only_dashboards_section(self):
        """Kiểm tra parse chỉ có dashboards, các section khác rỗng."""
        dsl = """
dashboards:
  - name: only-dashboard
    type: api
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 1
        assert result["alerts"] == []
        assert result["slis"] == []

    def test_parse_only_alerts_section(self):
        """Kiểm tra parse chỉ có alerts, các section khác rỗng."""
        dsl = """
alerts:
  - name: only-alert
    metric_name: test_metric
    condition: greater_than
    threshold: 50
    severity: critical
"""
        result = self.parser.parse(dsl)
        assert result["dashboards"] == []
        assert len(result["alerts"]) == 1
        assert result["slis"] == []

    def test_parse_only_slis_section(self):
        """Kiểm tra parse chỉ có slis, các section khác rỗng."""
        dsl = """
slis:
  - name: only-sli
    metric_type: availability
    metric_name: uptime
    target: 0.999
"""
        result = self.parser.parse(dsl)
        assert result["dashboards"] == []
        assert result["alerts"] == []
        assert len(result["slis"]) == 1

    def test_parse_empty_sections(self):
        """Kiểm tra parse với các section rỗng."""
        dsl = """
dashboards: []
alerts: []
slis: []
"""
        result = self.parser.parse(dsl)
        assert result["dashboards"] == []
        assert result["alerts"] == []
        assert result["slis"] == []

    # =========================================================================
    # Multiple entries in each section
    # =========================================================================

    def test_parse_multiple_dashboards(self):
        """Kiểm tra parse nhiều dashboards cùng lúc."""
        dsl = """
dashboards:
  - name: dashboard-1
    type: api
    refresh_interval_seconds: 15
  - name: dashboard-2
    type: system
    refresh_interval_seconds: 60
  - name: dashboard-3
    type: business
    refresh_interval_seconds: 120
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 3
        assert result["dashboards"][0].dashboard_type == DashboardType.API
        assert result["dashboards"][1].dashboard_type == DashboardType.SYSTEM
        assert result["dashboards"][2].dashboard_type == DashboardType.BUSINESS

    # =========================================================================
    # New sections: health_checks, notification_channels, escalation_policies, slo_tracking
    # =========================================================================

    def test_parse_health_checks_section(self):
        """Kiểm tra parse health_checks section."""
        dsl = """
health_checks:
  - name: api-health
    check_type: liveness
    path: /health
    interval_seconds: 10
    timeout_seconds: 5
    unhealthy_threshold: 3
"""
        result = self.parser.parse(dsl)
        assert len(result["health_checks"]) == 1
        hc = result["health_checks"][0]
        assert hc.name == "api-health"
        assert hc.check_type.value == "liveness"
        assert hc.path == "/health"
        assert hc.interval_seconds == 10
        assert hc.timeout_seconds == 5
        assert hc.unhealthy_threshold == 3

    def test_parse_health_check_all_types(self):
        """Kiểm tra parse tất cả các loại health check."""
        dsl = """
health_checks:
  - name: liveness-hc
    check_type: liveness
    path: /health
  - name: readiness-hc
    check_type: readiness
    path: /ready
  - name: custom-hc
    check_type: custom
    path: /custom-health
"""
        result = self.parser.parse(dsl)
        assert len(result["health_checks"]) == 3
        types = [hc.check_type.value for hc in result["health_checks"]]
        assert types == ["liveness", "readiness", "custom"]

    def test_parse_health_check_invalid_type_raises(self):
        """Kiểm tra parse health check type không hợp lệ throw error."""
        dsl = """
health_checks:
  - name: bad-hc
    check_type: invalid_type
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_notification_channels_section(self):
        """Kiểm tra parse notification_channels section."""
        dsl = """
notification_channels:
  - name: ops-email
    channel_type: email
    endpoint: ops@company.com
    severity_filter:
      - critical
  - name: slack-alerts
    channel_type: slack
    endpoint: "#alerts"
    severity_filter:
      - warning
      - critical
"""
        result = self.parser.parse(dsl)
        assert len(result["notification_channels"]) == 2
        ch1 = result["notification_channels"][0]
        assert ch1.name == "ops-email"
        assert ch1.channel_type.value == "email"
        assert ch1.endpoint == "ops@company.com"
        assert ch1.severity_filter == ["critical"]
        ch2 = result["notification_channels"][1]
        assert ch2.channel_type.value == "slack"
        assert ch2.severity_filter == ["warning", "critical"]

    def test_parse_notification_channel_all_types(self):
        """Kiểm tra parse tất cả channel types."""
        dsl = """
notification_channels:
  - name: email-ch
    channel_type: email
    endpoint: test@test.com
  - name: slack-ch
    channel_type: slack
    endpoint: "#test"
  - name: webhook-ch
    channel_type: webhook
    endpoint: "https://hook.example.com"
  - name: pd-ch
    channel_type: pagerduty
    endpoint: "routing-key-123"
  - name: os-ch
    channel_type: opsgenie
    endpoint: "integration-key"
"""
        result = self.parser.parse(dsl)
        types = [ch.channel_type.value for ch in result["notification_channels"]]
        assert types == ["email", "slack", "webhook", "pagerduty", "opsgenie"]

    def test_parse_escalation_policies_section(self):
        """Kiểm tra parse escalation_policies section."""
        dsl = """
escalation_policies:
  - name: infra-escalation
    levels:
      - l1-oncall
      - l2-team
      - engineering-lead
    timeout_seconds: 300
    channels:
      - ops-email
      - pager-duty
"""
        result = self.parser.parse(dsl)
        assert len(result["escalation_policies"]) == 1
        ep = result["escalation_policies"][0]
        assert ep.name == "infra-escalation"
        assert ep.levels == ["l1-oncall", "l2-team", "engineering-lead"]
        assert ep.timeout_seconds == 300
        assert ep.channels == ["ops-email", "pager-duty"]

    def test_parse_slo_tracking_section(self):
        """Kiểm tra parse slo_tracking section."""
        dsl = """
slo_tracking:
  - name: api-availability-slo
    sli_name: api-availability
    target_percentage: 99.9
    budget_period_seconds: 2592000
    burn_rate: 1h
    fast_burn_threshold: 14.4
    slow_burn_threshold: 1.0
    pages_enabled: true
"""
        result = self.parser.parse(dsl)
        assert len(result["slo_tracking"]) == 1
        slo = result["slo_tracking"][0]
        assert slo.name == "api-availability-slo"
        assert slo.sli_name == "api-availability"
        assert slo.target_percentage == 99.9
        assert slo.budget_period_seconds == 2592000
        assert slo.burn_rate.value == "1h"
        assert slo.fast_burn_threshold == 14.4
        assert slo.pages_enabled is True

    def test_parse_slo_tracking_all_burn_rates(self):
        """Kiểm tra parse tất cả burn rate types."""
        dsl = """
slo_tracking:
  - name: one-hour-slo
    sli_name: api-availability
    target_percentage: 99.9
    burn_rate: 1h
  - name: six-hour-slo
    sli_name: api-availability
    target_percentage: 99.9
    burn_rate: 6h
  - name: twelve-hour-slo
    sli_name: api-availability
    target_percentage: 99.9
    burn_rate: 12h
  - name: two-day-slo
    sli_name: api-availability
    target_percentage: 99.9
    burn_rate: 2d
  - name: seven-day-slo
    sli_name: api-availability
    target_percentage: 99.9
    burn_rate: 7d
"""
        result = self.parser.parse(dsl)
        assert len(result["slo_tracking"]) == 5
        rates = [s.burn_rate.value for s in result["slo_tracking"]]
        assert rates == ["1h", "6h", "12h", "2d", "7d"]

    # =========================================================================
    # to_dict methods coverage
    # =========================================================================

    def test_panel_to_dict(self):
        """Kiểm tra Panel.to_dict()."""
        from midicoder.packs.cp_full_monitoring.models import Panel
        p = Panel(name="cpu-panel", metric_name="cpu_usage", panel_type="gauge", labels={"env": "prod"})
        data = p.to_dict()
        assert data["name"] == "cpu-panel"
        assert data["metric_name"] == "cpu_usage"
        assert data["panel_type"] == "gauge"
        assert data["labels"] == {"env": "prod"}

    def test_fired_alert_to_dict(self):
        """Kiểm tra FiredAlert.to_dict()."""
        from midicoder.packs.cp_full_monitoring.models import FiredAlert
        import datetime
        fa = FiredAlert(
            rule_name="high-cpu",
            metric_name="cpu_usage",
            current_value=95.0,
            threshold=90.0,
            severity="critical",
            fired_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
            condition=">",
        )
        data = fa.to_dict()
        assert data["rule_name"] == "high-cpu"
        assert data["current_value"] == 95.0
        assert data["condition"] == ">"
        assert data["severity"] == "critical"

    def test_sli_status_to_dict(self):
        """Kiểm tra SLIStatus.to_dict()."""
        from midicoder.packs.cp_full_monitoring.models import SLIStatus
        import datetime
        ss = SLIStatus(
            sli_name="api-availability",
            metric_type="availability",
            current_value=99.95,
            target=99.9,
            is_healthy=True,
            evaluated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
        )
        data = ss.to_dict()
        assert data["sli_name"] == "api-availability"
        assert data["current_value"] == 99.95
        assert data["is_healthy"] is True

    def test_parse_non_dict_dashboard_raises(self):
        """Kiểm tra parse dashboard entry không phải dict throw error."""
        dsl = """
dashboards:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_alert_raises(self):
        """Kiểm tra parse alert entry không phải dict throw error."""
        dsl = """
alerts:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_sli_raises(self):
        """Kiểm tra parse sli entry không phải dict throw error."""
        dsl = """
slis:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_health_check_raises(self):
        """Kiểm tra parse health check entry không phải dict throw error."""
        dsl = """
health_checks:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_notification_channel_raises(self):
        """Kiểm tra parse notification channel entry không phải dict throw error."""
        dsl = """
notification_channels:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_escalation_raises(self):
        """Kiểm tra parse escalation policy entry không phải dict throw error."""
        dsl = """
escalation_policies:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_parse_non_dict_slo_raises(self):
        """Kiểm tra parse slo tracking entry không phải dict throw error."""
        dsl = """
slo_tracking:
  - "not-a-dict"
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F15_MONITORING_PARSE_ERROR

    def test_panel_empty_name_raises(self):
        """Kiểm tra Panel tên rỗng throw error."""
        from midicoder.packs.cp_full_monitoring.models import Panel
        with pytest.raises(MidicoderError) as exc_info:
            Panel(name="", metric_name="test")
        assert exc_info.value.code == ErrorCode.MDC-F15_EMPTY_PANEL_NAME
