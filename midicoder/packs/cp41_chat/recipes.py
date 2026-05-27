# coding: utf-8
"""
Mô-đun recipes cho CP41 — Chat & Messaging.

Cung cấp các recipe patterns để generate hội thoại, tin nhắn,
thông báo, và cấu hình kết nối theo common use cases.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass

from midicoder.packs.cp41_chat.models import (
    ChatMessage,
    Conversation,
    ConversationParticipant,
    ConversationType,
    MessageStatus,
    MessageType,
    Notification,
    NotificationType,
    ReadReceipt,
    ReadReceiptType,
)
from midicoder.packs.cp41_chat.parser import ChatIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ChatIR kết quả
    """
    name: str
    description: str
    ir: ChatIR


def basic_chat_recipe() -> RecipeOutput:
    """Recipe: Chat cơ bản — 2 hội thoại, 3 tin nhắn, không Redis.

    Tạo 2 hội thoại: 1 trò chuyện trực tiếp (user_001 ↔ user_002),
    1 nhóm hỗ trợ. Tổng cộng 3 tin nhắn, không kết nối Redis,
    WebSocket mặc định bật — phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình chat cơ bản
    """
    conversations = [
        Conversation(
            conversation_id="conv_direct_001",
            name="",
            conversation_type=ConversationType.DIRECT,
            created_by="user_001",
            max_participants=2,
            is_active=True,
            metadata={"platform": "web"},
        ),
        Conversation(
            conversation_id="conv_group_001",
            name="Đội hỗ trợ",
            conversation_type=ConversationType.GROUP,
            created_by="user_001",
            max_participants=50,
            is_active=True,
            metadata={"department": "support"},
        ),
    ]

    participants = []

    messages = [
        ChatMessage(
            message_id="msg_001",
            conversation_id="conv_direct_001",
            sender_id="user_001",
            message_type=MessageType.TEXT,
            content="Xin chào, bạn có thể giúp tôi không?",
            status=MessageStatus.SENT,
        ),
        ChatMessage(
            message_id="msg_002",
            conversation_id="conv_direct_001",
            sender_id="user_002",
            message_type=MessageType.TEXT,
            content="Chào bạn! Tất nhiên rồi, bạn cần hỗ trợ gì?",
            status=MessageStatus.SENT,
        ),
        ChatMessage(
            message_id="msg_003",
            conversation_id="conv_group_001",
            sender_id="user_001",
            message_type=MessageType.TEXT,
            content="Mọi người ơi, ai rảnh hỗ trợ ticket #1234 không?",
            status=MessageStatus.SENT,
        ),
    ]

    return RecipeOutput(
        name="basic_chat",
        description="2 hội thoại (direct + group), 3 tin nhắn, không Redis",
        ir=ChatIR(
            conversations=conversations,
            messages=messages,
            notifications=[],
            redis_url="",
            use_websocket=True,
        ),
    )


def full_messaging_recipe() -> RecipeOutput:
    """Recipe: Messaging đầy đủ — 3 hội thoại, 5 tin nhắn, thông báo, Redis.

    Tạo 3 hội thoại: direct, group, support. Tổng cộng 5 tin nhắn
    phân bố across conversations, 3 thông báo (new_message, mention, reply),
    kết nối Redis pub/sub, WebSocket bật, bao gồm xác nhận đọc.

    Returns:
        RecipeOutput với cấu hình messaging đầy đủ
    """
    conversations = [
        Conversation(
            conversation_id="conv_direct_002",
            name="",
            conversation_type=ConversationType.DIRECT,
            created_by="user_001",
            max_participants=2,
            is_active=True,
            metadata={"platform": "mobile"},
        ),
        Conversation(
            conversation_id="conv_group_002",
            name="Đội dự án Alpha",
            conversation_type=ConversationType.GROUP,
            created_by="user_001",
            max_participants=30,
            is_active=True,
            metadata={"project": "alpha", "department": "engineering"},
        ),
        Conversation(
            conversation_id="conv_support_001",
            name="Hỗ trợ khách hàng #5678",
            conversation_type=ConversationType.SUPPORT,
            created_by="user_003",
            max_participants=5,
            is_active=True,
            metadata={"ticket_id": "5678", "priority": "high"},
        ),
    ]

    messages = [
        ChatMessage(
            message_id="msg_full_001",
            conversation_id="conv_direct_002",
            sender_id="user_001",
            message_type=MessageType.TEXT,
            content="Bạn đã xem báo cáo tháng này chưa?",
            status=MessageStatus.READ,
        ),
        ChatMessage(
            message_id="msg_full_002",
            conversation_id="conv_direct_002",
            sender_id="user_002",
            message_type=MessageType.TEXT,
            content="Rồi, mình đã xem xong. Có vài điểm cần điều chỉnh.",
            status=MessageStatus.READ,
            reply_to="msg_full_001",
        ),
        ChatMessage(
            message_id="msg_full_003",
            conversation_id="conv_group_002",
            sender_id="user_001",
            message_type=MessageType.TEXT,
            content="@user_003 Bạn vui lòng review PR #42 khi rảnh nhé.",
            status=MessageStatus.DELIVERED,
        ),
        ChatMessage(
            message_id="msg_full_004",
            conversation_id="conv_group_002",
            sender_id="user_003",
            message_type=MessageType.TEXT,
            content="Đã nhận, mình sẽ review trong ngày hôm nay.",
            status=MessageStatus.SENT,
            reply_to="msg_full_003",
        ),
        ChatMessage(
            message_id="msg_full_005",
            conversation_id="conv_support_001",
            sender_id="user_003",
            message_type=MessageType.TEXT,
            content="Chúng tôi đã nhận yêu cầu hỗ trợ của bạn. Nhân viên sẽ liên hệ trong 24h.",
            status=MessageStatus.DELIVERED,
        ),
    ]

    notifications = [
        Notification(
            notification_id="notif_001",
            conversation_id="conv_direct_002",
            target_user_id="user_002",
            notification_type=NotificationType.NEW_MESSAGE,
            message_id="msg_full_001",
            is_read=False,
        ),
        Notification(
            notification_id="notif_002",
            conversation_id="conv_group_002",
            target_user_id="user_003",
            notification_type=NotificationType.MENTION,
            message_id="msg_full_003",
            is_read=False,
        ),
        Notification(
            notification_id="notif_003",
            conversation_id="conv_group_002",
            target_user_id="user_001",
            notification_type=NotificationType.REPLY,
            message_id="msg_full_004",
            is_read=True,
        ),
    ]

    return RecipeOutput(
        name="full_messaging",
        description="3 hội thoại, 5 tin nhắn, 3 thông báo, Redis pub/sub, xác nhận đọc",
        ir=ChatIR(
            conversations=conversations,
            messages=messages,
            notifications=notifications,
            redis_url="redis://localhost:6379/0",
            use_websocket=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_chat_recipe",
    "full_messaging_recipe",
]
