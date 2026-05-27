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

from midicoder.packs.cp16_monitoring.models import (
    AlertCondition,
    AlertRule,
    AlertSeverity,
    DashboardProfile,
    DashboardType,
    EscalationPolicy,
    HealthCheck,
    HealthCheckType,
    NotificationChannel,
    NotificationChannelType,
    Panel,
    SLIDefinition,
    SLIMetricType,
    SLOBurnRate,
    SLOTracking,
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
            Dict với keys: "dashboards", "alerts", "slis",
                          "health_checks", "notification_channels",
                          "escalation_policies", "slo_tracking"

        Raises:
            MidicoderError: Nếu YAML không hợp lệ (MDC-CP16-010)
        """
        # Trường hợp rỗng hoặc whitespace-only
        if not raw or not raw.strip():
            return {
                "dashboards": [],
                "alerts": [],
                "slis": [],
                "health_checks": [],
                "notification_channels": [],
                "escalation_policies": [],
                "slo_tracking": [],
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
                "health_checks": [],
                "notification_channels": [],
                "escalation_policies": [],
                "slo_tracking": [],
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
            "health_checks": [],
            "notification_channels": [],
            "escalation_policies": [],
            "slo_tracking": [],
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

        # Parse health_checks section
        raw_health_checks = data.get("health_checks", [])
        if isinstance(raw_health_checks, list):
            for hc_data in raw_health_checks:
                hc = self._parse_health_check(hc_data)
                result["health_checks"].append(hc)

        # Parse notification_channels section
        raw_channels = data.get("notification_channels", [])
        if isinstance(raw_channels, list):
            for ch_data in raw_channels:
                ch = self._parse_notification_channel(ch_data)
                result["notification_channels"].append(ch)

        # Parse escalation_policies section
        raw_escalations = data.get("escalation_policies", [])
        if isinstance(raw_escalations, list):
            for esc_data in raw_escalations:
                esc = self._parse_escalation_policy(esc_data)
                result["escalation_policies"].append(esc)

        # Parse slo_tracking section
        raw_slos = data.get("slo_tracking", [])
        if isinstance(raw_slos, list):
            for slo_data in raw_slos:
                slo = self._parse_slo_tracking(slo_data)
                result["slo_tracking"].append(slo)

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

    # ------------------------------------------------------------------
    # Health Check parsing
    # ------------------------------------------------------------------

    def _parse_health_check(self, data: dict[str, Any]) -> HealthCheck:
        """
        Parse dict thành HealthCheck.

        Args:
            data: Dict chứa thông tin health check

        Returns:
            HealthCheck instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Health check entry phải là YAML mapping",
            )

        # Parse health check type
        type_str = data.get("check_type", "liveness")
        try:
            check_type = HealthCheckType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                check_type=type_str,
                valid_types=[t.value for t in HealthCheckType],
            )

        return HealthCheck(
            name=data.get("name", ""),
            check_type=check_type,
            path=data.get("path", "/health"),
            interval_seconds=data.get("interval_seconds", 10),
            timeout_seconds=data.get("timeout_seconds", 5),
            unhealthy_threshold=data.get("unhealthy_threshold", 3),
            tags=data.get("tags", {}) if data.get("tags") else {},
        )

    # ------------------------------------------------------------------
    # Notification Channel parsing
    # ------------------------------------------------------------------

    def _parse_notification_channel(self, data: dict[str, Any]) -> NotificationChannel:
        """
        Parse dict thành NotificationChannel.

        Args:
            data: Dict chứa thông tin notification channel

        Returns:
            NotificationChannel instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Notification channel entry phải là YAML mapping",
            )

        # Parse channel type
        type_str = data.get("channel_type", "email")
        try:
            channel_type = NotificationChannelType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_INVALID_NOTIFICATION_CHANNEL_TYPE,
                channel_type=type_str,
                valid_types=[t.value for t in NotificationChannelType],
            )

        return NotificationChannel(
            name=data.get("name", ""),
            channel_type=channel_type,
            endpoint=data.get("endpoint", ""),
            severity_filter=data.get("severity_filter", []),
            enabled=data.get("enabled", True),
        )

    # ------------------------------------------------------------------
    # Escalation Policy parsing
    # ------------------------------------------------------------------

    def _parse_escalation_policy(self, data: dict[str, Any]) -> EscalationPolicy:
        """
        Parse dict thành EscalationPolicy.

        Args:
            data: Dict chứa thông tin escalation policy

        Returns:
            EscalationPolicy instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="Escalation policy entry phải là YAML mapping",
            )

        return EscalationPolicy(
            name=data.get("name", ""),
            levels=data.get("levels", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            channels=data.get("channels", []),
        )

    # ------------------------------------------------------------------
    # SLO Tracking parsing
    # ------------------------------------------------------------------

    def _parse_slo_tracking(self, data: dict[str, Any]) -> SLOTracking:
        """
        Parse dict thành SLOTracking.

        Args:
            data: Dict chứa thông tin SLO tracking

        Returns:
            SLOTracking instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                message="SLO tracking entry phải là YAML mapping",
            )

        # Parse burn rate
        burn_str = data.get("burn_rate", "7d")
        try:
            burn_rate = SLOBurnRate(burn_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
                burn_rate=burn_str,
                valid_rates=[r.value for r in SLOBurnRate],
            )

        return SLOTracking(
            name=data.get("name", ""),
            sli_name=data.get("sli_name", ""),
            target_percentage=data.get("target_percentage", 99.9),
            budget_period_seconds=data.get("budget_period_seconds", 2592000),
            burn_rate=burn_rate,
            fast_burn_threshold=data.get("fast_burn_threshold", 14.4),
            slow_burn_threshold=data.get("slow_burn_threshold", 1.0),
            pages_enabled=data.get("pages_enabled", True),
        )
