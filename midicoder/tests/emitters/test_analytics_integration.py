"""
Integration tests CP17 — Business Intelligence & Analytics Generator.

Kiểm tra:
- Parser → Engine wiring (analytics_models, dashboards, reports)
- All 4 emitters produce non-empty output
- Pack.yml sync (capabilities, status, models, enums)
- Taxonomy sync (CP17 status = stable)
- CP15 → CP17 data flow (mock MetricRegistry → AnalyticsEngine.query())
- Full pipeline: parse → register → query → dashboard → report → snapshot immutability
"""

import json
import os
import sys
from datetime import datetime, timezone

import pytest
import yaml

# Thêm project root vào path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ===========================================================================
# Mock CP15 MetricRegistry for testing
# ===========================================================================

class MockEntry:
    """Mock metric entry mimicking CP15 MetricRegistry output."""
    def __init__(self, name, value, timestamp):
        self.name = name
        self.value = value
        self.timestamp = timestamp


class MockRegistry:
    """Mock MetricRegistry for CP15 → CP17 data flow tests."""
    def __init__(self):
        self._data = {}

    def get(self, name, labels=None):
        return self._data.get(name, [])

    def add(self, name, entries):
        self._data[name] = entries


# ===========================================================================
# Full DSL fixture
# ===========================================================================

FULL_ANALYTICS_DSL = """\
analytics_models:
  - name: "sales_overview"
    source_type: "metric_registry"
    metric_names:
      - "revenue_total"
      - "order_count"
    aggregations:
      - "sum"
      - "average"
      - "count"
    max_stale_seconds: 600

dashboards:
  - name: "exec_dashboard"
    title: "Executive Sales Dashboard"
    refresh_interval_seconds: 60
    widgets:
      - name: "revenue_chart"
        visualization_type: "line_chart"
        metric_name: "revenue_total"
      - name: "order_gauge"
        visualization_type: "gauge"
        metric_name: "order_count"

reports:
  - name: "weekly_sales_report"
    title: "Weekly Sales Summary"
    model_name: "sales_overview"
    frequency: "weekly"
    output_format: "json"
    recipients:
      - "cto@example.com"
      - "cfo@example.com"
"""


# ===========================================================================
# Test 1: Parser → Engine wiring
# ===========================================================================

class TestParserEngineWiring:
    """Kiểm tra parse DSL → wire vào AnalyticsEngine, DashboardBuilder, ReportScheduler."""

    def test_parse_full_dsl_all_three_sections(self):
        """Parser phải parse đầy đủ 3 sections: analytics_models, dashboards, reports."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)

        assert "analytics_models" in result
        assert "dashboards" in result
        assert "reports" in result

        assert len(result["analytics_models"]) == 1
        assert len(result["dashboards"]) == 1
        assert len(result["reports"]) == 1

    def test_parse_models_registered_in_engine(self):
        """Models từ parser phải đăng ký thành công vào AnalyticsEngine."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)

        engine = AnalyticsEngine()
        for model in result["analytics_models"]:
            engine.register_model(model)

        models = engine.get_available_models()
        assert len(models) == 1
        assert models[0].name == "sales_overview"
        assert models[0].metric_names == ["revenue_total", "order_count"]

    def test_parse_dashboards_created_in_builder(self):
        """Dashboards từ parser phải tạo thành công trong DashboardBuilder."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.dashboard_builder import DashboardBuilder

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)

        builder = DashboardBuilder()
        for dashboard_def in result["dashboards"]:
            builder.create_dashboard(dashboard_def)

        dashboards = builder.list_dashboards()
        assert len(dashboards) == 1
        assert dashboards[0].name == "exec_dashboard"
        assert dashboards[0].title == "Executive Sales Dashboard"

    def test_parse_reports_scheduled_in_scheduler(self):
        """Reports từ parser phải lập lịch thành công trong ReportScheduler."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import ReportScheduler

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)

        scheduler = ReportScheduler()
        for report_def in result["reports"]:
            scheduler.schedule_report(report_def)

        scheduled = scheduler.get_scheduled_reports()
        assert len(scheduled) == 1
        assert scheduled[0].name == "weekly_sales_report"
        assert scheduled[0].title == "Weekly Sales Summary"

    def test_parse_empty_dsl_returns_empty_lists(self):
        """Parser với DSL rỗng phải trả về danh sách rỗng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser

        parser = AnalyticsParser()
        result = parser.parse("")

        assert result["analytics_models"] == []
        assert result["dashboards"] == []
        assert result["reports"] == []

    def test_parse_whitespace_dsl_returns_empty_lists(self):
        """Parser với DSL chỉ whitespace phải trả về danh sách rỗng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser

        parser = AnalyticsParser()
        result = parser.parse("   \n  \n  ")

        assert result["analytics_models"] == []
        assert result["dashboards"] == []
        assert result["reports"] == []


