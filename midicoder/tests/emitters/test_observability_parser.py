# coding: utf-8
"""
Test cases cho CP15 Observability Stack Parser.

Kiểm tra:
- ObservabilityParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid types, invalid enums
- Edge cases: Empty input, missing sections, default values

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
from midicoder.emitters.core.cp15_observability.models import (
    LogLevel,
    MetricProfile,
    MetricType,
    StructuredLogConfig,
    TraceConfig,
    TracePropagationFormat,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestObservabilityParser:
    """Test suite cho ObservabilityParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = ObservabilityParser()

    # =========================================================================
    # Empty / whitespace input
    # =========================================================================

    def test_parse_empty_string_returns_empty_dicts(self):
        """Kiểm tra parse string rỗng trả về dict rỗng cho tất cả sections."""
        result = self.parser.parse("")
        assert result == {"metrics": [], "logging": [], "tracing": []}

    def test_parse_whitespace_only_returns_empty_dicts(self):
        """Kiểm tra parse whitespace trả về dict rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert result == {"metrics": [], "logging": [], "tracing": []}

    def test_parse_comment_only_returns_empty_dicts(self):
        """Kiểm tra parse chỉ có comment YAML trả về dict rỗng."""
        dsl = """
# Chỉ có comment
# Không có dữ liệu
"""
        result = self.parser.parse(dsl)
        assert result == {"metrics": [], "logging": [], "tracing": []}

    # =========================================================================
    # Valid metrics section
    # =========================================================================

    def test_parse_single_metric_counter(self):
        """Kiểm tra parse metric counter hợp lệ."""
        dsl = """
metrics:
  - name: http_requests_total
    type: counter
    unit: count
    labels:
      method: GET
      status: "200"
    retention_days: 90
    description: Total HTTP requests
"""
        result = self.parser.parse(dsl)
        assert len(result["metrics"]) == 1
        assert len(result["logging"]) == 0
        assert len(result["tracing"]) == 0

        metric = result["metrics"][0]
        assert isinstance(metric, MetricProfile)
        assert metric.name == "http_requests_total"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.unit == "count"
        assert metric.labels == {"method": "GET", "status": "200"}
        assert metric.retention_days == 90
        assert metric.description == "Total HTTP requests"

    def test_parse_metric_with_default_values(self):
        """Kiểm tra parse metric với default values."""
        dsl = """
metrics:
  - name: simple_metric
"""
        result = self.parser.parse(dsl)
        metric = result["metrics"][0]
        assert metric.name == "simple_metric"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.unit == ""
        assert metric.labels == {}
        assert metric.retention_days == 30
        assert metric.description == ""

    def test_parse_all_metric_types(self):
        """Kiểm tra parse tất cả loại metric."""
        dsl = """
metrics:
  - name: counter_metric
    type: counter
  - name: gauge_metric
    type: gauge
  - name: histogram_metric
    type: histogram
"""
        result = self.parser.parse(dsl)
        assert len(result["metrics"]) == 3
        assert result["metrics"][0].metric_type == MetricType.COUNTER
        assert result["metrics"][1].metric_type == MetricType.GAUGE
        assert result["metrics"][2].metric_type == MetricType.HISTOGRAM

    def test_parse_metric_histogram_with_retention(self):
        """Kiểm tra parse metric histogram với retention ngắn."""
        dsl = """
metrics:
  - name: response_time_seconds
    type: histogram
    unit: seconds
    retention_days: 30
"""
        result = self.parser.parse(dsl)
        metric = result["metrics"][0]
        assert metric.name == "response_time_seconds"
        assert metric.metric_type == MetricType.HISTOGRAM
        assert metric.unit == "seconds"
        assert metric.retention_days == 30

    # =========================================================================
    # Valid logging section
    # =========================================================================

    def test_parse_single_log_config(self):
        """Kiểm tra parse log config hợp lệ."""
        dsl = """
logging:
  - service_name: order-service
    log_level: INFO
    include_trace_id: true
    output_format: json
"""
        result = self.parser.parse(dsl)
        assert len(result["logging"]) == 1

        log_cfg = result["logging"][0]
        assert isinstance(log_cfg, StructuredLogConfig)
        assert log_cfg.service_name == "order-service"
        assert log_cfg.log_level == LogLevel.INFO
        assert log_cfg.include_trace_id is True
        assert log_cfg.output_format == "json"

    def test_parse_log_config_with_span_id(self):
        """Kiểm tra parse log config có span_id."""
        dsl = """
