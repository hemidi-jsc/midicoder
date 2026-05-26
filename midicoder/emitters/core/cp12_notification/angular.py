# coding: utf-8
"""
Angular Emitter cho CP12: Notification & Communication.

Module này render Jinja2 templates để sinh notification code
cho Angular stack, bao gồm notification toast component,
HTTP service, và type definitions.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularNotificationEmitter",
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


class AngularNotificationEmitter:
    """Emitter cho Angular stack — CP12 Notification & Communication.

    Render templates từ `stacks/angular/core/cp12_notification/`
    để sinh notification frontend code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp12_notification"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND,
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
        """Emit notification code cho Angular.

        Sinh 3 files:
        - notification-toast.component.ts
        - notification.service.ts
        - types.ts

        Args:
            ir: Raw dict chứa keys: "notifications", "providers",
                "channels", "webhooks".
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("notification-toast.component.ts.jinja2", "src/app/shared/notification/notification-toast.component.ts"),
            ("notification.service.ts.jinja2", "src/app/shared/notification/notification.service.ts"),
            ("types.ts.jinja2", "src/app/shared/notification/types.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: dict[str, Any]) -> dict[str, Any]:
        """Xây dựng template context từ raw dict IR."""
        return {
            "notifications": ir.get("notifications", []),
            "providers": ir.get("providers", []),
            "channels": ir.get("channels", {}),
            "webhooks": ir.get("webhooks", []),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_RENDER_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
