# coding: utf-8
"""
Unit tests cho template discovery của CP26.

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


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
