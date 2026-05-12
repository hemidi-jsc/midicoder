# Changelog: CP04 RBAC & Policy Engine

## [1.0.0] - 2026-05-06

### Added
- Models: Permission, Role, Policy, PolicyCondition, PolicyEvaluationResult, PolicyRule, PolicyContext, PolicyDecision, RBACConfig
- Enums: PolicyEffect
- FastAPI emitter: RBAC middleware, policy enforcement point
- NestJS emitter: rbac.guard.ts, policies.module.ts, policy.service.ts
- pack.yml: Self-declare capabilities (authorize_role, check_policy)
- Error codes: MDC-CP04-001 to MDC-CP04-008
