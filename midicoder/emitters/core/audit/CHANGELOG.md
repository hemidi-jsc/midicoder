# Changelog — CP14: Audit Trail & Compliance Generator

## [1.0.0] - 2026-05-06

### Added
- `models.py`: AuditTrail, AuditRule, ComplianceControl, AuditComplianceCollection + enums
- `parser.py`: AuditComplianceParser (YAML DSL → Collection)
- `fastapi.py`: FastAPIAuditComplianceEmitter
- `nestjs.py`: NestJSAuditComplianceEmitter
- `audit_engine.py`: AuditLogger (dual write), AuditRuleEngine, ComplianceEnforcer
- `pack.yml`: Pack metadata (sync với taxonomy.yml CP14)
- Error codes MDC-CP14-001 ~ MDC-CP14-010 trong errors.py
- Tests: test_audit_models.py, test_audit_parser.py

### Notes
- CP14 thay thế `write_audit_log` capability của contracts
- Dual write: database + append-only file logs
- SHA-256 hash chain cho tamper-evidence (RX11)
- Standard retention + archive policy