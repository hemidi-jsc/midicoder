# Changelog: CP53 Domain Pack Runtime Bridge

## [1.0.0] - 2026-05-06

### Added
- Models: DomainPackDescriptor, BridgeBinding, RuntimeInvoker
- FastAPI Emitter: FastAPIDomainBridgeEmitter
- NestJS Emitter: NestJSDomainBridgeEmitter
- pack.yml: Self-declare capabilities (bridge_domain_pack, runtime_invoke)
- Error codes: MDC-CP53-001 to MDC-CP53-005
- 2 obligations: BridgeBinding references existing CP capability, RuntimeInvoker has registered DP target
- Meta pack — no frontend/backend emitter needed
