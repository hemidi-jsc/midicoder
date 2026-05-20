"""
Cron expression parser — tự implement, không external dependency.

Module này cung cấp CronParser để parse, validate và tính toán
next_run_time / prev_run_time cho standard cron expression.

Support:
- Standard 5/6 field: minute hour day_of_month month day_of_week [year]
- Special chars: * (wildcard), , (list), - (range), / (step)
- Special strings: @yearly, @monthly, @weekly, @daily, @hourly
- Named months/days: JAN, FEB, ..., MON, TUE, ...

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# Bảng ánh xạ tên tháng/ngày sang số
MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

DAY_NAMES = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}

# Shortcut special strings → cron expression
SPECIAL_STRINGS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# Giới hạn của từng field
FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 6),
    "year": (1970, 9999),
}


@dataclass
class CronField:
    """Biểu diễn một field đã parse trong cron expression.

    Attributes:
        values: Tập giá trị match.
        min_val: Giá trị nhỏ nhất của field.
        max_val: Giá trị lớn nhất của field.
        raw: Raw string của field.
    """

    values: set[int] = field(default_factory=set)
    min_val: int = 0
    max_val: int = 59
    raw: str = ""

    def __post_init__(self) -> None:
        """Nếu values rỗng, fill toàn bộ range."""
        if not self.values:
            self.values = set(range(self.min_val, self.max_val + 1))


@dataclass
class ParsedCron:
    """Kết quả parse của một cron expression.

    Attributes:
        expression: Cron expression gốc.
        minute: Field phút.
        hour: Field giờ.
        day_of_month: Field ngày trong tháng.
        month: Field tháng.
        day_of_week: Field ngày trong tuần.
        year: Field năm (nếu có).
        timezone: Timezone (mặc định UTC).
    """

    expression: str
    minute: CronField
    hour: CronField
    day_of_month: CronField
    month: CronField
    day_of_week: CronField
    year: Optional[CronField] = None
    timezone: str = "UTC"


class CronParser:
    """Parser cho standard cron expression.

    Support 5 hoặc 6 field: minute hour day_of_month month day_of_week [year]
    Support special strings: @yearly, @monthly, @weekly, @daily, @hourly

    Ví dụ:
        >>> parser = CronParser()
        >>> parsed = parser.parse("0 9 * * 1-5")
        >>> parsed.minute.values
        {0}
        >>> parsed.day_of_week.values
        {1, 2, 3, 4, 5}
    """

    def parse(self, expression: str, timezone: str = "UTC") -> ParsedCron:
        """Parse cron expression thành ParsedCron.

        Args:
            expression: Cron expression string.
            timezone: Timezone (mặc định UTC).

        Returns:
            ParsedCron object.

        Raises:
            MidicoderError: Nếu expression invalid.
        """
        if not expression or not expression.strip():
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_CRON_EXPR,
                expression=expression,
                reason="Expression không được rỗng",
            )

        expr = expression.strip()

        # Resolve special string
        if expr.lower() in SPECIAL_STRINGS:
            expr = SPECIAL_STRINGS[expr.lower()]

        # Split fields
        parts = expr.split()
        if len(parts) not in (5, 6):
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_CRON_EXPR,
                expression=expr,
                reason=f"Cron cần 5 hoặc 6 field, nhận được {len(parts)}",
            )

        try:
            minute = self._parse_field(parts[0], "minute")
            hour = self._parse_field(parts[1], "hour")
            dom = self._parse_field(parts[2], "day_of_month")
            month = self._parse_field(parts[3], "month")
            dow = self._parse_field(parts[4], "day_of_week")
            year = None
            if len(parts) == 6:
                year = self._parse_field(parts[5], "year")
        except ValueError as e:
            raise EM.raise_error(
                ErrorCode.CP31_INVALID_CRON_EXPR,
                expression=expr,
                reason=str(e),
            )

        return ParsedCron(
            expression=expr,
            minute=minute,
            hour=hour,
            day_of_month=dom,
            month=month,
            day_of_week=dow,
            year=year,
            timezone=timezone,
        )

    def _parse_field(self, raw: str, field_name: str) -> CronField:
        """Parse một field cron thành CronField.

        Args:
            raw: Raw string của field.
            field_name: Tên field để validate range.

        Returns:
            CronField object.
        """
        min_val, max_val = FIELD_RANGES[field_name]
        values = set()

        # Replace named months/days
        upper_raw = raw.upper()
        for name, num in MONTH_NAMES.items():
            upper_raw = upper_raw.replace(name, str(num))
        for name, num in DAY_NAMES.items():
            upper_raw = upper_raw.replace(name, str(num))

        # Parse comma-separated list
        parts = upper_raw.split(",")
        for part in parts:
            part = part.strip()
            if "/" in part:
                # Step: start/step or */step
                base, step_str = part.split("/", 1)
                step = int(step_str)
                if base == "*":
                    start = min_val
                    end = max_val
                elif "-" in base:
                    start, end = map(int, base.split("-", 1))
                else:
                    start = int(base)
                    end = max_val
                for v in range(start, end + 1, step):
                    values.add(v)
            elif "-" in part:
                # Range
                start, end = map(int, part.split("-", 1))
                for v in range(start, end + 1):
                    values.add(v)
            elif part == "*":
                # Wildcard
                values = set(range(min_val, max_val + 1))
            else:
                # Single value
                values.add(int(part))

        # Validate range
        for v in values:
            if v < min_val or v > max_val:
                raise EM.raise_error(
                    ErrorCode.CP31_INVALID_CRON_EXPR,
                    field=field_name,
                    value=v,
                    reason=f"Giá trị {v} vượt range [{min_val}, {max_val}] cho {field_name}",
                )

        return CronField(values=values, min_val=min_val, max_val=max_val, raw=raw)

    def next_run_time(self, parsed: ParsedCron, after: Optional[datetime] = None) -> datetime:
        """Tính thời điểm chạy tiếp theo.

        Args:
            parsed: ParsedCron đã parse.
            after: Tính từ thời điểm nào (mặc định now).

        Returns:
            datetime của lần chạy tiếp theo.

        Raises:
            MidicoderError: Nếu không tính được.
        """
        if after is None:
            after = datetime.utcnow()

        # Start from next minute
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Brute-force search (max 4 years ahead)
        max_iterations = 366 * 24 * 60 * 4  # ~4 years of minutes
        for _ in range(max_iterations):
            if self._matches(candidate, parsed):
                return candidate
            candidate += timedelta(minutes=1)

        raise EM.raise_error(
            ErrorCode.CP31_NEXT_RUN_CALC_FAILED,
            expression=parsed.expression,
            reason="Không tìm thấy thời điểm chạy trong 4 năm tới",
        )

    def prev_run_time(self, parsed: ParsedCron, before: Optional[datetime] = None) -> datetime:
        """Tính thời điểm chạy vừa qua.

        Args:
            parsed: ParsedCron đã parse.
            before: Tính trước thời điểm nào (mặc định now).

        Returns:
            datetime của lần chạy vừa qua.

        Raises:
            MidicoderError: Nếu không tính được.
        """
        if before is None:
            before = datetime.utcnow()

        candidate = before.replace(second=0, microsecond=0) - timedelta(minutes=1)

        max_iterations = 366 * 24 * 60 * 4
        for _ in range(max_iterations):
            if self._matches(candidate, parsed):
                return candidate
            candidate -= timedelta(minutes=1)
            if candidate.year < 1970:
                break

        raise EM.raise_error(
            ErrorCode.CP31_NEXT_RUN_CALC_FAILED,
            expression=parsed.expression,
            reason="Không tìm thấy thời điểm chạy trước đó",
        )

    def _matches(self, dt: datetime, parsed: ParsedCron) -> bool:
        """Kiểm tra xem một datetime có match cron expression không.

        Args:
            dt: DateTime cần kiểm tra.
            parsed: ParsedCron.

        Returns:
            True nếu match.
        """
        if dt.minute not in parsed.minute.values:
            return False
        if dt.hour not in parsed.hour.values:
            return False
        if dt.month not in parsed.month.values:
            return False
        if dt.day not in parsed.day_of_month.values:
            return False
        if dt.weekday() in (0, 1, 2, 3, 4, 5, 6):
            # Python weekday(): Mon=0..Sun=6
            # Cron day_of_week: Sun=0..Sat=6
            cron_dow = (dt.weekday() + 1) % 7
            if cron_dow not in parsed.day_of_week.values:
                return False
        if parsed.year and dt.year not in parsed.year.values:
            return False
        return True

    def validate(self, expression: str) -> bool:
        """Validate cron expression.

        Args:
            expression: Cron expression string.

        Returns:
            True nếu valid.
        """
        try:
            self.parse(expression)
            return True
        except Exception:
            return False

    def to_dict(self, parsed: ParsedCron) -> dict[str, Any]:
        """Chuyển ParsedCron sang dict.

        Args:
            parsed: ParsedCron object.

        Returns:
            Dict representation.
        """
        return {
            "expression": parsed.expression,
            "minute": sorted(parsed.minute.values),
            "hour": sorted(parsed.hour.values),
            "day_of_month": sorted(parsed.day_of_month.values),
            "month": sorted(parsed.month.values),
            "day_of_week": sorted(parsed.day_of_week.values),
            "year": sorted(parsed.year.values) if parsed.year else None,
            "timezone": parsed.timezone,
        }
