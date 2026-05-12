# Changelog: CP02 Multi-Tenant Architecture Generator

## [1.0.0] - 2026-05-06

### Added
- Models: TenantConfig, TenantContext, TenantResolver
- Enums: TenantMode
- FastAPI emitter: tenant middleware, tenant-scoped dependencies
- NestJS emitter: tenant.guard.ts, tenant.module.ts, tenant-interceptor.service.ts
- pack.yml: Self-declare capabilities (enforce_tenant_scope, tenant_isolation)
- Error codes: CP02001-CP02005
