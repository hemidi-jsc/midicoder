# coding: utf-8
"""
CP41 — Chat & Messaging Pack.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp41_chat.models import (
    ChatManager,
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
from midicoder.packs.cp41_chat.parser import (
    ChatIR,
    parse_conversations,
    parse_messages,
    parse_notifications,
    parse_to_ir,
)
from midicoder.packs.cp41_chat.recipes import (
    RecipeOutput,
    basic_chat_recipe,
    full_messaging_recipe,
)
from midicoder.packs.cp41_chat.fastapi import (
    FastAPIChatEmitter,
)
from midicoder.packs.cp41_chat.nestjs import (
    NestJSChatEmitter,
)
from midicoder.packs.cp41_chat.angular import (
    AngularChatEmitter,
)
from midicoder.packs.cp41_chat.react import (
    ReactChatEmitter,
)

__all__ = [
    # Models - Enums
    "MessageType",
    "MessageStatus",
    "ConversationType",
    "NotificationType",
    "ReadReceiptType",
    # Models - Core
    "Conversation",
    "ChatMessage",
    "ConversationParticipant",
    "ReadReceipt",
    "Notification",
    # Models - Engine
    "ChatManager",
    # Parser
    "ChatIR",
    "parse_conversations",
    "parse_messages",
    "parse_notifications",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_chat_recipe",
    "full_messaging_recipe",
    # Emitters
    "FastAPIChatEmitter",
    "NestJSChatEmitter",
    "AngularChatEmitter",
    "ReactChatEmitter",
]
