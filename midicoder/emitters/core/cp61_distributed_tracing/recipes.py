# coding: utf-8
"""
Mô-đun recipes cho CP61 — Distributed Tracing & Correlation ID.

Cung cấp các recipe để build TracingIR cho các use case phổ biến:
- opentelemetry_tracing_recipe: OpenTelemetry với auto-instrumentation
- correlation_id_recipe: X-Correlation-ID middleware + propagation
- jaeger_exporter_recipe: Jaeger tracer với batching
- full_tracing_recipe: Full trace + log correlation + metrics integration

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp61_distributed_tracing.parser import (
    TracingIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: TracingIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: TracingIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def opentelemetry_tracing_recipe() -> RecipeOutput:
    """Recipe: OpenTelemetry với auto-instrumentation.

    Cấu hình tracing chuẩn OpenTelemetry:
    - OTel Collector exporter
    - W3C Trace Context propagation
    - Probabilistic sampler (100%)
    - Các span cho HTTP server/client operations

    Returns:
        RecipeOutput chứa TracingIR
    """
    data = {
        "configs": [
            {
                "config_id": "otel_main",
                "name": "OpenTelemetry Main Config",
                "sampler": "always_on",
                "sample_rate": 1.0,
                "exporter": "otel",
                "propagation_format": "w3c",
                "service_name": "app-service",
            }
        ],
        "exporters": [
            {
                "exporter_id": "otel_collector",
                "name": "OTel Collector",
                "type": "otel",
                "endpoint": "http://localhost:4318",
                "batching_interval": 5,
                "max_queue_size": 2048,
            }
        ],
        "spans": [
            {
                "span_id": "http_server_span",
                "operation_name": "HTTP Server",
                "kind": "server",
                "attributes": {
                    "http.method": "dynamic",
                    "http.route": "dynamic",
                    "http.status_code": "dynamic",
                },
                "timeout_ms": 30000,
            },
            {
                "span_id": "http_client_span",
                "operation_name": "HTTP Client",
                "kind": "client",
                "attributes": {
                    "http.method": "dynamic",
                    "http.url": "dynamic",
                    "http.status_code": "dynamic",
                },
                "timeout_ms": 10000,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="opentelemetry_tracing_recipe",
        description="OpenTelemetry với auto-instrumentation — W3C propagation, OTel Collector",
        ir=ir,
        raw_data=data,
    )


def correlation_id_recipe() -> RecipeOutput:
    """Recipe: X-Correlation-ID middleware + propagation.

    Cấu hình correlation ID cho request tracking:
    - X-Correlation-ID header
    - Propagate đến downstream services
    - UUID4 format
    - Không mask sensitive data

    Returns:
        RecipeOutput chứa TracingIR
    """
    data = {
        "configs": [
            {
                "config_id": "correlation_config",
                "name": "Correlation ID Config",
                "sampler": "always_on",
                "sample_rate": 1.0,
                "exporter": "otel",
                "propagation_format": "w3c",
                "service_name": "app-service",
            }
        ],
        "correlation_fields": [
            {
                "field_id": "x_correlation_id",
                "name": "Correlation ID",
                "header_name": "X-Correlation-ID",
                "propagate": True,
                "mask_sensitive": False,
                "format": "uuid4",
            }
        ],
        "spans": [
            {
                "span_id": "correlation_middleware_span",
                "operation_name": "Correlation ID Middleware",
                "kind": "server",
                "attributes": {
                    "correlation.header": "X-Correlation-ID",
                    "correlation.format": "uuid4",
                },
                "timeout_ms": 5000,
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="correlation_id_recipe",
        description="X-Correlation-ID middleware + propagation — UUID4 format, cross-service",
        ir=ir,
        raw_data=data,
    )


def jaeger_exporter_recipe() -> RecipeOutput:
    """Recipe: Jaeger tracer với batching.

    Cấu hình Jaeger-specific tracing:
    - Jaeger exporter với UDP/HTTP
    - Jaeger propagation format
    - Probabilistic sampler (50%)
    - Batching interval 2 giây

    Returns:
        RecipeOutput chứa TracingIR
    """
    data = {
        "configs": [
            {
                "config_id": "jaeger_config",
                "name": "Jaeger Tracing Config",
                "sampler": "probabilistic",
                "sample_rate": 0.5,
                "exporter": "jaeger",
                "propagation_format": "jaeger",
                "service_name": "app-service",
            }
        ],
        "exporters": [
            {
                "exporter_id": "jaeger_http",
                "name": "Jaeger HTTP Exporter",
                "type": "jaeger",
                "endpoint": "http://jaeger-collector:14268/api/traces",
                "batching_interval": 2,
                "max_queue_size": 1024,
            }
        ],
        "spans": [
            {
                "span_id": "jaeger_server_span",
                "operation_name": "Jaeger HTTP Server",
                "kind": "server",
                "attributes": {
                    "jaeger.debug": "false",
                    "http.method": "dynamic",
                    "http.route": "dynamic",
                },
                "timeout_ms": 30000,
            },
            {
                "span_id": "jaeger_db_span",
                "operation_name": "Database Query",
                "kind": "client",
                "attributes": {
                    "db.system": "dynamic",
                    "db.statement": "dynamic",
                    "db.operation": "dynamic",
                },
                "timeout_ms": 5000,
            },
            {
                "span_id": "jaeger_mq_producer_span",
                "operation_name": "Message Queue Producer",
                "kind": "producer",
                "attributes": {
                    "messaging.system": "dynamic",
                    "messaging.destination": "dynamic",
                    "messaging.operation": "send",
                },
                "timeout_ms": 10000,
            },
            {
                "span_id": "jaeger_mq_consumer_span",
                "operation_name": "Message Queue Consumer",
                "kind": "consumer",
                "attributes": {
                    "messaging.system": "dynamic",
                    "messaging.destination": "dynamic",
                    "messaging.operation": "process",
                },
                "timeout_ms": 30000,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="jaeger_exporter_recipe",
        description="Jaeger tracer với batching — UDP/HTTP exporter, 50% sampling",
        ir=ir,
        raw_data=data,
    )


def full_tracing_recipe() -> RecipeOutput:
    """Recipe: Full trace + log correlation + metrics integration.

    Cấu hình distributed tracing đầy đủ:
    - OTel Collector exporter
    - W3C propagation
    - Always-on sampler (100%)
    - X-Correlation-ID với propagation
    - Log correlation (trace_id, span_id vào logs)
    - Các span cho HTTP, DB, MQ
    - Log level DEBUG cho trace context injection

    Returns:
        RecipeOutput chứa TracingIR
    """
    data = {
        "configs": [
            {
                "config_id": "full_tracing_config",
                "name": "Full Tracing Configuration",
                "sampler": "always_on",
                "sample_rate": 1.0,
                "exporter": "otel",
                "propagation_format": "w3c",
                "service_name": "app-service",
            }
        ],
        "correlation_fields": [
            {
                "field_id": "x_correlation_id",
                "name": "Correlation ID",
                "header_name": "X-Correlation-ID",
                "propagate": True,
                "mask_sensitive": False,
                "format": "uuid4",
            },
            {
                "field_id": "x_request_id",
                "name": "Request ID",
                "header_name": "X-Request-ID",
                "propagate": True,
                "mask_sensitive": False,
                "format": "uuid4",
            }
        ],
        "spans": [
            {
                "span_id": "http_server_span",
                "operation_name": "HTTP Server",
                "kind": "server",
                "attributes": {
                    "http.method": "dynamic",
                    "http.route": "dynamic",
                    "http.status_code": "dynamic",
                },
                "timeout_ms": 30000,
            },
            {
                "span_id": "http_client_span",
                "operation_name": "HTTP Client",
                "kind": "client",
                "attributes": {
                    "http.method": "dynamic",
                    "http.url": "dynamic",
                },
                "timeout_ms": 10000,
            },
            {
                "span_id": "db_query_span",
                "operation_name": "Database Query",
                "kind": "client",
                "attributes": {
                    "db.system": "dynamic",
                    "db.statement": "dynamic",
                    "db.operation": "dynamic",
                },
                "timeout_ms": 5000,
            },
            {
                "span_id": "mq_producer_span",
                "operation_name": "Message Queue Producer",
                "kind": "producer",
                "attributes": {
                    "messaging.system": "dynamic",
                    "messaging.destination": "dynamic",
                },
                "timeout_ms": 10000,
            },
            {
                "span_id": "mq_consumer_span",
                "operation_name": "Message Queue Consumer",
                "kind": "consumer",
                "attributes": {
                    "messaging.system": "dynamic",
                    "messaging.destination": "dynamic",
                },
                "timeout_ms": 30000,
            },
        ],
        "exporters": [
            {
                "exporter_id": "otel_collector",
                "name": "OTel Collector",
                "type": "otel",
                "endpoint": "http://otel-collector:4318",
                "batching_interval": 5,
                "max_queue_size": 2048,
            }
        ],
        "log_correlation": [
            {
                "config_id": "log_trace_correlation",
                "trace_id_field": "trace_id",
                "span_id_field": "span_id",
                "correlation_id_field": "correlation_id",
                "inject_into_logs": True,
                "log_level_for_trace": "DEBUG",
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_tracing_recipe",
        description="Full distributed tracing — OTel + correlation + log correlation + metrics",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "opentelemetry_tracing_recipe",
    "correlation_id_recipe",
    "jaeger_exporter_recipe",
    "full_tracing_recipe",
]
