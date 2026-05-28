# coding: utf-8
"""
Kiểm tra mô-đun recipes cho CP41 — Chat & Messaging.

Bao gồm các tests cho:
- RecipeOutput: tạo, fields, loại IR
- basic_chat_recipe: tên, mô tả, hội thoại, tin nhắn, không Redis, WebSocket
- full_messaging_recipe: tên, mô tả, hội thoại đa dạng, tin nhắn, thông báo, Redis
- to_dict roundtrip cho cả hai recipe
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_chat.recipes import (
    RecipeOutput,
    basic_chat_recipe,
    full_messaging_recipe,
)


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Kiểm tra RecipeOutput — dataclass cơ bản cho kết quả recipe."""

    def test_recipe_output_creation(self):
        """Kiểm tra tạo RecipeOutput với các trường hợp lệ."""
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = RecipeOutput(
            name="test_recipe",
            description="Mô tả test",
            ir=ChatIR(),
        )
        assert output.name == "test_recipe"
        assert output.description == "Mô tả test"
        assert isinstance(output.ir, ChatIR)

    def test_recipe_output_ir_is_chat_ir(self):
        """Kiểm tra IR của RecipeOutput có loại là ChatIR."""
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = RecipeOutput(
            name="ir_test",
            description="Kiểm tra loại IR",
            ir=ChatIR(),
        )
        assert type(output.ir).__name__ == "ChatIR"

    def test_recipe_output_has_name_and_description(self):
        """Kiểm tra RecipeOutput có tên và mô tả không rỗng."""
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = RecipeOutput(
            name="filled_recipe",
            description="Không để trống",
            ir=ChatIR(redis_url="redis://localhost:6379/0"),
        )
        assert output.name
        assert output.description
        assert output.ir.redis_url == "redis://localhost:6379/0"


# ===========================================================================
# Test basic_chat_recipe
# ===========================================================================


class TestBasicChatRecipe:
    """Kiểm tra basic_chat_recipe — tên, mô tả, hội thoại, tin nhắn, không Redis."""

    def test_basic_recipe_name(self):
        """Kiểm tra tên recipe chứa 'chat' hoặc 'basic'."""
        output = basic_chat_recipe()
        name_lower = output.name.lower()
        assert "chat" in name_lower or "basic" in name_lower

    def test_basic_recipe_description(self):
        """Kiểm tra mô tả recipe không rỗng."""
        output = basic_chat_recipe()
        assert output.description
        assert len(output.description.strip()) > 0

    def test_basic_recipe_has_two_conversations(self):
        """Kiểm tra recipe có đúng 2 hội thoại."""
        output = basic_chat_recipe()
        assert len(output.ir.conversations) == 2

    def test_basic_recipe_first_conversation_is_direct(self):
        """Kiểm tra hội thoại đầu tiên có loại là direct."""
        from midicoder.packs.cp_full_chat.models import ConversationType
        output = basic_chat_recipe()
        assert output.ir.conversations[0].conversation_type == ConversationType.DIRECT

    def test_basic_recipe_second_conversation_is_group(self):
        """Kiểm tra hội thoại thứ hai có loại là group."""
        from midicoder.packs.cp_full_chat.models import ConversationType
        output = basic_chat_recipe()
        assert output.ir.conversations[1].conversation_type == ConversationType.GROUP

    def test_basic_recipe_has_three_messages(self):
        """Kiểm tra recipe có đúng 3 tin nhắn."""
        output = basic_chat_recipe()
        assert len(output.ir.messages) == 3

    def test_basic_recipe_messages_reference_conversations(self):
        """Kiểm tra tin nhắn tham chiếu đến hội thoại hợp lệ."""
        output = basic_chat_recipe()
        conv_ids = {c.conversation_id for c in output.ir.conversations}
        for msg in output.ir.messages:
            assert msg.conversation_id in conv_ids

    def test_basic_recipe_no_redis_url(self):
        """Kiểm tra recipe không có URL Redis."""
        output = basic_chat_recipe()
        assert output.ir.redis_url == ""

    def test_basic_recipe_websocket_enabled(self):
        """Kiểm tra WebSocket được bật mặc định."""
        output = basic_chat_recipe()
        assert output.ir.use_websocket is True

    def test_basic_recipe_no_notifications(self):
        """Kiểm tra recipe không có thông báo nào."""
        output = basic_chat_recipe()
        assert len(output.ir.notifications) == 0

    def test_basic_recipe_conversations_have_valid_ids(self):
        """Kiểm tra hội thoại có ID hợp lệ (không rỗng)."""
        output = basic_chat_recipe()
        for conv in output.ir.conversations:
            assert conv.conversation_id
            assert len(conv.conversation_id.strip()) > 0

    def test_basic_recipe_messages_have_valid_ids(self):
        """Kiểm tra tin nhắn có ID hợp lệ (không rỗng)."""
        output = basic_chat_recipe()
        for msg in output.ir.messages:
            assert msg.message_id
            assert len(msg.message_id.strip()) > 0

    def test_basic_recipe_messages_have_senders(self):
        """Kiểm tra tin nhắn có người gửi hợp lệ."""
        output = basic_chat_recipe()
        for msg in output.ir.messages:
            assert msg.sender_id
            assert len(msg.sender_id.strip()) > 0

    def test_basic_recipe_conversations_have_max_participants(self):
        """Kiểm tra hội thoại có max_participants lớn hơn 0."""
        output = basic_chat_recipe()
        for conv in output.ir.conversations:
            assert conv.max_participants > 0

    def test_basic_recipe_conversations_are_active(self):
        """Kiểm tra tất cả hội thoại đều đang hoạt động."""
        output = basic_chat_recipe()
        for conv in output.ir.conversations:
            assert conv.is_active is True


