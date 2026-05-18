# Changelog — CP04 RBAC & Policy Engine

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-18

### Fixed

- **Template Rule V1**: Removed `midicoder/contracts/rbac_models` import from `nestjs/service.ts.jinja2` — generated code now fully standalone with inline type definitions (`RBACRole`, `PolicyRule`, `PolicyEvaluationResult`)
- **Template Rule V2**: Removed `__post_init__` from `fastapi/service.py.jinja2` `Role` dataclass — replaced with `field(default_factory=list)`
- **FastAPI emitter**: Removed `from midicoder.emitters.core.cp04_rbac.*` imports in generated `service.py` — `check_policy()` now uses standalone inline expression evaluator (no runtime dependency on PolicyEngine)
- **Pack.yml paths**: Aligned all `path` entries with actual emitter output (FastAPI: `app/rbac/*`, NestJS: `src/core/rbac/*`, React: `src/core/rbac/*`)
- **Pack.yml**: Split shared FastAPI/NestJS template entries into stack-specific entries
- **Added missing templates**: `__init__.py.jinja2` (FastAPI), `module.ts.jinja2` (NestJS), `policy_guard.ts.jinja2` (NestJS), `with_permission.tsx.jinja2` (React)
- **EMITTER_REGISTRY**: Registered CP04 for all 4 stacks (`cp04.rbac.fastapi`, `cp04.rbac.nestjs`, `cp04.rbac.angular`, `cp04.rbac.react`)
- **taxonomy.yml**: Updated `definitions_count` from 4 → 11 (actual count in `models.py`)

### Added

- Standalone ABAC expression evaluator in generated FastAPI `RBACService.check_policy()` (supports `==`, `!=`, `>`, `>=`, `<`, `<=`, `AND`, `OR`, `NOT`)
- `init_rbac_service()` helper in generated FastAPI service for DI setup
- Complete test suite moved into pack folder (`tests/`) with 100% model/engine coverage
- React emitter now emits `useRbac.ts` (renamed from `useAuth.ts`) for consistency

### Changed

- React emitter output path: `src/core/rbac/useAuth.ts` → `src/core/rbac/useRbac.ts`
- FastAPI emitter output path: `app/core/rbac/*` → `app/rbac/*`
- CP version bumped from 1.0.0 → 1.1.0

---

## [1.0.0] - 2026-05-06

### Added

- **Models**: Permission, Role, Policy, PolicyCondition, PolicyEvaluationResult, PolicyRule, PolicyContext, PolicyDecision, RBACConfig
- **Enums**: PolicyEffect
- **FastAPI Emitter**: RBAC middleware, policy enforcement point
- **NestJS Emitter**: rbac.guard.ts, policies.module.ts, policy.service.ts
- **Angular Integration**: RbacService, RoleGuard, PermissionDirective
- **React Integration**: useRbac, ProtectedRoute, WithPermission

---

**Capabilities Provided:** `authorize_role`, `check_policy`

**Capabilities (Runtime):** `role_check`, `policy_evaluation`, `role_hierarchy`, `abac_engine`

**Obligations:**

1. **RoleHierarchy** — Role assignments must respect hierarchical ordering

**Dependencies:** CP02, CP03
