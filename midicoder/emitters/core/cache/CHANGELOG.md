# Changelog

All notable changes to CP09 - Caching & Performance Layer Generator.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-05-08

### Added
- **5 Cache Definitions**: CacheProfile, CacheStrategy, CacheInvalidationRule, CacheWarmConfig, CacheMetrics
- **CacheParser**: Parse YAML và MIR metadata thành CacheCollection với validation
- **FastAPICacheEmitter**: Render 4 templates (redis, strategy, decorators, invalidation)
- **NestJSCacheEmitter**: Render 3 templates (module, service, interceptor)
- **Angular Templates**: CacheService, CacheInterceptor, CacheNgModule
- **React Templates**: useCache hook, CacheProvider, cacheUtils
- **Runtime Providers**: RedisCacheProvider, MemoryCacheProvider (ABC-based)
- **Cache Decorators**: @cache, @cache_tenant, @cache_disable
- **Cache Warm-up**: CacheWarmer, ScheduledWarmJob
- **5 Error Codes**: MDC-CP09-001..005 với templates và suggestions
- **KPI-029**: Tenant isolation enforced trong tất cả models và templates
- **pack.yml**: Đồng bộ 1:1 với taxonomy.yml (capabilities_provided)

### Obligations
- TTL Validation: TTL phải > 0 (enforce tại model __post_init__)
- Tenant Isolation: tenant_isolated=True mặc định cho tất cả cache profiles
