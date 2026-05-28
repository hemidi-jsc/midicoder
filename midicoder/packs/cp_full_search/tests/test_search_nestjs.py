# coding: utf-8
"""
Tests cho NestJS Search Emitter (CP10).

Test coverage:
- NestJSSearchEmitter.emit(): Emit search files tu SearchCollection
- GeneratedFile pattern
- SearchModule, SearchService, Decorators

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path

from midicoder.packs.cp_full_search.models import (
    SearchCollection,
    SearchIndex,
    SearchProviderType,
)
from midicoder.packs.cp_full_search.nestjs import (
    NestJSSearchEmitter,
    GeneratedFile,
)


class TestNestJSSearchEmitter:
    """Tests cho NestJSSearchEmitter."""

    def test_emit_returns_generated_files(self, tmp_path: Path):
        """Emit tra ve danh sach GeneratedFile."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_search_module(self, tmp_path: Path):
        """Emit tao file search module."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("search.module" in p for p in paths)

    def test_emit_creates_search_service(self, tmp_path: Path):
        """Emit tao file search service."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("search.service" in p for p in paths)

    def test_emit_creates_decorators(self, tmp_path: Path):
        """Emit tao file search decorators."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="articles"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("decorators" in p for p in paths)

    def test_emit_includes_tenant(self, tmp_path: Path):
        """KPI-029: Emit bao gom tenant isolation."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders", tenant_isolated=True))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(f.content for f in files)
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong tra ve list rong."""
        emitter = NestJSSearchEmitter()
        files = emitter.emit(SearchCollection(), tmp_path)
        assert isinstance(files, list)
        assert len(files) == 0

    def test_emit_files_have_correct_capability(self, tmp_path: Path):
        """Tat ca GeneratedFile co capability = 'CP10'."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        assert all(f.capability == "CP10" for f in files)

    def test_emit_has_nestjs_module_decorator(self, tmp_path: Path):
        """Search module co @Module decorator."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        module_content = next(
            (f.content for f in files if "module" in f.path.name), ""
        )
        assert "@Module" in module_content

    def test_emit_service_has_injectable(self, tmp_path: Path):
        """Search service co @Injectable decorator."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = NestJSSearchEmitter()
        files = emitter.emit(collection, tmp_path)

        service_content = next(
            (f.content for f in files if "service" in f.path.name), ""
        )
        assert "@Injectable" in service_content
