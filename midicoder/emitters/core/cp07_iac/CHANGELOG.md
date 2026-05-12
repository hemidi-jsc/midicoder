# Changelog — CP07 Infrastructure as Code Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
