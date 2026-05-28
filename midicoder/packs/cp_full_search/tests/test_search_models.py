# coding: utf-8
"""
Tests cho Search & Indexing models (CP10).

Test coverage:
- SearchProviderType enum
- SyncStrategy enum
- SyncTrigger enum
- SearchIndexColumn: __post_init__ validation, to_dict, from_dict
- SearchIndex: __post_init__ validation, KPI-029 tenant isolation, to_dict, from_dict
- SearchCollection: add_index, get_by_id, tenant_isolated_indices, to_dict, from_dict
- Error codes: MDC-CP10-001 ~ MDC-CP10-005

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_search.models import (
    AggregationFunction,
    Facet,
    FacetedSearchIndex,
    FacetType,
    GeoOperation,
    GeoSearchColumn,
    GeoSearchIndex,
    SearchCollection,
    SearchIndex,
    SearchIndexColumn,
    SearchProviderType,
    SearchQuery,
    SearchQueryType,
    SyncStrategy,
    SyncTrigger,
    VectorIndexColumn,
    VectorIndexType,
    VectorSearchIndex,
    VectorSimilarityMetric,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test SearchProviderType Enum
# ============================================================================


class TestSearchProviderType:
    """Tests cho SearchProviderType enum."""

    def test_elasticsearch_value(self):
        """Kiểm tra giá trị Elasticsearch."""
        assert SearchProviderType.ELASTICSEARCH.value == "elasticsearch"

    def test_meilisearch_value(self):
        """Kiểm tra giá trị MeiliSearch."""
        assert SearchProviderType.MEILISEARCH.value == "meilisearch"

    def test_from_string_elasticsearch(self):
        """Tạo từ string elasticsearch."""
        provider = SearchProviderType("elasticsearch")
        assert provider == SearchProviderType.ELASTICSEARCH

    def test_from_string_meilisearch(self):
        """Tạo từ string meilisearch."""
        provider = SearchProviderType("meilisearch")
        assert provider == SearchProviderType.MEILISEARCH

    def test_invalid_provider_raises(self):
        """Provider không hợp lệ throw error."""
        with pytest.raises(ValueError):
            SearchProviderType("invalid_provider")


# ============================================================================
# Test SyncStrategy Enum
# ============================================================================


class TestSyncStrategy:
    """Tests cho SyncStrategy enum."""

    def test_realtime_value(self):
        """Kiểm tra giá trị realtime."""
        assert SyncStrategy.REALTIME.value == "realtime"

    def test_near_realtime_value(self):
        """Kiểm tra giá trị near_realtime."""
        assert SyncStrategy.NEAR_REALTIME.value == "near_realtime"

    def test_batch_value(self):
        """Kiểm tra giá trị batch."""
        assert SyncStrategy.BATCH.value == "batch"

    def test_from_string(self):
        """Tạo từ string."""
        assert SyncStrategy("near_realtime") == SyncStrategy.NEAR_REALTIME

    def test_invalid_strategy_raises(self):
        """Strategy không hợp lệ throw error."""
        with pytest.raises(ValueError):
            SyncStrategy("invalid_strategy")


# ============================================================================
# Test SyncTrigger Enum
# ============================================================================


class TestSyncTrigger:
    """Tests cho SyncTrigger enum."""

    def test_event_value(self):
        """Kiểm tra giá trị event."""
        assert SyncTrigger.EVENT.value == "event"

    def test_polling_value(self):
        """Kiểm tra giá trị polling."""
        assert SyncTrigger.POLLING.value == "polling"

    def test_from_string(self):
        """Tạo từ string."""
        assert SyncTrigger("event") == SyncTrigger.EVENT


# ============================================================================
# Test SearchIndexColumn
# ============================================================================


class TestSearchIndexColumnValidation:
    """Tests cho validation __post_init__ của SearchIndexColumn."""

    def test_valid_text_column(self):
        """Tạo text column hợp lệ."""
        col = SearchIndexColumn(
            name="title",
            column_type="text",
            searchable=True,
        )
        assert col.name == "title"
        assert col.column_type == "text"
        assert col.searchable is True

    def test_valid_keyword_column(self):
        """Tạo keyword column hợp lệ."""
        col = SearchIndexColumn(
            name="status",
            column_type="keyword",
            filterable=True,
        )
        assert col.filterable is True

    def test_valid_numeric_column(self):
        """Tạo numeric column hợp lệ."""
        col = SearchIndexColumn(
            name="price",
            column_type="numeric",
            sortable=True,
        )
        assert col.sortable is True

    def test_valid_date_column(self):
        """Tạo date column hợp lệ."""
        col = SearchIndexColumn(
            name="created_at",
            column_type="date",
            sortable=True,
        )
        assert col.column_type == "date"

    def test_valid_geo_column(self):
        """Tạo geo column hợp lệ."""
        col = SearchIndexColumn(
            name="location",
            column_type="geo",
        )
        assert col.column_type == "geo"

    def test_empty_name_raises_error(self):
        """Tên column rỗng throw MDC-CP10-001."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndexColumn(name="", column_type="text")
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_empty_column_name_raises_error(self):
        """Tên column là whitespace throw MDC-CP10-001."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndexColumn(name="   ", column_type="text")
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_invalid_column_type_raises_error(self):
        """Column type không hợp lệ throw MDC-CP10-004."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndexColumn(name="field", column_type="invalid_type")
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_column_type_boolean_invalid(self):
        """Column type boolean không hợp lệ."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndexColumn(name="active", column_type="boolean")
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_defaults(self):
        """Kiểm tra giá trị mặc định của column."""
        col = SearchIndexColumn(name="description")
        assert col.column_type == "text"
        assert col.searchable is False
        assert col.filterable is False
        assert col.sortable is False
        assert col.analyser == ""
        assert col.description == ""


class TestSearchIndexColumnSerialization:
    """Tests cho to_dict/from_dict của SearchIndexColumn."""

    def test_to_dict(self):
        """Chuyển column sang dict."""
        col = SearchIndexColumn(
            name="title",
            column_type="text",
            searchable=True,
            analyser="vietnamese",
        )
        d = col.to_dict()
        assert d["name"] == "title"
        assert d["type"] == "text"
        assert d["searchable"] is True
        assert d["analyser"] == "vietnamese"

    def test_from_dict(self):
        """Tạo column từ dict."""
        d = {
            "name": "tags",
            "type": "keyword",
            "filterable": True,
            "analyser": "",
        }
        col = SearchIndexColumn.from_dict(d)
        assert col.name == "tags"
        assert col.column_type == "keyword"
        assert col.filterable is True

    def test_from_dict_with_column_type_key(self):
        """Tạo column từ dict dùng key column_type."""
        d = {
            "name": "price",
            "column_type": "numeric",
            "sortable": True,
        }
        col = SearchIndexColumn.from_dict(d)
        assert col.column_type == "numeric"

    def test_roundtrip(self):
        """Roundtrip to_dict → from_dict."""
        original = SearchIndexColumn(
            name="description",
            column_type="text",
            searchable=True,
            filterable=False,
            sortable=False,
            analyser="vietnamese",
            description="Mo ta san pham",
        )
        d = original.to_dict()
        restored = SearchIndexColumn.from_dict(d)
        assert restored.name == original.name
        assert restored.column_type == original.column_type
        assert restored.searchable == original.searchable
        assert restored.analyser == original.analyser


# ============================================================================
# Test SearchIndex
# ============================================================================


class TestSearchIndexValidation:
    """Tests cho validation __post_init__ của SearchIndex."""

    def test_valid_basic_index(self):
        """Tao search index co ban hop le."""
        index = SearchIndex(
            id="products",
            provider=SearchProviderType.ELASTICSEARCH,
        )
        assert index.id == "products"
        assert index.provider == SearchProviderType.ELASTICSEARCH

    def test_valid_meilisearch_index(self):
        """Tao search index voi MeiliSearch."""
        index = SearchIndex(
            id="articles",
            provider=SearchProviderType.MEILISEARCH,
        )
        assert index.provider == SearchProviderType.MEILISEARCH

    def test_default_tenant_isolated_true(self):
        """KPI-029: tenant_isolated mac dinh la True."""
        index = SearchIndex(id="orders")
        assert index.tenant_isolated is True

    def test_explicit_tenant_isolated_false(self):
        """Seet tenant_isolated = False."""
        index = SearchIndex(id="public_data", tenant_isolated=False)
        assert index.tenant_isolated is False

    def test_default_sync_strategy(self):
        """Sync strategy mac dinh la near_realtime."""
        index = SearchIndex(id="data")
        assert index.sync_strategy == SyncStrategy.NEAR_REALTIME

    def test_default_sync_trigger(self):
        """Sync trigger mac dinh la event."""
        index = SearchIndex(id="data")
        assert index.sync_trigger == SyncTrigger.EVENT

    def test_empty_id_raises_error(self):
        """Index id rong throw MDC-CP10-001."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndex(id="")
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_whitespace_id_raises_error(self):
        """Index id la whitespace throw MDC-CP10-001."""
        with pytest.raises(MidicoderError) as exc_info:
            SearchIndex(id="   ")
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_valid_with_columns(self):
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

    def test_all_attributes(self):
        """Tao search index voi tat ca attributes."""
        index = SearchIndex(
            id="full_index",
            provider=SearchProviderType.ELASTICSEARCH,
            columns=[SearchIndexColumn(name="name", column_type="text", searchable=True)],
            sync_strategy=SyncStrategy.REALTIME,
            sync_trigger=SyncTrigger.EVENT,
            tenant_isolated=True,
            description="Index day du cac thuoc tinh",
        )
        assert index.id == "full_index"
        assert index.sync_strategy == SyncStrategy.REALTIME
        assert index.sync_trigger == SyncTrigger.EVENT
        assert index.tenant_isolated is True


