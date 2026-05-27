"""
Unit tests cho CronParser.

Test parse, validate, next_run_time, prev_run_time cho cron expressions.
"""

import pytest
from datetime import datetime

from midicoder.packs.cp31_scheduler.cron_parser import CronParser
from midicoder.errors import MidicoderError


class TestCronParserParse:
    """Test parse cron expression."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = CronParser()

    def test_parse_simple_expression(self):
        """Parse cron expression đơn giản."""
        parsed = self.parser.parse("0 9 * * *")
        assert 0 in parsed.minute.values
        assert 9 in parsed.hour.values
        assert len(parsed.day_of_month.values) == 31  # all days

    def test_parse_expression_with_range(self):
        """Parse cron expression với range."""
        parsed = self.parser.parse("0 9 * * 1-5")
        assert parsed.day_of_week.values == {1, 2, 3, 4, 5}

    def test_parse_expression_with_list(self):
        """Parse cron expression với list."""
        parsed = self.parser.parse("0,30 * * * *")
        assert parsed.minute.values == {0, 30}

    def test_parse_expression_with_step(self):
        """Parse cron expression với step."""
        parsed = self.parser.parse("0 */4 * * *")
        assert parsed.hour.values == {0, 4, 8, 12, 16, 20}

    def test_parse_special_string_daily(self):
        """Parse special string @daily."""
        parsed = self.parser.parse("@daily")
        assert parsed.minute.values == {0}
        assert parsed.hour.values == {0}

    def test_parse_special_string_hourly(self):
        """Parse special string @hourly."""
        parsed = self.parser.parse("@hourly")
        assert parsed.minute.values == {0}
        assert len(parsed.hour.values) == 24

    def test_parse_special_string_monthly(self):
        """Parse special string @monthly."""
        parsed = self.parser.parse("@monthly")
        assert parsed.minute.values == {0}
        assert parsed.hour.values == {0}
        assert parsed.day_of_month.values == {1}

    def test_parse_with_named_month(self):
        """Parse cron với tên tháng."""
        parsed = self.parser.parse("0 0 1 JAN *")
        assert parsed.month.values == {1}

    def test_parse_with_named_day(self):
        """Parse cron với tên ngày trong tuần."""
        parsed = self.parser.parse("0 9 * * MON-FRI")
        assert parsed.day_of_week.values == {1, 2, 3, 4, 5}

    def test_parse_six_field_expression(self):
        """Parse 6-field cron (với year)."""
        parsed = self.parser.parse("0 0 1 1 * 2026")
        assert parsed.year is not None
        assert 2026 in parsed.year.values

    def test_empty_expression_raises_error(self):
        """Expression rỗng throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse("")

    def test_invalid_field_count_raises_error(self):
        """Số field không đúng throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse("* * *")

    def test_invalid_value_range_raises_error(self):
        """Giá trị vượt range throw error."""
        with pytest.raises(MidicoderError):
            self.parser.parse("60 * * * *")  # minute > 59


class TestCronParserNextRun:
    """Test next_run_time calculation."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = CronParser()

    def test_next_run_daily(self):
        """Next run cho @daily."""
        parsed = self.parser.parse("@daily")
        after = datetime(2026, 5, 19, 12, 0, 0)
        next_run = self.parser.next_run_time(parsed, after)
        assert next_run.year == 2026
        assert next_run.month == 5
        assert next_run.day == 20
        assert next_run.hour == 0
        assert next_run.minute == 0

    def test_next_run_weekday_only(self):
        """Next run chỉ weekday."""
        parsed = self.parser.parse("9 0 * * 1-5")
        # Saturday May 23 -> next Monday May 25
        after = datetime(2026, 5, 23, 0, 0, 0)
        next_run = self.parser.next_run_time(parsed, after)
        assert next_run.day == 25  # Monday

    def test_next_run_every_4_hours(self):
        """Next run mỗi 4 giờ."""
        parsed = self.parser.parse("0 */4 * * *")
        after = datetime(2026, 5, 19, 5, 0, 0)
        next_run = self.parser.next_run_time(parsed, after)
        assert next_run.hour == 8  # next multiple of 4


class TestCronParserPrevRun:
    """Test prev_run_time calculation."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = CronParser()

    def test_prev_run_daily(self):
        """Prev run cho @daily."""
        parsed = self.parser.parse("@daily")
        before = datetime(2026, 5, 20, 12, 0, 0)
        prev_run = self.parser.prev_run_time(parsed, before)
        assert prev_run.day == 20
        assert prev_run.hour == 0


class TestCronParserValidate:
    """Test validate cron expression."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = CronParser()

    def test_valid_expression(self):
        """Expression valid trả về True."""
        assert self.parser.validate("0 0 * * *") is True

    def test_invalid_expression(self):
        """Expression invalid trả về False."""
        assert self.parser.validate("invalid") is False

    def test_empty_expression(self):
        """Expression rỗng trả về False."""
        assert self.parser.validate("") is False


class TestCronParserToDict:
    """Test to_dict serialization."""

    def setup_method(self):
        """Setup test fixture."""
        self.parser = CronParser()

    def test_to_dict(self):
        """Chuyển ParsedCron sang dict."""
        parsed = self.parser.parse("0 9 * * 1-5")
        data = self.parser.to_dict(parsed)
        assert "expression" in data
        assert "minute" in data
        assert data["minute"] == [0]
        assert data["day_of_week"] == [1, 2, 3, 4, 5]
