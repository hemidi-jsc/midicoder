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

from midicoder.emitters.core.cp15_observability.models import (
    LogLevel,
    MetricProfile,
    MetricType,
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
