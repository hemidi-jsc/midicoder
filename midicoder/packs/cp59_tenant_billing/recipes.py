# coding: utf-8
"""
Mô-đun recipes cho CP59 — Tenant Billing & Invoicing.

Cung cấp các recipe để build BillingIR cho các use case phổ biến:
- saas_billing_recipe: SaaS subscription với Stripe
- usage_based_billing_recipe: Metered usage billing
- multi_tier_billing_recipe: Free → Starter → Pro tiers
- invoice_generation_recipe: Automated invoice generation

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp59_tenant_billing.parser import (
    BillingIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: BillingIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: BillingIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def saas_billing_recipe() -> RecipeOutput:
    """Recipe: SaaS subscription billing với Stripe.

    Cấu hình billing cho mô hình SaaS subscription tiêu chuẩn:
    - 4 billing plans (Free, Starter, Professional, Enterprise)
    - Billing cycle hàng tháng và hàng năm
    - Stripe payment gateway với webhook
    - Usage meters cho API calls và storage

    Returns:
        RecipeOutput chứa BillingIR
    """
    data = {
        "plans": [
            {
                "id": "plan_free",
                "name": "Free Plan",
                "tier": "free",
                "monthly_price": 0,
                "annual_price": 0,
                "features": ["1 project", "1 GB storage", "Community support"],
                "usage_limits": {"api_calls": 1000, "storage_gb": 1, "users": 1},
            },
            {
                "id": "plan_starter",
                "name": "Starter Plan",
                "tier": "starter",
                "monthly_price": 2900,
                "annual_price": 29000,
                "features": [
                    "5 projects",
                    "10 GB storage",
                    "Email support",
                    "Basic analytics",
                ],
                "usage_limits": {"api_calls": 50000, "storage_gb": 10, "users": 5},
            },
            {
                "id": "plan_professional",
                "name": "Professional Plan",
                "tier": "professional",
                "monthly_price": 9900,
                "annual_price": 99000,
                "features": [
                    "Unlimited projects",
                    "100 GB storage",
                    "Priority support",
                    "Advanced analytics",
                    "API access",
                    "Custom integrations",
                ],
                "usage_limits": {"api_calls": 500000, "storage_gb": 100, "users": 25},
            },
            {
                "id": "plan_enterprise",
                "name": "Enterprise Plan",
                "tier": "enterprise",
                "monthly_price": 29900,
                "annual_price": 299000,
                "features": [
                    "Everything in Professional",
                    "Unlimited storage",
                    "Dedicated support",
                    "SLA guarantee",
                    "SSO/SAML",
                    "Audit logs",
                    "Custom contracts",
                ],
                "usage_limits": {"api_calls": -1, "storage_gb": -1, "users": -1},
            },
        ],
        "cycles": [
            {
                "id": "cycle_monthly",
                "type": "monthly",
                "auto_renew": True,
            },
            {
                "id": "cycle_annual",
                "type": "annual",
                "auto_renew": True,
            },
        ],
        "meters": [
            {
                "id": "meter_api_calls",
                "metric_name": "api_calls",
                "unit_price": 0.01,
                "billing_period": "monthly",
                "threshold_alerts": [50, 80, 90, 100],
            },
            {
                "id": "meter_storage_gb",
                "metric_name": "storage_gb",
                "unit_price": 0.10,
                "billing_period": "monthly",
                "threshold_alerts": [75, 90, 100],
            },
        ],
        "gateways": [
            {
                "id": "gw_stripe",
                "provider": "stripe",
                "currencies": ["USD", "EUR", "GBP"],
                "capture_mode": "automatic",
                "is_sandbox": True,
                "is_enabled": True,
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="saas_billing_recipe",
        description="SaaS subscription billing — 4 tiers với Stripe gateway",
        ir=ir,
        raw_data=data,
    )


def usage_based_billing_recipe() -> RecipeOutput:
    """Recipe: Usage-based (metered) billing.

    Cấu hình billing dựa trên lượng sử dụng thực tế:
    - 2 plans cơ bản (Base + Overage)
    - Usage meters cho nhiều metric (API, storage, bandwidth)
    - Stripe payment gateway với manual capture

    Returns:
        RecipeOutput chứa BillingIR
    """
    data = {
        "plans": [
            {
                "id": "plan_base",
                "name": "Base Plan",
                "tier": "starter",
                "monthly_price": 4900,
                "annual_price": 49000,
                "features": ["Base allowance for all metrics"],
                "usage_limits": {
                    "api_calls": 100000,
                    "storage_gb": 50,
                    "bandwidth_gb": 100,
                },
            },
            {
                "id": "plan_overage",
                "name": "Overage Plan",
                "tier": "professional",
                "monthly_price": 0,
                "annual_price": 0,
                "features": ["Pay-as-you-go overage charges"],
                "usage_limits": {},
            },
        ],
        "cycles": [
            {
                "id": "cycle_monthly",
                "type": "monthly",
                "auto_renew": True,
            },
        ],
        "meters": [
            {
                "id": "meter_api_calls",
                "metric_name": "api_calls",
                "unit_price": 10,
                "billing_period": "monthly",
                "threshold_alerts": [80, 90, 100, 120, 150],
            },
            {
                "id": "meter_storage_gb",
                "metric_name": "storage_gb",
                "unit_price": 50,
                "billing_period": "monthly",
                "threshold_alerts": [75, 90, 100],
            },
            {
                "id": "meter_bandwidth_gb",
                "metric_name": "bandwidth_gb",
                "unit_price": 20,
                "billing_period": "monthly",
                "threshold_alerts": [80, 90, 100],
            },
        ],
        "gateways": [
            {
                "id": "gw_stripe",
                "provider": "stripe",
                "currencies": ["USD"],
                "capture_mode": "manual",
                "is_sandbox": True,
                "is_enabled": True,
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="usage_based_billing_recipe",
        description="Usage-based billing — metered charges với nhiều metric",
        ir=ir,
        raw_data=data,
    )


def multi_tier_billing_recipe() -> RecipeOutput:
    """Recipe: Multi-tier billing (Free → Starter → Pro).

    Cấu hình billing với các tier kế tiếp nhau, hỗ trợ upgrade/downgrade:
    - 3 tiers: Free, Starter, Professional
    - Invoice generation tự động
    - Multi-currency support (USD, EUR, VND)

    Returns:
        RecipeOutput chứa BillingIR
    """
    data = {
        "plans": [
            {
                "id": "plan_free",
                "name": "Free Tier",
                "tier": "free",
                "monthly_price": 0,
                "annual_price": 0,
                "features": ["Basic features", "1 user", "100 MB storage"],
                "usage_limits": {"api_calls": 500, "storage_gb": 0.1, "users": 1},
            },
            {
                "id": "plan_starter",
                "name": "Starter Tier",
                "tier": "starter",
                "monthly_price": 1900,
                "annual_price": 19000,
                "features": [
                    "All Free features",
                    "5 users",
                    "5 GB storage",
                    "Email support",
                ],
                "usage_limits": {"api_calls": 25000, "storage_gb": 5, "users": 5},
            },
            {
                "id": "plan_professional",
                "name": "Professional Tier",
                "tier": "professional",
                "monthly_price": 7900,
                "annual_price": 79000,
                "features": [
                    "All Starter features",
                    "20 users",
                    "50 GB storage",
                    "Priority support",
                    "Advanced features",
                ],
                "usage_limits": {"api_calls": 200000, "storage_gb": 50, "users": 20},
            },
        ],
        "cycles": [
            {
                "id": "cycle_monthly",
                "type": "monthly",
                "auto_renew": True,
            },
            {
                "id": "cycle_annual",
                "type": "annual",
                "auto_renew": True,
            },
        ],
        "invoice_configs": [
            {
                "id": "inv_template_monthly",
                "tenant_id": "tenant_placeholder",
                "plan_id": "plan_starter",
                "amount": 1900,
                "currency": "USD",
                "status": "draft",
                "line_items": [
                    {"description": "Starter Plan — Monthly", "amount": 1900, "quantity": 1},
                ],
            },
        ],
        "meters": [
            {
                "id": "meter_api",
                "metric_name": "api_calls",
                "unit_price": 5,
                "billing_period": "monthly",
                "threshold_alerts": [80, 90, 100],
            },
            {
                "id": "meter_storage",
                "metric_name": "storage_gb",
                "unit_price": 30,
                "billing_period": "monthly",
                "threshold_alerts": [75, 90],
            },
        ],
        "gateways": [
            {
                "id": "gw_stripe",
                "provider": "stripe",
                "currencies": ["USD", "EUR"],
                "capture_mode": "automatic",
                "is_sandbox": True,
            },
            {
                "id": "gw_adyen",
                "provider": "adyen",
                "currencies": ["USD", "EUR", "VND"],
                "capture_mode": "automatic",
                "is_sandbox": True,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="multi_tier_billing_recipe",
        description="Multi-tier billing — Free → Starter → Pro với upgrade/downgrade",
        ir=ir,
        raw_data=data,
    )


def invoice_generation_recipe() -> RecipeOutput:
    """Recipe: Automated invoice generation.

    Cấu hình hệ thống tự động sinh hóa đơn:
    - Invoice config với line items chi tiết
    - Multiple payment gateways (Stripe + PayPal)
    - Usage meters để tính phí overage
    - Billing cycle hàng tháng với auto-renew

    Returns:
        RecipeOutput chứa BillingIR
    """
    data = {
        "plans": [
            {
                "id": "plan_standard",
                "name": "Standard Plan",
                "tier": "professional",
                "monthly_price": 4900,
                "annual_price": 49000,
                "features": [
                    "Core platform access",
                    "10 GB storage",
                    "API access (100K calls/month)",
                ],
                "usage_limits": {"api_calls": 100000, "storage_gb": 10, "users": 10},
            },
        ],
        "cycles": [
            {
                "id": "cycle_monthly",
                "type": "monthly",
                "auto_renew": True,
            },
        ],
        "invoice_configs": [
            {
                "id": "inv_001",
                "tenant_id": "tenant_acme_corp",
                "plan_id": "plan_standard",
                "amount": 5400,
                "currency": "USD",
                "status": "draft",
                "line_items": [
                    {
                        "description": "Standard Plan — Monthly subscription",
                        "amount": 4900,
                        "quantity": 1,
                    },
                    {
                        "description": "API Overage — 5,000 extra calls",
                        "amount": 500,
                        "quantity": 1,
                    },
                ],
            },
            {
                "id": "inv_002",
                "tenant_id": "tenant_globex",
                "plan_id": "plan_standard",
                "amount": 4900,
                "currency": "EUR",
                "status": "draft",
                "line_items": [
                    {
                        "description": "Standard Plan — Monthly subscription",
                        "amount": 4900,
                        "quantity": 1,
                    },
                ],
            },
        ],
        "meters": [
            {
                "id": "meter_api",
                "metric_name": "api_calls",
                "unit_price": 10,
                "billing_period": "monthly",
                "threshold_alerts": [75, 85, 95, 100],
            },
            {
                "id": "meter_storage",
                "metric_name": "storage_gb",
                "unit_price": 40,
                "billing_period": "monthly",
                "threshold_alerts": [80, 90, 100],
            },
        ],
        "gateways": [
            {
                "id": "gw_stripe",
                "provider": "stripe",
                "currencies": ["USD", "EUR", "GBP"],
                "capture_mode": "automatic",
                "is_sandbox": True,
                "is_enabled": True,
            },
            {
                "id": "gw_paypal",
                "provider": "paypal",
                "currencies": ["USD", "EUR"],
                "capture_mode": "automatic",
                "is_sandbox": True,
                "is_enabled": True,
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="invoice_generation_recipe",
        description="Automated invoice generation — multi-tenant với line items chi tiết",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "saas_billing_recipe",
    "usage_based_billing_recipe",
    "multi_tier_billing_recipe",
    "invoice_generation_recipe",
]
