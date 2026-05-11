"""Job Scheduling Models — CP13: Background Job & Workflow Generator.

Module này cung cấp các model cho job scheduling: JobDefinition, JobInstance,
SchedulePolicy và JobPriority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobPriority(str, Enum):
    """Mức độ ưu tiên của job."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Delayed import để tránh circular — import ở top cho __post_init__ dùng được
from midicoder.errors import ErrorCode  # noqa: E402


@dataclass
class SchedulePolicy:
    """Chính sách schedule cho job — cron expression hoặc interval.

    Attributes:
        cron_expr: Cron expression (vd: "0 */5 * * * *").
        interval_seconds: Khoảng thời gian giữa các lần chạy (giây).
        max_concurrent: Số job chạy song song tối đa.
        timezone: Timezone cho cron expression.
    """

    cron_expr: str | None = None
    interval_seconds: int | None = None
    max_concurrent: int = 1
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Validate: phải có cron_expr HOẶC interval_seconds."""
        if self.cron_expr is None and self.interval_seconds is None:
            raise ValueError(
                "SchedulePolicy phải có cron_expr hoặc interval_seconds "
                f"[{ErrorCode.CP13_SCHEDULE_POLICY_INVALID.value}]"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "cron_expr": self.cron_expr,
            "interval_seconds": self.interval_seconds,
            "max_concurrent": self.max_concurrent,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchedulePolicy:
        """Tạo SchedulePolicy từ dict."""
        return cls(
            cron_expr=data.get("cron_expr"),
            interval_seconds=data.get("interval_seconds"),
            max_concurrent=data.get("max_concurrent", 1),
            timezone=data.get("timezone", "UTC"),
        )


@dataclass
class JobDefinition:
    """Định nghĩa job — template cho việc lập lịch job.

    Attributes:
        job_id: Unique ID của job.
        name: Tên mô tả của job.
        task_type: Loại task (vd: "email_report", "session_cleanup").
        schedule: Chính sách schedule.
        priority: Mức độ ưu tiên.
        retry_count: Số lần retry tối đa.
        timeout_seconds: Thời gian timeout (giây).
        enabled: Job có được kích hoạt hay không.
        metadata: Metadata bổ sung.
    """

    job_id: str
    name: str
    task_type: str
    schedule: SchedulePolicy
    priority: JobPriority = JobPriority.NORMAL
    retry_count: int = 3
    timeout_seconds: int = 3600
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate: job_id và task_type không được rỗng."""
        if not self.job_id or not self.job_id.strip():
            raise ValueError(
                f"job_id không được rỗng [{ErrorCode.CP13_JOB_NOT_FOUND.value}]"
            )
        if not self.task_type or not self.task_type.strip():
            raise ValueError(
                f"task_type không được rỗng [{ErrorCode.CP13_JOB_SCHEDULE_FAILED.value}]"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "task_type": self.task_type,
            "schedule": self.schedule.to_dict(),
            "priority": self.priority.value,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobDefinition:
        """Tạo JobDefinition từ dict."""
        schedule_data = data.get("schedule", {})
        schedule = SchedulePolicy.from_dict(schedule_data) if isinstance(schedule_data, dict) else schedule_data

        priority_val = data.get("priority", "normal")
        priority = JobPriority(priority_val) if isinstance(priority_val, str) else priority_val

        return cls(
            job_id=data["job_id"],
            name=data["name"],
            task_type=data["task_type"],
            schedule=schedule,
            priority=priority,
            retry_count=data.get("retry_count", 3),
            timeout_seconds=data.get("timeout_seconds", 3600),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class JobInstance:
    """Instance của job — đại diện cho một lần thực thi cụ thể.

    Attributes:
        instance_id: Unique ID của instance.
        job_id: Reference đến JobDefinition.
        status: Trạng thái hiện tại (pending/running/completed/failed/cancelled).
        started_at: Thời điểm bắt đầu.
        completed_at: Thời điểm hoàn thành.
        retries: Số lần đã retry.
        error: Lỗi (nếu có).
        result: Kết quả (nếu hoàn thành).
    """

    instance_id: str
    job_id: str
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    error: str | None = None
    result: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate: instance_id và job_id không được rỗng."""
        if not self.instance_id or not self.instance_id.strip():
            raise ValueError(
                f"instance_id không được rỗng [{ErrorCode.CP13_JOB_NOT_FOUND.value}]"
            )
        if not self.job_id or not self.job_id.strip():
            raise ValueError(
                f"job_id không được rỗng [{ErrorCode.CP13_JOB_NOT_FOUND.value}]"
            )

    def mark_running(self) -> None:
        """Đánh dấu job đang chạy."""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Đánh dấu job hoàn thành."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        if result is not None:
            self.result = result

    def mark_failed(self, error: str) -> None:
        """Đánh dấu job thất bại và tăng retry count."""
        self.status = "failed"
        self.error = error
        self.retries += 1

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "instance_id": self.instance_id,
            "job_id": self.job_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "error": self.error,
            "result": self.result,
        }
