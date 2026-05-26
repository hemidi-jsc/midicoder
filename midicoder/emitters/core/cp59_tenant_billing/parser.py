# coding: utf-8
"""
Mô-đun parser cho CP59 — Tenant Billing & Invoicing.

Parse DSL dict (từ contract YAML) sang BillingIR — Intermediate Representation
cho billing plans, billing cycles, invoice configs, usage meters,
và payment gateway configurations.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp59_tenant_billing.models import (
    BillingCycle,
    BillingPlan,
    InvoiceConfig,
    PaymentGatewayConfig,
    UsageMeter,
)


@dataclass
class BillingIR:
    """Intermediate Representation cho CP59.

    Gom tập tất cả cấu hình billing từ DSL, bao gồm
    billing plans, billing cycles, invoice configs, usage meters,
    và payment gateway configs.

    Attributes:
        plans: Danh sách billing plans
        cycles: Danh sách billing cycles
        invoice_configs: Danh sách invoice configurations
        meters: Danh sách usage meters
        gateways: Danh sách payment gateway configs
    """
    plans: list[BillingPlan] = field(default_factory=list)
    cycles: list[BillingCycle] = field(default_factory=list)
    invoice_configs: list[InvoiceConfig] = field(default_factory=list)
    meters: list[UsageMeter] = field(default_factory=list)
    gateways: list[PaymentGatewayConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BillingIR sang dict."""
        return {
            "plans": [p.to_dict() for p in self.plans],
            "cycles": [c.to_dict() for c in self.cycles],
            "invoice_configs": [i.to_dict() for i in self.invoice_configs],
            "meters": [m.to_dict() for m in self.meters],
            "gateways": [g.to_dict() for g in self.gateways],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BillingIR":
        """Tạo BillingIR từ dict."""
        plans = [BillingPlan.from_dict(p) for p in data.get("plans", [])]
        cycles = [BillingCycle.from_dict(c) for c in data.get("cycles", [])]
        invoices = [InvoiceConfig.from_dict(i) for i in data.get("invoice_configs", [])]
        meters = [UsageMeter.from_dict(m) for m in data.get("meters", [])]
        gateways = [PaymentGatewayConfig.from_dict(g) for g in data.get("gateways", [])]
        return cls(
            plans=plans,
            cycles=cycles,
            invoice_configs=invoices,
            meters=meters,
            gateways=gateways,
        )


def parse_plans(data: dict[str, Any]) -> list[BillingPlan]:
    """Parse danh sách billing plans từ DSL dict.

    Args:
        data: DSL dict với key 'plans' hoặc 'billing_plans'

    Returns:
        Danh sách BillingPlan
    """
    raw = data.get("plans", data.get("billing_plans", []))
    plans = []
    for p_data in raw:
        plans.append(BillingPlan(
            id=p_data.get("id", ""),
            name=p_data.get("name", ""),
            tier=p_data.get("tier", "free"),
            monthly_price=p_data.get("monthly_price", 0),
            annual_price=p_data.get("annual_price", 0),
            features=p_data.get("features", []),
            usage_limits=p_data.get("usage_limits", {}),
        ))
    return plans


def parse_cycles(data: dict[str, Any]) -> list[BillingCycle]:
    """Parse danh sách billing cycles từ DSL dict.

    Args:
        data: DSL dict với key 'cycles' hoặc 'billing_cycles'

    Returns:
        Danh sách BillingCycle
    """
    raw = data.get("cycles", data.get("billing_cycles", []))
    cycles = []
    for c_data in raw:
        cycles.append(BillingCycle.from_dict(c_data))
    return cycles


def parse_invoice_configs(data: dict[str, Any]) -> list[InvoiceConfig]:
    """Parse danh sách invoice configs từ DSL dict.

    Args:
        data: DSL dict với key 'invoice_configs' hoặc 'invoices'

    Returns:
        Danh sách InvoiceConfig
    """
    raw = data.get("invoice_configs", data.get("invoices", []))
    invoices = []
    for i_data in raw:
        invoices.append(InvoiceConfig.from_dict(i_data))
    return invoices


def parse_meters(data: dict[str, Any]) -> list[UsageMeter]:
    """Parse danh sách usage meters từ DSL dict.

    Args:
        data: DSL dict với key 'meters' hoặc 'usage_meters'

    Returns:
        Danh sách UsageMeter
    """
    raw = data.get("meters", data.get("usage_meters", []))
    meters = []
    for m_data in raw:
        meters.append(UsageMeter.from_dict(m_data))
    return meters


def parse_gateways(data: dict[str, Any]) -> list[PaymentGatewayConfig]:
    """Parse danh sách payment gateway configs từ DSL dict.

    Args:
        data: DSL dict với key 'gateways' hoặc 'payment_gateways'

    Returns:
        Danh sách PaymentGatewayConfig
    """
    raw = data.get("gateways", data.get("payment_gateways", []))
    gateways = []
    for g_data in raw:
        gateways.append(PaymentGatewayConfig.from_dict(g_data))
    return gateways


def parse_to_ir(data: dict[str, Any]) -> BillingIR:
    """Parse DSL dict thành BillingIR.

    Args:
        data: DSL dict với plans, cycles, invoice_configs, meters, gateways

    Returns:
        BillingIR gom tập tất cả parsed data
    """
    plans = parse_plans(data)
    cycles = parse_cycles(data)
    invoices = parse_invoice_configs(data)
    meters = parse_meters(data)
    gateways = parse_gateways(data)

    return BillingIR(
        plans=plans,
        cycles=cycles,
        invoice_configs=invoices,
        meters=meters,
        gateways=gateways,
    )


__all__ = [
    "BillingIR",
    "parse_plans",
    "parse_cycles",
    "parse_invoice_configs",
    "parse_meters",
    "parse_gateways",
    "parse_to_ir",
]
