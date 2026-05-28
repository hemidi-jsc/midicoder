# coding: utf-8
"""
Mô-đun models cho API & System Monitoring Generator (CP16).

Định nghĩa các dataclass và enum biểu diễn:
- AlertSeverity: Mức độ nghiêm trọng của alert
- AlertCondition: Điều kiện kích hoạt alert
- SLIMetricType: Loại metric cho SLI
- DashboardType: Loại dashboard
- DashboardProfile: Profile cho dashboard — định nghĩa panels và layout
- Panel: Panel trong dashboard
- AlertRule: Alert rule — định nghĩa khi nào fire alert
- FiredAlert: Alert đã được kích hoạt — immutable
- SLIDefinition: SLI Definition — định nghĩa Service Level Indicator
- SLIStatus: Status của SLI tại thời điểm hiện tại

Tất cả models đọc từ CP15 MetricRegistry.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class AlertSeverity(str, Enum):
    """Mức độ nghiêm trọng của alert."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertCondition(str, Enum):
    """Điều kiện kích hoạt alert."""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"


class SLIMetricType(str, Enum):
    """Loại metric cho SLI."""
    AVAILABILITY = "availability"       # Tỷ lệ uptime
    LATENCY = "latency"                 # Độ trễ (p50/p95/p99)
    ERROR_RATE = "error_rate"           # Tỷ lệ lỗi


class DashboardType(str, Enum):
    """Loại dashboard."""
    SYSTEM = "system"
    API = "api"
    BUSINESS = "business"


class HealthCheckType(str, Enum):
    """Loại health check."""
    LIVENESS = "liveness"       # Process còn sống không
    READINESS = "readiness"     # Sẵn sàng nhận traffic chưa
    CUSTOM = "custom"           # Custom check


class NotificationChannelType(str, Enum):
    """Loại kênh thông báo."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    OPSGENIE = "opsgenie"


class SLOBurnRate(str, Enum):
    """Tốc độ tiêu thụ error budget."""
    ONE_HOUR = "1h"
    SIX_HOUR = "6h"
    TWELVE_HOUR = "12h"
    TWO_DAY = "2d"
    SEVEN_DAY = "7d"


# ===========================================================================
# DashboardProfile
# ===========================================================================


@dataclass
class DashboardProfile:
    """Profile cho dashboard — định nghĩa panels và layout.

    Attributes:
        name: Tên dashboard (bắt buộc, không rỗng)
        dashboard_type: Loại dashboard (system/api/business)
        panels: Danh sách panel definitions
        refresh_interval_seconds: Khoảng thời gian refresh (giây)
        description: Mô tả dashboard

    Validation: name không rỗng, refresh_interval >= 5
    """
    name: str
    dashboard_type: DashboardType = DashboardType.SYSTEM
    panels: list = field(default_factory=list)
    refresh_interval_seconds: int = 30
    description: str = ""

    def __post_init__(self) -> None:
        """Validate dashboard profile sau khi khởi tạo."""
        # Tên dashboard không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_DASHBOARD_NAME,
                field="name"
            )
        # Khoảng thời gian refresh phải >= 5 giây
        if self.refresh_interval_seconds < 5:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="refresh_interval_seconds",
                value=self.refresh_interval_seconds,
                minimum=5
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DashboardProfile sang dict format."""
        return {
            "name": self.name,
            "dashboard_type": self.dashboard_type.value,
            "panels": self.panels,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DashboardProfile":
        """Tạo DashboardProfile từ dict."""
        return cls(
            name=data.get("name", ""),
            dashboard_type=DashboardType(data.get("dashboard_type", "system")),
            panels=data.get("panels", []),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 30),
            description=data.get("description", ""),
        )


# ===========================================================================
# AlertRule
# ===========================================================================


