# coding: utf-8
"""
Kiểm tra mô-đun models cho CP41 — Chat & Messaging.

Bao gồm các tests cho:
- Enums: MessageType, MessageStatus, ConversationType, NotificationType, ReadReceiptType
- Conversation: tạo, validate, to_dict/from_dict
- ChatMessage: tạo, validate độ dài nội dung, to_dict/from_dict
- ConversationParticipant: tạo, validate vai trò, to_dict/from_dict
- ReadReceipt: tạo, to_dict/from_dict
- Notification: tạo, to_dict/from_dict
- ChatManager: thêm hội thoại, gửi tin nhắn, broadcast, xác nhận đọc, thông báo
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP41
# ===========================================================================


class TestCP41ErrorCodes:
    """Kiểm tra các mã lỗi CP41 đã được định nghĩa đúng."""

    def test_cp41_conversation_not_found_code(self):
        """Kiểm tra mã lỗi hội thoại không tồn tại."""
        assert ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND == "MDC-CP41-001"

    def test_cp41_message_too_long_code(self):
        """Kiểm tra mã lỗi tin nhắn quá dài."""
        assert ErrorCode.CP41_CHAT_MESSAGE_TOO_LONG == "MDC-CP41-002"

    def test_cp41_user_not_in_conversation_code(self):
        """Kiểm tra mã lỗi người dùng không phải thành viên hội thoại."""
        assert ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION == "MDC-CP41-003"

    def test_cp41_websocket_connection_failed_code(self):
        """Kiểm tra mã lỗi kết nối WebSocket thất bại."""
        assert ErrorCode.CP41_CHAT_WEBSOCKET_CONNECTION_FAILED == "MDC-CP41-004"

    def test_cp41_redis_publish_failed_code(self):
        """Kiểm tra mã lỗi publish qua Redis thất bại."""
        assert ErrorCode.CP41_CHAT_REDIS_PUBLISH_FAILED == "MDC-CP41-005"

    def test_cp41_notification_send_failed_code(self):
        """Kiểm tra mã lỗi gửi thông báo thất bại."""
        assert ErrorCode.CP41_CHAT_NOTIFICATION_SEND_FAILED == "MDC-CP41-006"

    def test_cp41_attachment_too_large_code(self):
        """Kiểm tra mã lỗi file đính kèm quá lớn."""
        assert ErrorCode.CP41_CHAT_MESSAGE_ATTACHMENT_TOO_LARGE == "MDC-CP41-007"

    def test_cp41_rate_limit_exceeded_code(self):
        """Kiểm tra mã lỗi vượt quá giới hạn tốc độ."""
        assert ErrorCode.CP41_CHAT_RATE_LIMIT_EXCEEDED == "MDC-CP41-008"

    def test_cp41_content_filter_violation_code(self):
        """Kiểm tra mã lỗi vi phạm bộ lọc nội dung."""
        assert ErrorCode.CP41_CHAT_CONTENT_FILTER_VIOLATION == "MDC-CP41-009"

    def test_cp41_sse_connection_closed_code(self):
        """Kiểm tra mã lỗi kết nối SSE bị đóng."""
        assert ErrorCode.CP41_CHAT_SSE_CONNECTION_CLOSED == "MDC-CP41-010"


# ===========================================================================
# Test MessageType Enum
# ===========================================================================


class TestMessageType:
    """Kiểm tra các giá trị của enum MessageType."""

    def test_text_value(self):
        """Kiểm tra giá trị TEXT của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.TEXT.value == "text"

    def test_image_value(self):
        """Kiểm tra giá trị IMAGE của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.IMAGE.value == "image"

    def test_video_value(self):
        """Kiểm tra giá trị VIDEO của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.VIDEO.value == "video"

    def test_audio_value(self):
        """Kiểm tra giá trị AUDIO của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.AUDIO.value == "audio"

    def test_file_value(self):
        """Kiểm tra giá trị FILE của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.FILE.value == "file"

    def test_system_value(self):
        """Kiểm tra giá trị SYSTEM của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.SYSTEM.value == "system"

    def test_reaction_value(self):
        """Kiểm tra giá trị REACTION của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.REACTION.value == "reaction"

    def test_reply_value(self):
        """Kiểm tra giá trị REPLY của MessageType."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert MessageType.REPLY.value == "reply"

    def test_members_count(self):
        """Kiểm tra số lượng thành viên của MessageType bằng 8."""
        from midicoder.packs.cp41_chat.models import MessageType
        assert len(MessageType) == 8


# ===========================================================================
# Test MessageStatus Enum
# ===========================================================================


class TestMessageStatus:
    """Kiểm tra các giá trị của enum MessageStatus."""

    def test_sent_value(self):
        """Kiểm tra giá trị SENT của MessageStatus."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert MessageStatus.SENT.value == "sent"

    def test_delivered_value(self):
        """Kiểm tra giá trị DELIVERED của MessageStatus."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert MessageStatus.DELIVERED.value == "delivered"

    def test_read_value(self):
        """Kiểm tra giá trị READ của MessageStatus."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert MessageStatus.READ.value == "read"

    def test_failed_value(self):
        """Kiểm tra giá trị FAILED của MessageStatus."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert MessageStatus.FAILED.value == "failed"

    def test_pending_value(self):
        """Kiểm tra giá trị PENDING của MessageStatus."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert MessageStatus.PENDING.value == "pending"

    def test_members_count(self):
        """Kiểm tra số lượng thành viên của MessageStatus bằng 5."""
        from midicoder.packs.cp41_chat.models import MessageStatus
        assert len(MessageStatus) == 5


