# coding: utf-8
"""
Unit tests cho template discovery của CP26.

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
    "fastapi": PROJECT_ROOT / "stacks" / "fastapi" / "core" / "cp26_documentation",
    "nestjs": PROJECT_ROOT / "stacks" / "nestjs" / "core" / "cp26_documentation",
    "angular": PROJECT_ROOT / "stacks" / "angular" / "core" / "cp26_documentation",
    "react": PROJECT_ROOT / "stacks" / "react" / "core" / "cp26_documentation",
}

FASTAPI_TEMPLATES = [
    "mkdocs.yml.jinja2",
    "docs_index.md.jinja2",
    "openapi.json.jinja2",
    "nav.md.jinja2",
]

NESTJS_TEMPLATES = [
    "swagger_config.ts.jinja2",
    "docusaurus.config.js.jinja2",
    "sidebar.js.jinja2",
    "docs_index.md.jinja2",
]

ANGULAR_TEMPLATES = [
    "storybook_main.ts.jinja2",
    "storybook_preview.ts.jinja2",
    "typedoc.json.jinja2",
    "components.md.jinja2",
]

REACT_TEMPLATES = [
    "storybook_main.ts.jinja2",
    "storybook_preview.ts.jinja2",
    "typedoc.json.jinja2",
    "components.md.jinja2",
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
    # Context tối thiểu: các template CP26 dùng collection (portals, sections, api_configs)
    ctx = {
        "collection": type(
            "MockCollection",
            (),
            {
                "portals": [],
                "api_configs": [],
                "get_all_sections": lambda self: [],
            },
        )(),
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


class TestTemplateDiscovery:
    """Test template discovery cho CP26."""

    def test_fastapi_templates_exist(self) -> None:
        d = PROJECT_ROOT / "stacks" / "fastapi" / "core" / "cp26_documentation"
        assert (d / "mkdocs.yml.jinja2").exists()
        assert (d / "docs_index.md.jinja2").exists()
        assert (d / "openapi.json.jinja2").exists()
        assert (d / "nav.md.jinja2").exists()

    def test_nestjs_templates_exist(self) -> None:
        d = PROJECT_ROOT / "stacks" / "nestjs" / "core" / "cp26_documentation"
        assert (d / "swagger_config.ts.jinja2").exists()
        assert (d / "docusaurus.config.js.jinja2").exists()
        assert (d / "sidebar.js.jinja2").exists()
        assert (d / "docs_index.md.jinja2").exists()

    def test_angular_templates_exist(self) -> None:
        d = PROJECT_ROOT / "stacks" / "angular" / "core" / "cp26_documentation"
        assert (d / "storybook_main.ts.jinja2").exists()
        assert (d / "storybook_preview.ts.jinja2").exists()
        assert (d / "typedoc.json.jinja2").exists()
        assert (d / "components.md.jinja2").exists()

    def test_react_templates_exist(self) -> None:
        d = PROJECT_ROOT / "stacks" / "react" / "core" / "cp26_documentation"
        assert (d / "storybook_main.ts.jinja2").exists()
        assert (d / "storybook_preview.ts.jinja2").exists()
        assert (d / "typedoc.json.jinja2").exists()
        assert (d / "components.md.jinja2").exists()

    def test_pack_yml_exists(self) -> None:
        d = PROJECT_ROOT / "emitters" / "core" / "cp26_documentation"
        assert (d / "pack.yml").exists()


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
