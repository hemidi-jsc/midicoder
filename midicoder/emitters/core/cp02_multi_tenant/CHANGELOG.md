# Changelog — CP02 Multi-Tenant Architecture Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-06

### Added

- **Models**: TenantConfig, TenantContext, TenantResolver
- **Enums**: TenantMode
- **FastAPI Emitter**: Tenant middleware, tenant-scoped dependencies
- **NestJS Emitter**: tenant.guard.ts, tenant.module.ts, tenant-interceptor.service.ts
- **Angular Integration**: TenantService, TenantGuard, TenantInterceptor
- **React Integration**: useTenant, TenantProvider, TenantContext

---

**Capabilities Provided:** `enforce_tenant_scope`, `tenant_isolation`

**Capabilities (Runtime):** `tenant_middleware`, `tenant_context`

**Obligations:**

1. **TenantIsolation** — All data access must enforce tenant boundary

**Dependencies:** CP01
