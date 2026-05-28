"""
Test cho mô-đun models của CP22 — Real-time UI Generator.

Kiểm tra:
- ChannelSpec: validation, serialization, tenant isolation
- PresenceState: enum, transitions
- LiveFeedEntry: validation, serialization
- WidgetConfig: widget types, fallback transport
"""

import pytest
from pathlib import Path
from midicoder.errors import MidicoderError, ErrorCode
from midicoder.packs.cp_frontend_realtime_ui.models import (
    TransportType,
    WidgetType,
    PresenceStatus,
    ChannelSpec,
    PresenceState,
    LiveFeedEntry,
    WidgetConfig,
    SUPPORTED_UI_FRAMEWORKS,
)


# ============================================================================
# Test TransportType enum
# ============================================================================

class TestTransportType:
    """Kiểm tra enum transport type."""

    def test_has_websocket(self):
        """WebSocket transport tồn tại."""
        assert TransportType.WEBSOCKET.value == "websocket"

    def test_has_sse(self):
        """SSE transport tồn tại."""
        assert TransportType.SSE.value == "sse"


# ============================================================================
# Test WidgetType enum
# ============================================================================

class TestWidgetType:
    """Kiểm tra enum widget type."""

    def test_all_widget_types_exist(self):
        """Tất cả 5 widget primitives tồn tại."""
        assert WidgetType.PRESENCE.value == "presence"
        assert WidgetType.LIVE_FEED.value == "live_feed"
        assert WidgetType.LIVE_COUNTER.value == "live_counter"
        assert WidgetType.LIVE_CURSOR.value == "live_cursor"
        assert WidgetType.NOTIFICATION_TOAST.value == "notification_toast"


# ============================================================================
# Test PresenceStatus enum
# ============================================================================

class TestPresenceStatus:
    """Kiểm tra enum presence status."""

    def test_all_statuses_exist(self):
        """Tất cả trạng thái presence tồn tại."""
        assert PresenceStatus.ONLINE.value == "online"
        assert PresenceStatus.OFFLINE.value == "offline"
        assert PresenceStatus.TYPING.value == "typing"
        assert PresenceStatus.AWAY.value == "away"


# ============================================================================
# Test ChannelSpec
# ============================================================================

class TestChannelSpec:
    """Kiểm tra ChannelSpec model."""

    def test_create_basic_channel(self):
        """Tạo channel cơ bản từ event topic."""
        ch = ChannelSpec(
            channel_id="order.created",
            event_topic="order.created",
            transport=TransportType.WEBSOCKET,
        )
        assert ch.channel_id == "order.created"
        assert ch.transport == TransportType.WEBSOCKET
        assert ch.tenant_id is None
        assert ch.is_tenant_scoped is False

    def test_create_tenant_scoped_channel(self):
        """Tạo channel có scope theo tenant."""
        ch = ChannelSpec(
            channel_id="order.created",
            event_topic="order.created",
            transport=TransportType.WEBSOCKET,
            tenant_id="tenant-123",
        )
        assert ch.tenant_id == "tenant-123"
        assert ch.is_tenant_scoped is True
        assert ch.sub_protocol == "wss"

    def test_empty_channel_id_raises(self):
        """Channel ID rỗng gây lỗi."""
        with pytest.raises(MidicoderError) as exc_info:
            ChannelSpec(
                channel_id="",
                event_topic="order.created",
            )
        assert exc_info.value.code == ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND

    def test_empty_event_topic_raises(self):
        """Event topic rỗng gây lỗi."""
        with pytest.raises(MidicoderError) as exc_info:
            ChannelSpec(
                channel_id="ch",
                event_topic="",
            )
        assert exc_info.value.code == ErrorCode.MDC-FE02_EVENT_PARSE_FAILED

    def test_sse_fallback_transport(self):
        """Transport fallback sang SSE."""
        ch = ChannelSpec(
            channel_id="user.presence.changed",
            event_topic="user.presence.changed",
            transport=TransportType.SSE,
            fallback_url="/api/sse/presence",
        )
        assert ch.transport == TransportType.SSE
        assert ch.fallback_url == "/api/sse/presence"
        assert ch.sub_protocol == "https"

    def test_to_dict_serialization(self):
        """Serialization to_dict hoạt động đúng."""
        ch = ChannelSpec(
            channel_id="order.updated",
            event_topic="order.updated",
            transport=TransportType.WEBSOCKET,
            tenant_id="t-1",
            payload_fields=["order_id", "status", "total"],
        )
        d = ch.to_dict()
        assert d["channel_id"] == "order.updated"
        assert d["event_topic"] == "order.updated"
        assert d["transport"] == "websocket"
        assert d["tenant_id"] == "t-1"
        assert d["payload_fields"] == ["order_id", "status", "total"]
        assert d["is_tenant_scoped"] is True

    def test_from_dict_deserialization(self):
        """Deserialization from_dict hoạt động đúng."""
        d = {
            "channel_id": "live.counter.tick",
            "event_topic": "live.counter.tick",
            "transport": "sse",
            "fallback_url": "/api/sse/counter",
            "payload_fields": ["value", "label"],
        }
        ch = ChannelSpec.from_dict(d)
        assert ch.channel_id == "live.counter.tick"
        assert ch.transport == TransportType.SSE
        assert ch.fallback_url == "/api/sse/counter"
        assert ch.payload_fields == ["value", "label"]

    def test_channel_id_auto_from_topic(self):
        """Auto generate channel_id từ event topic nếu không có."""
        ch = ChannelSpec(
            channel_id=None,
            event_topic="payment.completed",
        )
        assert ch.channel_id == "payment.completed"


# ============================================================================
# Test PresenceState
# ============================================================================

