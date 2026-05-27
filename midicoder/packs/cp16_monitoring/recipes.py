# coding: utf-8
"""
Recipes for API & System Monitoring Generator (CP16).

Each recipe is a pre-configured factory that produces monitoring models
with concrete settings — representing common deployment patterns.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from .models import (
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


# ---------------------------------------------------------------------------
# Health Check Recipes
# ---------------------------------------------------------------------------


def liveness_check(
    name: str = "liveness",
    path: str = "/health/live",
    interval_seconds: int = 10,
    timeout_seconds: int = 3,
) -> HealthCheck:
    """
    Liveness probe recipe.

    Recommended for: Kubernetes liveness probe — restarts container
    if the process is deadlocked or unresponsive.
    """
    return HealthCheck(
        name=name,
        check_type=HealthCheckType.LIVENESS,
        path=path,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        unhealthy_threshold=3,
        tags={"orchestrator": "kubernetes", "probe": "liveness"},
    )


def readiness_check(
    name: str = "readiness",
    path: str = "/health/ready",
    interval_seconds: int = 10,
    timeout_seconds: int = 3,
) -> HealthCheck:
    """
    Readiness probe recipe.

    Recommended for: Kubernetes readiness probe — removes pod from
    service endpoints if dependencies (DB, cache) are down.
    """
    return HealthCheck(
        name=name,
        check_type=HealthCheckType.READINESS,
        path=path,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        unhealthy_threshold=2,
        tags={"orchestrator": "kubernetes", "probe": "readiness"},
    )


def custom_health_check(
    name: str,
    path: str,
    interval_seconds: int = 30,
    timeout_seconds: int = 10,
    tags: dict | None = None,
) -> HealthCheck:
    """
    Custom health check recipe.

    Recommended for: application-specific health validation
    (e.g., checking message queue connectivity, external API).
    """
    return HealthCheck(
        name=name,
        check_type=HealthCheckType.CUSTOM,
        path=path,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        unhealthy_threshold=3,
        tags=tags or {},
    )


# ---------------------------------------------------------------------------
# Dashboard Recipes
# ---------------------------------------------------------------------------


def system_dashboard(
    name: str = "System Overview",
    refresh_interval_seconds: int = 30,
) -> DashboardProfile:
    """
    System dashboard recipe with default panels for CPU, memory, disk.

    Recommended for: infrastructure monitoring overview.
    """
    panels = [
        Panel(name="cpu_usage", metric_name="system_cpu_percent", panel_type="gauge"),
        Panel(name="memory_usage", metric_name="system_memory_percent", panel_type="gauge"),
        Panel(name="disk_usage", metric_name="system_disk_percent", panel_type="gauge"),
        Panel(name="load_average", metric_name="system_load_average", panel_type="timeseries"),
    ]
    return DashboardProfile(
        name=name,
        dashboard_type=DashboardType.SYSTEM,
        panels=panels,
        refresh_interval_seconds=refresh_interval_seconds,
        description="System resource monitoring dashboard",
    )


def api_dashboard(
    name: str = "API Performance",
    refresh_interval_seconds: int = 15,
) -> DashboardProfile:
    """
    API dashboard recipe with panels for request rate, latency, errors.

    Recommended for: API gateway / backend service monitoring.
    """
    panels = [
        Panel(name="request_rate", metric_name="http_requests_total", panel_type="counter"),
        Panel(name="error_rate", metric_name="http_errors_total", panel_type="gauge"),
        Panel(name="p50_latency", metric_name="http_request_duration_p50", panel_type="gauge"),
        Panel(name="p95_latency", metric_name="http_request_duration_p95", panel_type="gauge"),
        Panel(name="p99_latency", metric_name="http_request_duration_p99", panel_type="gauge"),
    ]
    return DashboardProfile(
        name=name,
        dashboard_type=DashboardType.API,
        panels=panels,
        refresh_interval_seconds=refresh_interval_seconds,
        description="API performance monitoring dashboard",
    )


# ---------------------------------------------------------------------------
# Alert Recipes
# ---------------------------------------------------------------------------


def high_error_rate_alert(
    metric_name: str = "http_errors_total",
    threshold: float = 100.0,
    severity: AlertSeverity = AlertSeverity.CRITICAL,
) -> AlertRule:
    """
    High error rate alert recipe.

    Recommended for: detecting sudden spike in HTTP 5xx errors.
    """
    return AlertRule(
        name="high_error_rate",
        metric_name=metric_name,
        condition=AlertCondition.GREATER_THAN,
        threshold=threshold,
        severity=severity,
        evaluation_interval=30,
        description="Alert when error rate exceeds threshold",
    )


def high_latency_alert(
    metric_name: str = "http_request_duration_p99",
    threshold: float = 1000.0,
    severity: AlertSeverity = AlertSeverity.WARNING,
) -> AlertRule:
    """
    High latency alert recipe.

    Recommended for: detecting degraded API response times.
    """
    return AlertRule(
        name="high_latency_p99",
        metric_name=metric_name,
        condition=AlertCondition.GREATER_THAN,
        threshold=threshold,
        severity=severity,
        evaluation_interval=60,
        description="Alert when p99 latency exceeds threshold",
    )


def low_availability_alert(
    metric_name: str = "service_availability",
    threshold: float = 0.99,
    severity: AlertSeverity = AlertSeverity.CRITICAL,
) -> AlertRule:
    """
    Low availability alert recipe.

    Recommended for: SLO breach detection.
    """
    return AlertRule(
        name="low_availability",
        metric_name=metric_name,
        condition=AlertCondition.LESS_THAN,
        threshold=threshold,
        severity=severity,
        evaluation_interval=60,
        description="Alert when service availability drops below threshold",
    )


def high_cpu_alert(
    metric_name: str = "system_cpu_percent",
    threshold: float = 90.0,
) -> AlertRule:
    """
    High CPU usage alert recipe.
    """
    return AlertRule(
        name="high_cpu_usage",
        metric_name=metric_name,
        condition=AlertCondition.GREATER_THAN,
        threshold=threshold,
        severity=AlertSeverity.WARNING,
        evaluation_interval=30,
        description="Alert when CPU usage exceeds threshold",
    )


def high_memory_alert(
    metric_name: str = "system_memory_percent",
    threshold: float = 85.0,
) -> AlertRule:
    """
    High memory usage alert recipe.
    """
    return AlertRule(
        name="high_memory_usage",
        metric_name=metric_name,
        condition=AlertCondition.GREATER_THAN,
        threshold=threshold,
        severity=AlertSeverity.WARNING,
        evaluation_interval=30,
        description="Alert when memory usage exceeds threshold",
    )


# ---------------------------------------------------------------------------
# SLI Recipes
# ---------------------------------------------------------------------------


def availability_sli(
    name: str = "API Availability",
    metric_name: str = "service_availability",
    target: float = 0.999,
    window_seconds: int = 86400,
) -> SLIDefinition:
    """
    Availability SLI recipe (99.9% uptime).

    Recommended for: core service uptime monitoring.
    """
    return SLIDefinition(
        name=name,
        metric_type=SLIMetricType.AVAILABILITY,
        metric_name=metric_name,
        target=target,
        window_seconds=window_seconds,
        description="Service availability SLI",
    )


def latency_sli(
    name: str = "API Latency P95",
    metric_name: str = "http_request_duration_p95",
    target: float = 500.0,
    window_seconds: int = 3600,
) -> SLIDefinition:
    """
    Latency SLI recipe (p95 < 500ms).

    Recommended for: API response time monitoring.
    """
    return SLIDefinition(
        name=name,
        metric_type=SLIMetricType.LATENCY,
        metric_name=metric_name,
        target=target,
        window_seconds=window_seconds,
        description="API latency SLI (p95)",
    )


def error_rate_sli(
    name: str = "API Error Rate",
    metric_name: str = "http_error_rate",
    target: float = 0.01,
    window_seconds: int = 1800,
) -> SLIDefinition:
    """
    Error rate SLI recipe (< 1% errors).

    Recommended for: API error budget monitoring.
    """
    return SLIDefinition(
        name=name,
        metric_type=SLIMetricType.ERROR_RATE,
        metric_name=metric_name,
        target=target,
        window_seconds=window_seconds,
        description="API error rate SLI",
    )


# ---------------------------------------------------------------------------
# Notification Channel Recipes
# ---------------------------------------------------------------------------


def email_channel(
    name: str = "team-email",
    email: str = "team@example.com",
    severity_filter: list[str] | None = None,
) -> NotificationChannel:
    """
    Email notification channel recipe.
    """
    return NotificationChannel(
        name=name,
        channel_type=NotificationChannelType.EMAIL,
        endpoint=email,
        severity_filter=severity_filter or [],
    )


def slack_channel(
    name: str = "ops-slack",
    webhook_url: str = "https://hooks.slack.com/services/xxx",
    severity_filter: list[str] | None = None,
) -> NotificationChannel:
    """
    Slack notification channel recipe.
    """
    return NotificationChannel(
        name=name,
        channel_type=NotificationChannelType.SLACK,
        endpoint=webhook_url,
        severity_filter=severity_filter or [],
    )


def pagerduty_channel(
    name: str = "pagerduty-critical",
    integration_key: str = "your-pagerduty-integration-key",
    severity_filter: list[str] | None = None,
) -> NotificationChannel:
    """
    PagerDuty notification channel recipe.

    Recommended for: critical alerts that need immediate on-call response.
    """
    return NotificationChannel(
        name=name,
        channel_type=NotificationChannelType.PAGERDUTY,
        endpoint=integration_key,
        severity_filter=severity_filter or ["critical"],
    )


def webhook_channel(
    name: str,
    url: str,
    severity_filter: list[str] | None = None,
) -> NotificationChannel:
    """
    Generic webhook notification channel recipe.
    """
    return NotificationChannel(
        name=name,
        channel_type=NotificationChannelType.WEBHOOK,
        endpoint=url,
        severity_filter=severity_filter or [],
    )


# ---------------------------------------------------------------------------
# Escalation Policy Recipes
# ---------------------------------------------------------------------------


def standard_escalation(
    name: str = "standard-escalation",
    channels: list[str] | None = None,
    timeout_seconds: int = 300,
) -> EscalationPolicy:
    """
    Standard escalation policy: L1 → L2 → L3.

    Recommended for: general incident response.
    """
    return EscalationPolicy(
        name=name,
        levels=["L1-oncall", "L2-engineering", "L3-management"],
        timeout_seconds=timeout_seconds,
        channels=channels or [],
    )


def critical_escalation(
    name: str = "critical-escalation",
    channels: list[str] | None = None,
    timeout_seconds: int = 120,
) -> EscalationPolicy:
    """
    Critical escalation policy: immediate page + fast escalation.

    Recommended for: production-outage scenarios.
    """
    return EscalationPolicy(
        name=name,
        levels=["oncall-primary", "oncall-secondary", "engineering-lead", "vp-engineering"],
        timeout_seconds=timeout_seconds,
        channels=channels or [],
    )


# ---------------------------------------------------------------------------
# SLO Tracking Recipes
# ---------------------------------------------------------------------------


def availability_slo(
    name: str = "API Availability SLO",
    sli_name: str = "API Availability",
    target_percentage: float = 99.9,
) -> SLOTracking:
    """
    Availability SLO recipe (99.9% target, monthly budget).

    Recommended for: core service availability with multi-window burn rate.
    """
    return SLOTracking(
        name=name,
        sli_name=sli_name,
        target_percentage=target_percentage,
        budget_period_seconds=2592000,  # 30 days
        burn_rate=SLOBurnRate.SEVEN_DAY,
        fast_burn_threshold=14.4,
        slow_burn_threshold=1.0,
        pages_enabled=True,
    )


def latency_slo(
    name: str = "API Latency SLO",
    sli_name: str = "API Latency P95",
    target_percentage: float = 99.0,
) -> SLOTracking:
    """
    Latency SLO recipe (99% requests under target latency).
    """
    return SLOTracking(
        name=name,
        sli_name=sli_name,
        target_percentage=target_percentage,
        budget_period_seconds=2592000,  # 30 days
        burn_rate=SLOBurnRate.TWO_DAY,
        fast_burn_threshold=10.0,
        slow_burn_threshold=0.5,
        pages_enabled=False,
    )


def high_reliability_slo(
    name: str = "High Reliability SLO",
    sli_name: str = "API Availability",
    target_percentage: float = 99.99,
) -> SLOTracking:
    """
    High reliability SLO recipe (99.99% target — four nines).

    Recommended for: financial systems, healthcare, mission-critical services.
    """
    return SLOTracking(
        name=name,
        sli_name=sli_name,
        target_percentage=target_percentage,
        budget_period_seconds=2592000,  # 30 days
        burn_rate=SLOBurnRate.ONE_HOUR,
        fast_burn_threshold=14.4,
        slow_burn_threshold=1.0,
        pages_enabled=True,
    )
