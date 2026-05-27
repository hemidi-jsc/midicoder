# coding: utf-8
"""
Test cases cho CP17 Business Intelligence & Analytics Parser.

Kiểm tra:
- AnalyticsParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid types, invalid enums
- Edge cases: Empty input, missing sections, default values

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp17_bi_analytics.parser import AnalyticsParser
from midicoder.packs.cp17_bi_analytics.models import (
    AggregationType,
    AnalyticsModel,
    AnalyticsSourceType,
    DashboardDefinition,
    ReportFrequency,
    ScheduledReport,
    VisualizationType,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestAnalyticsParser:
    """Test suite cho AnalyticsParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = AnalyticsParser()

    # =========================================================================
    # Empty / whitespace input
    # =========================================================================

    def test_parse_empty_string_returns_empty_dicts(self):
        """Kiểm tra parse string rỗng trả về dict rỗng cho tất cả sections."""
        result = self.parser.parse("")
        assert result == {
            "analytics_models": [],
            "dashboards": [],
            "reports": [],
        }

    def test_parse_whitespace_only_returns_empty_dicts(self):
        """Kiểm tra parse whitespace trả về dict rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert result == {
            "analytics_models": [],
            "dashboards": [],
            "reports": [],
        }

    def test_parse_comment_only_returns_empty_dicts(self):
        """Kiểm tra parse chỉ có comment YAML trả về dict rỗng."""
        dsl = """
# Chỉ có comment
# Không có dữ liệu
"""
        result = self.parser.parse(dsl)
        assert result == {
            "analytics_models": [],
            "dashboards": [],
            "reports": [],
        }

    # =========================================================================
    # Valid analytics_models section
    # =========================================================================

    def test_parse_single_analytics_model(self):
        """Kiểm tra parse analytics model hợp lệ."""
        dsl = """
analytics_models:
  - name: api_performance
    source_type: metric_registry
    metric_names:
      - http_requests_total
      - http_errors_total
    aggregations:
      - sum
      - average
    max_stale_seconds: 300
"""
        result = self.parser.parse(dsl)
        assert len(result["analytics_models"]) == 1
        assert len(result["dashboards"]) == 0
        assert len(result["reports"]) == 0

        model = result["analytics_models"][0]
        assert isinstance(model, AnalyticsModel)
        assert model.name == "api_performance"
        assert model.source_type == AnalyticsSourceType.METRIC_REGISTRY
        assert model.metric_names == ["http_requests_total", "http_errors_total"]
        assert model.aggregations == [AggregationType.SUM, AggregationType.AVERAGE]
        assert model.max_stale_seconds == 300

    def test_parse_analytics_model_with_database_source(self):
        """Kiểm tra parse analytics model với source_type database."""
        dsl = """
analytics_models:
  - name: business_metrics
    source_type: database
    metric_names:
      - orders_count
      - revenue
    aggregations:
      - sum
      - max
    max_stale_seconds: 600
"""
        result = self.parser.parse(dsl)
        model = result["analytics_models"][0]
        assert model.source_type == AnalyticsSourceType.DATABASE
        assert model.aggregations == [AggregationType.SUM, AggregationType.MAX]
        assert model.max_stale_seconds == 600

    def test_parse_analytics_model_with_defaults(self):
        """Kiểm tra parse analytics model chỉ có name, các field còn lại dùng default."""
        dsl = """
analytics_models:
  - name: minimal-model
"""
        result = self.parser.parse(dsl)
        model = result["analytics_models"][0]
        assert model.name == "minimal-model"
        assert model.source_type == AnalyticsSourceType.METRIC_REGISTRY
        assert model.metric_names == []
        assert model.aggregations == []
        assert model.max_stale_seconds == 300

    # =========================================================================
    # Valid dashboards section
    # =========================================================================

    def test_parse_single_dashboard_with_widgets(self):
        """Kiểm tra parse dashboard hợp lệ với widgets."""
        dsl = """