# ===========================================================================
# Test 2: All 4 emitters produce output
# ===========================================================================

class TestAllEmittersProduceOutput:
    """Kiểm tra tất cả 4 emitters generate Dict[str, str] không rỗng."""

    def test_fastapi_emitter_produces_files(self):
        """FastAPIAnalyticsEmitter phải generate các file Python."""
        from midicoder.emitters.core.cp17_bi_analytics.fastapi import FastAPIAnalyticsEmitter

        emitter = FastAPIAnalyticsEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) >= 1, "FastAPIAnalyticsEmitter phải generate ít nhất 1 file"
        for path, content in result.items():
            assert isinstance(path, str)
            assert isinstance(content, str)
            assert len(content) > 0

    def test_nestjs_emitter_produces_files(self):
        """NestJSAnalyticsEmitter phải generate các file TypeScript."""
        from midicoder.emitters.core.cp17_bi_analytics.nestjs import NestJSAnalyticsEmitter

        emitter = NestJSAnalyticsEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) >= 1, "NestJSAnalyticsEmitter phải generate ít nhất 1 file"
        for path, content in result.items():
            assert isinstance(path, str)
            assert isinstance(content, str)
            assert len(content) > 0

    def test_angular_emitter_produces_files(self):
        """AngularAnalyticsEmitter phải generate các file TypeScript."""
        from midicoder.emitters.core.cp17_bi_analytics.angular import AngularAnalyticsEmitter

        emitter = AngularAnalyticsEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) >= 1, "AngularAnalyticsEmitter phải generate ít nhất 1 file"
        for path, content in result.items():
            assert isinstance(path, str)
            assert isinstance(content, str)
            assert len(content) > 0

    def test_react_emitter_produces_files(self):
        """ReactAnalyticsEmitter phải generate các file TypeScript."""
        from midicoder.emitters.core.cp17_bi_analytics.react import ReactAnalyticsEmitter

        emitter = ReactAnalyticsEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) >= 1, "ReactAnalyticsEmitter phải generate ít nhất 1 file"
        for path, content in result.items():
            assert isinstance(path, str)
            assert isinstance(content, str)
            assert len(content) > 0

    def test_all_4_emitters_non_empty(self):
        """Tất cả 4 emitters phải generate kết quả không rỗng."""
        from midicoder.emitters.core.cp17_bi_analytics.fastapi import FastAPIAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.nestjs import NestJSAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.angular import AngularAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.react import ReactAnalyticsEmitter

        for cls in [FastAPIAnalyticsEmitter, NestJSAnalyticsEmitter,
                     AngularAnalyticsEmitter, ReactAnalyticsEmitter]:
            emitter = cls()
            result = emitter.generate()
            assert isinstance(result, dict), f"{cls.__name__} phải trả về Dict[str, str]"
            assert len(result) > 0, f"{cls.__name__} phải generate ít nhất 1 file"


# ===========================================================================
# Test 3: Pack.yml sync
# ===========================================================================

