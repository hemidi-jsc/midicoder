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
