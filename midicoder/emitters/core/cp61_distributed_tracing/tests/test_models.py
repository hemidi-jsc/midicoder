# coding: utf-8
"""Tests cho CP61 — Distributed Tracing & Correlation ID models."""

import pytest
from midicoder.emitters.core.cp61_distributed_tracing.models import (
    CorrelationField,
    CorrelationFormat,
    CorrelationHeader,
    ExporterType,
    LogCorrelationConfig,
    LogLevel,
    PropagationFormat,
    SamplerType,
    SpanDefinition,
    SpanKind,
    TraceConfig,
    TraceExporter,
)


# =============================================================================
# Enums
# =============================================================================

class TestSamplerType:
    def test_enum_values(self):
        assert SamplerType.ALWAYS_ON.value == "always_on"
        assert SamplerType.ALWAYS_OFF.value == "always_off"
        assert SamplerType.PROBABILISTIC.value == "probabilistic"
        assert SamplerType.RATE_LIMITING.value == "ratelimiting"

    def test_enum_count(self):
        assert len(SamplerType) == 4


class TestExporterType:
    def test_enum_values(self):
        assert ExporterType.JAEGER.value == "jaeger"
        assert ExporterType.ZIPKIN.value == "zipkin"
        assert ExporterType.OTEL.value == "otel"
        assert ExporterType.DATADOG.value == "datadog"

    def test_enum_count(self):
        assert len(ExporterType) == 4


class TestPropagationFormat:
    def test_enum_values(self):
        assert PropagationFormat.W3C.value == "w3c"
        assert PropagationFormat.B3.value == "b3"
        assert PropagationFormat.JAEGER.value == "jaeger"

    def test_enum_count(self):
        assert len(PropagationFormat) == 3


class TestSpanKind:
    def test_enum_values(self):
        assert SpanKind.SERVER.value == "server"
        assert SpanKind.CLIENT.value == "client"
        assert SpanKind.PRODUCER.value == "producer"
        assert SpanKind.CONSUMER.value == "consumer"

    def test_enum_count(self):
        assert len(SpanKind) == 4


class TestCorrelationFormat:
    def test_enum_values(self):
        assert CorrelationFormat.UUID4.value == "uuid4"
        assert CorrelationFormat.SNOWFLAKE.value == "snowflake"
        assert CorrelationFormat.TIMESTAMP.value == "timestamp"

    def test_enum_count(self):
        assert len(CorrelationFormat) == 3


class TestCorrelationHeader:
    def test_enum_values(self):
        assert CorrelationHeader.X_CORRELATION_ID.value == "X-Correlation-ID"
        assert CorrelationHeader.X_REQUEST_ID.value == "X-Request-ID"

    def test_enum_count(self):
        assert len(CorrelationHeader) == 2


