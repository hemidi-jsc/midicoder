"""
Calendar Engine — tính toán business day, holiday, calendar exceptions.

Module này cung cấp:
- BusinessDayCalculator: tính toán ngày làm việc (loại trừ weekend + holiday)
- CalendarEngine: engine chính để apply calendar exceptions lên schedule

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from midicoder.packs.cp31_scheduler.models import (
    CalendarException,
    CalendarSet,
    ExceptionType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class BusinessDayCalculator:
    """Tính toán ngày làm việc.

    Business day = weekday (Mon-Fri) trừ đi holidays.
    Chủ Nhật (6) và Thứ Bảy (5) không phải business day.

    Ví dụ:
        >>> calc = BusinessDayCalculator()
        >>> calc.is_business_day(date(2026, 5, 20))  # Thứ Tư
        True
        >>> calc.is_business_day(date(2026, 5, 18))  # Chủ Nhật
        False
    """

    @staticmethod
    def is_business_day(d: date, calendar_set: Optional[CalendarSet] = None) -> bool:
        """Kiểm tra xem một ngày có phải business day không.

        Args:
            d: Ngày cần kiểm tra.
            calendar_set: CalendarSet chứa holidays (nếu có).

        Returns:
            True nếu là business day.

        Raises:
            MidicoderError: Nếu ngày invalid.
        """
        if d is None:
            raise EM.raise_error(
                ErrorCode.CP31_BUSINESS_DAY_ERROR,
                reason="Ngày không được None",
            )

        # Python weekday(): Mon=0, ..., Sun=6
        # Weekend = Sat(5) và Sun(6)
        if d.weekday() >= 5:
            return False

        # Check holiday
        if calendar_set and calendar_set.is_exception_date(d):
            return False

        return True

    @staticmethod
    def next_business_day(d: date, calendar_set: Optional[CalendarSet] = None) -> date:
        """Tìm business day tiếp theo sau một ngày.

        Args:
            d: Ngày bắt đầu tìm.
            calendar_set: CalendarSet chứa holidays (nếu có).

        Returns:
            Business day tiếp theo.

        Raises:
            MidicoderError: Nếu không tìm được.
        """
        from datetime import timedelta

        candidate = d + timedelta(days=1)
        max_iterations = 366 * 2  # Max 2 years
        for _ in range(max_iterations):
            if BusinessDayCalculator.is_business_day(candidate, calendar_set):
                return candidate
            candidate += timedelta(days=1)

        raise EM.raise_error(
            ErrorCode.CP31_BUSINESS_DAY_ERROR,
            start_date=str(d),
            reason="Không tìm được business day trong 2 năm tới",
        )

    @staticmethod
    def prev_business_day(d: date, calendar_set: Optional[CalendarSet] = None) -> date:
        """Tìm business day trước đó của một ngày.

        Args:
            d: Ngày bắt đầu tìm.
            calendar_set: CalendarSet chứa holidays (nếu có).

        Returns:
            Business day trước đó.

        Raises:
            MidicoderError: Nếu không tìm được.
        """
        from datetime import timedelta

        candidate = d - timedelta(days=1)
        max_iterations = 366 * 2
        for _ in range(max_iterations):
            if BusinessDayCalculator.is_business_day(candidate, calendar_set):
                return candidate
            candidate -= timedelta(days=1)

        raise EM.raise_error(
            ErrorCode.CP31_BUSINESS_DAY_ERROR,
            start_date=str(d),
            reason="Không tìm được business day trước đó",
        )

    @staticmethod
    def business_days_between(start: date, end: date, calendar_set: Optional[CalendarSet] = None) -> int:
        """Đếm số business day giữa hai ngày.

        Args:
            start: Ngày bắt đầu (không include).
            end: Ngày kết thúc (include).

        Returns:
            Số business day.
        """
        from datetime import timedelta

        count = 0
        current = start + timedelta(days=1)
        while current <= end:
            if BusinessDayCalculator.is_business_day(current, calendar_set):
                count += 1
            current += timedelta(days=1)
        return count


class CalendarEngine:
    """Engine chính để apply calendar exceptions lên schedule.

    Sử dụng CalendarSet để skip holidays, business days,
    và adjust scheduled times.

    Ví dụ:
        >>> calendar = CalendarSet(calendar_set_id="us", name="US Holidays")
        >>> engine = CalendarEngine(calendar)
        >>> # Check if May 1 should be skipped
        >>> engine.should_skip(date(2026, 5, 1))
        True
    """

    def __init__(self, calendar_set: CalendarSet) -> None:
        """Initialise CalendarEngine.

        Args:
            calendar_set: CalendarSet chứa exceptions.
        """
        self.calendar_set = calendar_set

    def should_skip(self, d: date) -> bool:
        """Kiểm tra xem một ngày có nên skip không.

        Args:
            d: Ngày cần kiểm tra.

        Returns:
            True nếu là holiday hoặc skip exception.
        """
        if not self.calendar_set.is_exception_date(d):
            return False

        for exc in self.calendar_set.get_exceptions():
            if exc.date == d and exc.type in (ExceptionType.HOLIDAY, ExceptionType.SKIP):
                return True

        return False

    def adjust_date(self, d: date) -> date:
        """Điều chỉnh một ngày sang business day gần nhất nếu nó là holiday.

        Nếu ngày là holiday/skip, chuyển sang next business day.
        Nếu ngày là override, chuyển sang override_date.

        Args:
            d: Ngày cần điều chỉnh.

        Returns:
            Ngày đã điều chỉnh.
        """
        if not self.calendar_set.is_exception_date(d):
            return d

        for exc in self.calendar_set.get_exceptions():
            if exc.date == d:
                if exc.type == ExceptionType.OVERRIDE and exc.override_date:
                    return exc.override_date
                elif exc.type in (ExceptionType.HOLIDAY, ExceptionType.SKIP):
                    return BusinessDayCalculator.next_business_day(d, self.calendar_set)

        return d

    def skip_holidays(self, scheduled_time: datetime) -> datetime:
        """Skip holidays cho một scheduled time.

        Nếu scheduled_time rơi vào holiday, chuyển sang next business day
        cùng giờ.

        Args:
            scheduled_time: Thời gian đã schedule.

        Returns:
            Thời gian đã điều chỉnh.
        """
        sched_date = scheduled_time.date()
        adjusted = self.adjust_date(sched_date)
        return adjusted.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=scheduled_time.second,
            microsecond=scheduled_time.microsecond,
        )

    def get_holidays_in_range(self, start: date, end: date) -> list[CalendarException]:
        """Lấy danh sách holidays trong khoảng thời gian.

        Args:
            start: Ngày bắt đầu.
            end: Ngày kết thúc.

        Returns:
            Danh sách CalendarException trong khoảng.
        """
        result = []
        for exc in self.calendar_set.get_exceptions():
            if start <= exc.date <= end and exc.type in (ExceptionType.HOLIDAY, ExceptionType.SKIP):
                result.append(exc)
        return sorted(result, key=lambda x: x.date)
