# coding: utf-8
"""
Test cases cho CP16 API & System Monitoring Generator models.

Kiểm tra:
- AlertSeverity: Giá trị enum và membership
- AlertCondition: Giá trị enum và membership
- SLIMetricType: Giá trị enum và membership
- DashboardType: Giá trị enum và membership
- DashboardProfile: Tạo hợp lệ, tên rỗng → lỗi, refresh < 5 → lỗi, to_dict/from_dict, defaults
- AlertRule: Tạo hợp lệ, tên rỗng → lỗi, evaluation_interval < 5 → lỗi, to_dict/from_dict, defaults
- SLIDefinition: Tạo hợp lệ, target <= 0 → lỗi, window < 60 → lỗi, to_dict/from_dict, defaults
"""

import pytest

from midicoder.emitters.core.monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    SLIDefinition,
    SLIMetricType,
)
from midicoder.errors import ErrorCode, MidicoderError


# =============================================================================
# Enum Tests
# =============================================================================


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_critical_value(self):
        """Kiểm tra giá trị CRITICAL."""
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_warning_value(self):
        """Kiểm tra giá trị WARNING."""
        assert AlertSeverity.WARNING.value == "warning"

    def test_info_value(self):
        """Kiểm tra giá trị INFO."""
        assert AlertSeverity.INFO.value == "info"

    def test_total_count(self):
        """Kiểm tra tổng số severity levels = 3."""
        assert len(AlertSeverity) == 3

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert AlertSeverity.CRITICAL == "critical"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.INFO == "info"


class TestAlertCondition:
    """Test AlertCondition enum."""

    def test_greater_than_value(self):
        """Kiểm tra giá trị GREATER_THAN."""
        assert AlertCondition.GREATER_THAN.value == "greater_than"

    def test_less_than_value(self):
        """Kiểm tra giá trị LESS_THAN."""
        assert AlertCondition.LESS_THAN.value == "less_than"

    def test_equals_value(self):
        """Kiểm tra giá trị EQUALS."""
        assert AlertCondition.EQUALS.value == "equals"

    def test_not_equals_value(self):
        """Kiểm tra giá trị NOT_EQUALS."""
        assert AlertCondition.NOT_EQUALS.value == "not_equals"

    def test_total_count(self):
        """Kiểm tra tổng số conditions = 4."""
        assert len(AlertCondition) == 4

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert AlertCondition.GREATER_THAN == "greater_than"
        assert AlertCondition.LESS_THAN == "less_than"


class TestSLIMetricType:
    """Test SLIMetricType enum."""

    def test_availability_value(self):
        """Kiểm tra giá trị AVAILABILITY."""
        assert SLIMetricType.AVAILABILITY.value == "availability"

    def test_latency_value(self):
        """Kiểm tra giá trị LATENCY."""
        assert SLIMetricType.LATENCY.value == "latency"

    def test_error_rate_value(self):
        """Kiểm tra giá trị ERROR_RATE."""
        assert SLIMetricType.ERROR_RATE.value == "error_rate"

    def test_total_count(self):
        """Kiểm tra tổng số metric types = 3."""
        assert len(SLIMetricType) == 3

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert SLIMetricType.AVAILABILITY == "availability"
        assert SLIMetricType.LATENCY == "latency"
        assert SLIMetricType.ERROR_RATE == "error_rate"


class TestDashboardType:
    """Test DashboardType enum."""

    def test_system_value(self):
        """Kiểm tra giá trị SYSTEM."""
        assert DashboardType.SYSTEM.value == "system"

    def test_api_value(self):
        """Kiểm tra giá trị API."""
        assert DashboardType.API.value == "api"

    def test_business_value(self):
        """Kiểm tra giá trị BUSINESS."""
        assert DashboardType.BUSINESS.value == "business"

    def test_total_count(self):
        """Kiểm tra tổng số dashboard types = 3."""
        assert len(DashboardType) == 3

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert DashboardType.SYSTEM == "system"
        assert DashboardType.API == "api"
        assert DashboardType.BUSINESS == "business"


