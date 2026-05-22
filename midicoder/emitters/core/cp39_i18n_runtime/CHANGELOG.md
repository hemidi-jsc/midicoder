# Changelog — CP39: i18n/L10n Runtime

## [1.0.0] - 2026-05-22

### Added
- **LocaleConfig**: Cấu hình locale (BCP 47 code, date/number/currency format, plural rule, fallback)
- **TranslationEntry**: Bản ghi translation với key, namespace, locale, tenant scope
- **TranslationStore** (ABC): Abstract interface cho storage backend
- **InMemoryTranslationStore**: In-memory implementation cho dev/testing
- **LocaleFormatter**: Engine format date/number/currency/relative time theo locale
- **TranslationEngine**: Engine resolve translation với fallback chain (cache → tenant → global → fallback → raw key)
- **CacheConfig**: Cấu hình cache (memory/Redis, TTL, max_size)
- **DiscoverResult**: Kết quả auto-discover translatable strings
- **I18nRuntimeIR**: Intermediate Representation cho parser
- **Parser**: `parse_locales()`, `parse_translations()`, `parse_cache_config()`, `parse_to_ir()`
- **Recipes**: `basic_i18n_recipe()` (en/vi + memory cache), `multitenant_i18n_recipe()` (en/vi/fr + Redis + tenant override)
- **FastAPI Emitter**: 9 templates (models, schemas, service, formatter, router, cache, discover, ws, middleware)
- **NestJS Emitter**: 10 templates (entity, dto, service, controller, formatter, cache, gateway, interceptor, module)
- **Angular Emitter**: 4 templates (service, directive, sync service, formatter pipe)
- **React Emitter**: 5 templates (useTranslation, useLocale, useFormattedValue, sync worker, provider)
- **Error codes**: MDC-CP39-001 đến MDC-CP39-015

### Capabilities
- `locale_format`: Date/number/currency formatting theo locale
- `translation_manage`: CRUD translation entries với tenant isolation
- `language_switch`: Real-time language switch qua WebSocket/SSE

### Recipes
- `basic_i18n_recipe`: 2 locales (en, vi), memory cache, basic translations
- `multitenant_i18n_recipe`: 3 locales (en, vi, fr), Redis cache, tenant override support

### Obligations
- `TranslationFallbackChain`: Resolution chain: cache → tenant → global → fallback → raw key
- `TenantTranslationIsolation`: Tenant translations isolated với fallback về global

### Dependencies
- CP01: Domain Model DSL & IR Builder
- CP02: Multi-Tenant Architecture Generator
