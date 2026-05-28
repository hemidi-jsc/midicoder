# Changelog — B01 Domain Model DSL & IR Builder

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-28

- Migrate to taxonomy-v2: B01 cp_base_domain_model
- Add RenderContextSpec integration for typed render context
- Template path update: cp01_domain_model → cp_base_domain_model
- Add import from midicoder.packs.models shared models

## [Unreleased]

### Added

- **Recipes** (`recipes.py`): 10 factory functions for common domain patterns
    - `SimpleEntityRecipe` — CRUD entity with UUID, tenant_id, timestamps, lifecycle hooks
    - `AggregateRootRecipe` — consistency boundary with strict/eventual/relaxed options
    - `TemporalEntityRecipe` — SCD Type 2 with valid_from/valid_to, range query index
    - `CQRSCommandRecipe` — write operation with auth + tenant guards + transaction
    - `CQRSQueryRecipe` — read operation with auth + tenant guards + pagination + sort
    - `EventSourcedAggregateRecipe` — snapshot strategy + versioned optimistic concurrency
    - `SagaRecipe` — long-running transaction with compensating steps (orchestration)
    - `PolymorphicEntityRecipe` — subtype inheritance with discriminator column (STI/CTI/JTI)
    - `ProjectionRecipe` — CQRS read model subscribing to domain events
    - `ValueObjectRecipe` — immutable, equality-by-value domain primitive
- **Capabilities**: `domain_model_recipes`, `cqrs_recipes`, `event_sourcing_recipes`
- **Pack manifest**: `recipes_count: 10`, new `recipes` section in pack.yml

## [1.0.0] - 2026-05-12

### Added

- **Models**: Entity, Command, Query, ValueObject, AggregateRoot, DomainEvent
- **Parser**: DSL parser for entity, command, query, and value object definitions
- **FastAPI Emitter**: Entity models (SQLAlchemy), command handlers, query handlers, value objects (frozen dataclasses)
- **NestJS Emitter**: Entity models (TypeORM), command handlers, query handlers, value objects (immutable classes)
- **Guards & Effects**: CommandGuards, CommandEffects, QueryGuards, QueryEffects
- **Transaction Manager**: TransactionManagerSQL for command execution
- **Type Resolution**: TypeResolver, InheritanceResolver, ComputedFieldEvaluator

### Changed

- Merged entity/, command/, query/, value_object/ into unified domain_model/ package
- All 28 modules now reside in single pack directory with namespaced file names
- Updated resolver.py mapping: CP01 → domain_model

### Fixed

- Removed CP23→command from resolver fallback (command is part of CP01)

---

**Capabilities Provided:** `dsl_parsing`, `projection_tree_build`, `ir_build`, `domain_model_recipes`, `cqrs_recipes`, `event_sourcing_recipes`

**Capabilities (Runtime):** `entity_modeling`, `command_query_separation`, `value_object`, `aggregate_root`, `domain_events`, `cqrs_projection`, `event_sourcing`, `temporal_entity`, `polymorphic_entity`, `saga`, `recipes`

**Recipes (10):** `SimpleEntityRecipe`, `AggregateRootRecipe`, `TemporalEntityRecipe`, `CQRSCommandRecipe`, `CQRSQueryRecipe`, `EventSourcedAggregateRecipe`, `SagaRecipe`, `PolymorphicEntityRecipe`, `ProjectionRecipe`, `ValueObjectRecipe`

**Obligations:**

1. **EntityIdentity** — Every entity must have unique, non-null identifier
2. **CommandValidation** — All commands must be validated before execution
3. **AggregateBoundary** — Only aggregate root may be accessed directly from outside
4. **EventImmutability** — Domain events must be immutable once emitted

**Dependencies:** none
