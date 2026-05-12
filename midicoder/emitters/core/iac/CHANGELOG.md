# Changelog: CP07 Infrastructure as Code Generator

## [1.0.0] - 2026-05-06

### Added
- Models: InfrastructureConfig, AWSInfrastructureConfig
- Constants: DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT
- Docker emitter: Dockerfile, docker-compose.yml
- AWS emitter: CloudFormation/Terraform templates
- pack.yml: Self-declare capabilities (emit_iac_docker, emit_iac_aws)
- Error codes: MDC-CP07-001 to MDC-CP07-005
