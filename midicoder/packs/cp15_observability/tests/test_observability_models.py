# coding: utf-8
"""
Test cases cho CP15 Observability Stack Generator models.

Kiểm tra:
- MetricType: Giá trị enum và membership
- LogLevel: Giá trị enum và membership
- TracePropagationFormat: Giá trị enum và membership
- MetricProfile: Tạo hợp lệ, tên rỗng → lỗi, retention < 1 → lỗi, to_dict/from_dict, defaults
- StructuredLogConfig: Tạo hợp lệ, format sai → lỗi, defaults, to_dict/from_dict
- TraceConfig: Tạo hợp lệ, max_spans < 1 → lỗi, sample_rate ra ngoài khoảng → lỗi, defaults, to_dict/from_dict
"""

import pytest

from midicoder.packs.cp15_observability.models import (
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
from midicoder.errors import ErrorCode, MidicoderError


# =============================================================================
# Enum Tests
# =============================================================================


class TestMetricType:
    """Test MetricType enum."""

    def test_counter_value(self):
        """Kiểm tra giá trị COUNTER."""
        assert MetricType.COUNTER.value == "counter"

    def test_gauge_value(self):
        """Kiểm tra giá trị GAUGE."""
        assert MetricType.GAUGE.value == "gauge"

    def test_histogram_value(self):
        """Kiểm tra giá trị HISTOGRAM."""
        assert MetricType.HISTOGRAM.value == "histogram"

    def test_total_count(self):
        """Kiểm tra tổng số loại metric = 3."""
        assert len(MetricType) == 3

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert MetricType.COUNTER == "counter"
        assert MetricType.GAUGE == "gauge"
        assert MetricType.HISTOGRAM == "histogram"


class TestLogLevel:
    """Test LogLevel enum."""

    def test_debug_value(self):
        """Kiểm tra giá trị DEBUG."""
        assert LogLevel.DEBUG.value == "DEBUG"

    def test_info_value(self):
        """Kiểm tra giá trị INFO."""
        assert LogLevel.INFO.value == "INFO"

    def test_warning_value(self):
        """Kiểm tra giá trị WARNING."""
        assert LogLevel.WARNING.value == "WARNING"

    def test_error_value(self):
        """Kiểm tra giá trị ERROR."""
        assert LogLevel.ERROR.value == "ERROR"

    def test_critical_value(self):
        """Kiểm tra giá trị CRITICAL."""
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_total_count(self):
        """Kiểm tra tổng số log levels = 5."""
        assert len(LogLevel) == 5


class TestTracePropagationFormat:
    """Test TracePropagationFormat enum."""

    def test_w3c_value(self):
        """Kiểm tra giá trị W3C_TRACE_CONTEXT."""
        assert TracePropagationFormat.W3C_TRACE_CONTEXT.value == "w3c_trace_context"

    def test_b3_value(self):
        """Kiểm tra giá trị B3."""
        assert TracePropagationFormat.B3.value == "b3"

    def test_none_value(self):
        """Kiểm tra giá trị NONE."""
        assert TracePropagationFormat.NONE.value == "none"

    def test_total_count(self):
        """Kiểm tra tổng số propagation formats = 3."""
        assert len(TracePropagationFormat) == 3


# =============================================================================
# MetricProfile Tests
# =============================================================================


class TestMetricProfile:
    """Test MetricProfile dataclass."""

    def test_create_valid_counter(self):
        """Kiểm tra tạo counter metric hợp lệ."""
        mp = MetricProfile(name="http_requests_total", metric_type=MetricType.COUNTER)
        assert mp.name == "http_requests_total"
        assert mp.metric_type == MetricType.COUNTER
        assert mp.unit == "count"
        assert mp.retention_days == 30

    def test_create_valid_gauge(self):
        """Kiểm tra tạo gauge metric hợp lệ."""
        mp = MetricProfile(
            name="memory_usage",
            metric_type=MetricType.GAUGE,
            unit="bytes",
            labels={"environment": "production"},
            retention_days=90,
            description="Theo dõi bộ nhớ",
        )
        assert mp.name == "memory_usage"
        assert mp.metric_type == MetricType.GAUGE
        assert mp.unit == "bytes"
        assert mp.labels == {"environment": "production"}
        assert mp.retention_days == 90
        assert mp.description == "Theo dõi bộ nhớ"

    def test_create_valid_histogram(self):
        """Kiểm tra tạo histogram metric hợp lệ."""
        mp = MetricProfile(
            name="request_latency",
            metric_type=MetricType.HISTOGRAM,
            unit="seconds",
            retention_days=60,
        )
        assert mp.metric_type == MetricType.HISTOGRAM
        assert mp.unit == "seconds"

    def test_empty_name_raises_error(self):
        """Kiểm tra tên metric rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            MetricProfile(name="")
        assert exc_info.value.code == ErrorCode.CP15_EMPTY_METRIC_NAME

    def test_whitespace_only_name_raises_error(self):
        """Kiểm tra tên metric chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            MetricProfile(name="   ")
        assert exc_info.value.code == ErrorCode.CP15_EMPTY_METRIC_NAME

    def test_zero_retention_raises_error(self):
        """Kiểm tra retention_days = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            MetricProfile(name="test", retention_days=0)
        assert exc_info.value.code == ErrorCode.CP15_METRIC_RETENTION_INVALID

    def test_negative_retention_raises_error(self):
        """Kiểm tra retention_days âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            MetricProfile(name="test", retention_days=-5)
        assert exc_info.value.code == ErrorCode.CP15_METRIC_RETENTION_INVALID

    def test_default_values(self):
        """Kiểm tra default values của MetricProfile."""
        mp = MetricProfile(name="default_test")
        assert mp.metric_type == MetricType.COUNTER
        assert mp.unit == "count"
        assert mp.labels == {}
        assert mp.retention_days == 30
        assert mp.description == ""

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        mp = MetricProfile(
            name="cpu_usage",
            metric_type=MetricType.GAUGE,
            unit="percent",
            labels={"host": "server-1"},
            retention_days=60,
            description="Theo dõi CPU",
        )
        data = mp.to_dict()
        assert data["name"] == "cpu_usage"
        assert data["metric_type"] == "gauge"
        assert data["unit"] == "percent"
        assert data["labels"] == {"host": "server-1"}
        assert data["retention_days"] == 60
        assert data["description"] == "Theo dõi CPU"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "name": "disk_io",
            "metric_type": "histogram",
            "unit": "bytes",
            "labels": {"mount": "/data"},
            "retention_days": 45,
            "description": "Disk I/O",
        }
        mp = MetricProfile.from_dict(data)
        assert mp.name == "disk_io"
        assert mp.metric_type == MetricType.HISTOGRAM
        assert mp.unit == "bytes"
        assert mp.labels == {"mount": "/data"}
        assert mp.retention_days == 45

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = MetricProfile(
            name="network_bytes",
            metric_type=MetricType.COUNTER,
            unit="bytes",
            labels={"direction": "inbound"},
            retention_days=30,
            description="Byte mạng",
        )
        restored = MetricProfile.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.metric_type == original.metric_type
        assert restored.unit == original.unit
        assert restored.labels == original.labels
        assert restored.retention_days == original.retention_days
        assert restored.description == original.description


