# coding: utf-8
"""
CP10 Search & Indexing — Recipe Presets.

Module này cung cấp các recipe presets — cách gán giá trị cụ thể vào
pattern vocabulary của CP10. Recipe là "common way to wire up patterns",
không phải domain-specific macro.

Mỗi recipe là một hàm trả về model đã được cấu hình sẵn với các giá trị
khuyến nghị. User có thể override bất kỳ tham số nào.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp_full_search.models import (
    AggregationFunction,
    Facet,
    FacetedSearchIndex,
    FacetType,
    GeoOperation,
    GeoSearchColumn,
    GeoSearchIndex,
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


# ===========================================================================
# Provider Recipes — gán concrete values vào SearchIndex pattern
# ===========================================================================


def elasticsearch_recipe(
    index_id: str = "default_index",
    vector_support: bool = False,
    geo_support: bool = False,
    tenant_isolated: bool = True,
    sync_strategy: SyncStrategy = SyncStrategy.NEAR_REALTIME,
    sync_trigger: SyncTrigger = SyncTrigger.EVENT,
    columns: list[SearchIndexColumn] | None = None,
    description: str = "",
) -> SearchIndex:
    """
    Elasticsearch recipe — cấu hình mặc định cho Elasticsearch 8.x.

    Args:
        index_id: Định danh duy nhất của index.
        vector_support: Có hỗ trợ vector search không (yêu cầu ES 8+).
        geo_support: Có hỗ trợ geospatial search không.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        sync_strategy: Strategy đồng bộ data.
        sync_trigger: Trigger cho synchronization.
        columns: Danh sách columns tùy chỉnh.
        description: Mô tả index.

    Returns:
        SearchIndex đã cấu hình sẵn cho Elasticsearch.
    """
    default_columns: list[SearchIndexColumn] = columns or []

    if vector_support and not any(c.column_type == "vector" for c in default_columns):
        default_columns.append(SearchIndexColumn(
            name="_vector",
            column_type="vector",
            searchable=True,
            description="Embedding vector cho semantic search",
        ))

    if geo_support and not any(c.column_type == "geo" for c in default_columns):
        default_columns.append(SearchIndexColumn(
            name="location",
            column_type="geo",
            searchable=True,
            filterable=True,
            description="Vị trí geospatial",
        ))

    return SearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        columns=default_columns,
        sync_strategy=sync_strategy,
        sync_trigger=sync_trigger,
        tenant_isolated=tenant_isolated,
        description=description or f"Elasticsearch index: {index_id}",
    )


def meilisearch_recipe(
    index_id: str = "default_index",
    tenant_isolated: bool = True,
    sync_strategy: SyncStrategy = SyncStrategy.REALTIME,
    sync_trigger: SyncTrigger = SyncTrigger.EVENT,
    columns: list[SearchIndexColumn] | None = None,
    description: str = "",
) -> SearchIndex:
    """
    Meilisearch recipe — cấu hình mặc định cho MeiliSearch.

    Meilisearch là lightweight, fast full-text search engine.

    Args:
        index_id: Định danh duy nhất của index.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        sync_strategy: Strategy đồng bộ data.
        sync_trigger: Trigger cho synchronization.
        columns: Danh sách columns tùy chỉnh.
        description: Mô tả index.

    Returns:
        SearchIndex đã cấu hình sẵn cho MeiliSearch.
    """
    return SearchIndex(
        id=index_id,
        provider=SearchProviderType.MEILISEARCH,
        columns=columns or [],
        sync_strategy=sync_strategy,
        sync_trigger=sync_trigger,
        tenant_isolated=tenant_isolated,
        description=description or f"MeiliSearch index: {index_id}",
    )


def opensearch_recipe(
    index_id: str = "default_index",
    tenant_isolated: bool = True,
    sync_strategy: SyncStrategy = SyncStrategy.NEAR_REALTIME,
    columns: list[SearchIndexColumn] | None = None,
    description: str = "",
) -> SearchIndex:
    """
    OpenSearch recipe — tương thích Elasticsearch (OpenSearch là fork của ES).

    Dùng Elasticsearch provider vì OpenSearch API tương thích.

    Args:
        index_id: Định danh duy nhất của index.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        sync_strategy: Strategy đồng bộ data.
        columns: Danh sách columns tùy chỉnh.
        description: Mô tả index.

    Returns:
        SearchIndex đã cấu hình sẵn cho OpenSearch.
    """
    return SearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        columns=columns or [],
        sync_strategy=sync_strategy,
        sync_trigger=SyncTrigger.EVENT,
        tenant_isolated=tenant_isolated,
        description=description or f"OpenSearch index: {index_id}",
    )


# ===========================================================================
# Advanced Search Recipes
# ===========================================================================


def vector_search_recipe(
    index_id: str = "semantic_search",
    dimensions: int = 768,
    metric: VectorSimilarityMetric = VectorSimilarityMetric.COSINE,
    index_type: VectorIndexType = VectorIndexType.HNSW,
    top_k: int = 10,
    text_columns: list[SearchIndexColumn] | None = None,
    description: str = "",
) -> VectorSearchIndex:
    """
    Vector search recipe — cấu hình mặc định cho vector similarity search.

    Phù hợp cho semantic search: tìm kiếm theo ý nghĩa, không theo keyword.

    Args:
        index_id: Định danh duy nhất.
        dimensions: Số chiều vector (768 cho sentence-transformers, 1536 cho ada-002).
        metric: Metric tính toán similarity.
        index_type: Loại vector index (HNSW là chính xác nhất).
        top_k: Số kết quả trả về mặc định.
        text_columns: Các text columns để kết hợp hybrid search.
        description: Mô tả index.

    Returns:
        VectorSearchIndex đã cấu hình sẵn.
    """
    return VectorSearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        vector_column=VectorIndexColumn(
            name="_embedding",
            dimensions=dimensions,
            similarity_metric=metric,
            index_type=index_type,
            description=f"Embedding vector ({dimensions}d, {metric.value})",
        ),
        text_columns=text_columns or [],
        top_k=top_k,
        description=description or f"Vector search index ({dimensions}d, {metric.value})",
    )


def geospatial_search_recipe(
    index_id: str = "geo_search",
    geo_column_name: str = "location",
    operations: list[GeoOperation] | None = None,
    text_columns: list[SearchIndexColumn] | None = None,
    tenant_isolated: bool = True,
    description: str = "",
) -> GeoSearchIndex:
    """
    Geospatial search recipe — cấu hình mặc định cho tìm kiếm theo vị trí.

    Hỗ trợ: "cửa hàng gần tôi", "bất động sản trong khu vực".

    Args:
        index_id: Định danh duy nhất.
        geo_column_name: Tên column chứa geospatial data.
        operations: Các geospatial operations (mặc định: CIRCLE, DISTANCE).
        text_columns: Các text columns kết hợp.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả index.

    Returns:
        GeoSearchIndex đã cấu hình sẵn.
    """
    return GeoSearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        geo_column=GeoSearchColumn(
            name=geo_column_name,
            geo_type="point",
            crs="WGS84",
            searchable=True,
            filterable=True,
            description=f"Vị trí geospatial ({geo_column_name})",
        ),
        text_columns=text_columns or [],
        operations=operations or [GeoOperation.CIRCLE, GeoOperation.DISTANCE],
        tenant_isolated=tenant_isolated,
        description=description or f"Geospatial search index: {index_id}",
    )


def faceted_search_recipe(
    index_id: str = "faceted_search",
    columns: list[SearchIndexColumn] | None = None,
    facets: list[Facet] | None = None,
    tenant_isolated: bool = True,
    description: str = "",
) -> FacetedSearchIndex:
    """
    Faceted search recipe — cấu hình mặc định cho filter/explore theo nhiều chiều.

    Ví dụ: e-commerce có facets "Hãng", "Giá", "Đánh giá", "Màu sắc".

    Args:
        index_id: Định danh duy nhất.
        columns: Các columns cơ bản trong index.
        facets: Danh sách facets (nếu None sẽ tạo default facets).
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả index.

    Returns:
        FacetedSearchIndex đã cấu hình sẵn.
    """
    default_facets: list[Facet] = facets or [
        Facet(
            id="category",
            facet_type=FacetType.TERM,
            source_column="category",
            agg_function=AggregationFunction.COUNT,
            size=20,
            description="Phân loại theo danh mục",
        ),
        Facet(
            id="price_range",
            facet_type=FacetType.RANGE,
            source_column="price",
            agg_function=AggregationFunction.COUNT,
            range_bounds=[0, 100000, 500000, 1000000, 5000000],
            description="Phân loại theo mức giá",
        ),
        Facet(
            id="rating",
            facet_type=FacetType.HISTOGRAM,
            source_column="rating",
            agg_function=AggregationFunction.COUNT,
            interval="1",
            description="Phân loại theo đánh giá",
        ),
    ]

    return FacetedSearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        columns=columns or [],
        facets=default_facets,
        tenant_isolated=tenant_isolated,
        description=description or f"Faceted search index: {index_id}",
    )


# ===========================================================================
# Hybrid Search Recipe
# ===========================================================================


def hybrid_search_recipe(
    index_id: str = "hybrid_search",
    dimensions: int = 768,
    metric: VectorSimilarityMetric = VectorSimilarityMetric.COSINE,
    top_k: int = 10,
    description: str = "",
) -> VectorSearchIndex:
    """
    Hybrid search recipe — kết hợp vector + BM25 (fulltext) search.

    Hybrid search cho kết quả tốt nhất: semantic relevance + keyword matching.
    Ví dụ: tìm "áo thun nam" sẽ kết hợp cả ý nghĩa lẫn từ khóa chính xác.

    Args:
        index_id: Định danh duy nhất.
        dimensions: Số chiều vector.
        metric: Metric tính toán similarity.
        top_k: Số kết quả trả về mặc định.
        description: Mô tả index.

    Returns:
        VectorSearchIndex có cả vector column và text columns (hybrid).
    """
    return VectorSearchIndex(
        id=index_id,
        provider=SearchProviderType.ELASTICSEARCH,
        vector_column=VectorIndexColumn(
            name="_embedding",
            dimensions=dimensions,
            similarity_metric=metric,
            index_type=VectorIndexType.HNSW,
            description=f"Embedding vector ({dimensions}d, {metric.value})",
        ),
        text_columns=[
            SearchIndexColumn(
                name="title",
                column_type="text",
                searchable=True,
                analyser="vietnamese",
                description="Tiêu đề (fulltext BM25)",
            ),
            SearchIndexColumn(
                name="description",
                column_type="text",
                searchable=True,
                analyser="vietnamese",
                description="Mô tả (fulltext BM25)",
            ),
            SearchIndexColumn(
                name="tags",
                column_type="keyword",
                filterable=True,
                description="Tags (exact match)",
            ),
        ],
        top_k=top_k,
        description=description or f"Hybrid search (vector + BM25): {index_id}",
    )


# ===========================================================================
# Query Binding Recipes
# ===========================================================================


def fulltext_query_recipe(
    query_id: str = "search",
    target_index: str = "default_index",
    fields: list[str] | None = None,
    default_size: int = 20,
    tenant_isolated: bool = True,
    description: str = "",
) -> SearchQuery:
    """
    Fulltext query recipe — cấu hình mặc định cho full-text search query.

    Args:
        query_id: Định danh duy nhất.
        target_index: Tên index mục tiêu.
        fields: Các fields tham gia (nếu None thì tìm trên tất cả).
        default_size: Số kết quả trả về mặc định.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả query.

    Returns:
        SearchQuery đã cấu hình sẵn cho fulltext search.
    """
    return SearchQuery(
        id=query_id,
        query_type=SearchQueryType.FULLTEXT,
        target_index=target_index,
        fields=fields or [],
        default_size=default_size,
        tenant_isolated=tenant_isolated,
        description=description or f"Fulltext search query: {query_id}",
    )


def vector_query_recipe(
    query_id: str = "semantic_search",
    target_index: str = "semantic_search",
    default_size: int = 10,
    tenant_isolated: bool = True,
    description: str = "",
) -> SearchQuery:
    """
    Vector query recipe — cấu hình mặc định cho vector similarity query.

    Args:
        query_id: Định danh duy nhất.
        target_index: Tên vector index mục tiêu.
        default_size: Số kết quả trả về mặc định.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả query.

    Returns:
        SearchQuery đã cấu hình sẵn cho vector search.
    """
    return SearchQuery(
        id=query_id,
        query_type=SearchQueryType.VECTOR,
        target_index=target_index,
        default_size=default_size,
        tenant_isolated=tenant_isolated,
        description=description or f"Vector similarity query: {query_id}",
    )


def geo_query_recipe(
    query_id: str = "nearby_search",
    target_index: str = "geo_search",
    default_size: int = 20,
    tenant_isolated: bool = True,
    description: str = "",
) -> SearchQuery:
    """
    Geospatial query recipe — cấu hình mặc định cho tìm kiếm theo vị trí.

    Args:
        query_id: Định danh duy nhất.
        target_index: Tên geo index mục tiêu.
        default_size: Số kết quả trả về mặc định.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả query.

    Returns:
        SearchQuery đã cấu hình sẵn cho geospatial search.
    """
    return SearchQuery(
        id=query_id,
        query_type=SearchQueryType.GEO,
        target_index=target_index,
        default_size=default_size,
        tenant_isolated=tenant_isolated,
        description=description or f"Geospatial query: {query_id}",
    )


def facet_query_recipe(
    query_id: str = "faceted_explore",
    target_index: str = "faceted_search",
    default_size: int = 20,
    tenant_isolated: bool = True,
    description: str = "",
) -> SearchQuery:
    """
    Facet query recipe — cấu hình mặc định cho faceted aggregation query.

    Args:
        query_id: Định danh duy nhất.
        target_index: Tên faceted index mục tiêu.
        default_size: Số kết quả trả về mặc định.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả query.

    Returns:
        SearchQuery đã cấu hình sẵn cho faceted aggregation.
    """
    return SearchQuery(
        id=query_id,
        query_type=SearchQueryType.FACET,
        target_index=target_index,
        default_size=default_size,
        tenant_isolated=tenant_isolated,
        description=description or f"Faceted aggregation query: {query_id}",
    )


def hybrid_query_recipe(
    query_id: str = "hybrid_search",
    target_index: str = "hybrid_search",
    fields: list[str] | None = None,
    default_size: int = 10,
    tenant_isolated: bool = True,
    description: str = "",
) -> SearchQuery:
    """
    Hybrid query recipe — cấu hình mặc định cho hybrid (vector + BM25) query.

    Args:
        query_id: Định danh duy nhất.
        target_index: Tên hybrid index mục tiêu.
        fields: Các text fields tham gia BM25 phần.
        default_size: Số kết quả trả về mặc định.
        tenant_isolated: Có enforce tenant isolation không (KPI-029).
        description: Mô tả query.

    Returns:
        SearchQuery đã cấu hình sẵn cho hybrid search.
    """
    return SearchQuery(
        id=query_id,
        query_type=SearchQueryType.HYBRID,
        target_index=target_index,
        fields=fields or ["title", "description"],
        default_size=default_size,
        tenant_isolated=tenant_isolated,
        description=description or f"Hybrid search query: {query_id}",
    )


# ===========================================================================
# CP63: Search & Recommendation Engine — Recipes (merged)
# ===========================================================================


from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_search.parser import (
    RecommendationIR,
    parse_recommendation_to_ir,
)


@dataclass
class RecommendationRecipeOutput:
    """Ket qua tu recommendation recipe builder.

    Attributes:
        name: Ten recipe
        description: Mo ta recipe
        ir: RecommendationIR da build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: RecommendationIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def collaborative_filtering_recipe() -> RecommendationRecipeOutput:
    """Recipe: Collaborative filtering recommendation engine."""
    data = {
        "configs": [
            {
                "id": "cf_user_user",
                "name": "User-User Collaborative Filtering",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_cf",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 0.8,
                "history_window_days": 30,
                "exclude_viewed": True,
                "boost_categories": [],
            }
        ],
        "default_algorithm": "collaborative_filtering",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": False,
    }
    ir = parse_recommendation_to_ir(data)
    return RecommendationRecipeOutput(
        name="collaborative_filtering_recipe",
        description="Collaborative filtering — user-user CF voi product ratings",
        ir=ir,
        raw_data=data,
    )


