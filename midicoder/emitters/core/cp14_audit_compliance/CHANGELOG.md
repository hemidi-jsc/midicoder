# Changelog — CP14 Audit Trail & Compliance Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: AuditTrail, AuditRule, ComplianceControl
- **Enums**: AuditActionType, AuditLevel, ControlType, EnforcementLevel, StandardType
- **FastAPI Emitter**: Audit logger, audit middleware, compliance reporter
- **NestJS Emitter**: AuditModule, AuditService, ComplianceService
- **Angular Integration**: AuditLoggerService, AuditLogListComponent
- **React Integration**: useAudit, AuditLogList

---

**Capabilities Provided:** `write_audit_log`, `audit_query`, `compliance_report`

**Capabilities (Runtime):** `audit_logger`, `audit_query_engine`, `compliance_checker`

**Obligations:**

1. **AuditImmutability** — Audit logs must be append-only and tamper-proof

**Dependencies:** CP01
