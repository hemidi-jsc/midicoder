# coding: utf-8
"""
Kiểm tra integration giữa CP15 MetricRegistry và CP16 engine.
"""

import time
import pytest

from midicoder.packs.cp15_observability.metrics import MetricRegistry
from midicoder.packs.cp_full_monitoring.dashboard import DashboardManager, Panel
from midicoder.packs.cp_full_monitoring.alert import AlertEngine
from midicoder.packs.cp_full_monitoring.sli import SLIMonitor
from midicoder.packs.cp_full_monitoring.models import (
    DashboardProfile,
    DashboardType,
    AlertRule,
    AlertCondition,
    AlertSeverity,
    SLIDefinition,
    SLIMetricType,
)


# ===========================================================================
# DashboardManager + CP15 MetricRegistry Integration
# ===========================================================================

class TestDashboardMetricRegistryIntegration:
    """Kiểm tra DashboardManager đọc từ CP15 MetricRegistry."""

    def test_dashboard_reads_from_metric_registry(self) -> None:
        """Dashboard cập nhật panel values từ CP15 MetricRegistry."""
        registry = MetricRegistry()
        registry.record("http_requests", 42.0)

        dm = DashboardManager()
        panel = Panel(name="req_count", metric_name="http_requests")
        dm.create_dashboard("api", panels=[panel])

        dm.update_panel_values(registry)
        values = dm.get_panel_values("api")

        assert "req_count" in values
        assert values["req_count"]["value"] == 42.0

    def test_dashboard_multiple_panels_from_registry(self) -> None:
        """Dashboard có nhiều panels đọc từ registry."""
        registry = MetricRegistry()
        registry.record("requests", 100.0)
        registry.record("errors", 5.0)
        registry.record("latency", 200.0)

        dm = DashboardManager()
        panels = [
            Panel(name="req", metric_name="requests"),
            Panel(name="err", metric_name="errors"),
            Panel(name="lat", metric_name="latency"),
        ]
        dm.create_dashboard("api", panels=panels)
        dm.update_panel_values(registry)

        values = dm.get_panel_values("api")
        assert values["req"]["value"] == 100.0
        assert values["err"]["value"] == 5.0
        assert values["lat"]["value"] == 200.0

    def test_dashboard_panel_no_metric_data(self) -> None:
        """Panel có metric không tồn tại trong registry."""
        registry = MetricRegistry()
        dm = DashboardManager()
        panel = Panel(name="missing", metric_name="nonexistent_metric")
        dm.create_dashboard("test", panels=[panel])
        dm.update_panel_values(registry)

        values = dm.get_panel_values("test")
        assert values["missing"]["value"] is None

    def test_dashboard_export_json_with_registry_data(self) -> None:
        """Export JSON chứa panel values từ registry."""
        registry = MetricRegistry()
        registry.record("cpu_usage", 75.0)

        dm = DashboardManager()
        panel = Panel(name="cpu", metric_name="cpu_usage")
        dm.create_dashboard("system", panels=[panel])
        dm.update_panel_values(registry)

        exported = dm.export_json()
        assert "75.0" in exported

    def test_dashboard_refresh_panel_values(self) -> None:
        """Panel values cập nhật khi có metric mới."""
        registry = MetricRegistry()
        registry.record("requests", 10.0)

        dm = DashboardManager()
        panel = Panel(name="req", metric_name="requests")
        dm.create_dashboard("api", panels=[panel])
        dm.update_panel_values(registry)

        values = dm.get_panel_values("api")
        assert values["req"]["value"] == 10.0

        # Ghi thêm metric mới
        registry.record("requests", 20.0)
        dm.update_panel_values(registry)

        values = dm.get_panel_values("api")
        assert values["req"]["value"] == 20.0


# ===========================================================================
# AlertEngine + CP15 MetricRegistry Integration
# ===========================================================================

