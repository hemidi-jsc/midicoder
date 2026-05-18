# Changelog — CP06 API Gateway & Service Mesh Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-18

### Added

- **Unified Gateway Emitters**: FastAPIGatewayEmitter, NestJSGatewayEmitter, AngularGatewayEmitter, ReactGatewayEmitter
- **Pipeline Integration**: Registered all 4 stacks in EMITTER_REGISTRY (`cp06.gateway.{fastapi,nestjs,angular,react}`)
- **Parser Integration**: Registered `cp06_gateway` in PARSER_REGISTRY with `RouteParser.parse_from_metadata()`
- **RouteParser.dispatch**: Added CP06-specific dispatch logic in PackEmitterRouter
- **Pack metadata**: Updated `pack.yml` — definitions_count 2→29, obligations_count 0→8, capabilities expanded
- **Comprehensive tests**: 132 unit tests + 10-phase E2E test (moved from `tests/emitters/` into pack folder)
- **DSL validation tests**: Kong Gateway + Consul Service Mesh node validation (672 lines)

### Changed

- **Pack status**: `stable` → `developing` (active feature development)
- ****init**.py**: Added exports for all 4 unified gateway emitters
- **Test organization**: Moved 4 test files (2,405 lines) from `tests/emitters/` and `tests/dsl/` into `cp06_api_gateway/tests/`

### Fixed

- **Missing EMITTER_REGISTRY entries**: CP06 was not dispatchable through the pipeline
- **Missing PARSER_REGISTRY entry**: Raw MIR dicts could not be parsed into RouteCollection
- **Incomplete pack.yml**: Only listed 2 definitions out of 29 actual models

---

**Capabilities Provided:** `route_request`, `gateway_binding`, `service_mesh_config`, `http_routing`, `graphql_routing`, `webhook_handling`, `circuit_breaker`, `rate_limiting`, `tenant_isolation`, `load_balancing`

**Capabilities (Runtime):** `kong_gateway`, `consul_mesh`, `http_routing`, `graphql_routing`, `webhook`, `circuit_breaker`, `rate_limiting`, `tenant_aware`

**Obligations:** RouteAuthEnforced, TenantIsolation, ValidHttpMethod, ValidPathPattern, WebhookSignatureVerify, GraphQLAuthRequired, ConsulServiceRegistration, KongPluginScope

**Dependencies:** CP01, CP05

## [1.0.0] - 2026-05-12

### Added

- **Models**: GatewayProfile, RouteSpec
- **FastAPI Emitter**: HTTP/GraphQL/Webhook route handlers, Kong Gateway config
- **NestJS Emitter**: Route controllers, Kong Gateway module, Consul service mesh
- **Kong Gateway**: Declarative configuration emission
- **Consul Service Mesh**: Service discovery and mesh config

---

**Capabilities Provided:** `route_request`, `gateway_binding`, `service_mesh_config`

**Capabilities (Runtime):** `kong_gateway`, `consul_mesh`, `http_routing`, `graphql_routing`

**Obligations:** none

**Dependencies:** CP01, CP05
