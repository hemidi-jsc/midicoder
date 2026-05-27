# coding: utf-8
"""
Mô-đun report scheduler runtime engine (CP17).

Cung cấp:
- ReportSnapshot: Snapshot của một report — immutable sau khi sinh
- ReportScheduler: Scheduler cho reports tự động — lập lịch, sinh, quản lý history

Obligation: report immutability — mỗi snapshot có SHA-256 hash

Đọc dữ liệu metric từ CP15 MetricRegistry.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from midicoder.packs.cp17_bi_analytics.models import ScheduledReport, ReportFormat
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# ReportSnapshot
# ===========================================================================


@dataclass(frozen=True)
class ReportSnapshot:
    """Snapshot của một report — immutable sau khi sinh.

    Obligation: report immutability — có SHA-256 hash.

    Attributes:
        report_name: Tên report
        title: Tiêu đề
        generated_at: Thời điểm sinh
        data: Dữ liệu report (dict)
        hash_value: SHA-256 hash
        format: Định dạng output
        model_name: Model name đã dùng
    """
    report_name: str
    title: str
    generated_at: datetime
    data: dict
    hash_value: str
    format: str
    model_name: str

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ReportSnapshot sang dict format."""
        return {
            "report_name": self.report_name,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "data": self.data,
            "hash_value": self.hash_value,
            "format": self.format,
            "model_name": self.model_name,
        }


# ===========================================================================
# ReportScheduler
# ===========================================================================


