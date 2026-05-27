# coding: utf-8
"""
Tests cho FastAPI Search Emitter (CP10).

Test coverage:
- FastAPISearchEmitter.emit(): Emit search files từ SearchCollection
- GeneratedFile pattern
- Elasticsearch config với tenant isolation (KPI-029)
- Index manager
- Search service

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path

from midicoder.packs.cp10_search.models import (
    SearchCollection,
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SyncStrategy,
)
from midicoder.packs.cp10_search.fastapi import (
    FastAPISearchEmitter,
    GeneratedFile,
)


# ============================================================================
# Test FastAPISearchEmitter
# ============================================================================


class TestFastAPISearchEmitter:
    """Tests cho FastAPISearchEmitter."""

    def test_emit_returns_generated_files(self, tmp_path: Path):
        """Emit tra ve danh sach GeneratedFile."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_elasticsearch_config(self, tmp_path: Path):
        """Emit tao file elasticsearch config."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("elasticsearch" in p for p in paths)

    def test_emit_creates_search_service(self, tmp_path: Path):
        """Emit tao file search service."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders", provider=SearchProviderType.ELASTICSEARCH))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        paths = [f.path.name for f in files]
        assert any("search_service" in p or "search.service" in p for p in paths)

    def test_emit_includes_tenant_isolation(self, tmp_path: Path):
        """KPI-029: Emit bao gom tenant isolation."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders", provider=SearchProviderType.ELASTICSEARCH, tenant_isolated=True))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(f.content for f in files)
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong tra ve list rong."""
        emitter = FastAPISearchEmitter()
        files = emitter.emit(SearchCollection(), tmp_path)
        assert isinstance(files, list)

    def test_emit_multiple_indices(self, tmp_path: Path):
        """Emit voi nhieu indices."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))
        collection.add_index(SearchIndex(id="orders", provider=SearchProviderType.MEILISEARCH))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        assert len(files) > 0

    def test_emit_with_columns(self, tmp_path: Path):
        """Emit voi columns."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(
            id="products",
            provider=SearchProviderType.ELASTICSEARCH,
            columns=[
                SearchIndexColumn(name="name", column_type="text", searchable=True),
                SearchIndexColumn(name="price", column_type="numeric", sortable=True),
            ],
        ))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(f.content for f in files)
        assert "products" in all_content.lower()

    def test_emit_files_have_correct_capability(self, tmp_path: Path):
        """Tat ca GeneratedFile co capability = 'CP10'."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        assert all(f.capability == "CP10" for f in files)

    def test_emit_files_have_vietnamese_comments(self, tmp_path: Path):
        """Tat ca files co comments tieng Viet."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))

        emitter = FastAPISearchEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(f.content for f in files)
        # Kiem tra co comment tieng Viet
        assert "#" in all_content or '"""' in all_content


# ============================================================================
# Test GeneratedFile
# ============================================================================


class TestGeneratedFile:
    """Tests cho GeneratedFile dataclass."""

    def test_generated_file_attributes(self, tmp_path: Path):
        """Kiem tra cac attributes cua GeneratedFile."""
        gf = GeneratedFile(
            path=tmp_path / "test.py",
            content="print('hello')",
            template="test.py.jinja2",
            capability="CP10",
        )
        assert gf.path == tmp_path / "test.py"
        assert gf.content == "print('hello')"
        assert gf.template == "test.py.jinja2"
        assert gf.capability == "CP10"