# ===========================================================================
# Test full_messaging_recipe
# ===========================================================================


class TestFullMessagingRecipe:
    """Kiểm tra full_messaging_recipe — tên, mô tả, 3 hội thoại, 5 tin nhắn, thông báo, Redis."""

    def test_full_recipe_name(self):
        """Kiểm tra tên recipe chứa 'messaging' hoặc 'full'."""
        output = full_messaging_recipe()
        name_lower = output.name.lower()
        assert "messaging" in name_lower or "full" in name_lower

    def test_full_recipe_description(self):
        """Kiểm tra mô tả recipe không rỗng."""
        output = full_messaging_recipe()
        assert output.description
        assert len(output.description.strip()) > 0

    def test_full_recipe_has_three_conversations(self):
        """Kiểm tra recipe có đúng 3 hội thoại."""
        output = full_messaging_recipe()
        assert len(output.ir.conversations) == 3

    def test_full_recipe_conversation_types(self):
        """Kiểm tra recipe có đủ 3 loại hội thoại: direct, group, support."""
        from midicoder.packs.cp_full_chat.models import ConversationType
        output = full_messaging_recipe()
        types = {c.conversation_type for c in output.ir.conversations}
        assert ConversationType.DIRECT in types
        assert ConversationType.GROUP in types
        assert ConversationType.SUPPORT in types

    def test_full_recipe_has_five_messages(self):
        """Kiểm tra recipe có đúng 5 tin nhắn."""
        output = full_messaging_recipe()
        assert len(output.ir.messages) == 5

    def test_full_recipe_has_three_notifications(self):
        """Kiểm tra recipe có đúng 3 thông báo."""
        output = full_messaging_recipe()
        assert len(output.ir.notifications) == 3

    def test_full_recipe_has_redis_url(self):
        """Kiểm tra recipe có URL Redis hợp lệ."""
        output = full_messaging_recipe()
        assert output.ir.redis_url
        assert output.ir.redis_url == "redis://localhost:6379/0"

    def test_full_recipe_websocket_enabled(self):
        """Kiểm tra WebSocket được bật."""
        output = full_messaging_recipe()
        assert output.ir.use_websocket is True

    def test_full_recipe_notification_types(self):
        """Kiểm tra thông báo có đủ các loại: new_message, mention, reply."""
        from midicoder.packs.cp_full_chat.models import NotificationType
        output = full_messaging_recipe()
        types = {n.notification_type for n in output.ir.notifications}
        assert NotificationType.NEW_MESSAGE in types
        assert NotificationType.MENTION in types
        assert NotificationType.REPLY in types

    def test_full_recipe_notifications_not_read(self):
        """Kiểm tra có ít nhất một thông báo chưa được đọc."""
        output = full_messaging_recipe()
        assert any(not n.is_read for n in output.ir.notifications)

    def test_full_recipe_conversations_have_valid_ids(self):
        """Kiểm tra hội thoại có ID hợp lệ (không rỗng)."""
        output = full_messaging_recipe()
        for conv in output.ir.conversations:
            assert conv.conversation_id
            assert len(conv.conversation_id.strip()) > 0

    def test_full_recipe_messages_have_valid_ids(self):
        """Kiểm tra tin nhắn có ID hợp lệ (không rỗng)."""
        output = full_messaging_recipe()
        for msg in output.ir.messages:
            assert msg.message_id
            assert len(msg.message_id.strip()) > 0

    def test_full_recipe_messages_reference_conversations(self):
        """Kiểm tra tin nhắn tham chiếu đến hội thoại hợp lệ."""
        output = full_messaging_recipe()
        conv_ids = {c.conversation_id for c in output.ir.conversations}
        for msg in output.ir.messages:
            assert msg.conversation_id in conv_ids

    def test_full_recipe_messages_have_senders(self):
        """Kiểm tra tin nhắn có người gửi hợp lệ."""
        output = full_messaging_recipe()
        for msg in output.ir.messages:
            assert msg.sender_id
            assert len(msg.sender_id.strip()) > 0

    def test_full_recipe_notifications_reference_conversations(self):
        """Kiểm tra thông báo tham chiếu đến hội thoại hợp lệ."""
        output = full_messaging_recipe()
        conv_ids = {c.conversation_id for c in output.ir.conversations}
        for notif in output.ir.notifications:
            assert notif.conversation_id in conv_ids

    def test_full_recipe_notifications_reference_messages(self):
        """Kiểm tra thông báo tham chiếu đến tin nhắn hợp lệ."""
        output = full_messaging_recipe()
        msg_ids = {m.message_id for m in output.ir.messages}
        for notif in output.ir.notifications:
            if notif.message_id is not None:
                assert notif.message_id in msg_ids

    def test_full_recipe_notifications_have_target_users(self):
        """Kiểm tra thông báo có người dùng mục tiêu hợp lệ."""
        output = full_messaging_recipe()
        for notif in output.ir.notifications:
            assert notif.target_user_id
            assert len(notif.target_user_id.strip()) > 0

    def test_full_recipe_conversations_are_active(self):
        """Kiểm tra tất cả hội thoại đều đang hoạt động."""
        output = full_messaging_recipe()
        for conv in output.ir.conversations:
            assert conv.is_active is True

    def test_full_recipe_messages_have_types(self):
        """Kiểm tra tin nhắn có loại tin nhắn hợp lệ."""
        from midicoder.packs.cp_full_chat.models import MessageType
        output = full_messaging_recipe()
        for msg in output.ir.messages:
            assert msg.message_type in MessageType

    def test_full_recipe_messages_status(self):
        """Kiểm tra tin nhắn có trạng thái hợp lệ."""
        from midicoder.packs.cp_full_chat.models import MessageStatus
        output = full_messaging_recipe()
        for msg in output.ir.messages:
            assert msg.status in MessageStatus


