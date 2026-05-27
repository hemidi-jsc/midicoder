# coding: utf-8
"""
Mô-đun recipes cho CP40 — Webhook & Outbound Integration Hub.

Cung cấp các recipe patterns để generate webhook với subscriptions,
auth config, và dispatch config theo common use cases.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.packs.cp40_webhook.models import (
    WebhookAuthConfig,
    WebhookAuthType,
    WebhookSubscription,
    WebhookStatus,
)
from midicoder.packs.cp40_webhook.parser import WebhookIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: WebhookIR kết quả
    """
    name: str
    description: str
    ir: WebhookIR


def basic_webhook_recipe() -> RecipeOutput:
    """Recipe: Cấu hình webhook cơ bản — single endpoint, không auth.

    Tạo subscription đơn giản cho event 'order.created',
    không auth, retry mặc định — phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình cơ bản
    """
    subscriptions = [
        WebhookSubscription(
            subscription_id="wh_basic_001",
            event_type="order.created",
            url="https://example.com/webhooks/order-created",
            http_method="POST",
            auth_config=WebhookAuthConfig(auth_type=WebhookAuthType.NONE),
            payload_template={"event_type": "{{event_type}}", "data": "{{data}}"},
            retry_policy={"max_retries": 3, "base_delay": 1.0, "max_delay": 30.0},
            rate_limit_rpm=30,
            status=WebhookStatus.ACTIVE,
            tags=["basic", "order"],
        ),
        WebhookSubscription(
            subscription_id="wh_basic_002",
            event_type="customer.created",
            url="https://example.com/webhooks/customer-created",
            http_method="POST",
            auth_config=WebhookAuthConfig(auth_type=WebhookAuthType.NONE),
            payload_template={"event_type": "{{event_type}}", "data": "{{data}}"},
            retry_policy={"max_retries": 3, "base_delay": 1.0, "max_delay": 30.0},
            rate_limit_rpm=30,
            status=WebhookStatus.ACTIVE,
            tags=["basic", "customer"],
        ),
    ]

    return RecipeOutput(
        name="basic_webhook",
        description="Single endpoint, no auth, basic retry",
        ir=WebhookIR(subscriptions=subscriptions),
    )


def event_driven_webhook_recipe() -> RecipeOutput:
    """Recipe: Webhook event-driven — multi-subscriber, HMAC auth, Redis queue.

    Tạo nhiều subscriptions cho các event khác nhau,
    HMAC-SHA256 auth, Redis queue cho dispatch, retry exponential backoff.

    Returns:
        RecipeOutput với cấu hình event-driven
    """
    subscriptions = [
        WebhookSubscription(
            subscription_id="wh_event_001",
            event_type="order.created",
            url="https://partner-api.example.com/webhooks/orders",
            http_method="POST",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                header_name="X-Webhook-Signature",
                secret="whsec_placeholder_secret_key",
                algorithm="sha256",
            ),
            payload_template={
                "event": "{{event_type}}",
                "timestamp": "{{timestamp}}",
                "data": {
                    "order_id": "{{order_id}}",
                    "total": "{{total}}",
                    "customer_id": "{{customer_id}}",
                },
            },
            retry_policy={"max_retries": 5, "base_delay": 2.0, "max_delay": 120.0},
            rate_limit_rpm=60,
            status=WebhookStatus.ACTIVE,
            tenant_id="tenant_main",
            tags=["event-driven", "order", "partner"],
        ),
        WebhookSubscription(
            subscription_id="wh_event_002",
            event_type="order.status_changed",
            url="https://partner-api.example.com/webhooks/orders/status",
            http_method="POST",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.HMAC,
                header_name="X-Webhook-Signature",
                secret="whsec_placeholder_secret_key",
                algorithm="sha256",
            ),
            payload_template={
                "event": "{{event_type}}",
                "timestamp": "{{timestamp}}",
                "data": {
                    "order_id": "{{order_id}}",
                    "status": "{{status}}",
                },
            },
            retry_policy={"max_retries": 5, "base_delay": 2.0, "max_delay": 120.0},
            rate_limit_rpm=60,
            status=WebhookStatus.ACTIVE,
            tenant_id="tenant_main",
            tags=["event-driven", "order", "partner"],
        ),
        WebhookSubscription(
            subscription_id="wh_event_003",
            event_type="payment.completed",
            url="https://analytics.example.com/webhooks/payments",
            http_method="POST",
            auth_config=WebhookAuthConfig(
                auth_type=WebhookAuthType.BEARER,
                header_name="Authorization",
                secret="bearer_token_placeholder",
            ),
            payload_template={
                "event": "{{event_type}}",
                "data": {
                    "payment_id": "{{payment_id}}",
                    "amount": "{{amount}}",
                    "currency": "{{currency}}",
                },
            },
            retry_policy={"max_retries": 3, "base_delay": 1.0, "max_delay": 60.0},
            rate_limit_rpm=120,
            status=WebhookStatus.ACTIVE,
            tags=["event-driven", "payment", "analytics"],
        ),
    ]

    return RecipeOutput(
        name="event_driven_webhook",
        description="Multi-subscriber, HMAC auth, Redis queue, exponential backoff",
        ir=WebhookIR(subscriptions=subscriptions, redis_url="redis://localhost:6379/0"),
    )


__all__ = [
    "RecipeOutput",
    "basic_webhook_recipe",
    "event_driven_webhook_recipe",
]