class TestLogLevel:
    def test_enum_values(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"

    def test_enum_count(self):
        assert len(LogLevel) == 4


# =============================================================================
# TraceConfig
# =============================================================================

class TestTraceConfig:
    def test_creation_with_defaults(self):
        tc = TraceConfig(config_id="tc-1")
        assert tc.name == ""
        assert tc.sampler == SamplerType.ALWAYS_ON
        assert tc.sample_rate == 1.0
        assert tc.exporter == ExporterType.OTEL
        assert tc.propagation_format == PropagationFormat.W3C
        assert tc.service_name == ""

    def test_creation_with_all_fields(self):
        tc = TraceConfig(
            config_id="tc-2", name="jaeger-trace",
            sampler=SamplerType.PROBABILISTIC, sample_rate=0.5,
            exporter=ExporterType.JAEGER,
            propagation_format=PropagationFormat.B3,
            service_name="order-service",
        )
        assert tc.sampler == SamplerType.PROBABILISTIC
        assert tc.sample_rate == 0.5
        assert tc.exporter == ExporterType.JAEGER

    def test_to_dict(self):
        tc = TraceConfig(config_id="tc-3", name="test", service_name="svc")
        d = tc.to_dict()
        assert d["config_id"] == "tc-3"
        assert d["sampler"] == "always_on"
        assert d["sample_rate"] == 1.0

    def test_from_dict(self):
        data = {
            "config_id": "tc-4", "name": "from-dict",
            "sampler": "probabilistic", "sample_rate": 0.25,
            "exporter": "datadog", "propagation_format": "jaeger",
        }
        tc = TraceConfig.from_dict(data)
        assert tc.sampler == SamplerType.PROBABILISTIC
        assert tc.sample_rate == 0.25
        assert tc.exporter == ExporterType.DATADOG
        assert tc.propagation_format == PropagationFormat.JAEGER

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            TraceConfig(config_id="")

    def test_validation_error_sample_rate_negative(self):
        with pytest.raises(Exception):
            TraceConfig(config_id="tc-5", sample_rate=-0.1)

    def test_validation_error_sample_rate_over_one(self):
        with pytest.raises(Exception):
            TraceConfig(config_id="tc-6", sample_rate=1.5)

    def test_roundtrip(self):
        original = TraceConfig(
            config_id="rt-tc", name="rt", sampler=SamplerType.RATE_LIMITING,
            sample_rate=0.75, exporter=ExporterType.ZIPKIN,
        )
        d = original.to_dict()
        restored = TraceConfig.from_dict(d)
        assert restored.config_id == original.config_id
        assert restored.sampler == original.sampler
        assert restored.sample_rate == original.sample_rate
        assert restored.exporter == original.exporter


# =============================================================================
# CorrelationField
# =============================================================================

class TestCorrelationField:
    def test_creation_with_defaults(self):
        cf = CorrelationField(field_id="cf-1")
        assert cf.name == ""
        assert cf.header_name == CorrelationHeader.X_CORRELATION_ID
        assert cf.propagate is True
        assert cf.mask_sensitive is False
        assert cf.format == CorrelationFormat.UUID4

    def test_creation_with_all_fields(self):
        cf = CorrelationField(
            field_id="cf-2", name="req-id",
            header_name=CorrelationHeader.X_REQUEST_ID,
            propagate=False, mask_sensitive=True,
            format=CorrelationFormat.SNOWFLAKE,
        )
        assert cf.header_name == CorrelationHeader.X_REQUEST_ID
        assert cf.format == CorrelationFormat.SNOWFLAKE

    def test_to_dict(self):
        cf = CorrelationField(field_id="cf-3", name="trace-header")
        d = cf.to_dict()
        assert d["field_id"] == "cf-3"
        assert d["propagate"] is True
        assert d["format"] == "uuid4"

    def test_from_dict(self):
        data = {
            "field_id": "cf-4", "name": "x-req",
            "header_name": "X-Request-ID", "propagate": False,
            "mask_sensitive": True, "format": "timestamp",
        }
        cf = CorrelationField.from_dict(data)
        assert cf.header_name == CorrelationHeader.X_REQUEST_ID
        assert cf.propagate is False
        assert cf.format == CorrelationFormat.TIMESTAMP

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            CorrelationField(field_id="")

    def test_roundtrip(self):
        original = CorrelationField(
            field_id="rt-cf", name="rt", propagate=False, mask_sensitive=True,
        )
        d = original.to_dict()
        restored = CorrelationField.from_dict(d)
        assert restored.field_id == original.field_id
        assert restored.propagate == original.propagate
        assert restored.mask_sensitive == original.mask_sensitive


# =============================================================================
# SpanDefinition
# =============================================================================

class TestSpanDefinition:
    def test_creation_with_defaults(self):
        sd = SpanDefinition(span_id="sd-1")
        assert sd.operation_name == ""
        assert sd.kind == SpanKind.SERVER
        assert sd.timeout_ms == 30000
        assert sd.links_to == []

    def test_creation_with_all_fields(self):
        sd = SpanDefinition(
            span_id="sd-2", operation_name="POST /orders",
            kind=SpanKind.CLIENT, attributes={"http.method": "POST"},
            links_to=["sd-1"], timeout_ms=5000,
        )
        assert sd.kind == SpanKind.CLIENT
        assert sd.timeout_ms == 5000
        assert "sd-1" in sd.links_to

    def test_to_dict(self):
        sd = SpanDefinition(span_id="sd-3", operation_name="GET /users", kind=SpanKind.SERVER)
        d = sd.to_dict()
        assert d["span_id"] == "sd-3"
        assert d["kind"] == "server"
        assert d["timeout_ms"] == 30000

    def test_from_dict(self):
        data = {
            "span_id": "sd-4", "operation_name": "publish-order",
            "kind": "producer", "timeout_ms": 10000,
        }
        sd = SpanDefinition.from_dict(data)
        assert sd.kind == SpanKind.PRODUCER
        assert sd.timeout_ms == 10000

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            SpanDefinition(span_id="")

    def test_validation_error_zero_timeout(self):
        with pytest.raises(Exception):
            SpanDefinition(span_id="sd-5", timeout_ms=0)

    def test_roundtrip(self):
        original = SpanDefinition(
            span_id="rt-sd", operation_name="rt-op", kind=SpanKind.CONSUMER,
            attributes={"k": "v"}, timeout_ms=15000,
        )
        d = original.to_dict()
        restored = SpanDefinition.from_dict(d)
        assert restored.span_id == original.span_id
        assert restored.kind == original.kind
        assert restored.timeout_ms == original.timeout_ms


# =============================================================================
# TraceExporter
# =============================================================================

class TestTraceExporter:
    def test_creation_with_defaults(self):
        te = TraceExporter(exporter_id="te-1")
        assert te.name == ""
        assert te.type == ExporterType.OTEL
        assert te.endpoint == ""
        assert te.batching_interval == 5
        assert te.max_queue_size == 2048

    def test_creation_with_all_fields(self):
        te = TraceExporter(
            exporter_id="te-2", name="jaeger-exporter",
            type=ExporterType.JAEGER, endpoint="http://jaeger:14268/api/traces",
            batching_interval=10, max_queue_size=4096,
        )
        assert te.type == ExporterType.JAEGER
        assert te.batching_interval == 10

    def test_to_dict(self):
        te = TraceExporter(exporter_id="te-3", type=ExporterType.ZIPKIN)
        d = te.to_dict()
        assert d["type"] == "zipkin"
        assert d["max_queue_size"] == 2048

    def test_from_dict(self):
        data = {
            "exporter_id": "te-4", "name": "dd",
            "type": "datadog", "endpoint": "http://dd:8126",
            "batching_interval": 3, "max_queue_size": 1024,
        }
        te = TraceExporter.from_dict(data)
        assert te.type == ExporterType.DATADOG
        assert te.max_queue_size == 1024

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            TraceExporter(exporter_id="")

    def test_validation_error_zero_batching(self):
        with pytest.raises(Exception):
            TraceExporter(exporter_id="te-5", batching_interval=0)

    def test_validation_error_zero_queue(self):
        with pytest.raises(Exception):
            TraceExporter(exporter_id="te-6", max_queue_size=0)

    def test_roundtrip(self):
        original = TraceExporter(
            exporter_id="rt-te", name="rt", type=ExporterType.JAEGER,
            endpoint="http://j:14268", batching_interval=7,
        )
        d = original.to_dict()
        restored = TraceExporter.from_dict(d)
        assert restored.exporter_id == original.exporter_id
        assert restored.type == original.type
        assert restored.batching_interval == original.batching_interval


# =============================================================================
# LogCorrelationConfig
# =============================================================================

class TestLogCorrelationConfig:
    def test_creation_with_defaults(self):
        lc = LogCorrelationConfig(config_id="lc-1")
        assert lc.trace_id_field == "trace_id"
        assert lc.span_id_field == "span_id"
        assert lc.correlation_id_field == "correlation_id"
        assert lc.inject_into_logs is True
        assert lc.log_level_for_trace == LogLevel.DEBUG

    def test_creation_with_all_fields(self):
        lc = LogCorrelationConfig(
            config_id="lc-2",
            trace_id_field="tid", span_id_field="sid",
            correlation_id_field="cid", inject_into_logs=False,
            log_level_for_trace=LogLevel.INFO,
        )
        assert lc.trace_id_field == "tid"
        assert lc.inject_into_logs is False
        assert lc.log_level_for_trace == LogLevel.INFO

    def test_to_dict(self):
        lc = LogCorrelationConfig(config_id="lc-3", log_level_for_trace=LogLevel.ERROR)
        d = lc.to_dict()
        assert d["config_id"] == "lc-3"
        assert d["log_level_for_trace"] == "ERROR"
        assert d["inject_into_logs"] is True

    def test_from_dict(self):
        data = {
            "config_id": "lc-4", "trace_id_field": "trace",
            "inject_into_logs": False, "log_level_for_trace": "WARNING",
        }
        lc = LogCorrelationConfig.from_dict(data)
        assert lc.trace_id_field == "trace"
        assert lc.inject_into_logs is False
        assert lc.log_level_for_trace == LogLevel.WARNING

    def test_validation_error_empty_id(self):
        with pytest.raises(Exception):
            LogCorrelationConfig(config_id="")

    def test_roundtrip(self):
        original = LogCorrelationConfig(
            config_id="rt-lc", inject_into_logs=False, log_level_for_trace=LogLevel.INFO,
        )
        d = original.to_dict()
        restored = LogCorrelationConfig.from_dict(d)
        assert restored.config_id == original.config_id
        assert restored.inject_into_logs == original.inject_into_logs
        assert restored.log_level_for_trace == original.log_level_for_trace
