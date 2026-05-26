# coding: utf-8
"""
Mô-đun models cho CP61 — Distributed Tracing & Correlation ID.

Định nghĩa các dataclass biểu diễn:
- TraceConfig: Cấu hình distributed tracing (sampler, exporter, propagation)
- CorrelationField: Cấu hình correlation ID header và propagation
- SpanDefinition: Định nghĩa span cho các operation (server/client/producer/consumer)
- TraceExporter: Cấu hình exporter (Jaeger, Zipkin, OTel Collector, Datadog)
- LogCorrelationConfig: Cấu hình tương thích trace ID vào logs

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP61).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class SamplerType(str, Enum):
    """Loại sampler cho trace collection.

    - ALWAYS_ON: Thu thập mọi trace (phù hợp development/staging)
    - ALWAYS_OFF: Không thu thập trace nào (tắt tracing)
    - PROBABILISTIC: Mẫu xác suất theo tỷ lệ sample_rate
    - RATE_LIMITING: Giới hạn số trace per second
    """
    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    PROBABILISTIC = "probabilistic"
    RATE_LIMITING = "ratelimiting"


class ExporterType(str, Enum):
    """Loại trace exporter backend.

    - JAEGER: Jaeger tracing backend
    - ZIPKIN: Zipkin tracing backend
    - OTEL: OpenTelemetry Collector
    - DATADOG: Datadog APM
    """
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    OTEL = "otel"
    DATADOG = "datadog"


class PropagationFormat(str, Enum):
    """Định dạng propagation cho context cross-service.

    - W3C: W3C Trace Context (traceparent/tracestate headers)
    - B3: Zipkin B3 propagation headers
    - JAEGER: Jaeger propagation headers
    """
    W3C = "w3c"
    B3 = "b3"
    JAEGER = "jaeger"


class SpanKind(str, Enum):
    """Loại span trong distributed tracing.

    - SERVER: Span xử lý incoming request (server-side)
    - CLIENT: Span gửi outgoing request (client-side)
    - PRODUCER: Span publish message đến queue/topic
    - CONSUMER: Span consume message từ queue/topic
    """
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class CorrelationFormat(str, Enum):
    """Định dạng correlation ID.

    - UUID4: UUID version 4 (random)
    - SNOWFLAKE: Twitter Snowflake ID (timestamp-based, sorted)
    - TIMESTAMP: Unix timestamp + random suffix
    """
    UUID4 = "uuid4"
    SNOWFLAKE = "snowflake"
    TIMESTAMP = "timestamp"


class CorrelationHeader(str, Enum):
    """Tiêu đề HTTP cho correlation ID.

    - X_CORRELATION_ID: X-Correlation-ID (tiêu chuẩn phổ biến)
    - X_REQUEST_ID: X-Request-ID (nginx, Express convention)
    """
    X_CORRELATION_ID = "X-Correlation-ID"
    X_REQUEST_ID = "X-Request-ID"


class LogLevel(str, Enum):
    """Mức độ log cho trace correlation."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# ===========================================================================
# TraceConfig
# ===========================================================================


