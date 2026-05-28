"""
Mô-đun models cho CP22 — Real-time UI Generator.

Cung cấp các dataclass và enum để mô tả:
- ChannelSpec: mapping giữa CP05 event topic và WebSocket/SSE channel
- PresenceState: trạng thái presence của user (online/offline/typing/away)
- LiveFeedEntry: entry trong activity feed realtime
- WidgetConfig: cấu hình cho từng realtime widget
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from typing import ClassVar

# Danh sách UI frameworks được hỗ trợ (class-level constant)
SUPPORTED_UI_FRAMEWORKS: list[str] = [
    "material", "tailwind", "bootstrap", "antd", "carbon"
]


class TransportType(str, Enum):
    """Loại transport cho realtime channel."""

    WEBSOCKET = "websocket"
    SSE = "sse"


class WidgetType(str, Enum):
    """Loại widget realtime UI."""

    PRESENCE = "presence"
    LIVE_FEED = "live_feed"
    LIVE_COUNTER = "live_counter"
    LIVE_CURSOR = "live_cursor"
    NOTIFICATION_TOAST = "notification_toast"


class PresenceStatus(str, Enum):
    """Trạng thái presence của user."""

    ONLINE = "online"
    OFFLINE = "offline"
    TYPING = "typing"
    AWAY = "away"


@dataclass
class ChannelSpec:
    """
    Spec cho realtime channel — mapping từ CP05 event topic sang WebSocket/SSE channel.

    Attributes:
        channel_id: ID duy nhất của channel (tự động từ event_topic nếu None).
        event_topic: Topic của event từ CP05.
        transport: Loại transport (websocket hoặc sse).
        tenant_id: Tenant ID để scope channel (multi-tenant isolation).
        fallback_url: URL fallback cho SSE nếu transport là websocket.
        payload_fields: Danh sách fields trong payload event.
        sub_protocol: Protocol URL (wss cho websocket, https cho sse).
        is_tenant_scoped: Có scope theo tenant không.
    """

    channel_id: Optional[str]
    event_topic: str
    transport: TransportType = TransportType.WEBSOCKET
    tenant_id: Optional[str] = None
    fallback_url: Optional[str] = None
    payload_fields: list[str] = field(default_factory=list)
    sub_protocol: str = "wss"
    is_tenant_scoped: bool = False

    def __post_init__(self) -> None:
        """Validate và auto-set fields sau khi init."""
        from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

        # Tự động sinh channel_id từ event_topic nếu không có
        if self.channel_id is None:
            if not self.event_topic:
                raise EM.raise_error(
                    ErrorCode.MDC-FE02_EVENT_PARSE_FAILED,
                    detail="event_topic không được rỗng khi channel_id là None",
                )
            self.channel_id = self.event_topic

        # Validate channel_id không rỗng
        if not self.channel_id or not self.channel_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND,
                channel_id=self.channel_id,
                detail="channel_id không được rỗng",
            )

        # Validate event_topic không rỗng
        if not self.event_topic or not self.event_topic.strip():
            raise EM.raise_error(
                ErrorCode.MDC-FE02_EVENT_PARSE_FAILED,
                channel_id=self.channel_id,
                detail="event_topic không được rỗng",
            )

        # Set tenant scope flag
        self.is_tenant_scoped = self.tenant_id is not None

        # Set sub_protocol theo transport
        if self.transport == TransportType.SSE:
            self.sub_protocol = "https"
        else:
            self.sub_protocol = "wss"

    def to_dict(self) -> dict[str, Any]:
        """Serialization sang dict."""
        result: dict[str, Any] = {
            "channel_id": self.channel_id,
            "event_topic": self.event_topic,
            "transport": self.transport.value,
            "payload_fields": self.payload_fields,
            "is_tenant_scoped": self.is_tenant_scoped,
        }
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.fallback_url is not None:
            result["fallback_url"] = self.fallback_url
        if self.sub_protocol:
            result["sub_protocol"] = self.sub_protocol
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChannelSpec:
        """Deserialization từ dict."""
        transport_val = data.get("transport", "websocket")
        transport = TransportType(transport_val) if isinstance(transport_val, str) else transport_val
        return cls(
            channel_id=data.get("channel_id"),
            event_topic=data["event_topic"],
            transport=transport,
            tenant_id=data.get("tenant_id"),
            fallback_url=data.get("fallback_url"),
            payload_fields=data.get("payload_fields", []),
        )


@dataclass
class PresenceState:
    """
    Trạng thái presence của một user trong hệ thống realtime.

    Attributes:
        user_id: ID duy nhất của user.
        status: Trạng thái presence (online/offline/typing/away).
        tenant_id: Tenant scope để enforce isolation.
        last_seen: Timestamp cuối cùng user active.
        metadata: Metadata bổ sung (editor, device, v.v.).
    """

    user_id: str
    status: PresenceStatus
    tenant_id: Optional[str] = None
    last_seen: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate user_id không rỗng."""
        from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

        if not self.user_id or not self.user_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-FE02_INVALID_WIDGET_TYPE,
                detail="user_id không được rỗng cho PresenceState",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialization sang dict."""
        result: dict[str, Any] = {
            "user_id": self.user_id,
            "status": self.status.value,
        }
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.last_seen is not None:
            result["last_seen"] = self.last_seen
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresenceState:
        """Deserialization từ dict."""
        status_val = data.get("status", "online")
        status = PresenceStatus(status_val) if isinstance(status_val, str) else status_val
        return cls(
            user_id=data["user_id"],
            status=status,
            tenant_id=data.get("tenant_id"),
            last_seen=data.get("last_seen"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LiveFeedEntry:
    """
    Một entry trong live feed (activity stream realtime).

    Attributes:
        event_id: ID duy nhất của event.
        channel_id: Channel mà event thuộc về.
        payload: Dữ liệu của event.
        timestamp: Thời gian event xảy ra (ISO 8601).
        tenant_id: Tenant scope.
    """

    event_id: str
    channel_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None
    tenant_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate event_id không rỗng."""
        from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

        if not self.event_id or not self.event_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND,
                detail="event_id không được rỗng cho LiveFeedEntry",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialization sang dict."""
        result: dict[str, Any] = {
            "event_id": self.event_id,
            "channel_id": self.channel_id,
            "payload": self.payload,
        }
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LiveFeedEntry:
        """Deserialization từ dict."""
        return cls(
            event_id=data["event_id"],
            channel_id=data["channel_id"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp"),
            tenant_id=data.get("tenant_id"),
        )


@dataclass
class WidgetConfig:
    """
    Cấu hình cho realtime widget.

    Attributes:
        widget_type: Loại widget (presence, live_feed, live_counter, live_cursor, notification_toast).
        channel_id: Channel ID để subscribe.
        tenant_id: Tenant scope cho isolation.
        ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon).
        polling_interval_ms: Polling interval (None = realtime push).
        initial_value: Giá trị ban đầu (cho live_counter).
        threshold_colors: Màu threshold (cho live_counter).
        max_items: Số items tối đa (cho live_feed).
        auto_scroll: Tự động scroll (cho live_feed).
    """

    widget_type: WidgetType
    channel_id: str
    tenant_id: Optional[str] = None
    ui_framework: str = "material"
    polling_interval_ms: Optional[int] = None
    initial_value: Optional[float] = None
    threshold_colors: dict[str, str] = field(default_factory=dict)
    max_items: Optional[int] = None
    auto_scroll: bool = True

    @property
    def supported_ui_frameworks(self) -> list[str]:
        """Trả về danh sách UI frameworks được hỗ trợ."""
        return SUPPORTED_UI_FRAMEWORKS

    def __post_init__(self) -> None:
        """Validate channel_id không rỗng."""
        from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

        if not self.channel_id or not self.channel_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-FE02_CHANNEL_NOT_FOUND,
                widget_type=self.widget_type.value,
                detail="channel_id không được rỗng cho WidgetConfig",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialization sang dict."""
        result: dict[str, Any] = {
            "widget_type": self.widget_type.value,
            "channel_id": self.channel_id,
            "ui_framework": self.ui_framework,
            "auto_scroll": self.auto_scroll,
        }
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.polling_interval_ms is not None:
            result["polling_interval_ms"] = self.polling_interval_ms
        if self.initial_value is not None:
            result["initial_value"] = self.initial_value
        if self.threshold_colors:
            result["threshold_colors"] = self.threshold_colors
        if self.max_items is not None:
            result["max_items"] = self.max_items
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WidgetConfig:
        """Deserialization từ dict."""
        widget_type_val = data.get("widget_type", "presence")
        widget_type = WidgetType(widget_type_val) if isinstance(widget_type_val, str) else widget_type_val
        return cls(
            widget_type=widget_type,
            channel_id=data["channel_id"],
            tenant_id=data.get("tenant_id"),
            ui_framework=data.get("ui_framework", "material"),
            polling_interval_ms=data.get("polling_interval_ms"),
            initial_value=data.get("initial_value"),
            threshold_colors=data.get("threshold_colors", {}),
            max_items=data.get("max_items"),
            auto_scroll=data.get("auto_scroll", True),
        )


__all__ = [
    "SUPPORTED_UI_FRAMEWORKS",
    "TransportType",
    "WidgetType",
    "PresenceStatus",
    "ChannelSpec",
    "PresenceState",
    "LiveFeedEntry",
    "WidgetConfig",
]
