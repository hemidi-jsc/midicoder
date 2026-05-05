# coding: utf-8
"""
Tests cho Search Emitter module (P2-001-I).

Bao gom:
- Test Core Search Models (SearchIndex, SearchIndexColumn, SyncStrategy)
- Test Search Parser (parse_from_metadata)
- Test FastAPI Search Emitter (Elasticsearch emitter)
- Test NestJS Search Emitter (SearchModule emitter)
- Test KPI-029 Tenant Isolation cho search templates

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path

from midicoder.emitters.core.search.models import (
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
    SearchCollection,
)
from midicoder.emitters.core.search.parser import SearchParser
from midicoder.emitters.core.search.fastapi import ElasticsearchEmitter
from midicoder.emitters.core.search.nestjs import SearchModuleEmitter


# ============================================================================
# Test Core Search Models
# ============================================================================


class TestSearchIndexColumn:
    """Tests cho SearchIndexColumn model."""

    def test_create_text_column(self):
        """Tao text column."""
        col = SearchIndexColumn(
            name="title",
            column_type="text",
            searchable=True,
        )
        assert col.name == "title"
        assert col.column_type == "text"
        assert col.searchable is True

    def test_create_keyword_column(self):
        """Tao keyword column."""
        col = SearchIndexColumn(
            name="status",
            column_type="keyword",
            filterable=True,
        )
        assert col.filterable is True

    def test_create_numeric_column(self):
        """Tao numeric column."""
        col = SearchIndexColumn(
            name="price",
            column_type="numeric",
            sortable=True,
        )
        assert col.sortable is True

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = SearchIndexColumn(
            name="description",
            column_type="text",
            searchable=True,
            analyser="vietnamese",
        )
        d = original.to_dict()
        restored = SearchIndexColumn.from_dict(d)
        assert restored.name == original.name
        assert restored.analyser == original.analyser


class TestSearchIndex:
    """Tests cho SearchIndex model."""

    def test_create_basic_index(self):
        """Tao search index co ban."""
        index = SearchIndex(
            id="products",
            provider=SearchProviderType.ELASTICSEARCH,
        )
        assert index.id == "products"
        assert index.provider == SearchProviderType.ELASTICSEARCH

    def test_create_tenant_index(self):
        """Tao search index tenant-aware (KPI-029)."""
        index = SearchIndex(
            id="orders",
            provider=SearchProviderType.ELASTICSEARCH,
            tenant_isolated=True,
        )
        assert index.tenant_isolated is True

    def test_create_with_columns(self):
        """Tao search index voi columns."""
        index = SearchIndex(
            id="articles",
            provider=SearchProviderType.ELASTICSEARCH,
            columns=[
                SearchIndexColumn(name="title", column_type="text", searchable=True),
                SearchIndexColumn(name="author", column_type="keyword", filterable=True),
            ],
        )
        assert len(index.columns) == 2

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = SearchIndex(
            id="users",
            provider=SearchProviderType.ELASTICSEARCH,
            sync_strategy=SyncStrategy.NEAR_REALTIME,
            sync_trigger=SyncTrigger.EVENT,
            tenant_isolated=True,
            description="Search index cho users",
        )
        d = original.to_dict()
        restored = SearchIndex.from_dict(d)
        assert restored.id == original.id
        assert restored.sync_strategy == original.sync_strategy
        assert restored.tenant_isolated == original.tenant_isolated


class TestSearchCollection:
    """Tests cho SearchCollection."""

    def test_add_index_and_count(self):
        """Them index va dem."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))
        assert collection.total_count == 1

    def test_get_by_id(self):
        """Tim index theo ID."""
        collection = SearchCollection()
        index = SearchIndex(id="articles", provider=SearchProviderType.ELASTICSEARCH)
        collection.add_index(index)
        found = collection.get_by_id("articles")
        assert found is not None
        assert found.id == "articles"

    def test_tenant_isolated_indices(self):
        """Loc indices co tenant isolation (KPI-029)."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="a", provider=SearchProviderType.ELASTICSEARCH, tenant_isolated=True))
        collection.add_index(SearchIndex(id="b", provider=SearchProviderType.ELASTICSEARCH, tenant_isolated=False))
        result = collection.tenant_isolated_indices()
        assert len(result) == 1

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="main", provider=SearchProviderType.ELASTICSEARCH))
        d = collection.to_dict()
        restored = SearchCollection.from_dict(d)
        assert restored.total_count == 1


# ============================================================================
# Test Search Parser
# ============================================================================


class TestSearchParser:
    """Tests cho SearchParser."""

    def test_parse_indices(self):
        """Parse search indices tu metadata."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "products",
                    "provider": "elasticsearch",
                    "tenant_isolated": True,
                    "columns": [
                        {"name": "name", "type": "text", "searchable": True},
                    ],
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 1

    def test_parse_empty_metadata(self):
        """Parse empty metadata."""
        parser = SearchParser()
        collection = parser.parse_from_metadata({})
        assert collection.total_count == 0


