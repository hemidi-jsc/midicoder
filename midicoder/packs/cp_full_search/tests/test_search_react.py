# coding: utf-8
"""
Tests cho React Search Emitter (CP10).

Test coverage:
- ReactEmitter.emit(): Emit React search files
- GeneratedFile pattern
- SearchTypes, SearchProvider, useSearch, search-utils

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
from midicoder.packs.cp_full_search.react import (
    ReactEmitter,
    GeneratedFile,
)


class TestReactEmitter:
    """Tests cho ReactEmitter."""

    def test_emit_returns_generated_files(self, tmp_path: Path):
        """Emit tra ve danh sach GeneratedFile."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_types(self, tmp_path: Path):
        """Emit tao file search types."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("types" in p for p in paths)

    def test_emit_creates_provider(self, tmp_path: Path):
        """Emit tao file SearchProvider."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("SearchProvider" in p for p in paths)

    def test_emit_creates_hook(self, tmp_path: Path):
        """Emit tao file useSearch hook."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="articles"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("useSearch" in p for p in paths)

    def test_emit_creates_utils(self, tmp_path: Path):
        """Emit tao file search-utils."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("utils" in p for p in paths)

    def test_emit_creates_index(self, tmp_path: Path):
        """Emit tao file index.ts."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert "index.ts" in paths

    def test_emit_includes_tenant(self, tmp_path: Path):
        """KPI-029: Emit bao gom tenant awareness."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders", tenant_isolated=True))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(f.content for f in files)
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong tra ve list rong."""
        emitter = ReactEmitter()
        files = emitter.emit(SearchCollection(), tmp_path)
        assert isinstance(files, list)
        assert len(files) == 0

    def test_emit_files_have_correct_capability(self, tmp_path: Path):
        """Tat ca GeneratedFile co capability = 'CP10'."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        assert all(f.capability == "CP10" for f in files)

    def test_emit_provider_has_context(self, tmp_path: Path):
        """SearchProvider co React context."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        provider_content = next(
            (f.content for f in files if "SearchProvider" in f.path.name), ""
        )
        assert "createContext" in provider_content
        assert "SearchContext.Provider" in provider_content

    def test_emit_hook_throws_outside_provider(self, tmp_path: Path):
        """useSearch throw error khi dung ben ngoai provider."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = ReactEmitter()
        files = emitter.emit(collection, tmp_path)

        hook_content = next(
            (f.content for f in files if "useSearch" in f.path.name), ""
        )
        assert "throw new Error" in hook_content
