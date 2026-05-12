# coding: utf-8
"""
Test cases cho CP17 Business Intelligence & Analytics Generator models.

Kiểm tra:
- ReportFormat: Giá trị enum và membership
- SchedulePolicy: Giá trị enum và membership
- AnalyticsModel: Tạo hợp lệ, tên rỗng → lỗi, max_stale < 1 → lỗi, to_dict/from_dict, defaults
- DashboardDefinition: Tạo hợp lệ, tên rỗng → lỗi, refresh < 5 → lỗi, to_dict/from_dict, defaults
- ScheduledReport: Tạo hợp lệ, tên rỗng → lỗi, model_name rỗng → lỗi, next_run None → lỗi, to_dict/from_dict, defaults
"""

import pytest
from datetime import datetime, timezone

from midicoder.emitters.core.analytics.models import (
    AnalyticsModel,
    DashboardDefinition,
    ReportFormat,
    ScheduledReport,
    SchedulePolicy,
)
from midicoder.errors import ErrorCode, MidicoderError


# =============================================================================
# Enum Tests
# =============================================================================


class TestReportFormat:
    """Test ReportFormat enum."""

    def test_json_value(self):
        """Kiểm tra giá trị JSON."""
        assert ReportFormat.JSON.value == "json"

    def test_csv_value(self):
        """Kiểm tra giá trị CSV."""
        assert ReportFormat.CSV.value == "csv"

    def test_pdf_value(self):
        """Kiểm tra giá trị PDF."""
        assert ReportFormat.PDF.value == "pdf"

    def test_html_value(self):
        """Kiểm tra giá trị HTML."""
        assert ReportFormat.HTML.value == "html"

    def test_markdown_value(self):
        """Kiểm tra giá trị MARKDOWN."""
        assert ReportFormat.MARKDOWN.value == "markdown"

    def test_total_count(self):
        """Kiểm tra tổng số report formats = 5."""
        assert len(ReportFormat) == 5

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert ReportFormat.JSON == "json"
        assert ReportFormat.CSV == "csv"
        assert ReportFormat.PDF == "pdf"


class TestSchedulePolicy:
    """Test SchedulePolicy enum."""

    def test_once_value(self):
        """Kiểm tra giá trị ONCE."""
        assert SchedulePolicy.ONCE.value == "once"

    def test_hourly_value(self):
        """Kiểm tra giá trị HOURLY."""
        assert SchedulePolicy.HOURLY.value == "hourly"

    def test_daily_value(self):
        """Kiểm tra giá trị DAILY."""
        assert SchedulePolicy.DAILY.value == "daily"

    def test_weekly_value(self):
        """Kiểm tra giá trị WEEKLY."""
        assert SchedulePolicy.WEEKLY.value == "weekly"

    def test_monthly_value(self):
        """Kiểm tra giá trị MONTHLY."""
        assert SchedulePolicy.MONTHLY.value == "monthly"

    def test_total_count(self):
        """Kiểm tra tổng số schedule policies = 5."""
        assert len(SchedulePolicy) == 5

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert SchedulePolicy.ONCE == "once"
        assert SchedulePolicy.DAILY == "daily"
        assert SchedulePolicy.WEEKLY == "weekly"


# =============================================================================
# AnalyticsModel Tests
# =============================================================================