# ============================================================================
# Test FastAPI Search Emitter
# ============================================================================


class TestElasticsearchEmitter:
    """Tests cho ElasticsearchEmitter (FastAPI)."""

    def test_emit_creates_files(self, tmp_path: Path):
        """Emit tao cac file search."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))

        emitter = ElasticsearchEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)

    def test_emit_includes_tenant(self, tmp_path: Path):
        """Emit bao gom tenant isolation (KPI-029)."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="orders", provider=SearchProviderType.ELASTICSEARCH, tenant_isolated=True))

        emitter = ElasticsearchEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong."""
        emitter = ElasticsearchEmitter()
        files = emitter.emit(SearchCollection(), tmp_path)
        assert isinstance(files, dict)


# ============================================================================
# Test NestJS Search Emitter
# ============================================================================


class TestSearchModuleEmitter:
    """Tests cho SearchModuleEmitter (NestJS)."""

    def test_emit_creates_module(self, tmp_path: Path):
        """Emit tao search module."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products", provider=SearchProviderType.ELASTICSEARCH))

        emitter = SearchModuleEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong."""
        emitter = SearchModuleEmitter()
        files = emitter.emit(SearchCollection(), tmp_path)
        assert isinstance(files, dict)


# ============================================================================
# KPI-029 Tenant Isolation Tests
# ============================================================================


class TestKPI029SearchTenantIsolation:
    """Tests KPI-029: Tenant Isolation cho search templates."""

    def test_fastapi_elasticsearch_template_has_tenant(self):
        """FastAPI elasticsearch.py.jinja2 co tenant index prefix."""
        template_path = Path("midicoder/stacks/fastapi/templates/search/elasticsearch.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_index_manager_has_tenant(self):
        """FastAPI index_manager.py.jinja2 co tenant isolation."""
        template_path = Path("midicoder/stacks/fastapi/templates/search/index_manager.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_search_service_has_tenant(self):
        """FastAPI search_service.py.jinja2 co tenant awareness."""
        template_path = Path("midicoder/stacks/fastapi/templates/search/search_service.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_index_default_tenant_isolated(self):
        """SearchIndex mac dinh tenant_isolated=True (KPI-029)."""
        index = SearchIndex(id="test", provider=SearchProviderType.ELASTICSEARCH)
        assert index.tenant_isolated is True

    def test_provider_enum_coverage(self):
        """SearchProviderType enum co cac providers."""
        assert SearchProviderType.ELASTICSEARCH.value == "elasticsearch"
        assert SearchProviderType.MEILISEARCH.value == "meilisearch"

    def test_sync_strategy_enum_coverage(self):
        """SyncStrategy enum co cac strategies."""
        assert SyncStrategy.REALTIME.value == "realtime"
        assert SyncStrategy.NEAR_REALTIME.value == "near_realtime"
        assert SyncStrategy.BATCH.value == "batch"

    def test_sync_trigger_enum_coverage(self):
        """SyncTrigger enum co cac triggers."""
        assert SyncTrigger.EVENT.value == "event"
        assert SyncTrigger.POLLING.value == "polling"

    def test_index_with_all_attributes(self):
        """SearchIndex voi tat ca attributes."""
        index = SearchIndex(
            id="full",
            provider=SearchProviderType.ELASTICSEARCH,
            columns=[
                SearchIndexColumn(name="title", column_type="text", searchable=True),
                SearchIndexColumn(name="tags", column_type="keyword", filterable=True),
            ],
            sync_strategy=SyncStrategy.NEAR_REALTIME,
            sync_trigger=SyncTrigger.EVENT,
            tenant_isolated=True,
            description="Index day du",
        )
        d = index.to_dict()
        restored = SearchIndex.from_dict(d)
        assert len(restored.columns) == 2

    def test_full_collection_roundtrip(self):
        """Full roundtrip cho SearchCollection."""
        collection = SearchCollection()
        collection.add_index(
            SearchIndex(
                id="main",
                provider=SearchProviderType.ELASTICSEARCH,
                tenant_isolated=True,
                sync_strategy=SyncStrategy.REALTIME,
            )
        )
        d = collection.to_dict()
        restored = SearchCollection.from_dict(d)
        assert restored.total_count == 1

    def test_all_fastapi_search_templates_have_tenant(self):
        """Tat ca FastAPI search templates co tenant reference."""
        search_dir = Path("midicoder/stacks/fastapi/templates/search")
        if search_dir.exists():
            for template in search_dir.glob("*.jinja2"):
                content = template.read_text(encoding="utf-8")
                assert "tenant" in content.lower(), f"Template {template.name} missing tenant reference"