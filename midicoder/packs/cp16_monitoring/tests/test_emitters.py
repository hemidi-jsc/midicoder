# coding: utf-8
"""
Test cases cho emitter classes của CP16.

Kiểm tra:
- FastAPIMonitoringEmitter: generate() trả về dict, keys đúng, content không rỗng
- NestJSMonitoringEmitter: generate() trả về dict, keys đúng, content không rỗng
- AngularMonitoringEmitter: generate() trả về dict, keys đúng, content không rỗng
- ReactMonitoringEmitter: generate() trả về dict, keys đúng, content không rỗng
"""

import pytest

from midicoder.packs.cp16_monitoring.fastapi import FastAPIMonitoringEmitter
from midicoder.packs.cp16_monitoring.nestjs import NestJSMonitoringEmitter
from midicoder.packs.cp16_monitoring.angular import AngularMonitoringEmitter
from midicoder.packs.cp16_monitoring.react import ReactMonitoringEmitter


# ===========================================================================
# FastAPI Emitter Tests
# ===========================================================================


class TestFastAPIMonitoringEmitter:
    """Test FastAPIMonitoringEmitter."""

    def test_generate_returns_dict(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_service_file(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/monitoring_service.py" in result

    def test_generate_has_router_file(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/monitoring_router.py" in result

    def test_generate_total_files(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert len(result) == 2

    def test_service_content_not_empty(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert len(result["src/monitoring/monitoring_service.py"]) > 0

    def test_service_has_monitoring_service_class(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "class MonitoringService" in result["src/monitoring/monitoring_service.py"]

    def test_service_has_dashboard_manager(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "class DashboardManager" in result["src/monitoring/monitoring_service.py"]

    def test_service_has_alert_engine(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "class AlertEngine" in result["src/monitoring/monitoring_service.py"]

    def test_service_has_sli_monitor(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "class SLIMonitor" in result["src/monitoring/monitoring_service.py"]

    def test_router_has_api_router(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert "APIRouter" in result["src/monitoring/monitoring_router.py"]

    def test_router_has_dashboards_endpoint(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert '"/dashboards"' in result["src/monitoring/monitoring_router.py"]

    def test_router_has_alerts_endpoint(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert '"/alerts"' in result["src/monitoring/monitoring_router.py"]

    def test_router_has_slis_endpoint(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        assert '"/slis"' in result["src/monitoring/monitoring_router.py"]

    def test_generate_service_returns_dict(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate_service()
        assert isinstance(result, dict)

    def test_generate_router_returns_dict(self):
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate_router()
        assert isinstance(result, dict)

    def test_no_violation_post_init(self):
        """Verify V2: no __post_init__ in generated service."""
        emitter = FastAPIMonitoringEmitter()
        result = emitter.generate()
        content = result["src/monitoring/monitoring_service.py"]
        assert "__post_init__" not in content


# ===========================================================================
# NestJS Emitter Tests
# ===========================================================================


class TestNestJSMonitoringEmitter:
    """Test NestJSMonitoringEmitter."""

    def test_generate_returns_dict(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_module(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/monitoring.module.ts" in result

    def test_generate_has_service(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/monitoring.service.ts" in result

    def test_generate_has_controller(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/monitoring.controller.ts" in result

    def test_generate_total_files(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert len(result) == 3

    def test_module_has_module_decorator(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "@Module" in result["src/monitoring/monitoring.module.ts"]

    def test_module_has_global_decorator(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "@Global" in result["src/monitoring/monitoring.module.ts"]

    def test_service_has_monitoring_service(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "MonitoringService" in result["src/monitoring/monitoring.service.ts"]

    def test_service_has_create_dashboard(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "createDashboard" in result["src/monitoring/monitoring.service.ts"]

    def test_service_has_evaluate_alerts(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "evaluateAlerts" in result["src/monitoring/monitoring.service.ts"]

    def test_controller_has_dashboards_route(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "listDashboards" in result["src/monitoring/monitoring.controller.ts"]

    def test_controller_has_monitoring_prefix(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate()
        assert "@Controller('monitoring')" in result["src/monitoring/monitoring.controller.ts"]

    def test_generate_module_returns_dict(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate_module()
        assert isinstance(result, dict)

    def test_generate_service_returns_dict(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate_service()
        assert isinstance(result, dict)

    def test_generate_controller_returns_dict(self):
        emitter = NestJSMonitoringEmitter()
        result = emitter.generate_controller()
        assert isinstance(result, dict)


# ===========================================================================
# Angular Emitter Tests
# ===========================================================================


class TestAngularMonitoringEmitter:
    """Test AngularMonitoringEmitter."""

    def test_generate_returns_dict(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_dashboard_widget(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "src/app/core/monitoring/dashboard_widget.component.ts" in result

    def test_generate_has_alert_panel(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "src/app/core/monitoring/alert_panel.component.ts" in result

    def test_generate_total_files(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert len(result) == 2

    def test_dashboard_has_component_decorator(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "@Component" in result["src/app/core/monitoring/dashboard_widget.component.ts"]

    def test_dashboard_has_selector(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "app-dashboard-widget" in result["src/app/core/monitoring/dashboard_widget.component.ts"]

    def test_dashboard_has_http_client(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "HttpClient" in result["src/app/core/monitoring/dashboard_widget.component.ts"]

    def test_alert_panel_has_component_decorator(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "@Component" in result["src/app/core/monitoring/alert_panel.component.ts"]

    def test_alert_panel_has_selector(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "app-alert-panel" in result["src/app/core/monitoring/alert_panel.component.ts"]

    def test_alert_panel_has_severity_filter(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate()
        assert "severityFilter" in result["src/app/core/monitoring/alert_panel.component.ts"]

    def test_generate_dashboard_widget_returns_dict(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate_dashboard_widget()
        assert isinstance(result, dict)

    def test_generate_alert_panel_returns_dict(self):
        emitter = AngularMonitoringEmitter()
        result = emitter.generate_alert_panel()
        assert isinstance(result, dict)


# ===========================================================================
# React Emitter Tests
# ===========================================================================


class TestReactMonitoringEmitter:
    """Test ReactMonitoringEmitter."""

    def test_generate_returns_dict(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert isinstance(result, dict)

    def test_generate_has_types(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/types.ts" in result

    def test_generate_has_dashboard_panel(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/DashboardPanel.tsx" in result

    def test_generate_has_alert_banner(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "src/monitoring/AlertBanner.tsx" in result

    def test_generate_total_files(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert len(result) == 3

    def test_types_has_interfaces(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        content = result["src/monitoring/types.ts"]
        assert "interface Dashboard" in content
        assert "interface Panel" in content
        assert "interface FiredAlert" in content
        assert "interface SLIStatus" in content

    def test_types_has_severity_colors(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "SEVERITY_COLORS" in result["src/monitoring/types.ts"]

    def test_dashboard_panel_has_react_import(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "from 'react'" in result["src/monitoring/DashboardPanel.tsx"]

    def test_dashboard_panel_has_use_state(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "useState" in result["src/monitoring/DashboardPanel.tsx"]

    def test_dashboard_panel_has_use_effect(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "useEffect" in result["src/monitoring/DashboardPanel.tsx"]

    def test_alert_banner_has_react_import(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "from 'react'" in result["src/monitoring/AlertBanner.tsx"]

    def test_alert_banner_has_acknowledge(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "handleAcknowledge" in result["src/monitoring/AlertBanner.tsx"]

    def test_alert_banner_has_resolve(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate()
        assert "handleResolve" in result["src/monitoring/AlertBanner.tsx"]

    def test_generate_types_returns_dict(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate_types()
        assert isinstance(result, dict)

    def test_generate_dashboard_panel_returns_dict(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate_dashboard_panel()
        assert isinstance(result, dict)

    def test_generate_alert_banner_returns_dict(self):
        emitter = ReactMonitoringEmitter()
        result = emitter.generate_alert_banner()
        assert isinstance(result, dict)
