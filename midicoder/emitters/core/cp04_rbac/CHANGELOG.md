# Changelog — CP04 RBAC & Policy Engine

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
