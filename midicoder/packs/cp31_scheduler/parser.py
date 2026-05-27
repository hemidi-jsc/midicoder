"""
Scheduler DSL Parser — parse YAML/dict sang model objects.

Module này cung cấp SchedulerParser để convert YAML/dict
thành CronSchedule, RecurrenceSchedule, CalendarSchedule models.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from midicoder.packs.cp31_scheduler.models import (
    CalendarException,
    CalendarSchedule,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
    ScheduleType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class SchedulerParser:
    """Parser cho scheduler DSL.

    Convert YAML/dict sang typed model objects.

    Ví dụ:
        >>> parser = SchedulerParser()
        >>> data = {"type": "cron", "schedule_id": "daily-backup", "cron_expression": "0 2 * * *"}
        >>> schedule = parser.parse(data)
        >>> isinstance(schedule, CronSchedule)
        True
    """

    def parse(self, data: dict[str, Any]) -> Any:
        """Parse một schedule dict thành model object.

        Args:
            data: Dict chứa schedule data với field "type".

        Returns:
            CronSchedule, RecurrenceSchedule, CalendarSchedule, CalendarSet,
            hoặc CalendarException tùy theo type.

        Raises:
            MidicoderError: Nếu data invalid hoặc type không known.
        """
        if not data or not isinstance(data, dict):
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="Data phải là dict không rỗng",
            )

        # Ưu tiên schedule_type để tránh conflict với ExceptionType.type
        item_type = data.get("schedule_type")
        if item_type is None:
            # Fallback: dùng "type" nhưng chỉ khi data KHÔNG có các keys của exception
            if "exception_id" in data:
                item_type = "exception"
            elif "calendar_set_id" in data and "name" in data and "exceptions" in data:
                item_type = "calendar_set"
            else:
                item_type = data.get("type")

        if item_type == "calendar_set":
            return self._parse_calendar_set(data)
        elif item_type == "exception":
            return self._parse_exception(data)
        elif not item_type:
            # Try auto-detect
            if "cron_expression" in data:
                return self._parse_cron(data)
            elif "frequency" in data:
                return self._parse_recurrence(data)
            elif "calendar_set_id" in data:
                return self._parse_calendar_schedule(data)
            else:
                raise EM.raise_error(
                    ErrorCode.CP31_DSL_PARSE_ERROR,
                    data=str(data)[:200],
                    reason="Không xác định được loại schedule — thiếu field 'type'",
                )

        type_map = {
            "cron": self._parse_cron,
            "recurrence": self._parse_recurrence,
            "calendar": self._parse_calendar_schedule,
        }

        parser_fn = type_map.get(item_type)
        if not parser_fn:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                type=item_type,
                known=list(type_map.keys()),
            )

        return parser_fn(data)

    def parse_list(self, data_list: list[dict[str, Any]]) -> list[Any]:
        """Parse danh sách schedule dicts.

        Args:
            data_list: Danh sách dict chứa schedule data.

        Returns:
            Danh sách model objects.
        """
        return [self.parse(d) for d in data_list]

    def _parse_cron(self, data: dict[str, Any]) -> CronSchedule:
        """Parse dict thành CronSchedule.

        Args:
            data: Dict chứa cron schedule data.

        Returns:
            CronSchedule object.
        """
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="CronSchedule cần field 'schedule_id'",
            )
        if "cron_expression" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CronSchedule cần field 'cron_expression'",
            )

        return CronSchedule(
            schedule_id=data["schedule_id"],
            cron_expression=data["cron_expression"],
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def _parse_recurrence(self, data: dict[str, Any]) -> RecurrenceSchedule:
        """Parse dict thành RecurrenceSchedule.

        Args:
            data: Dict chứa recurrence schedule data.

        Returns:
            RecurrenceSchedule object.
        """
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="RecurrenceSchedule cần field 'schedule_id'",
            )

        from datetime import date as date_type

        freq_val = data.get("frequency", "daily")
        frequency = RecurrenceFrequency(freq_val) if isinstance(freq_val, str) else freq_val

        start_date = None
        if data.get("start_date"):
            start_date = date_type.fromisoformat(data["start_date"])

        end_date = None
        if data.get("end_date"):
            end_date = date_type.fromisoformat(data["end_date"])

        return RecurrenceSchedule(
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

    def _parse_calendar_schedule(self, data: dict[str, Any]) -> CalendarSchedule:
        """Parse dict thành CalendarSchedule.

        Args:
            data: Dict chứa calendar schedule data.

        Returns:
            CalendarSchedule object.
        """
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="CalendarSchedule cần field 'schedule_id'",
            )
        if "calendar_set_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CalendarSchedule cần field 'calendar_set_id'",
            )
        if "base_schedule" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CalendarSchedule cần field 'base_schedule'",
            )

        return CalendarSchedule(
            schedule_id=data["schedule_id"],
            base_schedule=data["base_schedule"],
            calendar_set_id=data["calendar_set_id"],
            skip_holidays=data.get("skip_holidays", True),
            business_days_only=data.get("business_days_only", False),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def _parse_calendar_set(self, data: dict[str, Any]) -> CalendarSet:
        """Parse dict thành CalendarSet.

        Args:
            data: Dict chứa calendar set data.

        Returns:
            CalendarSet object.
        """
        if "calendar_set_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="CalendarSet cần field 'calendar_set_id'",
            )
        if "name" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                calendar_set_id=data.get("calendar_set_id"),
                reason="CalendarSet cần field 'name'",
            )

        exceptions = []
        for exc_data in data.get("exceptions", []):
            exceptions.append(self._parse_exception(exc_data))

        return CalendarSet(
            calendar_set_id=data["calendar_set_id"],
            name=data["name"],
            exceptions=exceptions,
            country=data.get("country", ""),
        )

    def _parse_exception(self, data: dict[str, Any]) -> CalendarException:
        """Parse dict thành CalendarException.

        Args:
            data: Dict chứa exception data.

        Returns:
            CalendarException object.
        """
        if "exception_id" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                reason="CalendarException cần field 'exception_id'",
            )
        if "date" not in data:
            raise EM.raise_error(
                ErrorCode.CP31_DSL_PARSE_ERROR,
                exception_id=data.get("exception_id"),
                reason="CalendarException cần field 'date'",
            )

        from datetime import date as date_type

        type_val = data.get("type", "holiday")
        exc_type = ExceptionType(type_val) if isinstance(type_val, str) else type_val

        override_date = None
        if data.get("override_date"):
            override_date = date_type.fromisoformat(data["override_date"])

        return CalendarException(
            exception_id=data["exception_id"],
            date=date_type.fromisoformat(data["date"]),
            type=exc_type,
            label=data.get("label", ""),
            override_date=override_date,
        )
