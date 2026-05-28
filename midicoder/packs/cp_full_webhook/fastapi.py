# coding: utf-8
"""
FastAPI Emitter cho CP40: Webhook & Outbound Integration Hub.

Module này render Jinja2 templates để sinh webhook outbound code
cho FastAPI stack, bao gồm models, schemas, service, router,
dispatch engine, redis worker, và middleware.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_webhook.parser import WebhookIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIWebhookEmitter",
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


class FastAPIWebhookEmitter:
    """Emitter cho FastAPI stack — CP40 Webhook & Outbound Integration Hub.

    Render templates từ `stacks/fastapi/cp_full_webhook/`
    để sinh webhook outbound code.

    Ví dụ:
        >>> emitter = FastAPIWebhookEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_webhook"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.MDC-F17_WEBHOOK_PAYLOAD_RENDER_FAILED,
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
        ir: WebhookIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit webhook outbound code cho FastAPI.

        Sinh 7 files:
        - webhook_models.py
        - webhook_schemas.py
        - webhook_service.py
        - webhook_router.py
        - webhook_dispatch.py
        - webhook_worker.py
        - webhook_middleware.py

        Args:
            ir: WebhookIR chứa subscriptions, dispatches, redis_url.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        templates = [
            ("webhook_models.py.jinja2", "app/webhook/models.py"),
            ("webhook_schemas.py.jinja2", "app/webhook/schemas.py"),
            ("webhook_service.py.jinja2", "app/webhook/services/webhook_service.py"),
            ("webhook_router.py.jinja2", "app/webhook/routers/webhook_router.py"),
            ("webhook_dispatch.py.jinja2", "app/webhook/services/webhook_dispatch.py"),
            ("webhook_worker.py.jinja2", "app/webhook/workers/webhook_worker.py"),
            ("webhook_middleware.py.jinja2", "app/webhook/middleware.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: WebhookIR) -> dict[str, Any]:
        """Xây dựng template context từ WebhookIR.

        Args:
            ir: WebhookIR input.

        Returns:
            Dict context cho Jinja2.
        """
        subscriptions_list = [sub.to_dict() for sub in ir.subscriptions]

        # Event types unique list
        event_types = list({sub.event_type for sub in ir.subscriptions})

        return {
            "subscriptions": subscriptions_list,
            "subscription_count": len(ir.subscriptions),
            "event_types": event_types,
            "redis_url": ir.redis_url,
            "use_redis": bool(ir.redis_url),
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
                ErrorCode.MDC-F17_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F17_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
