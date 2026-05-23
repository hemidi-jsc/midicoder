# Changelog for CP43 — Versioning & History Generator

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-23

### Added

- **Models**: `OperationType` (CREATE, UPDATE, DELETE, RESTORE, HARD_DELETE), `VersionConfig` (versioning config cho entity), `HistoryRecord` (immutable snapshot với tamper-evidence hash), `SoftDeleteMixin` (soft delete + auto filter), `VersioningCollection` (collection cho nhiều entities)
- **Parser**: `VersioningParser` — parse YAML DSL và MIR metadata thành VersioningCollection
- **Recipes**: `build_versioning_ir`, `full_versioning_recipe`, `minimal_versioning_recipe`, `soft_delete_only_recipe`, `create_history_record`
- **FastAPI Emitter**: `FastAPIVersioningEmitter` — SQLAlchemy VersionMixin, SoftDeleteMixin, EntityHistoryMixin, HistoryRepository, VersionAuditLogger (integrate với CP14)
- **NestJS Emitter**: `NestJSVersioningEmitter` — @Versioned decorator, @SoftDelete decorator, EntityHistory, HistoryService, VersionAuditLogger
- **Angular Emitter**: `AngularVersioningEmitter` — VersionHistoryService, VersionHistoryComponent, RestoreVersionDialogComponent, SoftDeleteIndicatorComponent
- **React Emitter**: `ReactVersioningEmitter` — types, useVersionHistory hook, VersionHistory component, RestoreVersionModal, SoftDeleteIndicator
- **Error Codes**: MDC-CP43-001 → MDC-CP43-010 (10 error codes)
- **Registry**: `"CP43": "cp43_versioning"` trong `CP_ID_TO_INTERNAL`
- **Templates**: 16 Jinja2 templates (FastAPI: 5, NestJS: 5, Angular: 3, React: 3)

### Capabilities

- `entity_version`: Optimistic locking với version column (auto increment)
- `timetravel_query`: Time-travel query (get_at_version, get_at_timestamp, get_version_history)
- `soft_delete`: Soft delete với auto filter query + restore
- `history_audit`: Auto emit audit event tới CP14 audit_logger

### Integration

- **CP01**: Đọc entities từ CP01 metadata trong MIR
- **CP08**: Dùng cùng ORM pattern (SQLAlchemy/TypeORM) như CP08
- **CP14**: Emit audit events vào CP14 audit_logger