logging:
  - service_name: payment-service
    log_level: DEBUG
    include_trace_id: true
    include_span_id: true
"""
        result = self.parser.parse(dsl)
        log_cfg = result["logging"][0]
        assert log_cfg.service_name == "payment-service"
        assert log_cfg.log_level == LogLevel.DEBUG
        assert log_cfg.include_span_id is True

    def test_parse_all_log_levels(self):
        """Kiểm tra parse tất cả log levels."""
        dsl = """
logging:
  - service_name: svc_debug
    log_level: DEBUG
  - service_name: svc_info
    log_level: INFO
  - service_name: svc_warning
    log_level: WARNING
  - service_name: svc_error
    log_level: ERROR
  - service_name: svc_critical
    log_level: CRITICAL
"""
        result = self.parser.parse(dsl)
        assert len(result["logging"]) == 5
        levels = [c.log_level for c in result["logging"]]
        assert LogLevel.DEBUG in levels
        assert LogLevel.INFO in levels
        assert LogLevel.WARNING in levels
        assert LogLevel.ERROR in levels
        assert LogLevel.CRITICAL in levels

    # =========================================================================
    # Valid tracing section
    # =========================================================================

    def test_parse_single_trace_config(self):
        """Kiểm tra parse trace config hợp lệ."""
        dsl = """
tracing:
  - service_name: api-gateway
    propagation_format: w3c_trace_context
    max_spans: 200
    sample_rate: 0.5
"""
        result = self.parser.parse(dsl)
        assert len(result["tracing"]) == 1

        trace_cfg = result["tracing"][0]
        assert isinstance(trace_cfg, TraceConfig)
        assert trace_cfg.service_name == "api-gateway"
        assert trace_cfg.propagation_format == TracePropagationFormat.W3C_TRACE_CONTEXT
        assert trace_cfg.max_spans == 200
        assert trace_cfg.sample_rate == 0.5

    def test_parse_trace_config_b3_format(self):
        """Kiểm tra parse trace config với B3 format."""
        dsl = """
tracing:
  - service_name: legacy-service
    propagation_format: b3
"""
        result = self.parser.parse(dsl)
        trace_cfg = result["tracing"][0]
        assert trace_cfg.service_name == "legacy-service"
        assert trace_cfg.propagation_format == TracePropagationFormat.B3

    def test_parse_trace_config_none_format(self):
        """Kiểm tra parse trace config với NONE format."""
        dsl = """
tracing:
  - service_name: isolated-service
    propagation_format: none
"""
        result = self.parser.parse(dsl)
        trace_cfg = result["tracing"][0]
        assert trace_cfg.propagation_format == TracePropagationFormat.NONE

    # =========================================================================
    # Full DSL with all 3 sections
    # =========================================================================

    def test_parse_full_dsl_all_sections(self):
        """Kiểm tra parse DSL đầy đủ với cả 3 sections."""
        dsl = """
metrics:
  - name: http_requests_total
    type: counter
    unit: count
    labels:
      method: GET
      status: "200"
    retention_days: 90
    description: Total HTTP requests
  - name: response_time_seconds
    type: histogram
    unit: seconds
    retention_days: 30
logging:
  - service_name: order-service
    log_level: INFO
    include_trace_id: true
    output_format: json
  - service_name: payment-service
    log_level: DEBUG
    include_trace_id: true
    include_span_id: true
tracing:
  - service_name: api-gateway
    propagation_format: w3c_trace_context
    max_spans: 200
    sample_rate: 0.5
