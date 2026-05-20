"""
Unit tests cho SchedulerParser.
"""

import pytest
from datetime import date

from midicoder.emitters.core.cp31_scheduler.parser import SchedulerParser
from midicoder.emitters.core.cp31_scheduler.models import (
    CalendarException,
    CalendarSchedule,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
)
from midicoder.errors import MidicoderError


class TestSchedulerParser:
    """Test SchedulerParser."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = SchedulerParser()

    def test_parse_cron_schedule(self):
        """Parse cron schedule."""
        data = {
            "type": "cron",
            "schedule_id": "daily-backup",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
        }
        result = self.parser.parse(data)
        assert isinstance(result, CronSchedule)
        assert result.schedule_id == "daily-backup"
        assert result.cron_expression == "0 2 * * *"

    def test_parse_recurrence_schedule(self):
        """Parse recurrence schedule."""
        data = {
            "type": "recurrence",
            "schedule_id": "weekly-report",
            "frequency": "weekly",
            "interval": 1,
            "days_of_week": [1],
        }
        result = self.parser.parse(data)
        assert isinstance(result, RecurrenceSchedule)
        assert result.frequency == RecurrenceFrequency.WEEKLY

    def test_parse_calendar_schedule(self):
        """Parse calendar schedule."""
        data = {
            "type": "calendar",
            "schedule_id": "payroll",
            "base_schedule": {"cron_expression": "0 0 1 * *"},
            "calendar_set_id": "us-holidays",
            "skip_holidays": True,
        }
        result = self.parser.parse(data)
        assert isinstance(result, CalendarSchedule)
        assert result.calendar_set_id == "us-holidays"
        assert result.skip_holidays is True

    def test_parse_calendar_set(self):
        """Parse calendar set."""
        data = {
            "type": "calendar_set",
            "calendar_set_id": "us",
            "name": "US Holidays",
            "country": "US",
            "exceptions": [
                {
                    "exception_id": "new-year",
                    "date": "2026-01-01",
                    "type": "holiday",
                    "label": "New Year",
                }
            ],
        }
        result = self.parser.parse(data)
        assert isinstance(result, CalendarSet)
        assert len(result.get_exceptions()) == 1

    def test_parse_exception(self):
        """Parse single exception."""
        data = {
            "schedule_type": "exception",
            "exception_id": "test",
            "date": "2026-12-25",
            "type": "holiday",
            "label": "Christmas",
        }
        result = self.parser.parse(data)
        assert isinstance(result, CalendarException)

    def test_auto_detect_cron(self):
        """Auto detect cron schedule."""
        data = {
            "schedule_id": "test",
            "cron_expression": "0 0 * * *",
        }
        result = self.parser.parse(data)
        assert isinstance(result, CronSchedule)

    def test_auto_detect_recurrence(self):
        """Auto detect recurrence schedule."""
        data = {
            "schedule_id": "test",
            "frequency": "daily",
        }
        result = self.parser.parse(data)
        assert isinstance(result, RecurrenceSchedule)

    def test_parse_empty_data_raises_error(self):
        """Empty data throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({})

    def test_parse_none_raises_error(self):
        """None data throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse(None)

    def test_parse_unknown_type_raises_error(self):
        """Unknown type throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({"type": "unknown"})

    def test_parse_cron_missing_id_raises_error(self):
        """Cron thiếu schedule_id throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({"type": "cron", "cron_expression": "* * * * *"})

    def test_parse_cron_missing_expression_raises_error(self):
        """Cron thiếu cron_expression throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse({"type": "cron", "schedule_id": "test"})

    def test_parse_list(self):
        """Parse danh sách schedules."""
        data = [
            {"type": "cron", "schedule_id": "s1", "cron_expression": "0 0 * * *"},
            {"type": "cron", "schedule_id": "s2", "cron_expression": "0 12 * * *"},
        ]
        results = self.parser.parse_list(data)
        assert len(results) == 2
        assert all(isinstance(r, CronSchedule) for r in results)
