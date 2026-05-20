# coding: utf-8
"""
Unit tests cho 4 stack emitters của CP26.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp26_documentation.angular import AngularDocEmitter
from midicoder.emitters.core.cp26_documentation.fastapi import FastAPIDocEmitter
from midicoder.emitters.core.cp26_documentation.models import (
    ApiDocConfig,
    DocCollection,
    DocPortal,
    DocPortalType,
    DocSection,
)
from midicoder.emitters.core.cp26_documentation.nestjs import NestJSDocEmitter
from midicoder.emitters.core.cp26_documentation.react import ReactDocEmitter


def _make_collection():
    """Helper tạo test collection."""
    c = DocCollection()
    p = DocPortal(id="p1", type=DocPortalType.MKDOCS, title="Docs")
    p.add_section(DocSection(id="s1", portal_id="p1", title="Entities", path="entities.md", content_source="entities"))
    p.api_config = ApiDocConfig(id="api", title="API")
    c.add_portal(p)
    return c


class TestFastAPIDocEmitter:
    """Test FastAPIDocEmitter."""

    def test_generate_mkdocs(self) -> None:
        emitter = FastAPIDocEmitter("stacks/fastapi/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "mkdocs.yml" in paths

    def test_generate_index(self) -> None:
        emitter = FastAPIDocEmitter("stacks/fastapi/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "docs/index.md" in paths

    def test_generate_openapi(self) -> None:
        emitter = FastAPIDocEmitter("stacks/fastapi/core")
        results = emitter.generate(_make_collection(), entities=[{"id": "User"}])
        paths = [r["path"] for r in results]
        assert "docs/api/openapi.json" in paths

    def test_generate_nav(self) -> None:
        emitter = FastAPIDocEmitter("stacks/fastapi/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "docs/nav.md" in paths


class TestNestJSDocEmitter:
    """Test NestJSDocEmitter."""

    def test_generate_swagger(self) -> None:
        emitter = NestJSDocEmitter("stacks/nestjs/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "swagger-config.ts" in paths

    def test_generate_docusaurus(self) -> None:
        emitter = NestJSDocEmitter("stacks/nestjs/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "docs/docusaurus.config.js" in paths

    def test_generate_sidebar(self) -> None:
        emitter = NestJSDocEmitter("stacks/nestjs/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "docs/sidebar.js" in paths


class TestAngularDocEmitter:
    """Test AngularDocEmitter."""

    def test_generate_storybook_main(self) -> None:
        emitter = AngularDocEmitter("stacks/angular/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert ".storybook/main.ts" in paths

    def test_generate_storybook_preview(self) -> None:
        emitter = AngularDocEmitter("stacks/angular/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert ".storybook/preview.ts" in paths

    def test_generate_typedoc(self) -> None:
        emitter = AngularDocEmitter("stacks/angular/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "typedoc.json" in paths


class TestReactDocEmitter:
    """Test ReactDocEmitter."""

    def test_generate_storybook_main(self) -> None:
        emitter = ReactDocEmitter("stacks/react/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert ".storybook/main.ts" in paths

    def test_generate_storybook_preview(self) -> None:
        emitter = ReactDocEmitter("stacks/react/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert ".storybook/preview.ts" in paths

    def test_generate_components(self) -> None:
        emitter = ReactDocEmitter("stacks/react/core")
        results = emitter.generate(_make_collection())
        paths = [r["path"] for r in results]
        assert "docs/components.md" in paths
