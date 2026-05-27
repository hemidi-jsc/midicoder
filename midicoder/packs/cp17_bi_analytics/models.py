# coding: utf-8
"""
Mô-đun models cho Business Intelligence & Analytics Generator (CP17).

Định nghĩa các dataclass và enum biểu diễn:
- AnalyticsModel: Analytics model — định nghĩa metrics, filters, aggregations
- DashboardDefinition: Dashboard definition — định nghĩa BI dashboard
- ScheduledReport: Report đã lập lịch — định nghĩa metadata và schedule
- ReportFormat: Enum cho định dạng output của report

Tất cả models đọc dữ liệu từ CP15 MetricRegistry.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
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


# ===========================================================================
# AnalyticsModel
# ===========================================================================


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
        # Tên model không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP17_EMPTY_MODEL_NAME,
                field="name"
            )
        # Thời gian stale phải >= 1 giây
        if self.max_stale_seconds < 1:
            EM.raise_error(
                ErrorCode.CP17_INVALID_STALE_SECONDS,
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


# ===========================================================================
# DashboardDefinition
# ===========================================================================


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
        # Tên dashboard không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP17_EMPTY_DASHBOARD_NAME,
                field="name"
            )
        # Khoảng thời gian refresh phải >= 5 giây
        if self.refresh_interval_seconds < 5:
            EM.raise_error(
                ErrorCode.CP17_INVALID_REFRESH_INTERVAL,
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


# ===========================================================================
# ScheduledReport
# ===========================================================================


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
        # Tên report không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP17_EMPTY_REPORT_NAME,
                field="name"
            )
        # next_run phải có giá trị (parser có thể tạo report không có next_run)
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