# ===========================================================================
# Test ConversationType Enum
# ===========================================================================


class TestConversationType:
    """Kiểm tra các giá trị của enum ConversationType."""

    def test_direct_value(self):
        """Kiểm tra giá trị DIRECT của ConversationType."""
        from midicoder.packs.cp41_chat.models import ConversationType
        assert ConversationType.DIRECT.value == "direct"

    def test_group_value(self):
        """Kiểm tra giá trị GROUP của ConversationType."""
        from midicoder.packs.cp41_chat.models import ConversationType
        assert ConversationType.GROUP.value == "group"

    def test_support_value(self):
        """Kiểm tra giá trị SUPPORT của ConversationType."""
        from midicoder.packs.cp41_chat.models import ConversationType
        assert ConversationType.SUPPORT.value == "support"

    def test_broadcast_value(self):
        """Kiểm tra giá trị BROADCAST của ConversationType."""
        from midicoder.packs.cp41_chat.models import ConversationType
        assert ConversationType.BROADCAST.value == "broadcast"

    def test_members_count(self):
        """Kiểm tra số lượng thành viên của ConversationType bằng 4."""
        from midicoder.packs.cp41_chat.models import ConversationType
        assert len(ConversationType) == 4


# ===========================================================================
# Test NotificationType Enum
# ===========================================================================