class TestPackYmlSync:
    """Kiểm tra pack.yml đồng bộ với taxonomy.yml và code."""

    def test_pack_yml_exists(self):
        """pack.yml phải tồn tại."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        assert os.path.isfile(pack_path), "pack.yml missing"

    def test_pack_capabilities_provided(self):
        """pack.yml capabilities_provided phải đúng."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        caps = pack.get("pack", {}).get("capabilities_provided", [])
        assert "analytics_query" in caps
        assert "dashboard_build" in caps
        assert "report_schedule" in caps

    def test_pack_status_stable(self):
        """pack.yml status phải là 'stable'."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        assert pack.get("pack", {}).get("status") == "stable"

    def test_pack_models_list(self):
        """pack.yml models phải liệt kê đúng 3 models."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        models = pack.get("pack", {}).get("models", [])
        assert "AnalyticsModel" in models
        assert "DashboardDefinition" in models
        assert "ScheduledReport" in models

    def test_pack_enums_list(self):
        """pack.yml enums phải liệt kê đủ enums."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        enums = pack.get("pack", {}).get("enums", [])
        expected_enums = [
            "AnalyticsSourceType",
            "AggregationType",
            "VisualizationType",
            "ReportFrequency",
            "ReportFormat",
            "SchedulePolicy",
        ]
        for enum_name in expected_enums:
            assert enum_name in enums, f"Enum {enum_name} missing from pack.yml"


# ===========================================================================
# Test 4: Taxonomy sync
# ===========================================================================

class TestTaxonomySync:
    """Kiểm tra taxonomy.yml CP17 status là 'stable' (không phải 'planned')."""

    def test_taxonomy_cp17_status_stable(self):
        """taxonomy.yml CP17 status phải là 'stable'."""
        taxonomy_path = os.path.join(
            os.path.dirname(PROJECT_ROOT), "industry", "taxonomy.yml"
        )
        if not os.path.isfile(taxonomy_path):
            taxonomy_path = os.path.join(PROJECT_ROOT, "..", "industry", "taxonomy.yml")

        with open(taxonomy_path, "r") as f:
            taxonomy = yaml.safe_load(f)

        cp17 = None
        for pack in taxonomy.get("core_packs", []):
            if pack.get("id") == "CP17":
                cp17 = pack
                break

        assert cp17 is not None, "CP17 không tìm thấy trong taxonomy"
        assert cp17.get("status") == "stable", \
            f"CP17 status phải là stable, got {cp17.get('status')}"

    def test_taxonomy_cp17_capabilities_match_pack(self):
        """taxonomy.yml CP17 capabilities phải khớp với pack.yml."""
        # Load pack.yml
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "analytics", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        pack_caps = set(pack.get("pack", {}).get("capabilities_provided", []))

        # Load taxonomy.yml
        taxonomy_path = os.path.join(
            os.path.dirname(PROJECT_ROOT), "industry", "taxonomy.yml"
        )
        with open(taxonomy_path, "r") as f:
            taxonomy = yaml.safe_load(f)

        cp17 = None
        for pack_entry in taxonomy.get("core_packs", []):
            if pack_entry.get("id") == "CP17":
                cp17 = pack_entry
                break

        assert cp17 is not None, "CP17 không tìm thấy trong taxonomy"
        taxonomy_caps = set(cp17.get("capabilities_provided", []))

        assert pack_caps == taxonomy_caps, \
            f"Capabilities mismatch: pack={pack_caps}, taxonomy={taxonomy_caps}"


# ===========================================================================
# Test 5: CP15 → CP17 data flow
# ===========================================================================

class TestCP15ToCP17DataFlow:
    """Kiểm tra MockRegistry (mimicking CP15) → AnalyticsEngine.query() data flow."""

    def test_engine_query_reads_from_mock_registry(self):
        """AnalyticsEngine.query() phải đọc dữ liệu từ mock MetricRegistry."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        # Parse model
        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        # Create mock registry with data
        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("revenue_total", [
            MockEntry("revenue_total", 100.0, now),
            MockEntry("revenue_total", 200.0, now),
            MockEntry("revenue_total", 150.0, now),
        ])
        registry.add("order_count", [
            MockEntry("order_count", 10.0, now),
            MockEntry("order_count", 25.0, now),
        ])

        # Register model and query
        engine = AnalyticsEngine()
        engine.register_model(model)
        query_result = engine.query("sales_overview", registry=registry)

        # Verify: row_count = 3 (revenue) + 2 (orders) = 5 entries total
        assert query_result.row_count == 5
        assert query_result.model_name == "sales_overview"

    def test_engine_query_aggregation_from_registry(self):
        """Aggregation từ registry phải trả về kết quả đúng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("revenue_total", [
            MockEntry("revenue_total", 100.0, now),
            MockEntry("revenue_total", 200.0, now),
            MockEntry("revenue_total", 300.0, now),
        ])
        registry.add("order_count", [])

        engine = AnalyticsEngine()
        engine.register_model(model)
        query_result = engine.query("sales_overview", registry=registry)

        # 3 entries from revenue_total, 0 from order_count
        assert query_result.row_count == 3
        # sum = 100 + 200 + 300 = 600
        assert query_result.aggregations["sum"] == 600.0
        # average = 600 / 3 = 200
        assert query_result.aggregations["average"] == 200.0
        # count = 3
        assert query_result.aggregations["count"] == 3.0

    def test_engine_query_empty_registry(self):
        """Query với registry rỗng phải trả về aggregation = 0."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        registry = MockRegistry()
        # Không thêm dữ liệu

        engine = AnalyticsEngine()
        engine.register_model(model)
        query_result = engine.query("sales_overview", registry=registry)

        assert query_result.row_count == 0
        assert query_result.aggregations["sum"] == 0.0
        assert query_result.aggregations["count"] == 0.0

    def test_engine_query_no_registry(self):
        """Query không có registry phải trả về kết quả rỗng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        engine = AnalyticsEngine()
        engine.register_model(model)
        query_result = engine.query("sales_overview")

        assert query_result.row_count == 0
        assert query_result.model_name == "sales_overview"

    def test_engine_query_hash_immutability(self):
        """QueryResult hash_value phải khác nhau khi dữ liệu thay đổi."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        engine = AnalyticsEngine()
        engine.register_model(model)

        registry1 = MockRegistry()
        registry1.add("revenue_total", [MockEntry("revenue_total", 100.0, datetime.now(timezone.utc))])

        registry2 = MockRegistry()
        registry2.add("revenue_total", [MockEntry("revenue_total", 200.0, datetime.now(timezone.utc))])

        qr1 = engine.query("sales_overview", registry=registry1)
        qr2 = engine.query("sales_overview", registry=registry2)

        assert qr1.hash_value != qr2.hash_value, \
            "Hash phải khác nhau khi dữ liệu thay đổi"

    def test_engine_query_max_min_aggregation(self):
        """Aggregation max/min phải trả về giá trị đúng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine
        from midicoder.emitters.core.cp17_bi_analytics.models import AggregationType

        parser = AnalyticsParser()
        result = parser.parse(FULL_ANALYTICS_DSL)
        model = result["analytics_models"][0]

        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("revenue_total", [
            MockEntry("revenue_total", 50.0, now),
            MockEntry("revenue_total", 150.0, now),
            MockEntry("revenue_total", 100.0, now),
        ])

        engine = AnalyticsEngine()
        engine.register_model(model)
        query_result = engine.query(
            "sales_overview",
            aggregations=["max", "min"],
            registry=registry,
        )

        assert query_result.aggregations["max"] == 150.0
        assert query_result.aggregations["min"] == 50.0


# ===========================================================================
# Test 6: Full pipeline
# ===========================================================================

class TestFullPipeline:
    """Kiểm tra full pipeline: parse → register → query → dashboard → report → snapshot."""

    def test_full_pipeline_end_to_end(self):
        """Full pipeline: DSL → Engine → MockRegistry → Dashboard → Report → Snapshot."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine
        from midicoder.emitters.core.cp17_bi_analytics.dashboard_builder import DashboardBuilder
        from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import ReportScheduler

        # --- Step 1: Parse DSL ---
        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)
        assert len(parsed["analytics_models"]) == 1
        assert len(parsed["dashboards"]) == 1
        assert len(parsed["reports"]) == 1

        # --- Step 2: Register model in engine ---
        engine = AnalyticsEngine()
        for model in parsed["analytics_models"]:
            engine.register_model(model)
        assert len(engine.get_available_models()) == 1

        # --- Step 3: Create mock registry and query ---
        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("revenue_total", [
            MockEntry("revenue_total", 500.0, now),
            MockEntry("revenue_total", 750.0, now),
        ])
        registry.add("order_count", [
            MockEntry("order_count", 5.0, now),
            MockEntry("order_count", 12.0, now),
        ])

        query_result = engine.query("sales_overview", registry=registry)
        assert query_result.row_count == 4
        assert query_result.aggregations["sum"] == 1267.0  # 500+750+5+12
        assert query_result.hash_value is not None

        # --- Step 4: Create dashboard and add widgets ---
        builder = DashboardBuilder()
        dashboard_def = parsed["dashboards"][0]
        builder.create_dashboard(dashboard_def)

        # Add widgets from parsed definition
        for widget_def in dashboard_def.widgets:
            # VisualizationType enum has a .value, convert to string for Widget
            viz_type = widget_def["visualization_type"]
            if hasattr(viz_type, "value"):
                widget_def["visualization_type"] = viz_type.value
            builder.add_widget("exec_dashboard", widget_def)

        widgets = builder.get_widgets("exec_dashboard")
        assert len(widgets) == 2
        assert widgets[0].name == "revenue_chart"
        assert widgets[1].name == "order_gauge"

        # --- Step 5: Export dashboard ---
        exported = builder.export_dashboard("exec_dashboard")
        exported_data = json.loads(exported)
        assert "dashboard" in exported_data
        assert "widgets" in exported_data
        assert len(exported_data["widgets"]) == 2
        assert exported_data["dashboard"]["name"] == "exec_dashboard"

        # --- Step 6: Schedule report ---
        scheduler = ReportScheduler()
        report_def = parsed["reports"][0]
        scheduler.schedule_report(report_def)
        assert len(scheduler.get_scheduled_reports()) == 1

        # --- Step 7: Generate report with mock registry ---
        # The report reads from model_name key in registry
        registry.add("sales_overview", [
            MockEntry("revenue_total", 500.0, now),
            MockEntry("revenue_total", 750.0, now),
        ])

        snapshot = scheduler.generate_report("weekly_sales_report", registry=registry)
        assert snapshot.report_name == "weekly_sales_report"
        assert snapshot.title == "Weekly Sales Summary"
        assert snapshot.hash_value is not None
        assert len(snapshot.hash_value) == 64  # SHA-256 hex

        # --- Step 8: Verify snapshot immutability (frozen dataclass) ---
        with pytest.raises(Exception):
            snapshot.title = "tampered"

    def test_full_pipeline_snapshot_history(self):
        """Multiple report generations phải tạo multiple snapshots trong history."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import ReportScheduler

        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)

        scheduler = ReportScheduler()
        scheduler.schedule_report(parsed["reports"][0])

        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("sales_overview", [
            MockEntry("revenue_total", 100.0, now),
        ])

        # Generate report twice
        snap1 = scheduler.generate_report("weekly_sales_report", registry=registry)
        registry._data["sales_overview"].append(
            MockEntry("revenue_total", 200.0, now)
        )
        snap2 = scheduler.generate_report("weekly_sales_report", registry=registry)

        history = scheduler.get_report_history("weekly_sales_report")
        assert len(history) == 2

        # Snapshots should have different hashes
        assert snap1.hash_value != snap2.hash_value

    def test_full_pipeline_dashboard_refresh_from_registry(self):
        """Dashboard refresh phải lấy dữ liệu mới từ registry."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.dashboard_builder import DashboardBuilder

        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)

        builder = DashboardBuilder()
        dashboard_def = parsed["dashboards"][0]
        builder.create_dashboard(dashboard_def)

        # Add a widget with metric_name "revenue_total"
        widget_def = {
            "name": "revenue_widget",
            "visualization_type": "line_chart",
            "metric_name": "revenue_total",
        }
        builder.add_widget("exec_dashboard", widget_def)

        # Initially, widget data is empty
        widgets = builder.get_widgets("exec_dashboard")
        assert widgets[0].data == []

        # Refresh with registry data
        registry = MockRegistry()
        now = datetime.now(timezone.utc)
        registry.add("revenue_total", [
            MockEntry("revenue_total", 100.0, now),
            MockEntry("revenue_total", 200.0, now),
        ])
        builder.refresh_dashboard("exec_dashboard", registry)

        widgets = builder.get_widgets("exec_dashboard")
        assert len(widgets[0].data) == 2
        assert widgets[0].data[0]["value"] == 100.0

    def test_full_pipeline_engine_stale_check(self):
        """Engine stale check phải hoạt động đúng."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)
        model = parsed["analytics_models"][0]

        engine = AnalyticsEngine()
        engine.register_model(model)

        # Before any query, should be stale
        assert engine.is_stale("sales_overview") is True

        # After query, should not be stale (within max_stale_seconds)
        registry = MockRegistry()
        engine.query("sales_overview", registry=registry)
        assert engine.is_stale("sales_overview") is False

        # Nonexistent model should be stale
        assert engine.is_stale("nonexistent_model") is True

    def test_full_pipeline_model_unregister(self):
        """Unregister model phải xóa model và cache."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import AnalyticsEngine

        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)
        model = parsed["analytics_models"][0]

        engine = AnalyticsEngine()
        engine.register_model(model)
        assert len(engine.get_available_models()) == 1

        # Query to populate cache
        engine.query("sales_overview")
        assert engine.is_stale("sales_overview") is False

        # Unregister
        result = engine.unregister_model("sales_overview")
        assert result is True
        assert len(engine.get_available_models()) == 0
        assert engine.is_stale("sales_overview") is True

        # Unregister again should return False
        result = engine.unregister_model("sales_overview")
        assert result is False

    def test_full_pipeline_dashboard_export_structure(self):
        """Export dashboard JSON phải có cấu trúc đầy đủ."""
        from midicoder.emitters.core.cp17_bi_analytics.parser import AnalyticsParser
        from midicoder.emitters.core.cp17_bi_analytics.dashboard_builder import DashboardBuilder

        parser = AnalyticsParser()
        parsed = parser.parse(FULL_ANALYTICS_DSL)

        builder = DashboardBuilder()
        builder.create_dashboard(parsed["dashboards"][0])

        widget_def = {
            "name": "test_widget",
            "visualization_type": "bar_chart",
            "metric_name": "revenue_total",
            "title": "Revenue Bar Chart",
        }
        builder.add_widget("exec_dashboard", widget_def)

        exported = builder.export_dashboard("exec_dashboard")
        data = json.loads(exported)

        assert "dashboard" in data
        assert "widgets" in data
        assert "last_refresh" in data

        dash = data["dashboard"]
        assert dash["name"] == "exec_dashboard"
        assert dash["title"] == "Executive Sales Dashboard"

        w = data["widgets"][0]
        assert w["name"] == "test_widget"
        assert w["visualization_type"] == "bar_chart"
        assert w["metric_name"] == "revenue_total"
        assert w["title"] == "Revenue Bar Chart"


