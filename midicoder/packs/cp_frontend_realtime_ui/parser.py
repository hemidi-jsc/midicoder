"""
Mô-đun parser cho CP22 — Real-time UI Generator.

RealtimeParser chịu trách nhiệm:
- Parse danh sách CP05 EventDefinition (dict) → ChannelSpec list
- Tự động mapping event topic → WebSocket/SSE channel
- Tự động sinh WidgetConfig từ event names (heuristic)
- Enforce tenant isolation trên channels
"""

from __future__ import annotations

import re
from typing import Any

from .models import (
    ChannelSpec,
    TransportType,
    WidgetConfig,
    WidgetType,
)


# Pattern nhận diện event name liên quan presence
_PRESENCE_PATTERN = re.compile(r"presence|online|offline|typing|away", re.IGNORECASE)

# Pattern nhận diện event name liên quan notification
_NOTIFICATION_PATTERN = re.compile(r"notif|alert|warn|toast|message", re.IGNORECASE)

# Pattern nhận diện event name liên quan counter
_COUNTER_PATTERN = re.compile(r"count|metric|gauge|tick|stat", re.IGNORECASE)

# Pattern nhận diện event name liên quan cursor/collaboration
_CURSOR_PATTERN = re.compile(r"cursor|position|collab|edit|selection", re.IGNORECASE)

# Pattern nhận diện event name liên quan feed/activity
_FEED_PATTERN = re.compile(r"feed|activity|log|stream|history", re.IGNORECASE)


class RealtimeParser:
    """
    Parser để chuyển đổi CP05 EventDefinition sang ChannelSpec và WidgetConfig.

    Attributes:
        use_sse_fallback: Có sinh SSE fallback URL cho mỗi channel không.
    """

    def __init__(self, use_sse_fallback: bool = False) -> None:
        """
        Khởi tạo RealtimeParser.

        Args:
            use_sse_fallback: Nếu True, sinh SSE fallback URL cho tất cả channels.
        """
        self.use_sse_fallback = use_sse_fallback

    def parse(self, data: list[dict[str, Any]]) -> list[ChannelSpec]:
        """
        Parse danh sách event definitions (từ CP05) thành ChannelSpec list.

        Args:
            data: Danh sách dict, mỗi dict có cấu trúc giống CP05 EventDefinition:
                - event_name (bắt buộc): Tên event
                - payload_fields (tuỳ chọn): Danh sách fields trong payload
                - topic (tuỳ chọn): Event topic
                - tenant_id (tuỳ chọn): Tenant ID cho isolation

        Returns:
            Danh sách ChannelSpec đã parse.

        Raises:
            ValueError: Nếu event_name thiếu trong một event.
        """
        if not data:
            return []

        channels: list[ChannelSpec] = []
        for event_data in data:
            event_name = event_data.get("event_name", "").strip()
            if not event_name:
                raise ValueError(
                    "Event definition thiếu 'event_name'. "
                    "Mỗi event phải có event_name để sinh channel."
                )

            # Sinh fallback URL nếu cần
            fallback_url = None
            if self.use_sse_fallback:
                safe_name = event_name.replace(".", "-")
                fallback_url = f"/api/sse/events/{safe_name}"

            channels.append(ChannelSpec(
                channel_id=event_name,
                event_topic=event_data.get("topic", event_name),
                transport=TransportType.WEBSOCKET,
                tenant_id=event_data.get("tenant_id"),
                fallback_url=fallback_url,
                payload_fields=event_data.get("payload_fields", []),
            ))

        return channels

    def generate_widget_configs(
        self,
        data: list[dict[str, Any]],
        ui_framework: str = "material",
    ) -> list[WidgetConfig]:
        """
        Tự động sinh WidgetConfig từ danh sách event definitions.

        Dùng heuristic để phân loại event name → widget type:
        - presence/online/offline → PRESENCE widget
        - notif/alert/message → NOTIFICATION_TOAST widget
        - count/metric/gauge → LIVE_COUNTER widget
        - cursor/position/collab → LIVE_CURSOR widget
        - feed/activity/stream → LIVE_FEED widget
        - default → LIVE_FEED widget

        Args:
            data: Danh sách event definitions (giống input của parse()).
            ui_framework: UI framework để render widgets.

        Returns:
            Danh sách WidgetConfig tự động sinh.
        """
        if not data:
            return []

        configs: list[WidgetConfig] = []
        seen_types: set[WidgetType] = set()

        for event_data in data:
            event_name = event_data.get("event_name", "").lower()
            tenant_id = event_data.get("tenant_id")

            # Phân loại widget type từ event name
            widget_type = self._classify_event(event_name)

            # Tránh duplicate widget type (mỗi type chỉ cần 1 config)
            if widget_type in seen_types:
                continue
            seen_types.add(widget_type)

            configs.append(WidgetConfig(
                widget_type=widget_type,
                channel_id=event_data.get("event_name", ""),
                tenant_id=tenant_id,
                ui_framework=ui_framework,
                max_items=50 if widget_type == WidgetType.LIVE_FEED else None,
                auto_scroll=widget_type == WidgetType.LIVE_FEED,
            ))

        # Nếu không có widget nào được phân loại, default sinh LiveFeed
        if not configs and data:
            first_event = data[0]
            configs.append(WidgetConfig(
                widget_type=WidgetType.LIVE_FEED,
                channel_id=first_event.get("event_name", ""),
                tenant_id=first_event.get("tenant_id"),
                ui_framework=ui_framework,
                max_items=50,
            ))

        return configs

    @staticmethod
    def _classify_event(event_name: str) -> WidgetType:
        """
        Phân loại event name thành widget type bằng pattern matching.

        Args:
            event_name: Tên event để phân loại.

        Returns:
            WidgetType phù hợp nhất.
        """
        if _PRESENCE_PATTERN.search(event_name):
            return WidgetType.PRESENCE
        if _NOTIFICATION_PATTERN.search(event_name):
            return WidgetType.NOTIFICATION_TOAST
        if _COUNTER_PATTERN.search(event_name):
            return WidgetType.LIVE_COUNTER
        if _CURSOR_PATTERN.search(event_name):
            return WidgetType.LIVE_CURSOR
        if _FEED_PATTERN.search(event_name):
            return WidgetType.LIVE_FEED
        # Default: LiveFeed cho event không nhận diện được
        return WidgetType.LIVE_FEED


__all__ = ["RealtimeParser"]
