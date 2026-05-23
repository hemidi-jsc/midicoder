# coding: utf-8
"""
Kiểm tra mô-đun parser cho CP41 — Chat & Messaging.

Bao gồm các tests cho:
- ChatIR: empty, with data, to_dict/from_dict roundtrip
- parse_conversations: từ key 'conversations', từ key 'chat_rooms', empty, alias
- parse_messages: từ key 'messages', từ key 'chat_messages', empty, alias
- parse_notifications: từ key 'notifications', từ key 'alerts', empty, alias
- parse_to_ir: full data, empty data, partial data
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp41_chat.parser import (
    ChatIR,
    parse_conversations,
    parse_messages,
    parse_notifications,
    parse_to_ir,
)


# ===========================================================================
# Test ChatIR
# ===========================================================================


class TestChatIR:
    """Kiểm tra ChatIR — tạo, serialize, deserialize."""

    def test_chat_ir_empty(self):
        """Kiểm tra ChatIR rỗng có các danh sách trống và giá trị mặc định."""
        ir = ChatIR()
        assert len(ir.conversations) == 0
        assert len(ir.messages) == 0
        assert len(ir.notifications) == 0
        assert ir.redis_url == ""
        assert ir.use_websocket is True

    def test_chat_ir_to_dict_empty(self):
        """Kiểm tra ChatIR rỗng chuyển sang dict đúng định dạng."""
        ir = ChatIR()
        d = ir.to_dict()
        assert d["conversations"] == []
        assert d["messages"] == []
        assert d["notifications"] == []
        assert d["redis_url"] == ""
        assert d["use_websocket"] is True

    def test_chat_ir_with_data(self):
        """Kiểm tra ChatIR có dữ liệu hội thoại, tin nhắn, và thông báo."""
        from midicoder.emitters.core.cp41_chat.models import (
            ChatMessage,
            Conversation,
            ConversationType,
            MessageStatus,
            MessageType,
            Notification,
            NotificationType,
        )
        conv = Conversation(
            conversation_id="conv_001",
            name="Phòng chat chung",
            conversation_type=ConversationType.GROUP,
            created_by="user_001",
        )
        msg = ChatMessage(
            message_id="msg_001",
            conversation_id="conv_001",
            sender_id="user_001",
            message_type=MessageType.TEXT,
            content="Xin chào mọi người",
            status=MessageStatus.SENT,
        )
        notif = Notification(
            notification_id="notif_001",
            conversation_id="conv_001",
            target_user_id="user_002",
            notification_type=NotificationType.NEW_MESSAGE,
            message_id="msg_001",
        )
        ir = ChatIR(
            conversations=[conv],
            messages=[msg],
            notifications=[notif],
            redis_url="redis://localhost:6379/0",
            use_websocket=True,
        )
        assert len(ir.conversations) == 1
        assert len(ir.messages) == 1
        assert len(ir.notifications) == 1
        assert ir.redis_url == "redis://localhost:6379/0"
        assert ir.use_websocket is True

    def test_chat_ir_to_dict_with_data(self):
        """Kiểm tra ChatIR có dữ liệu chuyển sang dict đúng giá trị."""
        from midicoder.emitters.core.cp41_chat.models import (
            ChatMessage,
            Conversation,
            ConversationType,
            MessageStatus,
            MessageType,
            Notification,
            NotificationType,
        )
        conv = Conversation(
            conversation_id="conv_001",
            name="Phòng nhóm",
            conversation_type=ConversationType.GROUP,
        )
        msg = ChatMessage(
            message_id="msg_001",
            conversation_id="conv_001",
            sender_id="user_001",
            content="Chào nhóm",
        )
        ir = ChatIR(
            conversations=[conv],
            messages=[msg],
            redis_url="redis://localhost:6379/1",
        )
        d = ir.to_dict()
        assert len(d["conversations"]) == 1
        assert d["conversations"][0]["conversation_id"] == "conv_001"
        assert len(d["messages"]) == 1
        assert d["messages"][0]["message_id"] == "msg_001"
        assert d["redis_url"] == "redis://localhost:6379/1"

    def test_chat_ir_from_dict_roundtrip(self):
        """Kiểm tra ChatIR serialize rồi deserialize giữ nguyên dữ liệu."""
        from midicoder.emitters.core.cp41_chat.models import (
            ChatMessage,
            Conversation,
            ConversationType,
            MessageStatus,
            MessageType,
            Notification,
            NotificationType,
        )
        conv = Conversation(
            conversation_id="conv_rt",
            name="Phòng roundtrip",
            conversation_type=ConversationType.DIRECT,
        )
        msg = ChatMessage(
            message_id="msg_rt",
            conversation_id="conv_rt",
            sender_id="user_rt",
            message_type=MessageType.TEXT,
            content="Roundtrip test",
        )
        notif = Notification(
            notification_id="notif_rt",
            conversation_id="conv_rt",
            target_user_id="user_rt",
            notification_type=NotificationType.MENTION,
        )
        ir = ChatIR(
            conversations=[conv],
            messages=[msg],
            notifications=[notif],
            redis_url="redis://localhost:6379/2",
            use_websocket=False,
        )
        d = ir.to_dict()
        restored = ChatIR.from_dict(d)
        assert len(restored.conversations) == 1
        assert restored.conversations[0].conversation_id == "conv_rt"
        assert len(restored.messages) == 1
        assert restored.messages[0].message_id == "msg_rt"
        assert len(restored.notifications) == 1
        assert restored.notifications[0].notification_id == "notif_rt"
        assert restored.redis_url == "redis://localhost:6379/2"
        assert restored.use_websocket is False


# ===========================================================================
# Test parse_conversations
# ===========================================================================


class TestParseConversations:
    """Kiểm tra parse_conversations — nhiều key, alias, empty."""

    def test_parse_conversations_from_conversations_key(self):
        """Kiểm tra parse từ key chính 'conversations'."""
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_001",
                    "name": "Phòng chat",
                    "conversation_type": "direct",
                }
            ]
        }
        result = parse_conversations(data)
        assert len(result) == 1
        assert result[0].conversation_id == "conv_001"
        assert result[0].name == "Phòng chat"

    def test_parse_conversations_from_chat_rooms_key(self):
        """Kiểm tra parse từ key alias 'chat_rooms'."""
        data = {
            "chat_rooms": [
                {
                    "conversation_id": "conv_002",
                    "name": "Phòng alias",
                    "conversation_type": "group",
                }
            ]
        }
        result = parse_conversations(data)
        assert len(result) == 1
        assert result[0].conversation_id == "conv_002"

    def test_parse_conversations_empty(self):
        """Kiểm tra parse với dữ liệu rỗng trả về danh sách trống."""
        data = {}
        result = parse_conversations(data)
        assert len(result) == 0

    def test_parse_conversations_with_group_type(self):
        """Kiểm tra parse hội thoại loại group từ conversation_type."""
        from midicoder.emitters.core.cp41_chat.models import ConversationType
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_group",
                    "conversation_type": "group",
                    "max_participants": 50,
                }
            ]
        }
        result = parse_conversations(data)
        assert result[0].conversation_type == ConversationType.GROUP
        assert result[0].max_participants == 50

    def test_parse_conversations_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'conversation_id'."""
        data = {
            "conversations": [
                {
                    "id": "conv_alias_id",
                    "name": "Alias ID room",
                }
            ]
        }
        result = parse_conversations(data)
        assert result[0].conversation_id == "conv_alias_id"

    def test_parse_conversations_with_type_alias(self):
        """Kiểm tra alias key 'type' thay cho 'conversation_type'."""
        from midicoder.emitters.core.cp41_chat.models import ConversationType
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_type_alias",
                    "type": "support",
                }
            ]
        }
        result = parse_conversations(data)
        assert result[0].conversation_type == ConversationType.SUPPORT

    def test_parse_conversations_with_metadata(self):
        """Kiểm tra parse hội thoại có metadata dict."""
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_meta",
                    "name": "Phòng có metadata",
                    "metadata": {"department": "engineering", "priority": "high"},
                }
            ]
        }
        result = parse_conversations(data)
        assert result[0].metadata == {"department": "engineering", "priority": "high"}

    def test_parse_conversations_multiple(self):
        """Kiểm tra parse nhiều hội thoại trong cùng một dict."""
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_001",
                    "name": "Phòng 1",
                    "conversation_type": "direct",
                },
                {
                    "conversation_id": "conv_002",
                    "name": "Phòng 2",
                    "conversation_type": "group",
                },
            ]
        }
        result = parse_conversations(data)
        assert len(result) == 2
        assert result[0].conversation_id == "conv_001"
        assert result[1].conversation_id == "conv_002"


