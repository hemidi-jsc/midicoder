# coding: utf-8
"""
Kiểm tra runtime engine của CP16 — DashboardManager, AlertEngine, SLIMonitor.

Coverage: 100% cho dashboard.py, alert.py, sli.py
"""

import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from midicoder.emitters.core.cp16_monitoring.dashboard import DashboardManager
from midicoder.emitters.core.cp16_monitoring.alert import AlertEngine
from midicoder.emitters.core.cp16_monitoring.sli import SLIMonitor
from midicoder.emitters.core.cp16_monitoring.models import (
    DashboardProfile,
    DashboardType,
    Panel,
    AlertRule,
    AlertCondition,
    AlertSeverity,
    FiredAlert,
    SLIDefinition,
    SLIMetricType,
    SLIStatus,
)


# ===========================================================================
# Mock CP15 MetricRegistry
# ===========================================================================

class MockMetricEntry:
    """Entry mô phỏng từ CP15 MetricRegistry."""

    def __init__(self, value: float) -> None:
        self.value = value


class MockRegistry:
    """Registry giả lập CP15 MetricRegistry."""

    def __init__(self) -> None:
        self._metrics: dict[str, list] = {}

    def record(self, name: str, value: float, labels: dict | None = None) -> None:
        self._metrics.setdefault(name, []).append(MockMetricEntry(value))

    def get(self, name: str, labels: dict | None = None) -> list:
        return self._metrics.get(name, [])


# ===========================================================================
# DashboardManager Tests
# ===========================================================================

class TestDashboardManager:
    """Kiểm tra DashboardManager."""

    def test_create_dashboard_defaults(self) -> None:
        dm = DashboardManager()
        profile = dm.create_dashboard("test")
        assert profile.name == "test"
        assert profile.dashboard_type == DashboardType.SYSTEM
        assert profile.panels == []
        assert profile.refresh_interval_seconds == 30

    def test_create_dashboard_with_type(self) -> None:
        dm = DashboardManager()
        profile = dm.create_dashboard("api", dashboard_type=DashboardType.API)
        assert profile.dashboard_type == DashboardType.API

    def test_create_dashboard_with_panels(self) -> None:
        dm = DashboardManager()
        panel = Panel(name="p1", metric_name="http_requests")
        profile = dm.create_dashboard("test", panels=[panel])
        assert len(profile.panels) == 1

    def test_create_dashboard_with_description(self) -> None:
        dm = DashboardManager()
        profile = dm.create_dashboard("test", description="Mô tả dashboard")
        assert profile.description == "Mô tả dashboard"

    def test_create_dashboard_with_refresh(self) -> None:
        dm = DashboardManager()
        profile = dm.create_dashboard("test", refresh_interval_seconds=60)
        assert profile.refresh_interval_seconds == 60

    def test_add_panel(self) -> None:
        dm = DashboardManager()
        dm.create_dashboard("test")
        panel = Panel(name="p1", metric_name="http_requests")
        dm.add_panel("test", panel)
        dashboard = dm.get_dashboard("test")
        assert dashboard is not None
        assert len(dashboard.panels) == 1

    def test_add_panel_to_nonexistent_dashboard(self) -> None:
        dm = DashboardManager()
        panel = Panel(name="p1", metric_name="http_requests")
        with pytest.raises(KeyError):
            dm.add_panel("nonexistent", panel)

    def test_get_dashboard(self) -> None:
        dm = DashboardManager()
        dm.create_dashboard("test")
        profile = dm.get_dashboard("test")
        assert profile is not None
        assert profile.name == "test"

    def test_get_dashboard_not_found(self) -> None:
        dm = DashboardManager()
        profile = dm.get_dashboard("nonexistent")
        assert profile is None

    def test_list_dashboards_empty(self) -> None:
        dm = DashboardManager()
        assert dm.list_dashboards() == []

    def test_list_dashboards_multiple(self) -> None:
        dm = DashboardManager()
        dm.create_dashboard("d1")
        dm.create_dashboard("d2")
        dashboards = dm.list_dashboards()
        assert len(dashboards) == 2

    def test_update_panel_values_from_registry(self) -> None:
        dm = DashboardManager()
        panel = Panel(name="p1", metric_name="http_requests")
        dm.create_dashboard("test", panels=[panel])

        registry = MockRegistry()
        registry.record("http_requests", 100.0)
        dm.update_panel_values(registry)

        values = dm.get_panel_values("test")
        assert values["p1"]["value"] == 100.0

    def test_update_panel_values_no_data(self) -> None:
        dm = DashboardManager()
        panel = Panel(name="p1", metric_name="missing_metric")
        dm.create_dashboard("test", panels=[panel])

        registry = MockRegistry()
        dm.update_panel_values(registry)

        values = dm.get_panel_values("test")
        assert values["p1"]["value"] is None

    def test_export_json(self) -> None:
        dm = DashboardManager()
        dm.create_dashboard("test")
        exported = dm.export_json()
        data = json.loads(exported)
        assert "dashboards" in data
        assert "panel_values" in data
        assert len(data["dashboards"]) == 1

    def test_get_panel_values_empty(self) -> None:
        dm = DashboardManager()
        values = dm.get_panel_values("nonexistent")
        assert values == {}

    def test_multiple_panels_update(self) -> None:
        dm = DashboardManager()
        panels = [
            Panel(name="req", metric_name="requests"),
            Panel(name="err", metric_name="errors"),
        ]
        dm.create_dashboard("test", panels=panels)

        registry = MockRegistry()
        registry.record("requests", 500.0)
        registry.record("errors", 10.0)
        dm.update_panel_values(registry)

        values = dm.get_panel_values("test")
        assert values["req"]["value"] == 500.0
        assert values["err"]["value"] == 10.0


