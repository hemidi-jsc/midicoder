# Changelog — CP19 UI Component Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-06

### Added

- **Models**: ComponentSpec, FormFieldSpec, TableSpec, TableColumn
- **Enums**: ComponentType, FieldType
- **Angular Emitter**: FormFieldComponent, DataTableComponent, CardListComponent, DialogComponent
- **React Emitter**: FormField, DataTable, CardList, Dialog
- **FastAPI Emitter**: Form validation service, Pydantic schemas
- **NestJS Emitter**: Form validation DTOs, ValidationPipe
- **Angular Integration**: FormFieldComponent, DataTableComponent, CardListComponent, DialogComponent
- **React Integration**: FormField, DataTable, CardList, Dialog

---

**Capabilities Provided:** `component_render`, `form_generate`, `table_generate`

**Capabilities (Runtime):** `form_fields`, `data_tables`, `card_lists`, `dialogs`

**Obligations:**

1. **ComponentSchemaConsistency** — Component schemas must match entity field types from CP01

**Dependencies:** CP18