dashboards:
  - name: executive-overview
    title: Executive Overview
    refresh_interval_seconds: 60
    widgets:
      - name: revenue_trend
        visualization_type: line_chart
        metric_name: revenue
      - name: error_breakdown
        visualization_type: pie_chart
        metric_name: http_errors_total
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 1

        dashboard = result["dashboards"][0]
        assert isinstance(dashboard, DashboardDefinition)
        assert dashboard.name == "executive-overview"
        assert dashboard.title == "Executive Overview"
        assert dashboard.refresh_interval_seconds == 60
        assert len(dashboard.widgets) == 2

        # Kiểm tra widget đầu tiên
        widget = dashboard.widgets[0]
        assert widget["name"] == "revenue_trend"
        assert widget["visualization_type"] == VisualizationType.LINE_CHART
        assert widget["metric_name"] == "revenue"

        # Kiểm tra widget thứ hai
        widget2 = dashboard.widgets[1]
        assert widget2["visualization_type"] == VisualizationType.PIE_CHART

    def test_parse_dashboard_with_defaults(self):
        """Kiểm tra parse dashboard chỉ có name, các field còn lại dùng default."""
        dsl = """
dashboards:
  - name: minimal-dashboard
"""
        result = self.parser.parse(dsl)
        dashboard = result["dashboards"][0]
        assert dashboard.name == "minimal-dashboard"
        assert dashboard.title == ""
        assert dashboard.refresh_interval_seconds == 30
        assert dashboard.widgets == []

    def test_parse_dashboard_with_all_visualization_types(self):
        """Kiểm tra parse dashboard với các loại visualization khác nhau."""
        dsl = """
dashboards:
  - name: multi-widget
    title: Multi Widget Dashboard
    widgets:
      - name: line_w
        visualization_type: line_chart
        metric_name: m1
      - name: bar_w
        visualization_type: bar_chart
        metric_name: m2
      - name: table_w
        visualization_type: table
        metric_name: m3
      - name: gauge_w
        visualization_type: gauge
        metric_name: m4
"""
        result = self.parser.parse(dsl)
        widgets = result["dashboards"][0].widgets
        assert len(widgets) == 4
        assert widgets[0]["visualization_type"] == VisualizationType.LINE_CHART
        assert widgets[1]["visualization_type"] == VisualizationType.BAR_CHART
        assert widgets[2]["visualization_type"] == VisualizationType.TABLE
        assert widgets[3]["visualization_type"] == VisualizationType.GAUGE

    # =========================================================================
    # Valid reports section
    # =========================================================================

    def test_parse_single_scheduled_report(self):
        """Kiểm tra parse scheduled report hợp lệ."""
        dsl = """
reports:
  - name: daily-summary
    title: Daily Business Summary
    model_name: business_metrics
    frequency: daily
    output_format: json
    recipients:
      - cto@company.com
"""
        result = self.parser.parse(dsl)
        assert len(result["reports"]) == 1

        report = result["reports"][0]
        assert isinstance(report, ScheduledReport)
        assert report.name == "daily-summary"
        assert report.title == "Daily Business Summary"
        assert report.model_name == "business_metrics"
        assert report.frequency == ReportFrequency.DAILY
        assert report.output_format == "json"
        assert report.recipients == ["cto@company.com"]

    def test_parse_report_with_weekly_frequency(self):
        """Kiểm tra parse report với frequency weekly."""
        dsl = """
reports:
  - name: weekly-analytics
    title: Weekly Analytics
    model_name: api_performance
    frequency: weekly
    output_format: json
    recipients:
      - team@company.com
"""
        result = self.parser.parse(dsl)
        report = result["reports"][0]
        assert report.frequency == ReportFrequency.WEEKLY

    def test_parse_report_with_defaults(self):
        """Kiểm tra parse report chỉ có name, các field còn lại dùng default."""
        dsl = """
reports:
  - name: minimal-report
"""
        result = self.parser.parse(dsl)
        report = result["reports"][0]
        assert report.name == "minimal-report"
        assert report.title == ""
        assert report.model_name == ""
        assert report.frequency == ReportFrequency.DAILY
        assert report.output_format == "json"
        assert report.recipients == []

    # =========================================================================
    # Full DSL with all 3 sections
    # =========================================================================

    def test_parse_full_dsl_all_sections(self):
        """Kiểm tra parse DSL đầy đủ với cả 3 sections."""
        dsl = """
analytics_models:
  - name: api_performance
    source_type: metric_registry
    metric_names:
      - http_requests_total
      - http_errors_total
    aggregations:
      - sum
      - average
    max_stale_seconds: 300
  - name: business_metrics
    source_type: database
    metric_names:
      - orders_count
      - revenue
    aggregations:
      - sum
      - max
    max_stale_seconds: 600
dashboards:
  - name: executive-overview
    title: Executive Overview
    refresh_interval_seconds: 60
    widgets:
      - name: revenue_trend
        visualization_type: line_chart
        metric_name: revenue
      - name: error_breakdown
        visualization_type: pie_chart
        metric_name: http_errors_total
reports:
  - name: daily-summary
    title: Daily Business Summary
    model_name: business_metrics
    frequency: daily
    output_format: json
    recipients:
      - cto@company.com
  - name: weekly-analytics
    title: Weekly Analytics Report
    model_name: api_performance
    frequency: weekly
    output_format: json
    recipients:
      - team@company.com
"""
        result = self.parser.parse(dsl)
        assert len(result["analytics_models"]) == 2
        assert len(result["dashboards"]) == 1
        assert len(result["reports"]) == 2

        # Verify analytics models
        assert result["analytics_models"][0].source_type == AnalyticsSourceType.METRIC_REGISTRY
        assert result["analytics_models"][1].source_type == AnalyticsSourceType.DATABASE

        # Verify dashboard
        assert result["dashboards"][0].title == "Executive Overview"
        assert len(result["dashboards"][0].widgets) == 2

        # Verify reports
        assert result["reports"][0].frequency == ReportFrequency.DAILY
        assert result["reports"][1].frequency == ReportFrequency.WEEKLY

    # =========================================================================
    # Invalid YAML
    # =========================================================================

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw error."""
        invalid_yaml = """