# =============================================================================
# DashboardProfile Tests
# =============================================================================


class TestDashboardProfile:
    """Test DashboardProfile dataclass."""

    def test_create_valid_system_dashboard(self):
        """Kiểm tra tạo system dashboard hợp lệ."""
        dp = DashboardProfile(name="System Overview")
        assert dp.name == "System Overview"
        assert dp.dashboard_type == DashboardType.SYSTEM
        assert dp.panels == []
        assert dp.refresh_interval_seconds == 30
        assert dp.description == ""

    def test_create_valid_api_dashboard(self):
        """Kiểm tra tạo API dashboard hợp lệ với đầy đủ thuộc tính."""
        dp = DashboardProfile(
            name="API Performance",
            dashboard_type=DashboardType.API,
            panels=["latency_panel", "throughput_panel"],
            refresh_interval_seconds=10,
            description="Theo dõi hiệu suất API",
        )
        assert dp.name == "API Performance"
        assert dp.dashboard_type == DashboardType.API
        assert dp.panels == ["latency_panel", "throughput_panel"]
        assert dp.refresh_interval_seconds == 10
        assert dp.description == "Theo dõi hiệu suất API"

    def test_create_valid_business_dashboard(self):
        """Kiểm tra tạo business dashboard hợp lệ."""
        dp = DashboardProfile(
            name="Business Metrics",
            dashboard_type=DashboardType.BUSINESS,
            refresh_interval_seconds=60,
        )
        assert dp.dashboard_type == DashboardType.BUSINESS
        assert dp.refresh_interval_seconds == 60

    def test_empty_name_raises_error(self):
        """Kiểm tra tên dashboard rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardProfile(name="")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_DASHBOARD_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên dashboard chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardProfile(name="   ")
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_DASHBOARD_NAME

    def test_refresh_interval_less_than_5_raises_error(self):
        """Kiểm tra refresh_interval_seconds < 5 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardProfile(name="Test", refresh_interval_seconds=3)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_refresh_interval_zero_raises_error(self):
        """Kiểm tra refresh_interval_seconds = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardProfile(name="Test", refresh_interval_seconds=0)
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_refresh_interval_boundary_5(self):
        """Kiểm tra refresh_interval_seconds = 5 hợp lệ (giá trị tối thiểu)."""
        dp = DashboardProfile(name="Test", refresh_interval_seconds=5)
        assert dp.refresh_interval_seconds == 5

    def test_default_values(self):
        """Kiểm tra default values của DashboardProfile."""
        dp = DashboardProfile(name="Default Dashboard")
        assert dp.dashboard_type == DashboardType.SYSTEM
        assert dp.panels == []
        assert dp.refresh_interval_seconds == 30
        assert dp.description == ""

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        dp = DashboardProfile(
            name="Monitoring",
            dashboard_type=DashboardType.API,
            panels=["panel_a", "panel_b"],
            refresh_interval_seconds=15,
            description="Dashboard giám sát",
        )
        data = dp.to_dict()
        assert data["name"] == "Monitoring"
        assert data["dashboard_type"] == "api"
        assert data["panels"] == ["panel_a", "panel_b"]
        assert data["refresh_interval_seconds"] == 15
        assert data["description"] == "Dashboard giám sát"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "System Health",
            "dashboard_type": "business",
            "panels": ["cpu_panel", "memory_panel"],
            "refresh_interval_seconds": 20,
            "description": "Sức khỏe hệ thống",
        }
        dp = DashboardProfile.from_dict(data)
        assert dp.name == "System Health"
        assert dp.dashboard_type == DashboardType.BUSINESS
        assert dp.panels == ["cpu_panel", "memory_panel"]
        assert dp.refresh_interval_seconds == 20

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = DashboardProfile(
            name="Roundtrip Test",
            dashboard_type=DashboardType.SYSTEM,
            panels=["p1"],
            refresh_interval_seconds=45,
            description="Test roundtrip",
        )
        restored = DashboardProfile.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.dashboard_type == original.dashboard_type
        assert restored.panels == original.panels
        assert restored.refresh_interval_seconds == original.refresh_interval_seconds
        assert restored.description == original.description


# =============================================================================
# AlertRule Tests
# =============================================================================


class TestAlertRule:
    """Test AlertRule dataclass."""

    def test_create_valid_critical_alert(self):
        """Kiểm tra tạo critical alert hợp lệ."""
        ar = AlertRule(
            name="High CPU Usage",
            metric_name="cpu_usage_percent",
            condition=AlertCondition.GREATER_THAN,
            threshold=90.0,
            severity=AlertSeverity.CRITICAL,
        )
        assert ar.name == "High CPU Usage"
        assert ar.metric_name == "cpu_usage_percent"
        assert ar.condition == AlertCondition.GREATER_THAN
        assert ar.threshold == 90.0
        assert ar.severity == AlertSeverity.CRITICAL

    def test_create_valid_warning_alert(self):
        """Kiểm tra tạo warning alert với đầy đủ thuộc tính."""
        ar = AlertRule(
            name="Low Memory",
            metric_name="memory_available_bytes",
            condition=AlertCondition.LESS_THAN,
            threshold=1024.0,
            severity=AlertSeverity.WARNING,
            evaluation_interval=15,
            labels={"host": "web-1"},
            description="Cảnh báo bộ nhớ thấp",
        )
        assert ar.name == "Low Memory"
        assert ar.evaluation_interval == 15
        assert ar.labels == {"host": "web-1"}
        assert ar.description == "Cảnh báo bộ nhớ thấp"

    def test_create_valid_info_alert(self):
        """Kiểm tra tạo info alert với điều kiện equals."""
        ar = AlertRule(
            name="Service Down",
            metric_name="service_health",
            condition=AlertCondition.EQUALS,
            threshold=0.0,
            severity=AlertSeverity.INFO,
        )
        assert ar.condition == AlertCondition.EQUALS
        assert ar.severity == AlertSeverity.INFO

    def test_empty_name_raises_error(self):
        """Kiểm tra tên alert rule rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AlertRule(
                name="",
                metric_name="test_metric",
                condition=AlertCondition.GREATER_THAN,
                threshold=1.0,
            )
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_ALERT_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên alert rule chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AlertRule(
                name="   ",
                metric_name="test_metric",
                condition=AlertCondition.GREATER_THAN,
                threshold=1.0,
            )
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_ALERT_NAME

    def test_evaluation_interval_less_than_5_raises_error(self):
        """Kiểm tra evaluation_interval < 5 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AlertRule(
                name="Test Alert",
                metric_name="test_metric",
                condition=AlertCondition.GREATER_THAN,
                threshold=1.0,
                evaluation_interval=3,
            )
        assert exc_info.value.code == ErrorCode.CP16_ALERT_EVALUATION_INTERVAL_INVALID

    def test_evaluation_interval_zero_raises_error(self):
        """Kiểm tra evaluation_interval = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AlertRule(
                name="Test Alert",
                metric_name="test_metric",
                condition=AlertCondition.GREATER_THAN,
                threshold=1.0,
                evaluation_interval=0,
            )
        assert exc_info.value.code == ErrorCode.CP16_ALERT_EVALUATION_INTERVAL_INVALID

    def test_evaluation_interval_boundary_5(self):
        """Kiểm tra evaluation_interval = 5 hợp lệ (giá trị tối thiểu)."""
        ar = AlertRule(
            name="Test Alert",
            metric_name="test_metric",
            condition=AlertCondition.GREATER_THAN,
            threshold=1.0,
            evaluation_interval=5,
        )
        assert ar.evaluation_interval == 5

    def test_default_values(self):
        """Kiểm tra default values của AlertRule."""
        ar = AlertRule(
            name="Default Alert",
            metric_name="some_metric",
            condition=AlertCondition.GREATER_THAN,
            threshold=0.0,
        )
        assert ar.severity == AlertSeverity.WARNING
        assert ar.evaluation_interval == 30
        assert ar.labels == {}
        assert ar.description == ""

    def test_all_conditions_valid(self):
        """Kiểm tra tất cả alert conditions đều hợp lệ."""
        for condition in AlertCondition:
            ar = AlertRule(
                name=f"Alert for {condition.value}",
                metric_name="test_metric",
                condition=condition,
                threshold=1.0,
            )
            assert ar.condition == condition

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        ar = AlertRule(
            name="High Latency",
            metric_name="request_latency_ms",
            condition=AlertCondition.GREATER_THAN,
            threshold=500.0,
            severity=AlertSeverity.CRITICAL,
            evaluation_interval=10,
            labels={"service": "api-gateway"},
            description="Độ trễ cao",
        )
        data = ar.to_dict()
        assert data["name"] == "High Latency"
        assert data["metric_name"] == "request_latency_ms"
        assert data["condition"] == "greater_than"
        assert data["threshold"] == 500.0
        assert data["severity"] == "critical"
        assert data["evaluation_interval"] == 10
        assert data["labels"] == {"service": "api-gateway"}
        assert data["description"] == "Độ trễ cao"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "Disk Full",
            "metric_name": "disk_usage_percent",
            "condition": "greater_than",
            "threshold": 95.0,
            "severity": "critical",
            "evaluation_interval": 20,
            "labels": {"mount": "/data"},
            "description": "Đĩa đầy",
        }
        ar = AlertRule.from_dict(data)
        assert ar.name == "Disk Full"
        assert ar.metric_name == "disk_usage_percent"
        assert ar.condition == AlertCondition.GREATER_THAN
        assert ar.threshold == 95.0
        assert ar.severity == AlertSeverity.CRITICAL
        assert ar.evaluation_interval == 20
        assert ar.labels == {"mount": "/data"}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = AlertRule(
            name="Roundtrip Alert",
            metric_name="roundtrip_metric",
            condition=AlertCondition.NOT_EQUALS,
            threshold=42.0,
            severity=AlertSeverity.INFO,
            evaluation_interval=25,
            labels={"env": "test"},
            description="Test roundtrip",
        )
        restored = AlertRule.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.metric_name == original.metric_name
        assert restored.condition == original.condition
        assert restored.threshold == original.threshold
        assert restored.severity == original.severity
        assert restored.evaluation_interval == original.evaluation_interval
        assert restored.labels == original.labels
        assert restored.description == original.description


