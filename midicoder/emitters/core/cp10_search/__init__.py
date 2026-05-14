# coding: utf-8
"""
Search & Indexing Emitter Module (CP10).

Module nay dinh nghia cac emitter cho search layer (CP10):
- Models: SearchIndex, SearchIndexColumn, SearchProviderType, SyncStrategy, SearchCollection
- Parser: SearchParser de parse MIR metadata
- FastAPI Emitter: FastAPISearchEmitter (Elasticsearch config, index manager, search service)
- NestJS Emitter: NestJSSearchEmitter (SearchModule, SearchService, decorators)
- Angular Emitter: AngularEmitter (SearchService, SearchNgModule, models)
- React Emitter: ReactEmitter (SearchProvider, useSearch, types, utils)

KPI-029: Tenant Isolation — tenant_isolated=True mac dinh cho moi index.

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp10_search.models import (
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
)
from midicoder.emitters.core.cp10_search.parser import SearchParser
from midicoder.emitters.core.cp10_search.fastapi import FastAPISearchEmitter
from midicoder.emitters.core.cp10_search.nestjs import NestJSSearchEmitter
from midicoder.emitters.core.cp10_search.angular import AngularEmitter
from midicoder.emitters.core.cp10_search.react import ReactEmitter

__all__ = [
    # Models — basic
    "SearchProviderType",
    "SyncStrategy",
    "SyncTrigger",
    "SearchIndexColumn",
    "SearchIndex",
    "SearchQuery",
    "SearchQueryType",
    "SearchCollection",
    # Models — vector search
    "VectorSimilarityMetric",
    "VectorIndexType",
    "VectorIndexColumn",
    "VectorSearchIndex",
    # Models — geospatial search
    "GeoOperation",
    "GeoSearchColumn",
    "GeoSearchIndex",
    # Models — faceted aggregation
    "FacetType",
    "AggregationFunction",
    "Facet",
    "FacetedSearchIndex",
    # Parser
    "SearchParser",
    # Emitters
    "FastAPISearchEmitter",
    "NestJSSearchEmitter",
    "AngularEmitter",
    "ReactEmitter",
]
