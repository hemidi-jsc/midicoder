# coding: utf-8
"""
Comprehensive tests cho CP09 Cache models.

Test coverage:
- CacheProfile (create, validation, to_dict, from_dict)
- CacheStrategy (create, validation, serialization)
- CacheInvalidationRule (all strategies)
- CacheWarmConfig (validation)
- CacheMetrics (properties, validation)
- CacheCollection (CRUD, filters, serialization)
- CDNCacheLayer (create, validation, serialization)
- StampedePrevention (all strategies, validation)
- CacheTier (validation)
- CacheWarmupConfig (all strategies)
- Enum mapping
"""

import pytest
from midicoder.packs.cp09_cache.models import (
    CacheBackend,
    InvalidationStrategy,
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheWarmConfig,
    CacheMetrics,
    CacheCollection,
    _BACKEND_MAP,
    _STRATEGY_MAP,
    CDNCacheLayer,
    CDNCacheControlDirective,
    StampedePrevention,
    StampedePreventionStrategy,
    CacheTier,
    CacheWarmupConfig,
    CacheWarmupStrategy,
)


# ============================================================================
# CacheBackend enum
# ============================================================================

class TestCacheBackend:
    def test_redis_backend(self):
        assert CacheBackend.REDIS.value == "redis"

    def test_memory_backend(self):
        assert CacheBackend.MEMORY.value == "memory"

    def test_memcached_backend(self):
        assert CacheBackend.MEMCACHED.value == "memcached"

    def test_backend_map_complete(self):
        assert "redis" in _BACKEND_MAP
        assert "memory" in _BACKEND_MAP
        assert "memcached" in _BACKEND_MAP
        assert _BACKEND_MAP["redis"] == CacheBackend.REDIS
        assert _BACKEND_MAP["memory"] == CacheBackend.MEMORY
        assert _BACKEND_MAP["memcached"] == CacheBackend.MEMCACHED

    def test_strategy_map_complete(self):
        assert "pattern" in _STRATEGY_MAP
        assert "tag" in _STRATEGY_MAP
        assert "event" in _STRATEGY_MAP


# ============================================================================
# CacheProfile
# ============================================================================

class TestCacheProfile:
    def test_create_default(self):
        p = CacheProfile(id="test_cache", backend=CacheBackend.REDIS)
        assert p.id == "test_cache"
        assert p.backend == CacheBackend.REDIS
        assert p.ttl == 300
        assert p.max_size is None
        assert p.serializer == "json"
        assert p.key_prefix == ""
        assert p.tenant_isolated is True
        assert p.description == ""

    def test_create_custom(self):
        p = CacheProfile(
            id="custom",
            backend=CacheBackend.MEMCACHED,
            ttl=600,
            max_size=5000,
            serializer="pickle",
            key_prefix="app:",
            tenant_isolated=False,
            description="Custom cache",
        )
        assert p.backend == CacheBackend.MEMCACHED
        assert p.ttl == 600
        assert p.max_size == 5000
        assert p.serializer == "pickle"
        assert p.key_prefix == "app:"
        assert p.tenant_isolated is False

    def test_to_dict(self):
        p = CacheProfile(id="dict_test", backend=CacheBackend.MEMORY, ttl=120)
        d = p.to_dict()
        assert d["id"] == "dict_test"
        assert d["backend"] == "memory"
        assert d["ttl"] == 120
        assert d["tenant_isolated"] is True

    def test_from_dict(self):
        d = {"id": "from_dict", "backend": "redis", "ttl": 600, "max_size": 1000}
        p = CacheProfile.from_dict(d)
        assert p.id == "from_dict"
        assert p.backend == CacheBackend.REDIS
        assert p.ttl == 600
        assert p.max_size == 1000

    def test_from_dict_defaults(self):
        d = {}
        p = CacheProfile.from_dict(d)
        assert p.backend == CacheBackend.REDIS
        assert p.ttl == 300
        assert p.tenant_isolated is True

    def test_round_trip(self):
        p = CacheProfile(id="round", backend=CacheBackend.MEMCACHED, ttl=900, key_prefix="x:")
        d = p.to_dict()
        p2 = CacheProfile.from_dict(d)
        assert p2.id == p.id
        assert p2.backend == p.backend
        assert p2.ttl == p.ttl
        assert p2.key_prefix == p.key_prefix


# ============================================================================
# CacheStrategy
# ============================================================================

