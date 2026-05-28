# coding: utf-8
"""
Tests cho CP10 recipes.py — 12 recipe functions.

Test coverage:
- elasticsearch_recipe
- meilisearch_recipe
- opensearch_recipe
- vector_search_recipe
- geospatial_search_recipe
- faceted_search_recipe
- hybrid_search_recipe
- fulltext_query_recipe
- vector_query_recipe
- geo_query_recipe
- facet_query_recipe
- hybrid_query_recipe

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_search.recipes import (
    elasticsearch_recipe,
    meilisearch_recipe,
    opensearch_recipe,
    vector_search_recipe,
    geospatial_search_recipe,
    faceted_search_recipe,
    hybrid_search_recipe,
    fulltext_query_recipe,
    vector_query_recipe,
    geo_query_recipe,
    facet_query_recipe,
    hybrid_query_recipe,
)
from midicoder.packs.cp_full_search.models import (
    AggregationFunction,
    FacetType,
    GeoOperation,
    SearchCollection,
    SearchIndex,
    SearchProviderType,
    SearchQuery,
    SearchQueryType,
    SyncStrategy,
    SyncTrigger,
    VectorSimilarityMetric,
    VectorIndexType,
)


class TestElasticsearchRecipe:
    """Tests cho elasticsearch_recipe."""

    def test_returns_search_index(self):
        result = elasticsearch_recipe()
        assert isinstance(result, SearchIndex)

    def test_provider_is_elasticsearch(self):
        result = elasticsearch_recipe()
        assert result.provider == SearchProviderType.ELASTICSEARCH

    def test_default_sync_strategy(self):
        result = elasticsearch_recipe()
        assert result.sync_strategy == SyncStrategy.NEAR_REALTIME

    def test_default_sync_trigger(self):
        result = elasticsearch_recipe()
        assert result.sync_trigger == SyncTrigger.EVENT

    def test_tenant_isolated_default(self):
        result = elasticsearch_recipe()
        assert result.tenant_isolated is True

    def test_custom_index_id(self):
        result = elasticsearch_recipe(index_id="my_custom_idx")
        assert result.id == "my_custom_idx"

    def test_vector_support_adds_vector_column(self):
        result = elasticsearch_recipe(vector_support=True)
        types = [c.column_type for c in result.columns]
        assert "vector" in types

    def test_geo_support_adds_geo_column(self):
        result = elasticsearch_recipe(geo_support=True)
        types = [c.column_type for c in result.columns]
        assert "geo" in types

    def test_custom_sync_strategy(self):
        result = elasticsearch_recipe(sync_strategy=SyncStrategy.REALTIME)
        assert result.sync_strategy == SyncStrategy.REALTIME


class TestMeilisearchRecipe:
    """Tests cho meilisearch_recipe."""

    def test_returns_search_index(self):
        result = meilisearch_recipe()
        assert isinstance(result, SearchIndex)

    def test_provider_is_meilisearch(self):
        result = meilisearch_recipe()
        assert result.provider == SearchProviderType.MEILISEARCH

    def test_default_sync_strategy(self):
        result = meilisearch_recipe()
        assert result.sync_strategy == SyncStrategy.REALTIME

    def test_default_sync_trigger(self):
        result = meilisearch_recipe()
        assert result.sync_trigger == SyncTrigger.EVENT

    def test_custom_index_id(self):
        result = meilisearch_recipe(index_id="ms_idx")
        assert result.id == "ms_idx"


class TestOpensearchRecipe:
    """Tests cho opensearch_recipe."""

    def test_returns_search_index(self):
        result = opensearch_recipe()
        assert isinstance(result, SearchIndex)

    def test_provider_is_elasticsearch(self):
        result = opensearch_recipe()
        assert result.provider == SearchProviderType.ELASTICSEARCH

    def test_default_sync_strategy(self):
        result = opensearch_recipe()
        assert result.sync_strategy == SyncStrategy.NEAR_REALTIME

    def test_custom_index_id(self):
        result = opensearch_recipe(index_id="os_idx")
        assert result.id == "os_idx"


class TestVectorSearchRecipe:
    """Tests cho vector_search_recipe."""

    def test_returns_vector_search_index(self):
        from midicoder.packs.cp_full_search.models import VectorSearchIndex
        result = vector_search_recipe()
        assert isinstance(result, VectorSearchIndex)

    def test_default_dimensions(self):
        result = vector_search_recipe()
        assert result.vector_column.dimensions == 768

    def test_default_similarity_cosine(self):
        result = vector_search_recipe()
        assert result.vector_column.similarity_metric == VectorSimilarityMetric.COSINE

    def test_default_index_type_hnsw(self):
        result = vector_search_recipe()
        assert result.vector_column.index_type == VectorIndexType.HNSW

    def test_accepts_custom_dimensions(self):
        result = vector_search_recipe(dimensions=1536)
        assert result.vector_column.dimensions == 1536

    def test_accepts_custom_metric(self):
        result = vector_search_recipe(metric=VectorSimilarityMetric.EUCLIDEAN)
        assert result.vector_column.similarity_metric == VectorSimilarityMetric.EUCLIDEAN

    def test_accepts_custom_top_k(self):
        result = vector_search_recipe(top_k=50)
        assert result.top_k == 50

    def test_default_id(self):
        result = vector_search_recipe()
        assert result.id == "semantic_search"


class TestGeospatialSearchRecipe:
    """Tests cho geospatial_search_recipe."""

    def test_returns_geo_search_index(self):
        from midicoder.packs.cp_full_search.models import GeoSearchIndex
        result = geospatial_search_recipe()
        assert isinstance(result, GeoSearchIndex)

    def test_default_geo_type_point(self):
        result = geospatial_search_recipe()
        assert result.geo_column.geo_type == "point"

    def test_default_crs_wgs84(self):
        result = geospatial_search_recipe()
        assert result.geo_column.crs == "WGS84"

    def test_has_circle_operation(self):
        result = geospatial_search_recipe()
        assert GeoOperation.CIRCLE in result.operations

    def test_has_distance_operation(self):
        result = geospatial_search_recipe()
        assert GeoOperation.DISTANCE in result.operations

    def test_tenant_isolated_default(self):
        result = geospatial_search_recipe()
        assert result.tenant_isolated is True

    def test_custom_geo_column_name(self):
        result = geospatial_search_recipe(geo_column_name="coordinates")
        assert result.geo_column.name == "coordinates"

    def test_custom_operations(self):
        result = geospatial_search_recipe(operations=[GeoOperation.POLYGON])
        assert GeoOperation.POLYGON in result.operations


class TestFacetedSearchRecipe:
    """Tests cho faceted_search_recipe."""

    def test_returns_faceted_search_index(self):
        from midicoder.packs.cp_full_search.models import FacetedSearchIndex
        result = faceted_search_recipe()
        assert isinstance(result, FacetedSearchIndex)

    def test_has_default_facets(self):
        result = faceted_search_recipe()
        assert len(result.facets) == 3  # category, price_range, rating

    def test_has_term_facet(self):
        result = faceted_search_recipe()
        facet_types = [f.facet_type for f in result.facets]
        assert FacetType.TERM in facet_types

    def test_has_range_facet(self):
        result = faceted_search_recipe()
        facet_types = [f.facet_type for f in result.facets]
        assert FacetType.RANGE in facet_types

    def test_has_histogram_facet(self):
        result = faceted_search_recipe()
        facet_types = [f.facet_type for f in result.facets]
        assert FacetType.HISTOGRAM in facet_types

    def test_custom_facets_override(self):
        from midicoder.packs.cp_full_search.models import Facet
        custom = [Facet(id="custom", facet_type=FacetType.TERM, source_column="brand")]
        result = faceted_search_recipe(facets=custom)
        assert len(result.facets) == 1
        assert result.facets[0].id == "custom"

    def test_tenant_isolated_default(self):
        result = faceted_search_recipe()
        assert result.tenant_isolated is True


class TestHybridSearchRecipe:
    """Tests cho hybrid_search_recipe."""

    def test_returns_vector_search_index(self):
        from midicoder.packs.cp_full_search.models import VectorSearchIndex
        result = hybrid_search_recipe()
        assert isinstance(result, VectorSearchIndex)

    def test_has_vector_column(self):
        result = hybrid_search_recipe()
        assert result.vector_column is not None

    def test_has_text_columns(self):
        result = hybrid_search_recipe()
        assert len(result.text_columns) >= 2  # title, description, tags

    def test_text_column_names(self):
        result = hybrid_search_recipe()
        names = [c.name for c in result.text_columns]
        assert "title" in names
        assert "description" in names

    def test_vietnamese_analyser(self):
        result = hybrid_search_recipe()
        for col in result.text_columns:
            if col.name in ("title", "description"):
                assert col.analyser == "vietnamese"


class TestFulltextQueryRecipe:
    """Tests cho fulltext_query_recipe."""

    def test_returns_search_query(self):
        result = fulltext_query_recipe()
        assert isinstance(result, SearchQuery)

    def test_query_type_is_fulltext(self):
        result = fulltext_query_recipe()
        assert result.query_type == SearchQueryType.FULLTEXT

    def test_accepts_custom_fields(self):
        result = fulltext_query_recipe(fields=["name", "email", "phone"])
        assert result.fields == ["name", "email", "phone"]

    def test_accepts_custom_size(self):
        result = fulltext_query_recipe(default_size=50)
        assert result.default_size == 50

    def test_accepts_custom_target_index(self):
        result = fulltext_query_recipe(target_index="products")
        assert result.target_index == "products"

    def test_tenant_isolated_default(self):
        result = fulltext_query_recipe()
        assert result.tenant_isolated is True


class TestVectorQueryRecipe:
    """Tests cho vector_query_recipe."""

    def test_returns_search_query(self):
        result = vector_query_recipe()
        assert isinstance(result, SearchQuery)

    def test_query_type_is_vector(self):
        result = vector_query_recipe()
        assert result.query_type == SearchQueryType.VECTOR

    def test_default_target_index(self):
        result = vector_query_recipe()
        assert result.target_index == "semantic_search"

    def test_default_size(self):
        result = vector_query_recipe()
        assert result.default_size == 10


class TestGeoQueryRecipe:
    """Tests cho geo_query_recipe."""

    def test_returns_search_query(self):
        result = geo_query_recipe()
        assert isinstance(result, SearchQuery)

    def test_query_type_is_geo(self):
        result = geo_query_recipe()
        assert result.query_type == SearchQueryType.GEO

    def test_default_target_index(self):
        result = geo_query_recipe()
        assert result.target_index == "geo_search"

    def test_default_size(self):
        result = geo_query_recipe()
        assert result.default_size == 20


class TestFacetQueryRecipe:
    """Tests cho facet_query_recipe."""

    def test_returns_search_query(self):
        result = facet_query_recipe()
        assert isinstance(result, SearchQuery)

    def test_query_type_is_facet(self):
        result = facet_query_recipe()
        assert result.query_type == SearchQueryType.FACET

    def test_default_target_index(self):
        result = facet_query_recipe()
        assert result.target_index == "faceted_search"


class TestHybridQueryRecipe:
    """Tests cho hybrid_query_recipe."""

    def test_returns_search_query(self):
        result = hybrid_query_recipe()
        assert isinstance(result, SearchQuery)

    def test_query_type_is_hybrid(self):
        result = hybrid_query_recipe()
        assert result.query_type == SearchQueryType.HYBRID

    def test_default_target_index(self):
        result = hybrid_query_recipe()
        assert result.target_index == "hybrid_search"

    def test_default_fields(self):
        result = hybrid_query_recipe()
        assert "title" in result.fields
        assert "description" in result.fields

    def test_accepts_custom_fields(self):
        result = hybrid_query_recipe(fields=["name", "bio"])
        assert result.fields == ["name", "bio"]


class TestRecipeIntegration:
    """Integration tests — kết hợp nhiều recipes."""

    def test_combine_elasticsearch_and_vector(self):
        base = elasticsearch_recipe()
        vec = vector_search_recipe()
        collection = SearchCollection()
        collection.add_index(base)
        collection.add_vector_index(vec)
        assert collection.total_count == 1
        assert collection.total_vector_count == 1

    def test_combine_hybrid_and_queries(self):
        ft_q = fulltext_query_recipe()
        vec_q = vector_query_recipe()
        collection = SearchCollection()
        collection.add_query(ft_q)
        collection.add_query(vec_q)
        assert len(collection.queries) == 2

    def test_all_recipes_no_crash(self):
        """Verify all recipes can be called without error."""
        elasticsearch_recipe()
        meilisearch_recipe()
        opensearch_recipe()
        vector_search_recipe()
        geospatial_search_recipe()
        faceted_search_recipe()
        hybrid_search_recipe()
        fulltext_query_recipe()
        vector_query_recipe()
        geo_query_recipe()
        facet_query_recipe()
        hybrid_query_recipe()