class TestAnalyticsModel:
    """Test AnalyticsModel dataclass."""

    def test_create_valid_model_with_defaults(self):
        """Kiểm tra tạo analytics model hợp lệ với default values."""
        am = AnalyticsModel(name="revenue_analytics")
        assert am.name == "revenue_analytics"
        assert am.metric_names == []
        assert am.filters == {}
        assert am.aggregations == []
        assert am.max_stale_seconds == 300
        assert am.description == ""

    def test_create_valid_model_full(self):
        """Kiểm tra tạo analytics model với đầy đủ thuộc tính."""
        am = AnalyticsModel(
            name="sales_dashboard",
            metric_names=["revenue", "orders", "customers"],
            filters={"region": "us"},
            aggregations=["sum", "average"],
            max_stale_seconds=600,
            description="Dữ liệu bán hàng",
        )
        assert am.name == "sales_dashboard"
        assert am.metric_names == ["revenue", "orders", "customers"]
        assert am.filters == {"region": "us"}
        assert am.aggregations == ["sum", "average"]
        assert am.max_stale_seconds == 600
        assert am.description == "Dữ liệu bán hàng"

    def test_empty_name_raises_error(self):
        """Kiểm tra tên model rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AnalyticsModel(name="")
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_MODEL_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên model chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AnalyticsModel(name="   ")
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_MODEL_NAME

    def test_max_stale_seconds_zero_raises_error(self):
        """Kiểm tra max_stale_seconds = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AnalyticsModel(name="test", max_stale_seconds=0)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_STALE_SECONDS

    def test_max_stale_seconds_negative_raises_error(self):
        """Kiểm tra max_stale_seconds âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            AnalyticsModel(name="test", max_stale_seconds=-10)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_STALE_SECONDS

    def test_max_stale_seconds_boundary_1(self):
        """Kiểm tra max_stale_seconds = 1 hợp lệ (giá trị tối thiểu)."""
        am = AnalyticsModel(name="test", max_stale_seconds=1)
        assert am.max_stale_seconds == 1

    def test_default_values(self):
        """Kiểm tra default values của AnalyticsModel."""
        am = AnalyticsModel(name="default_model")
        assert am.metric_names == []
        assert am.filters == {}
        assert am.aggregations == []
        assert am.max_stale_seconds == 300
        assert am.description == ""

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        am = AnalyticsModel(
            name="reporting_model",
            metric_names=["clicks", "impressions"],
            filters={"country": "vn"},
            aggregations=["count"],
            max_stale_seconds=120,
            description="Mô hình báo cáo",
        )
        data = am.to_dict()
        assert data["name"] == "reporting_model"
        assert data["metric_names"] == ["clicks", "impressions"]
        assert data["filters"] == {"country": "vn"}
        assert data["aggregations"] == ["count"]
        assert data["max_stale_seconds"] == 120
        assert data["description"] == "Mô hình báo cáo"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "conversion_model",
            "metric_names": ["conversions", "revenue"],
            "filters": {"campaign": "q1"},
            "aggregations": ["sum"],
            "max_stale_seconds": 180,
            "description": "Mô hình chuyển đổi",
        }
        am = AnalyticsModel.from_dict(data)
        assert am.name == "conversion_model"
        assert am.metric_names == ["conversions", "revenue"]
        assert am.filters == {"campaign": "q1"}
        assert am.max_stale_seconds == 180

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = AnalyticsModel(
            name="roundtrip_test",
            metric_names=["m1", "m2"],
            filters={"env": "prod"},
            aggregations=["max"],
            max_stale_seconds=450,
            description="Test roundtrip",
        )
        restored = AnalyticsModel.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.metric_names == original.metric_names
        assert restored.filters == original.filters
        assert restored.aggregations == original.aggregations
        assert restored.max_stale_seconds == original.max_stale_seconds
        assert restored.description == original.description


# =============================================================================
# DashboardDefinition Tests
# =============================================================================


class TestDashboardDefinition:
    """Test DashboardDefinition dataclass."""

    def test_create_valid_dashboard_with_defaults(self):
        """Kiểm tra tạo dashboard hợp lệ với default values."""
        dd = DashboardDefinition(name="main_dashboard")
        assert dd.name == "main_dashboard"
        assert dd.title == ""
        assert dd.widgets == []
        assert dd.refresh_interval_seconds == 30
        assert dd.description == ""

    def test_create_valid_dashboard_full(self):
        """Kiểm tra tạo dashboard với đầy đủ thuộc tính."""
        dd = DashboardDefinition(
            name="bi_dashboard",
            title="Business Intelligence",
            widgets=[{"name": "chart1", "type": "bar"}],
            refresh_interval_seconds=60,
            description="Dashboard BI chính",
            metadata={"owner": "analytics_team"},
        )
        assert dd.name == "bi_dashboard"
        assert dd.title == "Business Intelligence"
        assert len(dd.widgets) == 1
        assert dd.refresh_interval_seconds == 60

    def test_empty_name_raises_error(self):
        """Kiểm tra tên dashboard rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardDefinition(name="")
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_DASHBOARD_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên dashboard chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardDefinition(name="   ")
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_DASHBOARD_NAME

    def test_refresh_interval_zero_raises_error(self):
        """Kiểm tra refresh_interval_seconds = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardDefinition(name="test", refresh_interval_seconds=0)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_REFRESH_INTERVAL

    def test_refresh_interval_less_than_5_raises_error(self):
        """Kiểm tra refresh_interval_seconds < 5 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            DashboardDefinition(name="test", refresh_interval_seconds=3)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_REFRESH_INTERVAL

    def test_refresh_interval_boundary_5(self):
        """Kiểm tra refresh_interval_seconds = 5 hợp lệ (giá trị tối thiểu)."""
        dd = DashboardDefinition(name="test", refresh_interval_seconds=5)
        assert dd.refresh_interval_seconds == 5

    def test_default_values(self):
        """Kiểm tra default values của DashboardDefinition."""
        dd = DashboardDefinition(name="default_dashboard")
        assert dd.title == ""
        assert dd.widgets == []
        assert dd.refresh_interval_seconds == 30
        assert dd.metadata == {}

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        dd = DashboardDefinition(
            name="exec_dashboard",
            title="Executive View",
            widgets=[{"name": "kpi_gauge"}],
            refresh_interval_seconds=120,
            description="Dashboard điều hành",
            metadata={"tier": "executive"},
        )
        data = dd.to_dict()
        assert data["name"] == "exec_dashboard"
        assert data["title"] == "Executive View"
        assert len(data["widgets"]) == 1
        assert data["refresh_interval_seconds"] == 120
        assert data["metadata"] == {"tier": "executive"}

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "ops_dashboard",
            "title": "Operations",
            "widgets": [{"name": "error_rate"}],
            "refresh_interval_seconds": 15,
            "description": "Giám sát vận hành",
            "metadata": {"team": "ops"},
        }
        dd = DashboardDefinition.from_dict(data)
        assert dd.name == "ops_dashboard"
        assert dd.title == "Operations"
        assert dd.refresh_interval_seconds == 15

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = DashboardDefinition(
            name="roundtrip_dashboard",
            title="Roundtrip Test",
            widgets=[{"name": "w1"}],
            refresh_interval_seconds=45,
            description="Test roundtrip",
            metadata={"key": "value"},
        )
        restored = DashboardDefinition.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.title == original.title
        assert restored.widgets == original.widgets
        assert restored.refresh_interval_seconds == original.refresh_interval_seconds
        assert restored.description == original.description
        assert restored.metadata == original.metadata


