# coding: utf-8
"""
Mô-đun recipes cho CP45 — Payment Gateway Abstraction.

Cung cấp các recipe để build PaymentIR cho các use case phổ biến:
- basic_payment_recipe: Cấu hình cơ bản (1 gateway, idempotency)
- full_payment_recipe: Cấu hình đầy đủ (3 gateways, refunds, webhooks, audit)

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp45_payment.models import (
    PaymentGatewayConfig,
    PaymentGatewayType,
)
from midicoder.packs.cp45_payment.parser import (
    PaymentIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: PaymentIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: PaymentIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def basic_payment_recipe() -> RecipeOutput:
    """Recipe: Cấu hình payment cơ bản.

    - 1 gateway (Stripe sandbox)
    - Idempotency enabled
    - Currency: VND
    - Không có refund/webhook

    Returns:
        RecipeOutput chứa PaymentIR
    """
    data = {
        "gateways": [
            {
                "config_id": "stripe_sandbox",
                "gateway_type": "stripe",
                "is_sandbox": True,
                "is_enabled": True,
                "timeout_seconds": 30,
            }
        ],
        "default_gateway": "stripe",
        "default_currency": "VND",
        "enable_idempotency": True,
        "enable_refunds": False,
        "enable_webhooks": False,
        "enable_audit": True,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="basic_payment_recipe",
        description="Payment gateway cơ bản — Stripe sandbox, idempotency",
        ir=ir,
        raw_data=data,
    )


def full_payment_recipe() -> RecipeOutput:
    """Recipe: Cấu hình payment đầy đủ.

    - 3 gateways (Stripe, VNPay, MoMo)
    - Idempotency enabled
    - Refunds enabled (max 100%)
    - Webhooks enabled
    - Audit trail enabled
    - Currency: VND

    Returns:
        RecipeOutput chứa PaymentIR
    """
    data = {
        "gateways": [
            {
                "config_id": "stripe_sandbox",
                "gateway_type": "stripe",
                "is_sandbox": True,
                "is_enabled": True,
                "timeout_seconds": 30,
            },
            {
                "config_id": "vnpay_sandbox",
                "gateway_type": "vnpay",
                "is_sandbox": True,
                "is_enabled": True,
                "timeout_seconds": 30,
            },
            {
                "config_id": "momo_sandbox",
                "gateway_type": "momo",
                "is_sandbox": True,
                "is_enabled": True,
                "timeout_seconds": 30,
            },
        ],
        "default_gateway": "stripe",
        "default_currency": "VND",
        "enable_idempotency": True,
        "enable_refunds": True,
        "enable_webhooks": True,
        "enable_audit": True,
        "max_refund_percentage": 100,
        "idempotency_ttl_seconds": 3600,
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_payment_recipe",
        description="Payment gateway đầy đủ — 3 providers, refunds, webhooks, audit",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "basic_payment_recipe",
    "full_payment_recipe",
]
