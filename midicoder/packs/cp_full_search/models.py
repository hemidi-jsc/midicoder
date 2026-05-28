# coding: utf-8
"""
Mô-đun models cho Search & Indexing Emitter (CP10).

Định nghĩa các dataclass biểu diễn:
- SearchProviderType: Enum các search providers (Elasticsearch, MeiliSearch)
- SyncStrategy: Enum các strategies đồng bộ data (realtime, near_realtime, batch)
- SyncTrigger: Enum các triggers đồng bộ (event, polling)
- SearchIndexColumn: Column trong search index với type, searchable, filterable
- SearchIndex: Search index với provider, columns, sync config, tenant_isolated
- SearchCollection: Collection chứa tất cả search indices

KPI-029: Tenant Isolation — tenant_isolated=True mặc định cho mọi index.
ValidationError: Dùng MDC-CP10 error codes (MDC-CP10-001 ~ MDC-CP10-005).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class SearchProviderType(str, Enum):
    """Enum các search providers hỗ trợ."""
    ELASTICSEARCH = "elasticsearch"
    MEILISEARCH = "meilisearch"


class SyncStrategy(str, Enum):
    """Enum các strategies đồng bộ data vào search index."""
    REALTIME = "realtime"
    NEAR_REALTIME = "near_realtime"
    BATCH = "batch"


class SyncTrigger(str, Enum):
    """Enum các triggers cho data synchronization."""
    EVENT = "event"
    POLLING = "polling"


# Danh sách các column types hợp lệ
_VALID_COLUMN_TYPES = {"text", "keyword", "numeric", "date", "geo", "vector"}


@dataclass
class SearchIndexColumn:
    """
    Column trong search index.

    Attributes:
        name: Tên column (không được để trống).
        column_type: Kiểu dữ liệu (text, keyword, numeric, date, geo).
        searchable: Có tham gia full-text search không.
        filterable: Có dùng để filter không.
        sortable: Có dùng để sort không.
        analyser: Analyzer cho text columns (vi, en, vn).
        description: Mô tả column.

    Raises:
        MidicoderError: Nếu name rỗng (MDC-CP10-001) hoặc
            column_type không hợp lệ (MDC-CP10-004).
    """
    name: str
    column_type: str = "text"
    searchable: bool = False
    filterable: bool = False
    sortable: bool = False
    analyser: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate các trường bắt buộc sau khi khởi tạo."""
        # Kiểm tra name không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F08_EMPTY_INDEX_NAME,
                name=self.name,
            )
        # Kiểm tra column_type hợp lệ
        if self.column_type not in _VALID_COLUMN_TYPES:
            EM.raise_error(
                ErrorCode.MDC-F08_INVALID_COLUMN_TYPE,
                name=self.name,
                column_type=self.column_type,
                valid_types=list(_VALID_COLUMN_TYPES),
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển column sang dict format."""
        return {
            "name": self.name,
            "type": self.column_type,
            "searchable": self.searchable,
            "filterable": self.filterable,
            "sortable": self.sortable,
            "analyser": self.analyser,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchIndexColumn":
        """Tạo SearchIndexColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            column_type=data.get("type", data.get("column_type", "text")),
            searchable=data.get("searchable", False),
            filterable=data.get("filterable", False),
            sortable=data.get("sortable", False),
            analyser=data.get("analyser", ""),
            description=data.get("description", ""),
        )


