# CP48 — API Rate Limiting & Quota Management

## Version 1.0.0 (2026-05-25)

### Initial Release

**Capabilities Provided:** `rate_limiting`, `quota_management`, `throttling`, `rate_limit_middleware`

**New Features:**
- 3 chiến lược rate limiting: Fixed Window, Sliding Window, Token Bucket
- Multi-level quota: Per-user, per-tenant, per-endpoint, global
- Redis primary + in-memory fallback cho distributed rate limiting
- Middleware tự động enforce + Service cho manual control
- Admin API cho CRUD policies và monitor usage
- Frontend dashboard: Angular + React

**Models:**
- `RateLimitStrategy` enum (FIXED_WINDOW, SLIDING_WINDOW, TOKEN_BUCKET)
- `QuotaLevel` enum (USER, TENANT, ENDPOINT, GLOBAL)
- `QuotaPeriod` enum (MINUTE, HOUR, DAY, WEEK, MONTH)
- `RateLimitPolicy` dataclass
- `QuotaConfig` dataclass
- `RateLimitCounter` dataclass
- `UsageStats` dataclass
- `RateLimitService` class
- `QuotaService` class

**Emitters:**
- FastAPI: models, middleware, service, router, quota_service (5 templates)
- NestJS: service, middleware, module, controller, quota_service (5 templates)
- Angular: dashboard, quota_status, service (3 templates)
- React: dashboard, quota_status, useRateLimit hook (3 templates)

**Recipes:**
- `build_rate_limit_recipe()` — 3 default policies
- `build_quota_recipe()` — 4 default quota configs
- `build_full_recipe()` — Kết hợp cả rate limiting và quota

**Error Codes:**
- `MDC-CP48-001` — Rate limit policy không tồn tại
- `MDC-CP48-002` — Rate limit strategy không hợp lệ
- `MDC-CP48-003` — Quota config không hợp lệ
- `MDC-CP48-004` — Vượt quá rate limit
- `MDC-CP48-005` — Vượt quá quota
- `MDC-CP48-006` — Window size không hợp lệ
- `MDC-CP48-007` — Redis connection failed
- `MDC-CP48-008` — Rate limit key rỗng
- `MDC-CP48-009` — Quota level không hợp lệ
- `MDC-CP48-010` — Throttling config không hợp lệ

**Dependencies:**
- CP03 (Authentication & Authorization Framework)

**Obligations:**
- TenantIsolation: Tất cả rate limit/quota enforce tenant scope
- GracefulDegradation: Redis down fallback sang in-memory

**Tests:** 100% coverage cho models, parser, recipes, emitters, error_codes
