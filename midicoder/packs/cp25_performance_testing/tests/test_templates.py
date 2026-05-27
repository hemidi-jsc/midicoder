# coding: utf-8
"""
Unit tests cho template discovery của CP25.

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path

import jinja2
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# ============================================================================
# Template directories và danh sách templates
# ============================================================================

STACK_DIRS = {
    "fastapi": PROJECT_ROOT / "stacks" / "fastapi" / "core" / "cp25_performance_testing",
    "nestjs": PROJECT_ROOT / "stacks" / "nestjs" / "core" / "cp25_performance_testing",
    "angular": PROJECT_ROOT / "stacks" / "angular" / "core" / "cp25_performance_testing",
    "react": PROJECT_ROOT / "stacks" / "react" / "core" / "cp25_performance_testing",
}

FASTAPI_TEMPLATES = [
    "locustfile.py.jinja2",
    "locust.conf.jinja2",
    "perf_test_entity.py.jinja2",
    "perf_baseline.py.jinja2",
]

NESTJS_TEMPLATES = [
    "artillery.yml.jinja2",
    "perf_baseline.spec.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "lighthouserc.js.jinja2",
    "web_vitals.spec.ts.jinja2",
    "lighthouse_ci.js.jinja2",
]

REACT_TEMPLATES = [
    "lighthouserc.js.jinja2",
    "web_vitals.test.tsx.jinja2",
    "lighthouse_ci.js.jinja2",
]

ALL_TEMPLATES = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản sử dụng Jinja2 trực tiếp."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    # Context tối thiểu: các template CP25 dùng scenarios / collection
    ctx = {
        "scenarios": [],
        "collection": type("MockCollection", (), {"get_all_scenarios": lambda self: []})(),
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


class TestTemplateDiscovery:
    """Test template discovery cho CP25."""

    def test_fastapi_templates_exist(self) -> None:
        """Kiểm tra templates FastAPI tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "fastapi" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "locustfile.py.jinja2",
            "locust.conf.jinja2",
            "perf_test_entity.py.jinja2",
            "perf_baseline.py.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_nestjs_templates_exist(self) -> None:
        """Kiểm tra templates NestJS tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "nestjs" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "artillery.yml.jinja2",
            "perf_baseline.spec.ts.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_angular_templates_exist(self) -> None:
        """Kiểm tra templates Angular tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "angular" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "lighthouserc.js.jinja2",
            "web_vitals.spec.ts.jinja2",
            "lighthouse_ci.js.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_react_templates_exist(self) -> None:
        """Kiểm tra templates React tồn tại."""
        templates_dir = PROJECT_ROOT / "stacks" / "react" / "core" / "cp25_performance_testing"
        assert templates_dir.exists()

        expected = [
            "lighthouserc.js.jinja2",
            "web_vitals.test.tsx.jinja2",
            "lighthouse_ci.js.jinja2",
        ]
        for t in expected:
            assert (templates_dir / t).exists(), f"Template {t} không tồn tại"

    def test_pack_yml_exists(self) -> None:
        """Kiểm tra pack.yml tồn tại."""
        pack_dir = PROJECT_ROOT / "emitters" / "core" / "cp25_performance_testing"
        assert (pack_dir / "pack.yml").exists()

    def test_pack_yml_content(self) -> None:
        """Kiểm tra nội dung pack.yml."""
        import yaml

        pack_dir = PROJECT_ROOT / "emitters" / "core" / "cp25_performance_testing"
        with open(pack_dir / "pack.yml") as f:
            data = yaml.safe_load(f)

        assert data["pack"]["id"] == "CP25"
        assert data["pack"]["internal_id"] == "cp25_performance_testing"
        assert "perf_test_run" in data["pack"]["capabilities_provided"]
        assert "load_scenario" in data["pack"]["capabilities_provided"]
        assert "baseline_compare" in data["pack"]["capabilities_provided"]


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self) -> None:
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self) -> None:
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self) -> None:
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self) -> None:
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self) -> None:
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self) -> None:
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self) -> None:
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self) -> None:
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
