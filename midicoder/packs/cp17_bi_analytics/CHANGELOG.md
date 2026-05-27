# Changelog — CP17 Business Intelligence & Analytics Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: AnalyticsModel, DashboardDefinition, ScheduledReport
- **Enums**: AnalyticsSourceType, AggregationType, VisualizationType, ReportFrequency, ReportFormat, SchedulePolicy
- **FastAPI Emitter**: Analytics service, analytics router, report scheduler
- **NestJS Emitter**: AnalyticsModule, AnalyticsService, ReportService
- **Angular Integration**: AnalyticsWidget, ReportViewer
- **React Integration**: AnalyticsChart, ReportTable

---

**Capabilities Provided:** `analytics_query`, `dashboard_build`, `report_schedule`

**Capabilities (Runtime):** `analytics_query_engine`, `dashboard_builder`, `report_scheduler`

**Obligations:**

1. **ModelNameRequired** — AnalyticsModel.name must be non-empty
2. **DataFreshness** — AnalyticsModel.max_stale_seconds must be >= 1
3. **DashboardNameRequired** — DashboardDefinition.name must be non-empty
4. **RefreshIntervalMinimum** — DashboardDefinition.refresh_interval_seconds must be >= 5
5. **ReportNameRequired** — ScheduledReport.name must be non-empty
6. **ReportNextRunAuto** — ScheduledReport.next_run auto-assigned when None

**Dependencies:** CP08, CP15