class TestNotificationType:
    """Kiểm tra các giá trị của enum NotificationType."""

    def test_new_message_value(self):
        """Kiểm tra giá trị NEW_MESSAGE của NotificationType."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert NotificationType.NEW_MESSAGE.value == "new_message"

    def test_mention_value(self):
        """Kiểm tra giá trị MENTION của NotificationType."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert NotificationType.MENTION.value == "mention"

    def test_reply_value(self):
        """Kiểm tra giá trị REPLY của NotificationType."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert NotificationType.REPLY.value == "reply"

    def test_system_value(self):
        """Kiểm tra giá trị SYSTEM của NotificationType."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert NotificationType.SYSTEM.value == "system"

    def test_mention_reply_value(self):
        """Kiểm tra giá trị MENTION_REPLY của NotificationType."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert NotificationType.MENTION_REPLY.value == "mention_reply"

    def test_members_count(self):
        """Kiểm tra số lượng thành viên của NotificationType bằng 5."""
        from midicoder.packs.cp41_chat.models import NotificationType
        assert len(NotificationType) == 5


# ===========================================================================
# Test ReadReceiptType Enum
# ===========================================================================


class TestReadReceiptType:
    """Kiểm tra các giá trị của enum ReadReceiptType."""

    def test_delivered_value(self):
        """Kiểm tra giá trị DELIVERED của ReadReceiptType."""
        from midicoder.packs.cp41_chat.models import ReadReceiptType
        assert ReadReceiptType.DELIVERED.value == "delivered"

    def test_read_value(self):
        """Kiểm tra giá trị READ của ReadReceiptType."""
        from midicoder.packs.cp41_chat.models import ReadReceiptType
        assert ReadReceiptType.READ.value == "read"

    def test_played_value(self):
        """Kiểm tra giá trị PLAYED của ReadReceiptType."""
        from midicoder.packs.cp41_chat.models import ReadReceiptType
        assert ReadReceiptType.PLAYED.value == "played"

    def test_members_count(self):
        """Kiểm tra số lượng thành viên của ReadReceiptType bằng 3."""
        from midicoder.packs.cp41_chat.models import ReadReceiptType
        assert len(ReadReceiptType) == 3


# ===========================================================================
# Test Conversation
# ===========================================================================


class TestConversation:
    """Kiểm tra Conversation — tạo, validate, serialize."""

    def test_create_valid_conversation(self):
        """Kiểm tra tạo hội thoại hợp lệ với các tham số đầy đủ."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_001",
            name="Phòng chat nhóm",
            conversation_type=ConversationType.GROUP,
            created_by="user_1",
        )
        assert conv.conversation_id == "conv_001"
        assert conv.name == "Phòng chat nhóm"
        assert conv.conversation_type == ConversationType.GROUP
        assert conv.created_by == "user_1"
        assert conv.max_participants == 100
        assert conv.is_active is True

    def test_create_conversation_with_empty_id_raises(self):
        """Kiểm tra tạo hội thoại với ID rỗng sẽ ném lỗi."""
        from midicoder.packs.cp41_chat.models import Conversation
        with pytest.raises(MidicoderError):
            Conversation(conversation_id="")

    def test_conversation_auto_timestamps(self):
        """Kiểm tra hội thoại tự động tạo timestamps."""
        from midicoder.packs.cp41_chat.models import Conversation
        conv = Conversation(conversation_id="conv_ts")
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_conversation_with_group_type(self):
        """Kiểm tra hội thoại với loại GROUP."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_grp",
            conversation_type=ConversationType.GROUP,
        )
        assert conv.conversation_type == ConversationType.GROUP

    def test_conversation_with_support_type(self):
        """Kiểm tra hội thoại với loại SUPPORT."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_sup",
            conversation_type=ConversationType.SUPPORT,
        )
        assert conv.conversation_type == ConversationType.SUPPORT

    def test_conversation_with_broadcast_type(self):
        """Kiểm tra hội thoại với loại BROADCAST."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_brd",
            conversation_type=ConversationType.BROADCAST,
        )
        assert conv.conversation_type == ConversationType.BROADCAST

    def test_conversation_with_max_participants(self):
        """Kiểm tra hội thoại với giới hạn người tham gia tùy chỉnh."""
        from midicoder.packs.cp41_chat.models import Conversation
        conv = Conversation(
            conversation_id="conv_max",
            max_participants=50,
        )
        assert conv.max_participants == 50

    def test_conversation_to_dict(self):
        """Kiểm tra chuyển Conversation sang dict."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_dict",
            name="Test Room",
            conversation_type=ConversationType.GROUP,
            created_by="user_1",
        )
        d = conv.to_dict()
        assert d["conversation_id"] == "conv_dict"
        assert d["name"] == "Test Room"
        assert d["conversation_type"] == "group"
        assert d["created_by"] == "user_1"
        assert d["max_participants"] == 100
        assert d["is_active"] is True
        assert "created_at" in d
        assert "updated_at" in d

    def test_conversation_from_dict_roundtrip(self):
        """Kiểm tra tạo Conversation từ dict và khôi phục đầy đủ."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        conv = Conversation(
            conversation_id="conv_rt",
            name="Round Trip Room",
            conversation_type=ConversationType.SUPPORT,
            created_by="admin_1",
            max_participants=200,
            is_active=False,
            metadata={"department": "support"},
        )
        d = conv.to_dict()
        restored = Conversation.from_dict(d)
        assert restored.conversation_id == "conv_rt"
        assert restored.name == "Round Trip Room"
        assert restored.conversation_type == ConversationType.SUPPORT
        assert restored.created_by == "admin_1"
        assert restored.max_participants == 200
        assert restored.is_active is False
        assert restored.metadata == {"department": "support"}

    def test_conversation_from_dict_without_optional_fields(self):
        """Kiểm tra tạo Conversation từ dict không có các trường tùy chọn."""
        from midicoder.packs.cp41_chat.models import Conversation, ConversationType
        data = {
            "conversation_id": "conv_min",
            "name": "",
            "created_by": "",
            "max_participants": 100,
            "is_active": True,
            "metadata": {},
            "created_at": None,
            "updated_at": None,
        }
        conv = Conversation.from_dict(data)
        assert conv.conversation_id == "conv_min"
        assert conv.conversation_type == ConversationType.DIRECT
        # __post_init__ tự động điền timestamps khi nhận None
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_conversation_is_active_default_true(self):
        """Kiểm tra is_active mặc định là True."""
        from midicoder.packs.cp41_chat.models import Conversation
        conv = Conversation(conversation_id="conv_active")
        assert conv.is_active is True

    def test_conversation_with_metadata(self):
        """Kiểm tra hội thoại với metadata tùy chỉnh."""
        from midicoder.packs.cp41_chat.models import Conversation
        conv = Conversation(
            conversation_id="conv_meta",
            metadata={"topic": "engineering", "priority": "high"},
        )
        assert conv.metadata["topic"] == "engineering"
        assert conv.metadata["priority"] == "high"


# ===========================================================================
# Test ChatMessage
# ===========================================================================


class TestChatMessage:
    """Kiểm tra ChatMessage — tạo, validate, serialize."""

    def test_create_valid_message(self):
        """Kiểm tra tạo tin nhắn hợp lệ với các tham số đầy đủ."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_001",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Xin chào mọi người!",
        )
        assert msg.message_id == "msg_001"
        assert msg.conversation_id == "conv_001"
        assert msg.sender_id == "user_1"
        assert msg.content == "Xin chào mọi người!"

    def test_create_message_with_empty_id_raises(self):
        """Kiểm tra tạo tin nhắn với ID rỗng sẽ ném lỗi."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        with pytest.raises(MidicoderError):
            ChatMessage(
                message_id="",
                conversation_id="conv_001",
                sender_id="user_1",
            )

    def test_create_message_with_too_long_content_raises(self):
        """Kiểm tra validate tin nhắn với nội dung quá 4096 ký tự sẽ ném lỗi."""
        from midicoder.packs.cp41_chat.models import ChatMessage, ChatManager
        long_content = "x" * 4097
        msg = ChatMessage(
            message_id="msg_long",
            conversation_id="conv_001",
            sender_id="user_1",
            content=long_content,
        )
        manager = ChatManager()
        with pytest.raises(MidicoderError):
            manager.validate_message(msg)

    def test_message_auto_timestamp(self):
        """Kiểm tra tin nhắn tự động tạo timestamp."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_ts",
            conversation_id="conv_001",
            sender_id="user_1",
        )
        assert msg.created_at is not None

    def test_message_with_image_type(self):
        """Kiểm tra tin nhắn với loại IMAGE."""
        from midicoder.packs.cp41_chat.models import ChatMessage, MessageType
        msg = ChatMessage(
            message_id="msg_img",
            conversation_id="conv_001",
            sender_id="user_1",
            message_type=MessageType.IMAGE,
            content="https://example.com/image.png",
        )
        assert msg.message_type == MessageType.IMAGE

    def test_message_with_attachments(self):
        """Kiểm tra tin nhắn với danh sách file đính kèm."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        attachments = [
            {"url": "https://example.com/file.pdf", "filename": "report.pdf", "mime_type": "application/pdf", "size": 1024},
        ]
        msg = ChatMessage(
            message_id="msg_attach",
            conversation_id="conv_001",
            sender_id="user_1",
            attachments=attachments,
        )
        assert len(msg.attachments) == 1
        assert msg.attachments[0]["filename"] == "report.pdf"

    def test_message_with_reply_to(self):
        """Kiểm tra tin nhắn với trường reply_to."""
        from midicoder.packs.cp41_chat.models import ChatMessage, MessageType
        msg = ChatMessage(
            message_id="msg_reply",
            conversation_id="conv_001",
            sender_id="user_1",
            message_type=MessageType.REPLY,
            reply_to="msg_001",
            content="Trả lời tin nhắn trước đó",
        )
        assert msg.reply_to == "msg_001"
        assert msg.message_type == MessageType.REPLY

    def test_message_status_default_sent(self):
        """Kiểm tra trạng thái mặc định của tin nhắn là PENDING."""
        from midicoder.packs.cp41_chat.models import ChatMessage, MessageStatus
        msg = ChatMessage(
            message_id="msg_status",
            conversation_id="conv_001",
            sender_id="user_1",
        )
        assert msg.status == MessageStatus.PENDING

    def test_message_to_dict(self):
        """Kiểm tra chuyển ChatMessage sang dict."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_dict",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Test content",
        )
        d = msg.to_dict()
        assert d["message_id"] == "msg_dict"
        assert d["conversation_id"] == "conv_001"
        assert d["sender_id"] == "user_1"
        assert d["content"] == "Test content"
        assert d["message_type"] == "text"
        assert d["status"] == "pending"
        assert "created_at" in d

    def test_message_from_dict_roundtrip(self):
        """Kiểm tra tạo ChatMessage từ dict và khôi phục đầy đủ."""
        from midicoder.packs.cp41_chat.models import ChatMessage, MessageType
        msg = ChatMessage(
            message_id="msg_rt",
            conversation_id="conv_rt",
            sender_id="user_rt",
            message_type=MessageType.IMAGE,
            content="image_url",
            attachments=[{"url": "https://ex.com/a.png", "filename": "a.png"}],
            reply_to="msg_parent",
        )
        d = msg.to_dict()
        restored = ChatMessage.from_dict(d)
        assert restored.message_id == "msg_rt"
        assert restored.conversation_id == "conv_rt"
        assert restored.sender_id == "user_rt"
        assert restored.message_type == MessageType.IMAGE
        assert restored.content == "image_url"
        assert len(restored.attachments) == 1
        assert restored.reply_to == "msg_parent"

    def test_message_from_dict_without_attachments(self):
        """Kiểm tra tạo ChatMessage từ dict không có attachments."""
        from midicoder.packs.cp41_chat.models import ChatMessage
        data = {
            "message_id": "msg_noattach",
            "conversation_id": "conv_001",
            "sender_id": "user_1",
            "message_type": "text",
            "content": "No attachments",
            "attachments": [],
            "reply_to": None,
            "status": "sent",
            "created_at": None,
        }
        msg = ChatMessage.from_dict(data)
        assert msg.message_id == "msg_noattach"
        assert msg.attachments == []

    def test_message_system_type(self):
        """Kiểm tra tin nhắn với loại SYSTEM."""
        from midicoder.packs.cp41_chat.models import ChatMessage, MessageType
        msg = ChatMessage(
            message_id="msg_sys",
            conversation_id="conv_001",
            sender_id="system",
            message_type=MessageType.SYSTEM,
            content="Hệ thống: Bảo trì vào thứ Bảy",
        )
        assert msg.message_type == MessageType.SYSTEM


