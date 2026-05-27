# coding: utf-8
"""
Mô-đun parser cho CP40 — Webhook & Outbound Integration Hub.

Parse DSL dict (từ contract YAML) sang WebhookIR — Intermediate Representation
cho webhook subscriptions, dispatches, và config.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp40_webhook.models import (
    WebhookAuthConfig,
    WebhookAuthType,
    WebhookDispatch,
    WebhookSubscription,
    WebhookStatus,
)


@dataclass
class WebhookIR:
    """Intermediate Representation cho CP40.

    Gom tập tất cả cấu hình webhook từ DSL, bao gồm subscriptions,
    dispatches, và global config.

    Attributes:
        subscriptions: Danh sách webhook subscriptions
        dispatches: Danh sách webhook dispatches
        redis_url: URL kết nối Redis cho dispatch queue
    """
    subscriptions: list[WebhookSubscription] = field(default_factory=list)
    dispatches: list[WebhookDispatch] = field(default_factory=list)
    redis_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WebhookIR sang dict."""
        return {
            "subscriptions": [sub.to_dict() for sub in self.subscriptions],
            "dispatches": [d.to_dict() for d in self.dispatches],
            "redis_url": self.redis_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookIR":
        """Tạo WebhookIR từ dict."""
        subscriptions = [WebhookSubscription.from_dict(s) for s in data.get("subscriptions", [])]
        dispatches = [WebhookDispatch.from_dict(d) for d in data.get("dispatches", [])]
        return cls(
            subscriptions=subscriptions,
            dispatches=dispatches,
            redis_url=data.get("redis_url", ""),
        )


def parse_subscriptions(data: dict[str, Any]) -> list[WebhookSubscription]:
    """Parse danh sách webhook subscriptions từ DSL dict.

    Args:
        data: DSL dict với key 'subscriptions' hoặc 'webhooks'

    Returns:
        Danh sách WebhookSubscription
    """
    raw = data.get("subscriptions", data.get("webhooks", []))
    subscriptions = []
    for sub in raw:
        auth_data = sub.get("auth_config", sub.get("auth", {}))
        auth_config = WebhookAuthConfig(
            auth_type=WebhookAuthType(auth_data.get("auth_type", "none")),
            header_name=auth_data.get("header_name", "Authorization"),
            secret=auth_data.get("secret", ""),
            algorithm=auth_data.get("algorithm", "sha256"),
        )

        subscriptions.append(WebhookSubscription(
            subscription_id=sub.get("subscription_id", sub.get("id", "")),
            event_type=sub.get("event_type", sub.get("event", "")),
            url=sub.get("url", ""),
            http_method=sub.get("http_method", sub.get("method", "POST")),
            auth_config=auth_config,
            payload_template=sub.get("payload_template", sub.get("template", {})),
            retry_policy=sub.get("retry_policy", {"max_retries": 3, "base_delay": 1.0, "max_delay": 60.0}),
            rate_limit_rpm=sub.get("rate_limit_rpm", sub.get("rate_limit", 60)),
            status=WebhookStatus(sub.get("status", "active")),
            tenant_id=sub.get("tenant_id"),
            tags=sub.get("tags", []),
        ))
    return subscriptions


def parse_dispatches(data: dict[str, Any]) -> list[WebhookDispatch]:
    """Parse danh sách webhook dispatches từ DSL dict.

    Args:
        data: DSL dict với key 'dispatches' hoặc 'deliveries'

    Returns:
        Danh sách WebhookDispatch
    """
    raw = data.get("dispatches", data.get("deliveries", []))
    from midicoder.packs.cp40_webhook.models import DispatchStatus, WebhookDispatch as WD

    dispatches = []
    for d in raw:
        dispatches.append(WD(
            dispatch_id=d.get("dispatch_id", d.get("id", "")),
            subscription_id=d.get("subscription_id", ""),
            event_type=d.get("event_type", ""),
            payload=d.get("payload", {}),
            status=DispatchStatus(d.get("status", "pending")),
            attempts=d.get("attempts", 0),
        ))
    return dispatches


def parse_to_ir(data: dict[str, Any]) -> WebhookIR:
    """Parse DSL dict thành WebhookIR.

    Args:
        data: DSL dict với subscriptions, dispatches, redis_url

    Returns:
        WebhookIR gom tập tất cả parsed data
    """
    subscriptions = parse_subscriptions(data)
    dispatches = parse_dispatches(data)
    return WebhookIR(
        subscriptions=subscriptions,
        dispatches=dispatches,
        redis_url=data.get("redis_url", ""),
    )


__all__ = [
    "WebhookIR",
    "parse_subscriptions",
    "parse_dispatches",
    "parse_to_ir",
]
