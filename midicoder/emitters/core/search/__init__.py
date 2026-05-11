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

from midicoder.emitters.core.search.models import (
    SearchProviderType,
    SyncStrategy,
    SyncTrigger,
    SearchIndexColumn,
    SearchIndex,
    SearchCollection,
)
from midicoder.emitters.core.search.parser import SearchParser
from midicoder.emitters.core.search.fastapi import FastAPISearchEmitter
from midicoder.emitters.core.search.nestjs import NestJSSearchEmitter
from midicoder.emitters.core.search.angular import AngularEmitter
from midicoder.emitters.core.search.react import ReactEmitter

__all__ = [
    # Models
    "SearchProviderType",
    "SyncStrategy",
    "SyncTrigger",
    "SearchIndexColumn",
    "SearchIndex",
    "SearchCollection",
    # Parser
    "SearchParser",
    # Emitters
    "FastAPISearchEmitter",
    "NestJSSearchEmitter",
    "AngularEmitter",
    "ReactEmitter",
]