# ===========================================================================
# Test 7: QueryResult immutability
# ===========================================================================

class TestQueryResultImmutability:
    """Kiểm tra QueryResult là frozen (immutable) — obligation: data freshness."""

    def test_query_result_is_frozen(self):
        """QueryResult không thể sửa đổi sau khi tạo."""
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import QueryResult

        qr = QueryResult(
            model_name="test",
            filters={},
            aggregations={"sum": 100.0},
            row_count=5,
            last_refresh=datetime.now(timezone.utc),
            hash_value="abc123",
        )
        with pytest.raises(Exception):
            qr.row_count = 10

    def test_query_result_to_dict(self):
        """QueryResult.to_dict() phải trả về dict đầy đủ."""
        from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import QueryResult

        qr = QueryResult(
            model_name="test_model",
            filters={"region": "us"},
            aggregations={"sum": 500.0, "count": 10.0},
            row_count=10,
            last_refresh=datetime.now(timezone.utc),
            hash_value="def456",
        )
        d = qr.to_dict()
        assert d["model_name"] == "test_model"
        assert d["filters"] == {"region": "us"}
        assert d["aggregations"] == {"sum": 500.0, "count": 10.0}
        assert d["row_count"] == 10
        assert d["hash_value"] == "def456"
        assert "last_refresh" in d