# ===========================================================================
# Test ConversationParticipant
# ===========================================================================


class TestConversationParticipant:
    """Kiểm tra ConversationParticipant — tạo, validate, serialize."""

    def test_create_valid_participant(self):
        """Kiểm tra tạo người tham gia hợp lệ."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_001",
            conversation_id="conv_001",
            user_id="user_1",
        )
        assert p.participant_id == "part_001"
        assert p.conversation_id == "conv_001"
        assert p.user_id == "user_1"
        assert p.role == "member"

    def test_participant_auto_timestamp(self):
        """Kiểm tra người tham gia tự động tạo joined_at timestamp."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_ts",
            conversation_id="conv_001",
            user_id="user_1",
        )
        assert p.joined_at is not None

    def test_participant_admin_role(self):
        """Kiểm tra người tham gia với vai trò admin."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_admin",
            conversation_id="conv_001",
            user_id="user_1",
            role="admin",
        )
        assert p.role == "admin"

    def test_participant_muted_role(self):
        """Kiểm tra người tham gia với vai trò muted."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_muted",
            conversation_id="conv_001",
            user_id="user_2",
            role="muted",
        )
        assert p.role == "muted"

    def test_participant_with_last_read_message_id(self):
        """Kiểm tra người tham gia với last_read_message_id."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_read",
            conversation_id="conv_001",
            user_id="user_1",
            last_read_message_id="msg_010",
        )
        assert p.last_read_message_id == "msg_010"

    def test_participant_to_dict(self):
        """Kiểm tra chuyển ConversationParticipant sang dict."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_dict",
            conversation_id="conv_001",
            user_id="user_1",
            role="admin",
        )
        d = p.to_dict()
        assert d["participant_id"] == "part_dict"
        assert d["conversation_id"] == "conv_001"
        assert d["user_id"] == "user_1"
        assert d["role"] == "admin"
        assert "joined_at" in d

    def test_participant_from_dict_roundtrip(self):
        """Kiểm tra tạo ConversationParticipant từ dict và khôi phục đầy đủ."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_rt",
            conversation_id="conv_rt",
            user_id="user_rt",
            role="muted",
            last_read_message_id="msg_005",
        )
        d = p.to_dict()
        restored = ConversationParticipant.from_dict(d)
        assert restored.participant_id == "part_rt"
        assert restored.conversation_id == "conv_rt"
        assert restored.user_id == "user_rt"
        assert restored.role == "muted"
        assert restored.last_read_message_id == "msg_005"

    def test_participant_from_dict_without_optional(self):
        """Kiểm tra tạo ConversationParticipant từ dict không có trường tùy chọn."""
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        data = {
            "participant_id": "part_min",
            "conversation_id": "conv_001",
            "user_id": "user_1",
            "role": "member",
            "joined_at": None,
            "last_read_message_id": None,
        }
        p = ConversationParticipant.from_dict(data)
        assert p.participant_id == "part_min"
        assert p.role == "member"
        assert p.last_read_message_id is None


# ===========================================================================
# Test ReadReceipt
# ===========================================================================


class TestReadReceipt:
    """Kiểm tra ReadReceipt — tạo, validate, serialize."""

    def test_create_valid_receipt(self):
        """Kiểm tra tạo xác nhận đọc hợp lệ."""
        from midicoder.packs.cp41_chat.models import ReadReceipt, ReadReceiptType
        r = ReadReceipt(
            receipt_id="receipt_001",
            message_id="msg_001",
            conversation_id="conv_001",
            user_id="user_1",
        )
        assert r.receipt_id == "receipt_001"
        assert r.message_id == "msg_001"
        assert r.conversation_id == "conv_001"
        assert r.user_id == "user_1"
        assert r.receipt_type == ReadReceiptType.READ

    def test_receipt_auto_timestamp(self):
        """Kiểm tra xác nhận đọc tự động tạo timestamp."""
        from midicoder.packs.cp41_chat.models import ReadReceipt
        r = ReadReceipt(
            receipt_id="receipt_ts",
            message_id="msg_001",
            conversation_id="conv_001",
            user_id="user_1",
        )
        assert r.created_at is not None

    def test_receipt_read_type(self):
        """Kiểm tra xác nhận đọc với loại READ."""
        from midicoder.packs.cp41_chat.models import ReadReceipt, ReadReceiptType
        r = ReadReceipt(
            receipt_id="receipt_read",
            message_id="msg_001",
            conversation_id="conv_001",
            user_id="user_1",
            receipt_type=ReadReceiptType.READ,
        )
        assert r.receipt_type == ReadReceiptType.READ

    def test_receipt_to_dict(self):
        """Kiểm tra chuyển ReadReceipt sang dict."""
        from midicoder.packs.cp41_chat.models import ReadReceipt, ReadReceiptType
        r = ReadReceipt(
            receipt_id="receipt_dict",
            message_id="msg_001",
            conversation_id="conv_001",
            user_id="user_1",
            receipt_type=ReadReceiptType.PLAYED,
        )
        d = r.to_dict()
        assert d["receipt_id"] == "receipt_dict"
        assert d["message_id"] == "msg_001"
        assert d["receipt_type"] == "played"
        assert "created_at" in d

    def test_receipt_from_dict_roundtrip(self):
        """Kiểm tra tạo ReadReceipt từ dict và khôi phục đầy đủ."""
        from midicoder.packs.cp41_chat.models import ReadReceipt, ReadReceiptType
        r = ReadReceipt(
            receipt_id="receipt_rt",
            message_id="msg_rt",
            conversation_id="conv_rt",
            user_id="user_rt",
            receipt_type=ReadReceiptType.DELIVERED,
        )
        d = r.to_dict()
        restored = ReadReceipt.from_dict(d)
        assert restored.receipt_id == "receipt_rt"
        assert restored.message_id == "msg_rt"
        assert restored.receipt_type == ReadReceiptType.DELIVERED

    def test_receipt_delivered_type(self):
        """Kiểm tra xác nhận đọc với loại DELIVERED."""
        from midicoder.packs.cp41_chat.models import ReadReceipt, ReadReceiptType
        r = ReadReceipt(
            receipt_id="receipt_del",
            message_id="msg_001",
            conversation_id="conv_001",
            user_id="user_1",
            receipt_type=ReadReceiptType.DELIVERED,
        )
        assert r.receipt_type == ReadReceiptType.DELIVERED


# ===========================================================================
# Test Notification
# ===========================================================================


class TestNotification:
    """Kiểm tra Notification — tạo, validate, serialize."""

    def test_create_valid_notification(self):
        """Kiểm tra tạo thông báo hợp lệ."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_001",
            conversation_id="conv_001",
            target_user_id="user_1",
        )
        assert n.notification_id == "notif_001"
        assert n.conversation_id == "conv_001"
        assert n.target_user_id == "user_1"
        assert n.notification_type == NotificationType.NEW_MESSAGE
        assert n.is_read is False

    def test_notification_auto_timestamp(self):
        """Kiểm tra thông báo tự động tạo timestamp."""
        from midicoder.packs.cp41_chat.models import Notification
        n = Notification(
            notification_id="notif_ts",
            conversation_id="conv_001",
            target_user_id="user_1",
        )
        assert n.created_at is not None

    def test_notification_mention_type(self):
        """Kiểm tra thông báo với loại MENTION."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_mention",
            conversation_id="conv_001",
            target_user_id="user_1",
            notification_type=NotificationType.MENTION,
        )
        assert n.notification_type == NotificationType.MENTION

    def test_notification_reply_type(self):
        """Kiểm tra thông báo với loại REPLY."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_reply",
            conversation_id="conv_001",
            target_user_id="user_1",
            notification_type=NotificationType.REPLY,
            message_id="msg_001",
        )
        assert n.notification_type == NotificationType.REPLY
        assert n.message_id == "msg_001"

    def test_notification_system_type(self):
        """Kiểm tra thông báo với loại SYSTEM."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_sys",
            conversation_id="conv_001",
            target_user_id="user_1",
            notification_type=NotificationType.SYSTEM,
        )
        assert n.notification_type == NotificationType.SYSTEM

    def test_notification_is_read_default_false(self):
        """Kiểm tra is_read mặc định là False."""
        from midicoder.packs.cp41_chat.models import Notification
        n = Notification(
            notification_id="notif_read",
            conversation_id="conv_001",
            target_user_id="user_1",
        )
        assert n.is_read is False

    def test_notification_to_dict(self):
        """Kiểm tra chuyển Notification sang dict."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_dict",
            conversation_id="conv_001",
            target_user_id="user_1",
            notification_type=NotificationType.MENTION_REPLY,
            message_id="msg_001",
            is_read=True,
        )
        d = n.to_dict()
        assert d["notification_id"] == "notif_dict"
        assert d["conversation_id"] == "conv_001"
        assert d["target_user_id"] == "user_1"
        assert d["notification_type"] == "mention_reply"
        assert d["message_id"] == "msg_001"
        assert d["is_read"] is True
        assert "created_at" in d

    def test_notification_from_dict_roundtrip(self):
        """Kiểm tra tạo Notification từ dict và khôi phục đầy đủ."""
        from midicoder.packs.cp41_chat.models import Notification, NotificationType
        n = Notification(
            notification_id="notif_rt",
            conversation_id="conv_rt",
            target_user_id="user_rt",
            notification_type=NotificationType.REPLY,
            message_id="msg_rt",
            is_read=True,
        )
        d = n.to_dict()
        restored = Notification.from_dict(d)
        assert restored.notification_id == "notif_rt"
        assert restored.conversation_id == "conv_rt"
        assert restored.target_user_id == "user_rt"
        assert restored.notification_type == NotificationType.REPLY
        assert restored.message_id == "msg_rt"
        assert restored.is_read is True


