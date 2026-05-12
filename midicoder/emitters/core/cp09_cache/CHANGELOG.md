# Changelog — CP09 Caching & Performance Layer Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: CacheProfile, CacheBinding, InvalidationStrategy
- **FastAPI Emitter**: Redis client, cache strategy, cache decorators, cache invalidation
- **NestJS Emitter**: CacheModule, CacheService, CacheInterceptor
- **Angular Integration**: CacheService, CacheInterceptor
- **React Integration**: useCache, CacheProvider

---

**Capabilities Provided:** `cache_get`, `cache_set`, `cache_invalidate`, `cache_warm`

**Capabilities (Runtime):** `redis`, `memory`, `tenant_aware`, `invalidation`

**Obligations:**

1. **CacheConsistency** — Cache must be invalidated on corresponding data mutation
2. **TenantAware** — Cache keys must include tenant isolation

**Dependencies:** CP08
