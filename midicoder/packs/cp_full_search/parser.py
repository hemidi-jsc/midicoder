# coding: utf-8
"""
Search Parser - Parse MIR metadata thành SearchCollection.

Module này cung cấp SearchParser để convert MIR metadata (từ Pipeline layer 2)
thành SearchCollection (CP10 models). Parser hỗ trợ:
- Parse search_indices từ MIR metadata
- Parse vector_search_indices (vector similarity search)
- Parse geo_search_indices (geospatial search)
- Parse faceted_search_indices (faceted aggregation)
- Parse search_queries (query bindings)
- Parse providers (Elasticsearch, MeiliSearch)
- Parse sync strategies (realtime, near_realtime, batch)
- Parse sync triggers (event, polling)
- Parse columns với types, searchable, filterable, sortable
- KPI-029: Tenant isolation (mặc định True)

Error handling: Bỏ qua các entries không hợp lệ, tiếp tục parse các entries khác.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from midicoder.packs.cp_full_search.models import (
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

# Mapping provider string -> enum
_PROVIDER_MAP = {
    "elasticsearch": SearchProviderType.ELASTICSEARCH,
    "meilisearch": SearchProviderType.MEILISEARCH,
}

# Mapping sync strategy string -> enum
_STRATEGY_MAP = {
    "realtime": SyncStrategy.REALTIME,
    "near_realtime": SyncStrategy.NEAR_REALTIME,
    "batch": SyncStrategy.BATCH,
}

# Mapping sync trigger string -> enum
_TRIGGER_MAP = {
    "event": SyncTrigger.EVENT,
    "polling": SyncTrigger.POLLING,
}

# Mapping query type string -> enum
_QUERY_TYPE_MAP = {
    "fulltext": SearchQueryType.FULLTEXT,
    "vector": SearchQueryType.VECTOR,
    "geo": SearchQueryType.GEO,
    "facet": SearchQueryType.FACET,
    "hybrid": SearchQueryType.HYBRID,
}

# Mapping vector similarity metric string -> enum
_VECTOR_METRIC_MAP = {
    "cosine": VectorSimilarityMetric.COSINE,
    "euclidean": VectorSimilarityMetric.EUCLIDEAN,
    "dot_product": VectorSimilarityMetric.DOT_PRODUCT,
    "manhattan": VectorSimilarityMetric.MANHATTAN,
    "hamming": VectorSimilarityMetric.HAMMING,
}

# Mapping vector index type string -> enum
_VECTOR_INDEX_TYPE_MAP = {
    "ivf_flat": VectorIndexType.IVF_FLAT,
    "ivf_pq": VectorIndexType.IVF_PQ,
    "hnsw": VectorIndexType.HNSW,
    "ivf_hnsw": VectorIndexType.IVF_HNSW,
    "flat": VectorIndexType.FLAT,
}

# Mapping geo operation string -> enum
_GEO_OP_MAP = {
    "bounding_box": GeoOperation.BOUNDING_BOX,
    "circle": GeoOperation.CIRCLE,
    "polygon": GeoOperation.POLYGON,
    "distance": GeoOperation.DISTANCE,
}

# Mapping facet type string -> enum
_FACET_TYPE_MAP = {
    "term": FacetType.TERM,
    "range": FacetType.RANGE,
    "date_histogram": FacetType.DATE_HISTOGRAM,
    "histogram": FacetType.HISTOGRAM,
    "geo_distance": FacetType.GEO_DISTANCE,
}


@dataclass
class SearchParser:
    """
    Parser để convert MIR metadata thành SearchCollection.

    Parse search indices declarations từ MIR metadata và chuyển thành
    các SearchIndex objects. Hỗ trợ fallback cho các giá trị mặc định
    khi fields thiếu.
    """

    def parse_from_metadata(self, metadata: Optional[dict[str, Any]]) -> SearchCollection:
        """
        Parse tất cả search-related entries từ MIR metadata.

        Hỗ trợ các keys:
        - search_indices: Basic search indices (đã có)
        - vector_search_indices: Vector similarity search indices
        - geo_search_indices: Geospatial search indices
        - faceted_search_indices: Faceted search indices
        - search_queries: Search query bindings

        Args:
            metadata: MIR metadata dictionary.

        Returns:
            SearchCollection chứa tất cả search entries đã parse.

        Raises:
            MidicoderError: Nếu metadata không hợp lệ (không raise, return empty collection).
        """
        collection = SearchCollection()

        # Handle None metadata
        if not metadata or not isinstance(metadata, dict):
            return collection

        # Parse basic search indices
        self._parse_indices_list(metadata, collection.add_index, self._parse_index)

        # Parse vector search indices
        self._parse_indices_list(
            metadata,
            collection.add_vector_index,
            self._parse_vector_index,
            "vector_search_indices",
        )

        # Parse geospatial search indices
        self._parse_indices_list(
            metadata,
            collection.add_geo_index,
            self._parse_geo_index,
            "geo_search_indices",
        )

        # Parse faceted search indices
        self._parse_indices_list(
            metadata,
            collection.add_faceted_index,
            self._parse_faceted_index,
            "faceted_search_indices",
        )

        # Parse search queries
        self._parse_indices_list(
            metadata,
            collection.add_query,
            self._parse_query,
            "search_queries",
        )

        return collection

    def _parse_indices_list(
        self,
        metadata: dict[str, Any],
        add_fn: Any,
        parse_fn: Any,
        key: str = "search_indices",
    ) -> None:
        """
        Parse một danh sách entries từ metadata và thêm vào collection.

        Generic helper để tránh lặp code pattern giữa các loại index.

        Args:
            metadata: MIR metadata dictionary.
            add_fn: Callable để thêm parsed object vào collection.
            parse_fn: Callable để parse một entry từ dict.
            key: Key trong metadata để lấy danh sách entries.
        """
        indices_data = metadata.get(key, [])
        if not indices_data or not isinstance(indices_data, list):
            return

        for entry_data in indices_data:
            try:
                if not isinstance(entry_data, dict):
                    continue
                add_fn(parse_fn(entry_data))
            except Exception:
                # Bỏ qua entries không parse được, tiếp tục với entries khác
                continue

    def _parse_index(self, data: dict[str, Any]) -> SearchIndex:
        """
        Parse một search index từ dictionary.

        Args:
            data: Dictionary chứa thông tin search index.

        Returns:
            SearchIndex instance đã parse.

        Raises:
            MidicoderError: Nếu index id rỗng (MDC-CP10-001).
        """
        # Parse provider — fallback default elasticsearch
        provider_str = data.get("provider", "elasticsearch")
        provider = _PROVIDER_MAP.get(provider_str, SearchProviderType.ELASTICSEARCH)

        # Parse sync strategy — fallback default near_realtime
        strategy_str = data.get("sync_strategy", "near_realtime")
        sync_strategy = _STRATEGY_MAP.get(strategy_str, SyncStrategy.NEAR_REALTIME)

        # Parse sync trigger — fallback default event
        trigger_str = data.get("sync_trigger", "event")
        sync_trigger = _TRIGGER_MAP.get(trigger_str, SyncTrigger.EVENT)

        # Parse columns
        columns = []
        columns_data = data.get("columns", [])
        if isinstance(columns_data, list):
            for col_data in columns_data:
                if isinstance(col_data, dict):
                    columns.append(SearchIndexColumn(
                        name=col_data.get("name", ""),
                        column_type=col_data.get("type", col_data.get("column_type", "text")),
                        searchable=col_data.get("searchable", False),
                        filterable=col_data.get("filterable", False),
                        sortable=col_data.get("sortable", False),
                        analyser=col_data.get("analyser", ""),
                        description=col_data.get("description", ""),
                    ))

        # Tạo SearchIndex — validation __post_init__ sẽ check id rỗng
        return SearchIndex(
            id=data.get("id", ""),
            provider=provider,
            columns=columns,
            sync_strategy=sync_strategy,
            sync_trigger=sync_trigger,
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )

    def _parse_vector_index(self, data: dict[str, Any]) -> VectorSearchIndex:
        """
        Parse một vector search index từ dictionary.

        Args:
            data: Dictionary chứa thông tin vector search index.

        Returns:
            VectorSearchIndex instance đã parse.
        """
        # Parse provider
        provider_str = data.get("provider", "elasticsearch")
        provider = _PROVIDER_MAP.get(provider_str, SearchProviderType.ELASTICSEARCH)

        # Parse vector column
        vector_column = None
        vc_data = data.get("vector_column")
        if isinstance(vc_data, dict):
            metric_str = vc_data.get("similarity_metric", "cosine")
            index_type_str = vc_data.get("index_type", "hnsw")

            vector_column = VectorIndexColumn(
                name=vc_data.get("name", ""),
                dimensions=vc_data.get("dimensions", 768),
                similarity_metric=_VECTOR_METRIC_MAP.get(metric_str, VectorSimilarityMetric.COSINE),
                index_type=_VECTOR_INDEX_TYPE_MAP.get(index_type_str, VectorIndexType.HNSW),
                description=vc_data.get("description", ""),
            )

        # Parse text columns
        text_columns = []
        tc_data = data.get("text_columns", [])
        if isinstance(tc_data, list):
            for col_data in tc_data:
                if isinstance(col_data, dict):
                    text_columns.append(SearchIndexColumn(
                        name=col_data.get("name", ""),
                        column_type=col_data.get("type", col_data.get("column_type", "text")),
                        searchable=col_data.get("searchable", False),
                        filterable=col_data.get("filterable", False),
                        sortable=col_data.get("sortable", False),
                        analyser=col_data.get("analyser", ""),
                        description=col_data.get("description", ""),
                    ))

        return VectorSearchIndex(
            id=data.get("id", ""),
            provider=provider,
            vector_column=vector_column,
            text_columns=text_columns,
            top_k=data.get("top_k", 10),
            description=data.get("description", ""),
        )

    def _parse_geo_index(self, data: dict[str, Any]) -> GeoSearchIndex:
        """
        Parse một geospatial search index từ dictionary.

        Args:
            data: Dictionary chứa thông tin geospatial search index.

        Returns:
            GeoSearchIndex instance đã parse.
        """
        # Parse provider
        provider_str = data.get("provider", "elasticsearch")
        provider = _PROVIDER_MAP.get(provider_str, SearchProviderType.ELASTICSEARCH)

        # Parse geo column
        geo_column = None
        gc_data = data.get("geo_column")
        if isinstance(gc_data, dict):
            geo_column = GeoSearchColumn(
                name=gc_data.get("name", ""),
                geo_type=gc_data.get("geo_type", "point"),
                crs=gc_data.get("crs", "WGS84"),
                searchable=gc_data.get("searchable", True),
                filterable=gc_data.get("filterable", True),
                description=gc_data.get("description", ""),
            )

        # Parse text columns
        text_columns = []
        tc_data = data.get("text_columns", [])
        if isinstance(tc_data, list):
            for col_data in tc_data:
                if isinstance(col_data, dict):
                    text_columns.append(SearchIndexColumn(
                        name=col_data.get("name", ""),
                        column_type=col_data.get("type", col_data.get("column_type", "text")),
                        searchable=col_data.get("searchable", False),
                        filterable=col_data.get("filterable", False),
                        sortable=col_data.get("sortable", False),
                        analyser=col_data.get("analyser", ""),
                        description=col_data.get("description", ""),
                    ))

        # Parse operations
        operations = []
        ops_data = data.get("operations", ["circle", "distance"])
        if isinstance(ops_data, list):
            for op_str in ops_data:
                if isinstance(op_str, str):
                    op = _GEO_OP_MAP.get(op_str, GeoOperation.CIRCLE)
                    if op not in operations:
                        operations.append(op)
        if not operations:
            operations = [GeoOperation.CIRCLE, GeoOperation.DISTANCE]

        return GeoSearchIndex(
            id=data.get("id", ""),
            provider=provider,
            geo_column=geo_column,
            text_columns=text_columns,
            operations=operations,
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )

    def _parse_faceted_index(self, data: dict[str, Any]) -> FacetedSearchIndex:
        """
        Parse một faceted search index từ dictionary.

        Args:
            data: Dictionary chứa thông tin faceted search index.

        Returns:
            FacetedSearchIndex instance đã parse.
        """
        # Parse provider
        provider_str = data.get("provider", "elasticsearch")
        provider = _PROVIDER_MAP.get(provider_str, SearchProviderType.ELASTICSEARCH)

        # Parse columns
        columns = []
        columns_data = data.get("columns", [])
        if isinstance(columns_data, list):
            for col_data in columns_data:
                if isinstance(col_data, dict):
                    columns.append(SearchIndexColumn(
                        name=col_data.get("name", ""),
                        column_type=col_data.get("type", col_data.get("column_type", "text")),
                        searchable=col_data.get("searchable", False),
                        filterable=col_data.get("filterable", False),
                        sortable=col_data.get("sortable", False),
                        analyser=col_data.get("analyser", ""),
                        description=col_data.get("description", ""),
                    ))

        # Parse facets
        facets = []
        facets_data = data.get("facets", [])
        if isinstance(facets_data, list):
            for facet_data in facets_data:
                if isinstance(facet_data, dict):
                    facets.append(Facet.from_dict(facet_data))

        return FacetedSearchIndex(
            id=data.get("id", ""),
            provider=provider,
            columns=columns,
            facets=facets,
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )

    def _parse_query(self, data: dict[str, Any]) -> SearchQuery:
        """
        Parse một search query binding từ dictionary.

        Args:
            data: Dictionary chứa thông tin search query.

        Returns:
            SearchQuery instance đã parse.
        """
        query_type_str = data.get("query_type", "fulltext")
        query_type = _QUERY_TYPE_MAP.get(query_type_str, SearchQueryType.FULLTEXT)

        fields = data.get("fields", [])
        if not isinstance(fields, list):
            fields = []

        return SearchQuery(
            id=data.get("id", ""),
            query_type=query_type,
            target_index=data.get("target_index", ""),
            fields=fields,
            default_size=data.get("default_size", 20),
            default_sort=data.get("default_sort", ""),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CP63: Search & Recommendation Engine — Parser (merged)
# ===========================================================================


from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_search.models import (
    ABTestConfig,
    ItemEmbedding,
    RecommendationAlgorithm,
    RecommendationCache,
    RecommendationConfig,
    SimilarityMetric,
    UserPreference,
)


@dataclass
class RecommendationIR:
    """Intermediate Representation cho CP63.

    Gom tập tất cả cấu hình recommendation engine từ DSL.

    Attributes:
        configs: Danh sách recommendation configurations
        embeddings: Danh sách item embedding configs
        preferences: Danh sách user preference configs
        caches: Danh sách recommendation cache entries
        ab_tests: Danh sách A/B test configurations
        default_algorithm: Thuật toán mặc định
        default_top_k: Số lượng items mặc định
        enable_cache: Có bật cache toàn cục không
        enable_ab_testing: Có bật A/B testing không
    """
    configs: list[RecommendationConfig] = field(default_factory=list)
    embeddings: list[ItemEmbedding] = field(default_factory=list)
    preferences: list[UserPreference] = field(default_factory=list)
    caches: list[RecommendationCache] = field(default_factory=list)
    ab_tests: list[ABTestConfig] = field(default_factory=list)
    default_algorithm: RecommendationAlgorithm = RecommendationAlgorithm.HYBRID
    default_top_k: int = 10
    enable_cache: bool = True
    enable_ab_testing: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "configs": [c.to_dict() for c in self.configs],
            "embeddings": [e.to_dict() for e in self.embeddings],
            "preferences": [p.to_dict() for p in self.preferences],
            "caches": [c.to_dict() for c in self.caches],
            "ab_tests": [a.to_dict() for a in self.ab_tests],
            "default_algorithm": self.default_algorithm.value,
            "default_top_k": self.default_top_k,
            "enable_cache": self.enable_cache,
            "enable_ab_testing": self.enable_ab_testing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationIR":
        configs = [RecommendationConfig.from_dict(c) for c in data.get("configs", [])]
        embeddings = [ItemEmbedding.from_dict(e) for e in data.get("embeddings", [])]
        preferences = [UserPreference.from_dict(p) for p in data.get("preferences", [])]
        caches = [RecommendationCache.from_dict(c) for c in data.get("caches", [])]
        ab_tests = [ABTestConfig.from_dict(a) for a in data.get("ab_tests", [])]
        return cls(
            configs=configs,
            embeddings=embeddings,
            preferences=preferences,
            caches=caches,
            ab_tests=ab_tests,
            default_algorithm=RecommendationAlgorithm(data.get("default_algorithm", "hybrid")),
            default_top_k=data.get("default_top_k", 10),
            enable_cache=data.get("enable_cache", True),
            enable_ab_testing=data.get("enable_ab_testing", False),
        )


def parse_recommendation_configs(data: dict[str, Any]) -> list[RecommendationConfig]:
    """Parse danh sách recommendation configs từ DSL dict."""
    raw = data.get("configs", data.get("recommendation_configs", []))
    return [RecommendationConfig.from_dict(c) for c in raw]


def parse_embeddings(data: dict[str, Any]) -> list[ItemEmbedding]:
    """Parse danh sách item embeddings từ DSL dict."""
    raw = data.get("embeddings", data.get("item_embeddings", []))
    return [ItemEmbedding.from_dict(e) for e in raw]


def parse_preferences(data: dict[str, Any]) -> list[UserPreference]:
    """Parse danh sách user preferences từ DSL dict."""
    raw = data.get("preferences", data.get("user_preferences", []))
    return [UserPreference.from_dict(p) for p in raw]


def parse_ab_tests(data: dict[str, Any]) -> list[ABTestConfig]:
    """Parse danh sách A/B test configs từ DSL dict."""
    raw = data.get("ab_tests", data.get("experiments", []))
    return [ABTestConfig.from_dict(a) for a in raw]


def parse_recommendation_to_ir(data: dict[str, Any]) -> RecommendationIR:
    """Parse DSL dict thành RecommendationIR."""
    configs = parse_recommendation_configs(data)
    embeddings = parse_embeddings(data)
    preferences = parse_preferences(data)
    caches = [RecommendationCache.from_dict(c) for c in data.get("caches", [])]
    ab_tests = parse_ab_tests(data)

    return RecommendationIR(
        configs=configs,
        embeddings=embeddings,
        preferences=preferences,
        caches=caches,
        ab_tests=ab_tests,
        default_algorithm=RecommendationAlgorithm(data.get("default_algorithm", "hybrid")),
        default_top_k=data.get("default_top_k", 10),
        enable_cache=data.get("enable_cache", True),
        enable_ab_testing=data.get("enable_ab_testing", False),
    )
