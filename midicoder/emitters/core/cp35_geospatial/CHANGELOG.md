# Changelog — CP35 Geospatial Services

## [1.0.0] — 2026-05-21

### Added

- GeoPoint, Geofence (3 shapes: circle/polygon/rectangle), RouteResult, RouteStep, GeospatialSpec
- Enums: GeofenceShape, DistanceUnit, RoutingProfile, GeofenceEvent
- GeospatialParser: YAML DSL + metadata dict parsing
- FastAPI emitter: 4 files (service, geofence, routing, routes)
- NestJS emitter: 4 files (service, geofence, routing, controller)
- Angular emitter: 2 components (map-viewer, geofence-alert)
- React emitter: 2 components (MapView, GeofenceAlert)
- 3 recipes: geofence_monitoring, routing_service, location_tracker
- 12 error codes MDC-CP35-001 ~ MDC-CP35-012
- Pack registered in EMITTER_REGISTRY (4 keys), PARSER_REGISTRY (1 key), contracts/registry.py
- Taxonomy: CP35 → stable

### Convention Compliance

- Rule V1: Generated code standalone (no midicoder imports in templates)
- Rule V2: Templates = structure only (no __post_init__ validation)
- Haversine formula for distance (deterministic)
- Ray casting for point-in-polygon
- OSRM integration with fallback
- DomSanitizer iframe (Angular), Subscription cleanup (ngOnDestroy)
- TypeScript type đầy đủ (React/TSX interface)
