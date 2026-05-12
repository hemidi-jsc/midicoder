# Changelog: CP52 Invariant Gate Framework

## [1.0.0] - 2026-05-06

### Added
- Models: InvariantDefinition, InvariantResult, InvariantReport, CompileTimeCheckSpec, RuntimeGuardSpec
- Enums: InvariantCategory, EnforcementMode, InvariantSeverity
- Invariant categories: business, compliance, failure_mode
- FastAPI emitter: invariant middleware, guard decorators
- NestJS emitter: invariant.guard.ts, invariant.module.ts
- pack.yml: Self-declare capabilities (enforce_invariant, gate_check)
- Error codes: INV001-INV015
- Meta pack — no frontend/backend emitter needed
