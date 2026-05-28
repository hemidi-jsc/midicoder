# coding: utf-8
"""
Comprehensive tests cho CP09 CacheParser.
"""

import pytest
import yaml
from midicoder.packs.cp_backend_cache.parser import CacheParser
from midicoder.packs.cp_backend_cache.models import (
    CacheBackend,
    InvalidationStrategy,
    StampedePreventionStrategy,
    CacheWarmupStrategy,
)


class TestCacheParser:
    def setup_method(self):
        self.parser = CacheParser()

    def test_parse_yaml_string(self):
        raw = yaml.dump({
            "cache_profiles": [
                {"id": "test_cache", "backend": "redis", "ttl": 600},
            ]
        })
        profiles = self.parser.parse(raw)
        assert len(profiles) == 1
        assert profiles[0].id == "test_cache"

    def test_parse_empty_yaml(self):
        raw = yaml.dump({"cache_profiles": []})
        profiles = self.parser.parse(raw)
        assert len(profiles) == 0

    def test_parse_from_metadata_minimal(self):
        metadata = {}
        collection = self.parser.parse_from_metadata(metadata)
        assert collection.total_count == 0

    def test_parse_profiles(self):
        metadata = {
            "cache_profiles": [
                {"id": "p1", "backend": "redis", "ttl": 300},
                {"id": "p2", "backend": "memory", "ttl": 60},
                {"id": "p3", "backend": "memcached", "ttl": 120},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.total_count == 3
        assert c.profiles[0].backend == CacheBackend.REDIS
        assert c.profiles[1].backend == CacheBackend.MEMORY
        assert c.profiles[2].backend == CacheBackend.MEMCACHED

    def test_parse_strategies(self):
        metadata = {
            "strategies": [
                {"profile_id": "p1", "strategy_type": "read_through", "load_from": "db"},
                {"profile_id": "p1", "strategy_type": "write_through"},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.strategies) == 2

    def test_parse_invalidation_rules(self):
        metadata = {
            "invalidation_rules": [
                {"profile_id": "p1", "pattern": "user:*", "strategy": "pattern"},
                {"profile_id": "p1", "tags": ["users"], "strategy": "tag"},
                {"profile_id": "p1", "events": ["OrderCreated"], "strategy": "event"},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.invalidation_rules) == 3

    def test_parse_warm_configs(self):
        metadata = {
            "warm_configs": [
                {"profile_id": "p1", "keys": ["k1", "k2"], "schedule": "*/5 * * * *"},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.warm_configs) == 1
        assert c.warm_configs[0].keys == ["k1", "k2"]

    def test_parse_metrics(self):
        metadata = {
            "metrics": [
                {"profile_id": "p1", "hit_count": 100, "miss_count": 50, "avg_latency_ms": 2.5},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.metrics) == 1
        assert c.metrics[0].hit_rate == 66.67

    def test_parse_cdn_layers(self):
        metadata = {
            "cdn_layers": [
                {"provider": "cloudflare", "zone_id": "z123", "default_ttl": 7200},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.cdn_layers) == 1
        assert c.cdn_layers[0].provider == "cloudflare"
        assert c.cdn_layers[0].default_ttl == 7200

    def test_parse_stampede_prevention(self):
        metadata = {
            "stampede_prevention": {
                "enabled": True,
                "strategy": "mutex",
                "lock_ttl": 15,
            }
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.stampede_prevention is not None
        assert c.stampede_prevention.strategy == StampedePreventionStrategy.MUTEX
        assert c.stampede_prevention.lock_ttl == 15

    def test_parse_stampede_invalid_strategy(self):
        metadata = {
            "stampede_prevention": {"strategy": "unknown_strategy"}
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.stampede_prevention is not None
        assert c.stampede_prevention.strategy == StampedePreventionStrategy.MUTEX

    def test_parse_tiers(self):
        metadata = {
            "tiers": [
                {"tier_name": "l1", "tier_order": 1, "backend": "memory", "max_size": 1000, "ttl": 60},
                {"tier_name": "l2", "tier_order": 2, "backend": "redis", "max_size": 10000, "ttl": 300},
            ]
        }
        c = self.parser.parse_from_metadata(metadata)
        assert len(c.tiers) == 2
        assert c.tiers[0].tier_order == 1
        assert c.tiers[1].tier_order == 2

    def test_parse_warmup_config(self):
        metadata = {
            "warmup_config": {
                "strategy": "scheduled",
                "schedule_cron": "*/10 * * * *",
                "warmup_keys": ["k1", "k2"],
                "parallelism": 8,
            }
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.warmup_config is not None
        assert c.warmup_config.strategy == CacheWarmupStrategy.SCHEDULED
        assert c.warmup_config.parallelism == 8

    def test_parse_warmup_invalid_strategy(self):
        metadata = {
            "warmup_config": {"strategy": "invalid"}
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.warmup_config is not None
        assert c.warmup_config.strategy == CacheWarmupStrategy.ON_STARTUP

    def test_parse_full_metadata(self):
        metadata = {
            "cache_profiles": [{"id": "p1", "backend": "redis"}],
            "strategies": [{"profile_id": "p1", "strategy_type": "cache_aside"}],
            "invalidation_rules": [{"profile_id": "p1", "pattern": "*", "strategy": "pattern"}],
            "warm_configs": [{"profile_id": "p1", "keys": ["k1"]}],
            "metrics": [{"profile_id": "p1", "hit_count": 100}],
            "cdn_layers": [{"provider": "cloudflare"}],
            "stampede_prevention": {"enabled": True},
            "tiers": [{"tier_name": "l1", "tier_order": 1}],
            "warmup_config": {"strategy": "on_startup"},
        }
        c = self.parser.parse_from_metadata(metadata)
        assert c.total_count == 1
        assert len(c.strategies) == 1
        assert len(c.invalidation_rules) == 1
        assert len(c.warm_configs) == 1
        assert len(c.metrics) == 1
        assert len(c.cdn_layers) == 1
        assert c.stampede_prevention is not None
        assert len(c.tiers) == 1
        assert c.warmup_config is not None

    def test_parse_invalid_yaml_raises(self):
        with pytest.raises(Exception):
            self.parser.parse("{{invalid yaml")
