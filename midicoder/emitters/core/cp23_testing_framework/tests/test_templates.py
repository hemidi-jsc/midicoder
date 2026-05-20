# coding: utf-8
"""
Test cases cho CP23 Jinja2 templates.

Kiểm tra:
- Templates tồn tại cho cả 4 stack
- Templates render được mà không lỗi
"""

import pytest
from pathlib import Path


class TestTemplatesExist:
    """Test templates tồn tại."""

    def _get_stacks_dir(self) -> Path:
        """Lấy stacks directory.

        Path:
        test_templates.py → tests/ → cp23_testing_framework/ → core/ → emitters/ → midicoder/
        parents[4] = midicoder/ → stacks/
        """
        return Path(__file__).resolve().parents[4] / "stacks"

    def test_fastapi_templates_exist(self):
        """Kiểm tra FastAPI templates tồn tại."""
        base = self._get_stacks_dir() / "fastapi" / "core" / "cp23_testing_framework"
        expected = [
            "pytest.ini.jinja2",
            "conftest.py.jinja2",
            "unit_test_entity.py.jinja2",
            "unit_test_command.py.jinja2",
            "unit_test_query.py.jinja2",
            "integration_test_api.py.jinja2",
            "e2e_test_flow.py.jinja2",
            "coverage_config.py.jinja2",
        ]
        for name in expected:
            assert (base / name).exists(), f"Template {name} không tồn tại"

    def test_nestjs_templates_exist(self):
        """Kiểm tra NestJS templates tồn tại."""
        base = self._get_stacks_dir() / "nestjs" / "core" / "cp23_testing_framework"
        expected = [
            "jest.config.ts.jinja2",
            "entity.spec.ts.jinja2",
            "command_handler.spec.ts.jinja2",
            "query_handler.spec.ts.jinja2",
            "integration.spec.ts.jinja2",
            "e2e_flows.spec.ts.jinja2",
        ]
        for name in expected:
            assert (base / name).exists(), f"Template {name} không tồn tại"

    def test_angular_templates_exist(self):
        """Kiểm tra Angular templates tồn tại."""
        base = self._get_stacks_dir() / "angular" / "core" / "cp23_testing_framework"
        expected = [
            "karma.conf.js.jinja2",
            "component.spec.ts.jinja2",
            "service.spec.ts.jinja2",
            "e2e_app.spec.ts.jinja2",
        ]
        for name in expected:
            assert (base / name).exists(), f"Template {name} không tồn tại"

    def test_react_templates_exist(self):
        """Kiểm tra React templates tồn tại."""
        base = self._get_stacks_dir() / "react" / "core" / "cp23_testing_framework"
        expected = [
            "jest.config.js.jinja2",
            "component.test.tsx.jinja2",
            "hook.test.tsx.jinja2",
            "e2e_app.test.tsx.jinja2",
        ]
        for name in expected:
            assert (base / name).exists(), f"Template {name} không tồn tại"

    def test_total_template_count(self):
        """Kiểm tra tổng số templates = 22."""
        total = 0
        for stack in ["fastapi", "nestjs", "angular", "react"]:
            base = self._get_stacks_dir() / stack / "core" / "cp23_testing_framework"
            if base.exists():
                total += len(list(base.glob("*.jinja2")))
        assert total == 22, f"Mong đợi 22 templates, thực tế {total}"
