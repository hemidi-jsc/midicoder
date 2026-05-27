# coding: utf-8
"""
Mô-đun parser cho CP61 — Distributed Tracing & Correlation ID.

Parse DSL dict (từ YAML/tracing config) sang TracingIR — Intermediate Representation
cho trace configurations, correlation fields, span definitions, exporters,
và log correlation settings.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp61_distributed_tracing.models import (
    CorrelationField,
    ExporterType,
    LogCorrelationConfig,
    PropagationFormat,
    SamplerType,
    SpanDefinition,
    TraceConfig,
    TraceExporter,
)


@dataclass
class TracingIR:
    """Intermediate Representation cho CP61.

    Gom tập tất cả cấu hình distributed tracing từ DSL, bao gồm
    trace configs, correlation fields, span definitions,
    exporter configs, và log correlation settings.

    Attributes:
        configs: Danh sách trace configurations
        correlation_fields: Danh sách correlation field definitions
        spans: Danh sách span definitions
        exporters: Danh sách trace exporter configs
        log_correlation: Danh sách log correlation configs
    """
    configs: list[TraceConfig] = field(default_factory=list)
    correlation_fields: list[CorrelationField] = field(default_factory=list)
    spans: list[SpanDefinition] = field(default_factory=list)
    exporters: list[TraceExporter] = field(default_factory=list)
    log_correlation: list[LogCorrelationConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TracingIR sang dict."""
        return {
            "configs": [c.to_dict() for c in self.configs],
            "correlation_fields": [f.to_dict() for f in self.correlation_fields],
            "spans": [s.to_dict() for s in self.spans],
            "exporters": [e.to_dict() for e in self.exporters],
            "log_correlation": [l.to_dict() for l in self.log_correlation],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TracingIR":
        """Tạo TracingIR từ dict."""
        configs = [TraceConfig.from_dict(c) for c in data.get("configs", data.get("trace_configs", []))]
        fields = [CorrelationField.from_dict(f) for f in data.get("correlation_fields", data.get("correlation", []))]
        spans = [SpanDefinition.from_dict(s) for s in data.get("spans", data.get("span_definitions", []))]
        exporters = [TraceExporter.from_dict(e) for e in data.get("exporters", data.get("trace_exporters", []))]
        log_corr = [LogCorrelationConfig.from_dict(l) for l in data.get("log_correlation", data.get("log_trace_correlation", []))]

        return cls(
            configs=configs,
            correlation_fields=fields,
            spans=spans,
            exporters=exporters,
            log_correlation=log_corr,
        )


def parse_trace_configs(data: dict[str, Any]) -> list[TraceConfig]:
    """Parse danh sách trace configurations từ DSL dict.

    Args:
        data: DSL dict với key 'configs' hoặc 'trace_configs'

    Returns:
        Danh sách TraceConfig
    """
    raw = data.get("configs", data.get("trace_configs", []))
    return [
        TraceConfig.from_dict(c) if isinstance(c, dict) else TraceConfig(
            config_id=c if isinstance(c, str) else "",
        )
        for c in raw
    ]


def parse_correlation_fields(data: dict[str, Any]) -> list[CorrelationField]:
    """Parse danh sách correlation fields từ DSL dict.

    Args:
        data: DSL dict với key 'correlation_fields' hoặc 'correlation'

    Returns:
        Danh sách CorrelationField
    """
    raw = data.get("correlation_fields", data.get("correlation", []))
    return [
        CorrelationField.from_dict(f) if isinstance(f, dict) else CorrelationField(
            field_id=f if isinstance(f, str) else "",
        )
        for f in raw
    ]


def parse_span_definitions(data: dict[str, Any]) -> list[SpanDefinition]:
    """Parse danh sách span definitions từ DSL dict.

    Args:
        data: DSL dict với key 'spans' hoặc 'span_definitions'

    Returns:
        Danh sách SpanDefinition
    """
    raw = data.get("spans", data.get("span_definitions", []))
    return [
        SpanDefinition.from_dict(s) if isinstance(s, dict) else SpanDefinition(
            span_id=s if isinstance(s, str) else "",
        )
        for s in raw
    ]


def parse_exporters(data: dict[str, Any]) -> list[TraceExporter]:
    """Parse danh sách trace exporters từ DSL dict.

    Args:
        data: DSL dict với key 'exporters' hoặc 'trace_exporters'

    Returns:
        Danh sách TraceExporter
    """
    raw = data.get("exporters", data.get("trace_exporters", []))
    return [
        TraceExporter.from_dict(e) if isinstance(e, dict) else TraceExporter(
            exporter_id=e if isinstance(e, str) else "",
        )
        for e in raw
    ]


def parse_log_correlation(data: dict[str, Any]) -> list[LogCorrelationConfig]:
    """Parse danh sách log correlation configs từ DSL dict.

    Args:
        data: DSL dict với key 'log_correlation' hoặc 'log_trace_correlation'

    Returns:
        Danh sách LogCorrelationConfig
    """
    raw = data.get("log_correlation", data.get("log_trace_correlation", []))
    return [
        LogCorrelationConfig.from_dict(l) if isinstance(l, dict) else LogCorrelationConfig(
            config_id=l if isinstance(l, str) else "",
        )
        for l in raw
    ]


def parse_to_ir(data: dict[str, Any]) -> TracingIR:
    """Parse DSL dict thành TracingIR.

    Args:
        data: DSL dict với configs, correlation_fields, spans, exporters, log_correlation

    Returns:
        TracingIR gom tập tất cả parsed data
    """
    return TracingIR(
        configs=parse_trace_configs(data),
        correlation_fields=parse_correlation_fields(data),
        spans=parse_span_definitions(data),
        exporters=parse_exporters(data),
        log_correlation=parse_log_correlation(data),
    )


__all__ = [
    "TracingIR",
    "parse_trace_configs",
    "parse_correlation_fields",
    "parse_span_definitions",
    "parse_exporters",
    "parse_log_correlation",
    "parse_to_ir",
]
