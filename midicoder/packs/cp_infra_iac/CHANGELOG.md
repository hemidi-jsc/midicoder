# Changelog — I01 Infrastructure as Code (cp_infra_iac)

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-28

### Changed

- **Migrated from CP07 to I01**: Renamed from `cp07_iac` to `cp_infra_iac` (taxonomy-v2)
- **Pack ID**: `CP07` → `I01`
- **Internal ID**: `cp07_iac` → `cp_infra_iac`
- **Error codes**: `MDC-CP07-*` → `MDC-I01-*`
- **Template paths**: Updated from `cp07_iac/` → `cp_infra_iac/`
- **Pack emitters**: Updated from `cp07.*` → `cp_infra_iac.*`
- Added `render_context_support: true` and `type: infra` fields
- Added `type: "infra"` category classification

## [1.0.0] - 2026-05-06

### Added

- **Models**: IacProfile, ServiceConfig
- **Docker Compose**: Local runtime emission with service definitions
- **Terraform AWS**: AWS baseline profiles (ECS, RDS, ElastiCache)

---

**Capabilities Provided:** `emit_iac_docker`, `emit_iac_aws`

**Capabilities (Runtime):** `docker_compose`, `terraform_aws`

**Obligations:**

1. **EnvParity** — Local and production infrastructure must maintain parity

**Dependencies:** none
