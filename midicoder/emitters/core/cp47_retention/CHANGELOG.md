# Changelog — CP47 Data Retention & Lifecycle Management

## [1.0.0] — 2026-05-24

### Added
- **Retention Policy Engine**: Policy types (time_based, event_based, status_based) với CRUD hoàn chỉnh
- **Data Archival**: Archive records sang cold storage với snapshot và restore API
- **Data Purging**: Soft/hard delete theo policy với batch processing
- **GDPR Erasure**: Full flow — scan PII, anonymize/erase, audit trail, progress tracking
- **Exemption System**: Legal hold, compliance, audit_trail, manual exemptions
- **Scheduler Integration**: APScheduler tasks cho retention scan, archive job, purge job
- **4 Stack Emitters**: FastAPI, NestJS, Angular, React (6 templates mỗi stack)
- **10 Error Codes**: MDC-CP47-001 → MDC-CP47-010
- **2 Recipes**: basic_retention_recipe, full_lifecycle_recipe
- **Tests**: 179 tests (models, parser, recipes, emitters, pack.yml, templates)

### Models
- `RetentionPolicy`: Policy cho entity type với retention_days, action, exemptions
- `ArchivedRecord`: Cold storage entry với data snapshot và restore
- `ErasureRequest`: GDPR erasure với subject scan, progress, completion tracking
- `RetentionEngine`: In-memory engine với policy/archive/erasure/exemption management

### Enums
- `RetentionAction`: archive, purge, anonymize, archive_then_purge
- `RetentionPolicyType`: time_based, event_based, status_based
- `RetentionPolicyStatus`: active, paused, expired
- `ArchiveStatus`: pending, archiving, archived, failed
- `ErasureStatus`: pending, processing, completed, failed, partially_completed