# ===========================================================================
# Test 8: ReportSnapshot immutability
# ===========================================================================

class TestReportSnapshotImmutability:
    """Kiểm tra ReportSnapshot là frozen — obligation: report immutability."""

    def test_report_snapshot_is_frozen(self):
        """ReportSnapshot không thể sửa đổi sau khi tạo."""
        from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import ReportSnapshot

        snap = ReportSnapshot(
            report_name="test_report",
            title="Test",
            generated_at=datetime.now(timezone.utc),
            data={"metrics": {}},
            hash_value="abc123",
            format="json",
            model_name="test_model",
        )
        # Frozen dataclass: reassigning a field raises FrozenInstanceError
        with pytest.raises(Exception):
            snap.report_name = "tampered_report"

    def test_report_snapshot_to_dict(self):
        """ReportSnapshot.to_dict() phải trả về dict đầy đủ."""
        from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import ReportSnapshot

        snap = ReportSnapshot(
            report_name="weekly_report",
            title="Weekly Summary",
            generated_at=datetime.now(timezone.utc),
            data={"metrics": {"revenue": [100.0]}},
            hash_value="sha256hash",
            format="json",
            model_name="sales_overview",
        )
        d = snap.to_dict()
        assert d["report_name"] == "weekly_report"
        assert d["title"] == "Weekly Summary"
        assert d["hash_value"] == "sha256hash"
        assert d["format"] == "json"
        assert d["model_name"] == "sales_overview"