"""
        result = self.parser.parse(dsl)
        assert len(result["metrics"]) == 2
        assert len(result["logging"]) == 2
        assert len(result["tracing"]) == 1

        # Verify metric types
        assert result["metrics"][0].metric_type == MetricType.COUNTER
        assert result["metrics"][1].metric_type == MetricType.HISTOGRAM

        # Verify log levels
        assert result["logging"][0].log_level == LogLevel.INFO
        assert result["logging"][1].log_level == LogLevel.DEBUG

        # Verify trace config
        assert result["tracing"][0].max_spans == 200
        assert result["tracing"][0].sample_rate == 0.5

    # =========================================================================
    # Invalid YAML
    # =========================================================================

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw error."""
        invalid_yaml = """
metrics:
  - name: test
    type: [invalid yaml
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra parse YAML list (không phải mapping) throw error."""
        list_yaml = """
- item1
- item2
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(list_yaml)
        assert exc_info.value.code == ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR

    # =========================================================================
    # Invalid enum values
    # =========================================================================

    def test_parse_invalid_metric_type_raises_error(self):
        """Kiểm tra metric type không hợp lệ throw error."""
        dsl = """
metrics:
  - name: bad_metric
    type: invalid_type
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_METRIC_TYPE

    def test_parse_invalid_log_level_raises_error(self):
        """Kiểm tra log level không hợp lệ throw error."""
        dsl = """
logging:
  - service_name: test-service
    log_level: TRACE
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_LOG_LEVEL

    def test_parse_invalid_propagation_format_raises_error(self):
        """Kiểm tra propagation format không hợp lệ throw error."""
        dsl = """
tracing:
  - service_name: test-service
    propagation_format: invalid_format
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.CP15_INVALID_TRACE_FORMAT

    # =========================================================================
    # Optional fields & defaults
    # =========================================================================

    def test_parse_metric_with_optional_fields(self):
        """Kiểm tra parse metric chỉ có name, các field còn lại dùng default."""
        dsl = """
metrics:
  - name: minimal_metric
"""
        result = self.parser.parse(dsl)
        metric = result["metrics"][0]
        assert metric.name == "minimal_metric"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.unit == ""
        assert metric.labels == {}
        assert metric.retention_days == 30
        assert metric.description == ""

    def test_parse_log_config_with_defaults(self):
        """Kiểm tra parse log config chỉ có service_name, defaults áp dụng."""
        dsl = """
logging:
  - service_name: minimal-service
"""
        result = self.parser.parse(dsl)
        log_cfg = result["logging"][0]
        assert log_cfg.service_name == "minimal-service"
        assert log_cfg.log_level == LogLevel.INFO
        assert log_cfg.include_trace_id is True
        assert log_cfg.include_span_id is True
        assert log_cfg.output_format == "json"
        assert log_cfg.fields == {}

    def test_parse_trace_config_with_defaults(self):
        """Kiểm tra parse trace config chỉ có service_name, defaults áp dụng."""
        dsl = """
tracing:
  - service_name: minimal-trace
"""
        result = self.parser.parse(dsl)
        trace_cfg = result["tracing"][0]
        assert trace_cfg.service_name == "minimal-trace"
        assert trace_cfg.propagation_format == TracePropagationFormat.W3C_TRACE_CONTEXT
        assert trace_cfg.max_spans == 100
        assert trace_cfg.sample_rate == 1.0
        assert trace_cfg.attributes == {}

    # =========================================================================
    # Missing sections
    # =========================================================================

    def test_parse_only_metrics_section(self):
        """Kiểm tra parse chỉ có metrics, các section khác rỗng."""
        dsl = """
metrics:
  - name: only_metric
    type: gauge
"""
        result = self.parser.parse(dsl)
        assert len(result["metrics"]) == 1
        assert result["logging"] == []
        assert result["tracing"] == []

    def test_parse_only_logging_section(self):
        """Kiểm tra parse chỉ có logging, các section khác rỗng."""
        dsl = """
logging:
  - service_name: only-log
    log_level: ERROR
"""
        result = self.parser.parse(dsl)
        assert result["metrics"] == []
        assert len(result["logging"]) == 1
        assert result["tracing"] == []

    def test_parse_only_tracing_section(self):
        """Kiểm tra parse chỉ có tracing, các section khác rỗng."""
        dsl = """
tracing:
  - service_name: only-trace
    propagation_format: b3
"""
        result = self.parser.parse(dsl)
        assert result["metrics"] == []
        assert result["logging"] == []
        assert len(result["tracing"]) == 1

    def test_parse_empty_sections(self):
        """Kiểm tra parse với các section rỗng."""
        dsl = """
metrics: []
logging: []
tracing: []
"""
        result = self.parser.parse(dsl)
        assert result["metrics"] == []
        assert result["logging"] == []
        assert result["tracing"] == []
