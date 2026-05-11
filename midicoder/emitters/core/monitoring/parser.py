# coding: utf-8
"""
Mô-đun parser cho CP16: API & System Monitoring Generator.

Parse YAML DSL thành dict chứa danh sách các model objects:
- dashboards[] → list[DashboardProfile]
- alerts[] → list[AlertRule]
- slis[] → list[SLIDefinition]

Sử dụng:
    parser = MonitoringParser()
    result = parser.parse(yaml_string)
    # result: dict với keys "dashboards", "alerts", "slis"

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    Panel,
    SLIDefinition,
    SLIMetricType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class MonitoringParser:
    """
    Parser cho monitoring DSL (dashboards, alerts, SLIs).

    Parse YAML string thành danh sách các model objects:
    - dashboards[] → list[DashboardProfile]
    - alerts[] → list[AlertRule]
    - slis[] → list[SLIDefinition]

    Usage:
        parser = MonitoringParser()
        result = parser.parse(yaml_string)
        # result: dict with "dashboards", "alerts", "slis" keys
    """

    def parse(self, raw: str) -> dict:
        """
        Parse YAML DSL string thành monitoring config.

        Args:
            raw: YAML string

        Returns:
            Dict với keys: "dashboards", "alerts", "slis"

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP16-010)
        """
        # Trường hợp rỗng hoặc whitespace-only
        if not raw or not raw.strip():
            return {
                "dashboards": [],
                "alerts": [],
                "slis": [],
            }

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message=f"Lỗi parse YAML monitoring: {e}",
                error=str(e),
            )

        # YAML comment-only hoặc null → treat as empty
        if data is None:
            return {
                "dashboards": [],
                "alerts": [],
                "slis": [],
            }

        # YAML phải là dict/mapping
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="DSL monitoring phải là YAML mapping",
            )

        result: dict[str, list] = {
            "dashboards": [],
            "alerts": [],
            "slis": [],
        }

        # Parse dashboards section
        raw_dashboards = data.get("dashboards", [])
        if isinstance(raw_dashboards, list):
            for dashboard_data in raw_dashboards:
                profile = self._parse_dashboard_profile(dashboard_data)
                result["dashboards"].append(profile)

        # Parse alerts section
        raw_alerts = data.get("alerts", [])
        if isinstance(raw_alerts, list):
            for alert_data in raw_alerts:
                rule = self._parse_alert_rule(alert_data)
                result["alerts"].append(rule)

        # Parse SLIs section
        raw_slis = data.get("slis", [])
        if isinstance(raw_slis, list):
            for sli_data in raw_slis:
                definition = self._parse_sli_definition(sli_data)
                result["slis"].append(definition)

        return result

    def _parse_dashboard_profile(self, data: dict[str, Any]) -> DashboardProfile:
        """
        Parse dict thành DashboardProfile.

        Args:
            data: Dict chứa thông tin dashboard profile

        Returns:
            DashboardProfile instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Dashboard entry phải là YAML mapping",
            )

        # Parse dashboard type
        type_str = data.get("type", "system")
        try:
            dashboard_type = DashboardType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                dashboard_type=type_str,
                valid_types=[t.value for t in DashboardType],
            )

        # Parse panels
        panels_data = data.get("panels", [])
        panels: list[Panel] = []
        if isinstance(panels_data, list):
            for panel_data in panels_data:
                panels.append(self._parse_panel(panel_data))

        return DashboardProfile(
            name=data.get("name", ""),
            dashboard_type=dashboard_type,
            refresh_interval_seconds=data.get("refresh_interval_seconds", 30),
            panels=panels,
            description=data.get("description", ""),
        )

    def _parse_panel(self, data: dict[str, Any]) -> Panel:
        """
        Parse dict thành Panel.

        Args:
            data: Dict chứa thông tin panel

        Returns:
            Panel instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Panel entry phải là YAML mapping",
            )

        return Panel(
            name=data.get("name", ""),
            metric_name=data.get("metric_name", ""),
            panel_type=data.get("panel_type", "counter"),
            labels=data.get("labels", {}) if data.get("labels") else {},
        )

    def _parse_alert_rule(self, data: dict[str, Any]) -> AlertRule:
        """
        Parse dict thành AlertRule.

        Args:
            data: Dict chứa thông tin alert rule

        Returns:
            AlertRule instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Alert entry phải là YAML mapping",
            )

        # Parse alert condition
        condition_str = data.get("condition", "greater_than")
        try:
            condition = AlertCondition(condition_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_INVALID_ALERT_CONDITION,
                condition=condition_str,
                valid_conditions=[c.value for c in AlertCondition],
            )

        # Parse alert severity
        severity_str = data.get("severity", "warning")
        try:
            severity = AlertSeverity(severity_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_INVALID_ALERT_SEVERITY,
                severity=severity_str,
                valid_severities=[s.value for s in AlertSeverity],
            )

        return AlertRule(
            name=data.get("name", ""),
            metric_name=data.get("metric_name", ""),
            condition=condition,
            threshold=data.get("threshold", 0.0),
            severity=severity,
            evaluation_interval=data.get("evaluation_interval", 30),
            labels=data.get("labels", {}) if data.get("labels") else {},
            description=data.get("description", ""),
        )

    def _parse_sli_definition(self, data: dict[str, Any]) -> SLIDefinition:
        """
        Parse dict thành SLIDefinition.

        Args:
            data: Dict chứa thông tin SLI definition

        Returns:
            SLIDefinition instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="SLI entry phải là YAML mapping",
            )

        # Parse SLI metric type
        metric_type_str = data.get("metric_type", "availability")
        try:
            metric_type = SLIMetricType(metric_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_INVALID_SLI_METRIC_TYPE,
                metric_type=metric_type_str,
                valid_types=[t.value for t in SLIMetricType],
            )

        return SLIDefinition(
            name=data.get("name", ""),
            metric_type=metric_type,
            metric_name=data.get("metric_name", ""),
            target=data.get("target", 0.999),
            window_seconds=data.get("window_seconds", 3600),
            labels=data.get("labels", {}) if data.get("labels") else {},
            description=data.get("description", ""),
        )
