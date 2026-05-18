# Changelog — CP09 Caching & Performance Layer Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-18

### Added

- **Models**: CDNCacheLayer, CDNCacheControlDirective (CDN edge cache config)
- **Models**: StampedePrevention, StampedePreventionStrategy (thundering-herd prevention)
- **Models**: CacheTier (multi-tier cache: L1=memory, L2=Redis, L3=database)
- **Models**: CacheWarmupStrategy, CacheWarmupConfig (cache warmup strategies)
- **Models**: CacheBackend.MEMCACHED (Memcached backend support)
- **Provider**: MemcachedCacheProvider (pymemcache-based with in-memory fallback)
- **Parser**: Parse CDN layers, stampede prevention, cache tiers, warmup config từ MIR metadata
- **Emitter (FastAPI)**: cdn_cache.py — CDN middleware, purge API, Cache-Control headers
- **Emitter (FastAPI)**: stampede_prevention.py — mutex-based stampede prevention
- **Emitter (FastAPI)**: cache_warmup.py — batch warmup với concurrency limit
- **Emitter (FastAPI)**: multi_tier.py — L1/L2 multi-tier cache
- **Emitter (FastAPI)**: memcached.py — Memcached client
- **Emitter (CacheCollection)**: add_cdn_layer, set_stampede_prevention, add_tier, set_warmup_config
- **Emitter (CacheCollection)**: memcached_profiles() filter
- **Pipeline**: Register CP09 trong EMITTER_REGISTRY (cp09.cache.fastapi, cp09.cache.nestjs, cp09.cache.angular, cp09.cache.react)
- **Pipeline**: Register cp09_cache parser trong PARSER_REGISTRY
- **DSL**: Update CacheParams — thêm backend, ttl, max_size, serializer, key_prefix, tenant_isolated, strategy, invalidation_strategy, cdn_enabled, cdn_provider, stampede_prevention, stampede_strategy, multi_tier, warmup_enabled
- **Templates**: cdn_cache.py.jinja2, stampede_prevention.py.jinja2, cache_warmup.py.jinja2
- **Pack.yml**: Fix definitions_count (3→14), obligations_count (2→5), thêm capabilities (tag_invalidation, distributed_lock, multi_tier_cache)

### Changed

- **Version**: 1.0.0 → 1.1.0
- **CacheBackend**: Added MEMCACHED variant
- **CacheCollection**: Extended with cdn_layers, stampede_prevention, tiers, warmup_config fields
- **to_dict/from_dict**: Include advanced fields in serialization

### Capabilities Provided

`cache_get`, `cache_set`, `cache_invalidate`, `cache_warm`, `cdn_cache`, `stampede_prevention`, `multi_tier_cache`, `tag_invalidation`, `distributed_lock`

### Obligations

1. **CacheConsistency** — Cache phải được invalidate khi data mutation tương ứng
2. **TenantAware** — Cache keys phải bao gồm tenant isolation
3. **StampedeProtection** — Cache miss đồng thời không được gây thundering herd
4. **CDNCacheControl** — CDN responses phải có Cache-Control headers rõ ràng
5. **MultiTierConsistency** — Multi-tier cache phải đồng bộ khi invalidate

---

## [1.0.0] - 2026-05-07

### Added

- **Models**: CacheProfile, CacheBinding, InvalidationStrategy
- **Models**: CacheStrategy, CacheInvalidationRule, CacheWarmConfig, CacheMetrics
- **FastAPI Emitter**: Redis client, cache strategy, cache decorators, cache invalidation
- **NestJS Emitter**: CacheModule, CacheService, CacheInterceptor
- **Angular Integration**: CacheService, CacheInterceptor
- **React Integration**: useCache, CacheProvider

---

**Dependencies:** CP08
