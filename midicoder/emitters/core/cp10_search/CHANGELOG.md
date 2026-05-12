# Changelog — CP10 Search & Indexing Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-11

### Added

- **Models**: SearchIndex, SearchQuery, SyncStrategy
- **FastAPI Emitter**: Elasticsearch client, search service, index manager
- **NestJS Emitter**: SearchModule, SearchService, SearchDecorators
- **Angular Integration**: SearchService, SearchComponent
- **React Integration**: useSearch, SearchProvider

---

**Capabilities Provided:** `search_index`, `search_query`, `fulltext_search`

**Capabilities (Runtime):** `elasticsearch`, `meilisearch`, `tenant_aware`, `fulltext`

**Obligations:**

1. **IndexSync** — Search index must stay in sync with source data
2. **TenantAware** — Search results must respect tenant boundaries

**Dependencies:** CP08
