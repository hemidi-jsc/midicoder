# Changelog — CP37 Feature Flags & Dynamic Config

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-22

### Added

- **Models**: `FeatureFlag`, `TargetingRule`, `FlagEvaluation`, `FeatureFlagEvaluator`, `ABExperiment`, `ABVariant`, `ABExperimentAssignment`, `ABExperimentEngine`, `DynamicConfig`, `ConfigChange`, `FlagStore`
- **Parser**: `FeatureFlagIR`, `parse_feature_flags()`, `parse_experiments()`, `parse_configs()`, `parse_to_ir()`
- **Recipes**: `simple_flags_recipe()`, `ab_testing_recipe()`, `dynamic_config_recipe()`
- **FastAPI Emitter**: 20 Jinja2 templates — models, schemas, services, routers, stores, middleware, websocket, sync worker
- **NestJS Emitter**: 15 Jinja2 templates — module, entities, DTOs, services, controllers, interceptor, gateway
- **Angular Emitter**: 5 Jinja2 templates — flag-provider.service, flag-directive, flag-interceptor, config.service, flag-sync.service
- **React Emitter**: 7 Jinja2 templates — FeatureFlagProvider, useFeatureFlag, useAllFlags, useABVariant, useConfig, FeatureFlagGate, FlagSyncWorker
- **Tests**: 67 tests covering error codes, enums, models, parser, recipes, emitters, pack.yml
- **Pack manifest**: `capabilities_provided` với 6 capabilities (evaluate_feature_flag, assign_experiment, read_dynamic_config, feature_toggle, ab_test, dynamic_config)

### Changed

- Updated taxonomy.yml — CP37 status `planned` → `stable`
- Added CP37 to CP_ID_TO_INTERNAL registry
- Updated TODOS.md — CP37 status TODO → DONE

### Fixed

- Template path consistency — NestJS DTO paths khớp giữa pack.yml và emitter
- Rule V1 compliance — Generated code không import từ `midicoder.*`

---

**Capabilities Provided:** `evaluate_feature_flag`, `assign_experiment`, `read_dynamic_config`, `feature_toggle`, `ab_test`, `dynamic_config`

**Capabilities (Runtime):** `feature_toggle`, `ab_test`, `dynamic_config`, `remote_sync`, `config_versioning`

**Recipes (3):** `simple_flags_recipe`, `ab_testing_recipe`, `dynamic_config_recipe`

**Obligations:**

1. **FlagEvaluationDeterminism** — Feature flag evaluation phải deterministic cho cùng context input
2. **ConfigChangeAudit** — Tất cả config changes phải được audit log qua CP14

**Dependencies:** CP01, CP02, CP14
