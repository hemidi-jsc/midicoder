"""Tests for EventParser."""

from __future__ import annotations

import pytest

from midicoder.packs.cp_core_event_driven.parser import EventParser


class TestEventParser:
    def setup_method(self):
        self.parser = EventParser()

    def test_parse_empty_list(self):
        result = self.parser.parse([])
        assert result == []

    def test_parse_single_event(self):
        data = [{"event_name": "order.created", "payload_fields": ["order_id"]}]
        result = self.parser.parse(data)
        assert len(result) == 1
        assert result[0].event_name == "order.created"
        assert result[0].payload_fields == ["order_id"]

    def test_parse_multiple_events(self):
        data = [
            {"event_name": "order.created"},
            {"event_name": "order.cancelled", "topic": "orders"},
            {"event_name": "payment.completed", "version": "2.0"},
        ]
        result = self.parser.parse(data)
        assert len(result) == 3
        assert result[1].topic == "orders"
        assert result[2].version == "2.0"

    def test_parse_with_all_fields(self):
        data = [
            {
                "event_name": "x",
                "payload_fields": ["a", "b"],
                "topic": "t",
                "version": "1.5",
                "tenant_id": "t1",
                "schema_fields": {"a": {"type": "str"}},
            }
        ]
        result = self.parser.parse(data)
        assert result[0].tenant_id == "t1"
        assert result[0].schema_fields == {"a": {"type": "str"}}

    def test_parse_defaults(self):
        data = [{"event_name": "x"}]
        result = self.parser.parse(data)
        assert result[0].topic == "default"
        assert result[0].version == "1.0"
        assert result[0].payload_fields == []

    def test_parse_missing_event_name_raises(self):
        with pytest.raises(ValueError, match="bắt buộc"):
            self.parser.parse([{"payload_fields": []}])

    def test_parse_empty_event_name_raises(self):
        with pytest.raises(ValueError):
            self.parser.parse([{"event_name": ""}])

    def test_parse_whitespace_event_name_raises(self):
        with pytest.raises(ValueError):
            self.parser.parse([{"event_name": "  "}])

    def test_parse_non_string_event_name_converted(self):
        data = [{"event_name": 123}]
        result = self.parser.parse(data)
        assert result[0].event_name == "123"