class TestSearchIndexSerialization:
    """Tests cho to_dict/from_dict cua SearchIndex."""

    def test_to_dict(self):
        """Chuyen index sang dict."""
        index = SearchIndex(
            id="users",
            provider=SearchProviderType.ELASTICSEARCH,
            columns=[
                SearchIndexColumn(name="name", column_type="text", searchable=True),
            ],
            tenant_isolated=True,
            description="Search index cho users",
        )
        d = index.to_dict()
        assert d["id"] == "users"
        assert d["provider"] == "elasticsearch"
        assert d["tenant_isolated"] is True
        assert len(d["columns"]) == 1

    def test_from_dict(self):
        """Tao index tu dict."""
        d = {
            "id": "products",
            "provider": "elasticsearch",
            "sync_strategy": "realtime",
            "sync_trigger": "polling",
            "tenant_isolated": False,
            "columns": [
                {"name": "sku", "type": "keyword", "filterable": True},
            ],
        }
        index = SearchIndex.from_dict(d)
        assert index.id == "products"
        assert index.sync_strategy == SyncStrategy.REALTIME
        assert index.sync_trigger == SyncTrigger.POLLING
        assert index.tenant_isolated is False
        assert len(index.columns) == 1

    def test_from_dict_defaults(self):
        """Tao index tu dict voi cac gia tri mac dinh."""
        d = {"id": "minimal"}
        index = SearchIndex.from_dict(d)
        assert index.provider == SearchProviderType.ELASTICSEARCH
        assert index.sync_strategy == SyncStrategy.NEAR_REALTIME
        assert index.tenant_isolated is True

    def test_roundtrip(self):
        """Roundtrip to_dict -> from_dict."""
        original = SearchIndex(
            id="orders",
            provider=SearchProviderType.MEILISEARCH,
            columns=[
                SearchIndexColumn(name="order_id", column_type="keyword", filterable=True),
                SearchIndexColumn(name="total", column_type="numeric", sortable=True),
            ],
            sync_strategy=SyncStrategy.BATCH,
            sync_trigger=SyncTrigger.POLLING,
            tenant_isolated=True,
            description="Don hang",
        )
        d = original.to_dict()
        restored = SearchIndex.from_dict(d)
        assert restored.id == original.id
        assert restored.provider == original.provider
        assert restored.sync_strategy == original.sync_strategy
        assert restored.tenant_isolated == original.tenant_isolated
        assert len(restored.columns) == len(original.columns)


