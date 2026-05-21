# coding: utf-8
"""
Mô-đun models cho Report & Document Generator (CP34).

Định nghĩa các dataclass biểu diễn:
- ReportFormat: Enum định dạng output (PDF, Excel, CSV)
- ReportLayout: Enum layout (table, dashboard, list)
- AggregationFunc: Enum hàm aggregation (SUM, COUNT, AVG, MIN, MAX)
- BatchJobStatus: Enum trạng thái batch job
- ReportSpec: Spec cho 1 report (từ DSL YAML)
- BatchJob: Job để xử lý batch document async
- ReportCollection: Collection chứa nhiều report specs

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ReportFormat(str, Enum):
    """Enum định dạng output của report."""
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"


class ReportLayout(str, Enum):
    """Enum layout hiển thị report."""
    TABLE = "table"
    DASHBOARD = "dashboard"
    LIST = "list"


class AggregationFunc(str, Enum):
    """Enum hàm aggregation cho report."""
    SUM = "SUM"
    COUNT = "COUNT"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"


class BatchJobStatus(str, Enum):
    """Enum trạng thái batch job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ===========================================================================
# ReportSpec
# ===========================================================================


@dataclass
class ReportSpec:
    """
    Spec cho 1 report — parse từ DSL YAML.

    Attributes:
        id: Định danh duy nhất của report
        name: Tên hiển thị
        entity: Entity source (link CP01)
        fields: Danh sách fields cần include trong report
        filter: Query filter (dict, link CP08)
        format: Định dạng output (pdf, xlsx, csv)
        layout: Layout hiển thị (table, dashboard, list)
        group_by: Nhóm data theo field nào
        aggregations: Danh sách aggregation functions
        description: Mô tả report (tiếng Việt)
    """
    id: str
    name: str
    entity: str
    fields: list[str] = field(default_factory=list)
    filter: dict[str, Any] = field(default_factory=dict)
    format: ReportFormat = ReportFormat.PDF
    layout: ReportLayout = ReportLayout.TABLE
    group_by: str = ""
    aggregations: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate report spec sau khi khởi tạo."""
        # ID không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP34_EMPTY_REPORT_ID)
        # Entity không được để trống
        if not self.entity or not self.entity.strip():
            EM.raise_error(ErrorCode.CP34_REPORT_SPEC_INVALID, reason="entity không được để trống")
        # Validate aggregation functions
        valid_funcs = {af.value for af in AggregationFunc}
        for agg in self.aggregations:
            if agg.upper() not in valid_funcs:
                EM.raise_error(
                    ErrorCode.CP34_INVALID_AGGREGATION,
                    func=agg,
                    valid_funcs=list(valid_funcs)
                )
        # Validate layout
        if not isinstance(self.layout, ReportLayout):
            EM.raise_error(
                ErrorCode.CP34_INVALID_LAYOUT,
                layout=self.layout,
                valid_layouts=[l.value for l in ReportLayout]
            )
        # Validate format
        if not isinstance(self.format, ReportFormat):
            EM.raise_error(
                ErrorCode.CP34_INVALID_FORMAT,
                fmt=self.format,
                valid_formats=[f.value for f in ReportFormat]
            )

    def has_aggregation(self) -> bool:
        """Kiểm tra report có aggregation không."""
        return len(self.aggregations) > 0

    def needs_grouping(self) -> bool:
        """Kiểm tra report cần group by không."""
        return bool(self.group_by and self.group_by.strip())

    def to_dict(self) -> dict[str, Any]:
        """Chuyển report spec sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "entity": self.entity,
            "fields": self.fields,
            "filter": self.filter,
            "format": self.format.value,
            "layout": self.layout.value,
            "group_by": self.group_by,
            "aggregations": self.aggregations,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportSpec":
        """Tạo ReportSpec từ dict."""
        fmt_str = data.get("format", "pdf")
        layout_str = data.get("layout", "table")

        try:
            fmt = ReportFormat(fmt_str)
        except ValueError:
            fmt = ReportFormat.PDF

        try:
            layout = ReportLayout(layout_str)
        except ValueError:
            layout = ReportLayout.TABLE

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity=data.get("entity", ""),
            fields=data.get("fields", []),
            filter=data.get("filter", {}),
            format=fmt,
            layout=layout,
            group_by=data.get("group_by", ""),
            aggregations=data.get("aggregations", []),
            description=data.get("description", ""),
        )


