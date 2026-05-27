# Changelog — CP51 Blueprint Composition Engine

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-12

### Added

- **Models**: Blueprint, PackReference, CompositionRule, ValidationReport
- **Capability Vocabulary (8 definitions)**: CapabilityNode, CapabilityGraph, ResolutionStatus, Resolution, MergeMode, MergeStrategy, ConflictResolution, BlueprintSchema, VersionConstraint
- **Recipes (5 pre-mixed blueprints)**: FullStackBlueprintRecipe, BackendOnlyRecipe, FrontendOnlyRecipe, MicroserviceBlueprintRecipe, MonolithRecipe

### Changed

- Normalized `capabilities_provided` to match taxonomy.yml (removed `resolve_capabilities`, `merge_pack_outputs`, `blueprint_schema_validation`)

---

**Capabilities Provided:** `compose_blueprint`, `validate_blueprint`

**Capabilities (Runtime):** none (meta pack)

**Obligations:**

1. **NoCircularDeps** — Blueprint must not contain circular pack dependencies (MDC-CP51-001)
2. **VersionCompat** — All referenced packs must satisfy version constraints (MDC-CP51-002)
3. **CapabilityCoverage** — All requested capabilities must be resolvable to a pack (MDC-CP51-003)

**Dependencies:** CP01
