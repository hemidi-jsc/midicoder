# coding: utf-8
"""
React Emitter cho CP45: Payment Gateway Abstraction.

Module này render Jinja2 templates để sinh payment gateway code
cho React stack, bao gồm dashboard, payment methods, payment history,
progress indicator, custom hook, và context provider.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp45_payment.parser import PaymentIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "ReactPaymentEmitter",
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


class ReactPaymentEmitter:
    """Emitter cho React stack — CP45 Payment Gateway Abstraction.

    Render templates từ `stacks/react/cp45_payment/`
    để sinh payment gateway frontend code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp45_payment"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP45_PAYMENT_GATEWAY_NOT_FOUND,
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
        """Emit payment gateway code cho React.

        Sinh 6 files:
        - PaymentDashboard.tsx
        - PaymentMethods.tsx
        - PaymentHistory.tsx
        - PaymentProgress.tsx
        - usePayment.ts
        - PaymentProvider.tsx

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
            ("PaymentDashboard.tsx.jinja2", "src/payment/PaymentDashboard.tsx"),
            ("PaymentMethods.tsx.jinja2", "src/payment/PaymentMethods.tsx"),
            ("PaymentHistory.tsx.jinja2", "src/payment/PaymentHistory.tsx"),
            ("PaymentProgress.tsx.jinja2", "src/payment/PaymentProgress.tsx"),
            ("usePayment.ts.jinja2", "src/payment/hooks/usePayment.ts"),
            ("PaymentProvider.tsx.jinja2", "src/payment/PaymentProvider.tsx"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: PaymentIR) -> dict[str, Any]:
        """Xây dựng template context từ PaymentIR."""
        return {
            "default_gateway": ir.default_gateway.value,
            "default_currency": ir.default_currency,
            "enable_refunds": ir.enable_refunds,
            "gateway_types": ["stripe", "vnpay", "momo"],
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP45_PAYMENT_GATEWAY_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP45_PAYMENT_PROCESSING_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
