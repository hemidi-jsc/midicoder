# Changelog: CP17 Business Intelligence & Analytics Generator

## [1.0.0] - 2026-05-06

### Added
- Models: AnalyticsModel, DashboardDefinition, ScheduledReport
- Enums: AnalyticsSourceType, AggregationType, VisualizationType, ReportFrequency, ReportFormat, SchedulePolicy
- FastAPI Emitter: analytics endpoints, dashboard renderer, report scheduler
- NestJS Emitter: analytics.module.ts, dashboard.service.ts, report-scheduler.service.ts
- pack.yml: Self-declare capabilities (analytics_query, dashboard_build, report_schedule)
- Error codes: MDC-CP17-001 to MDC-CP17-015