class TestCacheStrategy:
    def test_create_default(self):
        s = CacheStrategy(profile_id="p1")
        assert s.profile_id == "p1"
        assert s.strategy_type == "cache_aside"
        assert s.load_from == ""
        assert s.tenant_scoped is True

    def test_read_through(self):
        s = CacheStrategy(profile_id="p1", strategy_type="read_through", load_from="db")
        assert s.strategy_type == "read_through"
        assert s.load_from == "db"

    def test_write_through(self):
        s = CacheStrategy(profile_id="p1", strategy_type="write_through")
        assert s.strategy_type == "write_through"

    def test_to_dict_and_back(self):
        s = CacheStrategy(profile_id="s1", strategy_type="read_through", load_from="api")
        d = s.to_dict()
        s2 = CacheStrategy.from_dict(d)
        assert s2.profile_id == s.profile_id
        assert s2.strategy_type == s.strategy_type
        assert s2.load_from == s.load_from


# ============================================================================
# CacheInvalidationRule
# ============================================================================

class TestCacheInvalidationRule:
    def test_pattern_strategy(self):
        r = CacheInvalidationRule(profile_id="p1", pattern="user:*", strategy=InvalidationStrategy.PATTERN)
        assert r.pattern == "user:*"
        assert r.strategy == InvalidationStrategy.PATTERN

    def test_tag_strategy(self):
        r = CacheInvalidationRule(
            profile_id="p1",
            tags=["users", "orders"],
            strategy=InvalidationStrategy.TAG,
        )
        assert r.tags == ["users", "orders"]
        assert r.strategy == InvalidationStrategy.TAG

    def test_event_strategy(self):
        r = CacheInvalidationRule(
            profile_id="p1",
            events=["OrderCreated", "UserUpdated"],
            strategy=InvalidationStrategy.EVENT,
        )
        assert r.events == ["OrderCreated", "UserUpdated"]

    def test_to_dict_and_back(self):
        r = CacheInvalidationRule(profile_id="p1", pattern=":*", tags=["a"])
        d = r.to_dict()
        r2 = CacheInvalidationRule.from_dict(d)
        assert r2.profile_id == r.profile_id
        assert r2.pattern == r.pattern


# ============================================================================
# CacheWarmConfig
# ============================================================================

class TestCacheWarmConfig:
    def test_with_keys(self):
        w = CacheWarmConfig(profile_id="p1", keys=["k1", "k2"])
        assert w.keys == ["k1", "k2"]

    def test_with_pattern(self):
        w = CacheWarmConfig(profile_id="p1", pattern="user:*")
        assert w.pattern == "user:*"

    def test_round_trip(self):
        w = CacheWarmConfig(profile_id="p1", keys=["a"], schedule="*/5 * * * *")
        d = w.to_dict()
        w2 = CacheWarmConfig.from_dict(d)
        assert w2.schedule == w.schedule


# ============================================================================
# CacheMetrics
# ============================================================================

class TestCacheMetrics:
    def test_hit_rate_zero(self):
        m = CacheMetrics(profile_id="p1")
        assert m.hit_rate == 0.0

    def test_hit_rate_100(self):
        m = CacheMetrics(profile_id="p1", hit_count=100, miss_count=0)
        assert m.hit_rate == 100.0

    def test_hit_rate_50(self):
        m = CacheMetrics(profile_id="p1", hit_count=50, miss_count=50)
        assert m.hit_rate == 50.0

    def test_hit_rate_partial(self):
        m = CacheMetrics(profile_id="p1", hit_count=9, miss_count=1)
        assert m.hit_rate == 90.0

    def test_to_dict_includes_hit_rate(self):
        m = CacheMetrics(profile_id="p1", hit_count=80, miss_count=20)
        d = m.to_dict()
        assert d["hit_rate"] == 80.0
        assert d["hit_count"] == 80

    def test_round_trip(self):
        m = CacheMetrics(
            profile_id="m1",
            hit_count=100,
            miss_count=50,
            eviction_count=5,
            avg_latency_ms=2.5,
            peak_memory_mb=128.0,
        )
        d = m.to_dict()
        m2 = CacheMetrics.from_dict(d)
        assert m2.hit_count == m.hit_count
        assert m2.avg_latency_ms == m.avg_latency_ms


# ============================================================================
# CDNCacheLayer
# ============================================================================

