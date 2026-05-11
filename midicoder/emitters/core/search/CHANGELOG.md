# Changelog

## [1.0.0] - 2026-05-11

### Added
- Search & Indexing Generator (CP10) implementation
- Models: SearchProviderType, SyncStrategy, SyncTrigger, SearchIndexColumn, SearchIndex, SearchCollection
- Parser: SearchParser voi error handling
- FastAPI Emitter: FastAPISearchEmitter (elasticsearch config, search service, index manager)
- NestJS Emitter: NestJSSearchEmitter (search module, search service, decorators)
- Angular Emitter: AngularEmitter (search models, search service, search module)
- React Emitter: ReactEmitter (search types, SearchProvider, useSearch hook, utils)
- FastAPI templates: elasticsearch.py, search_service.py, index_manager.py
- NestJS templates: search.module.ts, search.service.ts, search.decorators.ts
- Angular templates: search.service.ts, search.module.ts
- React templates: SearchProvider.tsx, useSearch.ts
- Error codes: MDC-CP10-001 ~ MDC-CP10-005
- KPI-029: Tenant isolation support trong tat ca search operations
- pack.yml manifest dong bo voi taxonomy.yml
- Unit tests: 160+ tests cho models, parser, emitters, templates