class ReportScheduler:
    """Scheduler cho reports tự động.

    Cung cấp:
    - schedule_report(report_def) → lập lịch report
    - generate_report(report_name, registry) → sinh report thủ công
    - get_scheduled_reports() → lấy danh sách reports
    - execute_due_reports(registry) → chạy các reports đến hạn
    - get_report_history(report_name) → lịch sử reports
    - unregister_report(name) → hủy đăng ký report

    Obligation: report immutability — mỗi snapshot có SHA-256 hash

    Đọc dữ liệu metric từ CP15 MetricRegistry
    """

    def __init__(self) -> None:
        """Khởi tạo ReportScheduler."""
        self._reports: dict[str, ScheduledReport] = {}
        self._snapshots: dict[str, list[ReportSnapshot]] = {}

    def schedule_report(self, report_def: ScheduledReport) -> None:
        """Lập lịch report.

        Lưu ScheduledReport vào danh sách reports.
        Tạo danh sách snapshots rỗng cho report.

        Args:
            report_def: ScheduledReport cần lập lịch
        """
        self._reports[report_def.name] = report_def
        if report_def.name not in self._snapshots:
            self._snapshots[report_def.name] = []

    def generate_report(
        self,
        report_name: str,
        registry: Any = None,
    ) -> ReportSnapshot:
        """Sinh report thủ công.

        Tạo ReportSnapshot từ report definition. Nếu có registry, đọc metric data
        từ CP15 MetricRegistry; nếu không, dùng data rỗng.

        Args:
            report_name: Tên report đã lập lịch
            registry: CP15 MetricRegistry (tùy chọn, cho test)

        Returns:
            ReportSnapshot immutable

        Raises:
            KeyError: Nếu report không tồn tại
        """
        if report_name not in self._reports:
            raise KeyError(
                f"Report '{report_name}' không tồn tại. "
                f"Lập lịch report trước khi sinh."
            )

        report = self._reports[report_name]
        now = datetime.now(timezone.utc)

        # Thu thập dữ liệu từ registry
        data: dict[str, Any] = {
            "model_name": report.model_name,
            "parameters": report.parameters,
            "metrics": {},
        }

        if registry is not None:
            # Đọc tất cả metric entries từ registry
            all_entries = registry.get(report.model_name, None)
            if all_entries:
                for entry in all_entries:
                    metric_key = entry.name
                    if metric_key not in data["metrics"]:
                        data["metrics"][metric_key] = []
                    data["metrics"][metric_key].append({
                        "value": entry.value,
                        "timestamp": entry.timestamp.isoformat()
                        if hasattr(entry, "timestamp") else None,
                    })

        # Tính SHA-256 hash — obligation: report immutability
        hash_value = self._compute_hash(report_name, data, now)

        snapshot = ReportSnapshot(
            report_name=report_name,
            title=report.title,
            generated_at=now,
            data=data,
            hash_value=hash_value,
            format=report.format.value,
            model_name=report.model_name,
        )

        # Lưu snapshot vào history
        if report_name not in self._snapshots:
            self._snapshots[report_name] = []
        self._snapshots[report_name].append(snapshot)

        # Cập nhật next_run dựa trên schedule policy
        self._update_next_run(report)

        return snapshot

    def _compute_hash(
        self,
        report_name: str,
        data: dict,
        generated_at: datetime,
    ) -> str:
        """Tính SHA-256 hash cho report snapshot.

        Hash được tính từ report_name, data, và generated_at để đảm bảo
        mỗi snapshot là duy nhất và immutable.

        Args:
            report_name: Tên report
            data: Dữ liệu report
            generated_at: Thời điểm sinh

        Returns:
            Chuỗi SHA-256 hash
        """
        hash_input = json.dumps({
            "report_name": report_name,
            "data": data,
            "generated_at": generated_at.isoformat(),
        }, sort_keys=True)
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def get_scheduled_reports(self) -> list[ScheduledReport]:
        """Lấy danh sách reports đã lập lịch.

        Returns:
            Danh sách ScheduledReport
        """
        return list(self._reports.values())

    def execute_due_reports(self, registry: Any = None) -> list[ReportSnapshot]:
        """Chạy các reports đến hạn.

        Kiểm tra next_run <= now cho từng report, nếu đúng thì generate.
        Sau khi generate, cập nhật next_run dựa trên schedule policy.

        Args:
            registry: CP15 MetricRegistry (tùy chọn)

        Returns:
            Danh sách ReportSnapshot đã sinh
        """
        now = datetime.now(timezone.utc)
        due_reports: list[ScheduledReport] = []

        # Tìm các reports đến hạn
        for report in self._reports.values():
            if report.next_run and report.next_run <= now:
                due_reports.append(report)

        # Sinh từng report đến hạn
        snapshots: list[ReportSnapshot] = []
        for report in due_reports:
            snapshot = self.generate_report(report.name, registry)
            snapshots.append(snapshot)

        return snapshots

    def get_report_history(self, report_name: str) -> list[ReportSnapshot]:
        """Lấy lịch sử snapshots của một report.

        Args:
            report_name: Tên report

        Returns:
            Danh sách ReportSnapshot theo thứ tự thời gian
        """
        return list(self._snapshots.get(report_name, []))

    def unregister_report(self, name: str) -> bool:
        """Hủy đăng ký report.

        Xóa report và lịch sử snapshots.

        Args:
            name: Tên report

        Returns:
            True nếu thành công, False nếu report không tồn tại
        """
        if name not in self._reports:
            return False
        del self._reports[name]
        self._snapshots.pop(name, None)
        return True

    def _update_next_run(self, report: ScheduledReport) -> None:
        """Cập nhật next_run dựa trên schedule policy.

        Args:
            report: ScheduledReport cần cập nhật
        """
        from midicoder.packs.cp17_bi_analytics.models import SchedulePolicy

        if report.schedule_policy == SchedulePolicy.ONCE:
            # Chỉ chạy một lần — đặt next_run rất xa tương lai
            report.next_run = datetime(2999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        elif report.schedule_policy == SchedulePolicy.HOURLY:
            report.next_run = (report.next_run or datetime.now(timezone.utc)) + timedelta(hours=1)
        elif report.schedule_policy == SchedulePolicy.DAILY:
            report.next_run = (report.next_run or datetime.now(timezone.utc)) + timedelta(days=1)
        elif report.schedule_policy == SchedulePolicy.WEEKLY:
            report.next_run = (report.next_run or datetime.now(timezone.utc)) + timedelta(weeks=1)
        elif report.schedule_policy == SchedulePolicy.MONTHLY:
            # xấp xỉ: 30 ngày
            report.next_run = (report.next_run or datetime.now(timezone.utc)) + timedelta(days=30)
