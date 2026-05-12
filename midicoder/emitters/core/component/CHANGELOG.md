# Changelog — CP18 Frontend Framework Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.0] - 2025-07-26

### Added
- **models.py**: 3 definitions (`FrontendApp`, `RouteDefinition`, `StateStoreConfig`) + 4 enums (`FrontendFramework`, `StateStoreType`, `RouterStrategy`, `AppShellLayout`)
- **parser.py**: `FrontendFrameworkParser` — YAML DSL parser producing `{"frontend_app", "routes", "state_store"}` dict
- **angular.py**: `AngularComponentEmitter` — `emit()` (CRUD components), `emit_routes()`, `emit_state_store()`
- **react.py**: `ReactComponentEmitter` — `emit()` (CRUD components), `emit_routes()`, `emit_state_store()`
- **fastapi.py**: `FastAPIFrontendEmitter` — `generate()` → `frontend_config_service.py` + `frontend_router.py`
- **nestjs.py**: `NestJSFrontendEmitter` — `generate()` → module + service + controller
- **pack.yml**: Pack manifest with `capabilities_provided: [app_shell_scaffold, route_define, state_store_init]`
- **Error codes**: `MDC-CP18-001` through `MDC-CP18-010` in `midicoder/errors.py`
- **Templates (FastAPI)**: `frontend_config_service.py.jinja2`, `frontend_router.py.jinja2`
- **Templates (NestJS)**: `frontend-config.module.ts.jinja2`, `frontend-config.service.ts.jinja2`, `frontend-config.controller.ts.jinja2`
- **Templates (Angular)**: `app.routes.ts.jinja2`, `store.ts.jinja2`
- **Templates (React)**: `routes.tsx.jinja2`, `store.ts.jinja2`
- **Tests**: 76 tests (33 models + 15 parser + 19 emitters + 9 integration)

### Changed
- **taxonomy.yml**: CP18 status `developing` → `stable`
