# Changelog — CP06 API Gateway & Service Mesh Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