# =============================================================================
# StructuredLogConfig Tests
# =============================================================================


class TestStructuredLogConfig:
    """Test StructuredLogConfig dataclass."""

    def test_create_valid_json(self):
        """Kiểm tra tạo log config hợp lệ với format json."""
        cfg = StructuredLogConfig(service_name="api-gateway", log_level=LogLevel.DEBUG)
        assert cfg.service_name == "api-gateway"
        assert cfg.log_level == LogLevel.DEBUG
        assert cfg.output_format == "json"

    def test_create_valid_text(self):
        """Kiểm tra tạo log config hợp lệ với format text."""
        cfg = StructuredLogConfig(
            service_name="worker",
            log_level=LogLevel.WARNING,
            output_format="text",
        )
        assert cfg.output_format == "text"
        assert cfg.log_level == LogLevel.WARNING

    def test_invalid_format_raises_error(self):
        """Kiểm tra output_format không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            StructuredLogConfig(service_name="test", output_format="xml")
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_all_log_levels_valid(self):
        """Kiểm tra tất cả log levels đều hợp lệ."""
        for level in LogLevel:
            cfg = StructuredLogConfig(service_name="test", log_level=level)
            assert cfg.log_level == level

    def test_default_values(self):
        """Kiểm tra default values của StructuredLogConfig."""
        cfg = StructuredLogConfig()
        assert cfg.service_name == "midicoder"
        assert cfg.log_level == LogLevel.INFO
        assert cfg.include_trace_id is True
        assert cfg.include_span_id is True
        assert cfg.output_format == "json"
        assert cfg.fields == {}

    def test_custom_fields(self):
        """Kiểm tra thêm custom fields."""
        cfg = StructuredLogConfig(
            service_name="billing",
            fields={"region": "ap-southeast-1", "version": "2.0"},
        )
        assert cfg.fields == {"region": "ap-southeast-1", "version": "2.0"}

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        cfg = StructuredLogConfig(
            service_name="payment",
            log_level=LogLevel.ERROR,
            include_trace_id=False,
            include_span_id=False,
            output_format="text",
            fields={"env": "staging"},
        )
        data = cfg.to_dict()
        assert data["service_name"] == "payment"
        assert data["log_level"] == "ERROR"
        assert data["include_trace_id"] is False
        assert data["include_span_id"] is False
        assert data["output_format"] == "text"
        assert data["fields"] == {"env": "staging"}

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "service_name": "auth",
            "log_level": "WARNING",
            "include_trace_id": True,
            "include_span_id": False,
            "output_format": "json",
            "fields": {"tenant": "t-123"},
        }
        cfg = StructuredLogConfig.from_dict(data)
        assert cfg.service_name == "auth"
        assert cfg.log_level == LogLevel.WARNING
        assert cfg.include_span_id is False
        assert cfg.fields == {"tenant": "t-123"}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = StructuredLogConfig(
            service_name="order-svc",
            log_level=LogLevel.DEBUG,
            include_trace_id=True,
            include_span_id=True,
            output_format="json",
            fields={"cluster": "primary"},
        )
        restored = StructuredLogConfig.from_dict(original.to_dict())
        assert restored.service_name == original.service_name
        assert restored.log_level == original.log_level
        assert restored.include_trace_id == original.include_trace_id
        assert restored.include_span_id == original.include_span_id
        assert restored.output_format == original.output_format
        assert restored.fields == original.fields

    def test_compute_entry_hash(self):
        """Kiểm tra compute_entry_hash trả về SHA-256."""
        cfg = StructuredLogConfig(service_name="test-svc")
        h = cfg.compute_entry_hash("test message")
        assert len(h) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in h)

    def test_compute_entry_hash_different_messages(self):
        """Kiểm tra hash khác nhau cho message khác nhau."""
        cfg = StructuredLogConfig(service_name="test-svc")
        h1 = cfg.compute_entry_hash("message one")
        h2 = cfg.compute_entry_hash("message two")
        assert h1 != h2


# =============================================================================
# TraceConfig Tests
# =============================================================================


class TestTraceConfig:
    """Test TraceConfig dataclass."""

    def test_create_valid_w3c(self):
        """Kiểm tra tạo trace config hợp lệ với W3C."""
        cfg = TraceConfig(service_name="order-service")
        assert cfg.service_name == "order-service"
        assert cfg.propagation_format == TracePropagationFormat.W3C_TRACE_CONTEXT

    def test_create_valid_b3(self):
        """Kiểm tra tạo trace config hợp lệ với B3."""
        cfg = TraceConfig(
            service_name="payment",
            propagation_format=TracePropagationFormat.B3,
        )
        assert cfg.propagation_format == TracePropagationFormat.B3

    def test_create_valid_none(self):
        """Kiểm tra tạo trace config hợp lệ với NONE."""
        cfg = TraceConfig(
            service_name="local-test",
            propagation_format=TracePropagationFormat.NONE,
        )
        assert cfg.propagation_format == TracePropagationFormat.NONE

    def test_zero_max_spans_raises_error(self):
        """Kiểm tra max_spans = 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TraceConfig(service_name="test", max_spans=0)
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_negative_max_spans_raises_error(self):
        """Kiểm tra max_spans âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TraceConfig(service_name="test", max_spans=-1)
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_sample_rate_below_zero_raises_error(self):
        """Kiểm tra sample_rate < 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TraceConfig(service_name="test", sample_rate=-0.1)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_TRACE_FORMAT

    def test_sample_rate_above_one_raises_error(self):
        """Kiểm tra sample_rate > 1 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TraceConfig(service_name="test", sample_rate=1.5)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_TRACE_FORMAT

    def test_sample_rate_boundary_zero(self):
        """Kiểm tra sample_rate = 0.0 hợp lệ."""
        cfg = TraceConfig(service_name="test", sample_rate=0.0)
        assert cfg.sample_rate == 0.0

    def test_sample_rate_boundary_one(self):
        """Kiểm tra sample_rate = 1.0 hợp lệ."""
        cfg = TraceConfig(service_name="test", sample_rate=1.0)
        assert cfg.sample_rate == 1.0

    def test_default_values(self):
        """Kiểm tra default values của TraceConfig."""
        cfg = TraceConfig()
        assert cfg.service_name == "midicoder"
        assert cfg.propagation_format == TracePropagationFormat.W3C_TRACE_CONTEXT
        assert cfg.max_spans == 100
        assert cfg.sample_rate == 1.0
        assert cfg.attributes == {}

    def test_custom_attributes(self):
        """Kiểm tra thêm custom attributes."""
        cfg = TraceConfig(
            service_name="api",
            attributes={"version": "1.0", "environment": "prod"},
        )
        assert cfg.attributes == {"version": "1.0", "environment": "prod"}

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        cfg = TraceConfig(
            service_name="inventory",
            propagation_format=TracePropagationFormat.B3,
            max_spans=50,
            sample_rate=0.5,
            attributes={"region": "us-east"},
        )
        data = cfg.to_dict()
        assert data["service_name"] == "inventory"
        assert data["propagation_format"] == "b3"
        assert data["max_spans"] == 50
        assert data["sample_rate"] == 0.5
        assert data["attributes"] == {"region": "us-east"}

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "service_name": "notification",
            "propagation_format": "none",
            "max_spans": 200,
            "sample_rate": 0.25,
            "attributes": {"team": "platform"},
        }
        cfg = TraceConfig.from_dict(data)
        assert cfg.service_name == "notification"
        assert cfg.propagation_format == TracePropagationFormat.NONE
        assert cfg.max_spans == 200
        assert cfg.sample_rate == 0.25
        assert cfg.attributes == {"team": "platform"}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = TraceConfig(
            service_name="analytics",
            propagation_format=TracePropagationFormat.W3C_TRACE_CONTEXT,
            max_spans=150,
            sample_rate=0.75,
            attributes={"cluster": "eu-west"},
        )
        restored = TraceConfig.from_dict(original.to_dict())
        assert restored.service_name == original.service_name
        assert restored.propagation_format == original.propagation_format
        assert restored.max_spans == original.max_spans
        assert restored.sample_rate == original.sample_rate
        assert restored.attributes == original.attributes


# =============================================================================
# OTLPExportProtocol Enum Tests
# =============================================================================


class TestOTLPExportProtocol:
    """Test OTLPExportProtocol enum."""

    def test_grpc_value(self):
        """Kiểm tra giá trị GRPC."""
        assert OTLPExportProtocol.GRPC.value == "grpc"

    def test_http_json_value(self):
        """Kiểm tra giá trị HTTP_JSON."""
        assert OTLPExportProtocol.HTTP_JSON.value == "http_json"

    def test_http_protobuf_value(self):
        """Kiểm tra giá trị HTTP_PROTOBUF."""
        assert OTLPExportProtocol.HTTP_PROTOBUF.value == "http_protobuf"

    def test_total_count(self):
        """Kiểm tra tổng số protocol = 3."""
        assert len(OTLPExportProtocol) == 3

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert OTLPExportProtocol.GRPC == "grpc"
        assert OTLPExportProtocol.HTTP_JSON == "http_json"
        assert OTLPExportProtocol.HTTP_PROTOBUF == "http_protobuf"


# =============================================================================
# SamplerType Enum Tests
# =============================================================================


class TestSamplerType:
    """Test SamplerType enum."""

    def test_always_on_value(self):
        """Kiểm tra giá trị ALWAYS_ON."""
        assert SamplerType.ALWAYS_ON.value == "always_on"

    def test_always_off_value(self):
        """Kiểm tra giá trị ALWAYS_OFF."""
        assert SamplerType.ALWAYS_OFF.value == "always_off"

    def test_traceid_ratio_based_value(self):
        """Kiểm tra giá trị TRACEID_RATIO_BASED."""
        assert SamplerType.TRACEID_RATIO_BASED.value == "traceid_ratio_based"

    def test_parent_based_value(self):
        """Kiểm tra giá trị PARENT_BASED."""
        assert SamplerType.PARENT_BASED.value == "parent_based"

    def test_total_count(self):
        """Kiểm tra tổng số sampler types = 4."""
        assert len(SamplerType) == 4

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert SamplerType.ALWAYS_ON == "always_on"
        assert SamplerType.ALWAYS_OFF == "always_off"
        assert SamplerType.TRACEID_RATIO_BASED == "traceid_ratio_based"
        assert SamplerType.PARENT_BASED == "parent_based"


# =============================================================================
# SpanKind Enum Tests
# =============================================================================


class TestSpanKind:
    """Test SpanKind enum."""

    def test_internal_value(self):
        """Kiểm tra giá trị INTERNAL."""
        assert SpanKind.INTERNAL.value == "internal"

    def test_server_value(self):
        """Kiểm tra giá trị SERVER."""
        assert SpanKind.SERVER.value == "server"

    def test_client_value(self):
        """Kiểm tra giá trị CLIENT."""
        assert SpanKind.CLIENT.value == "client"

    def test_producer_value(self):
        """Kiểm tra giá trị PRODUCER."""
        assert SpanKind.PRODUCER.value == "producer"

    def test_consumer_value(self):
        """Kiểm tra giá trị CONSUMER."""
        assert SpanKind.CONSUMER.value == "consumer"

    def test_total_count(self):
        """Kiểm tra tổng số span kinds = 5."""
        assert len(SpanKind) == 5


# =============================================================================
# LogDestinationType Enum Tests
# =============================================================================


class TestLogDestinationType:
    """Test LogDestinationType enum."""

    def test_loki_value(self):
        assert LogDestinationType.LOKI.value == "loki"

    def test_cloudwatch_value(self):
        assert LogDestinationType.CLOUDWATCH.value == "cloudwatch"

    def test_datadog_value(self):
        assert LogDestinationType.DATADOG.value == "datadog"

    def test_elasticsearch_value(self):
        assert LogDestinationType.ELASTICSEARCH.value == "elasticsearch"

    def test_splunk_value(self):
        assert LogDestinationType.SPLUNK.value == "splunk"

    def test_stdout_value(self):
        assert LogDestinationType.STDOUT.value == "stdout"

    def test_file_value(self):
        assert LogDestinationType.FILE.value == "file"

    def test_total_count(self):
        """Kiểm tra tổng số destination types = 7."""
        assert len(LogDestinationType) == 7

    def test_string_comparison(self):
        """Kiểm tra so sánh với string."""
        assert LogDestinationType.LOKI == "loki"
        assert LogDestinationType.CLOUDWATCH == "cloudwatch"
        assert LogDestinationType.DATADOG == "datadog"


# =============================================================================
# OTelExporterConfig Tests
# =============================================================================


class TestOTelExporterConfig:
    """Test OTelExporterConfig dataclass."""

    def test_create_valid_defaults(self):
        """Kiểm tra tạo exporter config hợp lệ với defaults."""
        cfg = OTelExporterConfig()
        assert cfg.endpoint == "http://localhost:4317"
        assert cfg.protocol == OTLPExportProtocol.GRPC
        assert cfg.timeout_ms == 10000
        assert cfg.compression == "none"
        assert cfg.batch_size == 512
        assert cfg.batch_timeout_ms == 5000
        assert cfg.retry_on_failure is True
        assert cfg.max_queue_size == 2048
        assert cfg.description == ""

    def test_create_valid_custom(self):
        """Kiểm tra tạo exporter config custom."""
        cfg = OTelExporterConfig(
            endpoint="http://otel-collector:4318",
            protocol=OTLPExportProtocol.HTTP_JSON,
            timeout_ms=5000,
            headers={"Authorization": "Bearer token123"},
            compression="gzip",
            batch_size=256,
            batch_timeout_ms=3000,
            retry_on_failure=False,
            max_queue_size=4096,
            description="Custom OTLP exporter",
        )
        assert cfg.endpoint == "http://otel-collector:4318"
        assert cfg.protocol == OTLPExportProtocol.HTTP_JSON
        assert cfg.headers == {"Authorization": "Bearer token123"}
        assert cfg.compression == "gzip"
        assert cfg.batch_size == 256
        assert cfg.retry_on_failure is False

    def test_empty_endpoint_raises_error(self):
        """Kiểm tra endpoint rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            OTelExporterConfig(endpoint="")
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_whitespace_endpoint_raises_error(self):
        """Kiểm tra endpoint chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            OTelExporterConfig(endpoint="   ")
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_zero_timeout_clamped(self):
        """Kiểm tra timeout_ms = 0 được clamp về 10000."""
        cfg = OTelExporterConfig(timeout_ms=0)
        assert cfg.timeout_ms == 10000

    def test_zero_batch_size_clamped(self):
        """Kiểm tra batch_size = 0 được clamp về 512."""
        cfg = OTelExporterConfig(batch_size=0)
        assert cfg.batch_size == 512

    def test_all_protocols(self):
        """Kiểm tra tất cả protocol đều hợp lệ."""
        for proto in OTLPExportProtocol:
            cfg = OTelExporterConfig(protocol=proto)
            assert cfg.protocol == proto

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        cfg = OTelExporterConfig(
            endpoint="http://otel:4317",
            protocol=OTLPExportProtocol.HTTP_PROTOBUF,
            timeout_ms=8000,
            headers={"X-API-Key": "secret"},
            compression="gzip",
            batch_size=1024,
            batch_timeout_ms=4000,
            retry_on_failure=True,
            max_queue_size=1024,
            description="Test exporter",
        )
        data = cfg.to_dict()
        assert data["endpoint"] == "http://otel:4317"
        assert data["protocol"] == "http_protobuf"
        assert data["timeout_ms"] == 8000
        assert data["headers"] == {"X-API-Key": "secret"}
        assert data["compression"] == "gzip"
        assert data["batch_size"] == 1024
        assert data["description"] == "Test exporter"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "endpoint": "http://collector:4319",
            "protocol": "http_json",
            "timeout_ms": 15000,
            "headers": {"X-Custom": "val"},
            "compression": "none",
            "batch_size": 2048,
            "batch_timeout_ms": 6000,
            "retry_on_failure": False,
            "max_queue_size": 8192,
            "description": "",
        }
        cfg = OTelExporterConfig.from_dict(data)
        assert cfg.endpoint == "http://collector:4319"
        assert cfg.protocol == OTLPExportProtocol.HTTP_JSON
        assert cfg.timeout_ms == 15000
        assert cfg.headers == {"X-Custom": "val"}
        assert cfg.batch_size == 2048
        assert cfg.retry_on_failure is False

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = OTelExporterConfig(
            endpoint="http://otel-svc:4317",
            protocol=OTLPExportProtocol.GRPC,
            timeout_ms=10000,
            headers={"Authorization": "Bearer tk"},
            compression="gzip",
            batch_size=512,
            batch_timeout_ms=5000,
            retry_on_failure=True,
            max_queue_size=2048,
            description="Roundtrip test",
        )
        restored = OTelExporterConfig.from_dict(original.to_dict())
        assert restored.endpoint == original.endpoint
        assert restored.protocol == original.protocol
        assert restored.timeout_ms == original.timeout_ms
        assert restored.headers == original.headers
        assert restored.compression == original.compression
        assert restored.batch_size == original.batch_size
        assert restored.batch_timeout_ms == original.batch_timeout_ms
        assert restored.retry_on_failure == original.retry_on_failure
        assert restored.max_queue_size == original.max_queue_size
        assert restored.description == original.description


# =============================================================================
# OpenTelemetryConfig Tests
# =============================================================================


class TestOpenTelemetryConfig:
    """Test OpenTelemetryConfig dataclass."""

    def test_create_valid_defaults(self):
        """Kiểm tra tạo OpenTelemetry config hợp lệ với defaults."""
        cfg = OpenTelemetryConfig()
        assert cfg.service_name == "midicoder"
        assert cfg.sampler_type == SamplerType.TRACEID_RATIO_BASED
        assert cfg.sampler_rate == 1.0
        assert cfg.enable_traces is True
        assert cfg.enable_metrics is True
        assert cfg.enable_logs is True
        assert isinstance(cfg.exporter, OTelExporterConfig)
        assert cfg.description == ""

    def test_create_valid_full(self):
        """Kiểm tra tạo OpenTelemetry config đầy đủ."""
        exporter = OTelExporterConfig(
            endpoint="http://collector:4318",
            protocol=OTLPExportProtocol.HTTP_JSON,
        )
        cfg = OpenTelemetryConfig(
            service_name="payment-service",
            exporter=exporter,
            sampler_type=SamplerType.PARENT_BASED,
            sampler_rate=0.5,
            resource_attributes={"env": "prod", "region": "us-east"},
            enable_traces=True,
            enable_metrics=False,
            enable_logs=True,
            description="Full OTel config",
        )
        assert cfg.service_name == "payment-service"
        assert cfg.sampler_type == SamplerType.PARENT_BASED
        assert cfg.sampler_rate == 0.5
        assert cfg.enable_metrics is False
        assert cfg.resource_attributes == {"env": "prod", "region": "us-east"}
        assert cfg.exporter.endpoint == "http://collector:4318"

    def test_empty_service_name_raises_error(self):
        """Kiểm tra service_name rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            OpenTelemetryConfig(service_name="")
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_sample_rate_negative_raises_error(self):
        """Kiểm tra sampler_rate < 0 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            OpenTelemetryConfig(service_name="test", sampler_rate=-0.5)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_TRACE_FORMAT

    def test_sample_rate_above_one_raises_error(self):
        """Kiểm tra sampler_rate > 1 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            OpenTelemetryConfig(service_name="test", sampler_rate=2.0)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_TRACE_FORMAT

    def test_all_sampler_types(self):
        """Kiểm tra tất cả sampler types đều hợp lệ."""
        for st in SamplerType:
            cfg = OpenTelemetryConfig(service_name="test", sampler_type=st)
            assert cfg.sampler_type == st

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        exporter = OTelExporterConfig(
            endpoint="http://otel:4317",
            protocol=OTLPExportProtocol.GRPC,
        )
        cfg = OpenTelemetryConfig(
            service_name="api-svc",
            exporter=exporter,
            sampler_type=SamplerType.ALWAYS_ON,
            sampler_rate=1.0,
            resource_attributes={"cluster": "primary"},
            enable_traces=True,
            enable_metrics=True,
            enable_logs=False,
            description="Dict test",
        )
        data = cfg.to_dict()
        assert data["service_name"] == "api-svc"
        assert data["sampler_type"] == "always_on"
        assert data["sampler_rate"] == 1.0
        assert data["enable_logs"] is False
        assert data["resource_attributes"] == {"cluster": "primary"}
        assert "exporter" in data
        assert data["exporter"]["endpoint"] == "http://otel:4317"

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "service_name": "worker-svc",
            "exporter": {
                "endpoint": "http://collector:4317",
                "protocol": "http_protobuf",
            },
            "sampler_type": "parent_based",
            "sampler_rate": 0.75,
            "resource_attributes": {"version": "2.0"},
            "enable_traces": True,
            "enable_metrics": True,
            "enable_logs": True,
            "description": "",
        }
        cfg = OpenTelemetryConfig.from_dict(data)
        assert cfg.service_name == "worker-svc"
        assert cfg.sampler_type == SamplerType.PARENT_BASED
        assert cfg.sampler_rate == 0.75
        assert cfg.exporter.endpoint == "http://collector:4317"
        assert cfg.exporter.protocol == OTLPExportProtocol.HTTP_PROTOBUF

    def test_from_dict_without_exporter(self):
        """Kiểm tra from_dict không có exporter dùng default."""
        data = {
            "service_name": "minimal-otel",
            "sampler_type": "always_on",
        }
        cfg = OpenTelemetryConfig.from_dict(data)
        assert cfg.service_name == "minimal-otel"
        assert isinstance(cfg.exporter, OTelExporterConfig)
        assert cfg.exporter.endpoint == "http://localhost:4317"

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = OpenTelemetryConfig(
            service_name="roundtrip-svc",
            exporter=OTelExporterConfig(
                endpoint="http://otel:4317",
                protocol=OTLPExportProtocol.GRPC,
                compression="gzip",
                batch_size=256,
            ),
            sampler_type=SamplerType.TRACEID_RATIO_BASED,
            sampler_rate=0.8,
            resource_attributes={"env": "staging"},
            enable_traces=True,
            enable_metrics=True,
            enable_logs=True,
            description="Roundtrip",
        )
        restored = OpenTelemetryConfig.from_dict(original.to_dict())
        assert restored.service_name == original.service_name
        assert restored.sampler_type == original.sampler_type
        assert restored.sampler_rate == original.sampler_rate
        assert restored.enable_traces == original.enable_traces
        assert restored.enable_metrics == original.enable_metrics
        assert restored.enable_logs == original.enable_logs
        assert restored.resource_attributes == original.resource_attributes
        assert restored.exporter.endpoint == original.exporter.endpoint
        assert restored.exporter.protocol == original.exporter.protocol
        assert restored.exporter.compression == original.exporter.compression
        assert restored.exporter.batch_size == original.exporter.batch_size


