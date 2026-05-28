# coding: utf-8
"""
Tests cho CP48 recipes — build_rate_limit_recipe, build_quota_recipe, build_full_recipe.

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_rate_limit.recipes import (
    RecipeOutput,
    build_full_recipe,
    build_quota_recipe,
    build_rate_limit_recipe,
)
from midicoder.packs.cp_full_rate_limit.models import (
    RateLimitStrategy,
    QuotaLevel,
    QuotaPeriod,
)


class TestBuildRateLimitRecipe:
    """Test build_rate_limit_recipe."""

    def test_returns_recipe_output(self):
        result = build_rate_limit_recipe()
        assert isinstance(result, RecipeOutput)

    def test_policies_count(self):
        result = build_rate_limit_recipe()
        assert len(result.ir.policies) == 3

    def test_strategies_present(self):
        result = build_rate_limit_recipe()
        strategies = {p.strategy for p in result.ir.policies}
        assert RateLimitStrategy.SLIDING_WINDOW in strategies
        assert RateLimitStrategy.FIXED_WINDOW in strategies
        assert RateLimitStrategy.TOKEN_BUCKET in strategies

    def test_policy_ids(self):
        result = build_rate_limit_recipe()
        ids = {p.policy_id for p in result.ir.policies}
        assert "rl_api_general" in ids
        assert "rl_api_strict" in ids
        assert "rl_api_burst" in ids

    def test_general_policy_config(self):
        result = build_rate_limit_recipe()
        general = next(p for p in result.ir.policies if p.policy_id == "rl_api_general")
        assert general.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert general.max_requests == 100
        assert general.window_seconds == 60

    def test_strict_policy_config(self):
        result = build_rate_limit_recipe()
        strict = next(p for p in result.ir.policies if p.policy_id == "rl_api_strict")
        assert strict.strategy == RateLimitStrategy.FIXED_WINDOW
        assert strict.max_requests == 10

    def test_burst_policy_config(self):
        result = build_rate_limit_recipe()
        burst = next(p for p in result.ir.policies if p.policy_id == "rl_api_burst")
        assert burst.strategy == RateLimitStrategy.TOKEN_BUCKET
        assert burst.refill_rate > 0
        assert burst.burst_size > 0

    def test_no_quotas(self):
        result = build_rate_limit_recipe()
        assert len(result.ir.quotas) == 0

    def test_metadata(self):
        result = build_rate_limit_recipe()
        assert result.metadata["recipe"] == "build_rate_limit_recipe"


class TestBuildQuotaRecipe:
    """Test build_quota_recipe."""

    def test_returns_recipe_output(self):
        result = build_quota_recipe()
        assert isinstance(result, RecipeOutput)

    def test_quotas_count(self):
        result = build_quota_recipe()
        assert len(result.ir.quotas) == 4

    def test_all_levels_present(self):
        result = build_quota_recipe()
        levels = {q.level for q in result.ir.quotas}
        assert QuotaLevel.USER in levels
        assert QuotaLevel.TENANT in levels
        assert QuotaLevel.ENDPOINT in levels
        assert QuotaLevel.GLOBAL in levels

    def test_config_ids(self):
        result = build_quota_recipe()
        ids = {q.config_id for q in result.ir.quotas}
        assert "quota_user_daily" in ids
        assert "quota_tenant_monthly" in ids
        assert "quota_endpoint_search" in ids
        assert "quota_global" in ids

    def test_user_quota_config(self):
        result = build_quota_recipe()
        user = next(q for q in result.ir.quotas if q.config_id == "quota_user_daily")
        assert user.level == QuotaLevel.USER
        assert user.period == QuotaPeriod.DAY
        assert user.max_requests == 1000

    def test_tenant_quota_config(self):
        result = build_quota_recipe()
        tenant = next(q for q in result.ir.quotas if q.config_id == "quota_tenant_monthly")
        assert tenant.level == QuotaLevel.TENANT
        assert tenant.period == QuotaPeriod.MONTH
        assert tenant.max_requests == 100000

    def test_endpoint_quota_config(self):
        result = build_quota_recipe()
        endpoint = next(q for q in result.ir.quotas if q.config_id == "quota_endpoint_search")
        assert endpoint.level == QuotaLevel.ENDPOINT
        assert endpoint.endpoint == "/api/search"

    def test_global_quota_config(self):
        result = build_quota_recipe()
        global_q = next(q for q in result.ir.quotas if q.config_id == "quota_global")
        assert global_q.level == QuotaLevel.GLOBAL
        assert global_q.max_requests == 1000000

    def test_no_policies(self):
        result = build_quota_recipe()
        assert len(result.ir.policies) == 0

    def test_metadata(self):
        result = build_quota_recipe()
        assert result.metadata["recipe"] == "build_quota_recipe"


class TestBuildFullRecipe:
    """Test build_full_recipe."""

    def test_returns_recipe_output(self):
        result = build_full_recipe()
        assert isinstance(result, RecipeOutput)

    def test_has_policies_and_quotas(self):
        result = build_full_recipe()
        assert len(result.ir.policies) == 3
        assert len(result.ir.quotas) == 4

    def test_metadata(self):
        result = build_full_recipe()
        assert result.metadata["recipe"] == "build_full_recipe"
        assert result.metadata["policies_count"] == 3
        assert result.metadata["quotas_count"] == 4
