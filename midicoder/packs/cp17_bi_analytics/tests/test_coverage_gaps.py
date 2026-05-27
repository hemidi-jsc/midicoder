
# coding: utf-8
"""
Test để đạt 100% coverage cho các gap còn lại:
- parser.py: non-dict entry trong analytics_models, dashboards, reports, widgets
- parser.py: non-list sections (aggregations, widgets)
- report_scheduler.py: branch khi report_name đã có trong _snapshots (generate 2 lần)
- report_scheduler.py: registry có model_name nhưng trả về None
- report_scheduler.py: SchedulePolicy.ONCE
"""

import pytest

from midicoder.packs.cp17_bi_analytics.parser import AnalyticsParser
from midicoder.packs.cp17_bi_analytics.models import ReportFrequency, ScheduledReport
from midicoder.packs.cp17_bi_analytics.report_scheduler import ReportScheduler
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Parser coverage gaps — non-dict entries
# ===========================================================================


class TestParserNonDictEntries:
    """Kiểm tra parser reject non-dict entries trong các danh sách."""

    def test_parse_analytics_model_non_dict_entry(self):
        """Non-dict entry trong analytics_models phải raise CP17_ANALYTICS_PARSE_ERROR."""
        parser = AnalyticsParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("""\
analytics_models:
  - "not_a_mapping"
""")
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR

    def test_parse_dashboard_non_dict_entry(self):
        """Non-dict entry trong dashboards phải raise CP17_ANALYTICS_PARSE_ERROR."""
        parser = AnalyticsParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("""\
dashboards:
  - "not_a_mapping"
""")
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR

    def test_parse_report_non_dict_entry(self):
        """Non-dict entry trong reports phải raise CP17_ANALYTICS_PARSE_ERROR."""
        parser = AnalyticsParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("""\
reports:
  - "not_a_mapping"
""")
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR

    def test_parse_widget_non_dict_entry(self):
        """Non-dict entry trong widgets phải raise CP17_ANALYTICS_PARSE_ERROR."""
        parser = AnalyticsParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("""\
dashboards:
  - name: "test_dash"
    widgets:
      - "not_a_mapping"
""")
        assert exc_info.value.code == ErrorCode.CP17_ANALYTICS_PARSE_ERROR


# ===========================================================================
# Parser coverage gaps — non-list aggregations/widgets
# ===========================================================================


class TestParserNonListSubFields:
    """Kiểm tra parser bỏ qua sub-fields không phải list."""

    def test_parse_analytics_model_aggregations_not_list(self):
        """aggregations không phải list phải được bỏ qua."""
        parser = AnalyticsParser()
        result = parser.parse("""\
analytics_models:
  - name: "test"
    aggregations: "not_a_list"
""")
        assert len(result["analytics_models"]) == 1
        assert result["analytics_models"][0].aggregations == []

    def test_parse_dashboard_widgets_not_list(self):
        """widgets không phải list phải được bỏ qua."""
        parser = AnalyticsParser()
        result = parser.parse("""\
dashboards:
  - name: "test_dash"
    widgets: "not_a_list"
""")
        assert len(result["dashboards"]) == 1
        assert result["dashboards"][0].widgets == []


# ===========================================================================
# ReportScheduler coverage gaps — registry returns None
# ===========================================================================


class TestReportSchedulerRegistryNone:
    """Kiểm tra branch khi registry.get() trả về None."""

    def test_generate_report_registry_returns_none(self):
        """Khi registry.get(model_name) trả về None, metrics phải rỗng."""
        from midicoder.packs.cp17_bi_analytics.models import (
            ReportFormat,
            ScheduledReport,
        )

        report = ScheduledReport(
            name="test_report",
            title="Test Report",
            model_name="nonexistent_model",
            frequency=ReportFrequency.DAILY,
        )

        scheduler = ReportScheduler()
        scheduler.schedule_report(report)

        # Registry có data nhưng không có model_name này
        class FakeRegistry:
            def get(self, name, labels=None):
                return None  # model_name không tồn tại

        snapshot = scheduler.generate_report("test_report", registry=FakeRegistry())
        assert snapshot.data["metrics"] == {}


# ===========================================================================
# ReportScheduler coverage gaps — SchedulePolicy.ONCE
# ===========================================================================


class TestReportSchedulerOncePolicy:
    """Kiểm tra SchedulePolicy.ONCE trong _update_next_run."""

    def test_update_next_run_once_sets_far_future(self):
        """SchedulePolicy.ONCE phải set next_run rất xa tương lai (2999)."""
        from datetime import datetime, timezone

        from midicoder.packs.cp17_bi_analytics.models import SchedulePolicy

        report = ScheduledReport(
            name="once_report",
            title="Once Report",
            model_name="test",
            frequency=ReportFrequency.DAILY,
            schedule_policy=SchedulePolicy.ONCE,
        )

        scheduler = ReportScheduler()
        scheduler.schedule_report(report)
        scheduler.generate_report("once_report")

        # SchedulePolicy.ONCE set next_run = 2999-12-31 23:59:59 UTC
        assert scheduler._reports["once_report"].next_run == datetime(2999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)  # noqa: SLF001


# ===========================================================================
# ReportScheduler coverage gap — generate_report 2 lần
# ===========================================================================


class TestReportSchedulerSnapshotAppend:
    """Kiểm tra branch khi report_name đã có trong _snapshots."""

    def test_generate_report_appends_to_existing_snapshots(self):
        """Generate report 2 lần phải append snapshot mới vào _snapshots existing."""
        from datetime import datetime, timezone

        from midicoder.packs.cp17_bi_analytics.models import (
            AggregationType,
            AnalyticsModel,
            AnalyticsSourceType,
        )

        report = ScheduledReport(
            name="test_report",
            title="Test Report",
            model_name="sales",
            frequency=ReportFrequency.DAILY,
        )

        scheduler = ReportScheduler()
        scheduler.schedule_report(report)

        # Generate report 1 lần
        snap1 = scheduler.generate_report("test_report")
        assert len(scheduler._snapshots["test_report"]) == 1  # noqa: SLF001

        # Generate report lần 2 — phải append vào existing snapshots
        snap2 = scheduler.generate_report("test_report")
        snapshots = scheduler._snapshots["test_report"]  # noqa: SLF001
        assert len(snapshots) == 2
        assert snap1 is snapshots[0]
        assert snap2 is snapshots[1]
