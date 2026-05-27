"""
Unit tests cho CalendarEngine và BusinessDayCalculator.
"""

import pytest
from datetime import date

from midicoder.packs.cp31_scheduler.calendar_engine import (
    BusinessDayCalculator,
    CalendarEngine,
)
from midicoder.packs.cp31_scheduler.models import (
    CalendarException,
    CalendarSet,
    ExceptionType,
)
from midicoder.errors import MidicoderError


class TestBusinessDayCalculator:
    """Test BusinessDayCalculator."""

    def test_weekday_is_business_day(self):
        """Thứ Tư là business day."""
        # May 20, 2026 is Wednesday
        assert BusinessDayCalculator.is_business_day(date(2026, 5, 20)) is True

    def test_saturday_not_business_day(self):
        """Thứ Bảy không phải business day."""
        # May 16, 2026 is Saturday
        assert BusinessDayCalculator.is_business_day(date(2026, 5, 16)) is False

    def test_sunday_not_business_day(self):
        """Chủ Nhật không phải business day."""
        # May 17, 2026 is Sunday
        assert BusinessDayCalculator.is_business_day(date(2026, 5, 17)) is False

    def test_holiday_not_business_day(self):
        """Holiday không phải business day."""
        cal = CalendarSet(calendar_set_id="test", name="Test")
        cal.add_exception(CalendarException(
            exception_id="x1",
            date=date(2026, 5, 20),
            type=ExceptionType.HOLIDAY,
        ))
        # May 20 is Wednesday, but holiday
        assert BusinessDayCalculator.is_business_day(date(2026, 5, 20), cal) is False

    def test_next_business_day_from_friday(self):
        """Next business day từ Thứ Sáu là Thứ Hai."""
        # May 15, 2026 is Friday
        result = BusinessDayCalculator.next_business_day(date(2026, 5, 15))
        assert result == date(2026, 5, 18)  # Monday

    def test_next_business_day_from_saturday(self):
        """Next business day từ Thứ Bảy là Thứ Hai."""
        # May 16, 2026 is Saturday
        result = BusinessDayCalculator.next_business_day(date(2026, 5, 16))
        assert result == date(2026, 5, 18)  # Monday

    def test_prev_business_day_from_monday(self):
        """Prev business day từ Thứ Hai là Thứ Sáu."""
        # May 18, 2026 is Monday
        result = BusinessDayCalculator.prev_business_day(date(2026, 5, 18))
        assert result == date(2026, 5, 15)  # Friday

    def test_business_days_between(self):
        """Đếm business days giữa hai ngày."""
        # May 15 (Fri) to May 22 (Fri) = 5 business days
        count = BusinessDayCalculator.business_days_between(
            date(2026, 5, 15), date(2026, 5, 22)
        )
        assert count == 5

    def test_none_date_raises_error(self):
        """None date throw error."""
        with pytest.raises(MidicoderError):
            BusinessDayCalculator.is_business_day(None)


class TestCalendarEngine:
    """Test CalendarEngine."""

    def setup_method(self):
        """Setup test fixture."""
        cal = CalendarSet(calendar_set_id="test", name="Test")
        cal.add_exception(CalendarException(
            exception_id="new-year",
            date=date(2026, 1, 1),
            type=ExceptionType.HOLIDAY,
            label="New Year",
        ))
        cal.add_exception(CalendarException(
            exception_id="independence",
            date=date(2026, 7, 4),
            type=ExceptionType.HOLIDAY,
            label="Independence Day",
        ))
        cal.add_exception(CalendarException(
            exception_id="observed",
            date=date(2026, 12, 25),
            type=ExceptionType.OVERRIDE,
            override_date=date(2026, 12, 24),
        ))
        self.engine = CalendarEngine(cal)

    def test_should_skip_holiday(self):
        """Holiday nên được skip."""
        assert self.engine.should_skip(date(2026, 1, 1)) is True

    def test_should_not_skip_normal_day(self):
        """Normal day không nên skip."""
        assert self.engine.should_skip(date(2026, 1, 2)) is False

    def test_adjust_date_skips_holiday(self):
        """Adjust date skip holiday."""
        # Jan 1 is holiday, should move to next business day
        result = self.engine.adjust_date(date(2026, 1, 1))
        assert result > date(2026, 1, 1)
        assert BusinessDayCalculator.is_business_day(result)

    def test_adjust_date_override(self):
        """Adjust date với override."""
        # Dec 25 has override to Dec 24
        result = self.engine.adjust_date(date(2026, 12, 25))
        assert result == date(2026, 12, 24)

    def test_adjust_normal_date_unchanged(self):
        """Normal date không thay đổi."""
        result = self.engine.adjust_date(date(2026, 1, 2))
        assert result == date(2026, 1, 2)

    def test_get_holidays_in_range(self):
        """Lấy holidays trong khoảng thời gian."""
        holidays = self.engine.get_holidays_in_range(
            date(2026, 1, 1), date(2026, 6, 30)
        )
        # July 4 is out of range, only New Year is within range
        assert len(holidays) == 1
        assert holidays[0].date == date(2026, 1, 1)
