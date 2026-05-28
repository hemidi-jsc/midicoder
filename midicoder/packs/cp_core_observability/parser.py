# coding: utf-8
"""
Mô-đun parser cho CP15: Observability Stack Generator.

Parse YAML DSL thành dict chứa danh sách các model objects:
- metrics[] → list[MetricProfile]
- logging[] → list[StructuredLogConfig]
- tracing[] → list[TraceConfig]

Sử dụng:
    parser = ObservabilityParser()
    result = parser.parse(yaml_string)
    # result: dict với keys "metrics", "logging", "tracing"

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_core_observability.models import (
    LogLevel,
    LogShippingConfig,
    MetricProfile,
    MetricType,
    OpenTelemetryConfig,
    StructuredLogConfig,
    TraceConfig,
    TracePropagationFormat,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class ObservabilityParser:
    """
    Parser cho observability DSL (metrics, logging, tracing).

    Parse YAML string thành danh sách các model objects:
    - metrics[] → list[MetricProfile]
    - logging[] → list[StructuredLogConfig]
    - tracing[] → list[TraceConfig]

    Usage:
        parser = ObservabilityParser()
        result = parser.parse(yaml_string)
        # result: dict with "metrics", "logging", "tracing" keys
    """

    def parse(self, raw: str) -> dict:
        """
        Parse YAML DSL string thành observability config.

        Args:
            raw: YAML string

        Returns:
            Dict với keys: "metrics", "logging", "tracing"

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP15-010)
        """
        # Trường hợp rỗng hoặc whitespace-only
        if not raw or not raw.strip():
            return {
                "metrics": [],
                "logging": [],
                "tracing": [],
            }

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message=f"Lỗi parse YAML observability: {e}",
                error=str(e),
            )

        # YAML comment-only hoặc null → treat as empty
        if data is None:
            return {
                "metrics": [],
                "logging": [],
                "tracing": [],
            }

        # YAML phải là dict/mapping
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="DSL observability phải là YAML mapping",
            )

        result: dict[str, list] = {
            "metrics": [],
            "logging": [],
            "tracing": [],
        }

        # Parse metrics section
        raw_metrics = data.get("metrics", [])
        if isinstance(raw_metrics, list):
            for metric_data in raw_metrics:
                profile = self._parse_metric_profile(metric_data)
                result["metrics"].append(profile)

        # Parse logging section
        raw_logging = data.get("logging", [])
        if isinstance(raw_logging, list):
            for log_data in raw_logging:
                config = self._parse_log_config(log_data)
                result["logging"].append(config)

        # Parse tracing section
        raw_tracing = data.get("tracing", [])
        if isinstance(raw_tracing, list):
            for trace_data in raw_tracing:
                config = self._parse_trace_config(trace_data)
                result["tracing"].append(config)

        # Parse OpenTelemetry section
        raw_otel = data.get("opentelemetry", None)
        if raw_otel and isinstance(raw_otel, dict):
            config = self._parse_otel_config(raw_otel)
            result["opentelemetry"] = config

        # Parse log_shipping section
        raw_shipping = data.get("log_shipping", None)
        if raw_shipping and isinstance(raw_shipping, dict):
            config = self._parse_log_shipping_config(raw_shipping)
            result["log_shipping"] = config

        return result

    def _parse_metric_profile(self, data: dict[str, Any]) -> MetricProfile:
        """
        Parse dict thành MetricProfile.

        Args:
            data: Dict chứa thông tin metric profile

        Returns:
            MetricProfile instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="Metric entry phải là YAML mapping",
            )

        # Parse metric type
        type_str = data.get("type", "counter")
        try:
            metric_type = MetricType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-C03_INVALID_METRIC_TYPE,
                metric_type=type_str,
                valid_types=[t.value for t in MetricType],
            )

        return MetricProfile(
            name=data.get("name", ""),
            metric_type=metric_type,
            unit=data.get("unit", ""),
            labels=data.get("labels", {}) if data.get("labels") else {},
            retention_days=data.get("retention_days", 30),
            description=data.get("description", ""),
        )

    def _parse_log_config(self, data: dict[str, Any]) -> StructuredLogConfig:
        """
        Parse dict thành StructuredLogConfig.

        Args:
            data: Dict chứa thông tin log config

        Returns:
            StructuredLogConfig instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="Log entry phải là YAML mapping",
            )

        # Parse log level
        level_str = data.get("log_level", "INFO")
        try:
            log_level = LogLevel(level_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-C03_INVALID_LOG_LEVEL,
                log_level=level_str,
                valid_levels=[l.value for l in LogLevel],
            )

        return StructuredLogConfig(
            service_name=data.get("service_name", ""),
            log_level=log_level,
            include_trace_id=data.get("include_trace_id", True),
            include_span_id=data.get("include_span_id", True),
            output_format=data.get("output_format", "json"),
            fields=data.get("fields", {}) if data.get("fields") else {},
        )

    def _parse_trace_config(self, data: dict[str, Any]) -> TraceConfig:
        """
        Parse dict thành TraceConfig.

        Args:
            data: Dict chứa thông tin trace config

        Returns:
            TraceConfig instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="Trace entry phải là YAML mapping",
            )

        # Parse propagation format
        fmt_str = data.get("propagation_format", "w3c_trace_context")
        try:
            prop_format = TracePropagationFormat(fmt_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-C03_INVALID_TRACE_FORMAT,
                propagation_format=fmt_str,
                valid_formats=[f.value for f in TracePropagationFormat],
            )

        return TraceConfig(
            service_name=data.get("service_name", ""),
            propagation_format=prop_format,
            max_spans=data.get("max_spans", 100),
            sample_rate=data.get("sample_rate", 1.0),
            attributes=data.get("attributes", {}) if data.get("attributes") else {},
        )

    def _parse_otel_config(self, data: dict[str, Any]) -> OpenTelemetryConfig:
        """
        Parse dict thành OpenTelemetryConfig.

        Args:
            data: Dict chứa thông tin OpenTelemetry config

        Returns:
            OpenTelemetryConfig instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="OpenTelemetry config phải là YAML mapping",
            )

        return OpenTelemetryConfig(
            service_name=data.get("service_name", "midicoder"),
            exporter=self._parse_otel_exporter(data.get("exporter", {})),
            sampler_type=self._parse_sampler_type(data.get("sampler_type", "traceid_ratio_based")),
            sampler_rate=data.get("sampler_rate", 1.0),
            resource_attributes=data.get("resource_attributes", {}) if data.get("resource_attributes") else {},
            enable_traces=data.get("enable_traces", True),
            enable_metrics=data.get("enable_metrics", True),
            enable_logs=data.get("enable_logs", True),
            description=data.get("description", ""),
        )

    def _parse_otel_exporter(self, data: dict[str, Any]):
        """Parse OTLP exporter config dict thành OTelExporterConfig."""
        from midicoder.packs.cp_core_observability.models import OTelExporterConfig, OTLPExportProtocol

        if not data or not isinstance(data, dict):
            return OTelExporterConfig()

        return OTelExporterConfig(
            endpoint=data.get("endpoint", "http://localhost:4317"),
            protocol=OTLPExportProtocol(data.get("protocol", "grpc")),
            timeout_ms=data.get("timeout_ms", 10000),
            headers=data.get("headers", {}) if data.get("headers") else {},
            compression=data.get("compression", "none"),
            batch_size=data.get("batch_size", 512),
            batch_timeout_ms=data.get("batch_timeout_ms", 5000),
            retry_on_failure=data.get("retry_on_failure", True),
            max_queue_size=data.get("max_queue_size", 2048),
            description=data.get("description", ""),
        )

    def _parse_sampler_type(self, value: str):
        """Parse sampler type string thành SamplerType enum."""
        from midicoder.packs.cp_core_observability.models import SamplerType

        try:
            return SamplerType(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-C03_INVALID_TRACE_FORMAT,
                sampler_type=value,
                valid_types=[t.value for t in SamplerType],
            )

    def _parse_log_shipping_config(self, data: dict[str, Any]) -> LogShippingConfig:
        """
        Parse dict thành LogShippingConfig.

        Args:
            data: Dict chứa thông tin log shipping config

        Returns:
            LogShippingConfig instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="Log shipping config phải là YAML mapping",
            )

        raw_destinations = data.get("destinations", [])
        destinations = []
        if isinstance(raw_destinations, list):
            for dest_data in raw_destinations:
                destinations.append(self._parse_log_destination(dest_data))

        return LogShippingConfig(
            enabled=data.get("enabled", True),
            destinations=destinations,
            async_shipping=data.get("async_shipping", True),
            max_queue_size=data.get("max_queue_size", 10000),
            drop_on_overflow=data.get("drop_on_overflow", False),
            description=data.get("description", ""),
        )

    def _parse_log_destination(self, data: dict[str, Any]):
        """Parse log destination dict thành LogShippingDestination."""
        from midicoder.packs.cp_core_observability.models import LogDestinationType, LogShippingDestination

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                message="Log destination phải là YAML mapping",
            )

        # Parse destination type
        dest_str = data.get("destination_type", "loki")
        try:
            dest_type = LogDestinationType(dest_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-C03_OBSERVABILITY_PARSE_ERROR,
                destination_type=dest_str,
                valid_types=[t.value for t in LogDestinationType],
            )

        return LogShippingDestination(
            destination_type=dest_type,
            endpoint=data.get("endpoint", ""),
            auth_token=data.get("auth_token", ""),
            flush_interval_ms=data.get("flush_interval_ms", 5000),
            max_batch_size=data.get("max_batch_size", 1000),
            compression=data.get("compression", "gzip"),
            labels=data.get("labels", {}) if data.get("labels") else {},
            filter_pattern=data.get("filter_pattern", ""),
            description=data.get("description", ""),
        )
