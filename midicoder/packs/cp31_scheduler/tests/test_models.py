"""
Unit tests cho CP31 models.

Test validation, serialization, và __post_init__ cho tất cả model classes.
"""

import pytest
from datetime import date

from midicoder.packs.cp31_scheduler.models import (
    CalendarException,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
    ScheduleType,
)
from midicoder.errors import MidicoderError


class TestCronSchedule:
    """Test CronSchedule model."""

    def test_create_valid_cron_schedule(self):
        """Tạo CronSchedule valid thành công."""
        schedule = CronSchedule(
            schedule_id="daily-backup",
            cron_expression="0 2 * * *",
        )
        assert schedule.schedule_id == "daily-backup"
        assert schedule.cron_expression == "0 2 * * *"
        assert schedule.timezone == "UTC"
        assert schedule.enabled is True

    def test_create_with_custom_timezone(self):
        """Tạo CronSchedule với timezone tùy chỉnh."""
        schedule = CronSchedule(
            schedule_id="asia-schedule",
            cron_expression="0 9 * * 1-5",
            timezone="Asia/Ho_Chi_Minh",
            enabled=False,
        )
        assert schedule.timezone == "Asia/Ho_Chi_Minh"
        assert schedule.enabled is False

    def test_empty_schedule_id_raises_error(self):
        """schedule_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            CronSchedule(schedule_id="", cron_expression="0 * * * *")

    def test_empty_cron_expression_raises_error(self):
        """cron_expression rỗng throw error."""
        with pytest.raises(MidicoderError):
            CronSchedule(schedule_id="test", cron_expression="")

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        original = CronSchedule(
            schedule_id="test",
            cron_expression="0 0 * * *",
            timezone="Asia/Tokyo",
            enabled=False,
            metadata={"key": "value"},
        )
        data = original.to_dict()
        restored = CronSchedule.from_dict(data)
        assert restored.schedule_id == original.schedule_id
        assert restored.cron_expression == original.cron_expression
        assert restored.timezone == original.timezone
        assert restored.enabled == original.enabled
        assert restored.metadata == original.metadata


class TestRecurrenceSchedule:
    """Test RecurrenceSchedule model."""

    def test_create_daily_recurrence(self):
        """Tạo RecurrenceSchedule daily thành công."""
        schedule = RecurrenceSchedule(
            schedule_id="daily-report",
            frequency=RecurrenceFrequency.DAILY,
        )
        assert schedule.frequency == RecurrenceFrequency.DAILY
        assert schedule.interval == 1

    def test_create_weekly_with_days(self):
        """Tạo weekly với days_of_week."""
        schedule = RecurrenceSchedule(
            schedule_id="weekly-meeting",
            frequency=RecurrenceFrequency.WEEKLY,
            days_of_week=[1, 3, 5],  # Mon, Wed, Fri
        )
        assert schedule.days_of_week == [1, 3, 5]

    def test_create_monthly_with_day(self):
        """Tạo monthly với day_of_month."""
        schedule = RecurrenceSchedule(
            schedule_id="monthly-billing",
            frequency=RecurrenceFrequency.MONTHLY,
            day_of_month=15,
        )
        assert schedule.day_of_month == 15

    def test_empty_schedule_id_raises_error(self):
        """schedule_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            RecurrenceSchedule(schedule_id="", frequency=RecurrenceFrequency.DAILY)

    def test_invalid_interval_raises_error(self):
        """interval < 1 throw error."""
        with pytest.raises(MidicoderError):
            RecurrenceSchedule(
                schedule_id="test",
                frequency=RecurrenceFrequency.DAILY,
                interval=0,
            )

    def test_invalid_day_of_week_raises_error(self):
        """days_of_week ngoài range [0,6] throw error."""
        with pytest.raises(MidicoderError):
            RecurrenceSchedule(
                schedule_id="test",
                frequency=RecurrenceFrequency.WEEKLY,
                days_of_week=[7],
            )

    def test_invalid_day_of_month_raises_error(self):
        """day_of_month ngoài range [1,31] throw error."""
        with pytest.raises(MidicoderError):
            RecurrenceSchedule(
                schedule_id="test",
                frequency=RecurrenceFrequency.MONTHLY,
                day_of_month=32,
            )

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        original = RecurrenceSchedule(
            schedule_id="test",
            frequency=RecurrenceFrequency.WEEKLY,
            interval=2,
            days_of_week=[1, 3],
            timezone="America/New_York",
        )
        data = original.to_dict()
        restored = RecurrenceSchedule.from_dict(data)
        assert restored.schedule_id == original.schedule_id
        assert restored.frequency == original.frequency
        assert restored.interval == original.interval
        assert restored.days_of_week == original.days_of_week


