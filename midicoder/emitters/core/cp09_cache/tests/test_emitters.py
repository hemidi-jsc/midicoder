# coding: utf-8
"""
Comprehensive tests cho CP09 FastAPI và NestJS emitters.
"""

import pytest
from pathlib import Path
from midicoder.emitters.core.cp09_cache.fastapi import FastAPICacheEmitter
from midicoder.emitters.core.cp09_cache.nestjs import NestJSCacheEmitter
from midicoder.emitters.core.cp09_cache.models import (
    CacheCollection,
    CacheProfile,
    CacheBackend,
    CDNCacheLayer,
    StampedePrevention,
    StampedePreventionStrategy,
    CacheTier,
    CacheWarmupConfig,
    CacheWarmupStrategy,
)


# ============================================================================
# FastAPICacheEmitter
# ============================================================================

class TestFastAPICacheEmitter:
    def test_empty_collection(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        files = emitter.generate(c)
        assert files == {}

    def test_redis_emits_basic_files(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        assert "cache/redis.py" in files
        assert "cache/cache_strategy.py" in files
        assert "cache/cache_decorators.py" in files
        assert "cache/cache_invalidate.py" in files
        assert "cache/__init__.py" in files

    def test_memcached_emits_client(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.MEMCACHED))
        files = emitter.generate(c)
        # memcached emitter không có redis nhưng có strategy/decorators/invalidate
        assert "cache/cache_strategy.py" in files

    def test_both_backends(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="r1", backend=CacheBackend.REDIS))
        c.add_profile(CacheProfile(id="m1", backend=CacheBackend.MEMCACHED))
        files = emitter.generate(c)
        assert "cache/redis.py" in files
        assert "cache/memcached.py" in files

    def test_cdn_emits_cdn_file(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_cdn_layer(CDNCacheLayer(provider="cloudflare", zone_id="z1"))
        files = emitter.generate(c)
        assert "cache/cdn_cache.py" in files
        assert "cloudflare" in files["cache/cdn_cache.py"]

    def test_stampede_emits_file(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.set_stampede_prevention(StampedePrevention(strategy=StampedePreventionStrategy.MUTEX, lock_ttl=20))
        files = emitter.generate(c)
        assert "cache/stampede_prevention.py" in files
        assert "_DEFAULT_LOCK_TTL = 20" in files["cache/stampede_prevention.py"]

    def test_warmup_emits_file(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.set_warmup_config(CacheWarmupConfig(strategy=CacheWarmupStrategy.SCHEDULED, warmup_keys=["k1", "k2"]))
        files = emitter.generate(c)
        assert "cache/cache_warmup.py" in files
        assert "k1" in files["cache/cache_warmup.py"]

    def test_tiers_emit_file(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_tier(CacheTier(tier_name="l1", tier_order=1, backend="memory", ttl=60))
        c.add_tier(CacheTier(tier_name="l2", tier_order=2, backend="redis", ttl=300))
        files = emitter.generate(c)
        assert "cache/multi_tier.py" in files
        assert "l1" in files["cache/multi_tier.py"]
        assert "l2" in files["cache/multi_tier.py"]

    def test_redis_content_has_tenant_key(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        assert "get_key_with_tenant" in files["cache/redis.py"]

    def test_strategy_content_has_all_types(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        strat = files["cache/cache_strategy.py"]
        assert "ReadThroughStrategy" in strat
        assert "WriteThroughStrategy" in strat
        assert "CacheAsideStrategy" in strat

    def test_decorators_content(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        dec = files["cache/cache_decorators.py"]
        assert "def cache(" in dec
        assert "def cache_tenant(" in dec
        assert "def cache_disable(" in dec

    def test_full_emit(self):
        emitter = FastAPICacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        c.add_cdn_layer(CDNCacheLayer(provider="cloudfront"))
        c.set_stampede_prevention(StampedePrevention())
        c.set_warmup_config(CacheWarmupConfig(warmup_keys=["key1"]))
        c.add_tier(CacheTier(tier_name="l1", tier_order=1))
        files = emitter.generate(c)
        # Base: redis, strategy, decorators, invalidate, __init__
        # Extra: cdn, stampede, warmup, multi_tier
        assert len(files) >= 9


# ============================================================================
# NestJSCacheEmitter
# ============================================================================

class TestNestJSCacheEmitter:
    def test_empty_collection(self):
        emitter = NestJSCacheEmitter()
        c = CacheCollection()
        files = emitter.generate(c)
        assert files == {}

    def test_redis_emits_module(self):
        emitter = NestJSCacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        assert "cache/cache.module.ts" in files
        assert "cache/cache.service.ts" in files
        assert "cache/cache.interceptor.ts" in files

    def test_service_has_tenant_aware(self):
        emitter = NestJSCacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        assert "buildKey" in files["cache/cache.service.ts"]

    def test_interceptor_has_decorators(self):
        emitter = NestJSCacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        interceptor = files["cache/cache.interceptor.ts"]
        assert "CACHE_TTL" in interceptor
        assert "CACHE_KEY" in interceptor
        assert "CACHE_DISABLE" in interceptor

    def test_module_is_global(self):
        emitter = NestJSCacheEmitter()
        c = CacheCollection()
        c.add_profile(CacheProfile(id="p1", backend=CacheBackend.REDIS))
        files = emitter.generate(c)
        module = files["cache/cache.module.ts"]
        assert "@Global()" in module
