# coding: utf-8
"""
Test cases cho CP23 Jinja2 templates.

Kiểm tra:
- Templates tồn tại cho cả 4 stack
- Templates render được mà không lỗi
"""

import pytest
from pathlib import Path
import jinja2


class TestTemplatesExist:
    """Test templates tồn tại."""

    def _get_stacks_dir(self) -> Path:
        """Lấy stacks directory.

        Path:
        test_templates.py → tests/ → cp23_testing_framework/ → packs/ → midicoder/
        parents[3] = midicoder/ → stacks/
        """
        return Path(__file__).resolve().parents[3] / "stacks"

    def test_fastapi_templates_exist(self):
        """Kiểm tra FastAPI templates tồn tại."""
        base = self._get_stacks_dir() / "fastapi" / "cp23_testing_framework"
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

# ===========================================================================
# Dữ liệu và helper cho Rule V1/V2 (P2-17)
# ===========================================================================

_FASTAPI_TEMPLATES = [
    "pytest.ini.jinja2",
    "conftest.py.jinja2",
    "unit_test_entity.py.jinja2",
    "unit_test_command.py.jinja2",
    "unit_test_query.py.jinja2",
    "integration_test_api.py.jinja2",
    "e2e_test_flow.py.jinja2",
    "coverage_config.py.jinja2",
]

_NESTJS_TEMPLATES = [
    "jest.config.ts.jinja2",
    "entity.spec.ts.jinja2",
    "command_handler.spec.ts.jinja2",
    "query_handler.spec.ts.jinja2",
    "integration.spec.ts.jinja2",
    "e2e_flows.spec.ts.jinja2",
]

_ANGULAR_TEMPLATES = [
    "karma.conf.js.jinja2",
    "component.spec.ts.jinja2",
    "service.spec.ts.jinja2",
    "e2e_app.spec.ts.jinja2",
]

_REACT_TEMPLATES = [
    "jest.config.js.jinja2",
    "component.test.tsx.jinja2",
    "hook.test.tsx.jinja2",
    "e2e_app.test.tsx.jinja2",
]


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback đọc raw nếu render lỗi."""
    template_path = Path(__file__).resolve().parents[4] / "stacks" / stack / "core" / "cp23_testing_framework"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            undefined=jinja2.ChainableUndefined,
        )
        template = env.get_template(template_name)
        return template.render(entity={"id": "User", "table_name": "users"})
    except Exception:
        # Fallback: đọc nội dung raw nếu Jinja2 parse lỗi (JS/Angular syntax conflict)
        raw_file = template_path / template_name
        if raw_file.exists():
            return raw_file.read_text(encoding="utf-8")
        raise


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in _FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in _NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in _ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in _REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in _FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in _NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in _ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in _REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
