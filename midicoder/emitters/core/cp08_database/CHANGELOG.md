# Changelog — CP08 Database & Data Access Layer Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-05-14

### Added

- **Spatial Emitter (FastAPI)**: `emit_spatial_columns()`, `emit_spatial_index()` — PostGIS helper module, GiST/SP-GiST index migration
- **Spatial Emitter (NestJS)**: `emit_spatial_columns()`, `emit_spatial_index()` — TypeORM spatial decorators, migration
- **Spatial Templates**: `spatial_helpers.py.jinja2`, `spatial_indexes.py.jinja2`, `spatial.decorators.ts.jinja2`, `spatial-indexes.ts.jinja2`
- **Time-Series Emitter (FastAPI)**: `emit_time_series_model()` — partitioned table model, hypertable migration comments, retention policy
- **Time-Series Emitter (NestJS)**: `emit_time_series_model()` — TypeORM entity with timestamptz partition key
- **Time-Series Templates**: `time_series_model.py.jinja2`, `time_series.entity.ts.jinja2`
- **CQRS Read Model Emitter (FastAPI)**: `emit_read_model()` — materialized view / denormalized table model with refresh() method
- **CQRS Read Model Emitter (NestJS)**: `emit_read_model()` — TypeORM entity with refreshStrategy
- **CQRS Templates**: `read_model.py.jinja2`, `read_model.entity.ts.jinja2`
- **Distributed Transaction Emitter (FastAPI)**: `emit_distributed_transaction()` — Saga orchestrator, 2PC coordinator, Outbox table
- **Distributed Transaction Emitter (NestJS)**: `emit_distributed_transaction()` — @Injectable() Saga service, Coordinator
- **Distributed Transaction Templates**: `distributed_transaction.py.jinja2`, `distributed_transaction.ts.jinja2`
- **JSONB Emitter (FastAPI)**: `emit_jsonb_columns()` — GIN index comments, path query helpers, contains helpers
- **JSONB Emitter (NestJS)**: `emit_jsonb_columns()` — `@Column('jsonb')` decorator, GIN index decorator
- **JSONB Templates**: `jsonb_helpers.py.jinja2`, `jsonb.decorators.ts.jinja2`
- **Tests**: `test_advanced_capabilities.py` — 40+ tests covering all 5 advanced capabilities (spatial, time_series, cqrs, distributed_tx, jsonb) across both stacks

### Changed

- **pack.yml**: version → 1.2.0, added `advanced_capabilities` section with 18 new file contribution entries
- **All 5 capabilities**: from model-only (declared but no emitter) → fully emitted with templates + tests

### Fixed

- All 5 advanced capabilities now emit actual code (was: models defined but no emitter/template code)

---

**Capabilities Provided:** `create_record`, `update_record`, `delete_record`, `query_records`, `load_entity`, `begin_transaction`, `commit_transaction`

**Capabilities (Runtime):** `datasource`, `entity_generation`, `repository_pattern`, `migration`, `spatial`, `time_series`, `cqrs_read_model`, `distributed_transaction`, `jsonb` (all 9 now fully emit code)

**Obligations:**

1. **TenantScope** — All queries must enforce tenant scope automatically (KPI-029)
2. **DistributedTxConsistency** — Distributed transactions must ensure eventual consistency across participants
3. **SpatialSRID** — All spatial columns must declare explicit SRID (default: 4326 WGS84)

**Dependencies:** CP01

## [1.1.0] - 2026-05-13

### Added

- **Recipes**: `postgres_datasource()`, `mysql_datasource()` — pre-configured DataSource factories
- **Column Types**: `ARRAY`, `BYTES`, `TIME` (in addition to existing STRING, INTEGER, BOOLEAN, DECIMAL, TEXT, JSON, DATETIME, UUID)
- **Database Engines**: `MONGODB`, `SQLITE` (in addition to POSTGRESQL, MYSQL, SQLSERVER, ORACLE)
- **Spatial Types**: `SpatialColumn`, `SpatialIndex`, `SpatialType` (POINT, LINESTRING, POLYGON, GEOMETRY, GEOGRAPHY, ...), `SpatialIndexType` (GIST, SPGIST, GIN, BRIN)
- **Time-Series**: `TimeSeriesModel`, `RetentionPolicy`, `TimeSeriesGranularity`, `RetentionPolicyType`
- **CQRS Read Models**: `ReadModel`, `ReadModelSource` (MATERIALIZED_VIEW, DENORMALIZED_TABLE, SEARCH_INDEX, CACHED_COMPUTATION), `RefreshStrategy` (REAL_TIME, BATCH, LAZY, EVENT_DRIVEN)
- **Distributed Transactions**: `DistributedTransaction`, `TransactionParticipant`, `DistributedTxProtocol` (TWO_PHASE_COMMIT, SAGA, OUTBOX, TCC), `ParticipantStatus`
- **JSONB**: `JSONBColumn`, `JSONBIndex`, `JSONBIndexType` (GIN, GIN_PATH_OPS, GIN_NULLS_PRUNED, BTREE), `JSONBValidationMode`
- **Pipeline Integration**: Registered `cp08.database.fastapi` and `cp08.database.nestjs` in `EMITTER_REGISTRY`
- **DSL Integration**: Added `get_datasources()`, `get_tables()`, `get_indexes()` convenience getters to `ProjectionTree`
- **Tests**: Moved to `cp08_database/tests/` — 100% coverage for models, parser, recipes, emitters, templates

### Changed

- **TypeORM Emitter**: Fixed `emit_connection_config()` — proper f-string interpolation (was hardcoded `'${datasource.engine.value}'`)
- **Parser**: Extended `_TYPE_MAP` and `_ENGINE_MAP` to cover all new column types and database engines
- **Emitter type maps**: Updated `_SQLALCHEMY_TYPE_MAP` and `_TYPEORM_TYPE_MAP` for ARRAY, BYTES, TIME

### Fixed

- TypeORM `emit_connection_config()` — engine type and connection string now properly interpolated
- Test paths — migrated from stale `stacks/fastapi/templates/db/` to `stacks/fastapi/core/cp08_database/`

---

**Capabilities Provided:** `create_record`, `update_record`, `delete_record`, `query_records`, `load_entity`, `begin_transaction`, `commit_transaction`

**Capabilities (Runtime):** `datasource`, `entity_generation`, `repository_pattern`, `migration`, `spatial`, `time_series`, `cqrs_read_model`, `distributed_transaction`, `jsonb`

**Obligations:**

1. **TenantScope** — All queries must enforce tenant scope automatically (KPI-029)
2. **DistributedTxConsistency** — Distributed transactions must ensure eventual consistency across participants
3. **SpatialSRID** — All spatial columns must declare explicit SRID (default: 4326 WGS84)

**Dependencies:** CP01

## [1.0.0] - 2026-05-06

### Added

- **Models**: DataSource, TableMapping, ColumnDef, Repository, Transaction, Migration
- **FastAPI Emitter**: SQLAlchemy models, repository pattern, Alembic migrations
- **NestJS Emitter**: TypeORM entities, repository modules, migration runner
- **Capability Modules**: datasource, entity_generation, repository_pattern, migration

---

**Capabilities Provided:** `create_record`, `update_record`, `delete_record`, `query_records`, `load_entity`, `begin_transaction`, `commit_transaction`

**Capabilities (Runtime):** `datasource`, `entity_generation`, `repository_pattern`, `migration`

**Obligations:**

1. **TenantScope** — All queries must enforce tenant scope automatically

**Dependencies:** CP01
