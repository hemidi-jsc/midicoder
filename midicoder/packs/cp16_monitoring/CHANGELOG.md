# Changelog — CP16 API & System Monitoring Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: DashboardProfile, AlertRule, SLIDefinition
- **Enums**: AlertSeverity, AlertCondition, SLIMetricType, DashboardType
- **FastAPI Emitter**: Monitoring service, dashboard builder, alert engine
- **NestJS Emitter**: MonitoringModule, MonitoringService, MonitoringController
- **Angular Integration**: DashboardWidget, AlertPanel
- **React Integration**: DashboardPanel, AlertBanner

---

**Capabilities Provided:** `dashboard_create`, `alert_define`, `sli_monitor`

**Capabilities (Runtime):** `dashboard`, `alert_engine`, `sli_tracker`

**Obligations:**

1. **AlertNotification** — Alerts must route to configured notification channels

**Dependencies:** CP15
