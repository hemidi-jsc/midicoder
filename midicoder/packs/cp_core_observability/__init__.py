# coding: utf-8
"""
CP15: Observability Stack Generator.

Cung cấp:
- models: MetricType, LogLevel, TracePropagationFormat, MetricProfile, StructuredLogConfig, TraceConfig
- models: OpenTelemetryConfig, OTelExporterConfig, OTLPExportProtocol, SamplerType, SpanKind
- models: LogShippingConfig, LogShippingDestination, LogDestinationType
- parser: ObservabilityParser
- engine: MetricRegistry, StructuredLogger, TraceContext
- emitters: FastAPIObservabilityEmitter, NestJSObservabilityEmitter, AngularObservabilityEmitter, ReactObservabilityEmitter
"""

from midicoder.packs.cp_core_observability.models import (
    # CP61 merged exports
    ExporterType,
    CorrelationFormat,
    CorrelationHeader,
    CorrelationField,
    SpanDefinition,
    TraceExporter,
    LogCorrelationConfig,  #
    LogLevel,
    LogDestinationType,
    LogShippingConfig,
    LogShippingDestination,
    MetricProfile,
    MetricType,
    OpenTelemetryConfig,
    OTelExporterConfig,
    OTLPExportProtocol,
    SamplerType,
    SpanKind,
    StructuredLogConfig,
    TraceConfig,
    TracePropagationFormat,
)
from midicoder.packs.cp_core_observability.parser import ObservabilityParser
from midicoder.packs.cp_core_observability.metrics import MetricRegistry
from midicoder.packs.cp_core_observability.logging import StructuredLogger
from midicoder.packs.cp_core_observability.tracing import TraceContext
from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter
from midicoder.packs.cp_core_observability.nestjs import NestJSObservabilityEmitter
from midicoder.packs.cp_core_observability.angular import AngularObservabilityEmitter
from midicoder.packs.cp_core_observability.react import ReactObservabilityEmitter

__all__ = [
    # Enums
    "MetricType",
    "LogLevel",
    "TracePropagationFormat",
    "OTLPExportProtocol",
    "SamplerType",
    "SpanKind",
    "LogDestinationType",
    # Models
    "MetricProfile",
    "StructuredLogConfig",
    "TraceConfig",
    "OpenTelemetryConfig",
    "OTelExporterConfig",
    "LogShippingConfig",
    "LogShippingDestination",
    # Parser
    "ObservabilityParser",
    # Engine
    "MetricRegistry",
    "StructuredLogger",
    # CP61 exports
    "ExporterType",
    "CorrelationFormat",
    "CorrelationHeader",
    "CorrelationField",
    "SpanDefinition",
    "TraceExporter",
    "LogCorrelationConfig",
    "TraceContext",
    # Emitters
    "FastAPIObservabilityEmitter",
    "NestJSObservabilityEmitter",
    "AngularObservabilityEmitter",
    "ReactObservabilityEmitter",
]
