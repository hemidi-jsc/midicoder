# coding: utf-8
"""
Test comprehensive cho CP17 Analytics Runtime Engine.

Kiểm tra toàn bộ 3 runtime modules:
- AnalyticsEngine: Analytics engine (query, aggregation, stale detection)
- DashboardBuilder: Dashboard builder (create, widget, export, refresh)
- ReportScheduler: Report scheduler (schedule, generate, history, next_run)

Và các data classes:
- QueryResult: Immutable query result với SHA-256 hash
- Widget: Dashboard widget definition
- ReportSnapshot: Immutable report snapshot với SHA-256 hash

Author: Midicoder Team
Version: 1.0.0
"""

import json
import unittest
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from midicoder.emitters.core.cp17_bi_analytics.analytics_engine import (
    QueryResult,
    AnalyticsEngine,
)
from midicoder.emitters.core.cp17_bi_analytics.dashboard_builder import (
    Widget,
    DashboardBuilder,
)
from midicoder.emitters.core.cp17_bi_analytics.report_scheduler import (
    ReportSnapshot,
    ReportScheduler,
)
from midicoder.emitters.core.cp17_bi_analytics.models import (
    AnalyticsModel,
    AnalyticsSourceType,
    DashboardDefinition,
    ScheduledReport,
    ReportFormat,
    ReportFrequency,
    SchedulePolicy,
)


# ===========================================================================
# Mock registry — mimics CP15 MetricRegistry for analytics testing
# ===========================================================================


class MockEntry:
    """Mock entry giống MetricEntry từ CP15."""

    def __init__(self, name, value, timestamp):
        self.name = name
        self.value = value
        self.timestamp = timestamp


class MockRegistry:
    """Mock registry để test AnalyticsEngine, DashboardBuilder, ReportScheduler."""

    def __init__(self):
        self._data = {}

    def get(self, name, labels=None):
        """Trả về entries cho metric name.

        Args:
            name: Tên metric
            labels: Labels filter (tùy chọn)

        Returns:
            Danh sách MockEntry hoặc danh sách rỗng
        """
        if name not in self._data:
            return []
        entries = self._data[name]
        if labels:
            return [e for e in entries if labels] if entries else []
        return entries

    def add(self, name, entries):
        """Thêm entries cho một metric name.

        Args:
            name: Tên metric
            entries: Danh sách MockEntry
        """
        self._data[name] = entries


# ===========================================================================
# QueryResult tests
# ===========================================================================


class TestQueryResult(unittest.TestCase):
    """Kiểm tra QueryResult — frozen dataclass, to_dict, immutability."""

    def test_init_all_fields(self):
        """Tạo QueryResult với đầy đủ fields."""
        now = datetime.now(timezone.utc)
        qr = QueryResult(
            model_name="test_model",
            filters={"key": "value"},
            aggregations={"sum": 100.0, "count": 5.0},
            row_count=5,
            last_refresh=now,
            hash_value="abc123",
        )
        self.assertEqual(qr.model_name, "test_model")
        self.assertEqual(qr.filters, {"key": "value"})
        self.assertEqual(qr.aggregations["sum"], 100.0)
        self.assertEqual(qr.row_count, 5)
        self.assertEqual(qr.last_refresh, now)
        self.assertEqual(qr.hash_value, "abc123")

    def test_frozen_immutability(self):
        """QueryResult là frozen — không thể sửa field sau khi tạo."""
        qr = QueryResult(
            model_name="test",
            filters={},
            aggregations={},
            row_count=0,
            last_refresh=datetime.now(timezone.utc),
            hash_value="hash",
        )
        with self.assertRaises(Exception):
            qr.model_name = "changed"

    def test_to_dict(self):
        """QueryResult.to_dict trả về dictionary đầy đủ."""
        now = datetime.now(timezone.utc)
        qr = QueryResult(
            model_name="dict_model",
            filters={"env": "prod"},
            aggregations={"average": 42.5},
            row_count=10,
            last_refresh=now,
            hash_value="sha256hash",
        )
        d = qr.to_dict()
        self.assertEqual(d["model_name"], "dict_model")
        self.assertEqual(d["filters"]["env"], "prod")
        self.assertEqual(d["aggregations"]["average"], 42.5)
        self.assertEqual(d["row_count"], 10)
        self.assertEqual(d["last_refresh"], now.isoformat())
        self.assertEqual(d["hash_value"], "sha256hash")

    def test_to_dict_all_keys_present(self):
        """QueryResult.to_dict có đầy đủ 6 keys."""
        qr = QueryResult(
            model_name="keys",
            filters={},
            aggregations={},
            row_count=0,
            last_refresh=datetime.now(timezone.utc),
            hash_value="h",
        )
        d = qr.to_dict()
        expected_keys = {
            "model_name",
            "filters",
            "aggregations",
            "row_count",
            "last_refresh",
            "hash_value",
        }
        self.assertEqual(set(d.keys()), expected_keys)


# ===========================================================================
# AnalyticsEngine tests
# ===========================================================================