@dataclass
class AlertRule:
    """Alert rule — định nghĩa khi nào fire alert.

    Attributes:
        name: Tên alert rule (bắt buộc, không rỗng)
        metric_name: Tên metric để theo dõi (từ CP15 MetricRegistry)
        condition: Điều kiện (greater_than, less_than, equals, not_equals)
        threshold: Ngưỡng kích hoạt
        severity: Mức độ nghiêm trọng (critical/warning/info)
        evaluation_interval: Khoảng thời gian evaluate (giây, >= 5)
        labels: Labels để filter metric
        description: Mô tả alert rule

    Obligation: evaluation_interval >= 5 (alert freshness)
    """
    name: str
    metric_name: str
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    evaluation_interval: int = 30
    labels: dict = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate alert rule sau khi khởi tạo."""
        # Tên alert không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_ALERT_NAME,
                field="name"
            )
        # Khoảng thời gian evaluate phải >= 5 giây
        if self.evaluation_interval < 5:
            EM.raise_error(
                ErrorCode.MDC-F15_ALERT_EVALUATION_INTERVAL_INVALID,
                evaluation_interval=self.evaluation_interval,
                minimum=5
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển AlertRule sang dict format."""
        return {
            "name": self.name,
            "metric_name": self.metric_name,
            "condition": self.condition.value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "evaluation_interval": self.evaluation_interval,
            "labels": self.labels,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertRule":
        """Tạo AlertRule từ dict."""
        return cls(
            name=data.get("name", ""),
            metric_name=data.get("metric_name", ""),
            condition=AlertCondition(data.get("condition", "greater_than")),
            threshold=data.get("threshold", 0.0),
            severity=AlertSeverity(data.get("severity", "warning")),
            evaluation_interval=data.get("evaluation_interval", 30),
            labels=data.get("labels", {}),
            description=data.get("description", ""),
        )


# ===========================================================================
# SLIDefinition
# ===========================================================================


@dataclass
class SLIDefinition:
    """SLI Definition — định nghĩa Service Level Indicator.

    Attributes:
        name: Tên SLI (bắt buộc, không rỗng)
        metric_type: Loại metric (availability/latency/error_rate)
        metric_name: Tên metric từ CP15 MetricRegistry
        target: Mục tiêu (0.0 - 1.0 cho availability, ms cho latency, % cho error_rate)
        window_seconds: Cửa sổ thời gian để tính toán
        labels: Labels để filter metric
        description: Mô tả SLI

    Validation: target > 0, window_seconds >= 60
    """
    name: str
    metric_type: SLIMetricType
    metric_name: str
    target: float
    window_seconds: int = 3600
    labels: dict = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate SLI definition sau khi khởi tạo."""
        # Tên SLI không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_SLI_NAME,
                field="name"
            )
        # Target phải > 0
        if self.target <= 0:
            EM.raise_error(
                ErrorCode.MDC-F15_INVALID_SLI_TARGET,
                target=self.target
            )
        # Cửa sổ thời gian phải >= 60 giây
        if self.window_seconds < 60:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="window_seconds",
                value=self.window_seconds,
                minimum=60
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển SLIDefinition sang dict format."""
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "metric_name": self.metric_name,
            "target": self.target,
            "window_seconds": self.window_seconds,
            "labels": self.labels,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SLIDefinition":
        """Tạo SLIDefinition từ dict."""
        return cls(
            name=data.get("name", ""),
            metric_type=SLIMetricType(data.get("metric_type", "availability")),
            metric_name=data.get("metric_name", ""),
            target=data.get("target", 0.0),
            window_seconds=data.get("window_seconds", 3600),
            labels=data.get("labels", {}),
            description=data.get("description", ""),
        )


# ===========================================================================
# Panel
# ===========================================================================


@dataclass
class Panel:
    """Panel trong dashboard.

    Attributes:
        name: Tên panel
        metric_name: Tên metric (từ CP15 MetricRegistry)
        panel_type: Loại panel (counter/gauge/histogram/table)
        labels: Labels để filter metric
    """
    name: str
    metric_name: str
    panel_type: str = "counter"
    labels: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate panel sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_PANEL_NAME,
                field="name"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Panel sang dict format."""
        return {
            "name": self.name,
            "metric_name": self.metric_name,
            "panel_type": self.panel_type,
            "labels": self.labels,
        }


# ===========================================================================
# FiredAlert
# ===========================================================================


@dataclass(frozen=True)
class FiredAlert:
    """Alert đã được kích hoạt — immutable.

    Attributes:
        rule_name: Tên alert rule
        metric_name: Tên metric
        current_value: Giá trị hiện tại của metric
        threshold: Ngưỡng
        severity: Mức độ
        fired_at: Thời điểm fire
        condition: Điều kiện
    """
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    fired_at: datetime
    condition: str

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FiredAlert sang dict format."""
        return {
            "rule_name": self.rule_name,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "severity": self.severity,
            "fired_at": self.fired_at.isoformat(),
            "condition": self.condition,
        }


# ===========================================================================
# SLIStatus
# ===========================================================================


@dataclass
class SLIStatus:
    """Status của một SLI tại thời điểm hiện tại.

    Attributes:
        sli_name: Tên SLI
        metric_type: Loại metric
        current_value: Giá trị hiện tại
        target: Mục tiêu
        is_healthy: Có đạt target không
        evaluated_at: Thời điểm đánh giá
    """
    sli_name: str
    metric_type: str
    current_value: float
    target: float
    is_healthy: bool
    evaluated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Chuyển SLIStatus sang dict format."""
        return {
            "sli_name": self.sli_name,
            "metric_type": self.metric_type,
            "current_value": self.current_value,
            "target": self.target,
            "is_healthy": self.is_healthy,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


# ===========================================================================
# HealthCheck
# ===========================================================================


@dataclass
class HealthCheck:
    """Định nghĩa health check cho service.

    Attributes:
        name: Tên health check (bắt buộc, không rỗng)
        check_type: Loại check (liveness/readiness/custom)
        path: HTTP path để check (vd: /health, /ready)
        interval_seconds: Khoảng thời gian check (giây, >= 5)
        timeout_seconds: Thời gian chờ response (giây, >= 1)
        unhealthy_threshold: Số lần fail liên tiếp để đánh unhealthy
        tags: Tags để group health checks
    """
    name: str
    check_type: HealthCheckType = HealthCheckType.LIVENESS
    path: str = "/health"
    interval_seconds: int = 10
    timeout_seconds: int = 5
    unhealthy_threshold: int = 3
    tags: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate health check sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_HEALTH_CHECK_NAME,
                field="name"
            )
        if not self.path.startswith("/"):
            EM.raise_error(
                ErrorCode.MDC-F15_INVALID_HEALTH_CHECK_PATH,
                path=self.path
            )
        if self.interval_seconds < 5:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="interval_seconds",
                value=self.interval_seconds,
                minimum=5
            )
        if self.timeout_seconds < 1:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="timeout_seconds",
                value=self.timeout_seconds,
                minimum=1
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển HealthCheck sang dict format."""
        return {
            "name": self.name,
            "check_type": self.check_type.value,
            "path": self.path,
            "interval_seconds": self.interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "unhealthy_threshold": self.unhealthy_threshold,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthCheck":
        """Tạo HealthCheck từ dict."""
        return cls(
            name=data.get("name", ""),
            check_type=HealthCheckType(data.get("check_type", "liveness")),
            path=data.get("path", "/health"),
            interval_seconds=data.get("interval_seconds", 10),
            timeout_seconds=data.get("timeout_seconds", 5),
            unhealthy_threshold=data.get("unhealthy_threshold", 3),
            tags=data.get("tags", {}),
        )


# ===========================================================================
# NotificationChannel
# ===========================================================================


@dataclass
class NotificationChannel:
    """Kênh thông báo cho alert.

    Attributes:
        name: Tên channel (bắt buộc, không rỗng)
        channel_type: Loại kênh (email/slack/webhook/pagerduty/opsgenie)
        endpoint: Địa chỉ endpoint (email address, webhook URL, Slack channel, ...)
        severity_filter: Chỉ nhận severity nào (rỗng = nhận tất cả)
        enabled: Có bật channel không
    """
    name: str
    channel_type: NotificationChannelType
    endpoint: str
    severity_filter: list[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate notification channel sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_ALERT_NAME,
                field="name"
            )
        if not self.endpoint or not self.endpoint.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="endpoint",
                message="Endpoint không được để trống"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển NotificationChannel sang dict format."""
        return {
            "name": self.name,
            "channel_type": self.channel_type.value,
            "endpoint": self.endpoint,
            "severity_filter": self.severity_filter,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationChannel":
        """Tạo NotificationChannel từ dict."""
        return cls(
            name=data.get("name", ""),
            channel_type=NotificationChannelType(data.get("channel_type", "email")),
            endpoint=data.get("endpoint", ""),
            severity_filter=data.get("severity_filter", []),
            enabled=data.get("enabled", True),
        )


# ===========================================================================
# EscalationPolicy
# ===========================================================================


@dataclass
class EscalationPolicy:
    """Chính sách upgrade alert.

    Attributes:
        name: Tên policy (bắt buộc, không rỗng)
        levels: Danh sách escalation levels (từ thấp đến cao)
        timeout_seconds: Thời gian không respond để escalate (giây, >= 60)
        channels: Danh sách channel references
    """
    name: str
    levels: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    channels: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate escalation policy sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_ESCALATION_NAME,
                field="name"
            )
        if self.timeout_seconds < 60:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="timeout_seconds",
                value=self.timeout_seconds,
                minimum=60
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EscalationPolicy sang dict format."""
        return {
            "name": self.name,
            "levels": self.levels,
            "timeout_seconds": self.timeout_seconds,
            "channels": self.channels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationPolicy":
        """Tạo EscalationPolicy từ dict."""
        return cls(
            name=data.get("name", ""),
            levels=data.get("levels", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            channels=data.get("channels", []),
        )


# ===========================================================================
# SLOTracking
# ===========================================================================


@dataclass
class SLOTracking:
    """Theo dõi SLO — Service Level Objective.

    Khác với SLIDefinition (chỉ đo 1 metric), SLOTracking định nghĩa
    error budget, burn rate detection, và multi-window alerting.

    Attributes:
        name: Tên SLO (bắt buộc, không rỗng)
        sli_name: Reference đến SLIDefinition
        target_percentage: Mục tiêu % (vd: 99.9)
        budget_period_seconds: Chu kỳ budget (vd: 1 tháng = 2592000)
        burn_rate: Tốc độ tiêu thụ budget để detect
        fast_burn_threshold: Ngưỡng fast burn (số lần nhân với base rate)
        slow_burn_threshold: Ngưỡng slow burn (số lần nhân với base rate)
        pages_enabled: Có gửi page không (cho fast burn)
    """
    name: str
    sli_name: str
    target_percentage: float
    budget_period_seconds: int = 2592000
    burn_rate: SLOBurnRate = SLOBurnRate.SEVEN_DAY
    fast_burn_threshold: float = 14.4
    slow_burn_threshold: float = 1.0
    pages_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate SLO tracking sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_SLO_NAME,
                field="name"
            )
        if not (0 < self.target_percentage <= 100):
            EM.raise_error(
                ErrorCode.MDC-F15_INVALID_SLO_TARGET,
                target=self.target_percentage,
                valid_range="0 < target <= 100"
            )
        if self.budget_period_seconds < 3600:
            EM.raise_error(
                ErrorCode.MDC-F15_MONITORING_PARSE_ERROR,
                field="budget_period_seconds",
                value=self.budget_period_seconds,
                minimum=3600
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển SLOTracking sang dict format."""
        return {
            "name": self.name,
            "sli_name": self.sli_name,
            "target_percentage": self.target_percentage,
            "budget_period_seconds": self.budget_period_seconds,
            "burn_rate": self.burn_rate.value,
            "fast_burn_threshold": self.fast_burn_threshold,
            "slow_burn_threshold": self.slow_burn_threshold,
            "pages_enabled": self.pages_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SLOTracking":
        """Tạo SLOTracking từ dict."""
        return cls(
            name=data.get("name", ""),
            sli_name=data.get("sli_name", ""),
            target_percentage=data.get("target_percentage", 99.9),
            budget_period_seconds=data.get("budget_period_seconds", 2592000),
            burn_rate=SLOBurnRate(data.get("burn_rate", "7d")),
            fast_burn_threshold=data.get("fast_burn_threshold", 14.4),
            slow_burn_threshold=data.get("slow_burn_threshold", 1.0),
            pages_enabled=data.get("pages_enabled", True),
        )


# ===========================================================================
# CP17 — BI Analytics Models (merged from cp17_bi_analytics)
# ===========================================================================


class AnalyticsSourceType(str, Enum):
    """Nguồn dữ liệu cho analytics model."""
    METRIC_REGISTRY = "metric_registry"  # Đọc từ CP15 MetricRegistry
    DATABASE = "database"                # Đọc từ database/warehouse
    EXTERNAL_API = "external_api"        # Đọc từ API bên ngoài


class AggregationType(str, Enum):
    """Loại aggregation cho analytics query."""
    SUM = "sum"         # Tổng
    AVERAGE = "average" # Trung bình
    COUNT = "count"     # Đếm
    MAX = "max"         # Tối đa
    MIN = "min"         # Tối thiểu


class VisualizationType(str, Enum):
    """Loại visualization cho dashboard widget."""
    LINE_CHART = "line_chart"  # Biểu đồ đường
    BAR_CHART = "bar_chart"    # Biểu đồ cột
    PIE_CHART = "pie_chart"    # Biểu đồ tròn
    GAUGE = "gauge"            # Đồng hồ
    TABLE = "table"            # Bảng dữ liệu


class ReportFrequency(str, Enum):
    """Tần suất chạy report tự động."""
    HOURLY = "hourly"   # Mỗi giờ
    DAILY = "daily"     # Mỗi ngày
    WEEKLY = "weekly"   # Mỗi tuần
    MONTHLY = "monthly" # Mỗi tháng


class ReportFormat(str, Enum):
    """Định dạng output của report."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"


class SchedulePolicy(str, Enum):
    """Chính sách lập lịch cho report."""
    ONCE = "once"                     # Chạy một lần tại next_run
    HOURLY = "hourly"                 # Mỗi giờ
    DAILY = "daily"                   # Mỗi ngày
    WEEKLY = "weekly"                 # Mỗi tuần
    MONTHLY = "monthly"               # Mỗi tháng


@dataclass
class AnalyticsModel:
    """Analytics model — định nghĩa metrics, filters, aggregations cho analytics query.

    Attributes:
        name: Tên model (bắt buộc, không rỗng)
        source_type: Nguồn dữ liệu (metric_registry, database, external_api)
        metric_names: Danh sách metric names từ CP15 MetricRegistry
        filters: Các filter fields mặc định
        aggregations: Các aggregation types mặc định
        max_stale_seconds: Khoảng thời gian tối đa trước khi query bị stale (giây)
        description: Mô tả model

    Obligation: data freshness — query không stale hơn max_stale_seconds
    """
    name: str
    source_type: AnalyticsSourceType = AnalyticsSourceType.METRIC_REGISTRY
    metric_names: list = field(default_factory=list)
    filters: dict = field(default_factory=dict)
    aggregations: list = field(default_factory=list)
    max_stale_seconds: int = 300
    description: str = ""

    def __post_init__(self) -> None:
        """Validate analytics model sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_MODEL_NAME,
                field="name"
            )
        if self.max_stale_seconds < 1:
            EM.raise_error(
                ErrorCode.MDC-F15_INVALID_STALE_SECONDS,
                max_stale_seconds=self.max_stale_seconds,
                minimum=1
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển AnalyticsModel sang dict format."""
        return {
            "name": self.name,
            "source_type": self.source_type.value,
            "metric_names": self.metric_names,
            "filters": self.filters,
            "aggregations": self.aggregations,
            "max_stale_seconds": self.max_stale_seconds,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalyticsModel":
        """Tạo AnalyticsModel từ dict."""
        return cls(
            name=data.get("name", ""),
            source_type=AnalyticsSourceType(data.get("source_type", "metric_registry")),
            metric_names=data.get("metric_names", []),
            filters=data.get("filters", {}),
            aggregations=data.get("aggregations", []),
            max_stale_seconds=data.get("max_stale_seconds", 300),
            description=data.get("description", ""),
        )


@dataclass
class DashboardDefinition:
    """Dashboard definition — định nghĩa BI dashboard với widgets.

    Attributes:
        name: Tên dashboard (bắt buộc, không rỗng)
        title: Tiêu đề hiển thị
        description: Mô tả dashboard
        widgets: Danh sách widget definitions (dict)
        refresh_interval_seconds: Khoảng thời gian refresh (giây, >= 5)
        created_at: Thời điểm tạo
        metadata: Metadata tùy chỉnh

    Validation: name không rỗng, refresh_interval >= 5
    """
    name: str
    title: str = ""
    description: str = ""
    widgets: list = field(default_factory=list)
    refresh_interval_seconds: int = 30
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate dashboard definition sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_DASHBOARD_NAME,
                field="name"
            )
        if self.refresh_interval_seconds < 5:
            EM.raise_error(
                ErrorCode.MDC-F15_INVALID_REFRESH_INTERVAL,
                refresh_interval_seconds=self.refresh_interval_seconds,
                minimum=5
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DashboardDefinition sang dict format."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "widgets": self.widgets,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DashboardDefinition":
        """Tạo DashboardDefinition từ dict."""
        created_at_str = data.get("created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc)
        return cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            widgets=data.get("widgets", []),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 30),
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class ScheduledReport:
    """Report đã lập lịch — định nghĩa metadata và schedule cho report tự động.

    Attributes:
        name: Tên report (bắt buộc, không rỗng)
        title: Tiêu đề report hiển thị
        model_name: Tên analytics model để query dữ liệu
        schedule_policy: Chính sách lập lịch (once/hourly/daily/weekly/monthly)
        frequency: Tần suất chạy report (hourly/daily/weekly/monthly)
        next_run: Thời điểm chạy tiếp theo
        format: Định dạng output (json/csv/pdf/html/markdown)
        output_format: Định dạng output (alias của format, dùng trong parser)
        recipients: Danh sách người nhận report
        description: Mô tả report
        parameters: Parameters tùy chỉnh cho report

    Validation: name không rỗng, model_name không rỗng, next_run phải có giá trị
    """
    name: str
    title: str = ""
    model_name: str = ""
    schedule_policy: SchedulePolicy = SchedulePolicy.ONCE
    frequency: ReportFrequency = ReportFrequency.DAILY
    next_run: datetime | None = None
    format: ReportFormat = ReportFormat.JSON
    output_format: str = "json"
    recipients: list = field(default_factory=list)
    description: str = ""
    parameters: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate scheduled report sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.MDC-F15_EMPTY_REPORT_NAME,
                field="name"
            )
        if self.next_run is None:
            # Tự động gán next_run là now cho trường hợp parser tạo ra
            object.__setattr__(self, 'next_run', datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ScheduledReport sang dict format."""
        return {
            "name": self.name,
            "title": self.title,
            "model_name": self.model_name,
            "schedule_policy": self.schedule_policy.value,
            "frequency": self.frequency.value,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "format": self.format.value,
            "output_format": self.output_format,
            "recipients": self.recipients,
            "description": self.description,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduledReport":
        """Tạo ScheduledReport từ dict."""
        next_run_str = data.get("next_run")
        next_run = datetime.fromisoformat(next_run_str) if next_run_str else None
        return cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            model_name=data.get("model_name", ""),
            schedule_policy=SchedulePolicy(data.get("schedule_policy", "once")),
            frequency=ReportFrequency(data.get("frequency", "daily")),
            next_run=next_run,
            format=ReportFormat(data.get("format", "json")),
            output_format=data.get("output_format", "json"),
            recipients=data.get("recipients", []),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
        )