@dataclass
class SearchIndex:
    """
    Search index definition.

    Attributes:
        id: Định danh duy nhất của index (không được để trống).
        provider: Search provider (ELASTICSEARCH, MEILISEARCH).
        columns: Danh sách columns trong index.
        sync_strategy: Strategy đồng bộ data (mac dinh: near_realtime).
        sync_trigger: Trigger cho synchronization (mac dinh: event).
        tenant_isolated: Co enforce tenant isolation khong (KPI-029, mac dinh: True).
        description: Mô tả index.

    Raises:
        MidicoderError: Nếu id rỗng (MDC-CP10-001).
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    columns: list[SearchIndexColumn] = field(default_factory=list)
    sync_strategy: SyncStrategy = SyncStrategy.NEAR_REALTIME
    sync_trigger: SyncTrigger = SyncTrigger.EVENT
    tenant_isolated: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate các trường bắt buộc sau khi khởi tạo."""
        # Kiểm tra id không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(
                ErrorCode.MDC-F08_EMPTY_INDEX_NAME,
                index_id=self.id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển index sang dict format."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "columns": [c.to_dict() for c in self.columns],
            "sync_strategy": self.sync_strategy.value,
            "sync_trigger": self.sync_trigger.value,
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchIndex":
        """Tạo SearchIndex từ dict."""
        return cls(
            id=data.get("id", ""),
            provider=SearchProviderType(data.get("provider", "elasticsearch")),
            columns=[SearchIndexColumn.from_dict(c) for c in data.get("columns", [])],
            sync_strategy=SyncStrategy(data.get("sync_strategy", "near_realtime")),
            sync_trigger=SyncTrigger(data.get("sync_trigger", "event")),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


@dataclass
class SearchCollection:
    """
    Collection chứa tất cả search indices.

    Attributes:
        indices: Danh sách search indices cơ bản.
        vector_indices: Danh sách vector search indices.
        geo_indices: Danh sách geospatial search indices.
        faceted_indices: Danh sách faceted search indices.
        queries: Danh sách search query bindings.
    """
    indices: list[SearchIndex] = field(default_factory=list)
    vector_indices: list["VectorSearchIndex"] = field(default_factory=list)
    geo_indices: list["GeoSearchIndex"] = field(default_factory=list)
    faceted_indices: list["FacetedSearchIndex"] = field(default_factory=list)
    queries: list["SearchQuery"] = field(default_factory=list)

    def add_index(self, index: SearchIndex) -> None:
        """Thêm index vào collection."""
        self.indices.append(index)

    def add_vector_index(self, index: "VectorSearchIndex") -> None:
        """Thêm vector search index vào collection."""
        self.vector_indices.append(index)

    def add_geo_index(self, index: "GeoSearchIndex") -> None:
        """Thêm geospatial search index vào collection."""
        self.geo_indices.append(index)

    def add_faceted_index(self, index: "FacetedSearchIndex") -> None:
        """Thêm faceted search index vào collection."""
        self.faceted_indices.append(index)

    def add_query(self, query: "SearchQuery") -> None:
        """Thêm search query vào collection."""
        self.queries.append(query)

    @property
    def total_count(self) -> int:
        """Tổng số indices trong collection."""
        return len(self.indices)

    @property
    def total_vector_count(self) -> int:
        """Tổng số vector indices trong collection."""
        return len(self.vector_indices)

    @property
    def total_geo_count(self) -> int:
        """Tổng số geo indices trong collection."""
        return len(self.geo_indices)

    @property
    def total_faceted_count(self) -> int:
        """Tổng số faceted indices trong collection."""
        return len(self.faceted_indices)

    @property
    def total_query_count(self) -> int:
        """Tổng số queries trong collection."""
        return len(self.queries)

    def get_by_id(self, index_id: str) -> Optional[SearchIndex]:
        """Tìm index theo ID."""
        for index in self.indices:
            if index.id == index_id:
                return index
        return None

    def get_vector_by_id(self, index_id: str) -> Optional["VectorSearchIndex"]:
        """Tìm vector index theo ID."""
        for index in self.vector_indices:
            if index.id == index_id:
                return index
        return None

    def get_geo_by_id(self, index_id: str) -> Optional["GeoSearchIndex"]:
        """Tìm geo index theo ID."""
        for index in self.geo_indices:
            if index.id == index_id:
                return index
        return None

    def get_faceted_by_id(self, index_id: str) -> Optional["FacetedSearchIndex"]:
        """Tìm faceted index theo ID."""
        for index in self.faceted_indices:
            if index.id == index_id:
                return index
        return None

    def get_query_by_id(self, query_id: str) -> Optional["SearchQuery"]:
        """Tìm query theo ID."""
        for query in self.queries:
            if query.id == query_id:
                return query
        return None

    def tenant_isolated_indices(self) -> list[SearchIndex]:
        """Lọc các indices có tenant isolation (KPI-029)."""
        return [i for i in self.indices if i.tenant_isolated]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "indices": [i.to_dict() for i in self.indices],
            "vector_indices": [i.to_dict() for i in self.vector_indices],
            "geo_indices": [i.to_dict() for i in self.geo_indices],
            "faceted_indices": [i.to_dict() for i in self.faceted_indices],
            "queries": [q.to_dict() for q in self.queries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchCollection":
        """Tạo SearchCollection từ dict."""
        result = cls()
        result.indices = [SearchIndex.from_dict(i) for i in data.get("indices", [])]
        result.vector_indices = [VectorSearchIndex.from_dict(i) for i in data.get("vector_indices", [])]
        result.geo_indices = [GeoSearchIndex.from_dict(i) for i in data.get("geo_indices", [])]
        result.faceted_indices = [FacetedSearchIndex.from_dict(i) for i in data.get("faceted_indices", [])]
        result.queries = [SearchQuery.from_dict(q) for q in data.get("queries", [])]
        return result


# ===========================================================================
# SearchQuery — first-class query binding
# ===========================================================================


class SearchQueryType(str, Enum):
    """
    Loại search query.

    - fulltext: Full-text search (BM25/TF-IDF)
    - vector: Vector similarity search (ANN)
    - geo: Geospatial search (circle, bounding_box, polygon)
    - facet: Faceted aggregation (term, range, histogram)
    - hybrid: Hybrid search (fulltext + vector combined)
    """
    FULLTEXT = "fulltext"
    VECTOR = "vector"
    GEO = "geo"
    FACET = "facet"
    HYBRID = "hybrid"


@dataclass
class SearchQuery:
    """
    Search query binding — liên kết query với search backend.

    SearchQuery đại diện cho một loại truy vấn tìm kiếm, xác định:
    - Index mục tiêu
    - Loại query (fulltext, vector, geo, facet, hybrid)
    - Các field tham gia
    - Default parameters (size, from, sort)

    Attributes:
        id: Định danh duy nhất (vd: "search_products", "find_nearby_stores")
        query_type: Loại query (fulltext, vector, geo, facet, hybrid)
        target_index: Tên search index mục tiêu
        fields: Các fields tham gia trong query
        default_size: Số kết quả trả về mặc định
        default_sort: Sort mặc định
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        description: Mô tả query

    Raises:
        MidicoderError: Nếu id rỗng (MDC-CP10-001).
    """
    id: str
    query_type: SearchQueryType = SearchQueryType.FULLTEXT
    target_index: str = ""
    fields: list[str] = field(default_factory=list)
    default_size: int = 20
    default_sort: str = ""
    tenant_isolated: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate các trường bắt buộc sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, name=self.id)
        if self.default_size < 1:
            self.default_size = 20

    def to_dict(self) -> dict[str, Any]:
        """Chuyển query sang dict format."""
        return {
            "id": self.id,
            "query_type": self.query_type.value,
            "target_index": self.target_index,
            "fields": self.fields,
            "default_size": self.default_size,
            "default_sort": self.default_sort,
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchQuery":
        """Tạo SearchQuery từ dict."""
        return cls(
            id=data.get("id", ""),
            query_type=SearchQueryType(data.get("query_type", "fulltext")),
            target_index=data.get("target_index", ""),
            fields=data.get("fields", []),
            default_size=data.get("default_size", 20),
            default_sort=data.get("default_sort", ""),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# Vector Search
# ===========================================================================


class VectorSimilarityMetric(str, Enum):
    """
    Metric tính toán độ tương đồng vector.

    - cosine: Cosine similarity ([-1, 1], 1 = cùng hướng) — phổ biến nhất
    - euclidean: L2 distance (0 = identical, càng lớn càng xa)
    - dot_product: Dot product (càng lớn càng tương đồng)
    - manhattan: L1 distance (total absolute difference)
    - hamming: Hamming distance (cho binary vectors)
    """
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"


class VectorIndexType(str, Enum):
    """
    Loại index cho vector similarity search.

    - ivf_flat: Inverted File Flat (nhanh, memory-efficient)
    - ivf_pq: Inverted File Product Quantization (tiết kiệm RAM, hơi kém chính xác)
    - hnsw: HNSW graph (chính xác nhất, chậm hơn build nhưng fast query)
    - ivf_hnsw: Hybrid IVF + HNSW
    - flat: Brute-force (chính xác 100%, chậm, dùng cho tập nhỏ)
    """
    IVF_FLAT = "ivf_flat"
    IVF_PQ = "ivf_pq"
    HNSW = "hnsw"
    IVF_HNSW = "ivf_hnsw"
    FLAT = "flat"


@dataclass
class VectorIndexColumn:
    """
    Column chứa embedding vectors — dùng cho semantic search.

    Attributes:
        name: Tên column (vd: "title_embedding", "description_vector")
        dimensions: Số chiều vector (vd: 768 cho sentence-transformers)
        similarity_metric: Metric tính toán similarity (cosine, euclidean, dot_product, ...)
        index_type: Loại vector index (hnsw, ivf_flat, ivf_pq, flat)
        description: Mô tả column
    """
    name: str
    dimensions: int
    similarity_metric: VectorSimilarityMetric = VectorSimilarityMetric.COSINE
    index_type: VectorIndexType = VectorIndexType.HNSW
    description: str = ""

    def __post_init__(self) -> None:
        """Validate vector index column sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, name=self.name)
        if self.dimensions < 1:
            EM.raise_error(ErrorCode.MDC-F08_INVALID_COLUMN_TYPE, name=self.name, column_type="vector", valid_types="dimensions > 0")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển vector column sang dict format."""
        return {
            "name": self.name,
            "dimensions": self.dimensions,
            "similarity_metric": self.similarity_metric.value,
            "index_type": self.index_type.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VectorIndexColumn":
        """Tạo VectorIndexColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            dimensions=data.get("dimensions", 768),
            similarity_metric=VectorSimilarityMetric(data.get("similarity_metric", "cosine")),
            index_type=VectorIndexType(data.get("index_type", "hnsw")),
            description=data.get("description", ""),
        )


@dataclass
class VectorSearchIndex:
    """
    Search index chuyên dụng cho vector similarity search.

    Hỗ trợ semantic search: tìm kiếm theo ý nghĩa, không theo keyword.
    Ví dụ: "điện thoại pin lâu" → trả về sản phẩm phone có pin tốt.

    Attributes:
        id: Định danh duy nhất (vd: "product_semantic_search")
        provider: Search provider hỗ trợ vector (ELASTICSEARCH 8+, MEILISEARCH)
        vector_column: Column chứa embeddings
        text_columns: Các text columns để kết hợp hybrid search (vector + BM25)
        top_k: Số kết quả trả về mặc định
        description: Mô tả index
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    vector_column: VectorIndexColumn | None = None
    text_columns: list[SearchIndexColumn] = field(default_factory=list)
    top_k: int = 10
    description: str = ""

    def __post_init__(self) -> None:
        """Validate vector search index sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, index_id=self.id)
        if not self.vector_column:
            EM.raise_error(ErrorCode.MDC-F08_INVALID_COLUMN_TYPE, name=self.id, column_type="vector", valid_types="vector_column required")
        if self.top_k < 1:
            self.top_k = 10

    def to_dict(self) -> dict[str, Any]:
        """Chuyển vector search index sang dict format."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "vector_column": self.vector_column.to_dict() if self.vector_column else None,
            "text_columns": [c.to_dict() for c in self.text_columns],
            "top_k": self.top_k,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VectorSearchIndex":
        """Tạo VectorSearchIndex từ dict."""
        vc_data = data.get("vector_column")
        return cls(
            id=data.get("id", ""),
            provider=SearchProviderType(data.get("provider", "elasticsearch")),
            vector_column=VectorIndexColumn.from_dict(vc_data) if vc_data else None,
            text_columns=[SearchIndexColumn.from_dict(c) for c in data.get("text_columns", [])],
            top_k=data.get("top_k", 10),
            description=data.get("description", ""),
        )


# ===========================================================================
# Geospatial Search
# ===========================================================================


class GeoOperation(str, Enum):
    """
    Loại geospatial operation.

    - bounding_box: Tìm trong rectangular area
    - circle: Tìm trong bán kính từ trung tâm
    - polygon: Tìm trong đa giác tùy ý
    - distance: Sắp xếp theo khoảng cách từ điểm
    """
    BOUNDING_BOX = "bounding_box"
    CIRCLE = "circle"
    POLYGON = "polygon"
    DISTANCE = "distance"


@dataclass
class GeoSearchColumn:
    """
    Column chứa geospatial data cho search.

    Attributes:
        name: Tên column (vd: "location", "coordinates")
        geo_type: Loại geospatial (point, polygon, line)
        crs: Coordinate Reference System (vd: "WGS84")
        searchable: Có dùng trong geospatial queries không
        filterable: Có dùng để filter theo region không
        description: Mô tả column
    """
    name: str
    geo_type: str = "point"
    crs: str = "WGS84"
    searchable: bool = True
    filterable: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate geospatial column sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, name=self.name)
        if self.geo_type not in ("point", "polygon", "line", "multipoint", "multipolygon"):
            EM.raise_error(ErrorCode.MDC-F08_INVALID_COLUMN_TYPE, name=self.name, column_type=self.geo_type, valid_types=["point", "polygon", "line", "multipoint", "multipolygon"])

    def to_dict(self) -> dict[str, Any]:
        """Chuyển geospatial column sang dict format."""
        return {
            "name": self.name,
            "geo_type": self.geo_type,
            "crs": self.crs,
            "searchable": self.searchable,
            "filterable": self.filterable,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoSearchColumn":
        """Tạo GeoSearchColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            geo_type=data.get("geo_type", "point"),
            crs=data.get("crs", "WGS84"),
            searchable=data.get("searchable", True),
            filterable=data.get("filterable", True),
            description=data.get("description", ""),
        )


@dataclass
class GeoSearchIndex:
    """
    Search index chuyên dụng cho geospatial queries.

    Hỗ trợ tìm kiếm theo vị trí: "cửa hàng gần tôi", "bất động sản trong khu vực".

    Attributes:
        id: Định danh duy nhất (vd: "store_locations")
        provider: Search provider (ELASTICSEARCH, MEILISEARCH)
        geo_column: Column chứa geospatial data
        text_columns: Các text columns kết hợp (vd: tên cửa hàng, mô tả)
        operations: Các geospatial operations được hỗ trợ
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        description: Mô tả index
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    geo_column: GeoSearchColumn | None = None
    text_columns: list[SearchIndexColumn] = field(default_factory=list)
    operations: list[GeoOperation] = field(default_factory=lambda: [GeoOperation.CIRCLE, GeoOperation.DISTANCE])
    tenant_isolated: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate geospatial search index sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, index_id=self.id)
        if not self.geo_column:
            EM.raise_error(ErrorCode.MDC-F08_INVALID_COLUMN_TYPE, name=self.id, column_type="geo", valid_types="geo_column required")
        if not self.operations:
            self.operations = [GeoOperation.CIRCLE, GeoOperation.DISTANCE]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển geospatial search index sang dict format."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "geo_column": self.geo_column.to_dict() if self.geo_column else None,
            "text_columns": [c.to_dict() for c in self.text_columns],
            "operations": [op.value for op in self.operations],
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoSearchIndex":
        """Tạo GeoSearchIndex từ dict."""
        gc_data = data.get("geo_column")
        return cls(
            id=data.get("id", ""),
            provider=SearchProviderType(data.get("provider", "elasticsearch")),
            geo_column=GeoSearchColumn.from_dict(gc_data) if gc_data else None,
            text_columns=[SearchIndexColumn.from_dict(c) for c in data.get("text_columns", [])],
            operations=[GeoOperation(op) for op in data.get("operations", ["circle", "distance"])],
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# Faceted Aggregation
# ===========================================================================


class FacetType(str, Enum):
    """
    Loại facet cho aggregation.

    - term: Group by discrete values (vd: category, brand, color)
    - range: Group by numeric ranges (vd: price $0-100, $100-500, $500+)
    - date_histogram: Group by time periods (vd: daily, weekly, monthly)
    - histogram: Group by numeric intervals (vd: rating 1-5)
    - geo_distance: Group by distance buckets (vd: 0-5km, 5-15km, 15km+)
    """
    TERM = "term"
    RANGE = "range"
    DATE_HISTOGRAM = "date_histogram"
    HISTOGRAM = "histogram"
    GEO_DISTANCE = "geo_distance"


class AggregationFunction(str, Enum):
    """
    Hàm aggregation.

    - count: Đếm số records
    - avg: Giá trị trung bình
    - sum: Tổng
    - min/max: Giá trị nhỏ nhất / lớn nhất
    - cardinality: Số giá trị unique (approximate distinct count)
    - percentiles: Phân vị (p50, p90, p95, p99)
    """
    COUNT = "count"
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    CARDINALITY = "cardinality"
    PERCENTILES = "percentiles"


@dataclass
class Facet:
    """
    Facet — phép phân nhóm dữ liệu cho filter/explore.

    Ví dụ: thương mại điện tử có facets "Hãng", "Giá", "Đánh giá", "Màu sắc".

    Attributes:
        id: Facet identifier (vd: "brand", "price_range", "rating")
        facet_type: Loại facet (term, range, date_histogram, histogram, geo_distance)
        source_column: Tên column trong index để aggregate
        agg_function: Hàm aggregation (count, avg, sum, cardinality, ...)
        size: Số bucket lớn nhất trả về (cho term facets)
        range_bounds: Range boundaries (cho range facets, vd: [0, 100, 500, 1000])
        interval: Interval (cho histogram, vd: "1d", "1w", "1m")
        description: Mô tả facet
    """
    id: str
    facet_type: FacetType
    source_column: str
    agg_function: AggregationFunction = AggregationFunction.COUNT
    size: int = 10
    range_bounds: list[float] = field(default_factory=list)
    interval: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate facet sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, name=self.id)
        if not self.source_column or not self.source_column.strip():
            EM.raise_error(ErrorCode.MDC-F08_INVALID_COLUMN_TYPE, name=self.id, column_type="facet", valid_types="source_column required")
        if self.size < 1:
            self.size = 10

    def to_dict(self) -> dict[str, Any]:
        """Chuyển facet sang dict format."""
        return {
            "id": self.id,
            "facet_type": self.facet_type.value,
            "source_column": self.source_column,
            "agg_function": self.agg_function.value,
            "size": self.size,
            "range_bounds": self.range_bounds,
            "interval": self.interval,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Facet":
        """Tạo Facet từ dict."""
        return cls(
            id=data.get("id", ""),
            facet_type=FacetType(data.get("facet_type", "term")),
            source_column=data.get("source_column", ""),
            agg_function=AggregationFunction(data.get("agg_function", "count")),
            size=data.get("size", 10),
            range_bounds=data.get("range_bounds", []),
            interval=data.get("interval", ""),
            description=data.get("description", ""),
        )


@dataclass
class FacetedSearchIndex:
    """
    Search index với faceted aggregation — cho phép explore/filter theo nhiều chiều.

    Ví dụ: tìm kiếm sản phẩm với facets "Hãng", "Giá", "Đánh giá", "Màu sắc"
    cho phép user drill-down qua từng dimension.

    Attributes:
        id: Định danh duy nhất (vd: "product_catalog_search")
        provider: Search provider
        columns: Các columns cơ bản trong index
        facets: Danh sách facets cho aggregation
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        description: Mô tả index
    """
    id: str
    provider: SearchProviderType = SearchProviderType.ELASTICSEARCH
    columns: list[SearchIndexColumn] = field(default_factory=list)
    facets: list[Facet] = field(default_factory=list)
    tenant_isolated: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate faceted search index sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F08_EMPTY_INDEX_NAME, index_id=self.id)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển faceted search index sang dict format."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "columns": [c.to_dict() for c in self.columns],
            "facets": [f.to_dict() for f in self.facets],
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FacetedSearchIndex":
        """Tạo FacetedSearchIndex từ dict."""
        return cls(
            id=data.get("id", ""),
            provider=SearchProviderType(data.get("provider", "elasticsearch")),
            columns=[SearchIndexColumn.from_dict(c) for c in data.get("columns", [])],
            facets=[Facet.from_dict(f) for f in data.get("facets", [])],
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CP63: Search & Recommendation Engine — Models (merged)
# ===========================================================================

from datetime import datetime, timezone


class RecommendationAlgorithm(str, Enum):
    """Loại thuật toán recommendation.

    - COLLABORATIVE_FILTERING: Collaborative filtering (user-user/item-item)
    - CONTENT_BASED: Content-based recommendation với item features
    - HYBRID: Hybrid kết hợp collaborative + content-based
    - POPULARITY: Popularity-based fallback
    - RANDOM: Random recommendation (cho A/B test control group)
    """
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULARITY = "popularity"
    RANDOM = "random"


class SimilarityMetric(str, Enum):
    """Phương pháp tính độ tương đồng.

    - COSINE: Cosine similarity
    - EUCLIDEAN: Euclidean distance
    - DOT_PRODUCT: Dot product
    """
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


@dataclass
class RecommendationConfig:
    """Cấu hình recommendation engine.

    Attributes:
        id: ID duy nhất của cấu hình recommendation
        name: Tên mô tả của cấu hình
        algorithm: Loại thuật toán recommendation
        item_entity: Tên entity của items được recommend
        user_entity: Tên entity của users nhận recommendation
        rating_field: Trường rating/score để tính toán
        top_k: Số lượng items tối đa trả về
        min_interactions: Số tương tác tối thiểu để train model
        ttl_seconds: Time-to-live cho cached recommendations
        cache_enabled: Có bật cache không
        metadata: Dữ liệu bổ sung
    """
    id: str
    name: str
    algorithm: RecommendationAlgorithm
    item_entity: str = "Product"
    user_entity: str = "User"
    rating_field: str = "rating"
    top_k: int = 10
    min_interactions: int = 5
    ttl_seconds: int = 3600
    cache_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="RecommendationConfig.id bắt buộc và không được để trống",
            )
        if self.top_k < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"top_k phải >= 1, nhận được: {self.top_k}",
            )
        if self.min_interactions < 0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"min_interactions phải >= 0, nhận được: {self.min_interactions}",
            )
        if self.ttl_seconds < 0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"ttl_seconds phải >= 0, nhận được: {self.ttl_seconds}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "item_entity": self.item_entity,
            "user_entity": self.user_entity,
            "rating_field": self.rating_field,
            "top_k": self.top_k,
            "min_interactions": self.min_interactions,
            "ttl_seconds": self.ttl_seconds,
            "cache_enabled": self.cache_enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationConfig":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            algorithm=RecommendationAlgorithm(data.get("algorithm", "hybrid")),
            item_entity=data.get("item_entity", "Product"),
            user_entity=data.get("user_entity", "User"),
            rating_field=data.get("rating_field", "rating"),
            top_k=data.get("top_k", 10),
            min_interactions=data.get("min_interactions", 5),
            ttl_seconds=data.get("ttl_seconds", 3600),
            cache_enabled=data.get("cache_enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ItemEmbedding:
    """Embedding vector cho items.

    Attributes:
        id: ID duy nhất của embedding config
        item_type: Loại item (vd: "product", "article", "video")
        embedding_fields: Danh sách các fields dùng để tạo embedding
        similarity_metric: Phương pháp tính độ tương đồng
        dimension: Số chiều của embedding vector
        auto_train: Có tự động train embedding model không
        metadata: Dữ liệu bổ sung
    """
    id: str
    item_type: str
    embedding_fields: list[str] = field(default_factory=list)
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    dimension: int = 128
    auto_train: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ItemEmbedding.id bắt buộc và không được để trống",
            )
        if not self.item_type or not self.item_type.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ItemEmbedding.item_type bắt buộc",
            )
        if self.dimension < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"dimension phải >= 1, nhận được: {self.dimension}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "item_type": self.item_type,
            "embedding_fields": self.embedding_fields,
            "similarity_metric": self.similarity_metric.value,
            "dimension": self.dimension,
            "auto_train": self.auto_train,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemEmbedding":
        return cls(
            id=data["id"],
            item_type=data.get("item_type", ""),
            embedding_fields=data.get("embedding_fields", []),
            similarity_metric=SimilarityMetric(data.get("similarity_metric", "cosine")),
            dimension=data.get("dimension", 128),
            auto_train=data.get("auto_train", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserPreference:
    """Sở thích người dùng.

    Attributes:
        id: ID duy nhất của preference config
        user_entity: Tên entity của user
        entity_type: Loại entity (vd: "user", "tenant_admin")
        weight: Trọng số của preference (0.0 - 1.0)
        history_window_days: Số ngày lịch sử tương tác để xem xét
        exclude_viewed: Có loại bỏ items đã xem không
        boost_categories: Danh sách categories ưu tiên
        metadata: Dữ liệu bổ sung
    """
    id: str
    user_entity: str = "User"
    entity_type: str = "user"
    weight: float = 1.0
    history_window_days: int = 30
    exclude_viewed: bool = True
    boost_categories: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="UserPreference.id bắt buộc và không được để trống",
            )
        if not 0.0 <= self.weight <= 1.0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"weight phải trong khoảng [0.0, 1.0], nhận được: {self.weight}",
            )
        if self.history_window_days < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"history_window_days phải >= 1, nhận được: {self.history_window_days}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_entity": self.user_entity,
            "entity_type": self.entity_type,
            "weight": self.weight,
            "history_window_days": self.history_window_days,
            "exclude_viewed": self.exclude_viewed,
            "boost_categories": self.boost_categories,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreference":
        return cls(
            id=data["id"],
            user_entity=data.get("user_entity", "User"),
            entity_type=data.get("entity_type", "user"),
            weight=data.get("weight", 1.0),
            history_window_days=data.get("history_window_days", 30),
            exclude_viewed=data.get("exclude_viewed", True),
            boost_categories=data.get("boost_categories", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RecommendationCache:
    """Cache kết quả recommendation.

    Attributes:
        id: ID duy nhất của cache entry
        user_id: ID user nhận recommendation
        item_type: Loại item được recommend
        items: Danh sách item IDs được recommend
        score: Score của recommendation
        generated_at: Thời điểm tạo recommendations
        ttl_seconds: Time-to-live của cache entry
    """
    id: str
    user_id: str
    item_type: str
    items: list[str] = field(default_factory=list)
    score: float = 0.0
    generated_at: datetime | None = None
    ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="RecommendationCache.id bắt buộc và không được để trống",
            )
        now = datetime.now(timezone.utc)
        if self.generated_at is None:
            self.generated_at = now

    @property
    def is_expired(self) -> bool:
        if self.generated_at is None:
            return True
        expiry = self.generated_at.timestamp() + self.ttl_seconds
        return datetime.now(timezone.utc).timestamp() > expiry

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_type": self.item_type,
            "items": self.items,
            "score": self.score,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationCache":
        return cls(
            id=data["id"],
            user_id=data.get("user_id", ""),
            item_type=data.get("item_type", ""),
            items=data.get("items", []),
            score=data.get("score", 0.0),
            ttl_seconds=data.get("ttl_seconds", 3600),
        )


@dataclass
class ABTestConfig:
    """Cấu hình A/B test cho recommendation strategies.

    Attributes:
        id: ID duy nhất của A/B test
        name: Tên mô tả của experiment
        variations: Danh sách recommendation variation names
        traffic_split: Tỷ lệ phân chia traffic (phải tổng = 1.0)
        success_metric: Metric đánh giá thành công
        min_sample_size: Số lượng mẫu tối thiểu
        metadata: Dữ liệu bổ sung
    """
    id: str
    name: str
    variations: list[str] = field(default_factory=list)
    traffic_split: list[float] = field(default_factory=list)
    success_metric: str = "click_through_rate"
    min_sample_size: int = 1000
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                reason="ABTestConfig.id bắt buộc và không được để trống",
            )
        if len(self.variations) != len(self.traffic_split):
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="Số lượng variations phải bằng số lượng traffic_split",
            )
        if self.traffic_split and abs(sum(self.traffic_split) - 1.0) > 0.001:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"traffic_split phải tổng bằng 1.0, nhận được: {sum(self.traffic_split)}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "variations": self.variations,
            "traffic_split": self.traffic_split,
            "success_metric": self.success_metric,
            "min_sample_size": self.min_sample_size,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABTestConfig":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            variations=data.get("variations", []),
            traffic_split=data.get("traffic_split", []),
            success_metric=data.get("success_metric", "click_through_rate"),
            min_sample_size=data.get("min_sample_size", 1000),
            metadata=data.get("metadata", {}),
        )
