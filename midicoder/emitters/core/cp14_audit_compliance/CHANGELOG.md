# Changelog — CP14 Audit Trail & Compliance Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-14

### Added

- **Models**: LedgerEntry, ImmutableLedgerConfig, ComplianceReportConfig, ReportSummary
- **Models**: LedgerStorageBackend, LedgerVerificationMode, ReportFormat, ReportScope, ComplianceStandard enums
- **Recipes**: basic_audit_recipe, immutable_ledger_recipe
- **Recipes**: gdpr_compliance_recipe, hipaa_compliance_recipe, sox_compliance_recipe, pci_dss_compliance_recipe
- **Recipes**: generate_compliance_report_config
- **FastAPI**: Audit API routes (POST /audit/log, GET /audit/query, GET /audit/entity, GET /audit/verify, GET /audit/export)
- **Templates**: All 8 templates updated to real Jinja2 (from static code)
- **Templates**: Sensitive data masking in audit logs
- **Tests**: Moved into pack folder (cp14_audit_compliance/tests/)
- **Tests**: test_recipes.py (73 tests for all recipes)
- **Tests**: test_ledger_report_models.py (98 tests for ledger/report models)
- **Tests**: test_emitters.py (45 tests for all 4 stack emitters)
- **Pack cohesion**: Single models.py, recipes.py added, **init**.py exports all public symbols
- **Obligations**: SensitiveDataMasking added (audit logs must mask sensitive fields)

### Changed

- **definitions_count**: 3 → 17 (all dataclasses + enums)
- **obligations_count**: 1 → 4 (AuditImmutability, LedgerChainIntegrity, ComplianceEvidence, SensitiveDataMasking)
- **capabilities_provided**: 3 → 7 (added immutable_ledger, compliance_reporting, tamper_detection, audit_export)
- **Templates**: Replaced static code with proper Jinja2 templates with collection context
- **Templates**: AuditActionType enum unified across all stacks (CREATE/UPDATE/DELETE/...)
- **FastAPI template**: AuditLogger now supports dual-write (DB + append-only JSONL file)
- **FastAPI template**: Sensitive data masking (password, secret, token, credit_card, ssn)
- **NestJS template**: Added DynamicModule pattern, AuditController, audit service
- **Taxonomy**: Updated to match actual pack state

### Removed

- **Tests**: test_audit_integration.py (moved to CP13 — tests AuditEffect, not CP14)

### Fixed

- Templates now render audit_logger.py.jinja2 with proper enum matching models.py AuditActionType
- Pack.yml file_contributions now includes per_command audit_api.py
- All models exported in **init**.py (LedgerEntry, ImmutableLedgerConfig, ComplianceReportConfig, ReportSummary, ...)

---

**Capabilities Provided:** `write_audit_log`, `audit_query`, `compliance_report`, `immutable_ledger`, `compliance_reporting`, `tamper_detection`, `audit_export`

**Capabilities (Runtime):** `audit_logger`, `audit_query_engine`, `compliance_checker`, `immutable_ledger`, `compliance_report`

**Obligations:**

1. **AuditImmutability** — Audit logs must be append-only and tamper-proof
2. **LedgerChainIntegrity** — Ledger hash chain must be verified on read; breaks must be alerted
3. **ComplianceEvidence** — Compliance reports must include evidence (old/new values)
4. **SensitiveDataMasking** — Sensitive fields must be masked in audit logs

**Dependencies:** CP01

---

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
