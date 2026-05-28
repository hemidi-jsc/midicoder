# coding: utf-8
"""
FastAPI Emitter cho CP45: Payment Gateway Abstraction.

Module này render Jinja2 templates để sinh payment gateway code
cho FastAPI stack, bao gồm models, schemas, service, router,
webhook handler, và event emitter.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_payment.parser import PaymentIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIPaymentEmitter",
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


class FastAPIPaymentEmitter:
    """Emitter cho FastAPI stack — CP45 Payment Gateway Abstraction.

    Render templates từ `stacks/fastapi/cp_full_payment/`
    để sinh payment gateway code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_payment"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_GATEWAY_NOT_FOUND,
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
        ir: PaymentIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit payment gateway code cho FastAPI.

        Sinh 6 files:
        - payment_models.py
        - payment_schemas.py
        - payment_service.py
        - payment_router.py
        - payment_webhook.py
        - payment_events.py

        Args:
            ir: PaymentIR chứa gateway configs và payment settings.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("payment_models.py.jinja2", "app/models/payment_models.py"),
            ("payment_schemas.py.jinja2", "app/schemas/payment_schemas.py"),
            ("payment_service.py.jinja2", "app/services/payment_service.py"),
            ("payment_router.py.jinja2", "app/api/payment_router.py"),
            ("payment_webhook.py.jinja2", "app/api/payment_webhook.py"),
            ("payment_events.py.jinja2", "app/services/payment_events.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: PaymentIR) -> dict[str, Any]:
        """Xây dựng template context từ PaymentIR."""
        gateways_list = [g.to_dict() for g in ir.gateways]
        methods_list = [m.to_dict() for m in ir.payment_methods]
        return {
            "gateways": gateways_list,
            "payment_methods": methods_list,
            "gateway_count": len(ir.gateways),
            "method_count": len(ir.payment_methods),
            "default_gateway": ir.default_gateway.value,
            "default_currency": ir.default_currency,
            "enable_idempotency": ir.enable_idempotency,
            "enable_refunds": ir.enable_refunds,
            "enable_webhooks": ir.enable_webhooks,
            "enable_audit": ir.enable_audit,
            "max_refund_percentage": ir.max_refund_percentage,
            "idempotency_ttl_seconds": ir.idempotency_ttl_seconds,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_GATEWAY_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_PROCESSING_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