class TestCalendarSet:
    """Test CalendarSet model."""

    def test_create_calendar_set(self):
        """Tạo CalendarSet thành công."""
        cal = CalendarSet(
            calendar_set_id="us-holidays",
            name="US Federal Holidays",
            country="US",
        )
        assert cal.calendar_set_id == "us-holidays"
        assert cal.country == "US"

    def test_empty_calendar_set_id_raises_error(self):
        """calendar_set_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            CalendarSet(calendar_set_id="", name="Test")

    def test_add_exception(self):
        """Thêm exception và kiểm tra."""
        cal = CalendarSet(calendar_set_id="test", name="Test")
        exc = CalendarException(
            exception_id="x1",
            date=date(2026, 1, 1),
            type=ExceptionType.HOLIDAY,
            label="New Year",
        )
        cal.add_exception(exc)
        assert len(cal.get_exceptions()) == 1

    def test_is_exception_date(self):
        """Kiểm tra exception date."""
        cal = CalendarSet(calendar_set_id="test", name="Test")
        exc = CalendarException(
            exception_id="x1",
            date=date(2026, 7, 4),
            type=ExceptionType.HOLIDAY,
        )
        cal.add_exception(exc)
        assert cal.is_exception_date(date(2026, 7, 4)) is True
        assert cal.is_exception_date(date(2026, 7, 5)) is False

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        exc = CalendarException(
            exception_id="x1",
            date=date(2026, 12, 25),
            type=ExceptionType.HOLIDAY,
            label="Christmas",
        )
        original = CalendarSet(
            calendar_set_id="test",
            name="Test",
            exceptions=[exc],
            country="US",
        )
        data = original.to_dict()
        restored = CalendarSet.from_dict(data)
        assert restored.calendar_set_id == original.calendar_set_id
        assert len(restored.get_exceptions()) == 1


class TestCalendarException:
    """Test CalendarException model."""

    def test_create_exception(self):
        """Tạo CalendarException thành công."""
        exc = CalendarException(
            exception_id="x1",
            date=date(2026, 5, 1),
            type=ExceptionType.HOLIDAY,
            label="Labor Day",
        )
        assert exc.type == ExceptionType.HOLIDAY
        assert exc.label == "Labor Day"

    def test_create_override_exception(self):
        """Tạo override exception với override_date."""
        exc = CalendarException(
            exception_id="x2",
            date=date(2026, 7, 4),
            type=ExceptionType.OVERRIDE,
            override_date=date(2026, 7, 5),
        )
        assert exc.override_date == date(2026, 7, 5)

    def test_empty_exception_id_raises_error(self):
        """exception_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            CalendarException(
                exception_id="",
                date=date(2026, 1, 1),
                type=ExceptionType.HOLIDAY,
            )


class TestEnums:
    """Test enum values."""

    def test_schedule_type_values(self):
        """ScheduleType enum có đủ values."""
        assert ScheduleType.CRON == "cron"
        assert ScheduleType.RECURRENCE == "recurrence"
        assert ScheduleType.CALENDAR == "calendar"

    def test_recurrence_frequency_values(self):
        """RecurrenceFrequency enum có đủ values."""
        assert RecurrenceFrequency.DAILY == "daily"
        assert RecurrenceFrequency.WEEKLY == "weekly"
        assert RecurrenceFrequency.MONTHLY == "monthly"
        assert RecurrenceFrequency.YEARLY == "yearly"
        assert RecurrenceFrequency.LAST_BUSINESS_DAY == "last_business_day"

    def test_exception_type_values(self):
        """ExceptionType enum có đủ values."""
        assert ExceptionType.HOLIDAY == "holiday"
        assert ExceptionType.SKIP == "skip"
        assert ExceptionType.OVERRIDE == "override"
