# coding: utf-8
"""
Angular Emitter cho CP40: Webhook & Outbound Integration Hub (Frontend).

Module này render Jinja2 templates để sinh webhook dashboard infrastructure
cho Angular stack, bao gồm:
- webhook-dashboard.component.ts: Component chính hiển thị danh sách webhook
- webhook-subscription-list.component.ts: List subscriptions + CRUD
- webhook-delivery-viewer.component.ts: Xem lịch sử delivery
- webhook.service.ts: Injectable service gọi API

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp40_webhook.parser import WebhookIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularWebhookEmitter",
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


class AngularWebhookEmitter:
    """Emitter cho Angular stack — CP40 Webhook Dashboard.

    Render templates từ `stacks/angular/cp40_webhook/`
    để sinh webhook dashboard infrastructure cho Angular.

    Ví dụ:
        >>> emitter = AngularWebhookEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = WebhookIR(subscriptions=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "webhook-dashboard.component.ts.jinja2": "src/app/webhook/webhook-dashboard.component.ts",
        "webhook-subscription-list.component.ts.jinja2": "src/app/webhook/webhook-subscription-list.component.ts",
        "webhook-delivery-viewer.component.ts.jinja2": "src/app/webhook/webhook-delivery-viewer.component.ts",
        "webhook.service.ts.jinja2": "src/app/core/webhook/webhook.service.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp40_webhook"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: WebhookIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit webhook dashboard infrastructure cho Angular.

        Sinh 4 files:
        - webhook-dashboard.component.ts
        - webhook-subscription-list.component.ts
        - webhook-delivery-viewer.component.ts
        - webhook.service.ts

        Args:
            ir: WebhookIR chứa subscriptions, dispatches.
            context: Context bổ sung (optional).

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        subscriptions_list = [sub.to_dict() for sub in ir.subscriptions]
        event_types = list({sub.event_type for sub in ir.subscriptions})

        template_context: dict[str, Any] = {
            "subscriptions": subscriptions_list,
            "subscription_count": len(ir.subscriptions),
            "event_types": event_types,
            "redis_url": ir.redis_url,
            "use_redis": bool(ir.redis_url),
            **extra_context,
        }

        result: list[dict[str, str]] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
            if self._template_exists(template_name):
                content = self._render(template_name, template_context)
                result.append({"path": output_path, "content": content})

        return result

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP40_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP40_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Render thất bại {template_name}: {e}",
            )
