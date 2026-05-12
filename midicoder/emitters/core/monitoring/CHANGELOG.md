# Changelog: CP16 API & System Monitoring Generator

## [1.0.0] - 2026-05-06

### Added
- Models: DashboardProfile, AlertRule, SLIDefinition, Panel, FiredAlert, SLIStatus
- Enums: AlertSeverity, AlertCondition, SLIMetricType, DashboardType
- FastAPI emitter: monitoring endpoints, alert dispatcher
- NestJS emitter: monitoring.module.ts, alert.service.ts, sli-tracker.service.ts
- pack.yml: Self-declare capabilities (dashboard_create, alert_define, sli_monitor)
- Error codes: MDC-CP16-001 to MDC-CP16-010
