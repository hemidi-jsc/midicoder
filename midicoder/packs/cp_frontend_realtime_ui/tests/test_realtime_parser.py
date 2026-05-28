"""
Test cho mô-đun parser của CP22 — Real-time UI Generator.

Kiểm tra:
- RealtimeParser: parse CP05 events → ChannelSpec list
- Tự động channel mapping từ event topic
- Tenant isolation
- Widget config generation
"""

import pytest
from midicoder.packs.cp_frontend_realtime_ui.parser import RealtimeParser
from midicoder.packs.cp_frontend_realtime_ui.models import (
    TransportType,
    WidgetType,
    ChannelSpec,
    WidgetConfig,
)


def _make_sample_events() -> list[dict]:
    """Tạo sample events giống CP05 EventDefinition."""
    return [
        {
            "event_name": "order.created",
            "payload_fields": ["order_id", "customer_id", "total", "items"],
            "topic": "orders",
            "version": "1.0",
        },
        {
            "event_name": "user.presence.changed",
            "payload_fields": ["user_id", "status", "last_seen"],
            "topic": "presence",
            "version": "1.0",
            "tenant_id": "tenant-1",
        },
        {
            "event_name": "payment.completed",
            "payload_fields": ["payment_id", "amount", "currency"],
            "topic": "payments",
            "version": "1.0",
            "tenant_id": "tenant-1",
        },
    ]


def _make_tenant_events() -> list[dict]:
    """Tạo sample events có tenant_id."""
    return [
        {
            "event_name": "order.updated",
            "payload_fields": ["order_id", "status"],
            "topic": "orders",
            "tenant_id": "t-a",
        },
        {
            "event_name": "order.shipped",
            "payload_fields": ["order_id", "tracking"],
            "topic": "orders",
            "tenant_id": "t-a",
        },
    ]


# ============================================================================
# Test RealtimeParser
# ============================================================================

class TestRealtimeParser:
    """Kiểm tra RealtimeParser."""

    def test_parse_events_to_channels(self):
        """Parse events → danh sách ChannelSpec."""
        parser = RealtimeParser()
        channels = parser.parse(_make_sample_events())

        assert len(channels) == 3
        assert isinstance(channels[0], ChannelSpec)

    def test_channel_id_from_event_name(self):
        """Channel ID được sinh từ event_name."""
        parser = RealtimeParser()
        channels = parser.parse(_make_sample_events())

        ids = [ch.channel_id for ch in channels]
        assert "order.created" in ids
        assert "user.presence.changed" in ids

    def test_transport_default_websocket(self):
        """Transport mặc định là WebSocket."""
        parser = RealtimeParser()
        channels = parser.parse(_make_sample_events())

        for ch in channels:
            assert ch.transport == TransportType.WEBSOCKET

    def test_tenant_isolation(self):
        """Tenant ID được propagate vào ChannelSpec."""
        parser = RealtimeParser()
        channels = parser.parse(_make_tenant_events())

        for ch in channels:
            assert ch.is_tenant_scoped is True
            assert ch.tenant_id == "t-a"

    def test_payload_fields_preserved(self):
        """Payload fields từ event được giữ nguyên."""
        parser = RealtimeParser()
        channels = parser.parse(_make_sample_events())

        order_ch = next(ch for ch in channels if ch.channel_id == "order.created")
        assert "order_id" in order_ch.payload_fields
        assert "customer_id" in order_ch.payload_fields
        assert "total" in order_ch.payload_fields

    def test_empty_events_returns_empty(self):
        """Events rỗng → channels rỗng."""
        parser = RealtimeParser()
        channels = parser.parse([])
        assert channels == []

    def test_parse_with_sse_fallback(self):
        """Parse với SSE fallback config."""
        parser = RealtimeParser(use_sse_fallback=True)
        channels = parser.parse(_make_sample_events())

        for ch in channels:
            assert ch.fallback_url is not None

    def test_generate_widget_configs(self):
        """Tự động sinh widget config từ events."""
        parser = RealtimeParser()
        configs = parser.generate_widget_configs(_make_sample_events())

        # Presence event → Presence widget
        presence_cfg = next(
            (c for c in configs if c.widget_type == WidgetType.PRESENCE),
            None
        )
        assert presence_cfg is not None
        assert "presence" in presence_cfg.channel_id

    def test_generate_widget_configs_no_events(self):
        """Không có events → không có widget config."""
        parser = RealtimeParser()
        configs = parser.generate_widget_configs([])
        assert configs == []

    def test_parse_invalid_event_raises(self):
        """Event không hợp lệ (thiếu event_name) gây lỗi."""
        parser = RealtimeParser()
        with pytest.raises(Exception):
            parser.parse([{"topic": "orders"}])
