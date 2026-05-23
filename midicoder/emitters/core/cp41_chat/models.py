# coding: utf-8
"""
Mô-đun models cho CP41 — Chat & Messaging.

Định nghĩa các dataclass biểu diễn:
- MessageType: Loại tin nhắn (text, image, video, audio, file, system, reaction, reply)
- MessageStatus: Trạng thái tin nhắn (sent, delivered, read, failed, pending)
- ConversationType: Loại hội thoại (direct, group, support, broadcast)
- NotificationType: Loại thông báo (new_message, mention, reply, system, mention_reply)
- ReadReceiptType: Loại xác nhận đọc (delivered, read, played)
- Conversation: Hội thoại (phòng chat) với metadata và người tham gia
- ChatMessage: Tin nhắn trong hội thoại (nội dung, đính kèm, phản hồi)
- ConversationParticipant: Người tham gia hội thoại với vai trò
- ReadReceipt: Xác nhận đọc tin nhắn
- Notification: Thông báo chat gửi đến người dùng
- ChatManager: Engine quản lý chat — dispatcher message broadcast qua Redis pub/sub

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP41).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class MessageType(str, Enum):
    """Loại tin nhắn trong hệ thống chat.

    - TEXT: Tin nhắn văn bản thuần
    - IMAGE: Tin nhắn ảnh
    - VIDEO: Tin nhắn video
    - AUDIO: Tin nhắn âm thanh
    - FILE: Tin nhắn file đính kèm
    - SYSTEM: Tin nhắn hệ thống (thông báo, cảnh báo)
    - REACTION: Phản ứng emoji trên tin nhắn
    - REPLY: Tin nhắn trả lời cho một tin nhắn khác
    """
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    SYSTEM = "system"
    REACTION = "reaction"
    REPLY = "reply"


class MessageStatus(str, Enum):
    """Trạng thái của tin nhắn.

    - SENT: Đã gửi từ máy khách
    - DELIVERED: Đã giao đến máy nhận
    - READ: Đã được người nhận đọc
    - FAILED: Gửi thất bại
    - PENDING: Đang chờ gửi
    """
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class ConversationType(str, Enum):
    """Loại hội thoại.

    - DIRECT: Trò chuyện trực tiếp giữa 2 người
    - GROUP: Trò chuyện nhóm (nhiều người tham gia)
    - SUPPORT: Hỗ trợ khách hàng
    - BROADCAST: Phát sóng cho nhiều người nhận
    """
    DIRECT = "direct"
    GROUP = "group"
    SUPPORT = "support"
    BROADCAST = "broadcast"


class NotificationType(str, Enum):
    """Loại thông báo trong hệ thống chat.

    - NEW_MESSAGE: Tin nhắn mới trong hội thoại
    - MENTION: Được nhắc đến trong tin nhắn (@mention)
    - REPLY: Có người trả lời tin nhắn của mình
    - SYSTEM: Thông báo hệ thống (cập nhật, bảo trì)
    - MENTION_REPLY: Được nhắc đến trong tin nhắn trả lời
    """
    NEW_MESSAGE = "new_message"
    MENTION = "mention"
    REPLY = "reply"
    SYSTEM = "system"
    MENTION_REPLY = "mention_reply"


class ReadReceiptType(str, Enum):
    """Loại xác nhận đọc tin nhắn.

    - DELIVERED: Tin nhắn đã được giao
    - READ: Tin nhắn đã được đọc
    - PLAYED: Nội dung đa phương tiện đã được phát
    """
    DELIVERED = "delivered"
    READ = "read"
    PLAYED = "played"


# ===========================================================================
# Conversation
# ===========================================================================


@dataclass
class Conversation:
    """Hội thoại (phòng chat) — chứa metadata và danh sách người tham gia.

    Mỗi hội thoại có loại (direct/group/support/broadcast), người tạo,
    và giới hạn số lượng người tham gia tối đa.

    Attributes:
        conversation_id: ID duy nhất của hội thoại
        name: Tên hội thoại (tùy chọn cho direct chat)
        conversation_type: Loại hội thoại
        created_by: ID người tạo hội thoại
        max_participants: Số người tham gia tối đa (mặc định 100)
        is_active: Hội thoại có đang hoạt động không
        metadata: Dữ liệu bổ sung (dict tùy chỉnh)
        created_at: Thời điểm tạo hội thoại
        updated_at: Thời điểm cập nhật cuối
    """
    conversation_id: str
    name: str = ""
    conversation_type: ConversationType = ConversationType.DIRECT
    created_by: str = ""
    max_participants: int = 100
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate hội thoại sau khi khởi tạo."""
        if not self.conversation_id or not self.conversation_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason=f"conversation_id bắt buộc và không được để trống",
            )

        if self.max_participants < 1:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason=f"max_participants phải lớn hơn 0, nhận được: {self.max_participants}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Conversation sang dict."""
        return {
            "conversation_id": self.conversation_id,
            "name": self.name,
            "conversation_type": self.conversation_type.value,
            "created_by": self.created_by,
            "max_participants": self.max_participants,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        """Tạo Conversation từ dict."""
        return cls(
            conversation_id=data.get("conversation_id", ""),
            name=data.get("name", ""),
            conversation_type=ConversationType(data.get("conversation_type", "direct")),
            created_by=data.get("created_by", ""),
            max_participants=data.get("max_participants", 100),
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# ChatMessage
# ===========================================================================


@dataclass
class ChatMessage:
    """Tin nhắn trong hội thoại.

    Mỗi tin nhắn có loại (text/image/video/...), nội dung, danh sách
    file đính kèm, và trạng thái giao/nhận.

    Attributes:
        message_id: ID duy nhất của tin nhắn
        conversation_id: ID hội thoại chứa tin nhắn này
        sender_id: ID người gửi tin nhắn
        message_type: Loại tin nhắn
        content: Nội dung tin nhắn (văn bản hoặc metadata đa phương tiện)
        attachments: Danh sách file đính kèm (dict: url, filename, mime_type, size)
        reply_to: ID tin nhắn được trả lời (nullable)
        status: Trạng thái tin nhắn
        created_at: Thời điểm gửi tin nhắn
    """
    message_id: str
    conversation_id: str
    sender_id: str
    message_type: MessageType = MessageType.TEXT
    content: str = ""
    attachments: list[dict[str, Any]] = field(default_factory=list)
    reply_to: str | None = None
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate tin nhắn sau khi khởi tạo."""
        if not self.message_id or not self.message_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_MESSAGE_TOO_LONG,
                reason="message_id bắt buộc và không được để trống",
            )

        if not self.conversation_id or not self.conversation_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason="conversation_id bắt buộc cho tin nhắn",
            )

        if not self.sender_id or not self.sender_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason="sender_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ChatMessage sang dict."""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "attachments": self.attachments,
            "reply_to": self.reply_to,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage":
        """Tạo ChatMessage từ dict."""
        return cls(
            message_id=data.get("message_id", ""),
            conversation_id=data.get("conversation_id", ""),
            sender_id=data.get("sender_id", ""),
            message_type=MessageType(data.get("message_type", "text")),
            content=data.get("content", ""),
            attachments=data.get("attachments", []),
            reply_to=data.get("reply_to"),
            status=MessageStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# ConversationParticipant
# ===========================================================================


@dataclass
class ConversationParticipant:
    """Người tham gia hội thoại.

    Theo dõi vai trò của mỗi user trong hội thoại: admin, member, muted.

    Attributes:
        participant_id: ID duy nhất của bản ghi tham gia
        conversation_id: ID hội thoại
        user_id: ID người dùng tham gia
        role: Vai trò trong hội thoại (admin, member, muted)
        joined_at: Thời điểm tham gia
        last_read_message_id: ID tin nhắn cuối cùng đã đọc
    """
    participant_id: str
    conversation_id: str
    user_id: str
    role: str = "member"
    joined_at: datetime | None = None
    last_read_message_id: str | None = None

    def __post_init__(self) -> None:
        """Validate người tham gia sau khi khởi tạo."""
        if not self.participant_id or not self.participant_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason="participant_id bắt buộc và không được để trống",
            )

        if not self.conversation_id or not self.conversation_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason="conversation_id bắt buộc cho người tham gia",
            )

        if not self.user_id or not self.user_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason="user_id bắt buộc và không được để trống",
            )

        valid_roles = ("admin", "member", "muted")
        if self.role not in valid_roles:
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason=f"role phải là một trong {valid_roles}, nhận được: {self.role}",
            )

        if self.joined_at is None:
            self.joined_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConversationParticipant sang dict."""
        return {
            "participant_id": self.participant_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_read_message_id": self.last_read_message_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationParticipant":
        """Tạo ConversationParticipant từ dict."""
        return cls(
            participant_id=data.get("participant_id", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            role=data.get("role", "member"),
            joined_at=datetime.fromisoformat(data["joined_at"]) if data.get("joined_at") else None,
            last_read_message_id=data.get("last_read_message_id"),
        )


# ===========================================================================
# ReadReceipt
# ===========================================================================


@dataclass
class ReadReceipt:
    """Xác nhận đọc tin nhắn.

    Ghi nhận khi một người dùng đã xem/phát nội dung tin nhắn.

    Attributes:
        receipt_id: ID duy nhất của xác nhận đọc
        message_id: ID tin nhắn được xác nhận
        conversation_id: ID hội thoại chứa tin nhắn
        user_id: ID người dùng xác nhận đọc
        receipt_type: Loại xác nhận (delivered, read, played)
        created_at: Thời điểm xác nhận
    """
    receipt_id: str
    message_id: str
    conversation_id: str
    user_id: str
    receipt_type: ReadReceiptType = ReadReceiptType.READ
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate xác nhận đọc sau khi khởi tạo."""
        if not self.receipt_id or not self.receipt_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_NOTIFICATION_SEND_FAILED,
                reason="receipt_id bắt buộc và không được để trống",
            )

        if not self.message_id or not self.message_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_NOTIFICATION_SEND_FAILED,
                reason="message_id bắt buộc cho xác nhận đọc",
            )

        if not self.user_id or not self.user_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason="user_id bắt buộc cho xác nhận đọc",
            )

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ReadReceipt sang dict."""
        return {
            "receipt_id": self.receipt_id,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "receipt_type": self.receipt_type.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReadReceipt":
        """Tạo ReadReceipt từ dict."""
        return cls(
            receipt_id=data.get("receipt_id", ""),
            message_id=data.get("message_id", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            receipt_type=ReadReceiptType(data.get("receipt_type", "read")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# Notification
# ===========================================================================


@dataclass
class Notification:
    """Thông báo chat gửi đến người dùng.

    Tạo khi có sự kiện mới: tin nhắn mới, được nhắc đến, trả lời, v.v.

    Attributes:
        notification_id: ID duy nhất của thông báo
        conversation_id: ID hội thoại liên quan
        target_user_id: ID người nhận thông báo
        notification_type: Loại thông báo
        message_id: ID tin nhắn liên quan (nullable)
        is_read: Thông báo đã được đọc chưa
        created_at: Thời điểm tạo thông báo
    """
    notification_id: str
    conversation_id: str
    target_user_id: str
    notification_type: NotificationType = NotificationType.NEW_MESSAGE
    message_id: str | None = None
    is_read: bool = False
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate thông báo sau khi khởi tạo."""
        if not self.notification_id or not self.notification_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_NOTIFICATION_SEND_FAILED,
                reason="notification_id bắt buộc và không được để trống",
            )

        if not self.conversation_id or not self.conversation_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason="conversation_id bắt buộc cho thông báo",
            )

        if not self.target_user_id or not self.target_user_id.strip():
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                reason="target_user_id bắt buộc và không được để trống",
            )

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển Notification sang dict."""
        return {
            "notification_id": self.notification_id,
            "conversation_id": self.conversation_id,
            "target_user_id": self.target_user_id,
            "notification_type": self.notification_type.value,
            "message_id": self.message_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Notification":
        """Tạo Notification từ dict."""
        return cls(
            notification_id=data.get("notification_id", ""),
            conversation_id=data.get("conversation_id", ""),
            target_user_id=data.get("target_user_id", ""),
            notification_type=NotificationType(data.get("notification_type", "new_message")),
            message_id=data.get("message_id"),
            is_read=data.get("is_read", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# ChatManager
# ===========================================================================


class ChatManager:
    """Engine quản lý chat — dispatcher message broadcast qua Redis pub/sub.

    In-memory dispatcher cho message broadcast: quản lý hội thoại,
    người tham gia, gửi tin nhắn, xác nhận đọc, và thông báo.
    Tích hợp Redis pub/sub để broadcast realtime đến các client kết nối.

    Workflow:
    1. Tạo hội thoại và thêm người tham gia
    2. Gửi tin nhắn — validate người gửi, kiểm tra độ dài nội dung
    3. Tạo thông báo cho các người tham gia khác
    4. Broadcast tin nhắn đến các client kết nối qua Redis pub/sub
    5. Xác nhận đọc tin nhắn
    6. Truy vấn hội thoại và lịch sử tin nhắn

    Attributes:
        conversations: Dict conversation_id -> Conversation
        messages: Dict message_id -> ChatMessage
        participants: Dict participant_id -> ConversationParticipant
        notifications: Dict notification_id -> Notification
        connected_clients: Danh sách client kết nối (WebSocket/SSE connections)
    """

    def __init__(self) -> None:
        """Khởi tạo ChatManager với các bộ sưu tập rỗng."""
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, ChatMessage] = {}
        self.participants: dict[str, ConversationParticipant] = {}
        self.notifications: dict[str, Notification] = {}
        self.connected_clients: list[str] = []
        self._notification_counter = 0
        self._receipt_counter = 0

    def add_conversation(self, conv: Conversation) -> None:
        """Thêm hội thoại mới.

        Validate hội thoại không trùng lặp trước khi thêm vào store.

        Args:
            conv: Conversation cần thêm

        Raises:
            MidicoderError: Nếu conversation_id đã tồn tại (MDC-CP41-002 — duplicate)
        """
        if conv.conversation_id in self.conversations:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                reason=f"conversation_id '{conv.conversation_id}' đã tồn tại",
            )
        self.conversations[conv.conversation_id] = conv

    def add_participant(self, participant: ConversationParticipant) -> None:
        """Thêm người tham gia vào hội thoại.

        Validate hội thoại tồn tại trước khi thêm người tham gia.

        Args:
            participant: ConversationParticipant cần thêm

        Raises:
            MidicoderError: Nếu conversation_id không tồn tại (MDC-CP41-001)
        """
        if participant.conversation_id not in self.conversations:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                conversation_id=participant.conversation_id,
            )
        self.participants[participant.participant_id] = participant

    def send_message(self, message: ChatMessage) -> ChatMessage:
        """Gửi tin nhắn trong hội thoại.

        Validate: (1) người gửi phải là thành viên hội thoại,
        (2) nội dung tin nhắn không vượt quá 4096 ký tự.
        Sau đó lưu tin nhắn và tạo thông báo cho các người tham gia khác.

        Args:
            message: ChatMessage cần gửi

        Returns:
            ChatMessage đã lưu

        Raises:
            MidicoderError: Nếu người gửi không phải thành viên (MDC-CP41-003)
            MidicoderError: Nếu nội dung quá 4096 ký tự (MDC-CP41-002)
            MidicoderError: Nếu hội thoại không tồn tại (MDC-CP41-001)
        """
        # Validate hội thoại tồn tại
        if message.conversation_id not in self.conversations:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                conversation_id=message.conversation_id,
            )

        # Validate người gửi là thành viên hội thoại
        if not self._is_participant(message.conversation_id, message.sender_id):
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                user_id=message.sender_id,
                conversation_id=message.conversation_id,
            )

        # Validate và kiểm tra nội dung tin nhắn
        self.validate_message(message)

        # Cập nhật trạng thái và lưu tin nhắn
        message.status = MessageStatus.SENT
        self.messages[message.message_id] = message

        # Tạo thông báo cho các người tham gia khác
        self._create_notifications(message)

        # Broadcast đến các client kết nối
        self.broadcast_to_conversation(message.conversation_id, message)

        return message

    def mark_as_read(self, conversation_id: str, user_id: str, message_id: str) -> ReadReceipt:
        """Đánh dấu tin nhắn đã đọc và tạo ReadReceipt.

        Args:
            conversation_id: ID hội thoại chứa tin nhắn
            user_id: ID người dùng đánh dấu đã đọc
            message_id: ID tin nhắn

        Returns:
            ReadReceipt đã tạo

        Raises:
            MidicoderError: Nếu hội thoại không tồn tại (MDC-CP41-001)
            MidicoderError: Nếu người dùng không phải thành viên (MDC-CP41-003)
        """
        # Validate hội thoại tồn tại
        if conversation_id not in self.conversations:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                conversation_id=conversation_id,
            )

        # Validate người dùng là thành viên
        if not self._is_participant(conversation_id, user_id):
            EM.raise_error(
                ErrorCode.CP41_CHAT_USER_NOT_IN_CONVERSATION,
                user_id=user_id,
                conversation_id=conversation_id,
            )

        # Tạo ReadReceipt
        self._receipt_counter += 1
        receipt_id = f"receipt_{self._receipt_counter}_{int(time.time() * 1000)}"

        receipt = ReadReceipt(
            receipt_id=receipt_id,
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            receipt_type=ReadReceiptType.READ,
        )

        # Cập nhật last_read_message_id cho người tham gia
        for p in self.participants.values():
            if p.conversation_id == conversation_id and p.user_id == user_id:
                p.last_read_message_id = message_id
                break

        return receipt

    def get_conversation(self, conversation_id: str) -> Conversation:
        """Lấy hội thoại theo ID.

        Args:
            conversation_id: ID hội thoại cần lấy

        Returns:
            Conversation nếu tìm thấy

        Raises:
            MidicoderError: Nếu không tìm thấy hội thoại (MDC-CP41-001)
        """
        if conversation_id not in self.conversations:
            EM.raise_error(
                ErrorCode.CP41_CHAT_CONVERSATION_NOT_FOUND,
                conversation_id=conversation_id,
            )
        return self.conversations[conversation_id]

    def get_messages(self, conversation_id: str, limit: int = 50) -> list[ChatMessage]:
        """Lấy danh sách tin nhắn trong hội thoại.

        Trả về tin nhắn được sắp xếp theo created_at giảm dần (mới nhất trước).

        Args:
            conversation_id: ID hội thoại
            limit: Số lượng tin nhắn tối đa (mặc định 50)

        Returns:
            Danh sách ChatMessage sắp xếp theo created_at giảm dần
        """
        conv_messages = [
            msg for msg in self.messages.values()
            if msg.conversation_id == conversation_id
        ]

        # Sắp xếp theo created_at giảm dần (mới nhất trước)
        conv_messages.sort(
            key=lambda m: m.created_at if m.created_at else datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        return conv_messages[:limit]

    def broadcast_to_conversation(self, conversation_id: str, message: ChatMessage) -> int:
        """Broadcast tin nhắn đến tất cả client kết nối trong hội thoại.

        Trong môi trường production, phương thức này sẽ publish tin nhắn
        qua Redis pub/sub channel. Trong môi trường in-memory, đếm số
        client đang kết nối.

        Args:
            conversation_id: ID hội thoại
            message: ChatMessage cần broadcast

        Returns:
            Số lượng client nhận được tin nhắn
        """
        client_count = len(self.connected_clients)
        # Trong production: redis.publish(f"chat:{conversation_id}", json.dumps(message.to_dict()))
        return client_count

    def validate_message(self, message: ChatMessage) -> None:
        """Validate tin nhắn trước khi gửi.

        Kiểm tra: (1) độ dài nội dung <= 4096 ký tự,
        (2) content filter hook để kiểm tra nội dung phù hợp.

        Args:
            message: ChatMessage cần validate

        Raises:
            MidicoderError: Nếu nội dung quá 4096 ký tự (MDC-CP41-002)
            MidicoderError: Nếu vi phạm content filter (MDC-CP41-009)
        """
        # Kiểm tra độ dài nội dung
        if len(message.content) > 4096:
            EM.raise_error(
                ErrorCode.CP41_CHAT_MESSAGE_TOO_LONG,
                reason=f"Nội dung tin nhắn không được vượt quá 4096 ký tự (hiện tại: {len(message.content)} ký tự)",
            )

        # Content filter hook — kiểm tra nội dung phù hợp
        self._content_filter(message.content)

    def connect_client(self, client_id: str) -> None:
        """Thêm client vào danh sách kết nối.

        Args:
            client_id: ID duy nhất của client WebSocket/SSE
        """
        if client_id not in self.connected_clients:
            self.connected_clients.append(client_id)

    def disconnect_client(self, client_id: str) -> bool:
        """Xóa client khỏi danh sách kết nối.

        Args:
            client_id: ID client cần ngắt kết nối

        Returns:
            True nếu ngắt kết nối thành công
        """
        if client_id in self.connected_clients:
            self.connected_clients.remove(client_id)
            return True
        return False

    def _is_participant(self, conversation_id: str, user_id: str) -> bool:
        """Kiểm tra user có phải thành viên hội thoại không.

        Args:
            conversation_id: ID hội thoại
            user_id: ID người dùng

        Returns:
            True nếu user là thành viên
        """
        return any(
            p.conversation_id == conversation_id and p.user_id == user_id
            for p in self.participants.values()
        )

    def _create_notifications(self, message: ChatMessage) -> None:
        """Tạo thông báo cho các người tham gia khác trong hội thoại.

        Tự động tạo notification cho tất cả người tham gia (trừ người gửi).

        Args:
            message: ChatMessage đã gửi
        """
        conv_participants = [
            p for p in self.participants.values()
            if p.conversation_id == message.conversation_id and p.user_id != message.sender_id
        ]

        for participant in conv_participants:
            self._notification_counter += 1
            notification_id = f"notif_{self._notification_counter}_{int(time.time() * 1000)}"

            notification = Notification(
                notification_id=notification_id,
                conversation_id=message.conversation_id,
                target_user_id=participant.user_id,
                notification_type=NotificationType.NEW_MESSAGE,
                message_id=message.message_id,
            )
            self.notifications[notification_id] = notification

    def _content_filter(self, content: str) -> None:
        """Kiểm tra nội dung tin nhắn qua content filter.

        Hook để mở rộng kiểm tra nội dung. Hiện tại chỉ kiểm tra
        nếu nội dung rỗng (không phải lỗi, chỉ là placeholder).

        Args:
            content: Nội dung tin nhắn cần kiểm tra

        Raises:
            MidicoderError: Nếu vi phạm content filter (MDC-CP41-009)
        """
        # Placeholder cho content filter — có thể mở rộng
        # Ví dụ: kiểm tra từ cấm, nội dung độc hại, spam, v.v.
        pass

    def get_participants(self, conversation_id: str) -> list[ConversationParticipant]:
        """Lấy danh sách người tham gia hội thoại.

        Args:
            conversation_id: ID hội thoại

        Returns:
            Danh sách ConversationParticipant trong hội thoại
        """
        return [
            p for p in self.participants.values()
            if p.conversation_id == conversation_id
        ]

    def get_unread_notifications(self, user_id: str) -> list[Notification]:
        """Lấy danh sách thông báo chưa đọc của người dùng.

        Args:
            user_id: ID người dùng

        Returns:
            Danh sách Notification chưa đọc
        """
        return [
            n for n in self.notifications.values()
            if n.target_user_id == user_id and not n.is_read
        ]

    def mark_notification_read(self, notification_id: str) -> bool:
        """Đánh dấu thông báo đã đọc.

        Args:
            notification_id: ID thông báo

        Returns:
            True nếu đánh dấu thành công
        """
        if notification_id in self.notifications:
            self.notifications[notification_id].is_read = True
            return True
        return False
