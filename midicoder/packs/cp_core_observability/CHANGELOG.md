# Changelog — C03 Observability Stack (Core Pack)

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-28

### Added

- **Merged CP61 capabilities**: `correlation_id`, `trace_export`, `log_trace_correlation` from CP61 Distributed Tracing
- **Merged CP61 definitions**: `CorrelationField`, `SpanDefinition`, `TraceExporter`, `LogCorrelationConfig`
- **Merged CP61 obligations**: `TraceContextPropagation`, `LogTraceCorrelation`
- **New capability**: `correlation_id` (W3C/B3/Jaeger context propagation)
- **New capability**: `trace_export` (Jaeger, Zipkin, OTel Collector, Datadog)
- **New capability**: `log_trace_correlation` (inject trace_id/span_id into logs)

### Changed

- **Pack rename**: CP15 → C03 (taxonomy-v2 migration)
- **Internal ID**: `cp15_observability` → `cp_core_observability`
- **Category**: `observability` → `core`
- **Type**: added `type: core`
- **Dependencies**: `CP07` → `I01`
- **All imports**: updated from `midicoder.packs.cp15_observability` → `midicoder.packs.cp_core_observability`
- **Template paths**: updated from `cp15_observability/` → `cp_core_observability/`
- **Stack directories**: renamed `cp15_observability/` → `cp_core_observability/` (fastapi, nestjs, angular, react)
- **Render context**: added `render_context_support: true`
- **Old IDs**: added `old_ids: [CP15, CP61]` for backward compatibility
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
