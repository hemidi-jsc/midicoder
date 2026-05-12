# CHANGELOG — CP51 Blueprint Composition Engine

## [1.0.0] — 2026-05-12

### Added

**Pattern Vocabulary (8 definitions):**

- `CapabilityNode` — Node trong capability graph (pack_id, pack_type, capabilities, depends_on)
- `CapabilityGraph` — DAG của capabilities từ CPs + DPs + RXs (Obligation 1: no cycle)
- `ResolutionStatus` — Enum: resolved, partial, failed
- `Resolution` — Kết quả resolve dependency graph (Obligation 2: include P0 mandatory)
- `MergeMode` — Enum: merge_all, merge_non_conflicting, priority_based, topological
- `MergeStrategy` — Chiến lược merge output từ nhiều packs
- `ConflictResolution` — Xử lý xung đột khi merge (file/function/class/import overlap)
- `BlueprintSchema` — Schema versioning + backward compatibility
- `VersionConstraint` — Ràng buộc version giữa packs (Obligation 3: semver)

**Recipes (5 pre-mixed blueprints):**

- `FullStackBlueprintRecipe()` — Full-stack app (frontend + backend + database)
- `BackendOnlyRecipe()` — Backend-only API service
- `FrontendOnlyRecipe()` — Frontend-only SPA/PWA
- `MicroserviceBlueprintRecipe()` — Microservice architecture (event-driven)
- `MonolithRecipe()` — Monolithic application (all-in-one)

### Obligations

1. **MDC-CP51-001**: CapabilityGraph PHẢI là DAG — không cho phép cycle
2. **MDC-CP51-002**: Resolution PHẢI include tất cả mandatory P0 packs
3. **MDC-CP51-003**: VersionConstraint PHẢI enforce semver compatibility

### Notes

- Meta pack — không cần frontend/backend emitters
- Dependency: CP52 (Invariant) và CP53 (Domain Bridge) đều depend on CP51