def content_based_recipe() -> RecommendationRecipeOutput:
    """Recipe: Content-based recommendation voi item features."""
    data = {
        "configs": [
            {
                "id": "cb_content",
                "name": "Content-Based Recommendation",
                "algorithm": "content_based",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "interaction_score",
                "top_k": 10,
                "min_interactions": 3,
                "ttl_seconds": 7200,
                "cache_enabled": True,
            }
        ],
        "embeddings": [
            {
                "id": "product_embedding",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags"],
                "similarity_metric": "cosine",
                "dimension": 128,
                "auto_train": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_cb",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 1.0,
                "history_window_days": 14,
                "exclude_viewed": True,
                "boost_categories": ["electronics", "accessories"],
            }
        ],
        "default_algorithm": "content_based",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": False,
    }
    ir = parse_recommendation_to_ir(data)
    return RecommendationRecipeOutput(
        name="content_based_recipe",
        description="Content-based recommendation — item embeddings voi cosine similarity",
        ir=ir,
        raw_data=data,
    )


def hybrid_recommendation_recipe() -> RecommendationRecipeOutput:
    """Recipe: Hybrid recommendation (collaborative + content-based)."""
    data = {
        "configs": [
            {
                "id": "hybrid_primary",
                "name": "Hybrid Recommendation Engine",
                "algorithm": "hybrid",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "composite_score",
                "top_k": 15,
                "min_interactions": 5,
                "ttl_seconds": 1800,
                "cache_enabled": True,
                "metadata": {
                    "collaborative_weight": 0.7,
                    "content_weight": 0.3,
                },
            },
            {
                "id": "cf_fallback",
                "name": "Collaborative Filtering Fallback",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 15,
                "min_interactions": 10,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
        ],
        "embeddings": [
            {
                "id": "product_embedding_hybrid",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags", "brand"],
                "similarity_metric": "dot_product",
                "dimension": 256,
                "auto_train": True,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_hybrid",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 0.9,
                "history_window_days": 60,
                "exclude_viewed": True,
                "boost_categories": ["electronics", "books"],
            }
        ],
        "default_algorithm": "hybrid",
        "default_top_k": 15,
        "enable_cache": True,
        "enable_ab_testing": False,
    }
    ir = parse_recommendation_to_ir(data)
    return RecommendationRecipeOutput(
        name="hybrid_recommendation_recipe",
        description="Hybrid recommendation — collaborative 70% + content-based 30% weighted scoring",
        ir=ir,
        raw_data=data,
    )


def popularity_fallback_recipe() -> RecommendationRecipeOutput:
    """Recipe: Popularity-based fallback recommendation."""
    data = {
        "configs": [
            {
                "id": "popularity_fallback",
                "name": "Popularity Fallback",
                "algorithm": "popularity",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "view_count",
                "top_k": 20,
                "min_interactions": 0,
                "ttl_seconds": 86400,
                "cache_enabled": True,
                "metadata": {
                    "popularity_metric": "weighted_score",
                    "view_weight": 0.2,
                    "rating_weight": 0.5,
                    "purchase_weight": 0.3,
                    "time_decay_hours": 168,
                },
            }
        ],
        "default_algorithm": "popularity",
        "default_top_k": 20,
        "enable_cache": True,
        "enable_ab_testing": False,
    }
    ir = parse_recommendation_to_ir(data)
    return RecommendationRecipeOutput(
        name="popularity_fallback_recipe",
        description="Popularity-based fallback — weighted view/rating/purchase score voi time decay",
        ir=ir,
        raw_data=data,
    )


def recommendation_ab_test_recipe() -> RecommendationRecipeOutput:
    """Recipe: A/B test cho multiple recommendation strategies."""
    data = {
        "configs": [
            {
                "id": "ab_cf",
                "name": "A/B Test — Collaborative Filtering",
                "algorithm": "collaborative_filtering",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "rating",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
            {
                "id": "ab_cb",
                "name": "A/B Test — Content-Based",
                "algorithm": "content_based",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "interaction_score",
                "top_k": 10,
                "min_interactions": 3,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
            {
                "id": "ab_hybrid",
                "name": "A/B Test — Hybrid",
                "algorithm": "hybrid",
                "item_entity": "Product",
                "user_entity": "User",
                "rating_field": "composite_score",
                "top_k": 10,
                "min_interactions": 5,
                "ttl_seconds": 3600,
                "cache_enabled": True,
            },
        ],
        "embeddings": [
            {
                "id": "ab_product_embedding",
                "item_type": "product",
                "embedding_fields": ["name", "description", "category", "tags"],
                "similarity_metric": "cosine",
                "dimension": 128,
                "auto_train": True,
            }
        ],
        "ab_tests": [
            {
                "id": "rec_algo_comparison",
                "name": "Recommendation Algorithm Comparison",
                "variations": ["collaborative_filtering", "content_based", "hybrid"],
                "traffic_split": [0.333, 0.333, 0.334],
                "success_metric": "click_through_rate",
                "min_sample_size": 5000,
            }
        ],
        "preferences": [
            {
                "id": "user_pref_ab",
                "user_entity": "User",
                "entity_type": "user",
                "weight": 1.0,
                "history_window_days": 30,
                "exclude_viewed": True,
                "boost_categories": [],
            }
        ],
        "default_algorithm": "hybrid",
        "default_top_k": 10,
        "enable_cache": True,
        "enable_ab_testing": True,
    }
    ir = parse_recommendation_to_ir(data)
    return RecommendationRecipeOutput(
        name="recommendation_ab_test_recipe",
        description="A/B test — so sanh CF, Content-Based, Hybrid voi CTR metric",
        ir=ir,
        raw_data=data,
    )