class TestCDNCacheLayer:
    def test_defaults(self):
        c = CDNCacheLayer()
        assert c.provider == "cloudflare"
        assert c.default_ttl == 3600
        assert c.max_ttl == 86400
        assert c.enable_compression is True
        assert c.enable_origin_shield is False

    def test_custom_provider(self):
        c = CDNCacheLayer(provider="cloudfront", zone_id="z123", origin_url="https://origin.example.com")
        assert c.provider == "cloudfront"
        assert c.zone_id == "z123"

    def test_ttl_validation(self):
        c = CDNCacheLayer(default_ttl=-1)
        assert c.default_ttl == 3600  # corrected to default

    def test_max_ttl_less_than_default(self):
        c = CDNCacheLayer(default_ttl=7200, max_ttl=1800)
        assert c.max_ttl >= c.default_ttl

    def test_round_trip(self):
        c = CDNCacheLayer(provider="fastly", zone_id="z99", origin_url="https://o.com", default_ttl=1800)
        d = c.to_dict()
        c2 = CDNCacheLayer.from_dict(d)
        assert c2.provider == c.provider
        assert c2.default_ttl == c.default_ttl


# ============================================================================
# StampedePrevention
# ============================================================================

class TestStampedePrevention:
    def test_defaults(self):
        s = StampedePrevention()
        assert s.enabled is True
        assert s.strategy == StampedePreventionStrategy.MUTEX
        assert s.lock_ttl == 10
        assert s.lock_timeout == 5

    def test_all_strategies(self):
        for strat in StampedePreventionStrategy:
            s = StampedePrevention(strategy=strat)
            assert s.strategy == strat

    def test_ttl_validation(self):
        s = StampedePrevention(lock_ttl=0)
        assert s.lock_ttl == 10

    def test_threshold_validation(self):
        s = StampedePrevention(early_refresh_threshold=2.0)
        assert s.early_refresh_threshold == 0.8

    def test_round_trip(self):
        s = StampedePrevention(
            enabled=True,
            strategy=StampedePreventionStrategy.EARLY_UPDATE,
            lock_ttl=15,
            early_refresh_threshold=0.9,
        )
        d = s.to_dict()
        s2 = StampedePrevention.from_dict(d)
        assert s2.enabled == s.enabled
        assert s2.strategy == s.strategy


# ============================================================================
# CacheTier
# ============================================================================

class TestCacheTier:
    def test_l1_memory(self):
        t = CacheTier(tier_name="l1_memory", tier_order=1, backend="memory", max_size=1000, ttl=60)
        assert t.tier_order == 1

    def test_l2_redis(self):
        t = CacheTier(tier_name="l2_redis", tier_order=2, backend="redis", max_size=10000, ttl=300)
        assert t.tier_order == 2

    def test_validation(self):
        t = CacheTier(tier_name="test", tier_order=-1)
        assert t.tier_order == 1

    def test_round_trip(self):
        t = CacheTier(tier_name="l3_db", tier_order=3, backend="database", eviction_policy="lfu")
        d = t.to_dict()
        t2 = CacheTier.from_dict(d)
        assert t2.tier_name == t.tier_name
        assert t2.eviction_policy == t.eviction_policy


# ============================================================================
# CacheWarmupConfig
# ============================================================================

class TestCacheWarmupConfig:
    def test_defaults(self):
        w = CacheWarmupConfig()
        assert w.strategy == CacheWarmupStrategy.ON_STARTUP
        assert w.batch_size == 100
        assert w.max_keys == 10000
        assert w.parallelism == 4

    def test_scheduled(self):
        w = CacheWarmupConfig(strategy=CacheWarmupStrategy.SCHEDULED, schedule_cron="*/10 * * * *")
        assert w.schedule_cron == "*/10 * * * *"

    def test_validation(self):
        w = CacheWarmupConfig(batch_size=0)
        assert w.batch_size == 100

    def test_round_trip(self):
        w = CacheWarmupConfig(
            strategy=CacheWarmupStrategy.BACKGROUND,
            warmup_keys=["k1", "k2"],
            parallelism=8,
        )
        d = w.to_dict()
        w2 = CacheWarmupConfig.from_dict(d)
        assert w2.strategy == w.strategy
        assert w2.parallelism == w.parallelism


# ============================================================================
# CacheCollection
# ============================================================================

