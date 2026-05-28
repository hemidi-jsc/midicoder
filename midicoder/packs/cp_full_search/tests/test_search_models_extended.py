# coding: utf-8
"""
Extended tests cho CP10 advanced models (vector/geo/faceted/query).

Test coverage:
- SearchQueryType enum
- SearchQuery: validation, serialization, roundtrip
- VectorSimilarityMetric, VectorIndexType enums
- VectorIndexColumn: validation, serialization
- VectorSearchIndex: validation, serialization
- GeoOperation enum
- GeoSearchColumn: validation, serialization
- GeoSearchIndex: validation, serialization
- FacetType, AggregationFunction enums
- Facet: validation, serialization
- FacetedSearchIndex: validation, serialization
- SearchCollection: advanced accessor methods, full serialization

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
    VectorIndexColumn,
    VectorIndexType,
    VectorSearchIndex,
    VectorSimilarityMetric,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test SearchQueryType Enum
# ============================================================================


class TestSearchQueryType:
    """Tests cho SearchQueryType enum."""

    def test_fulltext_value(self):
        assert SearchQueryType.FULLTEXT.value == "fulltext"

    def test_vector_value(self):
        assert SearchQueryType.VECTOR.value == "vector"

    def test_geo_value(self):
        assert SearchQueryType.GEO.value == "geo"

    def test_facet_value(self):
        assert SearchQueryType.FACET.value == "facet"

    def test_hybrid_value(self):
        assert SearchQueryType.HYBRID.value == "hybrid"

    def test_from_string(self):
        assert SearchQueryType("fulltext") == SearchQueryType.FULLTEXT
        assert SearchQueryType("vector") == SearchQueryType.VECTOR


# ============================================================================
# Test SearchQuery
# ============================================================================


class TestSearchQuery:
    """Tests cho SearchQuery model."""

    def test_valid_fulltext_query(self):
        q = SearchQuery(id="search_products", query_type=SearchQueryType.FULLTEXT)
        assert q.id == "search_products"
        assert q.query_type == SearchQueryType.FULLTEXT

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            SearchQuery(id="")
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_negative_default_size_fixed(self):
        q = SearchQuery(id="q1", default_size=-5)
        assert q.default_size == 20  # auto-corrected

    def test_to_dict(self):
        q = SearchQuery(
            id="q1",
            query_type=SearchQueryType.HYBRID,
            target_index="hybrid_idx",
            fields=["title", "description"],
            default_size=10,
            tenant_isolated=True,
        )
        d = q.to_dict()
        assert d["id"] == "q1"
        assert d["query_type"] == "hybrid"
        assert d["target_index"] == "hybrid_idx"
        assert d["fields"] == ["title", "description"]

    def test_from_dict(self):
        d = {"id": "geo_q", "query_type": "geo", "target_index": "geo_idx"}
        q = SearchQuery.from_dict(d)
        assert q.id == "geo_q"
        assert q.query_type == SearchQueryType.GEO

    def test_roundtrip(self):
        original = SearchQuery(
            id="rt",
            query_type=SearchQueryType.VECTOR,
            target_index="vec_idx",
            fields=["v"],
            default_size=5,
            default_sort="_score",
            tenant_isolated=False,
        )
        d = original.to_dict()
        restored = SearchQuery.from_dict(d)
        assert restored.id == original.id
        assert restored.query_type == original.query_type
        assert restored.default_size == original.default_size

    def test_default_values(self):
        q = SearchQuery(id="defaults")
        assert q.query_type == SearchQueryType.FULLTEXT
        assert q.default_size == 20
        assert q.tenant_isolated is True


# ============================================================================
# Test Vector Enums
# ============================================================================


class TestVectorSimilarityMetric:
    """Tests cho VectorSimilarityMetric enum."""

    def test_all_values(self):
        assert VectorSimilarityMetric.COSINE.value == "cosine"
        assert VectorSimilarityMetric.EUCLIDEAN.value == "euclidean"
        assert VectorSimilarityMetric.DOT_PRODUCT.value == "dot_product"
        assert VectorSimilarityMetric.MANHATTAN.value == "manhattan"
        assert VectorSimilarityMetric.HAMMING.value == "hamming"


class TestVectorIndexType:
    """Tests cho VectorIndexType enum."""

    def test_all_values(self):
        assert VectorIndexType.HNSW.value == "hnsw"
        assert VectorIndexType.IVF_FLAT.value == "ivf_flat"
        assert VectorIndexType.IVF_PQ.value == "ivf_pq"
        assert VectorIndexType.FLAT.value == "flat"


# ============================================================================
# Test VectorIndexColumn
# ============================================================================


class TestVectorIndexColumn:
    """Tests cho VectorIndexColumn model."""

    def test_valid_column(self):
        c = VectorIndexColumn(name="embedding", dimensions=768)
        assert c.dimensions == 768
        assert c.similarity_metric == VectorSimilarityMetric.COSINE
        assert c.index_type == VectorIndexType.HNSW

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            VectorIndexColumn(name="", dimensions=768)

    def test_zero_dimensions_raises_error(self):
        with pytest.raises(MidicoderError):
            VectorIndexColumn(name="v", dimensions=0)

    def test_to_dict(self):
        c = VectorIndexColumn(name="vec", dimensions=1536, similarity_metric=VectorSimilarityMetric.EUCLIDEAN)
        d = c.to_dict()
        assert d["name"] == "vec"
        assert d["dimensions"] == 1536
        assert d["similarity_metric"] == "euclidean"

    def test_from_dict(self):
        d = {"name": "emb", "dimensions": 384, "index_type": "ivf_flat"}
        c = VectorIndexColumn.from_dict(d)
        assert c.name == "emb"
        assert c.index_type == VectorIndexType.IVF_FLAT

    def test_roundtrip(self):
        original = VectorIndexColumn(name="r", dimensions=512, similarity_metric=VectorSimilarityMetric.DOT_PRODUCT)
        d = original.to_dict()
        restored = VectorIndexColumn.from_dict(d)
        assert restored.dimensions == original.dimensions


# ============================================================================
# Test VectorSearchIndex
# ============================================================================


class TestVectorSearchIndex:
    """Tests cho VectorSearchIndex model."""

    def test_valid_index(self):
        vc = VectorIndexColumn(name="emb", dimensions=768)
        idx = VectorSearchIndex(id="semantic", vector_column=vc)
        assert idx.id == "semantic"
        assert idx.vector_column == vc

    def test_empty_id_raises_error(self):
        vc = VectorIndexColumn(name="emb", dimensions=768)
        with pytest.raises(MidicoderError):
            VectorSearchIndex(id="", vector_column=vc)

    def test_missing_vector_column_raises_error(self):
        with pytest.raises(MidicoderError):
            VectorSearchIndex(id="no_vec", vector_column=None)

    def test_to_dict(self):
        vc = VectorIndexColumn(name="emb", dimensions=768)
        idx = VectorSearchIndex(id="vec_idx", vector_column=vc, top_k=20)
        d = idx.to_dict()
        assert d["id"] == "vec_idx"
        assert d["top_k"] == 20
        assert d["vector_column"]["dimensions"] == 768

    def test_from_dict(self):
        d = {
            "id": "parsed_vec",
            "provider": "meilisearch",
            "vector_column": {"name": "v", "dimensions": 256},
            "top_k": 5,
        }
        idx = VectorSearchIndex.from_dict(d)
        assert idx.id == "parsed_vec"
        assert idx.top_k == 5

    def test_roundtrip(self):
        vc = VectorIndexColumn(name="e", dimensions=1024)
        original = VectorSearchIndex(id="rt", vector_column=vc)
        d = original.to_dict()
        restored = VectorSearchIndex.from_dict(d)
        assert restored.id == original.id


# ============================================================================
# Test Geo Enums
# ============================================================================


class TestGeoOperation:
    """Tests cho GeoOperation enum."""

    def test_all_values(self):
        assert GeoOperation.BOUNDING_BOX.value == "bounding_box"
        assert GeoOperation.CIRCLE.value == "circle"
        assert GeoOperation.POLYGON.value == "polygon"
        assert GeoOperation.DISTANCE.value == "distance"


# ============================================================================
# Test GeoSearchColumn
# ============================================================================


class TestGeoSearchColumn:
    """Tests cho GeoSearchColumn model."""

    def test_valid_column(self):
        c = GeoSearchColumn(name="location")
        assert c.geo_type == "point"
        assert c.crs == "WGS84"

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError):
            GeoSearchColumn(name="")

    def test_invalid_geo_type_raises_error(self):
        with pytest.raises(MidicoderError):
            GeoSearchColumn(name="loc", geo_type="invalid_type")

    def test_to_dict(self):
        c = GeoSearchColumn(name="loc", geo_type="polygon", crs="EPSG:4326")
        d = c.to_dict()
        assert d["geo_type"] == "polygon"
        assert d["crs"] == "EPSG:4326"

    def test_from_dict(self):
        d = {"name": "coords", "geo_type": "multipoint"}
        c = GeoSearchColumn.from_dict(d)
        assert c.geo_type == "multipoint"


# ============================================================================
# Test GeoSearchIndex
# ============================================================================


class TestGeoSearchIndex:
    """Tests cho GeoSearchIndex model."""

    def test_valid_index(self):
        gc = GeoSearchColumn(name="loc")
        idx = GeoSearchIndex(id="geo_idx", geo_column=gc)
        assert idx.id == "geo_idx"

    def test_empty_id_raises_error(self):
        gc = GeoSearchColumn(name="loc")
        with pytest.raises(MidicoderError):
            GeoSearchIndex(id="", geo_column=gc)

    def test_missing_geo_column_raises_error(self):
        with pytest.raises(MidicoderError):
            GeoSearchIndex(id="no_geo", geo_column=None)

    def test_default_operations(self):
        gc = GeoSearchColumn(name="loc")
        idx = GeoSearchIndex(id="default_ops", geo_column=gc)
        assert GeoOperation.CIRCLE in idx.operations
        assert GeoOperation.DISTANCE in idx.operations

    def test_to_dict(self):
        gc = GeoSearchColumn(name="pos")
        idx = GeoSearchIndex(id="d", geo_column=gc)
        d = idx.to_dict()
        assert d["id"] == "d"
        assert "circle" in d["operations"]

    def test_from_dict(self):
        d = {
            "id": "parsed_geo",
            "geo_column": {"name": "g"},
            "operations": ["polygon"],
        }
        idx = GeoSearchIndex.from_dict(d)
        assert idx.id == "parsed_geo"
        assert GeoOperation.POLYGON in idx.operations


# ============================================================================
# Test Facet Enums
# ============================================================================


class TestFacetType:
    """Tests cho FacetType enum."""

    def test_all_values(self):
        assert FacetType.TERM.value == "term"
        assert FacetType.RANGE.value == "range"
        assert FacetType.DATE_HISTOGRAM.value == "date_histogram"
        assert FacetType.HISTOGRAM.value == "histogram"
        assert FacetType.GEO_DISTANCE.value == "geo_distance"


class TestAggregationFunction:
    """Tests cho AggregationFunction enum."""

    def test_all_values(self):
        assert AggregationFunction.COUNT.value == "count"
        assert AggregationFunction.AVG.value == "avg"
        assert AggregationFunction.SUM.value == "sum"
        assert AggregationFunction.MIN.value == "min"
        assert AggregationFunction.MAX.value == "max"


# ============================================================================
# Test Facet
# ============================================================================


class TestFacet:
    """Tests cho Facet model."""

    def test_valid_facet(self):
        f = Facet(id="brand", facet_type=FacetType.TERM, source_column="brand")
        assert f.size == 10

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            Facet(id="", facet_type=FacetType.TERM, source_column="c")

    def test_empty_source_column_raises_error(self):
        with pytest.raises(MidicoderError):
            Facet(id="f1", facet_type=FacetType.TERM, source_column="")

    def test_negative_size_fixed(self):
        f = Facet(id="f1", facet_type=FacetType.TERM, source_column="c", size=-1)
        assert f.size == 10

    def test_to_dict(self):
        f = Facet(id="cat", facet_type=FacetType.TERM, source_column="category", size=20)
        d = f.to_dict()
        assert d["id"] == "cat"
        assert d["facet_type"] == "term"

    def test_from_dict(self):
        d = {"id": "price_r", "facet_type": "range", "source_column": "price", "range_bounds": [0, 100, 500]}
        f = Facet.from_dict(d)
        assert f.facet_type == FacetType.RANGE
        assert f.range_bounds == [0, 100, 500]


# ============================================================================
# Test FacetedSearchIndex
# ============================================================================


class TestFacetedSearchIndex:
    """Tests cho FacetedSearchIndex model."""

    def test_valid_index(self):
        idx = FacetedSearchIndex(id="product_facets")
        assert idx.id == "product_facets"

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            FacetedSearchIndex(id="")

    def test_to_dict(self):
        facet = Facet(id="b", facet_type=FacetType.TERM, source_column="brand")
        idx = FacetedSearchIndex(id="fi", facets=[facet])
        d = idx.to_dict()
        assert len(d["facets"]) == 1

    def test_from_dict(self):
        d = {
            "id": "parsed_facet",
            "facets": [{"id": "c", "facet_type": "term", "source_column": "cat"}],
        }
        idx = FacetedSearchIndex.from_dict(d)
        assert len(idx.facets) == 1

    def test_roundtrip(self):
        facet = Facet(id="r", facet_type=FacetType.TERM, source_column="rc")
        original = FacetedSearchIndex(id="rt", facets=[facet])
        d = original.to_dict()
        restored = FacetedSearchIndex.from_dict(d)
        assert len(restored.facets) == 1


# ============================================================================
# Test SearchCollection — Advanced Accessors & Serialization
# ============================================================================


class TestSearchCollectionAdvanced:
    """Tests cho SearchCollection advanced methods."""

    def test_add_vector_index(self):
        c = SearchCollection()
        vc = VectorIndexColumn(name="e", dimensions=768)
        c.add_vector_index(VectorSearchIndex(id="v1", vector_column=vc))
        assert c.total_vector_count == 1

    def test_add_geo_index(self):
        c = SearchCollection()
        gc = GeoSearchColumn(name="loc")
        c.add_geo_index(GeoSearchIndex(id="g1", geo_column=gc))
        assert c.total_geo_count == 1

    def test_add_faceted_index(self):
        c = SearchCollection()
        c.add_faceted_index(FacetedSearchIndex(id="f1"))
        assert c.total_faceted_count == 1

    def test_add_query(self):
        c = SearchCollection()
        c.add_query(SearchQuery(id="q1"))
        assert len(c.queries) == 1

    def test_get_vector_by_id_found(self):
        c = SearchCollection()
        vc = VectorIndexColumn(name="e", dimensions=768)
        c.add_vector_index(VectorSearchIndex(id="v_target", vector_column=vc))
        result = c.get_vector_by_id("v_target")
        assert result is not None
        assert result.id == "v_target"

    def test_get_vector_by_id_not_found(self):
        c = SearchCollection()
        assert c.get_vector_by_id("missing") is None

    def test_get_geo_by_id_found(self):
        c = SearchCollection()
        gc = GeoSearchColumn(name="loc")
        c.add_geo_index(GeoSearchIndex(id="g_target", geo_column=gc))
        result = c.get_geo_by_id("g_target")
        assert result is not None

    def test_get_faceted_by_id_found(self):
        c = SearchCollection()
        c.add_faceted_index(FacetedSearchIndex(id="f_target"))
        result = c.get_faceted_by_id("f_target")
        assert result is not None

    def test_get_query_by_id_found(self):
        c = SearchCollection()
        c.add_query(SearchQuery(id="q_target"))
        result = c.get_query_by_id("q_target")
        assert result is not None
        assert result.id == "q_target"

    def test_to_dict_with_all_types(self):
        c = SearchCollection()
        c.add_index(SearchIndex(id="basic"))
        vc = VectorIndexColumn(name="e", dimensions=128)
        c.add_vector_index(VectorSearchIndex(id="vec", vector_column=vc))
        gc = GeoSearchColumn(name="loc")
        c.add_geo_index(GeoSearchIndex(id="geo", geo_column=gc))
        c.add_faceted_index(FacetedSearchIndex(id="facet"))
        c.add_query(SearchQuery(id="q"))
        d = c.to_dict()
        assert len(d["indices"]) == 1
        assert len(d["vector_indices"]) == 1
        assert len(d["geo_indices"]) == 1
        assert len(d["faceted_indices"]) == 1
        assert len(d["queries"]) == 1

    def test_from_dict_with_all_types(self):
        d = {
            "indices": [{"id": "basic"}],
            "vector_indices": [{"id": "vec", "vector_column": {"name": "e", "dimensions": 64}}],
            "geo_indices": [{"id": "geo", "geo_column": {"name": "g"}}],
            "faceted_indices": [{"id": "facet"}],
            "queries": [{"id": "q", "query_type": "fulltext"}],
        }
        c = SearchCollection.from_dict(d)
        assert c.total_count == 1
        assert c.total_vector_count == 1
        assert c.total_geo_count == 1
        assert c.total_faceted_count == 1
        assert len(c.queries) == 1
