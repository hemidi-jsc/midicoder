"""Job Scheduling Models — CP13: Background Job & Workflow Generator.

Module này cung cấp các model cho job scheduling: JobDefinition, JobInstance,
SchedulePolicy và JobPriority.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class JobPriority(str, Enum):
    """Mức độ ưu tiên của job."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Delayed import để tránh circular — import ở top cho __post_init__ dùng được
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM  # noqa: E402


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


@dataclass
class RetryPolicy:
    """Chính sách retry với exponential backoff cho job.

    Attributes:
        max_retries: Số lần retry tối đa.
        base_delay_seconds: Độ trễ cơ bản (giây) cho lần retry đầu tiên.
        max_delay_seconds: Độ trễ tối đa (giây) giới hạn trên.
        backoff_multiplier: Hệ số nhân cho exponential backoff.
        jitter: Có thêm ngẫu nhiên vào độ trễ để tránh thundering herd.
    """

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0
    backoff_multiplier: float = 2.0
    jitter: bool = True

    def get_delay_attempt(self, attempt: int) -> float:
        """Tính độ trễ cho attempt cụ thể với exponential backoff và jitter.

        Args:
            attempt: Số lần retry hiện tại (0-based).

        Returns:
            Độ trễ tính bằng giây.
        """
        delay = self.base_delay_seconds * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay_seconds)

        if self.jitter:
            delay = random.uniform(0, delay)

        return delay

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "max_retries": self.max_retries,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "jitter": self.jitter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetryPolicy:
        """Tạo RetryPolicy từ dict."""
        return cls(
            max_retries=data.get("max_retries", 3),
            base_delay_seconds=data.get("base_delay_seconds", 1.0),
            max_delay_seconds=data.get("max_delay_seconds", 300.0),
            backoff_multiplier=data.get("backoff_multiplier", 2.0),
            jitter=data.get("jitter", True),
        )


@dataclass
class DeadLetterQueue:
    """Dead letter queue cho các job thất bại không thể recover.

    Attributes:
        queue_name: Tên của queue.
        messages: Danh sách các message thất bại.
        max_size: Số message tối đa trong queue.
        retention_hours: Thời gian giữ message (giờ). Mặc định 168 giờ (7 ngày).
    """

    queue_name: str
    messages: list[dict] = field(default_factory=list)
    max_size: int = 10000
    retention_hours: int = 168

    def add(self, message: dict) -> None:
        """Thêm message vào dead letter queue.

        Args:
            message: Message dict chứa thông tin job thất bại.
        """
        self.messages.append(message)

    def get_all(self) -> list[dict]:
        """Trả về tất cả messages trong queue."""
        return self.messages

    def purge(self) -> None:
        """Xóa tất cả messages khỏi queue."""
        self.messages.clear()

    def size(self) -> int:
        """Trả về số message hiện tại trong queue."""
        return len(self.messages)

    def is_full(self) -> bool:
        """Kiểm tra queue đã đầy chưa."""
        return len(self.messages) >= self.max_size

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "queue_name": self.queue_name,
            "messages": self.messages,
            "max_size": self.max_size,
            "retention_hours": self.retention_hours,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeadLetterQueue:
        """Tạo DeadLetterQueue từ dict."""
        return cls(
            queue_name=data["queue_name"],
            messages=data.get("messages", []),
            max_size=data.get("max_size", 10000),
            retention_hours=data.get("retention_hours", 168),
        )


@dataclass
class JobRetryTracker:
    """Theo dõi trạng thái retry cho một job instance.

    Attributes:
        instance_id: ID của job instance.
        retry_policy: Chính sách retry áp dụng.
        current_attempt: Số lần attempt hiện tại.
        last_error: Lỗi cuối cùng (nếu có).
        next_retry_at: Thời điểm retry tiếp theo.
        is_exhausted: Đã hết lượt retry hay chưa.
    """

    instance_id: str
    retry_policy: RetryPolicy
    current_attempt: int = 0
    last_error: str = ""
    next_retry_at: datetime | None = None
    is_exhausted: bool = False

    def record_failure(self, error: str) -> None:
        """Ghi nhận thất bại, tăng attempt, tính thời điểm retry tiếp theo.

        Args:
            error: Thông điệp lỗi của lần attempt này.
        """
        self.current_attempt += 1
        self.last_error = error

        if self.current_attempt >= self.retry_policy.max_retries:
            self.is_exhausted = True
            EM.raise_error(
                ErrorCode.CP13_JOB_RETRY_EXHAUSTED,
                instance_id=str(self.instance_id),
                attempt=self.current_attempt,
                max_retries=self.retry_policy.max_retries,
                last_error=error,
            )
            return

        delay = self.retry_policy.get_delay_attempt(self.current_attempt)
        self.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    def reset(self) -> None:
        """Đặt lại trạng thái retry về ban đầu."""
        self.current_attempt = 0
        self.last_error = ""
        self.next_retry_at = None
        self.is_exhausted = False

    def should_retry(self) -> bool:
        """Kiểm tra xem còn nên retry nữa không.

        Returns:
            True nếu chưa hết lượt retry.
        """
        return not self.is_exhausted

    def get_next_delay(self) -> float:
        """Tính độ trễ cho lần retry tiếp theo.

        Returns:
            Độ trễ tính bằng giây.
        """
        return self.retry_policy.get_delay_attempt(self.current_attempt)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "instance_id": self.instance_id,
            "retry_policy": self.retry_policy.to_dict(),
            "current_attempt": self.current_attempt,
            "last_error": self.last_error,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "is_exhausted": self.is_exhausted,
        }
