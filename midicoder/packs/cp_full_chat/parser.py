# coding: utf-8
"""
Mô-đun parser cho CP41 — Chat & Messaging.

Parse DSL dict (từ contract YAML) sang ChatIR — Intermediate Representation
cho hội thoại, tin nhắn, và thông báo.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_chat.models import (
    ChatMessage,
    Conversation,
    ConversationType,
    MessageStatus,
    MessageType,
    Notification,
    NotificationType,
)


@dataclass
class ChatIR:
    """Intermediate Representation cho CP41.

    Gom tập tất cả cấu hình chat từ DSL, bao gồm hội thoại,
    tin nhắn, thông báo, và cấu hình kết nối.

    Attributes:
        conversations: Danh sách hội thoại
        messages: Danh sách tin nhắn
        notifications: Danh sách thông báo
        redis_url: URL kết nối Redis cho pub/sub
        use_websocket: Có sử dụng WebSocket không
    """
    conversations: list[Conversation] = field(default_factory=list)
    messages: list[ChatMessage] = field(default_factory=list)
    notifications: list[Notification] = field(default_factory=list)
    redis_url: str = ""
    use_websocket: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ChatIR sang dict."""
        return {
            "conversations": [c.to_dict() for c in self.conversations],
            "messages": [m.to_dict() for m in self.messages],
            "notifications": [n.to_dict() for n in self.notifications],
            "redis_url": self.redis_url,
            "use_websocket": self.use_websocket,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatIR":
        """Tạo ChatIR từ dict."""
        conversations = [Conversation.from_dict(c) for c in data.get("conversations", [])]
        messages = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
        notifications = [Notification.from_dict(n) for n in data.get("notifications", [])]
        return cls(
            conversations=conversations,
            messages=messages,
            notifications=notifications,
            redis_url=data.get("redis_url", ""),
            use_websocket=data.get("use_websocket", True),
        )


def parse_conversations(data: dict[str, Any]) -> list[Conversation]:
    """Parse danh sách hội thoại từ DSL dict.

    Args:
        data: DSL dict với key 'conversations' hoặc 'chat_rooms'

    Returns:
        Danh sách Conversation
    """
    raw = data.get("conversations", data.get("chat_rooms", []))
    conversations = []
    for conv in raw:
        conversations.append(Conversation(
            conversation_id=conv.get("conversation_id", conv.get("id", "")),
            name=conv.get("name", ""),
            conversation_type=ConversationType(conv.get("conversation_type", conv.get("type", "direct"))),
            created_by=conv.get("created_by", ""),
            max_participants=conv.get("max_participants", 100),
            is_active=conv.get("is_active", True),
            metadata=conv.get("metadata", {}),
            created_at=conv.get("created_at"),
            updated_at=conv.get("updated_at"),
        ))
    return conversations


def parse_messages(data: dict[str, Any]) -> list[ChatMessage]:
    """Parse danh sách tin nhắn từ DSL dict.

    Args:
        data: DSL dict với key 'messages' hoặc 'chat_messages'

    Returns:
        Danh sách ChatMessage
    """
    raw = data.get("messages", data.get("chat_messages", []))
    messages = []
    for msg in raw:
        messages.append(ChatMessage(
            message_id=msg.get("message_id", msg.get("id", "")),
            conversation_id=msg.get("conversation_id", msg.get("conv_id", "")),
            sender_id=msg.get("sender_id", msg.get("from", "")),
            message_type=MessageType(msg.get("message_type", msg.get("type", "text"))),
            content=msg.get("content", ""),
            attachments=msg.get("attachments", []),
            reply_to=msg.get("reply_to"),
            status=MessageStatus(msg.get("status", "pending")),
            created_at=msg.get("created_at"),
        ))
    return messages


def parse_notifications(data: dict[str, Any]) -> list[Notification]:
    """Parse danh sách thông báo từ DSL dict.

    Args:
        data: DSL dict với key 'notifications' hoặc 'alerts'

    Returns:
        Danh sách Notification
    """
    raw = data.get("notifications", data.get("alerts", []))
    notifications = []
    for notif in raw:
        notifications.append(Notification(
            notification_id=notif.get("notification_id", notif.get("id", "")),
            conversation_id=notif.get("conversation_id", notif.get("conv_id", "")),
            target_user_id=notif.get("target_user_id", notif.get("user_id", "")),
            notification_type=NotificationType(notif.get("notification_type", notif.get("type", "new_message"))),
            message_id=notif.get("message_id"),
            is_read=notif.get("is_read", False),
            created_at=notif.get("created_at"),
        ))
    return notifications


def parse_to_ir(data: dict[str, Any]) -> ChatIR:
    """Parse DSL dict thành ChatIR.

    Args:
        data: DSL dict với conversations, messages, notifications, redis_url, use_websocket

    Returns:
        ChatIR gom tập tất cả parsed data
    """
    conversations = parse_conversations(data)
    messages = parse_messages(data)
    notifications = parse_notifications(data)
    return ChatIR(
        conversations=conversations,
        messages=messages,
        notifications=notifications,
        redis_url=data.get("redis_url", ""),
        use_websocket=data.get("use_websocket", True),
    )


__all__ = [
    "ChatIR",
    "parse_conversations",
    "parse_messages",
    "parse_notifications",
    "parse_to_ir",
]
