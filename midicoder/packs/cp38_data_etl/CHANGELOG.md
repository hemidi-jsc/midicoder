# Changelog — CP38 Data Import/Export/ETL

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-22

### Added

- **Models**: `ImportJob`, `ExportJob`, `ETLMapping`, `ExtractConfig`, `TransformConfig`, `LoadConfig`, `ETLStep`, `ETLJob`, `ImportError`, `BulkConfig`
- **Enums**: `ImportFormat`, `JobStatus`, `TransformType`, `ExtractSource`, `LoadMode`
- **Parser**: `ETLIR`, `parse_import_jobs()`, `parse_export_jobs()`, `parse_etl_pipelines()`, `parse_to_ir()`
- **Recipes**: `csv_import_recipe()`, `json_import_recipe()`, `data_migrate_recipe()`, `etl_pipeline_recipe()`, `bulk_export_recipe()`
- **FastAPI Emitter**: 11 Jinja2 templates — __init__, models, schemas, import/export/etl services, routers, bulk worker, csv/json parsers
- **NestJS Emitter**: 9 Jinja2 templates — entity, DTO, import/export/etl services, controllers, bulk processor, module
- **Angular Emitter**: 5 Jinja2 templates — import-wizard.component, export-dialog.component, import/export services, job-status.component
- **React Emitter**: 7 Jinja2 templates — ImportWizard, ExportDialog, useImportJob, useExportJob, JobStatusPanel, import/export services
- **Pack manifest**: `capabilities_provided` với 6 capabilities (csv_import, json_import, data_migrate, bulk_operation, etl_pipeline, data_export)

### Changed

- Updated taxonomy.yml — CP38 status `planned` → `stable`
- Added CP38 to CP_ID_TO_INTERNAL registry
- Updated TODOS.md — CP38 status TODO → DONE

### Fixed

- Template path consistency — FastAPI/NestJS paths khớp giữa pack.yml và emitter
- Rule V1 compliance — Generated code không import từ `midicoder.*`

---

**Capabilities Provided:** `csv_import`, `json_import`, `data_migrate`, `bulk_operation`, `etl_pipeline`, `data_export`

**Capabilities (Runtime):** `csv_import`, `json_import`, `data_migrate`, `bulk_operation`, `etl_pipeline`, `data_export`

**Recipes (5):** `csv_import_recipe`, `json_import_recipe`, `data_migrate_recipe`, `etl_pipeline_recipe`, `bulk_export_recipe`

**Obligations:**

1. **ImportDataIntegrity** — Tất cả import jobs phải đảm bảo data integrity với transaction rollback khi lỗi vượt quá threshold
2. **AuditTrailRequired** — Tất cả import/export/ETL jobs phải được audit log qua CP14 với job status và kết quả

**Dependencies:** CP01, CP08, CP13, CP14
