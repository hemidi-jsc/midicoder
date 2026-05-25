# coding: utf-8
"""
Tests cho CP48 parser — RateLimitParser.

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp48_rate_limit.parser import (
    RateLimitIR,
    RateLimitParser,
)
from midicoder.emitters.core.cp48_rate_limit.models import (
    RateLimitStrategy,
    QuotaLevel,
    QuotaPeriod,
)
from midicoder.errors import MidicoderError


class TestRateLimitParserPolicies:
    """Test RateLimitParser.parse_policies."""

    def test_parse_single_fixed_window(self):
        yaml_data = [{
            "id": "p1",
            "name": "General API",
            "strategy": "fixed_window",
            "max_requests": 100,
            "window_seconds": 60,
        }]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert len(policies) == 1
        assert policies[0].policy_id == "p1"
        assert policies[0].strategy == RateLimitStrategy.FIXED_WINDOW

    def test_parse_sliding_window(self):
        yaml_data = [{
            "policy_id": "p2",
            "name": "Sliding",
            "strategy": "sliding_window",
            "max_requests": 200,
            "window_seconds": 120,
        }]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert policies[0].strategy == RateLimitStrategy.SLIDING_WINDOW

    def test_parse_token_bucket(self):
        yaml_data = [{
            "policy_id": "p3",
            "name": "Burst",
            "strategy": "token_bucket",
            "max_requests": 50,
            "window_seconds": 60,
            "refill_rate": 2.0,
            "burst_size": 15,
        }]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert policies[0].refill_rate == 2.0
        assert policies[0].burst_size == 15

    def test_parse_multiple_policies(self):
        yaml_data = [
            {"policy_id": "p1", "name": "A", "strategy": "fixed_window", "max_requests": 100, "window_seconds": 60},
            {"policy_id": "p2", "name": "B", "strategy": "sliding_window", "max_requests": 200, "window_seconds": 60},
        ]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert len(policies) == 2

    def test_parse_invalid_strategy_raises(self):
        yaml_data = [{
            "policy_id": "bad",
            "name": "Bad",
            "strategy": "invalid_strategy",
            "max_requests": 100,
            "window_seconds": 60,
        }]
        with pytest.raises(MidicoderError):
            RateLimitParser.parse_policies(yaml_data)

    def test_defaults(self):
        yaml_data = [{
            "policy_id": "p1",
            "name": "Test",
            "strategy": "fixed_window",
            "max_requests": 100,
            "window_seconds": 60,
        }]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert policies[0].enabled is True
        assert policies[0].bypass_keys == []

    def test_bypass_keys_and_metadata(self):
        yaml_data = [{
            "policy_id": "p1",
            "name": "Test",
            "strategy": "fixed_window",
            "max_requests": 100,
            "window_seconds": 60,
            "bypass_keys": ["admin", "system"],
            "metadata": {"key": "value"},
        }]
        policies = RateLimitParser.parse_policies(yaml_data)
        assert "admin" in policies[0].bypass_keys
        assert policies[0].metadata["key"] == "value"

    def test_empty_list(self):
        policies = RateLimitParser.parse_policies([])
        assert len(policies) == 0


class TestRateLimitParserQuotas:
    """Test RateLimitParser.parse_quotas."""

    def test_parse_user_quota(self):
        yaml_data = [{
            "id": "q1",
            "level": "user",
            "period": "day",
            "max_requests": 1000,
        }]
        quotas = RateLimitParser.parse_quotas(yaml_data)
        assert len(quotas) == 1
        assert quotas[0].level == QuotaLevel.USER
        assert quotas[0].period == QuotaPeriod.DAY

    def test_parse_tenant_quota(self):
        yaml_data = [{
            "config_id": "q2",
            "level": "tenant",
            "period": "month",
            "max_requests": 100000,
            "tenant_id": "t1",
        }]
        quotas = RateLimitParser.parse_quotas(yaml_data)
        assert quotas[0].level == QuotaLevel.TENANT
        assert quotas[0].tenant_id == "t1"

    def test_parse_endpoint_quota(self):
        yaml_data = [{
            "config_id": "q3",
            "level": "endpoint",
            "period": "minute",
            "max_requests": 50,
            "endpoint": "/api/search",
        }]
        quotas = RateLimitParser.parse_quotas(yaml_data)
        assert quotas[0].endpoint == "/api/search"

    def test_parse_global_quota(self):
        yaml_data = [{
            "config_id": "q4",
            "level": "global",
            "period": "hour",
            "max_requests": 100000,
        }]
        quotas = RateLimitParser.parse_quotas(yaml_data)
        assert quotas[0].level == QuotaLevel.GLOBAL

    def test_parse_invalid_level_raises(self):
        yaml_data = [{
            "config_id": "bad",
            "level": "invalid_level",
            "period": "day",
            "max_requests": 100,
        }]
        with pytest.raises(MidicoderError):
            RateLimitParser.parse_quotas(yaml_data)

    def test_parse_invalid_period_raises(self):
        yaml_data = [{
            "config_id": "bad",
            "level": "user",
            "period": "invalid_period",
            "max_requests": 100,
        }]
        with pytest.raises(MidicoderError):
            RateLimitParser.parse_quotas(yaml_data)

    def test_defaults(self):
        yaml_data = [{
            "config_id": "q1",
            "level": "user",
            "period": "day",
            "max_requests": 1000,
        }]
        quotas = RateLimitParser.parse_quotas(yaml_data)
        assert quotas[0].enabled is True

    def test_empty_list(self):
        quotas = RateLimitParser.parse_quotas([])
        assert len(quotas) == 0


class TestRateLimitParserToIR:
    """Test RateLimitParser.parse_to_ir."""

    def test_parse_full_yaml(self):
        yaml_dict = {
            "policies": [
                {
                    "policy_id": "p1",
                    "name": "API",
                    "strategy": "fixed_window",
                    "max_requests": 100,
                    "window_seconds": 60,
                }
            ],
            "quotas": [
                {
                    "config_id": "q1",
                    "level": "user",
                    "period": "day",
                    "max_requests": 1000,
                }
            ],
        }
        ir = RateLimitParser.parse_to_ir(yaml_dict)
        assert len(ir.policies) == 1
        assert len(ir.quotas) == 1

    def test_parse_empty_yaml(self):
        ir = RateLimitParser.parse_to_ir({})
        assert len(ir.policies) == 0
        assert len(ir.quotas) == 0


class TestRateLimitIR:
    """Test RateLimitIR dataclass."""

    def test_to_dict(self):
        ir = RateLimitIR()
        d = ir.to_dict()
        assert d == {"policies": [], "quotas": []}

    def test_from_dict_empty(self):
        ir = RateLimitIR.from_dict({})
        assert len(ir.policies) == 0
        assert len(ir.quotas) == 0

    def test_from_dict_with_data(self):
        data = {
            "policies": [
                {
                    "policy_id": "p1",
                    "name": "Test",
                    "strategy": "fixed_window",
                    "max_requests": 100,
                    "window_seconds": 60,
                }
            ],
            "quotas": [
                {
                    "config_id": "q1",
                    "level": "user",
                    "period": "day",
                    "max_requests": 1000,
                }
            ],
        }
        ir = RateLimitIR.from_dict(data)
        assert len(ir.policies) == 1
        assert len(ir.quotas) == 1

    def test_roundtrip(self):
        original = RateLimitIR.from_dict({
            "policies": [
                {"policy_id": "p1", "name": "A", "strategy": "token_bucket", "max_requests": 50, "window_seconds": 60, "refill_rate": 1.0, "burst_size": 10}
            ],
            "quotas": [
                {"config_id": "q1", "level": "global", "period": "minute", "max_requests": 100000}
            ],
        })
        restored = RateLimitIR.from_dict(original.to_dict())
        assert len(restored.policies) == len(original.policies)
        assert restored.policies[0].policy_id == original.policies[0].policy_id