class TestAnalyticsEngine(unittest.TestCase):
    """Kiểm tra AnalyticsEngine — register, query, aggregate, stale."""

    def _make_model(self, name="test_model", stale=300):
        """Helper: tạo AnalyticsModel cho testing."""
        return AnalyticsModel(
            name=name,
            source_type=AnalyticsSourceType.METRIC_REGISTRY,
            metric_names=["metric_a", "metric_b"],
            aggregations=["count"],
            max_stale_seconds=stale,
            description="Test model",
        )

    def test_init(self):
        """Tạo AnalyticsEngine — models và cache đều rỗng."""
        engine = AnalyticsEngine()
        self.assertEqual(len(engine._models), 0)
        self.assertEqual(len(engine._cache), 0)

    def test_register_model(self):
        """Đăng ký analytics model."""
        engine = AnalyticsEngine()
        model = self._make_model("registered")
        engine.register_model(model)
        self.assertIn("registered", engine._models)
        self.assertIs(engine._models["registered"], model)

    def test_register_multiple_models(self):
        """Đăng ký nhiều models."""
        engine = AnalyticsEngine()
        m1 = self._make_model("model_1")
        m2 = self._make_model("model_2")
        engine.register_model(m1)
        engine.register_model(m2)
        self.assertEqual(len(engine._models), 2)

    def test_register_overwrite(self):
        """Đăng ký model cùng tên sẽ ghi đè."""
        engine = AnalyticsEngine()
        m1 = self._make_model("overwrite", stale=100)
        m2 = self._make_model("overwrite", stale=500)
        engine.register_model(m1)
        engine.register_model(m2)
        self.assertEqual(engine._models["overwrite"].max_stale_seconds, 500)

    def test_unregister_model_success(self):
        """Hủy đăng ký model thành công."""
        engine = AnalyticsEngine()
        model = self._make_model("to_unregister")
        engine.register_model(model)
        result = engine.unregister_model("to_unregister")
        self.assertTrue(result)
        self.assertNotIn("to_unregister", engine._models)

    def test_unregister_model_not_found(self):
        """Hủy đăng ký model không tồn tại trả về False."""
        engine = AnalyticsEngine()
        result = engine.unregister_model("nonexistent")
        self.assertFalse(result)

    def test_unregister_clears_cache(self):
        """Hủy đăng ký model xóa cache liên quan."""
        engine = AnalyticsEngine()
        model = self._make_model("clear_cache")
        engine.register_model(model)
        engine._cache["clear_cache"] = QueryResult(
            model_name="clear_cache",
            filters={},
            aggregations={},
            row_count=0,
            last_refresh=datetime.now(timezone.utc),
            hash_value="old_hash",
        )
        engine.unregister_model("clear_cache")
        self.assertNotIn("clear_cache", engine._cache)

    def test_query_model_not_found(self):
        """Query model không tồn tại raise KeyError."""
        engine = AnalyticsEngine()
        with self.assertRaises(KeyError):
            engine.query("nonexistent")

    def test_query_without_registry(self):
        """Query không có registry trả về kết quả rỗng."""
        engine = AnalyticsEngine()
        model = self._make_model("no_reg")
        engine.register_model(model)
        result = engine.query("no_reg")
        self.assertEqual(result.model_name, "no_reg")
        self.assertEqual(result.row_count, 0)
        # Default aggregation là count → 0.0
        self.assertEqual(result.aggregations["count"], 0.0)

    def test_query_with_registry(self):
        """Query với registry đọc đúng metric data."""
        engine = AnalyticsEngine()
        model = AnalyticsModel(
            name="with_reg",
            metric_names=["latency"],
            aggregations=["sum", "count"],
        )
        engine.register_model(model)

        registry = MockRegistry()
        registry.add("latency", [
            MockEntry("latency", 10.0, datetime.now(timezone.utc)),
            MockEntry("latency", 20.0, datetime.now(timezone.utc)),
            MockEntry("latency", 30.0, datetime.now(timezone.utc)),
        ])

        result = engine.query("with_reg", registry=registry)
        self.assertEqual(result.row_count, 3)
        self.assertEqual(result.aggregations["sum"], 60.0)
        self.assertEqual(result.aggregations["count"], 3.0)

    def test_query_with_filters(self):
        """Query với filters."""
        engine = AnalyticsEngine()
        model = self._make_model("filtered")
        engine.register_model(model)
        result = engine.query("filtered", filters={"env": "prod"})
        self.assertEqual(result.filters, {"env": "prod"})

    def test_query_with_custom_aggregations(self):
        """Query với custom aggregation types."""
        engine = AnalyticsEngine()
        model = self._make_model("agg_test")
        engine.register_model(model)

        registry = MockRegistry()
        registry.add("metric_a", [
            MockEntry("metric_a", 5.0, datetime.now(timezone.utc)),
            MockEntry("metric_a", 15.0, datetime.now(timezone.utc)),
        ])

        result = engine.query(
            "agg_test",
            aggregations=["sum", "average", "max", "min"],
            registry=registry,
        )
        self.assertEqual(result.aggregations["sum"], 20.0)
        self.assertEqual(result.aggregations["average"], 10.0)
        self.assertEqual(result.aggregations["max"], 15.0)
        self.assertEqual(result.aggregations["min"], 5.0)

    def test_query_caches_result(self):
        """Query lưu kết quả vào cache."""
        engine = AnalyticsEngine()
        model = self._make_model("cached")
        engine.register_model(model)
        engine.query("cached")
        self.assertIn("cached", engine._cache)

    def test_query_has_hash(self):
        """Query result có SHA-256 hash hợp lệ."""
        engine = AnalyticsEngine()
        model = self._make_model("hash_test")
        engine.register_model(model)
        result = engine.query("hash_test")
        self.assertEqual(len(result.hash_value), 64)  # SHA-256 hex length
        int(result.hash_value, 16)  # Không raise → hợp lệ hex

    def test_aggregate_sum(self):
        """Aggregation sum trả về tổng."""
        engine = AnalyticsEngine()
        result = engine._aggregate([1.0, 2.0, 3.0], "sum")
        self.assertEqual(result, 6.0)

    def test_aggregate_average(self):
        """Aggregation average trả về trung bình."""
        engine = AnalyticsEngine()
        result = engine._aggregate([10.0, 20.0, 30.0], "average")
        self.assertEqual(result, 20.0)

    def test_aggregate_count(self):
        """Aggregation count trả về số lượng."""
        engine = AnalyticsEngine()
        result = engine._aggregate([1, 2, 3, 4, 5], "count")
        self.assertEqual(result, 5.0)

    def test_aggregate_max(self):
        """Aggregation max trả về giá trị lớn nhất."""
        engine = AnalyticsEngine()
        result = engine._aggregate([5.0, 15.0, 3.0, 25.0], "max")
        self.assertEqual(result, 25.0)

    def test_aggregate_min(self):
        """Aggregation min trả về giá trị nhỏ nhất."""
        engine = AnalyticsEngine()
        result = engine._aggregate([5.0, 15.0, 3.0, 25.0], "min")
        self.assertEqual(result, 3.0)

    def test_aggregate_unknown_type(self):
        """Aggregation loại không xác định trả về count mặc định."""
        engine = AnalyticsEngine()
        result = engine._aggregate([1, 2, 3], "unknown_type")
        self.assertEqual(result, 3.0)

    def test_aggregate_empty_values(self):
        """Aggregation với values rỗng trả về 0.0."""
        engine = AnalyticsEngine()
        for agg_type in ["sum", "average", "count", "max", "min", "unknown"]:
            self.assertEqual(engine._aggregate([], agg_type), 0.0)

    def test_get_available_models(self):
        """get_available_models trả về danh sách models."""
        engine = AnalyticsEngine()
        m1 = self._make_model("model_a")
        m2 = self._make_model("model_b")
        engine.register_model(m1)
        engine.register_model(m2)
        models = engine.get_available_models()
        self.assertEqual(len(models), 2)
        names = {m.name for m in models}
        self.assertIn("model_a", names)
        self.assertIn("model_b", names)

    def test_get_available_models_empty(self):
        """get_available_models khi không có model trả về danh sách rỗng."""
        engine = AnalyticsEngine()
        self.assertEqual(len(engine.get_available_models()), 0)

    def test_is_stale_no_model(self):
        """is_stale trả về True khi model không tồn tại."""
        engine = AnalyticsEngine()
        self.assertTrue(engine.is_stale("nonexistent"))

    def test_is_stale_no_cache(self):
        """is_stale trả về True khi model tồn tại nhưng không có cache."""
        engine = AnalyticsEngine()
        engine.register_model(self._make_model("no_cache"))
        self.assertTrue(engine.is_stale("no_cache"))

    def test_is_stale_not_stale(self):
        """is_stale trả về False khi kết quả còn tươi."""
        engine = AnalyticsEngine()
        model = self._make_model("fresh", stale=300)
        engine.register_model(model)
        engine.query("fresh")
        self.assertFalse(engine.is_stale("fresh"))

    def test_is_stale_expired(self):
        """is_stale trả về True khi kết quả quá thời gian stale."""
        engine = AnalyticsEngine()
        # max_stale_seconds = 0.001 giây
        model = AnalyticsModel(
            name="expired",
            max_stale_seconds=1,
        )
        engine.register_model(model)
        # Tạo cache entry với last_refresh trong quá khứ
        old_time = datetime.now(timezone.utc) - timedelta(hours=1)
        engine._cache["expired"] = QueryResult(
            model_name="expired",
            filters={},
            aggregations={},
            row_count=0,
            last_refresh=old_time,
            hash_value="old",
        )
        self.assertTrue(engine.is_stale("expired"))


