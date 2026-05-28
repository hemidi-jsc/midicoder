# coding: utf-8
"""
Search & Indexing Emitter Module (CP10) + Recommendation Engine (CP63).

Module nay dinh nghia cac emitter cho search layer (CP10) + recommendation (CP63):
- Models (CP10): SearchIndex, SearchIndexColumn, SearchProviderType, SyncStrategy, SearchCollection
- Models (CP63): RecommendationAlgorithm, SimilarityMetric, RecommendationConfig, ItemEmbedding,
          UserPreference, RecommendationCache, ABTestConfig
- Parser: SearchParser de parse MIR metadata (CP10)
- Parser (CP63): RecommendationIR, parse_recommendation_to_ir
- FastAPI Emitter: FastAPISearchEmitter
- NestJS Emitter: NestJSSearchEmitter
- Angular Emitter: AngularEmitter
- React Emitter: ReactEmitter
- Recipes (CP10): Search recipes (provider, vector, geo, faceted, hybrid, query)
- Recipes (CP63): RecommendationRecipeOutput, collaborative_filtering_recipe, content_based_recipe,
          hybrid_recommendation_recipe, popularity_fallback_recipe, recommendation_ab_test_recipe

KPI-029: Tenant Isolation — tenant_isolated=True mac dinh cho moi index.

Author: Midicoder Team
Version: 2.0.0
"""

from midicoder.packs.cp_full_search.models import (
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
    SearchIndexColumn,
    SearchIndex,
    SearchQuery,
    SearchQueryType,
    SearchCollection,
    VectorSimilarityMetric,
    VectorIndexType,
    VectorIndexColumn,
    VectorSearchIndex,
    GeoOperation,
    GeoSearchColumn,
    GeoSearchIndex,
    FacetType,
    AggregationFunction,
    Facet,
    FacetedSearchIndex,
    # CP63 models
    RecommendationAlgorithm,
    SimilarityMetric,
    RecommendationConfig,
    ItemEmbedding,
    UserPreference,
    RecommendationCache,
    ABTestConfig,
)
from midicoder.packs.cp_full_search.parser import (
    SearchParser,
    # CP63 parser
    RecommendationIR,
    parse_recommendation_configs,
    parse_embeddings,
    parse_preferences,
    parse_ab_tests,
    parse_recommendation_to_ir,
)
from midicoder.packs.cp_full_search.fastapi import FastAPISearchEmitter
from midicoder.packs.cp_full_search.nestjs import NestJSSearchEmitter
from midicoder.packs.cp_full_search.angular import AngularEmitter
from midicoder.packs.cp_full_search.react import ReactEmitter
from midicoder.packs.cp_full_search.recipes import (
    # CP63 recipes
    RecommendationRecipeOutput,
    collaborative_filtering_recipe,
    content_based_recipe,
    hybrid_recommendation_recipe,
    popularity_fallback_recipe,
    recommendation_ab_test_recipe,
)

__all__ = [
    # Models — basic search (CP10)
    "SearchProviderType",
    "SyncStrategy",
    "SyncTrigger",
    "SearchIndexColumn",
    "SearchIndex",
    "SearchQuery",
    "SearchQueryType",
    "SearchCollection",
    # Models — vector search (CP10)
    "VectorSimilarityMetric",
    "VectorIndexType",
    "VectorIndexColumn",
    "VectorSearchIndex",
    # Models — geospatial search (CP10)
    "GeoOperation",
    "GeoSearchColumn",
    "GeoSearchIndex",
    # Models — faceted aggregation (CP10)
    "FacetType",
    "AggregationFunction",
    "Facet",
    "FacetedSearchIndex",
    # Models — recommendation (CP63)
    "RecommendationAlgorithm",
    "SimilarityMetric",
    "RecommendationConfig",
    "ItemEmbedding",
    "UserPreference",
    "RecommendationCache",
    "ABTestConfig",
    # Parser (CP10)
    "SearchParser",
    # Parser (CP63)
    "RecommendationIR",
    "parse_recommendation_configs",
    "parse_embeddings",
    "parse_preferences",
    "parse_ab_tests",
    "parse_recommendation_to_ir",
    # Emitters (CP10)
    "FastAPISearchEmitter",
    "NestJSSearchEmitter",
    "AngularEmitter",
    "ReactEmitter",
    # Recipes (CP63)
    "RecommendationRecipeOutput",
    "collaborative_filtering_recipe",
    "content_based_recipe",
    "hybrid_recommendation_recipe",
    "popularity_fallback_recipe",
    "recommendation_ab_test_recipe",
]
