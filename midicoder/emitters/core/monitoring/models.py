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
                ErrorCode.CP16_EMPTY_DASHBOARD_NAME,
                field="name"
            )
        # Khoảng thời gian refresh phải >= 5 giây
        if self.refresh_interval_seconds < 5:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
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
                ErrorCode.CP16_EMPTY_ALERT_NAME,
                field="name"
            )
        # Khoảng thời gian evaluate phải >= 5 giây
        if self.evaluation_interval < 5:
            EM.raise_error(
                ErrorCode.CP16_ALERT_EVALUATION_INTERVAL_INVALID,
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
                ErrorCode.CP16_EMPTY_DASHBOARD_NAME,
                field="name"
            )
        # Target phải > 0
        if self.target <= 0:
            EM.raise_error(
                ErrorCode.CP16_INVALID_SLI_TARGET,
                target=self.target
            )
        # Cửa sổ thời gian phải >= 60 giây
        if self.window_seconds < 60:
            EM.raise_error(
                ErrorCode.CP16_MONITORING_PARSE_ERROR,
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
                ErrorCode.CP16_EMPTY_PANEL_NAME,
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
