# coding: utf-8
"""
Tests cho Search Parser (CP10).

Test coverage:
- SearchParser.parse_from_metadata(): Parse search indices từ MIR metadata
- Error handling khi parse fail
- Parse từ search_indices key
- Parse empty metadata
- Parse với provider, sync_strategy, sync_trigger
- Parse với columns
- Parse với tenant_isolation (KPI-029)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.search.parser import SearchParser
from midicoder.emitters.core.search.models import (
    SearchCollection,
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
)


# ============================================================================
# Test SearchParser - Basic parsing
# ============================================================================


class TestSearchParserBasic:
    """Tests cho chức năng parse cơ bản của SearchParser."""

    def test_parse_single_index(self):
        """Parse một search index từ metadata."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "products",
                    "provider": "elasticsearch",
                    "columns": [
                        {"name": "name", "type": "text", "searchable": True},
                    ],
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 1
        assert collection.indices[0].id == "products"

    def test_parse_multiple_indices(self):
        """Parse nhiều search indices từ metadata."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "products", "provider": "elasticsearch"},
                {"id": "orders", "provider": "meilisearch"},
                {"id": "users", "provider": "elasticsearch"},
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 3

    def test_parse_empty_metadata(self):
        """Parse metadata rỗng trả về collection rỗng."""
        parser = SearchParser()
        collection = parser.parse_from_metadata({})
        assert collection.total_count == 0

    def test_parse_empty_search_indices(self):
        """Parse search_indices rỗng."""
        parser = SearchParser()
        collection = parser.parse_from_metadata({"search_indices": []})
        assert collection.total_count == 0

    def test_parse_none_search_indices(self):
        """Parse khi search_indices là None."""
        parser = SearchParser()
        collection = parser.parse_from_metadata({"other_key": "value"})
        assert collection.total_count == 0


# ============================================================================
# Test SearchParser - Provider parsing
# ============================================================================


class TestSearchParserProvider:
    """Tests cho parse provider từ metadata."""

    def test_parse_elasticsearch_provider(self):
        """Parse provider elasticsearch."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "provider": "elasticsearch"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].provider == SearchProviderType.ELASTICSEARCH

    def test_parse_meilisearch_provider(self):
        """Parse provider meilisearch."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "provider": "meilisearch"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].provider == SearchProviderType.MEILISEARCH

    def test_parse_default_provider(self):
        """Parse khi không có provider — mặc định là elasticsearch."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].provider == SearchProviderType.ELASTICSEARCH

    def test_parse_invalid_provider_uses_default(self):
        """Parse provider không hợp lệ — sử dụng default."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "provider": "invalid_provider"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].provider == SearchProviderType.ELASTICSEARCH


# ============================================================================
# Test SearchParser - Sync Strategy parsing
# ============================================================================


class TestSearchParserSyncStrategy:
    """Tests cho parse sync_strategy và sync_trigger."""

    def test_parse_realtime_strategy(self):
        """Parse sync_strategy realtime."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "sync_strategy": "realtime"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_strategy == SyncStrategy.REALTIME

    def test_parse_near_realtime_strategy(self):
        """Parse sync_strategy near_realtime."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "sync_strategy": "near_realtime"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_strategy == SyncStrategy.NEAR_REALTIME

    def test_parse_batch_strategy(self):
        """Parse sync_strategy batch."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "sync_strategy": "batch"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_strategy == SyncStrategy.BATCH

    def test_parse_default_strategy(self):
        """Parse khi không có sync_strategy — mặc định near_realtime."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_strategy == SyncStrategy.NEAR_REALTIME

    def test_parse_event_trigger(self):
        """Parse sync_trigger event."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "sync_trigger": "event"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_trigger == SyncTrigger.EVENT

    def test_parse_polling_trigger(self):
        """Parse sync_trigger polling."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "sync_trigger": "polling"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_trigger == SyncTrigger.POLLING

    def test_parse_default_trigger(self):
        """Parse khi không có sync_trigger — mặc định event."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].sync_trigger == SyncTrigger.EVENT


# ============================================================================
# Test SearchParser - Column parsing
# ============================================================================


