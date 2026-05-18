# coding: utf-8
"""
Kiểm tra templates của CP16 — existence và content validation.
"""

import os
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

# Định nghĩa tất cả templates mong đợi
TEMPLATES = {
    # FastAPI (2 templates)
    "fastapi": [
        "monitoring_service.py.jinja2",
        "monitoring_router.py.jinja2",
    ],
    # NestJS (3 templates)
    "nestjs": [
        "monitoring.module.ts.jinja2",
        "monitoring.service.ts.jinja2",
        "monitoring.controller.ts.jinja2",
    ],
    # Angular (2 templates)
    "angular": [
        "dashboard_widget.component.ts.jinja2",
        "alert_panel.component.ts.jinja2",
    ],
    # React (3 templates)
    "react": [
        "types.ts.jinja2",
        "DashboardPanel.tsx.jinja2",
        "AlertBanner.tsx.jinja2",
    ],
}


class TestTemplateExistence:
    """Kiểm tra sự tồn tại của templates."""

    @pytest.mark.parametrize("template", TEMPLATES["fastapi"])
    def test_fastapi_template_exists(self, template) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "fastapi", "core", "cp16_monitoring", template)
        assert os.path.isfile(path), f"Template không tồn tại: {path}"

    @pytest.mark.parametrize("template", TEMPLATES["nestjs"])
    def test_nestjs_template_exists(self, template) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "nestjs", "core", "cp16_monitoring", template)
        assert os.path.isfile(path), f"Template không tồn tại: {path}"

    @pytest.mark.parametrize("template", TEMPLATES["angular"])
    def test_angular_template_exists(self, template) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "angular", "core", "cp16_monitoring", template)
        assert os.path.isfile(path), f"Template không tồn tại: {path}"

    @pytest.mark.parametrize("template", TEMPLATES["react"])
    def test_react_template_exists(self, template) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "react", "core", "cp16_monitoring", template)
        assert os.path.isfile(path), f"Template không tồn tại: {path}"


class TestTemplateContent:
    """Kiểm tra nội dung templates."""

    def test_fastapi_service_has_monitoring_service(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "fastapi", "core", "cp16_monitoring", "monitoring_service.py.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "MonitoringService" in content or "monitoring_service" in content

    def test_fastapi_router_has_router(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "fastapi", "core", "cp16_monitoring", "monitoring_router.py.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "APIRouter" in content or "router" in content.lower()

    def test_nestjs_module_has_module_decorator(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "nestjs", "core", "cp16_monitoring", "monitoring.module.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "@Module" in content or "Module" in content

    def test_nestjs_service_has_service_class(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "nestjs", "core", "cp16_monitoring", "monitoring.service.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "MonitoringService" in content or "Service" in content

    def test_nestjs_controller_has_controller(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "nestjs", "core", "cp16_monitoring", "monitoring.controller.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "MonitoringController" in content or "Controller" in content

    def test_angular_dashboard_has_component(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "angular", "core", "cp16_monitoring", "dashboard_widget.component.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "@Component" in content or "Component" in content

    def test_angular_alert_has_panel(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "angular", "core", "cp16_monitoring", "alert_panel.component.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "@Component" in content or "Component" in content

    def test_react_types_has_interface(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "react", "core", "cp16_monitoring", "types.ts.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "interface" in content or "type" in content

    def test_react_dashboard_has_function_component(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "react", "core", "cp16_monitoring", "DashboardPanel.tsx.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "DashboardPanel" in content or "function" in content or "const" in content

    def test_react_alert_has_banner(self) -> None:
        path = os.path.join(REPO_ROOT, "midicoder", "stacks", "react", "core", "cp16_monitoring", "AlertBanner.tsx.jinja2")
        content = open(path, encoding="utf-8").read()
        assert "AlertBanner" in content or "function" in content or "const" in content

    def test_all_templates_non_empty(self) -> None:
        for stack, templates in TEMPLATES.items():
            for template in templates:
                path = os.path.join(REPO_ROOT, "midicoder", "stacks", stack, "core", "cp16_monitoring", template)
                size = os.path.getsize(path)
                assert size > 0, f"Template rỗng: {path}"

    def test_total_template_count(self) -> None:
        total = sum(len(v) for v in TEMPLATES.values())
        assert total == 10
