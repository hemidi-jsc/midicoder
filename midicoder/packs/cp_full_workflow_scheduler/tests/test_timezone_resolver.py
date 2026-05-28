"""
Unit tests cho TimeZoneResolver.
"""

import pytest
from datetime import datetime, timedelta

from midicoder.packs.cp_full_workflow_scheduler.timezone_resolver import (
    FixedOffsetTimeZone,
    TimeZoneResolver,
)
from midicoder.errors import MidicoderError


class TestFixedOffsetTimeZone:
    """Test FixedOffsetTimeZone."""

    def test_utc_offset(self):
        """Fixed offset UTC."""
        tz = FixedOffsetTimeZone(timedelta(0), "UTC")
        assert tz.utcoffset(None) == timedelta(0)
        assert tz.tzname(None) == "UTC"
        assert tz.dst(None) == timedelta(0)

    def test_positive_offset(self):
        """Fixed offset dương (UTC+7)."""
        tz = FixedOffsetTimeZone(timedelta(hours=7), "Asia/Ho_Chi_Minh")
        assert tz.utcoffset(None) == timedelta(hours=7)
        assert tz.tzname(None) == "Asia/Ho_Chi_Minh"

    def test_negative_offset(self):
        """Fixed offset âm (UTC-5)."""
        tz = FixedOffsetTimeZone(timedelta(hours=-5), "America/New_York")
        assert tz.utcoffset(None) == timedelta(hours=-5)


class TestTimeZoneResolver:
    """Test TimeZoneResolver."""

    def setup_method(self):
        """Setup test fixture."""
        self.resolver = TimeZoneResolver()

    def test_resolve_utc(self):
        """Resolve UTC timezone."""
        tz = self.resolver.resolve("UTC")
        assert tz.utcoffset(None) == timedelta(0)

    def test_resolve_america_new_york(self):
        """Resolve America/New_York."""
        tz = self.resolver.resolve("America/New_York")
        assert tz.utcoffset(None) == timedelta(hours=-5)

    def test_resolve_asia_tokyo(self):
        """Resolve Asia/Tokyo."""
        tz = self.resolver.resolve("Asia/Tokyo")
        assert tz.utcoffset(None) == timedelta(hours=9)

    def test_resolve_asia_ho_chi_minh(self):
        """Resolve Asia/Ho_Chi_Minh."""
        tz = self.resolver.resolve("Asia/Ho_Chi_Minh")
        assert tz.utcoffset(None) == timedelta(hours=7)

    def test_resolve_utc_plus_offset(self):
        """Resolve UTC+7."""
        tz = self.resolver.resolve("UTC+7")
        assert tz.utcoffset(None) == timedelta(hours=7)

    def test_resolve_utc_minus_offset(self):
        """Resolve UTC-5:30."""
        tz = self.resolver.resolve("UTC-5:30")
        assert tz.utcoffset(None) == timedelta(hours=-5, minutes=-30)

    def test_resolve_unknown_raises_error(self):
        """Unknown timezone throw error."""
        with pytest.raises(MidicoderError):
            self.resolver.resolve("Unknown/Timezone")

    def test_resolve_empty_raises_error(self):
        """Empty timezone throw error."""
        with pytest.raises(MidicoderError):
            self.resolver.resolve("")

    def test_convert_timezones(self):
        """Convert giữa 2 timezones."""
        # 9:00 UTC+7 = 2:00 UTC
        dt = datetime(2026, 5, 20, 9, 0, 0)
        result = self.resolver.convert(dt, "UTC+7", "UTC")
        assert result.hour == 2

    def test_to_utc(self):
        """Convert sang UTC."""
        dt = datetime(2026, 5, 20, 9, 0, 0)
        result = self.resolver.to_utc(dt, "UTC+7")
        assert result.hour == 2

    def test_from_utc(self):
        """Convert từ UTC."""
        dt = datetime(2026, 5, 20, 0, 0, 0)
        result = self.resolver.from_utc(dt, "UTC+7")
        assert result.hour == 7

    def test_list_known(self):
        """List known timezones."""
        known = self.resolver.list_known()
        assert "UTC" in known
        assert "Asia/Tokyo" in known
        assert len(known) > 10
