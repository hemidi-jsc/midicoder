# Changelog — CP18 Frontend Framework Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: FrontendApp, RouteDefinition, StateStoreConfig, FrontendFramework, StateStoreType, RouterStrategy, AppShellLayout
- **Parser**: FrontendFrameworkParser (YAML → FrontendApp + RouteDefinition[] + StateStoreConfig)
- **Angular Emitter**: App shell with Angular Material, routing module, Signals-based state store
- **React Emitter**: App shell with TailwindCSS, React Router v6, Zustand state store
- **FastAPI Emitter**: Frontend config service
- **NestJS Emitter**: Frontend config module
- **Angular Integration**: AppShellModule, AppRoutes, StateStoreModule
- **React Integration**: AppShell, AppRouter, useStore

---

**Capabilities Provided:** `app_shell_scaffold`, `route_define`, `state_store_init`

**Capabilities (Runtime):** `app_shell`, `routing`, `state_store`

**Obligations:**

1. **RouteEntityMapping** — Auto-generated routes must map 1:1 to domain entities
2. **StateStoreIsolation** — State stores must be namespaced per feature module

**Dependencies:** CP01