class TestCacheCollection:
    def test_empty(self):
        c = CacheCollection()
        assert c.total_count == 0
        assert c.profiles == []
        assert c.cdn_layers == []
        assert c.stampede_prevention is None
        assert c.tiers == []
        assert c.warmup_config is None

    def test_add_profile(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        assert c.total_count == 1

    def test_get_by_id(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_profile(CacheProfile(id="p2", backend=CacheBackend.MEMORY))
        assert c.get_by_id("p1").id == "p1"
        assert c.get_by_id("nonexist") is None

    def test_filters(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="r1", backend=CacheBackend.REDIS, tenant_isolated=True))
        c.add_profile(CacheProfile(id="m1", backend=CacheBackend.MEMORY, tenant_isolated=True))
        c.add_profile(CacheProfile(id="mc1", backend=CacheBackend.MEMCACHED, tenant_isolated=False))
        assert len(c.redis_profiles()) == 1
        assert len(c.memory_profiles()) == 1
        assert len(c.memcached_profiles()) == 1
        assert len(c.tenant_isolated_profiles()) == 2

    def test_add_strategies_and_rules(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_strategy(CacheStrategy(profile_id="p1", strategy_type="read_through"))
        c.add_invalidation_rule(
            CacheInvalidationRule(profile_id="p1", pattern="*", strategy=InvalidationStrategy.PATTERN)
        )
        assert len(c.get_strategies_for("p1")) == 1
        assert len(c.get_invalidation_rules_for("p1")) == 1

    def test_add_cdn_layer(self):
        c = CacheCollection()
        c.add_cdn_layer(CDNCacheLayer(provider="cloudflare"))
        assert len(c.cdn_layers) == 1
        assert c.cdn_layers[0].provider == "cloudflare"

    def test_set_stampede_prevention(self):
        c = CacheCollection()
        c.set_stampede_prevention(StampedePrevention(strategy=StampedePreventionStrategy.MUTEX))
        assert c.stampede_prevention is not None
        assert c.stampede_prevention.strategy == StampedePreventionStrategy.MUTEX

    def test_add_tier(self):
        c = CacheCollection()
        c.add_tier(CacheTier(tier_name="l1", tier_order=1))
        assert len(c.tiers) == 1

    def test_set_warmup_config(self):
        c = CacheCollection()
        c.set_warmup_config(CacheWarmupConfig(strategy=CacheWarmupStrategy.SCHEDULED))
        assert c.warmup_config.strategy == CacheWarmupStrategy.SCHEDULED

    def test_to_dict_full(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_cdn_layer(CDNCacheLayer(provider="cloudfront"))
        c.set_stampede_prevention(StampedePrevention())
        c.add_tier(CacheTier(tier_name="l1", tier_order=1))
        c.set_warmup_config(CacheWarmupConfig())
        d = c.to_dict()
        assert "cdn_layers" in d
        assert "stampede_prevention" in d
        assert "tiers" in d
        assert "warmup_config" in d

    def test_from_dict_full(self):
        d = {
            "profiles": [{"id": "p1", "backend": "redis"}],
            "cdn_layers": [{"provider": "fastly", "zone_id": "z1"}],
            "stampede_prevention": {"enabled": True, "strategy": "lease"},
            "tiers": [{"tier_name": "l1", "tier_order": 1}],
            "warmup_config": {"strategy": "background", "warmup_keys": ["k1"]},
        }
        c = CacheCollection.from_dict(d)
        assert len(c.profiles) == 1
        assert len(c.cdn_layers) == 1
        assert c.stampede_prevention.strategy == StampedePreventionStrategy.LEASE
        assert len(c.tiers) == 1
        assert c.warmup_config.strategy == CacheWarmupStrategy.BACKGROUND

    def test_round_trip(self):
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.MEMCACHED, ttl=600))
        c.add_strategy(CacheStrategy(profile_id="p1", strategy_type="write_through"))
        c.add_cdn_layer(CDNCacheLayer(provider="cloudflare"))
        c.set_stampede_prevention(StampedePrevention())
        c.add_tier(CacheTier(tier_name="l1", tier_order=1, backend="memory"))
        c.set_warmup_config(CacheWarmupConfig(strategy=CacheWarmupStrategy.ON_STARTUP))

        d = c.to_dict()
        c2 = CacheCollection.from_dict(d)
        assert c2.total_count == 1
        assert len(c2.cdn_layers) == 1
        assert c2.stampede_prevention is not None
        assert len(c2.tiers) == 1
        assert c2.warmup_config is not None
