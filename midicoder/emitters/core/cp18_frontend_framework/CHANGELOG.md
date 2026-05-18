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

**Known Scope Gaps (P2 backlog):**

The following capabilities are NOT in scope for v1.0 — planned for future releases:

| # | Capability | Priority | Rationale |
|---|-----------|----------|-----------|
| 1 | **API Service Layer** | HIGH | HttpClient/RTK Query service generation — owned by CP20 |
| 2 | **Middleware/Interceptor** | HIGH | Auth/error/caching interceptors — requires CP03 integration |
| 3 | **Theme Management** | MEDIUM | Dynamic theme, dark mode, CSS variables |
| 4 | **Error Boundary** | MEDIUM | React ErrorBoundary / Angular global error handler |
| 5 | **Loading/Skeleton** | MEDIUM | Loading spinner, skeleton screen components |
| 6 | **Form Validation Library** | MEDIUM | react-hook-form, zod, yup integration |
| 7 | **PWA Manifest** | MEDIUM | manifest.json, service worker |
| 8 | **i18n/Localization** | MEDIUM | Translation files, locale config |
| 9 | **Environment Config** | MEDIUM | .env, environment.ts templates |
| 10 | **Module Federation** | LOW | Micro Frontend (Webpack/Vite Module Federation) |
| 11 | **SSR/SSG** | LOW | Next.js/Nuxt.js support — SPA only in v1 |
