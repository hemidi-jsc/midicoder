# coding: utf-8
"""
Mô-đun recipes cho CP48 — API Rate Limiting & Quota Management.

Cung cấp các recipe mặc định để generate IR cho rate limiting + quota.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp48_rate_limit.models import (
    QuotaConfig,
    QuotaLevel,
    QuotaPeriod,
    RateLimitPolicy,
    RateLimitStrategy,
)
from midicoder.packs.cp48_rate_limit.parser import RateLimitIR


# ===========================================================================
# Recipe Output
# ===========================================================================


@dataclass
class RecipeOutput:
    """Kết quả từ recipe.

    Attributes:
        ir: RateLimitIR đã build
        metadata: Thông tin bổ sung về recipe
    """
    ir: RateLimitIR
    metadata: dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# Recipes
# ===========================================================================


def build_rate_limit_recipe() -> RecipeOutput:
    """Build recipe mặc định cho rate limiting.

    Tạo các policies baseline cho API:
    - API general: 100 req/phút (Sliding Window)
    - API strict: 10 req/phút (Fixed Window) — cho auth endpoints
    - API burst: Token Bucket cho endpoints cần burst
    """
    policies = [
        RateLimitPolicy(
            policy_id="rl_api_general",
            name="API General Rate Limit",
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            max_requests=100,
            window_seconds=60,
            enabled=True,
            metadata={"description": "Giới hạn 100 request/phút cho API chung"},
        ),
        RateLimitPolicy(
            policy_id="rl_api_strict",
            name="API Strict Rate Limit",
            strategy=RateLimitStrategy.FIXED_WINDOW,
            max_requests=10,
            window_seconds=60,
            enabled=True,
            metadata={"description": "Giới hạn 10 request/phút cho auth endpoints"},
        ),
        RateLimitPolicy(
            policy_id="rl_api_burst",
            name="API Burst Rate Limit",
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            max_requests=50,
            window_seconds=60,
            refill_rate=1.0,
            burst_size=20,
            enabled=True,
            metadata={"description": "Token Bucket cho endpoints cần burst"},
        ),
    ]

    return RecipeOutput(
        ir=RateLimitIR(policies=policies, quotas=[]),
        metadata={
            "recipe": "build_rate_limit_recipe",
            "policies_count": len(policies),
        },
    )


def build_quota_recipe() -> RecipeOutput:
    """Build recipe mặc định cho quota management.

    Tạo các quota configs baseline:
    - Per-user: 1000 req/ngày
    - Per-tenant: 100000 req/tháng
    - Per-endpoint: 50 req/phút cho search
    - Global: 1M req/phút
    """
    quotas = [
        QuotaConfig(
            config_id="quota_user_daily",
            level=QuotaLevel.USER,
            period=QuotaPeriod.DAY,
            max_requests=1000,
            enabled=True,
            metadata={"description": "Quota 1000 request/ngày cho từng user"},
        ),
        QuotaConfig(
            config_id="quota_tenant_monthly",
            level=QuotaLevel.TENANT,
            period=QuotaPeriod.MONTH,
            max_requests=100000,
            tenant_id="__default__",
            enabled=True,
            metadata={"description": "Quota 100000 request/tháng cho tenant"},
        ),
        QuotaConfig(
            config_id="quota_endpoint_search",
            level=QuotaLevel.ENDPOINT,
            period=QuotaPeriod.MINUTE,
            max_requests=50,
            endpoint="/api/search",
            enabled=True,
            metadata={"description": "Quota 50 request/phút cho search endpoint"},
        ),
        QuotaConfig(
            config_id="quota_global",
            level=QuotaLevel.GLOBAL,
            period=QuotaPeriod.MINUTE,
            max_requests=1000000,
            enabled=True,
            metadata={"description": "Quota 1 triệu request/phút toàn hệ thống"},
        ),
    ]

    return RecipeOutput(
        ir=RateLimitIR(policies=[], quotas=quotas),
        metadata={
            "recipe": "build_quota_recipe",
            "quotas_count": len(quotas),
        },
    )


def build_full_recipe() -> RecipeOutput:
    """Build recipe đầy đủ: cả rate limiting và quota.

    Kết hợp build_rate_limit_recipe + build_quota_recipe.
    """
    rl = build_rate_limit_recipe()
    qt = build_quota_recipe()

    ir = RateLimitIR(
        policies=rl.ir.policies,
        quotas=qt.ir.quotas,
    )

    return RecipeOutput(
        ir=ir,
        metadata={
            "recipe": "build_full_recipe",
            "policies_count": len(ir.policies),
            "quotas_count": len(ir.quotas),
        },
    )


__all__ = [
    "RecipeOutput",
    "build_rate_limit_recipe",
    "build_quota_recipe",
    "build_full_recipe",
]