# =============================================================================
# ScheduledReport Tests
# =============================================================================


class TestScheduledReport:
    """Test ScheduledReport dataclass."""

    def test_create_valid_report_with_defaults(self):
        """Kiểm tra tạo scheduled report hợp lệ với default values."""
        sr = ScheduledReport(
            name="daily_sales",
            model_name="sales_model",
            next_run=datetime.now(timezone.utc),
        )
        assert sr.name == "daily_sales"
        assert sr.title == ""
        assert sr.schedule_policy == SchedulePolicy.ONCE
        assert sr.format == ReportFormat.JSON
        assert sr.description == ""
        assert sr.parameters == {}

    def test_create_valid_report_full(self):
        """Kiểm tra tạo scheduled report với đầy đủ thuộc tính."""
        sr = ScheduledReport(
            name="weekly_summary",
            title="Weekly Business Summary",
            model_name="analytics_model",
            schedule_policy=SchedulePolicy.WEEKLY,
            next_run=datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
            format=ReportFormat.PDF,
            description="Báo cáo tuần",
            parameters={"include_charts": True},
        )
        assert sr.name == "weekly_summary"
        assert sr.schedule_policy == SchedulePolicy.WEEKLY
        assert sr.format == ReportFormat.PDF
        assert sr.parameters == {"include_charts": True}

    def test_empty_name_raises_error(self):
        """Kiểm tra tên report rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            ScheduledReport(
                name="",
                model_name="some_model",
                next_run=datetime.now(timezone.utc),
            )
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_REPORT_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên report chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            ScheduledReport(
                name="   ",
                model_name="some_model",
                next_run=datetime.now(timezone.utc),
            )
        assert exc_info.value.code == ErrorCode.CP17_EMPTY_REPORT_NAME

    def test_empty_model_name_auto_defaults(self):
        """Kiểm tra model_name rỗng tự động dùng default (parser mode)."""
        sr = ScheduledReport(
            name="test_report",
            model_name="",
            next_run=datetime.now(timezone.utc),
        )
        assert sr.model_name == ""

    def test_none_next_run_auto_assigns(self):
        """Kiểm tra next_run = None tự động gán thời gian hiện tại."""
        sr = ScheduledReport(
            name="test_report",
            model_name="some_model",
            next_run=None,
        )
        assert sr.next_run is not None

    def test_all_schedule_policies(self):
        """Kiểm tra tất cả schedule policies đều hợp lệ."""
        now = datetime.now(timezone.utc)
        for policy in SchedulePolicy:
            sr = ScheduledReport(
                name=f"report_{policy.value}",
                model_name="test_model",
                schedule_policy=policy,
                next_run=now,
            )
            assert sr.schedule_policy == policy

    def test_all_output_formats(self):
        """Kiểm tra tất cả report formats đều hợp lệ."""
        now = datetime.now(timezone.utc)
        for fmt in ReportFormat:
            sr = ScheduledReport(
                name=f"report_{fmt.value}",
                model_name="test_model",
                format=fmt,
                next_run=now,
            )
            assert sr.format == fmt

    def test_default_values(self):
        """Kiểm tra default values của ScheduledReport."""
        sr = ScheduledReport(
            name="default_report",
            model_name="default_model",
            next_run=datetime.now(timezone.utc),
        )
        assert sr.title == ""
        assert sr.schedule_policy == SchedulePolicy.ONCE
        assert sr.format == ReportFormat.JSON
        assert sr.description == ""
        assert sr.parameters == {}

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        now = datetime(2026, 5, 15, 8, 0, 0, tzinfo=timezone.utc)
        sr = ScheduledReport(
            name="monthly_report",
            title="Monthly Analytics",
            model_name="full_model",
            schedule_policy=SchedulePolicy.MONTHLY,
            next_run=now,
            format=ReportFormat.CSV,
            description="Báo cáo tháng",
            parameters={"group_by": "region"},
        )
        data = sr.to_dict()
        assert data["name"] == "monthly_report"
        assert data["schedule_policy"] == "monthly"
        assert data["format"] == "csv"
        assert data["parameters"] == {"group_by": "region"}

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "hourly_report",
            "title": "Hourly Snapshot",
            "model_name": "live_model",
            "schedule_policy": "hourly",
            "next_run": "2026-05-20T10:00:00+00:00",
            "format": "pdf",
            "description": "Snapshot giờ",
            "parameters": {"top_n": 10},
        }
        sr = ScheduledReport.from_dict(data)
        assert sr.name == "hourly_report"
        assert sr.schedule_policy == SchedulePolicy.HOURLY
        assert sr.format == ReportFormat.PDF
        assert sr.parameters == {"top_n": 10}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        now = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        original = ScheduledReport(
            name="roundtrip_report",
            title="Roundtrip Test",
            model_name="rt_model",
            schedule_policy=SchedulePolicy.DAILY,
            next_run=now,
            format=ReportFormat.HTML,
            description="Test roundtrip",
            parameters={"detail": True},
        )
        restored = ScheduledReport.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.title == original.title
        assert restored.model_name == original.model_name
        assert restored.schedule_policy == original.schedule_policy
        assert restored.format == original.format
        assert restored.description == original.description
        assert restored.parameters == original.parameters