# ===========================================================================
# Test parse_messages
# ===========================================================================


class TestParseMessages:
    """Kiểm tra parse_messages — nhiều key, alias, empty."""

    def test_parse_messages_from_messages_key(self):
        """Kiểm tra parse từ key chính 'messages'."""
        data = {
            "messages": [
                {
                    "message_id": "msg_001",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                    "content": "Xin chào",
                }
            ]
        }
        result = parse_messages(data)
        assert len(result) == 1
        assert result[0].message_id == "msg_001"
        assert result[0].content == "Xin chào"

    def test_parse_messages_from_chat_messages_key(self):
        """Kiểm tra parse từ key alias 'chat_messages'."""
        data = {
            "chat_messages": [
                {
                    "message_id": "msg_002",
                    "conversation_id": "conv_001",
                    "sender_id": "user_002",
                    "content": "Tin nhắn alias",
                }
            ]
        }
        result = parse_messages(data)
        assert len(result) == 1
        assert result[0].message_id == "msg_002"

    def test_parse_messages_empty(self):
        """Kiểm tra parse với dữ liệu rỗng trả về danh sách trống."""
        data = {}
        result = parse_messages(data)
        assert len(result) == 0

    def test_parse_messages_with_image_type(self):
        """Kiểm tra parse tin nhắn loại image từ message_type."""
        from midicoder.emitters.core.cp41_chat.models import MessageType
        data = {
            "messages": [
                {
                    "message_id": "msg_img",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                    "message_type": "image",
                    "content": "https://example.com/photo.jpg",
                }
            ]
        }
        result = parse_messages(data)
        assert result[0].message_type == MessageType.IMAGE

    def test_parse_messages_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'message_id'."""
        data = {
            "messages": [
                {
                    "id": "msg_alias_id",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                }
            ]
        }
        result = parse_messages(data)
        assert result[0].message_id == "msg_alias_id"

    def test_parse_messages_with_sender_alias(self):
        """Kiểm tra alias key 'from' thay cho 'sender_id'."""
        data = {
            "messages": [
                {
                    "message_id": "msg_sender",
                    "conversation_id": "conv_001",
                    "from": "user_from_alias",
                    "content": "Tin từ alias sender",
                }
            ]
        }
        result = parse_messages(data)
        assert result[0].sender_id == "user_from_alias"

    def test_parse_messages_with_attachments(self):
        """Kiểm tra parse tin nhắn có danh sách file đính kèm."""
        data = {
            "messages": [
                {
                    "message_id": "msg_attach",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                    "attachments": [
                        {"url": "https://example.com/doc.pdf", "filename": "doc.pdf", "mime_type": "application/pdf"},
                    ],
                }
            ]
        }
        result = parse_messages(data)
        assert len(result[0].attachments) == 1
        assert result[0].attachments[0]["filename"] == "doc.pdf"

    def test_parse_messages_multiple(self):
        """Kiểm tra parse nhiều tin nhắn trong cùng một dict."""
        data = {
            "messages": [
                {
                    "message_id": "msg_001",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                    "content": "Tin nhắn thứ nhất",
                },
                {
                    "message_id": "msg_002",
                    "conversation_id": "conv_001",
                    "sender_id": "user_002",
                    "content": "Tin nhắn thứ hai",
                },
            ]
        }
        result = parse_messages(data)
        assert len(result) == 2
        assert result[0].message_id == "msg_001"
        assert result[1].message_id == "msg_002"


# ===========================================================================
# Test parse_notifications
# ===========================================================================


class TestParseNotifications:
    """Kiểm tra parse_notifications — nhiều key, alias, empty."""

    def test_parse_notifications_from_notifications_key(self):
        """Kiểm tra parse từ key chính 'notifications'."""
        data = {
            "notifications": [
                {
                    "notification_id": "notif_001",
                    "conversation_id": "conv_001",
                    "target_user_id": "user_002",
                    "notification_type": "new_message",
                }
            ]
        }
        result = parse_notifications(data)
        assert len(result) == 1
        assert result[0].notification_id == "notif_001"
        assert result[0].target_user_id == "user_002"

    def test_parse_notifications_from_alerts_key(self):
        """Kiểm tra parse từ key alias 'alerts'."""
        data = {
            "alerts": [
                {
                    "notification_id": "notif_002",
                    "conversation_id": "conv_001",
                    "target_user_id": "user_003",
                }
            ]
        }
        result = parse_notifications(data)
        assert len(result) == 1
        assert result[0].notification_id == "notif_002"

    def test_parse_notifications_empty(self):
        """Kiểm tra parse với dữ liệu rỗng trả về danh sách trống."""
        data = {}
        result = parse_notifications(data)
        assert len(result) == 0

    def test_parse_notifications_with_mention_type(self):
        """Kiểm tra parse thông báo loại mention từ notification_type."""
        from midicoder.emitters.core.cp41_chat.models import NotificationType
        data = {
            "notifications": [
                {
                    "notification_id": "notif_mention",
                    "conversation_id": "conv_001",
                    "target_user_id": "user_001",
                    "notification_type": "mention",
                }
            ]
        }
        result = parse_notifications(data)
        assert result[0].notification_type == NotificationType.MENTION

    def test_parse_notifications_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'notification_id'."""
        data = {
            "notifications": [
                {
                    "id": "notif_alias_id",
                    "conversation_id": "conv_001",
                    "target_user_id": "user_001",
                }
            ]
        }
        result = parse_notifications(data)
        assert result[0].notification_id == "notif_alias_id"

    def test_parse_notifications_with_target_user_alias(self):
        """Kiểm tra alias key 'user_id' thay cho 'target_user_id'."""
        data = {
            "notifications": [
                {
                    "notification_id": "notif_user_alias",
                    "conversation_id": "conv_001",
                    "user_id": "user_target_alias",
                }
            ]
        }
        result = parse_notifications(data)
        assert result[0].target_user_id == "user_target_alias"


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Kiểm tra parse_to_ir — full data, empty data, partial data."""

    def test_parse_to_ir_full_data(self):
        """Kiểm tra parse_to_ir với đầy đủ dữ liệu hội thoại, tin nhắn, thông báo."""
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_001",
                    "name": "Phòng chat",
                    "conversation_type": "direct",
                }
            ],
            "messages": [
                {
                    "message_id": "msg_001",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                    "content": "Chào bạn",
                }
            ],
            "notifications": [
                {
                    "notification_id": "notif_001",
                    "conversation_id": "conv_001",
                    "target_user_id": "user_002",
                }
            ],
            "redis_url": "redis://localhost:6379/0",
        }
        ir = parse_to_ir(data)
        assert len(ir.conversations) == 1
        assert len(ir.messages) == 1
        assert len(ir.notifications) == 1
        assert ir.redis_url == "redis://localhost:6379/0"
        assert ir.conversations[0].conversation_id == "conv_001"
        assert ir.messages[0].message_id == "msg_001"
        assert ir.notifications[0].notification_id == "notif_001"

    def test_parse_to_ir_empty_data(self):
        """Kiểm tra parse_to_ir với dữ liệu rỗng trả về IR trống."""
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.conversations) == 0
        assert len(ir.messages) == 0
        assert len(ir.notifications) == 0
        assert ir.redis_url == ""
        assert ir.use_websocket is True

    def test_parse_to_ir_only_conversations(self):
        """Kiểm tra parse_to_ir chỉ có hội thoại, không có tin nhắn và thông báo."""
        data = {
            "conversations": [
                {
                    "conversation_id": "conv_only",
                    "conversation_type": "group",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.conversations) == 1
        assert len(ir.messages) == 0
        assert len(ir.notifications) == 0

    def test_parse_to_ir_only_messages(self):
        """Kiểm tra parse_to_ir chỉ có tin nhắn, không có hội thoại và thông báo."""
        data = {
            "messages": [
                {
                    "message_id": "msg_only",
                    "conversation_id": "conv_001",
                    "sender_id": "user_001",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.conversations) == 0
        assert len(ir.messages) == 1
        assert len(ir.notifications) == 0
        assert ir.messages[0].message_id == "msg_only"

    def test_parse_to_ir_with_redis_url_and_websocket(self):
        """Kiểm tra parse_to_ir với redis_url và use_websocket tùy chỉnh."""
        data = {
            "redis_url": "redis://prod-server:6379/5",
            "use_websocket": False,
        }
        ir = parse_to_ir(data)
        assert ir.redis_url == "redis://prod-server:6379/5"
        assert ir.use_websocket is False