# ============================================================================
# Test SearchCollection
# ============================================================================


class TestSearchCollection:
    """Tests cho SearchCollection."""

    def test_empty_collection(self):
        """Collection rong mac dinh."""
        collection = SearchCollection()
        assert collection.total_count == 0
        assert len(collection.indices) == 0

    def test_add_index(self):
        """Them index vao collection."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))
        assert collection.total_count == 1

    def test_add_multiple_indices(self):
        """Them nhieu indices."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))
        collection.add_index(SearchIndex(id="orders"))
        collection.add_index(SearchIndex(id="users"))
        assert collection.total_count == 3

    def test_get_by_id_found(self):
        """Tim index theo ID thanh cong."""
        collection = SearchCollection()
        idx = SearchIndex(id="articles", provider=SearchProviderType.MEILISEARCH)
        collection.add_index(idx)
        found = collection.get_by_id("articles")
        assert found is not None
        assert found.id == "articles"
        assert found.provider == SearchProviderType.MEILISEARCH

    def test_get_by_id_not_found(self):
        """Tim index theo ID khong tim thay."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="products"))
        found = collection.get_by_id("nonexistent")
        assert found is None

    def test_tenant_isolated_indices(self):
        """KPI-029: Loc cac indices co tenant isolation."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="a", tenant_isolated=True))
        collection.add_index(SearchIndex(id="b", tenant_isolated=False))
        collection.add_index(SearchIndex(id="c", tenant_isolated=True))
        result = collection.tenant_isolated_indices()
        assert len(result) == 2
        assert all(i.tenant_isolated for i in result)

    def test_tenant_isolated_indices_all_false(self):
        """KPI-029: Tat ca indices khong co tenant isolation."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="public1", tenant_isolated=False))
        collection.add_index(SearchIndex(id="public2", tenant_isolated=False))
        result = collection.tenant_isolated_indices()
        assert len(result) == 0

    def test_tenant_isolated_indices_default_true(self):
        """KPI-029: Mac dinh tenant_isolated = True nen tat ca duoc loc."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="auto1"))
        collection.add_index(SearchIndex(id="auto2"))
        result = collection.tenant_isolated_indices()
        assert len(result) == 2


