# coding: utf-8
"""
React Emitter cho CP41: Chat & Messaging (Frontend).

Module này render Jinja2 templates để sinh chat & messaging infrastructure
cho React stack, bao gồm:
- ChatWindow.tsx: Component chính hiển thị cửa sổ hội thoại
- ConversationList.tsx: Danh sách các cuộc hội thoại
- NotificationBell.tsx: Bell icon với badge thông báo
- useChat.ts: Custom hook để quản lý trạng thái chat
- useNotifications.ts: Custom hook để quản lý thông báo
- chatService.ts: Service layer cho API chat

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_chat.parser import ChatIR
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


__all__ = [
    "ReactChatEmitter",
]


class ReactChatEmitter:
    """Emitter cho React stack — CP41 Chat & Messaging.

    Render templates từ `stacks/react/cp_full_chat/`
    để sinh chat & messaging frontend components.

    Ví dụ:
        >>> emitter = ReactChatEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = ChatIR(conversations=[...], messages=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "ChatWindow.tsx.jinja2": "src/chat/ChatWindow.tsx",
        "ConversationList.tsx.jinja2": "src/chat/ConversationList.tsx",
        "NotificationBell.tsx.jinja2": "src/chat/NotificationBell.tsx",
        "useChat.ts.jinja2": "src/chat/hooks/useChat.ts",
        "useNotifications.ts.jinja2": "src/chat/hooks/useNotifications.ts",
        "chatService.ts.jinja2": "src/chat/services/chatService.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_chat"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.MDC-F19_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: ChatIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit chat & messaging infrastructure cho React.

        Sinh 6 files:
        - ChatWindow.tsx
        - ConversationList.tsx
        - NotificationBell.tsx
        - useChat.ts
        - useNotifications.ts
        - chatService.ts

        Args:
            ir: ChatIR chứa conversations, messages, notifications.
            context: Context bổ sung (optional).

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        conversations_list = [c.to_dict() for c in ir.conversations]
        messages_list = [m.to_dict() for m in ir.messages]
        notification_types = list({n.notification_type for n in ir.notifications})

        template_context: dict[str, Any] = {
            "conversations": conversations_list,
            "messages": messages_list,
            "notifications": [n.to_dict() for n in ir.notifications],
            "notification_types": notification_types,
            "conversation_count": len(ir.conversations),
            "message_count": len(ir.messages),
            "notification_count": len(ir.notifications),
            "redis_url": ir.redis_url,
            "use_redis": bool(ir.redis_url),
            "use_websocket": ir.use_websocket,
            **extra_context,
        }

        result: list[dict[str, str]] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
            if self._template_exists(template_name):
                content = self._render(template_name, template_context)
                result.append({"path": output_path, "content": content})

        return result

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một template.

        Args:
            template_name: Tên template file.
            context: Template context.

        Returns:
            Rendered string.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render lỗi.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F19_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F19_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Render thất bại {template_name}: {e}",
            )
