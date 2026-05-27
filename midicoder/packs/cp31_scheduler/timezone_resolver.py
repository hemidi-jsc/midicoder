"""
Timezone Resolver — phân giải timezone name thành timezone object.

Module này cung cấp TimeZoneResolver để:
- Resolve timezone name (vd: "America/New_York") thành timezone object
- Convert giữa các timezones
- Support DST transition

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo, timedelta
from typing import Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class FixedOffsetTimeZone(tzinfo):
    """Timezone với fixed offset — không xử lý DST.

    Dùng cho các timezone không có daylight saving time.

    Attributes:
        offset: Offset từ UTC (timedelta).
        name: Tên timezone.
    """

    def __init__(self, offset: timedelta, name: str) -> None:
        """Initialise FixedOffsetTimeZone.

        Args:
            offset: Offset từ UTC.
            name: Tên timezone.
        """
        self._offset = offset
        self._name = name

    def utcoffset(self, dt: Optional[datetime] = None) -> timedelta:
        """Trả về offset từ UTC."""
        return self._offset

    def tzname(self, dt: Optional[datetime] = None) -> str:
        """Trả về tên timezone."""
        return self._name

    def dst(self, dt: Optional[datetime] = None) -> timedelta:
        """DST offset — luôn 0 cho fixed timezone."""
        return timedelta(0)

    def __repr__(self) -> str:
        """String representation."""
        total_minutes = int(self._offset.total_seconds() / 60)
        sign = "+" if total_minutes >= 0 else "-"
        abs_minutes = abs(total_minutes)
        hours, minutes = divmod(abs_minutes, 60)
        return f"FixedOffsetTimeZone({self._name}, UTC{sign}{hours:02d}:{minutes:02d})"


class TimeZoneResolver:
    """Phân giải timezone name thành timezone object.

    Support các timezone phổ biến và custom fixed offset.

    Ví dụ:
        >>> resolver = TimeZoneResolver()
        >>> tz = resolver.resolve("America/New_York")
        >>> tz is not None
        True
    """

    # Bảng ánh xạ timezone phổ biến → fixed offset (không DST)
    # Trong generated code, user có thể thay bằng pytz/dateutil
    _KNOWN_TIMEZONES: dict[str, timedelta] = {
        "UTC": timedelta(0),
        "GMT": timedelta(0),
        "US/Eastern": timedelta(hours=-5),
        "US/Central": timedelta(hours=-6),
        "US/Mountain": timedelta(hours=-7),
        "US/Pacific": timedelta(hours=-8),
        "America/New_York": timedelta(hours=-5),
        "America/Chicago": timedelta(hours=-6),
        "America/Denver": timedelta(hours=-7),
        "America/Los_Angeles": timedelta(hours=-8),
        "America/Toronto": timedelta(hours=-5),
        "America/Vancouver": timedelta(hours=-8),
        "Europe/London": timedelta(0),
        "Europe/Paris": timedelta(hours=1),
        "Europe/Berlin": timedelta(hours=1),
        "Europe/Moscow": timedelta(hours=3),
        "Asia/Tokyo": timedelta(hours=9),
        "Asia/Shanghai": timedelta(hours=8),
        "Asia/Hong_Kong": timedelta(hours=8),
        "Asia/Singapore": timedelta(hours=8),
        "Asia/Seoul": timedelta(hours=9),
        "Asia/Kolkata": timedelta(hours=5, minutes=30),
        "Asia/Bangkok": timedelta(hours=7),
        "Asia/Ho_Chi_Minh": timedelta(hours=7),
        "Asia/Hanoi": timedelta(hours=7),
        "Australia/Sydney": timedelta(hours=10),
        "Australia/Perth": timedelta(hours=8),
        "Pacific/Auckland": timedelta(hours=12),
    }

    def resolve(self, name: str) -> tzinfo:
        """Phân giải tên timezone thành timezone object.

        Args:
            name: Tên timezone (vd: "America/New_York", "UTC+7").

        Returns:
            Timezone object.

        Raises:
            MidicoderError: Nếu timezone không recognized.
        """
        if not name or not name.strip():
            raise EM.raise_error(
                ErrorCode.CP31_TIMEZONE_NOT_FOUND,
                name=name,
                reason="Tên timezone không được rỗng",
            )

        name = name.strip()

        # Try known timezones
        if name in self._KNOWN_TIMEZONES:
            return FixedOffsetTimeZone(self._KNOWN_TIMEZONES[name], name)

        # Try UTC+offset format (vd: "UTC+7", "UTC-5:30")
        utc_match = self._parse_utc_offset(name)
        if utc_match:
            return FixedOffsetTimeZone(utc_match, name)

        raise EM.raise_error(
            ErrorCode.CP31_TIMEZONE_NOT_FOUND,
            name=name,
            known=list(self._KNOWN_TIMEZONES.keys())[:10],
        )

    def _parse_utc_offset(self, name: str) -> Optional[timedelta]:
        """Parse UTC offset string thành timedelta.

        Support: "UTC+7", "UTC-5:30", "UTC+0530", "+0700", "-05:30"

        Args:
            name: Offset string.

        Returns:
            Timedelta nếu parse được, None nếu không.
        """
        import re

        match = re.match(r'^[Uu][Tt][Cc]?\s*([+-])(\d{1,2})(?::(\d{2}))?$', name)
        if not match:
            # Try pure offset like "+0700"
            match = re.match(r'^([+-])(\d{2}):?(\d{2})$', name)

        if match:
            sign = 1 if match.group(1) == "+" else -1
            hours = int(match.group(2))
            minutes = int(match.group(3)) if match.group(3) else 0
            total = sign * (hours * 60 + minutes)
            return timedelta(minutes=total)

        return None

    def convert(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime từ timezone này sang timezone khác.

        Cách hoạt động:
        1. Gắn timezone nguồn vào dt (nếu naive)
        2. Chuyển sang UTC: utc_dt = dt - from_offset
        3. Chuyển sang target: result = utc_dt + to_offset

        Args:
            dt: DateTime cần convert (naive hoặc aware).
            from_tz: Timezone nguồn.
            to_tz: Timezone đích.

        Returns:
            DateTime đã convert với timezone đích.
        """
        from_tz_obj = self.resolve(from_tz)
        to_tz_obj = self.resolve(to_tz)

        # Bước 1: Gắn timezone nguồn nếu dt naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=from_tz_obj)

        # Bước 2: Chuyển sang UTC (naive)
        from_offset = dt.utcoffset()
        if from_offset is None:
            from_offset = timedelta(0)
        utc_naive = dt - from_offset

        # Bước 3: Thêm offset đích và gắn timezone đích
        to_offset = to_tz_obj.utcoffset(utc_naive)
        result = utc_naive + to_offset
        return result.replace(tzinfo=to_tz_obj)

    def to_utc(self, dt: datetime, from_tz: str) -> datetime:
        """Convert datetime sang UTC.

        Args:
            dt: DateTime cần convert.
            from_tz: Timezone nguồn.

        Returns:
            DateTime trong UTC.
        """
        from_tz_obj = self.resolve(from_tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=from_tz_obj)

        utc_offset = dt.utcoffset()
        return (dt - utc_offset).replace(tzinfo=timezone.utc) if utc_offset else dt.replace(tzinfo=timezone.utc)

    def from_utc(self, dt: datetime, to_tz: str) -> datetime:
        """Convert từ UTC sang timezone khác.

        Args:
            dt: DateTime trong UTC.
            to_tz: Timezone đích.

        Returns:
            DateTime trong timezone đích.
        """
        to_tz_obj = self.resolve(to_tz)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        target_offset = to_tz_obj.utcoffset(dt)
        utc_offset = dt.utcoffset()
        return (dt + target_offset - (utc_offset if utc_offset else timedelta(0))).replace(tzinfo=to_tz_obj)

    def list_known(self) -> list[str]:
        """Lấy danh sách timezone đã biết.

        Returns:
            Danh sách tên timezone.
        """
        return sorted(self._KNOWN_TIMEZONES.keys())
