# Changelog — CP20 API Client & Integration Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: ApiSpec, ClientBinding, RealtimeBridgeSpec, TransportType, AuthMode, HttpMethod
- **Angular Emitter**: ApiClientService, RealtimeBridgeService, OpenApiBindModule
- **React Emitter**: useApiClient, useRealtime, ApiTypes
- **FastAPI Emitter**: OpenAPI endpoint, WebSocket gateway
- **NestJS Emitter**: OpenAPIModule, WebSocketGateway
- **Angular Integration**: ApiClientService, RealtimeBridgeService, OpenApiBindModule
- **React Integration**: useApiClient, useRealtime, ApiTypes

---

**Capabilities Provided:** `api_client_generate`, `realtime_bridge`, `openapi_bind`

**Capabilities (Runtime):** `typed_client`, `websocket_bridge`, `sse_bridge`, `openapi_binding`

**Obligations:**

1. **TypeSafety** — Client types must match backend route types exactly
2. **ErrorMapping** — Backend errors must be mapped to client-side error types
3. **AuthInjection** — Each request must automatically attach auth token

**Dependencies:** CP06, CP18
