# coding: utf-8
"""
NestJS Emitter cho CP41: Chat & Messaging.

Module này render Jinja2 templates để sinh chat/messaging code
cho NestJS stack, bao gồm entity, DTO, service, controller,
WebSocket gateway, module, và queue service.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp41_chat.parser import ChatIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSChatEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class NestJSChatEmitter:
    """Emitter cho NestJS stack — CP41 Chat & Messaging.

    Render templates từ `stacks/nestjs/cp41_chat/`
    để sinh chat & messaging code.

    Ví dụ:
        >>> emitter = NestJSChatEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp41_chat"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP41_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: ChatIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit chat & messaging code cho NestJS.

        Sinh 7 files:
        - chat.entity.ts
        - chat.dto.ts
        - chat.service.ts
        - chat.controller.ts
        - chat.gateway.ts
        - chat.module.ts
        - chat-queue.service.ts

        Args:
            ir: ChatIR chứa conversations, messages, notifications.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        templates = [
            ("chat.entity.ts.jinja2", "src/chat/chat.entity.ts"),
            ("chat.dto.ts.jinja2", "src/chat/chat.dto.ts"),
            ("chat.service.ts.jinja2", "src/chat/chat.service.ts"),
            ("chat.controller.ts.jinja2", "src/chat/chat.controller.ts"),
            ("chat.gateway.ts.jinja2", "src/chat/chat.gateway.ts"),
            ("chat.module.ts.jinja2", "src/chat/chat.module.ts"),
            ("chat-queue.service.ts.jinja2", "src/chat/chat-queue.service.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: ChatIR) -> dict[str, Any]:
        """Xây dựng template context từ ChatIR.

        Args:
            ir: ChatIR input.

        Returns:
            Dict context cho Jinja2.
        """
        conversations_list = [c.to_dict() for c in ir.conversations]
        messages_list = [m.to_dict() for m in ir.messages]

        # Notification types unique list
        notification_types = list({n.notification_type for n in ir.notifications})

        return {
            "conversations": conversations_list,
            "conversations_list": conversations_list,
            "messages": messages_list,
            "messages_list": messages_list,
            "notifications": [n.to_dict() for n in ir.notifications],
            "notification_types": notification_types,
            "conversation_count": len(ir.conversations),
            "message_count": len(ir.messages),
            "notification_count": len(ir.notifications),
            "redis_url": ir.redis_url,
            "use_redis": bool(ir.redis_url),
            "use_websocket": ir.use_websocket,
        }

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
                ErrorCode.CP41_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP41_CHAT_WEBSOCKET_CONNECTION_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