# ===========================================================================
# Widget tests
# ===========================================================================


class TestWidget(unittest.TestCase):
    """Kiểm tra Widget — dataclass, to_dict."""

    def test_init_defaults(self):
        """Tạo Widget với giá trị mặc định."""
        w = Widget(
            name="widget_1",
            visualization_type="line_chart",
            metric_name="latency",
        )
        self.assertEqual(w.name, "widget_1")
        self.assertEqual(w.visualization_type, "line_chart")
        self.assertEqual(w.metric_name, "latency")
        self.assertEqual(w.title, "")
        self.assertEqual(w.data, [])

    def test_init_all_fields(self):
        """Tạo Widget với đầy đủ fields."""
        w = Widget(
            name="full_widget",
            visualization_type="bar_chart",
            metric_name="requests",
            title="Request Count",
            data=[{"value": 10, "timestamp": "2026-01-01"}],
        )
        self.assertEqual(w.title, "Request Count")
        self.assertEqual(len(w.data), 1)
        self.assertEqual(w.data[0]["value"], 10)

    def test_to_dict(self):
        """Widget.to_dict trả về dictionary đầy đủ."""
        w = Widget(
            name="dict_widget",
            visualization_type="pie_chart",
            metric_name="errors",
            title="Error Rate",
            data=[{"value": 5}],
        )
        d = w.to_dict()
        self.assertEqual(d["name"], "dict_widget")
        self.assertEqual(d["visualization_type"], "pie_chart")
        self.assertEqual(d["metric_name"], "errors")
        self.assertEqual(d["title"], "Error Rate")
        self.assertEqual(d["data"], [{"value": 5}])

    def test_to_dict_all_keys(self):
        """Widget.to_dict có đầy đủ 5 keys."""
        w = Widget(
            name="keys",
            visualization_type="gauge",
            metric_name="cpu",
        )
        d = w.to_dict()
        expected_keys = {"name", "visualization_type", "metric_name", "title", "data"}
        self.assertEqual(set(d.keys()), expected_keys)


