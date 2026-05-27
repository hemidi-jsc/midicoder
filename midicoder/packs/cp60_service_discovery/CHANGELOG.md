# Changelog — CP60 Service Discovery & Config Center

## 1.0.0 (2026-05-26)

### Added

- **Service Discovery & Config Center** — Unified service discovery và centralized config management
- **4 Registry Providers**: Consul, etcd, ZooKeeper, Eureka
- **4 Load Balancing Strategies**: round_robin, least_connections, random, weighted
- **ServiceInstance** — Thực thể service với health check và metadata
- **ServiceRegistry** — Registry management với quorum và session TTL
- **ConfigEntry** — Cấu hình theo environment với encryption, versioning
- **ConfigWatch** — Watcher với polling và callback notification
- **LoadBalancingConfig** — Load balancing strategy với health check interval
- **ServiceDiscoveryIR** — Intermediate Representation cho DSL parsing
- **5 Jinja2 Templates × 2 stacks**: FastAPI, NestJS
- **4 Recipes**: consul_service_discovery, config_center, dynamic_config, load_balancing
- **Registry Integration** — CP60 registered trong contracts/registry.py

### Dependencies

- CP01 (Domain Model)
- CP05 (Event-Driven Architecture)
- CP14 (Audit Trail & Compliance)