# ===========================================================================
# BatchJob
# ===========================================================================


@dataclass
class BatchJob:
    """
    Job để xử lý batch document async (qua CP13 worker).

    Attributes:
        id: UUID định danh job
        status: Trạng thái job
        report_spec_ids: Danh sách report spec IDs cần generate
        created_at: Thời điểm tạo job
        completed_at: Thời điểm hoàn thành (optional)
        error: Lỗi (nếu failed)
        result_urls: URLs của file đã generate (CP11 presigned URL)
        retries: Số lần retry đã thực hiện
        max_retries: Số lần retry tối đa
        metadata: Metadata mở rộng
    """
    report_spec_ids: list[str]
    id: str = field(default_factory=lambda: str(uuid4()))
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: str = ""
    result_urls: list[str] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate batch job sau khi khởi tạo."""
        if not self.report_spec_ids:
            EM.raise_error(
                ErrorCode.CP34_BATCH_JOB_FAILED,
                reason="Batch job phải có ít nhất 1 report spec"
            )
        if self.max_retries < 0:
            self.max_retries = 3

    def can_retry(self) -> bool:
        """Kiểm tra job có thể retry không."""
        return self.retries < self.max_retries and self.status == BatchJobStatus.FAILED

    def mark_running(self) -> None:
        """Đánh dấu job đang chạy."""
        self.status = BatchJobStatus.RUNNING

    def mark_completed(self, urls: list[str] | None = None) -> None:
        """Đánh dấu job hoàn thành."""
        self.status = BatchJobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if urls:
            self.result_urls = urls

    def mark_failed(self, error_msg: str) -> None:
        """Đánh dấu job thất bại."""
        self.status = BatchJobStatus.FAILED
        self.error = error_msg
        self.completed_at = datetime.now(timezone.utc)

    def mark_cancelled(self) -> None:
        """Đánh dấu job bị hủy."""
        self.status = BatchJobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển batch job sang dict format."""
        return {
            "id": self.id,
            "status": self.status.value,
            "report_spec_ids": self.report_spec_ids,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result_urls": self.result_urls,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchJob":
        """Tạo BatchJob từ dict."""
        return cls(
            id=data.get("id", str(uuid4())),
            report_spec_ids=data.get("report_spec_ids", []),
            status=BatchJobStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error", ""),
            result_urls=data.get("result_urls", []),
            retries=data.get("retries", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ReportCollection
# ===========================================================================


@dataclass
class ReportCollection:
    """
    Collection chứa tất cả report specs.

    Dùng làm output của ReportParser và input cho Stack Emitters.

    Attributes:
        reports: Danh sách ReportSpec
    """
    reports: list[ReportSpec] = field(default_factory=list)

    def add_report(self, report: ReportSpec) -> None:
        """Thêm report spec vào collection."""
        if self.get_report_by_id(report.id):
            EM.raise_error(ErrorCode.DSL_DUPLICATE_NODE_ID, id=report.id, kind="report")
        self.reports.append(report)

    def get_report_by_id(self, report_id: str) -> Optional[ReportSpec]:
        """Tìm report spec theo ID."""
        for report in self.reports:
            if report.id == report_id:
                return report
        return None

    def get_reports_by_format(self, fmt: ReportFormat) -> list[ReportSpec]:
        """Lọc reports theo format."""
        return [r for r in self.reports if r.format == fmt]

    def get_reports_by_entity(self, entity: str) -> list[ReportSpec]:
        """Lọc reports theo entity source."""
        return [r for r in self.reports if r.entity == entity]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "reports": [r.to_dict() for r in self.reports],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportCollection":
        """Tạo ReportCollection từ dict."""
        result = cls()
        result.reports = [ReportSpec.from_dict(r) for r in data.get("reports", [])]
        return result
