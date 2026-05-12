# Changelog — CP08 Database & Data Access Layer Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
