# Changelog

## [1.0.0] - 2026-05-24

### Added

- **Models**: BulkAction, JobStatus, ChunkStatus, RetryStrategy enums
- **Models**: BulkJob, BulkChunk, BulkResult, DLQEntry dataclasses
- **Engine**: BulkEngine với create_job, process_job, cancel_job, retry_record, get_progress, get_dlq_entries, replay_dlq
- **Parser**: BulkIR + parse_bulk_jobs, parse_bulk_config, parse_dlq_config, parse_to_ir
- **Recipes**: basic_bulk_recipe, full_bulk_recipe
- **Emitters**: FastAPIBulkOpsEmitter, NestJSBulkOpsEmitter, AngularBulkOpsEmitter, ReactBulkOpsEmitter
- **Templates FastAPI**: bulk_models, bulk_schemas, bulk_service, bulk_router, bulk_worker, bulk_dlq_worker, bulk_sse
- **Templates NestJS**: bulk.entity, bulk.dto, bulk.service, bulk.controller, bulk.module, bulk.scheduler, bulk.gateway
- **Templates Angular**: bulk-dashboard, bulk-jobs, bulk-job-details, bulk.service, bulk.store, bulk-types
- **Templates React**: BulkDashboard, BulkJobs, BulkJobDetails, BulkProgress, useBulkOps
- **Pack manifest**: pack.yml với file_contributions cho 4 stacks
- **Tests**: test_models (55 tests), test_parser (21 tests), test_recipes (21 tests)

### Integration

- Tích hợp CP05 (Event-Driven): emit events cho bulk job lifecycle
- Tích hợp CP13 (Background Job): delegate chunk processing
- Tích hợp CP14 (Audit Trail): ghi audit log cho mọi bulk job
- Multi-tenant: tenant scope enforcement (CP02)
- Realtime progress: SSE endpoint cho FastAPI, WebSocket gateway cho NestJS
