# Changelog

## [Unreleased]

### Changed
- Merged route/ into gateway/ — unified CP06 API Gateway & Service Mesh pack
- Route models, parser, and emitters now reside as route_*.py within gateway/
- Updated resolver.py mapping: CP06 → gateway (was route)
- Added compat re-export in route/__init__.py for backward compatibility

### Added
- Route models: Route, GraphQLResolver, WebhookHandler, RouteCollection
- Route emitters: FastAPIRouteEmitter, NestJSRouteEmitter (merged from route/)

## [1.0.0] - 2026-05-12

### Added
- Kong Gateway configuration models (KongGateway, KongService, KongRoute, KongUpstream)
- Consul Service Mesh models (ConsulService, ConsulHealthCheck, ConsulConnect)
- HTTP REST route models with auth, tenant scope, request/response schemas
- GraphQL resolver models (query/mutation/subscription)
- Webhook handler models with HMAC signature verification