@dataclass
class TraceConfig:
    """Cấu hình distributed tracing cho một service.

    Định nghĩa cách thức thu thập, sampling, và export trace data
    cho một service cụ thể trong hệ thống distributed.

    Attributes:
        config_id: ID duy nhất của cấu hình tracing
        name: Tên mô tả của cấu hình
        sampler: Loại sampler (always_on, always_off, probabilistic, ratelimiting)
        sample_rate: Tỷ lệ sampling (0.0 - 1.0, chỉ dùng cho probabilistic)
        exporter: Loại exporter backend (jaeger, zipkin, otel, datadog)
        propagation_format: Định dạng propagation (w3c, b3, jaeger)
        service_name: Tên service trong trace context
        metadata: Dữ liệu bổ sung
    """
    config_id: str
    name: str = ""
    sampler: SamplerType = SamplerType.ALWAYS_ON
    sample_rate: float = 1.0
    exporter: ExporterType = ExporterType.OTEL
    propagation_format: PropagationFormat = PropagationFormat.W3C
    service_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.config_id or not self.config_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason="TraceConfig.config_id bắt buộc và không được để trống",
            )

        if not (0.0 <= self.sample_rate <= 1.0):
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"sample_rate phải nằm trong khoảng 0.0-1.0, nhận được: {self.sample_rate}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TraceConfig sang dict."""
        return {
            "config_id": self.config_id,
            "name": self.name,
            "sampler": self.sampler.value,
            "sample_rate": self.sample_rate,
            "exporter": self.exporter.value,
            "propagation_format": self.propagation_format.value,
            "service_name": self.service_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceConfig":
        """Tạo TraceConfig từ dict."""
        return cls(
            config_id=data["config_id"],
            name=data.get("name", ""),
            sampler=SamplerType(data.get("sampler", "always_on")),
            sample_rate=data.get("sample_rate", 1.0),
            exporter=ExporterType(data.get("exporter", "otel")),
            propagation_format=PropagationFormat(data.get("propagation_format", "w3c")),
            service_name=data.get("service_name", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# CorrelationField
# ===========================================================================


@dataclass
class CorrelationField:
    """Cấu hình correlation ID cho request propagation.

    Định nghĩa cách tạo và truyền correlation ID qua HTTP headers
    để track request xuyên suốt nhiều service.

    Attributes:
        field_id: ID duy nhất của correlation field
        name: Tên mô tả
        header_name: Tên HTTP header để truyền correlation ID
        propagate: Có propagate correlation ID đến downstream services không
        mask_sensitive: Có mask các giá trị nhạy cảm trong correlation không
        format: Định dạng correlation ID (uuid4, snowflake, timestamp)
        metadata: Dữ liệu bổ sung
    """
    field_id: str
    name: str = ""
    header_name: CorrelationHeader = CorrelationHeader.X_CORRELATION_ID
    propagate: bool = True
    mask_sensitive: bool = False
    format: CorrelationFormat = CorrelationFormat.UUID4
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate correlation field sau khi khởi tạo."""
        if not self.field_id or not self.field_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason="CorrelationField.field_id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CorrelationField sang dict."""
        return {
            "field_id": self.field_id,
            "name": self.name,
            "header_name": self.header_name.value,
            "propagate": self.propagate,
            "mask_sensitive": self.mask_sensitive,
            "format": self.format.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorrelationField":
        """Tạo CorrelationField từ dict."""
        return cls(
            field_id=data["field_id"],
            name=data.get("name", ""),
            header_name=CorrelationHeader(data.get("header_name", "X-Correlation-ID")),
            propagate=data.get("propagate", True),
            mask_sensitive=data.get("mask_sensitive", False),
            format=CorrelationFormat(data.get("format", "uuid4")),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# SpanDefinition
# ===========================================================================


@dataclass
class SpanDefinition:
    """Định nghĩa span cho một operation cụ thể.

    Mô tả span cần tạo cho một operation (HTTP endpoint, message handler, v.v.)
    bao gồm kind, attributes, và các liên kết với spans khác.

    Attributes:
        span_id: ID duy nhất của span definition
        operation_name: Tên operation (hiển thị trong trace UI)
        kind: Loại span (server, client, producer, consumer)
        attributes: Các attribute key-value gắn với span
        links_to: Danh sách span IDs liên kết (cho cross-service tracing)
        timeout_ms: Thời gian timeout tối đa của span (milliseconds)
        metadata: Dữ liệu bổ sung
    """
    span_id: str
    operation_name: str = ""
    kind: SpanKind = SpanKind.SERVER
    attributes: dict[str, Any] = field(default_factory=dict)
    links_to: list[str] = field(default_factory=list)
    timeout_ms: int = 30000
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate span definition sau khi khởi tạo."""
        if not self.span_id or not self.span_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason="SpanDefinition.span_id bắt buộc và không được để trống",
            )

        if self.timeout_ms < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"timeout_ms phải lớn hơn 0, nhận được: {self.timeout_ms}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển SpanDefinition sang dict."""
        return {
            "span_id": self.span_id,
            "operation_name": self.operation_name,
            "kind": self.kind.value,
            "attributes": self.attributes,
            "links_to": self.links_to,
            "timeout_ms": self.timeout_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpanDefinition":
        """Tạo SpanDefinition từ dict."""
        return cls(
            span_id=data["span_id"],
            operation_name=data.get("operation_name", ""),
            kind=SpanKind(data.get("kind", "server")),
            attributes=data.get("attributes", {}),
            links_to=data.get("links_to", []),
            timeout_ms=data.get("timeout_ms", 30000),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# TraceExporter
# ===========================================================================


@dataclass
class TraceExporter:
    """Cấu hình trace exporter backend.

    Định nghĩa kết nối đến backend trace storage (Jaeger, Zipkin, OTel, Datadog)
    với batching và queue settings.

    Attributes:
        exporter_id: ID duy nhất của exporter
        name: Tên mô tả của exporter
        type: Loại exporter backend
        endpoint: URL endpoint của exporter
        batching_interval: Khoảng thời gian batch (giây)
        max_queue_size: Kích thước queue tối đa trước khi drop spans
        metadata: Dữ liệu bổ sung
    """
    exporter_id: str
    name: str = ""
    type: ExporterType = ExporterType.OTEL
    endpoint: str = ""
    batching_interval: int = 5
    max_queue_size: int = 2048
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate exporter sau khi khởi tạo."""
        if not self.exporter_id or not self.exporter_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason="TraceExporter.exporter_id bắt buộc và không được để trống",
            )

        if self.batching_interval < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"batching_interval phải lớn hơn 0, nhận được: {self.batching_interval}",
            )

        if self.max_queue_size < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"max_queue_size phải lớn hơn 0, nhận được: {self.max_queue_size}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TraceExporter sang dict."""
        return {
            "exporter_id": self.exporter_id,
            "name": self.name,
            "type": self.type.value,
            "endpoint": self.endpoint,
            "batching_interval": self.batching_interval,
            "max_queue_size": self.max_queue_size,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceExporter":
        """Tạo TraceExporter từ dict."""
        return cls(
            exporter_id=data["exporter_id"],
            name=data.get("name", ""),
            type=ExporterType(data.get("type", "otel")),
            endpoint=data.get("endpoint", ""),
            batching_interval=data.get("batching_interval", 5),
            max_queue_size=data.get("max_queue_size", 2048),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# LogCorrelationConfig
# ===========================================================================


@dataclass
class LogCorrelationConfig:
    """Cấu hình tương thích trace ID vào logs.

    Cho phép inject trace_id, span_id, correlation_id vào log entries
    để correlate logs với traces trong observability platform.

    Attributes:
        config_id: ID duy nhất của cấu hình log correlation
        trace_id_field: Tên field trong log cho trace_id
        span_id_field: Tên field trong log cho span_id
        correlation_id_field: Tên field trong log cho correlation_id
        inject_into_logs: Có inject trace context vào logs không
        log_level_for_trace: Mức độ log tối thiểu để inject trace context
        metadata: Dữ liệu bổ sung
    """
    config_id: str
    trace_id_field: str = "trace_id"
    span_id_field: str = "span_id"
    correlation_id_field: str = "correlation_id"
    inject_into_logs: bool = True
    log_level_for_trace: LogLevel = LogLevel.DEBUG
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate log correlation config sau khi khởi tạo."""
        if not self.config_id or not self.config_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason="LogCorrelationConfig.config_id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển LogCorrelationConfig sang dict."""
        return {
            "config_id": self.config_id,
            "trace_id_field": self.trace_id_field,
            "span_id_field": self.span_id_field,
            "correlation_id_field": self.correlation_id_field,
            "inject_into_logs": self.inject_into_logs,
            "log_level_for_trace": self.log_level_for_trace.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogCorrelationConfig":
        """Tạo LogCorrelationConfig từ dict."""
        return cls(
            config_id=data["config_id"],
            trace_id_field=data.get("trace_id_field", "trace_id"),
            span_id_field=data.get("span_id_field", "span_id"),
            correlation_id_field=data.get("correlation_id_field", "correlation_id"),
            inject_into_logs=data.get("inject_into_logs", True),
            log_level_for_trace=LogLevel(data.get("log_level_for_trace", "DEBUG")),
            metadata=data.get("metadata", {}),
        )


__all__ = [
    # Enums
    "SamplerType",
    "ExporterType",
    "PropagationFormat",
    "SpanKind",
    "CorrelationFormat",
    "CorrelationHeader",
    "LogLevel",
    # Dataclasses
    "TraceConfig",
    "CorrelationField",
    "SpanDefinition",
    "TraceExporter",
    "LogCorrelationConfig",
]
