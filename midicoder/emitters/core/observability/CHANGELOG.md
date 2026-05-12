# Changelog: CP15 Observability Stack Generator

## [1.0.0] - 2026-05-06

### Added
- Models: MetricProfile, StructuredLogConfig, TraceConfig
- Enums: MetricType, LogLevel, TracePropagationFormat
- FastAPI emitter: metrics endpoint, structured logging middleware, trace context
- NestJS emitter: observability.module.ts, metrics.interceptor.ts, tracing.interceptor.ts
- pack.yml: Self-declare capabilities (emit_metric, structured_logging, distributed_tracing)
- Error codes: MDC-CP15-001 to MDC-CP15-010
