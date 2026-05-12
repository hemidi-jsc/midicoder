# Changelog: CP20 API Client & Integration Generator

## [1.0.0] - 2026-05-06

### Added
- Models: ApiSpec, ClientBinding, RealtimeBridgeSpec
- Enums: TransportType, AuthMode, HttpMethod
- Angular Emitter: api-client.service.ts, realtime-bridge.service.ts, openapi-bind.ts
- React Emitter: api-client.ts, realtime-hooks.ts, openapi-bind.ts
- FastAPI Emitter: openapi_endpoint.py, websocket_gateway.py
- NestJS Emitter: openapi.module.ts, websocket.gateway.ts
- pack.yml: Self-declare capabilities (api_client_generate, realtime_bridge, openapi_bind)
- Error codes: MDC-CP20-001 to MDC-CP20-005
- 3 obligations: Type Safety, Error Mapping, Auth Injection
