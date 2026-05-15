# Changelog — CP02 Multi-Tenant Architecture Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-14

### Added

- **Enum**: `TenantIsolationStrategy` (ROW, SCHEMA, DATABASE, HYBRID) — chính thức isolation enum
- **Dataclass**: `TenantFilter` với factory methods `create_row_filter()`, `create_schema_filter()`
- **Enum mapping**: `TenantMode.isolation_strategy` property để map TenantMode sang TenantIsolationStrategy
- **Contracts bridge**: `midicoder/contracts/tenant_models.py` — export `TenantContext`, `TenantFilter`, `TenantIsolationStrategy` cho generated code import
- **Recipes module** (`recipes.py`):
    - `row_level_tenant_recipe()` — row-level isolation (SaaS default)
    - `schema_level_tenant_recipe()` — schema-level isolation (compliance)
    - `database_level_tenant_recipe()` — database-level isolation (enterprise)
    - `auto_provisioning_recipe()` — auto-create tenant resources
    - `manual_review_provisioning_recipe()` — manual approval flow
    - `subdomain_tenant_recipe()` — subdomain-based discovery
    - `cross_tenant_access_recipe()` — cross-tenant data sharing rule
- **Tests**: Full pack-local test suite (`tests/`) — 114 tests covering models, recipes, all 4 stack emitters
- **Exports**: `__init__.py` updated to export all new dataclasses and enums

### Changed

- **pack.yml**: Updated `definitions_count` from 7 → 11 (added TenantResolver, TenantIsolationStrategy, TenantFilter, SchemaIsolationMode)
- **pack.yml**: Removed `frontend_integration` section (Angular/React dùng structured emitter, không phải Jinja2 templates)
- **NestJS emitter**: Fixed broken interceptor syntax (`{{'...'}}` → proper bracket notation)
- **NestJS emitter**: Replaced `ContextType` with `ExecutionContext` (NestJS API fix)

### Fixed

- **CRITICAL**: `midicoder.contracts.tenant_models` module không tồn tại — templates `tenant_models.py.jinja2` import bị `ImportError`
- **CRITICAL**: Enum mismatch — `TenantMode` (SCHEMA/ROW/SUBDOMAIN) vs `TenantIsolationStrategy` (ROW/SCHEMA/DATABASE/HYBRID) không compatible
- **HIGH**: NestJS `_emit_interceptor()` sinh TypeScript code có syntax error (`{{'{col}'}}` double-brace broken)

### Removed

- **Dead tests**: `tests/emitters/test_tenant_isolation.py` (40 dead tests — template files không tồn tại)
- **Old tests**: `tests/emitters/test_tenant.py` (thay thế bằng pack-local tests)

## [1.0.0] - 2026-05-06

### Added

- **Models**: TenantConfig, TenantContext, TenantResolver
- **Enums**: TenantMode
- **FastAPI Emitter**: Tenant middleware, tenant-scoped dependencies
- **NestJS Emitter**: tenant.guard.ts, tenant.module.ts, tenant-interceptor.service.ts
- **Angular Integration**: TenantService, TenantGuard, TenantInterceptor
- **React Integration**: useTenant, TenantProvider, TenantContext

---

**Capabilities Provided:** `enforce_tenant_scope`, `tenant_isolation`, `schema_isolation`, `tenant_provisioning`, `cross_tenant_access`

**Capabilities (Runtime):** `tenant_middleware`, `tenant_context`, `schema_isolation`, `tenant_provisioning`, `cross_tenant_access`

**Obligations:**

1. **TenantIsolation** — All data access must enforce tenant boundary
2. **SchemaProvisioning** — New tenant schema must be provisioned before first access
3. **CrossTenantApproval** — Cross-tenant access must be approved and time-limited
4. **ResourceLimits** — Tenant resource consumption must not exceed plan limits

**Dependencies:** CP01