# =============================================================================
# LogShippingDestination Tests
# =============================================================================


class TestLogShippingDestination:
    """Test LogShippingDestination dataclass."""

    def test_create_valid_loki(self):
        """Kiểm tra tạo destination Loki hợp lệ."""
        dest = LogShippingDestination(
            destination_type=LogDestinationType.LOKI,
            endpoint="http://loki:3100/loki/api/v1/push",
            flush_interval_ms=3000,
            max_batch_size=500,
            labels={"app": "midicoder", "env": "prod"},
        )
        assert dest.destination_type == LogDestinationType.LOKI
        assert dest.endpoint == "http://loki:3100/loki/api/v1/push"
        assert dest.labels == {"app": "midicoder", "env": "prod"}

    def test_create_all_destination_types(self):
        """Kiểm tra tất cả destination types đều hợp lệ."""
        for dt in LogDestinationType:
            dest = LogShippingDestination(destination_type=dt)
            assert dest.destination_type == dt

    def test_default_values(self):
        """Kiểm tra default values."""
        dest = LogShippingDestination(destination_type=LogDestinationType.LOKI)
        assert dest.endpoint == ""
        assert dest.auth_token == ""
        assert dest.flush_interval_ms == 5000
        assert dest.max_batch_size == 1000
        assert dest.compression == "gzip"
        assert dest.labels == {}
        assert dest.filter_pattern == ""

    def test_negative_flush_interval_clamped(self):
        """Kiểm tra flush_interval_ms âm được clamp."""
        dest = LogShippingDestination(
            destination_type=LogDestinationType.LOKI,
            flush_interval_ms=-1,
        )
        assert dest.flush_interval_ms == 5000

    def test_zero_batch_size_clamped(self):
        """Kiểm tra max_batch_size = 0 được clamp."""
        dest = LogShippingDestination(
            destination_type=LogDestinationType.LOKI,
            max_batch_size=0,
        )
        assert dest.max_batch_size == 1000

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        dest = LogShippingDestination(
            destination_type=LogDestinationType.DATADOG,
            endpoint="https://http-intake.logs.datadoghq.com",
            flush_interval_ms=5000,
            max_batch_size=2000,
            compression="gzip",
            labels={"service": "api"},
            filter_pattern="level >= warning",
            description="Datadog dest",
        )
        data = dest.to_dict()
        assert data["destination_type"] == "datadog"
        assert data["endpoint"] == "https://http-intake.logs.datadoghq.com"
        assert data["max_batch_size"] == 2000
        assert data["filter_pattern"] == "level >= warning"
        assert "auth_token" not in data

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "destination_type": "elasticsearch",
            "endpoint": "http://es:9200",
            "flush_interval_ms": 4000,
            "max_batch_size": 750,
            "compression": "none",
            "labels": {"index": "logs"},
            "filter_pattern": "",
            "description": "ES destination",
        }
        dest = LogShippingDestination.from_dict(data)
        assert dest.destination_type == LogDestinationType.ELASTICSEARCH
        assert dest.endpoint == "http://es:9200"
        assert dest.compression == "none"
        assert dest.labels == {"index": "logs"}

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = LogShippingDestination(
            destination_type=LogDestinationType.CLOUDWATCH,
            endpoint="arn:aws:logs:us-east-1:123456789",
            flush_interval_ms=5000,
            max_batch_size=1000,
            compression="gzip",
            labels={"account": "prod"},
            filter_pattern="level >= error",
            description="CloudWatch",
        )
        restored = LogShippingDestination.from_dict(original.to_dict())
        assert restored.destination_type == original.destination_type
        assert restored.endpoint == original.endpoint
        assert restored.flush_interval_ms == original.flush_interval_ms
        assert restored.max_batch_size == original.max_batch_size
        assert restored.compression == original.compression
        assert restored.labels == original.labels
        assert restored.filter_pattern == original.filter_pattern
        assert restored.description == original.description


