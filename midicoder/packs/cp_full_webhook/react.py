# coding: utf-8
"""
React Emitter cho CP40: Webhook & Outbound Integration Hub (Frontend).

Module này render Jinja2 templates để sinh webhook dashboard infrastructure
cho React stack, bao gồm:
- WebhookDashboard.tsx: Component chính hiển thị danh sách webhook
- WebhookSubscriptionList.tsx: List subscriptions + CRUD
- useWebhooks.ts: Custom hook để quản lý webhook subscriptions
- useDispatchStatus.ts: Custom hook để theo dõi status delivery

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
    "ReactWebhookEmitter",
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


class ReactWebhookEmitter:
    """Emitter cho React stack — CP40 Webhook Dashboard.

    Render templates từ `stacks/react/cp_full_webhook/`
    để sinh webhook dashboard infrastructure components.

    Ví dụ:
        >>> emitter = ReactWebhookEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = WebhookIR(subscriptions=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "WebhookDashboard.tsx.jinja2": "src/webhook/components/WebhookDashboard.tsx",
        "WebhookSubscriptionList.tsx.jinja2": "src/webhook/components/WebhookSubscriptionList.tsx",
        "useWebhooks.ts.jinja2": "src/webhook/hooks/useWebhooks.ts",
        "useDispatchStatus.ts.jinja2": "src/webhook/hooks/useDispatchStatus.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/`.

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

    def emit(self, ir: WebhookIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit webhook dashboard infrastructure cho React.

        Sinh 4 files:
        - WebhookDashboard.tsx
        - WebhookSubscriptionList.tsx
        - useWebhooks.ts
        - useDispatchStatus.ts

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
                ErrorCode.MDC-F17_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F17_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=f"Render thất bại {template_name}: {e}",
            )