# =============================================================================
# SLIDefinition Tests
# =============================================================================


class TestSLIDefinition:
    """Test SLIDefinition dataclass."""

    def test_create_valid_availability_sli(self):
        """Kiểm tra tạo SLI availability hợp lệ."""
        sli = SLIDefinition(
            name="API Availability",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="http_requests_total",
            target=0.999,
            window_seconds=86400,
            description="Tỷ lệ uptime API",
        )
        assert sli.name == "API Availability"
        assert sli.metric_type == SLIMetricType.AVAILABILITY
        assert sli.metric_name == "http_requests_total"
        assert sli.target == 0.999
        assert sli.window_seconds == 86400

    def test_create_valid_latency_sli(self):
        """Kiểm tra tạo SLI latency hợp lệ."""
        sli = SLIDefinition(
            name="Request Latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="request_latency_ms",
            target=200.0,
            labels={"percentile": "p95"},
        )
        assert sli.metric_type == SLIMetricType.LATENCY
        assert sli.target == 200.0
        assert sli.labels == {"percentile": "p95"}

    def test_create_valid_error_rate_sli(self):
        """Kiểm tra tạo SLI error_rate hợp lệ."""
        sli = SLIDefinition(
            name="Error Rate SLI",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="http_errors_total",
            target=0.01,
        )
        assert sli.metric_type == SLIMetricType.ERROR_RATE
        assert sli.target == 0.01

    def test_empty_name_raises_error(self):
        """Kiểm tra tên SLI rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="",
                metric_type=SLIMetricType.AVAILABILITY,
                metric_name="test",
                target=0.99,
            )
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_DASHBOARD_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên SLI chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="   ",
                metric_type=SLIMetricType.AVAILABILITY,
                metric_name="test",
                target=0.99,
            )
        assert exc_info.value.code == ErrorCode.CP16_EMPTY_DASHBOARD_NAME

    def test_zero_target_raises_error(self):
        """Kiểm tra target = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="Bad Target",
                metric_type=SLIMetricType.AVAILABILITY,
                metric_name="test",
                target=0.0,
            )
        assert exc_info.value.code == ErrorCode.CP16_INVALID_SLI_TARGET

    def test_negative_target_raises_error(self):
        """Kiểm tra target âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="Bad Target",
                metric_type=SLIMetricType.AVAILABILITY,
                metric_name="test",
                target=-0.5,
            )
        assert exc_info.value.code == ErrorCode.CP16_INVALID_SLI_TARGET

    def test_window_seconds_less_than_60_raises_error(self):
        """Kiểm tra window_seconds < 60 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="Bad Window",
                metric_type=SLIMetricType.LATENCY,
                metric_name="test",
                target=100.0,
                window_seconds=30,
            )
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_window_seconds_zero_raises_error(self):
        """Kiểm tra window_seconds = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            SLIDefinition(
                name="Bad Window",
                metric_type=SLIMetricType.LATENCY,
                metric_name="test",
                target=100.0,
                window_seconds=0,
            )
        assert exc_info.value.code == ErrorCode.CP16_MONITORING_PARSE_ERROR

    def test_window_seconds_boundary_60(self):
        """Kiểm tra window_seconds = 60 hợp lệ (giá trị tối thiểu)."""
        sli = SLIDefinition(
            name="Boundary Window",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="test",
            target=0.99,
            window_seconds=60,
        )
        assert sli.window_seconds == 60

    def test_default_values(self):
        """Kiểm tra default values của SLIDefinition."""
        sli = SLIDefinition(
            name="Default SLI",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="test_metric",
            target=0.99,
        )
        assert sli.window_seconds == 3600
        assert sli.labels == {}
        assert sli.description == ""

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        sli = SLIDefinition(
            name="SLA Compliance",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="uptime_total",
            target=0.9999,
            window_seconds=2592000,
            labels={"tier": "gold"},
            description="Tuân thủ SLA",
        )
        data = sli.to_dict()
        assert data["name"] == "SLA Compliance"
        assert data["metric_type"] == "availability"
        assert data["metric_name"] == "uptime_total"
        assert data["target"] == 0.9999
        assert data["window_seconds"] == 2592000
        assert data["labels"] == {"tier": "gold"}
        assert data["description"] == "Tuân thủ SLA"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "Error Budget",
            "metric_type": "error_rate",
            "metric_name": "error_count",
            "target": 0.001,
            "window_seconds": 7200,
            "labels": {"service": "checkout"},
            "description": "Ngân sách lỗi",
        }
        sli = SLIDefinition.from_dict(data)
        assert sli.name == "Error Budget"
        assert sli.metric_type == SLIMetricType.ERROR_RATE
        assert sli.metric_name == "error_count"
        assert sli.target == 0.001
        assert sli.window_seconds == 7200
        assert sli.labels == {"service": "checkout"}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = SLIDefinition(
            name="Roundtrip SLI",
            metric_type=SLIMetricType.LATENCY,
            metric_name="p99_latency",
            target=500.0,
            window_seconds=1800,
            labels={"env": "staging"},
            description="Test roundtrip SLI",
        )
        restored = SLIDefinition.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.metric_type == original.metric_type
        assert restored.metric_name == original.metric_name
        assert restored.target == original.target
        assert restored.window_seconds == original.window_seconds
        assert restored.labels == original.labels
        assert restored.description == original.description