# ===========================================================================
# AlertEngine Tests
# ===========================================================================

class TestAlertEngine:
    """Kiểm tra AlertEngine."""

    def test_add_rule(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
        )
        ae.add_rule(rule)
        assert len(ae._rules) == 1

    def test_remove_rule(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
        )
        ae.add_rule(rule)
        result = ae.remove_rule("high_errors")
        assert result is True
        assert len(ae._rules) == 0

    def test_remove_rule_not_found(self) -> None:
        ae = AlertEngine()
        result = ae.remove_rule("nonexistent")
        assert result is False

    def test_evaluate_greater_than_fires(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        registry.record("errors", 200.0)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 1
        assert alerts[0].rule_name == "high_errors"
        assert alerts[0].current_value == 200.0

    def test_evaluate_greater_than_no_fire(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        registry.record("errors", 50.0)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 0

    def test_evaluate_less_than_fires(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="low_availability",
            metric_name="availability",
            condition=AlertCondition.LESS_THAN,
            threshold=0.99,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        registry.record("availability", 0.95)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 1

    def test_evaluate_equals_fires(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="zero_requests",
            metric_name="requests",
            condition=AlertCondition.EQUALS,
            threshold=0,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        registry.record("requests", 0.0)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 1

    def test_evaluate_not_equals_fires(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="nonzero_requests",
            metric_name="requests",
            condition=AlertCondition.NOT_EQUALS,
            threshold=0,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        registry.record("requests", 10.0)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 1

    def test_evaluation_interval_enforced(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=60,  # 60 giây
        )
        ae.add_rule(rule)

        registry = MockRegistry()
        registry.record("errors", 200.0)
        alerts = ae.evaluate(registry)
        # Không fire vì chưa đủ khoảng thời gian
        assert len(alerts) == 0

    def test_fire_alert_creates_fired_alert(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
        )
        alert = ae.fire_alert(rule, 200.0)
        assert alert.rule_name == "high_errors"
        assert alert.current_value == 200.0
        assert alert.severity == "warning"

    def test_get_fired_alerts(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
        )
        ae.fire_alert(rule, 200.0)
        alerts = ae.get_fired_alerts()
        assert len(alerts) == 1

    def test_clear_alerts(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="errors",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
        )
        ae.fire_alert(rule, 200.0)
        ae.fire_alert(rule, 300.0)
        count = ae.clear_alerts()
        assert count == 2
        assert len(ae.get_fired_alerts()) == 0

    def test_evaluate_no_metric_data(self) -> None:
        ae = AlertEngine()
        rule = AlertRule(
            name="high_errors",
            metric_name="nonexistent",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=5,
        )
        ae.add_rule(rule)
        # Xóa time tracking để evaluate ngay
        ae._last_evaluations[rule.name] = None

        registry = MockRegistry()
        alerts = ae.evaluate(registry)
        assert len(alerts) == 0

    def test_multiple_rules_evaluate(self) -> None:
        ae = AlertEngine()
        ae.add_rule(AlertRule(
            name="rule1",
            metric_name="m1",
            condition=AlertCondition.GREATER_THAN,
            threshold=100,
            evaluation_interval=5,
        ))
        ae.add_rule(AlertRule(
            name="rule2",
            metric_name="m2",
            condition=AlertCondition.LESS_THAN,
            threshold=10,
            evaluation_interval=5,
        ))
        ae._last_evaluations["rule1"] = None
        ae._last_evaluations["rule2"] = None

        registry = MockRegistry()
        registry.record("m1", 200.0)
        registry.record("m2", 5.0)
        alerts = ae.evaluate(registry)
        assert len(alerts) == 2


# ===========================================================================
# SLIMonitor Tests
# ===========================================================================

class TestSLIMonitor:
    """Kiểm tra SLIMonitor."""

    def test_register_sli(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_availability",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        )
        sm.register_sli(sli)
        assert len(sm._definitions) == 1

    def test_unregister_sli(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_availability",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        )
        sm.register_sli(sli)
        result = sm.unregister_sli("api_availability")
        assert result is True
        assert len(sm._definitions) == 0

    def test_unregister_sli_not_found(self) -> None:
        sm = SLIMonitor()
        result = sm.unregister_sli("nonexistent")
        assert result is False

    def test_check_availability_healthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("availability", 0.999)
        statuses = sm.check_sli(registry)

        assert "api_avail" in statuses
        assert statuses["api_avail"].is_healthy is True

    def test_check_availability_unhealthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("availability", 0.95)
        statuses = sm.check_sli(registry)

        assert statuses["api_avail"].is_healthy is False

    def test_check_latency_healthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("latency", 200.0)
        statuses = sm.check_sli(registry)

        assert statuses["api_latency"].is_healthy is True

    def test_check_latency_unhealthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("latency", 1000.0)
        statuses = sm.check_sli(registry)

        assert statuses["api_latency"].is_healthy is False

    def test_check_error_rate_healthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_errors",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="error_rate",
            target=0.01,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("error_rate", 0.005)
        statuses = sm.check_sli(registry)

        assert statuses["api_errors"].is_healthy is True

    def test_check_error_rate_unhealthy(self) -> None:
        sm = SLIMonitor()
        sli = SLIDefinition(
            name="api_errors",
            metric_type=SLIMetricType.ERROR_RATE,
            metric_name="error_rate",
            target=0.01,
        )
        sm.register_sli(sli)

        registry = MockRegistry()
        registry.record("error_rate", 0.05)
        statuses = sm.check_sli(registry)

        assert statuses["api_errors"].is_healthy is False

    def test_check_sli_by_name(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="sli1",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="avail1",
            target=0.99,
        ))
        sm.register_sli(SLIDefinition(
            name="sli2",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="avail2",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("avail1", 0.999)
        registry.record("avail2", 0.999)
        statuses = sm.check_sli(registry, sli_name="sli1")

        assert "sli1" in statuses
        assert "sli2" not in statuses

    def test_get_sli_status(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("availability", 0.999)
        sm.check_sli(registry)

        status = sm.get_sli_status("api_avail")
        assert status is not None
        assert status.is_healthy is True

    def test_get_sli_status_not_found(self) -> None:
        sm = SLIMonitor()
        status = sm.get_sli_status("nonexistent")
        assert status is None

    def test_get_all_sli_status(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="sli1",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="avail",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("avail", 0.999)
        sm.check_sli(registry)

        all_status = sm.get_all_sli_status()
        assert "sli1" in all_status

    def test_is_all_healthy_true(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("availability", 0.999)
        sm.check_sli(registry)

        assert sm.is_all_healthy() is True

    def test_is_all_healthy_false(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("availability", 0.95)
        sm.check_sli(registry)

        assert sm.is_all_healthy() is False

    def test_is_all_healthy_no_slis(self) -> None:
        sm = SLIMonitor()
        assert sm.is_all_healthy() is True

    def test_check_sli_no_metric_data(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="nonexistent",
            target=0.99,
        ))

        registry = MockRegistry()
        statuses = sm.check_sli(registry)

        assert statuses["api_avail"].current_value == 0.0
        assert statuses["api_avail"].is_healthy is False

    def test_multiple_slis_all_healthy(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="avail",
            target=0.99,
        ))
        sm.register_sli(SLIDefinition(
            name="latency",
            metric_type=SLIMetricType.LATENCY,
            metric_name="latency",
            target=500,
        ))

        registry = MockRegistry()
        registry.record("avail", 0.999)
        registry.record("latency", 200.0)
        sm.check_sli(registry)

        assert sm.is_all_healthy() is True

    def test_sli_status_has_evaluated_at(self) -> None:
        sm = SLIMonitor()
        sm.register_sli(SLIDefinition(
            name="api_avail",
            metric_type=SLIMetricType.AVAILABILITY,
            metric_name="availability",
            target=0.99,
        ))

        registry = MockRegistry()
        registry.record("availability", 0.999)
        sm.check_sli(registry)

        status = sm.get_sli_status("api_avail")
        assert status is not None
        assert status.evaluated_at is not None
        assert status.evaluated_at.tzinfo is not None