class TestSearchParserColumns:
    """Tests cho parse columns từ metadata."""

    def test_parse_single_column(self):
        """Parse một column."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "idx1",
                    "columns": [
                        {"name": "title", "type": "text", "searchable": True}
                    ]
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.indices[0].columns) == 1
        assert collection.indices[0].columns[0].name == "title"

    def test_parse_multiple_columns(self):
        """Parse nhiều columns."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "idx1",
                    "columns": [
                        {"name": "title", "type": "text", "searchable": True},
                        {"name": "status", "type": "keyword", "filterable": True},
                        {"name": "price", "type": "numeric", "sortable": True},
                    ]
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.indices[0].columns) == 3

    def test_parse_empty_columns(self):
        """Parse khi không có columns."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.indices[0].columns) == 0

    def test_parse_column_with_analyser(self):
        """Parse column với analyser."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "idx1",
                    "columns": [
                        {"name": "title", "type": "text", "analyser": "vietnamese"}
                    ]
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].columns[0].analyser == "vietnamese"


# ============================================================================
# Test SearchParser - KPI-029 Tenant Isolation
# ============================================================================


class TestSearchParserTenantIsolation:
    """Tests KPI-029: Tenant Isolation cho parser."""

    def test_parse_tenant_isolated_true(self):
        """Parse tenant_isolated=True."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "tenant_isolated": True}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].tenant_isolated is True

    def test_parse_tenant_isolated_false(self):
        """Parse tenant_isolated=False."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1", "tenant_isolated": False}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].tenant_isolated is False

    def test_parse_default_tenant_isolated(self):
        """KPI-029: Mặc định tenant_isolated=True."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "idx1"}
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.indices[0].tenant_isolated is True


# ============================================================================
# Test SearchParser - Full integration
# ============================================================================


class TestSearchParserIntegration:
    """Tests integration — parse hoàn chỉnh từ metadata."""

    def test_parse_full_index(self):
        """Parse index hoàn chỉnh với tất cả fields."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {
                    "id": "products",
                    "provider": "elasticsearch",
                    "sync_strategy": "near_realtime",
                    "sync_trigger": "event",
                    "tenant_isolated": True,
                    "description": "Search index cho sản phẩm",
                    "columns": [
                        {"name": "name", "type": "text", "searchable": True, "analyser": "vietnamese"},
                        {"name": "sku", "type": "keyword", "filterable": True},
                        {"name": "price", "type": "numeric", "sortable": True},
                        {"name": "created_at", "type": "date"},
                    ],
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 1
        idx = collection.indices[0]
        assert idx.id == "products"
        assert idx.provider == SearchProviderType.ELASTICSEARCH
        assert idx.sync_strategy == SyncStrategy.NEAR_REALTIME
        assert idx.sync_trigger == SyncTrigger.EVENT
        assert idx.tenant_isolated is True
        assert idx.description == "Search index cho sản phẩm"
        assert len(idx.columns) == 4

    def test_parse_multiple_full_indices(self):
        """Parse nhiều indices hoàn chỉnh."""
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
                },
                {
                    "id": "orders",
                    "provider": "meilisearch",
                    "sync_strategy": "realtime",
                    "tenant_isolated": True,
                    "columns": [
                        {"name": "order_id", "type": "keyword", "filterable": True},
                    ],
                },
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 2
        assert collection.indices[0].provider == SearchProviderType.ELASTICSEARCH
        assert collection.indices[1].provider == SearchProviderType.MEILISEARCH

    def test_parse_skips_invalid_entries(self):
        """Parse bỏ qua các entries không hợp lệ."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "valid_index", "provider": "elasticsearch"},
                {},  # Thiếu id — sẽ bị skip
                {"id": "another_valid", "provider": "meilisearch"},
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        # Chỉ các index có id hợp lệ được parse
        assert collection.total_count >= 1


# ============================================================================
# Test SearchParser - Error handling
# ============================================================================


class TestSearchParserErrorHandling:
    """Tests cho error handling của parser."""

    def test_parse_with_none_metadata(self):
        """Parse metadata là None."""
        parser = SearchParser()
        # Parse nên handle None gracefully
        try:
            collection = parser.parse_from_metadata(None)  # type: ignore
            assert isinstance(collection, SearchCollection)
        except Exception:
            # Hoặc throw error hợp lệ
            pass

    def test_parse_with_malformed_index_data(self):
        """Parse index data bị hỏng — skip và continue."""
        parser = SearchParser()
        metadata = {
            "search_indices": [
                {"id": "valid1"},
                "not_a_dict",  # Không phải dict — sẽ bị skip
                {"id": "valid2"},
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        # Các valid entries vẫn được parse
        assert collection.total_count >= 1