# =============================================================================
# LogShippingConfig Tests
# =============================================================================


class TestLogShippingConfig:
    """Test LogShippingConfig dataclass."""

    def test_create_valid_defaults(self):
        """Kiểm tra tạo config hợp lệ với defaults."""
        cfg = LogShippingConfig()
        assert cfg.enabled is True
        assert cfg.destinations == []
        assert cfg.async_shipping is True
        assert cfg.max_queue_size == 10000
        assert cfg.drop_on_overflow is False
        assert cfg.description == ""

    def test_create_valid_with_destinations(self):
        """Kiểm tra tạo config với destinations."""
        dests = [
            LogShippingDestination(destination_type=LogDestinationType.LOKI, endpoint="http://loki:3100"),
            LogShippingDestination(destination_type=LogDestinationType.DATADOG, endpoint="https://dd-intake"),
        ]
        cfg = LogShippingConfig(
            enabled=True,
            destinations=dests,
            async_shipping=True,
            max_queue_size=5000,
            drop_on_overflow=True,
            description="Multi-dest config",
        )
        assert len(cfg.destinations) == 2
        assert cfg.destinations[0].destination_type == LogDestinationType.LOKI
        assert cfg.destinations[1].destination_type == LogDestinationType.DATADOG
        assert cfg.max_queue_size == 5000
        assert cfg.drop_on_overflow is True

    def test_zero_queue_size_clamped(self):
        """Kiểm tra max_queue_size = 0 được clamp về 10000."""
        cfg = LogShippingConfig(max_queue_size=0)
        assert cfg.max_queue_size == 10000

    def test_to_dict(self):
        """Kiểm tra to_dict serialization."""
        dest = LogShippingDestination(
            destination_type=LogDestinationType.LOKI,
            endpoint="http://loki:3100",
        )
        cfg = LogShippingConfig(
            enabled=True,
            destinations=[dest],
            async_shipping=False,
            max_queue_size=8000,
            drop_on_overflow=False,
            description="Test config",
        )
        data = cfg.to_dict()
        assert data["enabled"] is True
        assert len(data["destinations"]) == 1
        assert data["destinations"][0]["destination_type"] == "loki"
        assert data["async_shipping"] is False
        assert data["max_queue_size"] == 8000

    def test_from_dict(self):
        """Kiểm tra from_dict deserialization."""
        data = {
            "enabled": False,
            "destinations": [
                {
                    "destination_type": "loki",
                    "endpoint": "http://loki:3100",
                    "labels": {"app": "test"},
                },
                {
                    "destination_type": "stdout",
                },
            ],
            "async_shipping": True,
            "max_queue_size": 20000,
            "drop_on_overflow": True,
            "description": "Parsed config",
        }
        cfg = LogShippingConfig.from_dict(data)
        assert cfg.enabled is False
        assert len(cfg.destinations) == 2
        assert cfg.destinations[0].destination_type == LogDestinationType.LOKI
        assert cfg.destinations[1].destination_type == LogDestinationType.STDOUT
        assert cfg.max_queue_size == 20000
        assert cfg.drop_on_overflow is True

    def test_from_dict_empty_destinations(self):
        """Kiểm tra from_dict không có destinations."""
        data = {"enabled": True}
        cfg = LogShippingConfig.from_dict(data)
        assert cfg.enabled is True
        assert cfg.destinations == []

    def test_roundtrip_to_dict_from_dict(self):
        """Kiểm tra roundtrip to_dict → from_dict."""
        original = LogShippingConfig(
            enabled=True,
            destinations=[
                LogShippingDestination(
                    destination_type=LogDestinationType.LOKI,
                    endpoint="http://loki:3100/loki/api/v1/push",
                    labels={"app": "midicoder"},
                    filter_pattern="level >= info",
                ),
                LogShippingDestination(
                    destination_type=LogDestinationType.DATADOG,
                    endpoint="https://http-intake.datadoghq.com",
                    compression="gzip",
                ),
            ],
            async_shipping=True,
            max_queue_size=10000,
            drop_on_overflow=False,
            description="Roundtrip test",
        )
        restored = LogShippingConfig.from_dict(original.to_dict())
        assert restored.enabled == original.enabled
        assert restored.async_shipping == original.async_shipping
        assert restored.max_queue_size == original.max_queue_size
        assert restored.drop_on_overflow == original.drop_on_overflow
        assert restored.description == original.description
        assert len(restored.destinations) == len(original.destinations)
        for i, orig_dest in enumerate(original.destinations):
            assert restored.destinations[i].destination_type == orig_dest.destination_type
            assert restored.destinations[i].endpoint == orig_dest.endpoint
            assert restored.destinations[i].labels == orig_dest.labels