# ===========================================================================
# DashboardBuilder tests
# ===========================================================================


class TestDashboardBuilder(unittest.TestCase):
    """Kiểm tra DashboardBuilder — create, widget, export, refresh."""

    def _make_definition(self, name="test_dashboard", title="Test"):
        """Helper: tạo DashboardDefinition cho testing."""
        return DashboardDefinition(
            name=name,
            title=title,
            description="Test dashboard",
            refresh_interval_seconds=30,
        )

    def test_init(self):
        """Tạo DashboardBuilder — dashboards và widgets đều rỗng."""
        builder = DashboardBuilder()
        self.assertEqual(len(builder._dashboards), 0)
        self.assertEqual(len(builder._widgets), 0)
        self.assertEqual(len(builder._refresh_times), 0)

    def test_create_dashboard(self):
        """Tạo dashboard và trả về definition."""
        builder = DashboardBuilder()
        definition = self._make_definition("created")
        result = builder.create_dashboard(definition)
        self.assertIs(result, definition)
        self.assertIn("created", builder._dashboards)
        self.assertEqual(len(builder._widgets["created"]), 0)

    def test_create_multiple_dashboards(self):
        """Tạo nhiều dashboards."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("dash_1"))
        builder.create_dashboard(self._make_definition("dash_2"))
        self.assertEqual(len(builder._dashboards), 2)

    def test_add_widget(self):
        """Thêm widget vào dashboard."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("with_widget"))
        widget_def = {
            "name": "w1",
            "visualization_type": "line_chart",
            "metric_name": "latency",
            "title": "Latency Trend",
        }
        widget = builder.add_widget("with_widget", widget_def)
        self.assertIsInstance(widget, Widget)
        self.assertEqual(widget.name, "w1")
        self.assertEqual(len(builder._widgets["with_widget"]), 1)

    def test_add_widget_defaults(self):
        """Thêm widget với giá trị mặc định cho title và data."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("default_w"))
        widget_def = {
            "name": "w2",
            "visualization_type": "bar",
            "metric_name": "count",
        }
        widget = builder.add_widget("default_w", widget_def)
        self.assertEqual(widget.title, "")
        self.assertEqual(widget.data, [])

    def test_add_widget_to_nonexistent_dashboard(self):
        """Thêm widget vào dashboard không tồn tại raise KeyError."""
        builder = DashboardBuilder()
        with self.assertRaises(KeyError):
            builder.add_widget("nonexistent", {
                "name": "w",
                "visualization_type": "line",
                "metric_name": "m",
            })

    def test_add_multiple_widgets(self):
        """Thêm nhiều widgets vào cùng dashboard."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("multi"))
        builder.add_widget("multi", {
            "name": "w1", "visualization_type": "line", "metric_name": "m1",
        })
        builder.add_widget("multi", {
            "name": "w2", "visualization_type": "bar", "metric_name": "m2",
        })
        self.assertEqual(len(builder._widgets["multi"]), 2)

    def test_get_dashboard_found(self):
        """get_dashboard tìm thấy dashboard."""
        builder = DashboardBuilder()
        defn = self._make_definition("found")
        builder.create_dashboard(defn)
        result = builder.get_dashboard("found")
        self.assertIs(result, defn)

    def test_get_dashboard_not_found(self):
        """get_dashboard không tìm thấy trả về None."""
        builder = DashboardBuilder()
        result = builder.get_dashboard("nonexistent")
        self.assertIsNone(result)

    def test_list_dashboards(self):
        """list_dashboards trả về tất cả dashboards."""
        builder = DashboardBuilder()
        d1 = self._make_definition("list_1")
        d2 = self._make_definition("list_2")
        builder.create_dashboard(d1)
        builder.create_dashboard(d2)
        dashboards = builder.list_dashboards()
        self.assertEqual(len(dashboards), 2)
        names = {d.name for d in dashboards}
        self.assertIn("list_1", names)
        self.assertIn("list_2", names)

    def test_list_dashboards_empty(self):
        """list_dashboards khi không có dashboard trả về danh sách rỗng."""
        builder = DashboardBuilder()
        self.assertEqual(len(builder.list_dashboards()), 0)

    def test_export_dashboard(self):
        """Export dashboard trả về JSON hợp lệ."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("export_test"))
        builder.add_widget("export_test", {
            "name": "w1",
            "visualization_type": "line",
            "metric_name": "latency",
            "title": "Latency",
        })
        json_str = builder.export_dashboard("export_test")
        data = json.loads(json_str)
        self.assertIn("dashboard", data)
        self.assertIn("widgets", data)
        self.assertIn("last_refresh", data)
        self.assertEqual(data["dashboard"]["name"], "export_test")
        self.assertEqual(len(data["widgets"]), 1)
        self.assertEqual(data["widgets"][0]["name"], "w1")

    def test_export_dashboard_no_widgets(self):
        """Export dashboard không có widgets."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("no_w"))
        json_str = builder.export_dashboard("no_w")
        data = json.loads(json_str)
        self.assertEqual(len(data["widgets"]), 0)

    def test_export_dashboard_not_found(self):
        """Export dashboard không tồn tại raise KeyError."""
        builder = DashboardBuilder()
        with self.assertRaises(KeyError):
            builder.export_dashboard("nonexistent")

    def test_refresh_dashboard(self):
        """Refresh dashboard với mock registry."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("refresh_test"))
        builder.add_widget("refresh_test", {
            "name": "w1",
            "visualization_type": "line",
            "metric_name": "cpu_usage",
        })

        registry = MockRegistry()
        registry.add("cpu_usage", [
            MockEntry("cpu_usage", 45.0, datetime.now(timezone.utc)),
            MockEntry("cpu_usage", 55.0, datetime.now(timezone.utc)),
        ])

        builder.refresh_dashboard("refresh_test", registry)
        widgets = builder._widgets["refresh_test"]
        self.assertEqual(len(widgets[0].data), 2)
        self.assertEqual(widgets[0].data[0]["value"], 45.0)
        self.assertEqual(widgets[0].data[1]["value"], 55.0)

    def test_refresh_dashboard_empty_registry(self):
        """Refresh dashboard khi registry không có data."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("empty_reg"))
        builder.add_widget("empty_reg", {
            "name": "w1",
            "visualization_type": "line",
            "metric_name": "no_data",
        })

        registry = MockRegistry()
        builder.refresh_dashboard("empty_reg", registry)
        widgets = builder._widgets["empty_reg"]
        self.assertEqual(widgets[0].data, [])

    def test_refresh_dashboard_not_found(self):
        """Refresh dashboard không tồn tại raise KeyError."""
        builder = DashboardBuilder()
        registry = MockRegistry()
        with self.assertRaises(KeyError):
            builder.refresh_dashboard("nonexistent", registry)

    def test_refresh_updates_time(self):
        """Refresh cập nhật thời gian refresh."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("time_test"))
        registry = MockRegistry()
        before = datetime.now(timezone.utc)
        builder.refresh_dashboard("time_test", registry)
        after = datetime.now(timezone.utc)
        refresh_time = builder._refresh_times["time_test"]
        self.assertGreaterEqual(refresh_time, before - timedelta(seconds=1))
        self.assertLessEqual(refresh_time, after + timedelta(seconds=1))

    def test_get_widgets(self):
        """get_widgets trả về danh sách widgets của dashboard."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("get_w"))
        builder.add_widget("get_w", {
            "name": "w1", "visualization_type": "line", "metric_name": "m1",
        })
        widgets = builder.get_widgets("get_w")
        self.assertEqual(len(widgets), 1)
        self.assertEqual(widgets[0].name, "w1")

    def test_get_widgets_empty(self):
        """get_widgets khi dashboard không có widget trả về danh sách rỗng."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("empty_w"))
        widgets = builder.get_widgets("empty_w")
        self.assertEqual(len(widgets), 0)

    def test_get_widgets_nonexistent(self):
        """get_widgets dashboard không tồn tại trả về danh sách rỗng."""
        builder = DashboardBuilder()
        widgets = builder.get_widgets("nonexistent")
        self.assertEqual(len(widgets), 0)

    def test_export_json_format(self):
        """Export dashboard JSON có indent=2."""
        builder = DashboardBuilder()
        builder.create_dashboard(self._make_definition("fmt"))
        json_str = builder.export_dashboard("fmt")
        # Kiểm tra có indent (newline + spaces)
        self.assertIn("\n", json_str)
        self.assertIn("  ", json_str)


# ===========================================================================
# ReportSnapshot tests
# ===========================================================================


class TestReportSnapshot(unittest.TestCase):
    """Kiểm tra ReportSnapshot — frozen dataclass, to_dict, immutability."""

    def _make_snapshot(self):
        """Helper: tạo ReportSnapshot cho testing."""
        return ReportSnapshot(
            report_name="test_report",
            title="Test Report",
            generated_at=datetime.now(timezone.utc),
            data={"key": "value"},
            hash_value="sha256hash123",
            format="json",
            model_name="analytics_model",
        )

    def test_init_all_fields(self):
        """Tạo ReportSnapshot với đầy đủ fields."""
        snap = self._make_snapshot()
        self.assertEqual(snap.report_name, "test_report")
        self.assertEqual(snap.title, "Test Report")
        self.assertIsInstance(snap.generated_at, datetime)
        self.assertEqual(snap.data["key"], "value")
        self.assertEqual(snap.hash_value, "sha256hash123")
        self.assertEqual(snap.format, "json")
        self.assertEqual(snap.model_name, "analytics_model")

    def test_frozen_immutability(self):
        """ReportSnapshot là frozen — không thể sửa field sau khi tạo."""
        snap = self._make_snapshot()
        with self.assertRaises(Exception):
            snap.report_name = "changed"

    def test_to_dict(self):
        """ReportSnapshot.to_dict trả về dictionary đầy đủ."""
        now = datetime.now(timezone.utc)
        snap = ReportSnapshot(
            report_name="dict_report",
            title="Dict Report",
            generated_at=now,
            data={"metrics": {"cpu": [1, 2, 3]}},
            hash_value="dict_hash",
            format="csv",
            model_name="model_x",
        )
        d = snap.to_dict()
        self.assertEqual(d["report_name"], "dict_report")
        self.assertEqual(d["title"], "Dict Report")
        self.assertEqual(d["generated_at"], now.isoformat())
        self.assertEqual(d["data"]["metrics"]["cpu"], [1, 2, 3])
        self.assertEqual(d["hash_value"], "dict_hash")
        self.assertEqual(d["format"], "csv")
        self.assertEqual(d["model_name"], "model_x")

    def test_to_dict_all_keys(self):
        """ReportSnapshot.to_dict có đầy đủ 7 keys."""
        snap = self._make_snapshot()
        d = snap.to_dict()
        expected_keys = {
            "report_name",
            "title",
            "generated_at",
            "data",
            "hash_value",
            "format",
            "model_name",
        }
        self.assertEqual(set(d.keys()), expected_keys)


# ===========================================================================
# ReportScheduler tests
# ===========================================================================


class TestReportScheduler(unittest.TestCase):
    """Kiểm tra ReportScheduler — schedule, generate, history, next_run."""

    def _make_report(self, name="test_report", policy=SchedulePolicy.ONCE):
        """Helper: tạo ScheduledReport cho testing."""
        return ScheduledReport(
            name=name,
            title="Test Report",
            model_name="analytics_model",
            schedule_policy=policy,
            format=ReportFormat.JSON,
            parameters={"param1": "value1"},
        )

    def test_init(self):
        """Tạo ReportScheduler — reports và snapshots đều rỗng."""
        scheduler = ReportScheduler()
        self.assertEqual(len(scheduler._reports), 0)
        self.assertEqual(len(scheduler._snapshots), 0)

    def test_schedule_report(self):
        """Lập lịch report."""
        scheduler = ReportScheduler()
        report = self._make_report("scheduled")
        scheduler.schedule_report(report)
        self.assertIn("scheduled", scheduler._reports)
        self.assertIn("scheduled", scheduler._snapshots)
        self.assertEqual(len(scheduler._snapshots["scheduled"]), 0)

    def test_schedule_report_does_not_overwrite_snapshots(self):
        """Lập lịch report không ghi đè snapshots đã tồn tại."""
        scheduler = ReportScheduler()
        report = self._make_report("keep_snap")
        scheduler.schedule_report(report)
        # Thêm snapshot giả
        scheduler._snapshots["keep_snap"].append("existing")
        # Schedule lại
        scheduler.schedule_report(report)
        self.assertEqual(len(scheduler._snapshots["keep_snap"]), 1)

    def test_generate_report_not_found(self):
        """Generate report không tồn tại raise KeyError."""
        scheduler = ReportScheduler()
        with self.assertRaises(KeyError):
            scheduler.generate_report("nonexistent")

    def test_generate_report_without_registry(self):
        """Generate report không có registry dùng data rỗng."""
        scheduler = ReportScheduler()
        report = self._make_report("no_reg")
        scheduler.schedule_report(report)
        snapshot = scheduler.generate_report("no_reg")
        self.assertIsInstance(snapshot, ReportSnapshot)
        self.assertEqual(snapshot.report_name, "no_reg")
        self.assertEqual(snapshot.format, "json")
        self.assertEqual(snapshot.model_name, "analytics_model")
        # Data có cấu trúc nhưng metrics rỗng
        self.assertIn("metrics", snapshot.data)
        self.assertEqual(snapshot.data["metrics"], {})

    def test_generate_report_with_registry(self):
        """Generate report với registry đọc metric data."""
        scheduler = ReportScheduler()
        report = ScheduledReport(
            name="with_reg",
            model_name="latency",
            format=ReportFormat.CSV,
        )
        scheduler.schedule_report(report)

        registry = MockRegistry()
        registry.add("latency", [
            MockEntry("latency", 10.0, datetime.now(timezone.utc)),
            MockEntry("latency", 20.0, datetime.now(timezone.utc)),
        ])

        snapshot = scheduler.generate_report("with_reg", registry=registry)
        self.assertEqual(snapshot.format, "csv")
        self.assertIn("latency", snapshot.data["metrics"])
        self.assertEqual(len(snapshot.data["metrics"]["latency"]), 2)

    def test_generate_report_creates_snapshot(self):
        """Generate report lưu snapshot vào history."""
        scheduler = ReportScheduler()
        report = self._make_report("history")
        scheduler.schedule_report(report)
        scheduler.generate_report("history")
        history = scheduler.get_report_history("history")
        self.assertEqual(len(history), 1)

    def test_generate_report_multiple_snapshots(self):
        """Generate report nhiều lần tạo nhiều snapshots."""
        scheduler = ReportScheduler()
        report = self._make_report("multi_gen")
        scheduler.schedule_report(report)
        scheduler.generate_report("multi_gen")
        scheduler.generate_report("multi_gen")
        history = scheduler.get_report_history("multi_gen")
        self.assertEqual(len(history), 2)

    def test_generate_report_hash_uniqueness(self):
        """Mỗi snapshot có hash SHA-256 duy nhất."""
        scheduler = ReportScheduler()
        report = self._make_report("unique_hash")
        scheduler.schedule_report(report)
        s1 = scheduler.generate_report("unique_hash")
        s2 = scheduler.generate_report("unique_hash")
        # Hash khác nhau vì generated_at khác nhau
        self.assertNotEqual(s1.hash_value, s2.hash_value)

    def test_compute_hash_format(self):
        """_compute_hash trả về SHA-256 hex string 64 ký tự."""
        scheduler = ReportScheduler()
        now = datetime.now(timezone.utc)
        h = scheduler._compute_hash("test", {"key": "val"}, now)
        self.assertEqual(len(h), 64)
        int(h, 16)  # Không raise → hợp lệ hex

    def test_get_scheduled_reports(self):
        """get_scheduled_reports trả về danh sách reports."""
        scheduler = ReportScheduler()
        r1 = self._make_report("sched_1")
        r2 = self._make_report("sched_2")
        scheduler.schedule_report(r1)
        scheduler.schedule_report(r2)
        reports = scheduler.get_scheduled_reports()
        self.assertEqual(len(reports), 2)
        names = {r.name for r in reports}
        self.assertIn("sched_1", names)
        self.assertIn("sched_2", names)

    def test_get_scheduled_reports_empty(self):
        """get_scheduled_reports khi không có report trả về danh sách rỗng."""
        scheduler = ReportScheduler()
        self.assertEqual(len(scheduler.get_scheduled_reports()), 0)

    def test_execute_due_reports(self):
        """execute_due_reports chạy các reports đến hạn."""
        scheduler = ReportScheduler()
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        report = ScheduledReport(
            name="due_report",
            model_name="model",
            next_run=past,
            schedule_policy=SchedulePolicy.HOURLY,
        )
        scheduler.schedule_report(report)
        snapshots = scheduler.execute_due_reports()
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].report_name, "due_report")

    def test_execute_due_reports_no_due(self):
        """execute_due_reports khi không có report đến hạn."""
        scheduler = ReportScheduler()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        report = ScheduledReport(
            name="not_due",
            model_name="model",
            next_run=future,
            schedule_policy=SchedulePolicy.HOURLY,
        )
        scheduler.schedule_report(report)
        snapshots = scheduler.execute_due_reports()
        self.assertEqual(len(snapshots), 0)

    def test_execute_due_reports_with_registry(self):
        """execute_due_reports với registry."""
        scheduler = ReportScheduler()
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        report = ScheduledReport(
            name="due_with_reg",
            model_name="metric_x",
            next_run=past,
        )
        scheduler.schedule_report(report)
        registry = MockRegistry()
        registry.add("metric_x", [
            MockEntry("metric_x", 42.0, datetime.now(timezone.utc)),
        ])
        snapshots = scheduler.execute_due_reports(registry)
        self.assertEqual(len(snapshots), 1)

    def test_get_report_history(self):
        """get_report_history trả về danh sách snapshots."""
        scheduler = ReportScheduler()
        report = self._make_report("hist")
        scheduler.schedule_report(report)
        scheduler.generate_report("hist")
        scheduler.generate_report("hist")
        history = scheduler.get_report_history("hist")
        self.assertEqual(len(history), 2)

    def test_get_report_history_nonexistent(self):
        """get_report_history report không tồn tại trả về danh sách rỗng."""
        scheduler = ReportScheduler()
        history = scheduler.get_report_history("nonexistent")
        self.assertEqual(len(history), 0)

    def test_unregister_report_success(self):
        """Hủy đăng ký report thành công."""
        scheduler = ReportScheduler()
        report = self._make_report("to_unregister")
        scheduler.schedule_report(report)
        scheduler.generate_report("to_unregister")
        result = scheduler.unregister_report("to_unregister")
        self.assertTrue(result)
        self.assertNotIn("to_unregister", scheduler._reports)
        self.assertNotIn("to_unregister", scheduler._snapshots)

    def test_unregister_report_not_found(self):
        """Hủy đăng ký report không tồn tại trả về False."""
        scheduler = ReportScheduler()
        result = scheduler.unregister_report("nonexistent")
        self.assertFalse(result)

    def test_update_next_run_once(self):
        """_update_next_run với policy ONCE đặt next_run rất xa."""
        scheduler = ReportScheduler()
        report = self._make_report("once_report", policy=SchedulePolicy.ONCE)
        old_next = report.next_run
        scheduler._update_next_run(report)
        self.assertEqual(report.next_run.year, 2999)

    def test_update_next_run_hourly(self):
        """_update_next_run với policy HOURLY thêm 1 giờ."""
        scheduler = ReportScheduler()
        now = datetime.now(timezone.utc)
        report = ScheduledReport(
            name="hourly",
            next_run=now,
            schedule_policy=SchedulePolicy.HOURLY,
        )
        scheduler._update_next_run(report)
        expected = now + timedelta(hours=1)
        # So sánh với dung sai 1 giây (vì datetime.now có thể drift)
        diff = abs((report.next_run - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_update_next_run_daily(self):
        """_update_next_run với policy DAILY thêm 1 ngày."""
        scheduler = ReportScheduler()
        now = datetime.now(timezone.utc)
        report = ScheduledReport(
            name="daily",
            next_run=now,
            schedule_policy=SchedulePolicy.DAILY,
        )
        scheduler._update_next_run(report)
        expected = now + timedelta(days=1)
        diff = abs((report.next_run - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_update_next_run_weekly(self):
        """_update_next_run với policy WEEKLY thêm 1 tuần."""
        scheduler = ReportScheduler()
        now = datetime.now(timezone.utc)
        report = ScheduledReport(
            name="weekly",
            next_run=now,
            schedule_policy=SchedulePolicy.WEEKLY,
        )
        scheduler._update_next_run(report)
        expected = now + timedelta(weeks=1)
        diff = abs((report.next_run - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_update_next_run_monthly(self):
        """_update_next_run với policy MONTHLY thêm ~30 ngày."""
        scheduler = ReportScheduler()
        now = datetime.now(timezone.utc)
        report = ScheduledReport(
            name="monthly",
            next_run=now,
            schedule_policy=SchedulePolicy.MONTHLY,
        )
        scheduler._update_next_run(report)
        expected = now + timedelta(days=30)
        diff = abs((report.next_run - expected).total_seconds())
        self.assertLess(diff, 2)

    def test_update_next_run_none_next_run(self):
        """_update_next_run với next_run là None dùng datetime.now."""
        scheduler = ReportScheduler()
        report = ScheduledReport(
            name="none_next",
            next_run=None,
            schedule_policy=SchedulePolicy.DAILY,
        )
        # next_run=None sẽ được __post_init__ gán = now
        # Nhưng test trường hợp next_run vẫn là None sau khi tạo
        object.__setattr__(report, "next_run", None)
        scheduler._update_next_run(report)
        self.assertIsNotNone(report.next_run)

    def test_report_snapshot_hash_length(self):
        """ReportSnapshot hash_value là SHA-256 (64 hex chars)."""
        scheduler = ReportScheduler()
        report = self._make_report("hash_len")
        scheduler.schedule_report(report)
        snap = scheduler.generate_report("hash_len")
        self.assertEqual(len(snap.hash_value), 64)

    def test_report_data_structure(self):
        """Report data có cấu trúc model_name, parameters, metrics."""
        scheduler = ReportScheduler()
        report = ScheduledReport(
            name="data_struct",
            model_name="my_model",
            parameters={"env": "prod"},
        )
        scheduler.schedule_report(report)
        snap = scheduler.generate_report("data_struct")
        self.assertEqual(snap.data["model_name"], "my_model")
        self.assertEqual(snap.data["parameters"]["env"], "prod")
        self.assertIn("metrics", snap.data)


# ===========================================================================
# Entry point
# ===========================================================================


if __name__ == "__main__":
    unittest.main()
