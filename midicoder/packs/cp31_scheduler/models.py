"""
Mô-đun DSL models cho Scheduler & Cron Engine.

Cung cấp các dataclasses định nghĩa scheduling:
- CronSchedule: Lịch trình theo cron expression
- RecurrenceSchedule: Lịch trình theo recurrence pattern semantic
- CalendarSchedule: Lịch trình aware calendar/holiday
- CalendarException: Ngày ngoại lệ (holiday, skip day)
- CalendarSet: Tập hợp exceptions cho một calendar

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class ScheduleType(str, Enum):
    """Loại lịch trình."""

    CRON = "cron"
    RECURRENCE = "recurrence"
    CALENDAR = "calendar"


class RecurrenceFrequency(str, Enum):
    """Tần suất recurrence semantic."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LAST_BUSINESS_DAY = "last_business_day"
    FIRST_DAY_OF_WEEK_IN_MONTH = "first_day_of_week_in_month"


class ExceptionType(str, Enum):
    """Loại calendar exception."""

    HOLIDAY = "holiday"
    SKIP = "skip"
    OVERRIDE = "override"


@dataclass
class CronSchedule:
    """Lịch trình theo cron expression.

    Attributes:
        schedule_id: Unique ID của schedule.
        cron_expression: Cron expression (vd: "0 9 * * 1-5").
        timezone: Timezone cho expression (mặc định UTC).
        enabled: Có kích hoạt hay không.
        metadata: Metadata bổ sung.
    """

    schedule_id: str
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.schedule_id or not self.schedule_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_CRON_EXPR,
                schedule_id=self.schedule_id,
                reason="schedule_id không được rỗng",
            )
        if not self.cron_expression or not self.cron_expression.strip():
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_CRON_EXPR,
                schedule_id=self.schedule_id,
                reason="cron_expression không được rỗng",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "schedule_id": self.schedule_id,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CronSchedule:
        """Tạo CronSchedule từ dict."""
        return cls(
            schedule_id=data["schedule_id"],
            cron_expression=data["cron_expression"],
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RecurrenceSchedule:
    """Lịch trình theo recurrence pattern semantic.

    Attributes:
        schedule_id: Unique ID của schedule.
        frequency: Tần suất (daily, weekly, monthly, yearly).
        interval: Khoảng cách giữa các lần chạy (mặc định 1).
        days_of_week: Ngày trong tuần (cho weekly).
        day_of_month: Ngày trong tháng (cho monthly).
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc (nếu có).
        timezone: Timezone (mặc định UTC).
        enabled: Có kích hoạt hay không.
        metadata: Metadata bổ sung.
    """

    schedule_id: str
    frequency: RecurrenceFrequency
    interval: int = 1
    days_of_week: list[int] = field(default_factory=list)
    day_of_month: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone: str = "UTC"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.schedule_id or not self.schedule_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_RECURRENCE,
                schedule_id=self.schedule_id,
                reason="schedule_id không được rỗng",
            )
        if self.interval < 1:
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_RECURRENCE,
                schedule_id=self.schedule_id,
                reason="interval phải >= 1",
            )
        # Validate days_of_week cho weekly
        if self.frequency == RecurrenceFrequency.WEEKLY and self.days_of_week:
            for day in self.days_of_week:
                if day < 0 or day > 6:
                    raise EM.raise_error(
                        ErrorCode.CP31_INVALID_RECURRENCE,
                        schedule_id=self.schedule_id,
                        reason=f"days_of_week phải trong [0, 6], nhận được {day}",
                    )
        # Validate day_of_month cho monthly
        if self.frequency == RecurrenceFrequency.MONTHLY and self.day_of_month:
            if self.day_of_month < 1 or self.day_of_month > 31:
                raise EM.raise_error(
                    ErrorCode.CP31_INVALID_RECURRENCE,
                    schedule_id=self.schedule_id,
                    reason=f"day_of_month phải trong [1, 31], nhận được {self.day_of_month}",
                )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "schedule_id": self.schedule_id,
            "frequency": self.frequency.value if isinstance(self.frequency, RecurrenceFrequency) else self.frequency,
            "interval": self.interval,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecurrenceSchedule:
        """Tạo RecurrenceSchedule từ dict."""
        freq_val = data.get("frequency", "daily")
        frequency = RecurrenceFrequency(freq_val) if isinstance(freq_val, str) else freq_val

        start_date = None
        if data.get("start_date"):
            start_date = date.fromisoformat(data["start_date"])

        end_date = None
        if data.get("end_date"):
            end_date = date.fromisoformat(data["end_date"])

        return cls(
            schedule_id=data["schedule_id"],
            frequency=frequency,
            interval=data.get("interval", 1),
            days_of_week=data.get("days_of_week", []),
            day_of_month=data.get("day_of_month"),
            start_date=start_date,
            end_date=end_date,
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CalendarSchedule:
    """Lịch trình aware calendar/holiday.

    Attributes:
        schedule_id: Unique ID của schedule.
        base_schedule: Schedule cơ sở (cron hoặc recurrence).
        calendar_set_id: Reference đến CalendarSet.
        skip_holidays: Có skip holidays không.
        business_days_only: Chỉ chạy vào business day.
        timezone: Timezone (mặc định UTC).
        enabled: Có kích hoạt hay không.
        metadata: Metadata bổ sung.
    """

    schedule_id: str
    base_schedule: dict[str, Any]
    calendar_set_id: str
    skip_holidays: bool = True
    business_days_only: bool = False
    timezone: str = "UTC"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.schedule_id or not self.schedule_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                schedule_id=self.schedule_id,
                reason="schedule_id không được rỗng",
            )
        if not self.calendar_set_id or not self.calendar_set_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_CALENDAR_NOT_FOUND,
                schedule_id=self.schedule_id,
                reason="calendar_set_id không được rỗng",
            )
        if not self.base_schedule:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                schedule_id=self.schedule_id,
                reason="base_schedule không được rỗng",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "schedule_id": self.schedule_id,
            "base_schedule": self.base_schedule,
            "calendar_set_id": self.calendar_set_id,
            "skip_holidays": self.skip_holidays,
            "business_days_only": self.business_days_only,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarSchedule:
        """Tạo CalendarSchedule từ dict."""
        return cls(
            schedule_id=data["schedule_id"],
            base_schedule=data["base_schedule"],
            calendar_set_id=data["calendar_set_id"],
            skip_holidays=data.get("skip_holidays", True),
            business_days_only=data.get("business_days_only", False),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CalendarException:
    """Ngày ngoại lệ trong calendar.

    Attributes:
        exception_id: Unique ID.
        date: Ngày ngoại lệ.
        type: Loại (holiday, skip, override).
        label: Tên mô tả.
        override_date: Nếu override, ngày thay thế là gì.
    """

    exception_id: str
    date: date
    type: ExceptionType
    label: str = ""
    override_date: Optional[date] = None

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.exception_id or not self.exception_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_BUSINESS_DAY_ERROR,
                exception_id=self.exception_id,
                reason="exception_id không được rỗng",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "exception_id": self.exception_id,
            "date": self.date.isoformat(),
            "type": self.type.value if isinstance(self.type, ExceptionType) else self.type,
            "label": self.label,
            "override_date": self.override_date.isoformat() if self.override_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarException:
        """Tạo CalendarException từ dict."""
        type_val = data.get("type", "holiday")
        exc_type = ExceptionType(type_val) if isinstance(type_val, str) else type_val

        override_date = None
        if data.get("override_date"):
            override_date = date.fromisoformat(data["override_date"])

        return cls(
            exception_id=data["exception_id"],
            date=date.fromisoformat(data["date"]),
            type=exc_type,
            label=data.get("label", ""),
            override_date=override_date,
        )


@dataclass
class CalendarSet:
    """Tập hợp calendar exceptions.

    Attributes:
        calendar_set_id: Unique ID.
        name: Tên mô tả.
        exceptions: Danh sách exceptions.
        country: Mã quốc gia (nếu áp dụng).
    """

    calendar_set_id: str
    name: str
    exceptions: list[CalendarException] = field(default_factory=list)
    country: str = ""

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.calendar_set_id or not self.calendar_set_id.strip():
            raise EM.raise_error(
                ErrorCode.CP31_CALENDAR_NOT_FOUND,
                calendar_set_id=self.calendar_set_id,
                reason="calendar_set_id không được rỗng",
            )

    def add_exception(self, exc: CalendarException) -> None:
        """Thêm exception vào calendar set.

        Args:
            exc: CalendarException cần thêm.
        """
        self.exceptions.append(exc)

    def is_exception_date(self, d: date) -> bool:
        """Kiểm tra xem một ngày có phải exception không.

        Args:
            d: Ngày cần kiểm tra.

        Returns:
            True nếu là ngày exception.
        """
        return any(exc.date == d for exc in self.exceptions)

    def get_exceptions(self) -> list[CalendarException]:
        """Trả về tất cả exceptions."""
        return self.exceptions

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "calendar_set_id": self.calendar_set_id,
            "name": self.name,
            "exceptions": [exc.to_dict() for exc in self.exceptions],
            "country": self.country,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarSet:
        """Tạo CalendarSet từ dict."""
        exceptions = []
        for exc_data in data.get("exceptions", []):
            exceptions.append(CalendarException.from_dict(exc_data))

        return cls(
            calendar_set_id=data["calendar_set_id"],
            name=data["name"],
            exceptions=exceptions,
            country=data.get("country", ""),
        )
