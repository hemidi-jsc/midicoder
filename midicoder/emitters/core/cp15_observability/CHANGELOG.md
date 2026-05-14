# Changelog — CP15 Observability Stack Generator

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **OpenTelemetry models**: `OTLPExportProtocol`, `SamplerType`, `SpanKind`, `OTelExporterConfig`, `OpenTelemetryConfig`
- **Log Shipping models**: `LogDestinationType`, `LogShippingDestination`, `LogShippingConfig`
- **Parser extensions**: `opentelemetry` DSL section, `log_shipping` DSL section (`_parse_otel_config`, `_parse_otel_exporter`, `_parse_sampler_type`, `_parse_log_shipping_config`, `_parse_log_destination`)
- **B3 propagation**: `inject_trace_header(format="b3")`, `_inject_b3()`, `extract_trace_header(format="b3")`, `_extract_b3()` trong `tracing.py`
- **Metrics endpoint**: `generate_metrics_endpoint()` cho FastAPI + NestJS emitters
- **Jinja2 templates**: `metrics_endpoint.py.jinja2` (FastAPI), `metrics.controller.ts.jinja2` (NestJS)
- **Tests (models)**: 64+ test methods cho 8 model mới (`OTLPExportProtocol`, `SamplerType`, `SpanKind`, `LogDestinationType`, `OTelExporterConfig`, `OpenTelemetryConfig`, `LogShippingDestination`, `LogShippingConfig`)
- **Tests (parser)**: 19 test methods cho parser extensions (`opentelemetry`, `log_shipping` DSL sections)
- **Test organization**: Di chuyển 5 test files từ `tests/emitters/` → `cp15_observability/tests/`

### Fixed

- **Angular LogViewer import path**: Sửa `./logging_service` → `../../core/observability/logging_service` (cả template + emitter)
- **Integration tests**: Loại bỏ `TestQueryEffectsIntegration` và `TestCommandEffectsIntegration` (dùng `inspect.getsource()` + `MagicMock` — fragile, dễ break khi refactor)

### Changed

- **taxonomy.yml sync**: Update `definitions_count: 9`, `obligations_count: 5`, thêm `opentelemetry_export`, `log_shipping`, `span_propagation`
- **pack.yml**: Thêm `metrics_endpoint.py.jinja2` (FastAPI) và `metrics.controller.ts.jinja2` (NestJS) vào `file_contributions`
- **`__init__.py`**: Thêm export cho tất cả model mới (`LogDestinationType`, `LogShippingConfig`, `LogShippingDestination`, `OpenTelemetryConfig`, `OTelExporterConfig`, `OTLPExportProtocol`, `SamplerType`, `SpanKind`)

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