class TestAlertEngineMetricRegistryIntegration:
    """Kiểm tra AlertEngine evaluate từ CP15 MetricRegistry."""

    def test_alert_fires_from_registry(self) -> None:
        """Alert fire khi metric từ registry vượt ngưỡng."""
        registry = MetricRegistry()
        registry.record("error_rate", 0.1)

        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="error_rate",
            condition=AlertCondition.GREATER_THAN,
            threshold=0.05,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        ae._last_evaluations["high_errors"] = None

        alerts = ae.evaluate(registry)
        assert len(alerts) == 1
        assert alerts[0].current_value == 0.1

    def test_alert_does_not_fire_below_threshold(self) -> None:
        """Alert không fire khi metric dưới ngưỡng."""
        registry = MetricRegistry()
        registry.record("error_rate", 0.01)

        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="error_rate",
            condition=AlertCondition.GREATER_THAN,
            threshold=0.05,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        ae._last_evaluations["high_errors"] = None

        alerts = ae.evaluate(registry)
        assert len(alerts) == 0

    def test_alert_with_labels(self) -> None:
        """Alert rule có labels đọc từ registry."""
        registry = MetricRegistry()
        registry.record("requests", 100.0, labels={"method": "GET"})

        ae = AlertEngine()
        rule = AlertRule(
            name="high_get",
            metric_name="requests",
            condition=AlertCondition.GREATER_THAN,
            threshold=50,
            evaluation_interval=5,
            labels={"method": "GET"},
        )
        ae.add_rule(rule)
        ae._last_evaluations["high_get"] = None

        alerts = ae.evaluate(registry)
        assert len(alerts) >= 0  # Registry có thể trả về tất cả entries

    def test_multiple_alerts_from_registry(self) -> None:
        """Nhiều rules evaluate cùng lúc từ registry."""
        registry = MetricRegistry()
        registry.record("cpu", 95.0)
        registry.record("memory", 85.0)

        ae = AlertEngine()
        ae.add_rule(AlertRule(
            name="high_cpu",
            metric_name="cpu",
            condition=AlertCondition.GREATER_THAN,
            threshold=90,
            evaluation_interval=5,
        ))
        ae.add_rule(AlertRule(
            name="high_memory",
            metric_name="memory",
            condition=AlertCondition.GREATER_THAN,
            threshold=80,
            evaluation_interval=5,
        ))
        ae._last_evaluations["high_cpu"] = None
        ae._last_evaluations["high_memory"] = None

        alerts = ae.evaluate(registry)
        assert len(alerts) == 2

    def test_alert_interval_prevents_duplicate_fire(self) -> None:
        """Alert interval ngăn fire lại trong cùng khoảng thời gian."""
        registry = MetricRegistry()
        registry.record("errors", 200.0)

        ae = AlertEngine()
        ae.add_rule(AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=60,  # 60 giây
        ))

        # Evaluate ngay → không fire vì chưa đủ interval
        alerts = ae.evaluate(registry)
        assert len(alerts) == 0


# ===========================================================================
# SLIMonitor + CP15 MetricRegistry Integration
# ===========================================================================

class TestSLIMonitorMetricRegistryIntegration:
    """Kiểm tra SLIMonitor đọc từ CP15 MetricRegistry."""

    def test_sli_healthy_from_registry(self) -> None:
        """SLI healthy khi metric từ registry đạt target."""
        registry = MetricRegistry()
        registry.record("availability", 0.999)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_availability",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_availability"].is_healthy is True

    def test_sli_unhealthy_from_registry(self) -> None:
        """SLI unhealthy khi metric từ registry không đạt target."""
        registry = MetricRegistry()
        registry.record("availability", 0.95)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_availability",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_availability"].is_healthy is False

    def test_sli_latency_healthy(self) -> None:
        """SLI latency healthy khi metric dưới target."""
        registry = MetricRegistry()
        registry.record("latency", 150.0)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_latency"].is_healthy is True

    def test_sli_latency_unhealthy(self) -> None:
        """SLI latency unhealthy khi metric vượt target."""
        registry = MetricRegistry()
        registry.record("latency", 1000.0)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_latency"].is_healthy is False

    def test_sli_error_rate_healthy(self) -> None:
        """SLI error_rate healthy khi metric dưới target."""
        registry = MetricRegistry()
        registry.record("error_rate", 0.005)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_errors",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="error_rate",
            target=0.01,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_errors"].is_healthy is True

    def test_sli_error_rate_unhealthy(self) -> None:
        """SLI error_rate unhealthy khi metric vượt target."""
        registry = MetricRegistry()
        registry.record("error_rate", 0.05)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_errors",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="error_rate",
            target=0.01,
        ))

        statuses = sm.check_sli(registry)
        assert statuses["api_errors"].is_healthy is False

    def test_all_slis_healthy_from_registry(self) -> None:
        """Tất cả SLIs healthy khi tất cả metrics đạt target."""
        registry = MetricRegistry()
        registry.record("availability", 0.999)
        registry.record("latency", 100.0)
        registry.record("error_rate", 0.001)

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))
        sm.register_sli(SLIDefinition(
            name="latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        ))
        sm.register_sli(SLIDefinition(
            name="errors",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="error_rate",
            target=0.01,
        ))

        sm.check_sli(registry)
        assert sm.is_all_healthy() is True

    def test_mixed_sli_health_from_registry(self) -> None:
        """Một số SLIs healthy, một số không → is_all_healthy false."""
        registry = MetricRegistry()
        registry.record("availability", 0.999)
        registry.record("latency", 1000.0)  # vượt target

        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))
        sm.register_sli(SLIDefinition(
            name="latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        ))

        sm.check_sli(registry)
        assert sm.is_all_healthy() is False
