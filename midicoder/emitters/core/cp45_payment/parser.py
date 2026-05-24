# coding: utf-8
"""
Mô-đun parser cho CP45 — Payment Gateway Abstraction.

Parse DSL dict (từ contract YAML) sang PaymentIR — Intermediate Representation
cho payment gateway configurations, payment methods, transaction settings,
và refund policies.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp45_payment.models import (
    PaymentGatewayConfig,
    PaymentGatewayType,
    PaymentMethod,
    PaymentMethodType,
    PaymentRefund,
    PaymentTransaction,
)


@dataclass
class PaymentIR:
    """Intermediate Representation cho CP45.

    Gom tập tất cả cấu hình payment gateway từ DSL, bao gồm
    gateway configs, payment methods, transaction defaults,
    và refund policies.

    Attributes:
        gateways: Danh sách gateway configurations
        payment_methods: Danh sách payment method types được hỗ trợ
        default_gateway: Gateway mặc định
        default_currency: Currency mặc định
        default_amount: Amount mặc định (cho testing)
        enable_idempotency: Có bật idempotency protection không
        enable_refunds: Có bật refund flow không
        enable_webhooks: Có bật webhook handling không
        enable_audit: Có ghi audit trail không
        max_refund_percentage: Phần trăm hoàn tiền tối đa (mặc định: 100)
        idempotency_ttl_seconds: TTL của idempotency key (mặc định: 3600)
    """
    gateways: list[PaymentGatewayConfig] = field(default_factory=list)
    payment_methods: list[PaymentMethod] = field(default_factory=list)
    default_gateway: PaymentGatewayType = PaymentGatewayType.STRIPE
    default_currency: str = "VND"
    default_amount: int = 0
    enable_idempotency: bool = True
    enable_refunds: bool = True
    enable_webhooks: bool = True
    enable_audit: bool = True
    max_refund_percentage: int = 100
    idempotency_ttl_seconds: int = 3600

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentIR sang dict."""
        return {
            "gateways": [g.to_dict() for g in self.gateways],
            "payment_methods": [m.to_dict() for m in self.payment_methods],
            "default_gateway": self.default_gateway.value,
            "default_currency": self.default_currency,
            "default_amount": self.default_amount,
            "enable_idempotency": self.enable_idempotency,
            "enable_refunds": self.enable_refunds,
            "enable_webhooks": self.enable_webhooks,
            "enable_audit": self.enable_audit,
            "max_refund_percentage": self.max_refund_percentage,
            "idempotency_ttl_seconds": self.idempotency_ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentIR":
        """Tạo PaymentIR từ dict."""
        gateways = [PaymentGatewayConfig.from_dict(g) for g in data.get("gateways", [])]
        methods = [PaymentMethod.from_dict(m) for m in data.get("payment_methods", [])]
        return cls(
            gateways=gateways,
            payment_methods=methods,
            default_gateway=PaymentGatewayType(data.get("default_gateway", "stripe")),
            default_currency=data.get("default_currency", "VND"),
            default_amount=data.get("default_amount", 0),
            enable_idempotency=data.get("enable_idempotency", True),
            enable_refunds=data.get("enable_refunds", True),
            enable_webhooks=data.get("enable_webhooks", True),
            enable_audit=data.get("enable_audit", True),
            max_refund_percentage=data.get("max_refund_percentage", 100),
            idempotency_ttl_seconds=data.get("idempotency_ttl_seconds", 3600),
        )


def parse_gateways(data: dict[str, Any]) -> list[PaymentGatewayConfig]:
    """Parse danh sách gateway configurations từ DSL dict.

    Args:
        data: DSL dict với key 'gateways' hoặc 'payment_gateways'

    Returns:
        Danh sách PaymentGatewayConfig
    """
    raw = data.get("gateways", data.get("payment_gateways", []))
    gateways = []
    for gw_data in raw:
        gateways.append(PaymentGatewayConfig(
            config_id=gw_data.get("config_id", gw_data.get("id", "")),
            gateway_type=PaymentGatewayType(gw_data.get("gateway_type", gw_data.get("type", "stripe"))),
            api_key=gw_data.get("api_key", ""),
            api_secret=gw_data.get("api_secret", ""),
            webhook_secret=gw_data.get("webhook_secret", ""),
            endpoint_url=gw_data.get("endpoint_url", ""),
            webhook_url=gw_data.get("webhook_url", ""),
            timeout_seconds=gw_data.get("timeout_seconds", 30),
            is_sandbox=gw_data.get("is_sandbox", gw_data.get("sandbox", True)),
            is_enabled=gw_data.get("is_enabled", gw_data.get("enabled", True)),
            metadata=gw_data.get("metadata", {}),
        ))
    return gateways


def parse_payment_methods(data: dict[str, Any]) -> list[PaymentMethod]:
    """Parse danh sách payment methods từ DSL dict.

    Args:
        data: DSL dict với key 'payment_methods' hoặc 'methods'

    Returns:
        Danh sách PaymentMethod
    """
    raw = data.get("payment_methods", data.get("methods", []))
    methods = []
    for m_data in raw:
        methods.append(PaymentMethod(
            method_id=m_data.get("method_id", m_data.get("id", "")),
            user_id=m_data.get("user_id", ""),
            method_type=PaymentMethodType(m_data.get("method_type", m_data.get("type", "credit_card"))),
            gateway_type=PaymentGatewayType(m_data.get("gateway_type", "stripe")),
            display_name=m_data.get("display_name", ""),
            last4=m_data.get("last4", ""),
            token=m_data.get("token", ""),
            is_default=m_data.get("is_default", False),
            tenant_id=m_data.get("tenant_id", ""),
            metadata=m_data.get("metadata", {}),
        ))
    return methods


def parse_payment_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse cấu hình payment defaults từ DSL dict.

    Args:
        data: DSL dict với các config keys

    Returns:
        Dict chứa default_gateway, default_currency, enable_idempotency,
        enable_refunds, enable_webhooks, enable_audit,
        max_refund_percentage, idempotency_ttl_seconds
    """
    return {
        "default_gateway": data.get("default_gateway", data.get("gateway", "stripe")),
        "default_currency": data.get("default_currency", "VND"),
        "enable_idempotency": data.get("enable_idempotency", True),
        "enable_refunds": data.get("enable_refunds", True),
        "enable_webhooks": data.get("enable_webhooks", True),
        "enable_audit": data.get("enable_audit", True),
        "max_refund_percentage": data.get("max_refund_percentage", 100),
        "idempotency_ttl_seconds": data.get("idempotency_ttl_seconds", 3600),
    }


def parse_to_ir(data: dict[str, Any]) -> PaymentIR:
    """Parse DSL dict thành PaymentIR.

    Args:
        data: DSL dict với gateways, payment_methods, config

    Returns:
        PaymentIR gom tập tất cả parsed data
    """
    gateways = parse_gateways(data)
    methods = parse_payment_methods(data)
    config = parse_payment_config(data)

    return PaymentIR(
        gateways=gateways,
        payment_methods=methods,
        default_gateway=PaymentGatewayType(config["default_gateway"]),
        default_currency=config["default_currency"],
        enable_idempotency=config["enable_idempotency"],
        enable_refunds=config["enable_refunds"],
        enable_webhooks=config["enable_webhooks"],
        enable_audit=config["enable_audit"],
        max_refund_percentage=config["max_refund_percentage"],
        idempotency_ttl_seconds=config["idempotency_ttl_seconds"],
    )


__all__ = [
    "PaymentIR",
    "parse_gateways",
    "parse_payment_methods",
    "parse_payment_config",
    "parse_to_ir",
]
