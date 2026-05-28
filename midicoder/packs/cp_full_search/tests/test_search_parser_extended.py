# coding: utf-8
"""
Extended tests cho SearchParser — advanced parsing (vector/geo/faceted/query).

Test coverage:
- _parse_vector_index: valid, missing column, zero dimensions
- _parse_geo_index: valid, missing column, invalid geo_type
- _parse_faceted_index: valid, empty facets, missing facet fields
- _parse_query: valid, missing id, auto-correct negative size
- parse_from_metadata: combined metadata with all 5 search keys
- Multiple indices of each type
- Enum mapping correctness

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_search.parser import SearchParser
from midicoder.packs.cp_full_search.models import (
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


class TestParseVectorIndex:
    """Tests cho _parse_vector_index."""

    def setup_method(self):
        self.parser = SearchParser()

    def test_valid_vector_index(self):
        raw = {
            "id": "semantic",
            "provider": "meilisearch",
            "vector_column": {"name": "embedding", "dimensions": 768, "similarity_metric": "cosine"},
            "top_k": 10,
        }
        result = self.parser._parse_vector_index(raw)
        assert result.id == "semantic"
        assert result.provider == SearchProviderType.MEILISEARCH
        assert result.vector_column.dimensions == 768
        assert result.vector_column.similarity_metric == VectorSimilarityMetric.COSINE
        assert result.top_k == 10

    def test_default_top_k(self):
        raw = {
            "id": "v1",
            "vector_column": {"name": "e", "dimensions": 128},
        }
        result = self.parser._parse_vector_index(raw)
        assert result.top_k == 10

    def test_missing_id_raises_error(self):
        raw = {"vector_column": {"name": "e", "dimensions": 128}}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_vector_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_missing_vector_column_raises_error(self):
        raw = {"id": "no_col"}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_vector_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_zero_dimensions_raises_error(self):
        raw = {"id": "v", "vector_column": {"name": "e", "dimensions": 0}}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_vector_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_all_similarity_metrics(self):
        for metric in ["cosine", "euclidean", "dot_product", "manhattan", "hamming"]:
            raw = {
                "id": f"v_{metric}",
                "vector_column": {"name": "e", "dimensions": 64, "similarity_metric": metric},
            }
            result = self.parser._parse_vector_index(raw)
            assert result.vector_column.similarity_metric.value == metric

    def test_all_index_types(self):
        for idx_type in ["hnsw", "ivf_flat", "ivf_pq", "flat"]:
            raw = {
                "id": f"v_{idx_type}",
                "vector_column": {"name": "e", "dimensions": 64, "index_type": idx_type},
            }
            result = self.parser._parse_vector_index(raw)
            assert result.vector_column.index_type.value == idx_type


class TestParseGeoIndex:
    """Tests cho _parse_geo_index."""

    def setup_method(self):
        self.parser = SearchParser()

    def test_valid_geo_index(self):
        raw = {
            "id": "locations",
            "geo_column": {"name": "location", "geo_type": "point"},
            "operations": ["bounding_box", "distance"],
        }
        result = self.parser._parse_geo_index(raw)
        assert result.id == "locations"
        assert result.geo_column.name == "location"
        assert result.geo_column.geo_type == "point"
        assert GeoOperation.BOUNDING_BOX in result.operations
        assert GeoOperation.DISTANCE in result.operations

    def test_default_geo_type(self):
        raw = {"id": "g1", "geo_column": {"name": "loc"}}
        result = self.parser._parse_geo_index(raw)
        assert result.geo_column.geo_type == "point"

    def test_default_crs(self):
        raw = {"id": "g1", "geo_column": {"name": "loc"}}
        result = self.parser._parse_geo_index(raw)
        assert result.geo_column.crs == "WGS84"

    def test_missing_id_raises_error(self):
        raw = {"geo_column": {"name": "loc"}}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_geo_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_missing_geo_column_raises_error(self):
        raw = {"id": "no_col"}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_geo_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_invalid_geo_type_raises_error(self):
        raw = {"id": "bad", "geo_column": {"name": "loc", "geo_type": "invalid"}}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_geo_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_all_geo_types(self):
        for gt in ["point", "line", "polygon", "multipoint", "multipolygon"]:
            raw = {"id": f"g_{gt}", "geo_column": {"name": "loc", "geo_type": gt}}
            result = self.parser._parse_geo_index(raw)
            assert result.geo_column.geo_type == gt

    def test_all_operations(self):
        raw = {
            "id": "ops",
            "geo_column": {"name": "loc"},
            "operations": ["bounding_box", "circle", "polygon", "distance"],
        }
        result = self.parser._parse_geo_index(raw)
        assert len(result.operations) == 4


class TestParseFacetedIndex:
    """Tests cho _parse_faceted_index."""

    def setup_method(self):
        self.parser = SearchParser()

    def test_valid_faceted_index(self):
        raw = {
            "id": "products",
            "facets": [
                {"id": "brand", "facet_type": "term", "source_column": "brand"},
                {"id": "price", "facet_type": "range", "source_column": "price", "range_bounds": [0, 50, 200]},
            ],
        }
        result = self.parser._parse_faceted_index(raw)
        assert result.id == "products"
        assert len(result.facets) == 2
        assert result.facets[0].facet_type == FacetType.TERM
        assert result.facets[1].range_bounds == [0, 50, 200]

    def test_empty_facets_list(self):
        raw = {"id": "empty_facets", "facets": []}
        result = self.parser._parse_faceted_index(raw)
        assert result.id == "empty_facets"
        assert len(result.facets) == 0

    def test_missing_id_raises_error(self):
        raw = {"facets": [{"id": "f1", "facet_type": "term", "source_column": "c"}]}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_faceted_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_missing_facet_id_raises_error(self):
        raw = {"id": "fi", "facets": [{"facet_type": "term", "source_column": "c"}]}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_faceted_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_missing_facet_source_raises_error(self):
        raw = {"id": "fi", "facets": [{"id": "f1", "facet_type": "term"}]}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_faceted_index(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_INVALID_COLUMN_TYPE

    def test_all_facet_types(self):
        for ft in ["term", "range", "date_histogram", "histogram", "geo_distance"]:
            raw = {"id": f"f_{ft}", "facets": [{"id": "ff", "facet_type": ft, "source_column": "c"}]}
            result = self.parser._parse_faceted_index(raw)
            assert result.facets[0].facet_type.value == ft


class TestParseQuery:
    """Tests cho _parse_query."""

    def setup_method(self):
        self.parser = SearchParser()

    def test_valid_query(self):
        raw = {
            "id": "search_products",
            "query_type": "fulltext",
            "target_index": "products_idx",
            "fields": ["title", "description"],
            "default_size": 15,
        }
        result = self.parser._parse_query(raw)
        assert result.id == "search_products"
        assert result.query_type == SearchQueryType.FULLTEXT
        assert result.default_size == 15

    def test_default_query_type(self):
        raw = {"id": "q1"}
        result = self.parser._parse_query(raw)
        assert result.query_type == SearchQueryType.FULLTEXT

    def test_default_size(self):
        raw = {"id": "q1"}
        result = self.parser._parse_query(raw)
        assert result.default_size == 20

    def test_negative_size_fixed(self):
        raw = {"id": "q1", "default_size": -5}
        result = self.parser._parse_query(raw)
        assert result.default_size == 20

    def test_missing_id_raises_error(self):
        raw = {"query_type": "fulltext"}
        with pytest.raises(MidicoderError) as exc_info:
            self.parser._parse_query(raw)
        assert exc_info.value.code == ErrorCode.MDC-F08_EMPTY_INDEX_NAME

    def test_all_query_types(self):
        for qt in ["fulltext", "vector", "geo", "facet", "hybrid"]:
            raw = {"id": f"q_{qt}", "query_type": qt}
            result = self.parser._parse_query(raw)
            assert result.query_type.value == qt


class TestParseMetadataCombined:
    """Tests cho parse_from_metadata với combined metadata."""

    def test_parse_all_five_keys(self):
        parser = SearchParser()
        meta = {
            "search_indices": [
                {"id": "basic", "columns": [{"name": "title", "searchable": True}], "sync_strategy": "sync"}
            ],
            "vector_search_indices": [
                {"id": "vec", "vector_column": {"name": "emb", "dimensions": 768}}
            ],
            "geo_search_indices": [
                {"id": "geo", "geo_column": {"name": "loc"}}
            ],
            "faceted_search_indices": [
                {"id": "facet", "facets": [{"id": "b", "facet_type": "term", "source_column": "brand"}]}
            ],
            "search_queries": [
                {"id": "q1", "query_type": "hybrid"}
            ],
        }
        result = parser.parse_from_metadata(meta)
        assert result.total_count == 1
        assert result.total_vector_count == 1
        assert result.total_geo_count == 1
        assert result.total_faceted_count == 1
        assert len(result.queries) == 1

    def test_parse_empty_metadata(self):
        parser = SearchParser()
        result = parser.parse_from_metadata({})
        assert result.total_count == 0
        assert result.total_vector_count == 0

    def test_parse_only_vector(self):
        parser = SearchParser()
        meta = {
            "vector_search_indices": [
                {"id": "v1", "vector_column": {"name": "e", "dimensions": 128}}
            ]
        }
        result = parser.parse_from_metadata(meta)
        assert result.total_vector_count == 1
        assert result.total_count == 0

    def test_multiple_indices_same_type(self):
        parser = SearchParser()
        meta = {
            "search_indices": [
                {"id": "i1", "columns": [{"name": "c1", "searchable": True}], "sync_strategy": "sync"},
                {"id": "i2", "columns": [{"name": "c2", "searchable": True}], "sync_strategy": "async"},
                {"id": "i3", "columns": [{"name": "c3", "searchable": True}], "sync_strategy": "eventual"},
            ]
        }
        result = parser.parse_from_metadata(meta)
        assert result.total_count == 3
        assert result.get_by_id("i2") is not None

    def test_invalid_provider_handled(self):
        parser = SearchParser()
        meta = {
            "search_indices": [
                {"id": "bad_prov", "provider": "invalid_provider", "columns": [{"name": "c", "searchable": True}], "sync_strategy": "sync"}
            ]
        }
        result = parser.parse_from_metadata(meta)
        assert result.get_by_id("bad_prov").provider == SearchProviderType.ELASTICSEARCH


class TestSearchParserIntegration:
    """Integration tests cho toàn bộ parser pipeline."""

    def test_full_metadata_pipeline(self):
        """Test full flow: raw dict → SearchCollection → to_dict → from_dict"""
        parser = SearchParser()
        raw = {
            "search_indices": [
                {
                    "id": "documents",
                    "provider": "elasticsearch",
                    "columns": [
                        {"name": "title", "searchable": True},
                        {"name": "content", "searchable": True},
                    ],
                    "sync_strategy": "sync",
                    "tenant_isolated": True,
                }
            ],
            "vector_search_indices": [
                {
                    "id": "embeddings",
                    "vector_column": {
                        "name": "vector",
                        "dimensions": 1536,
                        "similarity_metric": "cosine",
                        "index_type": "hnsw",
                    },
                    "top_k": 20,
                }
            ],
            "geo_search_indices": [
                {
                    "id": "places",
                    "geo_column": {"name": "coordinates", "geo_type": "point"},
                    "operations": ["circle", "distance"],
                }
            ],
            "faceted_search_indices": [
                {
                    "id": "categories",
                    "facets": [
                        {"id": "cat", "facet_type": "term", "source_column": "category"},
                        {"id": "price", "facet_type": "range", "source_column": "price", "range_bounds": [0, 100, 1000]},
                    ],
                }
            ],
            "search_queries": [
                {"id": "search_all", "query_type": "hybrid", "target_index": "documents", "fields": ["title", "content"], "default_size": 25},
                {"id": "search_nearby", "query_type": "geo"},
                {"id": "search_similar", "query_type": "vector"},
            ],
        }

        collection = parser.parse_from_metadata(raw)

        # Verify all types parsed
        assert collection.total_count == 1
        assert collection.total_vector_count == 1
        assert collection.total_geo_count == 1
        assert collection.total_faceted_count == 1
        assert len(collection.queries) == 3

        # Verify specific values
        doc_idx = collection.get_by_id("documents")
        assert doc_idx.tenant_isolated is True
        assert len(doc_idx.columns) == 2

        vec_idx = collection.get_vector_by_id("embeddings")
        assert vec_idx.vector_column.dimensions == 1536
        assert vec_idx.top_k == 20

        geo_idx = collection.get_geo_by_id("places")
        assert GeoOperation.CIRCLE in geo_idx.operations

        facet_idx = collection.get_faceted_by_id("categories")
        assert len(facet_idx.facets) == 2

        hybrid_q = collection.get_query_by_id("search_all")
        assert hybrid_q.query_type == SearchQueryType.HYBRID
        assert hybrid_q.default_size == 25

        # Verify roundtrip
        d = collection.to_dict()
        restored = SearchCollection.from_dict(d)
        assert restored.total_count == collection.total_count
        assert restored.total_vector_count == collection.total_vector_count
