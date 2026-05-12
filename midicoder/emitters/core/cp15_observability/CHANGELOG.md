# Changelog — CP15 Observability Stack Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-07

### Added

- **Models**: MetricProfile, StructuredLogConfig, TraceConfig
- **Enums**: MetricType, LogLevel, TracePropagationFormat
- **FastAPI Emitter**: Observability service, observability middleware
- **NestJS Emitter**: ObservabilityModule, MetricsService, TracingService
- **Angular Integration**: LoggingService, LogViewerComponent
- **React Integration**: useLogging, LogViewer

---

**Capabilities Provided:** `emit_metric`, `structured_logging`, `distributed_tracing`

**Capabilities (Runtime):** `metrics`, `structured_logging`, `tracing`

**Obligations:**

1. **LogStructured** — All logs must be structured JSON with correlation IDs
2. **TracePropagation** — Trace context must propagate across service boundaries

**Dependencies:** CP07
