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

from midicoder.emitters.core.observability.models import (
    LogLevel,
    MetricProfile,
    MetricType,
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
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
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
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
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
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                message="Metric entry phải là YAML mapping",
            )

        # Parse metric type
        type_str = data.get("type", "counter")
        try:
            metric_type = MetricType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP15_INVALID_METRIC_TYPE,
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
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                message="Log entry phải là YAML mapping",
            )

        # Parse log level
        level_str = data.get("log_level", "INFO")
        try:
            log_level = LogLevel(level_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP15_INVALID_LOG_LEVEL,
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
                ErrorCode.CP15_OBSERVABILITY_PARSE_ERROR,
                message="Trace entry phải là YAML mapping",
            )

        # Parse propagation format
        fmt_str = data.get("propagation_format", "w3c_trace_context")
        try:
            prop_format = TracePropagationFormat(fmt_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP15_INVALID_TRACE_FORMAT,
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