class TestSearchCollectionSerialization:
    """Tests cho to_dict/from_dict cua SearchCollection."""

    def test_to_dict_empty(self):
        """Chuyen collection rong sang dict."""
        collection = SearchCollection()
        d = collection.to_dict()
        assert d == {
            "indices": [],
            "vector_indices": [],
            "geo_indices": [],
            "faceted_indices": [],
            "queries": [],
        }

    def test_to_dict_with_indices(self):
        """Chuyen collection co indices sang dict."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="main", provider=SearchProviderType.ELASTICSEARCH))
        d = collection.to_dict()
        assert len(d["indices"]) == 1
        assert d["indices"][0]["id"] == "main"

    def test_from_dict(self):
        """Tao collection tu dict."""
        d = {
            "indices": [
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
                    "sync_strategy": "batch",
                },
            ],
        }
        collection = SearchCollection.from_dict(d)
        assert collection.total_count == 2
        assert collection.indices[0].id == "products"
        assert collection.indices[1].id == "orders"

    def test_from_dict_empty(self):
        """Tao collection tu dict rong."""
        d = {"indices": []}
        collection = SearchCollection.from_dict(d)
        assert collection.total_count == 0

    def test_roundtrip(self):
        """Roundtrip to_dict -> from_dict."""
        collection = SearchCollection()
        collection.add_index(
            SearchIndex(
                id="main",
                provider=SearchProviderType.ELASTICSEARCH,
                tenant_isolated=True,
                sync_strategy=SyncStrategy.REALTIME,
                columns=[
                    SearchIndexColumn(name="title", column_type="text", searchable=True),
                ],
            )
        )
        d = collection.to_dict()
        restored = SearchCollection.from_dict(d)
        assert restored.total_count == 1
        assert restored.indices[0].id == "main"
        assert restored.indices[0].tenant_isolated is True
        assert len(restored.indices[0].columns) == 1


# ============================================================================
# KPI-029 Tenant Isolation Integration Tests
# ============================================================================


class TestKPI029TenantIsolation:
    """Tests KPI-029: Tenant Isolation cho search models."""

    def test_index_default_tenant_isolated(self):
        """SearchIndex mac dinh tenant_isolated=True (KPI-029)."""
        index = SearchIndex(id="test")
        assert index.tenant_isolated is True

    def test_collection_only_tenant_isolated(self):
        """Collection chi tra ve indices co tenant isolation."""
        collection = SearchCollection()
        collection.add_index(SearchIndex(id="secure", tenant_isolated=True))
        collection.add_index(SearchIndex(id="open", tenant_isolated=False))
        tenant_indices = collection.tenant_isolated_indices()
        assert len(tenant_indices) == 1
        assert tenant_indices[0].id == "secure"

    def test_serialization_preserves_tenant_isolation(self):
        """Serialization giữ nguyên tenant_isolation flag."""
        index = SearchIndex(id="orders", tenant_isolated=True)
        d = index.to_dict()
        restored = SearchIndex.from_dict(d)
        assert restored.tenant_isolated is True

    def test_serialization_preserves_tenant_non_isolated(self):
        """Serialization giữ nguyên tenant_isolated=False."""
        index = SearchIndex(id="public", tenant_isolated=False)
        d = index.to_dict()
        restored = SearchIndex.from_dict(d)
        assert restored.tenant_isolated is False


# ============================================================================
# Error Code Tests
# ============================================================================


class TestCP10ErrorCodes:
    """Tests cho CP10 error codes trong ErrorCode enum."""

    def test_error_code_enum_exists(self):
        """Kiểm tra CP10 error codes tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP10_EMPTY_INDEX_NAME")
        assert hasattr(ErrorCode, "CP10_INVALID_PROVIDER")
        assert hasattr(ErrorCode, "CP10_SYNC_STRATEGY_INVALID")
        assert hasattr(ErrorCode, "CP10_INVALID_COLUMN_TYPE")
        assert hasattr(ErrorCode, "CP10_INDEX_CREATE_FAILED")

    def test_error_code_values(self):
        """Kiểm tra giá trị của CP10 error codes."""
        assert ErrorCode.MDC-F08_EMPTY_INDEX_NAME.value == "MDC-CP10-001"
        assert ErrorCode.MDC-F08_INVALID_PROVIDER.value == "MDC-CP10-002"
        assert ErrorCode.MDC-F08_SYNC_STRATEGY_INVALID.value == "MDC-CP10-003"
        assert ErrorCode.MDC-F08_INVALID_COLUMN_TYPE.value == "MDC-CP10-004"
        assert ErrorCode.MDC-F08_INDEX_CREATE_FAILED.value == "MDC-CP10-005"