# ===========================================================================
# Test to_dict roundtrip cho recipes
# ===========================================================================


class TestRecipeToDict:
    """Kiểm tra to_dict và from_dict roundtrip cho các recipe."""

    def test_basic_recipe_to_dict(self):
        """Kiểm tra basic_chat_recipe chuyển thành dict chứa hội thoại và tin nhắn."""
        output = basic_chat_recipe()
        d = output.ir.to_dict()
        assert "conversations" in d
        assert "messages" in d
        assert "notifications" in d
        assert len(d["conversations"]) == 2
        assert len(d["messages"]) == 3
        assert len(d["notifications"]) == 0
        assert d["redis_url"] == ""
        assert d["use_websocket"] is True

    def test_basic_recipe_to_dict_from_dict_roundtrip(self):
        """Kiểm tra basic_chat_recipe roundtrip qua to_dict/from_dict giữ nguyên dữ liệu."""
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = basic_chat_recipe()
        d = output.ir.to_dict()
        restored = ChatIR.from_dict(d)
        assert len(restored.conversations) == 2
        assert len(restored.messages) == 3
        assert restored.conversations[0].conversation_id == "conv_direct_001"
        assert restored.conversations[1].conversation_id == "conv_group_001"
        assert restored.messages[0].message_id == "msg_001"
        assert restored.redis_url == ""
        assert restored.use_websocket is True

    def test_full_recipe_to_dict(self):
        """Kiểm tra full_messaging_recipe chuyển thành dict đầy đủ."""
        output = full_messaging_recipe()
        d = output.ir.to_dict()
        assert "conversations" in d
        assert "messages" in d
        assert "notifications" in d
        assert len(d["conversations"]) == 3
        assert len(d["messages"]) == 5
        assert len(d["notifications"]) == 3
        assert d["redis_url"] == "redis://localhost:6379/0"
        assert d["use_websocket"] is True

    def test_full_recipe_to_dict_from_dict_roundtrip(self):
        """Kiểm tra full_messaging_recipe roundtrip qua to_dict/from_dict giữ nguyên dữ liệu."""
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = full_messaging_recipe()
        d = output.ir.to_dict()
        restored = ChatIR.from_dict(d)
        assert len(restored.conversations) == 3
        assert len(restored.messages) == 5
        assert len(restored.notifications) == 3
        assert restored.redis_url == "redis://localhost:6379/0"
        assert restored.use_websocket is True

    def test_full_recipe_roundtrip_preserves_conversations(self):
        """Kiểm tra roundtrip giữ nguyên ID và loại của hội thoại."""
        from midicoder.packs.cp_full_chat.models import ConversationType
        from midicoder.packs.cp_full_chat.parser import ChatIR
        output = full_messaging_recipe()
        d = output.ir.to_dict()
        restored = ChatIR.from_dict(d)
        conv_ids = {c.conversation_id for c in restored.conversations}
        assert "conv_direct_002" in conv_ids
        assert "conv_group_002" in conv_ids
        assert "conv_support_001" in conv_ids
        conv_types = {c.conversation_id: c.conversation_type for c in restored.conversations}
        assert conv_types["conv_direct_002"] == ConversationType.DIRECT
        assert conv_types["conv_group_002"] == ConversationType.GROUP
        assert conv_types["conv_support_001"] == ConversationType.SUPPORT
