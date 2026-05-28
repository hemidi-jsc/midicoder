# Changelog — CP34 Report & Document Generator

All notable changes to this pack will be documented in this file.

## [1.0.0] — 2026-05-21

### Added

- ReportSpec, BatchJob, ReportCollection models + enums (ReportFormat, ReportLayout, AggregationFunc, BatchJobStatus)
- ReportParser: YAML DSL + metadata dict parsing
- FastAPI emitter: 6 files (service, routes, worker, pdf/excel/csv generators)
- NestJS emitter: 6 files (service, controller, pdf/excel/csv generators, batch worker)
- Angular emitter: 3 components (report-list, report-viewer, batch-status)
- React emitter: 3 components (ReportList, ReportViewer, BatchStatus)
- 4 recipes: basic_report, pdf_report, excel_export, batch_workflow
- 15 error codes MDC-CP34-001 ~ MDC-CP34-015
- 90 unit tests (models, parser, emitters, recipes)
- Pack registered in EMITTER_REGISTRY (4 keys), PARSER_REGISTRY (1 key), contracts/registry.py
- Taxonomy: CP34 → stable

### Convention Compliance

- Rule V1: Generated code standalone (no midicoder imports in templates)
- Rule V2: Templates = structure only (no __post_init__ validation)
- Angular: DomSanitizer iframe, Subscription cleanup (ngOnDestroy)
- React: Full TypeScript interfaces
