# coding: utf-8
"""
Mô-đun parser cho CP17: Business Intelligence & Analytics Generator.

Parse YAML DSL thành dict chứa danh sách các model objects:
- analytics_models[] → list[AnalyticsModel]
- dashboards[] → list[DashboardDefinition]
- reports[] → list[ScheduledReport]

Sử dụng:
    parser = AnalyticsParser()
    result = parser.parse(yaml_string)
    # result: dict với keys "analytics_models", "dashboards", "reports"

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp17_bi_analytics.models import (
    AggregationType,
    AnalyticsModel,
    AnalyticsSourceType,
    DashboardDefinition,
    ReportFrequency,
    ScheduledReport,
    VisualizationType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AnalyticsParser:
    """
    Parser cho analytics DSL (models, dashboards, reports).

    Phân tích chuỗi YAML thành danh sách các đối tượng model:
    - analytics_models[] → list[AnalyticsModel]
    - dashboards[] → list[DashboardDefinition]
    - reports[] → list[ScheduledReport]

    Usage:
        parser = AnalyticsParser()
        result = parser.parse(yaml_string)
        # result: dict với các khóa "analytics_models", "dashboards", "reports"
    """

    def parse(self, raw: str) -> dict:
        """
        Parse YAML DSL string thành analytics config.

        Args:
            raw: Chuỗi YAML đầu vào

        Returns:
            Dict với các khóa: "analytics_models", "dashboards", "reports"

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP17-010)
        """
        # Trường hợp rỗng hoặc whitespace-only
        if not raw or not raw.strip():
            return {
                "analytics_models": [],
                "dashboards": [],
                "reports": [],
            }

        # Phân tích YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message=f"Lỗi parse YAML analytics: {e}",
                error=str(e),
            )

        # YAML comment-only hoặc null → treat as empty
        if data is None:
            return {
                "analytics_models": [],
                "dashboards": [],
                "reports": [],
            }

        # YAML phải là dict/mapping
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message="DSL analytics phải là YAML mapping",
            )

        result: dict[str, list] = {
            "analytics_models": [],
            "dashboards": [],
            "reports": [],
        }

        # Phân tích phần analytics_models
        raw_models = data.get("analytics_models", [])
        if isinstance(raw_models, list):
            for model_data in raw_models:
                model = self._parse_analytics_model(model_data)
                result["analytics_models"].append(model)

        # Phân tích phần dashboards
        raw_dashboards = data.get("dashboards", [])
        if isinstance(raw_dashboards, list):
            for dashboard_data in raw_dashboards:
                dashboard = self._parse_dashboard_definition(dashboard_data)
                result["dashboards"].append(dashboard)

        # Phân tích phần reports
        raw_reports = data.get("reports", [])
        if isinstance(raw_reports, list):
            for report_data in raw_reports:
                report = self._parse_scheduled_report(report_data)
                result["reports"].append(report)

        return result

    def _parse_analytics_model(self, data: dict[str, Any]) -> AnalyticsModel:
        """
        Parse dict thành AnalyticsModel.

        Args:
            data: Dict chứa thông tin analytics model

        Returns:
            Thể hiện AnalyticsModel

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message="Analytics model entry phải là YAML mapping",
            )

        # Phân tích source_type
        source_type_str = data.get("source_type", "metric_registry")
        try:
            source_type = AnalyticsSourceType(source_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP17_INVALID_SOURCE_TYPE,
                source_type=source_type_str,
                valid_types=[t.value for t in AnalyticsSourceType],
            )

        # Phân tích aggregations
        aggregation_list = data.get("aggregations", [])
        aggregations: list[AggregationType] = []
        if isinstance(aggregation_list, list):
            for agg_str in aggregation_list:
                try:
                    aggregations.append(AggregationType(agg_str))
                except ValueError:
                    EM.raise_error(
                        ErrorCode.CP17_INVALID_AGGREGATION_TYPE,
                        aggregation=agg_str,
                        valid_aggregations=[a.value for a in AggregationType],
                    )

        return AnalyticsModel(
            name=data.get("name", ""),
            source_type=source_type,
            metric_names=data.get("metric_names", []),
            aggregations=aggregations,
            max_stale_seconds=data.get("max_stale_seconds", 300),
        )

    def _parse_dashboard_definition(self, data: dict[str, Any]) -> DashboardDefinition:
        """
        Parse dict thành DashboardDefinition.

        Args:
            data: Dict chứa thông tin dashboard definition

        Returns:
            Thể hiện DashboardDefinition

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message="Dashboard entry phải là YAML mapping",
            )

        # Phân tích widgets
        widgets_data = data.get("widgets", [])
        widgets: list[dict[str, Any]] = []
        if isinstance(widgets_data, list):
            for widget_data in widgets_data:
                widgets.append(self._parse_widget(widget_data))

        return DashboardDefinition(
            name=data.get("name", ""),
            title=data.get("title", ""),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 30),
            widgets=widgets,
        )

    def _parse_widget(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse dict thành widget dict với visualization_type enum.

        Args:
            data: Dict chứa thông tin widget

        Returns:
            Dict với widget info, visualization_type đã convert sang enum

        Raises:
            MidicoderError: Nếu visualization_type không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message="Widget entry phải là YAML mapping",
            )

        # Phân tích visualization_type
        viz_type_str = data.get("visualization_type", "line_chart")
        try:
            viz_type = VisualizationType(viz_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP17_INVALID_VISUALIZATION_TYPE,
                visualization_type=viz_type_str,
                valid_types=[t.value for t in VisualizationType],
            )

        return {
            "name": data.get("name", ""),
            "visualization_type": viz_type,
            "metric_name": data.get("metric_name", ""),
        }

    def _parse_scheduled_report(self, data: dict[str, Any]) -> ScheduledReport:
        """
        Parse dict thành ScheduledReport.

        Args:
            data: Dict chứa thông tin scheduled report

        Returns:
            Thể hiện ScheduledReport

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP17_ANALYTICS_PARSE_ERROR,
                message="Report entry phải là YAML mapping",
            )

        # Phân tích frequency
        frequency_str = data.get("frequency", "daily")
        try:
            frequency = ReportFrequency(frequency_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP17_INVALID_REPORT_FREQUENCY,
                frequency=frequency_str,
                valid_frequencies=[f.value for f in ReportFrequency],
            )

        return ScheduledReport(
            name=data.get("name", ""),
            title=data.get("title", ""),
            model_name=data.get("model_name", ""),
            frequency=frequency,
            output_format=data.get("output_format", "json"),
            recipients=data.get("recipients", []),
        )
