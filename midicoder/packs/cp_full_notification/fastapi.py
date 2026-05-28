# coding: utf-8
"""
FastAPI Emitter cho CP12: Notification & Communication.

Module này render Jinja2 templates để sinh notification code
cho FastAPI stack, bao gồm notification service, email service,
webhook service, và delivery tracker.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_notification.models import (
    NotificationProvider,
    NotificationTemplate,
    WebhookConfig,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPINotificationEmitter",
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


class FastAPINotificationEmitter:
    """Emitter cho FastAPI stack — CP12 Notification & Communication.

    Render templates từ `stacks/fastapi/cp_full_notification/`
    để sinh notification service code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_notification"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-F06_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
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
        ir: dict[str, Any],
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit notification code cho FastAPI.

        Sinh 4 files:
        - notification_service.py
        - email_service.py
        - webhook_service.py
        - delivery_tracker.py

        Args:
            ir: Dictionary chứa keys: "notifications", "providers",
                "channels", "webhooks".
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("notification_service.py.jinja2", "app/services/notification_service.py"),
            ("email_service.py.jinja2", "app/services/email_service.py"),
            ("webhook_service.py.jinja2", "app/services/webhook_service.py"),
            ("delivery_tracker.py.jinja2", "app/services/delivery_tracker.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: dict[str, Any]) -> dict[str, Any]:
        """Xây dựng template context từ raw IR dictionary.

        Args:
            ir: Dictionary với keys "notifications", "providers",
                "channels", "webhooks".

        Returns:
            Dictionary context cho Jinja2 template.
        """
        notifications: list[NotificationTemplate] = ir.get("notifications", [])
        providers: list[NotificationProvider] = ir.get("providers", [])
        channels: dict[str, Any] = ir.get("channels", {})
        webhooks: list[WebhookConfig] = ir.get("webhooks", [])

        templates_list = [t.to_dict() if isinstance(t, NotificationTemplate) else t for t in notifications]
        providers_list = [p.to_dict() if isinstance(p, NotificationProvider) else p for p in providers]
        webhooks_list = [w.to_dict() if isinstance(w, WebhookConfig) else w for w in webhooks]

        return {
            "templates": templates_list,
            "providers": providers_list,
            "webhooks": webhooks_list,
            "channels": channels,
            "template_count": len(templates_list),
            "provider_count": len(providers_list),
            "webhook_count": len(webhooks_list),
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template file có tồn tại không."""
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một Jinja2 template với context.

        Args:
            template_name: Tên file template (.jinja2).
            context: Dictionary context cho template.

        Returns:
            Nội dung template sau khi render.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render thất bại.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F06_NOTIFICATION_TEMPLATE_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F06_NOTIFICATION_TEMPLATE_RENDER_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