# ===========================================================================
# Test ChatManager
# ===========================================================================


class TestChatManager:
    """Kiểm tra ChatManager — quản lý hội thoại, tin nhắn, thông báo."""

    def _setup_manager_with_conv_and_participant(self):
        """Thiết lập ChatManager với hội thoại và người tham gia mẫu."""
        from midicoder.packs.cp41_chat.models import (
            ChatManager,
            Conversation,
            ConversationParticipant,
        )
        manager = ChatManager()
        conv = Conversation(
            conversation_id="conv_001",
            name="Test Room",
            created_by="user_1",
        )
        manager.add_conversation(conv)

        participant = ConversationParticipant(
            participant_id="part_001",
            conversation_id="conv_001",
            user_id="user_1",
        )
        manager.add_participant(participant)

        return manager

    def test_add_conversation(self):
        """Kiểm tra thêm hội thoại vào ChatManager."""
        from midicoder.packs.cp41_chat.models import ChatManager, Conversation
        manager = ChatManager()
        conv = Conversation(conversation_id="conv_001")
        manager.add_conversation(conv)
        assert "conv_001" in manager.conversations
        assert manager.conversations["conv_001"].conversation_id == "conv_001"

    def test_add_duplicate_conversation_raises(self):
        """Kiểm tra thêm hội thoại trùng lặp sẽ ném lỗi."""
        from midicoder.packs.cp41_chat.models import ChatManager, Conversation
        manager = ChatManager()
        conv = Conversation(conversation_id="conv_dup")
        manager.add_conversation(conv)
        with pytest.raises(MidicoderError):
            manager.add_conversation(conv)

    def test_add_participant(self):
        """Kiểm tra thêm người tham gia vào hội thoại."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p = ConversationParticipant(
            participant_id="part_user2",
            conversation_id="conv_001",
            user_id="user_2",
        )
        manager.add_participant(p)
        assert "part_user2" in manager.participants
        assert manager.participants["part_user2"].user_id == "user_2"

    def test_add_participant_to_nonexistent_conversation_raises(self):
        """Kiểm tra thêm người tham gia vào hội thoại không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp41_chat.models import ChatManager, ConversationParticipant
        manager = ChatManager()
        p = ConversationParticipant(
            participant_id="part_bad",
            conversation_id="conv_notexist",
            user_id="user_1",
        )
        with pytest.raises(MidicoderError):
            manager.add_participant(p)

    def test_send_message_creates_message(self):
        """Kiểm tra gửi tin nhắn tạo và lưu tin nhắn vào store."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_send",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Nội dung tin nhắn",
        )
        result = manager.send_message(msg)
        assert "msg_send" in manager.messages
        assert result.message_id == "msg_send"

    def test_send_message_user_not_in_conversation_raises(self):
        """Kiểm tra gửi tin nhắn khi người gửi không phải thành viên sẽ ném lỗi."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_nouser",
            conversation_id="conv_001",
            sender_id="user_unknown",
            content="Tin nhắn",
        )
        with pytest.raises(MidicoderError):
            manager.send_message(msg)

    def test_send_message_too_long_raises(self):
        """Kiểm tra gửi tin nhắn quá 4096 ký tự sẽ ném lỗi."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        long_content = "x" * 4097
        msg = ChatMessage(
            message_id="msg_toolong",
            conversation_id="conv_001",
            sender_id="user_1",
            content=long_content,
        )
        with pytest.raises(MidicoderError):
            manager.send_message(msg)

    def test_send_message_validates_content(self):
        """Kiểm tra gửi tin nhắn validate nội dung tin nhắn."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_validate",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Nội dung hợp lệ",
        )
        result = manager.send_message(msg)
        assert result.content == "Nội dung hợp lệ"

    def test_send_message_stores_and_returns(self):
        """Kiểm tra gửi tin nhắn lưu vào store và trả về tin nhắn đã lưu."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_store",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Test",
        )
        returned = manager.send_message(msg)
        assert returned.message_id == "msg_store"
        stored = manager.messages["msg_store"]
        assert stored.content == "Test"

    def test_mark_as_read_creates_receipt(self):
        """Kiểm tra đánh dấu đã đọc tạo ReadReceipt."""
        manager = self._setup_manager_with_conv_and_participant()
        receipt = manager.mark_as_read("conv_001", "user_1", "msg_001")
        assert receipt.receipt_id is not None
        assert receipt.message_id == "msg_001"
        assert receipt.conversation_id == "conv_001"
        assert receipt.user_id == "user_1"

    def test_get_conversation(self):
        """Kiểm tra lấy hội thoại theo ID thành công."""
        manager = self._setup_manager_with_conv_and_participant()
        conv = manager.get_conversation("conv_001")
        assert conv.conversation_id == "conv_001"

    def test_get_conversation_not_found_raises(self):
        """Kiểm tra lấy hội thoại không tồn tại sẽ ném lỗi."""
        manager = self._setup_manager_with_conv_and_participant()
        with pytest.raises(MidicoderError):
            manager.get_conversation("conv_notexist")

    def test_get_messages_sorted_by_created_at_desc(self):
        """Kiểm tra lấy danh sách tin nhắn sắp xếp theo created_at giảm dần."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        from datetime import datetime, timezone, timedelta

        msg1 = ChatMessage(
            message_id="msg_first",
            conversation_id="conv_001",
            sender_id="user_1",
            content="First",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        msg2 = ChatMessage(
            message_id="msg_second",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Second",
            created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        )
        manager.messages["msg_first"] = msg1
        manager.messages["msg_second"] = msg2

        messages = manager.get_messages("conv_001")
        assert messages[0].message_id == "msg_second"
        assert messages[1].message_id == "msg_first"

    def test_get_messages_with_limit(self):
        """Kiểm tra lấy danh sách tin nhắn với giới hạn số lượng."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        from datetime import datetime, timezone

        for i in range(5):
            msg = ChatMessage(
                message_id=f"msg_limit_{i}",
                conversation_id="conv_001",
                sender_id="user_1",
                content=f"Message {i}",
                created_at=datetime(2025, 1, 1 + i, tzinfo=timezone.utc),
            )
            manager.messages[f"msg_limit_{i}"] = msg

        messages = manager.get_messages("conv_001", limit=3)
        assert len(messages) == 3

    def test_broadcast_to_conversation(self):
        """Kiểm tra broadcast tin nhắn đến các client đã kết nối."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        manager.connect_client("ws_client_1")
        manager.connect_client("ws_client_2")

        msg = ChatMessage(
            message_id="msg_bcast",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Broadcast test",
        )
        count = manager.broadcast_to_conversation("conv_001", msg)
        assert count == 2

    def test_broadcast_to_conversation_no_clients(self):
        """Kiểm tra broadcast khi không có client kết nối trả về 0."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_no_client",
            conversation_id="conv_001",
            sender_id="user_1",
        )
        count = manager.broadcast_to_conversation("conv_001", msg)
        assert count == 0

    def test_connect_client(self):
        """Kiểm tra kết nối client vào ChatManager."""
        manager = self._setup_manager_with_conv_and_participant()
        manager.connect_client("client_001")
        assert "client_001" in manager.connected_clients
        assert len(manager.connected_clients) == 1

    def test_disconnect_client(self):
        """Kiểm tra ngắt kết nối client khỏi ChatManager."""
        manager = self._setup_manager_with_conv_and_participant()
        manager.connect_client("client_001")
        result = manager.disconnect_client("client_001")
        assert result is True
        assert "client_001" not in manager.connected_clients

    def test_validate_message_valid(self):
        """Kiểm tra validate tin nhắn hợp lệ không ném lỗi."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_valid",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Nội dung hợp lệ dưới 4096 ký tự",
        )
        # Không ném lỗi
        manager.validate_message(msg)

    def test_validate_message_too_long(self):
        """Kiểm tra validate tin nhắn quá 4096 ký tự sẽ ném lỗi."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage
        msg = ChatMessage(
            message_id="msg_invalid",
            conversation_id="conv_001",
            sender_id="user_1",
            content="x" * 4097,
        )
        with pytest.raises(MidicoderError):
            manager.validate_message(msg)

    def test_get_participants(self):
        """Kiểm tra lấy danh sách người tham gia hội thoại."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ConversationParticipant
        p2 = ConversationParticipant(
            participant_id="part_u2",
            conversation_id="conv_001",
            user_id="user_2",
        )
        manager.add_participant(p2)
        participants = manager.get_participants("conv_001")
        assert len(participants) == 2

    def test_get_unread_notifications(self):
        """Kiểm tra lấy danh sách thông báo chưa đọc."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ConversationParticipant, Notification
        # Thêm người tham gia thứ 2
        p2 = ConversationParticipant(
            participant_id="part_u2",
            conversation_id="conv_001",
            user_id="user_2",
        )
        manager.add_participant(p2)

        # Thêm thông báo trực tiếp vào store
        notif = Notification(
            notification_id="notif_unread",
            conversation_id="conv_001",
            target_user_id="user_1",
            is_read=False,
        )
        manager.notifications["notif_unread"] = notif

        unread = manager.get_unread_notifications("user_1")
        assert len(unread) >= 1
        assert any(n.notification_id == "notif_unread" for n in unread)

    def test_mark_notification_read(self):
        """Kiểm tra đánh dấu thông báo đã đọc."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import Notification
        notif = Notification(
            notification_id="notif_mark",
            conversation_id="conv_001",
            target_user_id="user_1",
            is_read=False,
        )
        manager.notifications["notif_mark"] = notif

        result = manager.mark_notification_read("notif_mark")
        assert result is True
        assert manager.notifications["notif_mark"].is_read is True

    def test_send_message_creates_notification(self):
        """Kiểm tra gửi tin nhắn tạo thông báo cho người tham gia khác."""
        manager = self._setup_manager_with_conv_and_participant()
        from midicoder.packs.cp41_chat.models import ChatMessage, ConversationParticipant, NotificationType
        # Thêm người tham gia thứ 2
        p2 = ConversationParticipant(
            participant_id="part_u2",
            conversation_id="conv_001",
            user_id="user_2",
        )
        manager.add_participant(p2)

        msg = ChatMessage(
            message_id="msg_notif",
            conversation_id="conv_001",
            sender_id="user_1",
            content="Tin nhắn tạo thông báo",
        )
        manager.send_message(msg)

        # Kiểm tra có thông báo được tạo cho user_2
        user2_notifs = [
            n for n in manager.notifications.values()
            if n.target_user_id == "user_2"
        ]
        assert len(user2_notifs) >= 1
        assert user2_notifs[0].notification_type == NotificationType.NEW_MESSAGE

    def test_multiple_conversations(self):
        """Kiểm tra ChatManager quản lý nhiều hội thoại đồng thời."""
        from midicoder.packs.cp41_chat.models import ChatManager, Conversation
        manager = ChatManager()

        conv1 = Conversation(conversation_id="conv_a", name="Phòng A")
        conv2 = Conversation(conversation_id="conv_b", name="Phòng B")
        conv3 = Conversation(conversation_id="conv_c", name="Phòng C")

        manager.add_conversation(conv1)
        manager.add_conversation(conv2)
        manager.add_conversation(conv3)

        assert len(manager.conversations) == 3
        assert "conv_a" in manager.conversations
        assert "conv_b" in manager.conversations
        assert "conv_c" in manager.conversations