analytics_models:
  - name: test
    source_type: [invalid yaml
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra parse YAML list (không phải mapping) throw error."""
        list_yaml = """
- item1
- item2
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(list_yaml)
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR

    # =========================================================================
    # Invalid enum values
    # =========================================================================

    def test_parse_invalid_source_type_raises_error(self):
        """Kiểm tra source_type không hợp lệ throw error."""
        dsl = """
analytics_models:
  - name: bad-model
    source_type: invalid_source
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_SOURCE_TYPE

    def test_parse_invalid_aggregation_type_raises_error(self):
        """Kiểm tra aggregation type không hợp lệ throw error."""
        dsl = """
analytics_models:
  - name: bad-model
    aggregations:
      - invalid_agg
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_AGGREGATION_TYPE

    def test_parse_invalid_report_frequency_raises_error(self):
        """Kiểm tra report frequency không hợp lệ throw error."""
        dsl = """
reports:
  - name: bad-report
    frequency: invalid_freq
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_REPORT_FREQUENCY

    def test_parse_invalid_visualization_type_raises_error(self):
        """Kiểm tra visualization_type không hợp lệ throw error."""
        dsl = """
dashboards:
  - name: bad-dashboard
    widgets:
      - name: bad_widget
        visualization_type: scatter_plot
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP17_INVALID_VISUALIZATION_TYPE

    # =========================================================================
    # Missing sections
    # =========================================================================

    def test_parse_only_analytics_models_section(self):
        """Kiểm tra parse chỉ có analytics_models, các section khác rỗng."""
        dsl = """
analytics_models:
  - name: only-model
    source_type: metric_registry
"""
        result = self.parser.parse(dsl)
        assert len(result["analytics_models"]) == 1
        assert result["dashboards"] == []
        assert result["reports"] == []

    def test_parse_only_dashboards_section(self):
        """Kiểm tra parse chỉ có dashboards, các section khác rỗng."""
        dsl = """
dashboards:
  - name: only-dashboard
    title: Only Dashboard
"""
        result = self.parser.parse(dsl)
        assert result["analytics_models"] == []
        assert len(result["dashboards"]) == 1
        assert result["reports"] == []

    def test_parse_only_reports_section(self):
        """Kiểm tra parse chỉ có reports, các section khác rỗng."""
        dsl = """
reports:
  - name: only-report
    frequency: weekly
"""
        result = self.parser.parse(dsl)
        assert result["analytics_models"] == []
        assert result["dashboards"] == []
        assert len(result["reports"]) == 1

    def test_parse_empty_sections(self):
        """Kiểm tra parse với các section rỗng."""
        dsl = """
analytics_models: []
dashboards: []
reports: []
"""
        result = self.parser.parse(dsl)
        assert result["analytics_models"] == []
        assert result["dashboards"] == []
        assert result["reports"] == []

    # =========================================================================
    # Multiple entries in each section
    # =========================================================================

    def test_parse_multiple_analytics_models(self):
        """Kiểm tra parse nhiều analytics models cùng lúc."""
        dsl = """
analytics_models:
  - name: model-1
    source_type: metric_registry
    aggregations:
      - sum
  - name: model-2
    source_type: database
    aggregations:
      - average
  - name: model-3
    source_type: external_api
    aggregations:
      - max
      - min
"""
        result = self.parser.parse(dsl)
        assert len(result["analytics_models"]) == 3
        assert result["analytics_models"][0].source_type == AnalyticsSourceType.METRIC_REGISTRY
        assert result["analytics_models"][1].source_type == AnalyticsSourceType.DATABASE
        assert result["analytics_models"][2].source_type == AnalyticsSourceType.EXTERNAL_API

    def test_parse_multiple_dashboards(self):
        """Kiểm tra parse nhiều dashboards cùng lúc."""
        dsl = """
dashboards:
  - name: dashboard-1
    title: First Dashboard
    refresh_interval_seconds: 30
  - name: dashboard-2
    title: Second Dashboard
    refresh_interval_seconds: 120
"""
        result = self.parser.parse(dsl)
        assert len(result["dashboards"]) == 2
        assert result["dashboards"][0].title == "First Dashboard"
        assert result["dashboards"][1].title == "Second Dashboard"

    def test_parse_multiple_reports(self):
        """Kiểm tra parse nhiều reports cùng lúc."""
        dsl = """
reports:
  - name: report-daily
    frequency: daily
    recipients:
      - daily@team.com
  - name: report-weekly
    frequency: weekly
    recipients:
      - weekly@team.com
  - name: report-monthly
    frequency: monthly
    recipients:
      - monthly@team.com
"""
        result = self.parser.parse(dsl)
        assert len(result["reports"]) == 3
        assert result["reports"][0].frequency == ReportFrequency.DAILY
        assert result["reports"][1].frequency == ReportFrequency.WEEKLY
        assert result["reports"][2].frequency == ReportFrequency.MONTHLY