# ===========================================================================
# Test 9: __init__.py exports
# ===========================================================================

class TestInitExports:
    """Kiểm tra __init__.py export đầy đủ."""

    def test_all_models_exported(self):
        """Tất cả models phải được export."""
        from midicoder.emitters.core.cp17_bi_analytics import (
            AnalyticsModel,
            DashboardDefinition,
            ScheduledReport,
        )
        assert AnalyticsModel is not None
        assert DashboardDefinition is not None
        assert ScheduledReport is not None

    def test_all_enums_exported(self):
        """Tất cả enums phải được export."""
        from midicoder.emitters.core.cp17_bi_analytics import (
            AnalyticsSourceType,
            AggregationType,
            VisualizationType,
            ReportFrequency,
            ReportFormat,
            SchedulePolicy,
        )
        assert AnalyticsSourceType is not None
        assert AggregationType is not None
        assert VisualizationType is not None
        assert ReportFrequency is not None
        assert ReportFormat is not None
        assert SchedulePolicy is not None

    def test_all_emitters_exported(self):
        """Tất cả emitters phải được export."""
        from midicoder.emitters.core.cp17_bi_analytics import (
            FastAPIAnalyticsEmitter,
            NestJSAnalyticsEmitter,
            AngularAnalyticsEmitter,
            ReactAnalyticsEmitter,
        )
        assert FastAPIAnalyticsEmitter is not None
        assert NestJSAnalyticsEmitter is not None
        assert AngularAnalyticsEmitter is not None
        assert ReactAnalyticsEmitter is not None

    def test_engine_exported(self):
        """Tất cả engine classes phải được export."""
        from midicoder.emitters.core.cp17_bi_analytics import (
            AnalyticsEngine,
            QueryResult,
            DashboardBuilder,
            Widget,
            ReportScheduler,
            ReportSnapshot,
        )
        assert AnalyticsEngine is not None
        assert QueryResult is not None
        assert DashboardBuilder is not None
        assert Widget is not None
        assert ReportScheduler is not None
        assert ReportSnapshot is not None

    def test_all_list_complete(self):
        """__all__ phải chứa tất cả exports."""
        from midicoder.emitters.core.cp17_bi_analytics import __all__
        expected = {
            "AnalyticsModel", "DashboardDefinition", "ScheduledReport",
            "AnalyticsSourceType", "AggregationType", "VisualizationType",
            "ReportFrequency", "ReportFormat", "SchedulePolicy",
            "AnalyticsParser",
            "AnalyticsEngine", "QueryResult", "DashboardBuilder", "Widget",
            "ReportScheduler", "ReportSnapshot",
            "FastAPIAnalyticsEmitter", "NestJSAnalyticsEmitter",
            "AngularAnalyticsEmitter", "ReactAnalyticsEmitter",
        }
        actual = set(__all__)
        assert expected.issubset(actual), f"Thiếu exports: {expected - actual}"
