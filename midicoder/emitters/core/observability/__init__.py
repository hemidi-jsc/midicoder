# coding: utf-8
"""
CP15: Observability Stack Generator.

Cung cấp:
- models: MetricType, LogLevel, TracePropagationFormat, MetricProfile, StructuredLogConfig, TraceConfig
- parser: ObservabilityParser
- emitters: FastAPIObservabilityEmitter, NestJSObservabilityEmitter, AngularObservabilityEmitter, ReactObservabilityEmitter
- engine: MetricRegistry, StructuredLogger, TraceContext
"""

from midicoder.emitters.core.observability.models import (
    LogLevel,
    MetricProfile,
    MetricType,
    StructuredLogConfig,
    TraceConfig,
    TracePropagationFormat,
)
from midicoder.emitters.core.observability.parser import ObservabilityParser
from midicoder.emitters.core.observability.metrics import MetricRegistry
from midicoder.emitters.core.observability.logging import StructuredLogger
from midicoder.emitters.core.observability.tracing import TraceContext
from midicoder.emitters.core.observability.fastapi import FastAPIObservabilityEmitter
from midicoder.emitters.core.observability.nestjs import NestJSObservabilityEmitter
from midicoder.emitters.core.observability.angular import AngularObservabilityEmitter
from midicoder.emitters.core.observability.react import ReactObservabilityEmitter

__all__ = [
    # Models
    "MetricType",
    "LogLevel",
    "TracePropagationFormat",
    "MetricProfile",
    "StructuredLogConfig",
    "TraceConfig",
    # Parser
    "ObservabilityParser",
    # Engine
    "MetricRegistry",
    "StructuredLogger",
    "TraceContext",
    # Emitters
    "FastAPIObservabilityEmitter",
    "NestJSObservabilityEmitter",
    "AngularObservabilityEmitter",
    "ReactObservabilityEmitter",
]