class TestPresenceState:
    """Kiểm tra PresenceState model."""

    def test_create_online_presence(self):
        """Tạo presence state online."""
        ps = PresenceState(
            user_id="user-1",
            status=PresenceStatus.ONLINE,
            tenant_id="tenant-1",
        )
        assert ps.user_id == "user-1"
        assert ps.status == PresenceStatus.ONLINE
        assert ps.tenant_id == "tenant-1"

    def test_empty_user_id_raises(self):
        """User ID rỗng gây lỗi."""
        with pytest.raises(MidicoderError) as exc_info:
            PresenceState(
                user_id="",
                status=PresenceStatus.ONLINE,
            )
        assert exc_info.value.code == ErrorCode.MDC-FE02_INVALID_WIDGET_TYPE

    def test_to_dict_roundtrip(self):
        """Roundtrip serialization/deserialization."""
        ps = PresenceState(
            user_id="user-42",
            status=PresenceStatus.TYPING,
            tenant_id="t-2",
            last_seen="2026-05-20T10:00:00Z",
            metadata={"editor": "vscode"},
        )
        d = ps.to_dict()
        ps2 = PresenceState.from_dict(d)
        assert ps2.user_id == "user-42"
        assert ps2.status == PresenceStatus.TYPING
        assert ps2.tenant_id == "t-2"
        assert ps2.last_seen == "2026-05-20T10:00:00Z"
        assert ps2.metadata == {"editor": "vscode"}


# ============================================================================
# Test LiveFeedEntry
# ============================================================================

class TestLiveFeedEntry:
    """Kiểm tra LiveFeedEntry model."""

    def test_create_feed_entry(self):
        """Tạo live feed entry."""
        entry = LiveFeedEntry(
            event_id="evt-1",
            channel_id="order.created",
            payload={"order_id": "ORD-001", "status": "created"},
            timestamp="2026-05-20T10:00:00Z",
        )
        assert entry.event_id == "evt-1"
        assert entry.channel_id == "order.created"
        assert entry.payload["order_id"] == "ORD-001"

    def test_empty_event_id_raises(self):
        """Event ID rỗng gây lỗi."""
        with pytest.raises(MidicoderError) as exc_info:
            LiveFeedEntry(
                event_id="",
                channel_id="ch",
            )
        assert exc_info.value.code == ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND

    def test_to_dict_and_from_dict(self):
        """Serialization roundtrip."""
        entry = LiveFeedEntry(
            event_id="evt-2",
            channel_id="presence.changed",
            payload={"user_id": "u-1", "status": "online"},
            timestamp="2026-05-20T11:00:00Z",
            tenant_id="t-1",
        )
        d = entry.to_dict()
        e2 = LiveFeedEntry.from_dict(d)
        assert e2.event_id == "evt-2"
        assert e2.tenant_id == "t-1"


# ============================================================================
# Test WidgetConfig
# ============================================================================

class TestWidgetConfig:
    """Kiểm tra WidgetConfig model."""

    def test_create_presence_config(self):
        """Tạo config cho presence widget."""
        cfg = WidgetConfig(
            widget_type=WidgetType.PRESENCE,
            channel_id="user.presence.changed",
            tenant_id="t-1",
        )
        assert cfg.widget_type == WidgetType.PRESENCE
        assert cfg.polling_interval_ms is None  # realtime, không polling

    def test_create_counter_config(self):
        """Tạo config cho live counter widget."""
        cfg = WidgetConfig(
            widget_type=WidgetType.LIVE_COUNTER,
            channel_id="counter.tick",
            initial_value=0,
            threshold_colors={"low": "green", "high": "red"},
        )
        assert cfg.initial_value == 0
        assert cfg.threshold_colors == {"low": "green", "high": "red"}

    def test_empty_channel_id_raises(self):
        """Channel ID rỗng gây lỗi."""
        with pytest.raises(MidicoderError) as exc_info:
            WidgetConfig(
                widget_type=WidgetType.PRESENCE,
                channel_id="",
            )
        assert exc_info.value.code == ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND

    def test_to_dict_roundtrip(self):
        """Roundtrip serialization."""
        cfg = WidgetConfig(
            widget_type=WidgetType.LIVE_FEED,
            channel_id="activity.feed",
            tenant_id="t-3",
            max_items=50,
            auto_scroll=True,
            ui_framework="material",
        )
        d = cfg.to_dict()
        cfg2 = WidgetConfig.from_dict(d)
        assert cfg2.widget_type == WidgetType.LIVE_FEED
        assert cfg2.max_items == 50
        assert cfg2.auto_scroll is True
        assert cfg2.ui_framework == "material"

    def test_supported_ui_frameworks(self):
        """5 UI frameworks được hỗ trợ."""
        assert SUPPORTED_UI_FRAMEWORKS == [
            "material", "tailwind", "bootstrap", "antd", "carbon"
        ]


# ============================================================================
# Test Error Code existence
# ============================================================================

class TestErrorCodes:
    """Kiểm tra error codes tồn tại trong ErrorCode enum."""

    def test_cp22_error_codes_exist(self):
        """Tất cả error codes CP22 tồn tại."""
        assert hasattr(ErrorCode, "CP22_CHANNEL_NOT_FOUND")
        assert hasattr(ErrorCode, "CP22_INVALID_TRANSPORT")
        assert hasattr(ErrorCode, "CP22_TEMPLATE_NOT_FOUND")
        assert hasattr(ErrorCode, "CP22_RENDER_FAILED")
        assert hasattr(ErrorCode, "CP22_TENANT_ISOLATION_VIOLATION")
        assert hasattr(ErrorCode, "CP22_INVALID_WIDGET_TYPE")
        assert hasattr(ErrorCode, "CP22_EVENT_PARSE_FAILED")
