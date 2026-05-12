# coding: utf-8
"""
Mô-đun models cho Observability Stack Generator (CP15).

Định nghĩa các dataclass và enum biểu diễn:
- MetricType: Loại metric (counter/gauge/histogram)
- LogLevel: Mức độ log
- TracePropagationFormat: Định dạng propagation cho distributed tracing
- MetricProfile: Profile cho metric configuration
- StructuredLogConfig: Configuration cho structured logging
- TraceConfig: Configuration cho distributed tracing

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class MetricType(str, Enum):
    """Loại metric."""
    COUNTER = "counter"        # Chỉ tăng, không giảm
    GAUGE = "gauge"            # Có thể tăng giảm
    HISTOGRAM = "histogram"    # Phân phối giá trị


class LogLevel(str, Enum):
    """Mức độ log."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TracePropagationFormat(str, Enum):
    """Định dạng propagation cho distributed tracing."""
    W3C_TRACE_CONTEXT = "w3c_trace_context"
    B3 = "b3"
    NONE = "none"


# ===========================================================================
# MetricProfile
# ===========================================================================


@dataclass
class MetricProfile:
    """Profile cho metric — định nghĩa cách thu thập và lưu trữ metric.

    Attributes:
        name: Tên metric (bắt buộc, không rỗng)
        metric_type: Loại metric (counter/gauge/histogram)
        unit: Đơn vị (seconds, bytes, count...)
        labels: Labels để group/filter
        retention_days: Số ngày lưu trữ (bắt buộc >= 1)
        description: Mô tả metric

    Obligation: retention_days >= 1 (metric retention)
    """
    name: str
    metric_type: MetricType = MetricType.COUNTER
    unit: str = "count"
    labels: dict = field(default_factory=dict)
    retention_days: int = 30
    description: str = ""

    def __post_init__(self) -> None:
        """Validate metric profile sau khi khởi tạo."""
        # Tên metric không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP15_EMPTY_METRIC_NAME,
                field="name"
            )
        # Số ngày lưu trữ phải >= 1
        if self.retention_days < 1:
            EM.raise_error(
                ErrorCode.CP15_METRIC_RETENTION_INVALID,
                retention_days=self.retention_days
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MetricProfile sang dict format."""
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "unit": self.unit,
            "labels": self.labels,
            "retention_days": self.retention_days,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetricProfile":
        """Tạo MetricProfile từ dict."""
        return cls(
            name=data.get("name", ""),
            metric_type=MetricType(data.get("metric_type", "counter")),
            unit=data.get("unit", "count"),
            labels=data.get("labels", {}),
            retention_days=data.get("retention_days", 30),
            description=data.get("description", ""),
        )


# ===========================================================================
# StructuredLogConfig
# ===========================================================================


@dataclass
class StructuredLogConfig:
    """Configuration cho structured logging.

    Attributes:
        service_name: Tên service phát log
        log_level: Mức độ log tối thiểu
        include_trace_id: Có include trace_id không
        include_span_id: Có include span_id không
        output_format: Format output ("json" hay "text")
        fields: Fields bổ sung để include trong mọi log entry

    Obligation: immutable hash cho mỗi log entry
    """
    service_name: str = "midicoder"
    log_level: LogLevel = LogLevel.INFO
    include_trace_id: bool = True
    include_span_id: bool = True
    output_format: str = "json"
    fields: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate structured log config sau khi khởi tạo."""
        # Output format phải là "json" hoặc "text"
        if self.output_format not in ("json", "text"):
            EM.raise_error(
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                output_format=self.output_format,
                valid_formats=["json", "text"]
            )

    def compute_entry_hash(self, message: str, extra: dict | None = None) -> str:
        """
        Tính toán SHA-256 hash cho một log entry (immutable hash).

        Args:
            message: Nội dung log message
            extra: Dữ liệu bổ sung

        Returns:
            SHA-256 hash string
        """
        data = {
            "service_name": self.service_name,
            "log_level": self.log_level.value,
            "message": message,
            "include_trace_id": self.include_trace_id,
            "include_span_id": self.include_span_id,
            "extra": extra or {},
            "fields": self.fields,
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển StructuredLogConfig sang dict format."""
        return {
            "service_name": self.service_name,
            "log_level": self.log_level.value,
            "include_trace_id": self.include_trace_id,
            "include_span_id": self.include_span_id,
            "output_format": self.output_format,
            "fields": self.fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredLogConfig":
        """Tạo StructuredLogConfig từ dict."""
        return cls(
            service_name=data.get("service_name", "midicoder"),
            log_level=LogLevel(data.get("log_level", "INFO")),
            include_trace_id=data.get("include_trace_id", True),
            include_span_id=data.get("include_span_id", True),
            output_format=data.get("output_format", "json"),
            fields=data.get("fields", {}),
        )


# ===========================================================================
# TraceConfig
# ===========================================================================


@dataclass
class TraceConfig:
    """Configuration cho distributed tracing.

    Attributes:
        service_name: Tên service
        propagation_format: Format propagation (W3C/B3/NONE)
        max_spans: Số span tối đa trong một trace
        sample_rate: Tỷ lệ sampling (0.0 - 1.0)
        attributes: Attributes bổ sung cho mọi span
    """
    service_name: str = "midicoder"
    propagation_format: TracePropagationFormat = TracePropagationFormat.W3C_TRACE_CONTEXT
    max_spans: int = 100
    sample_rate: float = 1.0
    attributes: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate trace config sau khi khởi tạo."""
        # Số span tối đa phải >= 1
        if self.max_spans < 1:
            EM.raise_error(
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                field="max_spans",
                value=self.max_spans
            )
        # Tỷ lệ sampling phải trong khoảng [0.0, 1.0]
        if not (0.0 <= self.sample_rate <= 1.0):
            EM.raise_error(
                ErrorCode.CP15_INVALID_TRACE_FORMAT,
                sample_rate=self.sample_rate
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TraceConfig sang dict format."""
        return {
            "service_name": self.service_name,
            "propagation_format": self.propagation_format.value,
            "max_spans": self.max_spans,
            "sample_rate": self.sample_rate,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceConfig":
        """Tạo TraceConfig từ dict."""
        return cls(
            service_name=data.get("service_name", "midicoder"),
            propagation_format=TracePropagationFormat(
                data.get("propagation_format", "w3c_trace_context")
            ),
            max_spans=data.get("max_spans", 100),
            sample_rate=data.get("sample_rate", 1.0),
            attributes=data.get("attributes", {}),
        )


# ===========================================================================
# OpenTelemetry
# ===========================================================================


class OTLPExportProtocol(str, Enum):
    """
    Protocol cho OTLP exporter.

    - grpc: gRPC (nhanh, binary, streaming)
    - http_json: HTTP/JSON (compat tốt, dễ debug)
    - http_protobuf: HTTP/Protobuf (nhanh hơn JSON, nhẹ hơn gRPC)
    """
    GRPC = "grpc"
    HTTP_JSON = "http_json"
    HTTP_PROTOBUF = "http_protobuf"


class SamplerType(str, Enum):
    """
    Loại sampler cho OpenTelemetry.

    - always_on: Sample 100% traces
    - always_off: Sample 0% traces
    - traceid_ratio_based: Sample theo tỷ lệ dựa trên trace_id
    - parent_based: Theo parent span, tự sample nếu root
    """
    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    TRACEID_RATIO_BASED = "traceid_ratio_based"
    PARENT_BASED = "parent_based"


class SpanKind(str, Enum):
    """
    Loại span trong distributed tracing.

    - internal: Internal operation trong service
    - server: Server xử lý incoming request
    - client: Client gửi outgoing request
    - producer: Producer gửi message
    - consumer: Consumer nhận message
    """
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class OTelExporterConfig:
    """
    Configuration cho OpenTelemetry OTLP exporter.

    Export traces, metrics, và logs đến OTLP endpoint.

    Attributes:
        endpoint: OTLP endpoint (vd: "http://otel-collector:4317")
        protocol: Protocol (grpc, http_json, http_protobuf)
        timeout_ms: Timeout cho export request (milliseconds)
        headers: Custom headers (vd: API key)
        compression: Compression (gzip, none)
        batch_size: Số spans trong 1 batch export
        batch_timeout_ms: Timeout trước khi flush batch
        retry_on_failure: Có retry khi export thất bại không
        max_queue_size: Queue size tối đa cho spans chờ export
        description: Mô tả exporter
    """
    endpoint: str = "http://localhost:4317"
    protocol: OTLPExportProtocol = OTLPExportProtocol.GRPC
    timeout_ms: int = 10000
    headers: dict = field(default_factory=dict)
    compression: str = "none"
    batch_size: int = 512
    batch_timeout_ms: int = 5000
    retry_on_failure: bool = True
    max_queue_size: int = 2048
    description: str = ""

    def __post_init__(self) -> None:
        """Validate OTLP exporter config sau khi khởi tạo."""
        if not self.endpoint or not self.endpoint.strip():
            EM.raise_error(
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                field="endpoint",
                reason="OTLP endpoint không được để trống"
            )
        if self.timeout_ms < 1:
            self.timeout_ms = 10000
        if self.batch_size < 1:
            self.batch_size = 512

    def to_dict(self) -> dict[str, Any]:
        """Chuyển OTLP exporter config sang dict format."""
        return {
            "endpoint": self.endpoint,
            "protocol": self.protocol.value,
            "timeout_ms": self.timeout_ms,
            "headers": self.headers,
            "compression": self.compression,
            "batch_size": self.batch_size,
            "batch_timeout_ms": self.batch_timeout_ms,
            "retry_on_failure": self.retry_on_failure,
            "max_queue_size": self.max_queue_size,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OTelExporterConfig":
        """Tạo OTelExporterConfig từ dict."""
        return cls(
            endpoint=data.get("endpoint", "http://localhost:4317"),
            protocol=OTLPExportProtocol(data.get("protocol", "grpc")),
            timeout_ms=data.get("timeout_ms", 10000),
            headers=data.get("headers", {}),
            compression=data.get("compression", "none"),
            batch_size=data.get("batch_size", 512),
            batch_timeout_ms=data.get("batch_timeout_ms", 5000),
            retry_on_failure=data.get("retry_on_failure", True),
            max_queue_size=data.get("max_queue_size", 2048),
            description=data.get("description", ""),
        )


@dataclass
class OpenTelemetryConfig:
    """
    Configuration cho OpenTelemetry SDK.

    Unified config cho traces, metrics, và logs qua OpenTelemetry.

    Attributes:
        service_name: Tên service (resource attribute)
        exporter: OTLP exporter config
        sampler_type: Loại sampler
        sampler_rate: Tỷ lệ sampling (0.0 - 1.0)
        resource_attributes: Resource attributes bổ sung
        enable_traces: Có enable trace collection không
        enable_metrics: Có enable metric collection không
        enable_logs: Có enable log collection không
        description: Mô tả config
    """
    service_name: str = "midicoder"
    exporter: OTelExporterConfig = field(default_factory=OTelExporterConfig)
    sampler_type: SamplerType = SamplerType.TRACEID_RATIO_BASED
    sampler_rate: float = 1.0
    resource_attributes: dict = field(default_factory=dict)
    enable_traces: bool = True
    enable_metrics: bool = True
    enable_logs: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate OpenTelemetry config sau khi khởi tạo."""
        if not self.service_name or not self.service_name.strip():
            EM.raise_error(
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                field="service_name",
                reason="Service name không được để trống"
            )
        if not (0.0 <= self.sampler_rate <= 1.0):
            EM.raise_error(
                ErrorCode.CP15_INVALID_TRACE_FORMAT,
                sample_rate=self.sampler_rate
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển OpenTelemetry config sang dict format."""
        return {
            "service_name": self.service_name,
            "exporter": self.exporter.to_dict(),
            "sampler_type": self.sampler_type.value,
            "sampler_rate": self.sampler_rate,
            "resource_attributes": self.resource_attributes,
            "enable_traces": self.enable_traces,
            "enable_metrics": self.enable_metrics,
            "enable_logs": self.enable_logs,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpenTelemetryConfig":
        """Tạo OpenTelemetryConfig từ dict."""
        exp_data = data.get("exporter")
        return cls(
            service_name=data.get("service_name", "midicoder"),
            exporter=OTelExporterConfig.from_dict(exp_data) if exp_data else OTelExporterConfig(),
            sampler_type=SamplerType(data.get("sampler_type", "traceid_ratio_based")),
            sampler_rate=data.get("sampler_rate", 1.0),
            resource_attributes=data.get("resource_attributes", {}),
            enable_traces=data.get("enable_traces", True),
            enable_metrics=data.get("enable_metrics", True),
            enable_logs=data.get("enable_logs", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# Log Shipping
# ===========================================================================


class LogDestinationType(str, Enum):
    """
    Loại log destination.

    - loki: Grafana Loki
    - cloudwatch: AWS CloudWatch Logs
    - datadog: Datadog Logs
    - elasticsearch: Elasticsearch/OpenSearch
    - splunk: Splunk HEC
    - stdout: Standard output (development)
    - file: File system
    """
    LOKI = "loki"
    CLOUDWATCH = "cloudwatch"
    DATADOG = "datadog"
    ELASTICSEARCH = "elasticsearch"
    SPLUNK = "splunk"
    STDOUT = "stdout"
    FILE = "file"


@dataclass
class LogShippingDestination:
    """
    Destination cho log shipping — nơi logs được ship đến.

    Attributes:
        destination_type: Loại destination (loki, cloudwatch, datadog, elasticsearch, ...)
        endpoint: Endpoint URL (vd: "http://loki:3100/loki/api/v1/push")
        auth_token: Auth token/API key (set ở runtime)
        flush_interval_ms: Interval flush logs (milliseconds)
        max_batch_size: Số logs trong 1 batch
        compression: Compression (gzip, none)
        labels: Labels/tags cho logs (vd: {"app": "midicoder", "env": "prod"})
        filter_pattern: Log filter pattern (vd: "level >= warning")
        description: Mô tả destination
    """
    destination_type: LogDestinationType
    endpoint: str = ""
    auth_token: str = ""
    flush_interval_ms: int = 5000
    max_batch_size: int = 1000
    compression: str = "gzip"
    labels: dict = field(default_factory=dict)
    filter_pattern: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate log shipping destination sau khi khởi tạo."""
        if self.flush_interval_ms < 1:
            self.flush_interval_ms = 5000
        if self.max_batch_size < 1:
            self.max_batch_size = 1000

    def to_dict(self) -> dict[str, Any]:
        """Chuyển log destination sang dict format."""
        return {
            "destination_type": self.destination_type.value,
            "endpoint": self.endpoint,
            "flush_interval_ms": self.flush_interval_ms,
            "max_batch_size": self.max_batch_size,
            "compression": self.compression,
            "labels": self.labels,
            "filter_pattern": self.filter_pattern,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogShippingDestination":
        """Tạo LogShippingDestination từ dict."""
        return cls(
            destination_type=LogDestinationType(data.get("destination_type", "loki")),
            endpoint=data.get("endpoint", ""),
            auth_token=data.get("auth_token", ""),
            flush_interval_ms=data.get("flush_interval_ms", 5000),
            max_batch_size=data.get("max_batch_size", 1000),
            compression=data.get("compression", "gzip"),
            labels=data.get("labels", {}),
            filter_pattern=data.get("filter_pattern", ""),
            description=data.get("description", ""),
        )


@dataclass
class LogShippingConfig:
    """
    Configuration cho log shipping — ship logs đến external destinations.

    Attributes:
        enabled: Có enable log shipping không
        destinations: Danh sách log destinations
        async_shipping: Có ship logs async không (không block main thread)
        max_queue_size: Queue size tối đa cho logs chờ ship
        drop_on_overflow: Có drop logs khi queue overflow không
        description: Mô tả log shipping config
    """
    enabled: bool = True
    destinations: list[LogShippingDestination] = field(default_factory=list)
    async_shipping: bool = True
    max_queue_size: int = 10000
    drop_on_overflow: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate log shipping config sau khi khởi tạo."""
        if self.max_queue_size < 1:
            self.max_queue_size = 10000

    def to_dict(self) -> dict[str, Any]:
        """Chuyển log shipping config sang dict format."""
        return {
            "enabled": self.enabled,
            "destinations": [d.to_dict() for d in self.destinations],
            "async_shipping": self.async_shipping,
            "max_queue_size": self.max_queue_size,
            "drop_on_overflow": self.drop_on_overflow,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogShippingConfig":
        """Tạo LogShippingConfig từ dict."""
        return cls(
            enabled=data.get("enabled", True),
            destinations=[LogShippingDestination.from_dict(d) for d in data.get("destinations", [])],
            async_shipping=data.get("async_shipping", True),
            max_queue_size=data.get("max_queue_size", 10000),
            drop_on_overflow=data.get("drop_on_overflow", False),
            description=data.get("description", ""),
        )
