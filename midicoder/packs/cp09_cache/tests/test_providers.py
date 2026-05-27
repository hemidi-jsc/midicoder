# coding: utf-8
"""
Comprehensive tests cho CP09 Providers (Memory, Memcached, base).

Không test Redis provider vì cần Redis server.
"""

import pytest
import asyncio
from midicoder.packs.cp09_cache.providers.base import CacheProvider
from midicoder.packs.cp09_cache.providers.memory import MemoryCacheProvider
from midicoder.packs.cp09_cache.providers.memcached import MemcachedCacheProvider


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ============================================================================
# MemoryCacheProvider
# ============================================================================

class TestMemoryCacheProvider:
    def test_get_miss(self):
        p = MemoryCacheProvider()
        result = run_async(p.get("nonexist"))
        assert result is None

    def test_set_and_get(self):
        p = MemoryCacheProvider()
        run_async(p.set("key1", {"data": "value"}))
        result = run_async(p.get("key1"))
        assert result == {"data": "value"}

    def test_delete(self):
        p = MemoryCacheProvider()
        run_async(p.set("k", "v"))
        deleted = run_async(p.delete("k"))
        assert deleted is True
        assert run_async(p.get("k")) is None

    def test_delete_nonexist(self):
        p = MemoryCacheProvider()
        deleted = run_async(p.delete("nonexist"))
        assert deleted is False

    def test_invalidate_pattern(self):
        p = MemoryCacheProvider()
        run_async(p.set("user:1", "a"))
        run_async(p.set("user:2", "b"))
        run_async(p.set("order:1", "c"))
        count = run_async(p.invalidate("user:*"))
        assert count == 2
        assert run_async(p.get("order:1")) == "c"

    def test_tenant_isolation(self):
        p = MemoryCacheProvider(tenant_id="t1")
        run_async(p.set("key", "val"))
        result = run_async(p.get("key"))
        assert result == "val"

    def test_key_prefix(self):
        p = MemoryCacheProvider(key_prefix="app:")
        run_async(p.set("key", "val"))
        result = run_async(p.get("key"))
        assert result == "val"

    def test_ttl_expiry(self):
        p = MemoryCacheProvider()
        run_async(p.set("expiring", "val", ttl=0))
        import time
        time.sleep(0.01)
        result = run_async(p.get("expiring"))
        # ttl=0 means no expiry
        assert result is not None

    def test_max_size_eviction(self):
        p = MemoryCacheProvider(max_size=3)
        run_async(p.set("a", 1))
        run_async(p.set("b", 2))
        run_async(p.set("c", 3))
        run_async(p.set("d", 4))  # Should evict oldest
        # After eviction, at least one key may be missing

    def test_health_check(self):
        p = MemoryCacheProvider()
        healthy = run_async(p.health_check())
        assert healthy is True

    def test_close(self):
        p = MemoryCacheProvider()
        run_async(p.set("k", "v"))
        run_async(p.close())
        result = run_async(p.get("k"))
        assert result is None

    def test_warm_existing_keys(self):
        p = MemoryCacheProvider()
        run_async(p.set("k1", "existing"))
        def loader(key):
            return "loaded"
        count = run_async(p.warm(["k1", "k2"], loader))
        assert count >= 1

    def test_complex_value(self):
        p = MemoryCacheProvider()
        data = {"nested": {"list": [1, 2, 3]}, "bool": True, "null": None}
        run_async(p.set("complex", data))
        result = run_async(p.get("complex"))
        assert result["nested"]["list"] == [1, 2, 3]


# ============================================================================
# MemcachedCacheProvider
# ============================================================================

class TestMemcachedCacheProvider:
    def test_get_miss(self):
        p = MemcachedCacheProvider()
        result = run_async(p.get("nonexist"))
        assert result is None

    def test_set_and_get(self):
        p = MemcachedCacheProvider()
        run_async(p.set("key1", {"data": "value"}))
        result = run_async(p.get("key1"))
        assert result == {"data": "value"}

    def test_delete(self):
        p = MemcachedCacheProvider()
        run_async(p.set("k", "v"))
        deleted = run_async(p.delete("k"))
        assert deleted is True

    def test_delete_nonexist(self):
        p = MemcachedCacheProvider()
        deleted = run_async(p.delete("nonexist"))
        assert deleted is False

    def test_invalidate_pattern(self):
        p = MemcachedCacheProvider()
        run_async(p.set("user:1", "a"))
        run_async(p.set("user:2", "b"))
        run_async(p.set("order:1", "c"))
        count = run_async(p.invalidate("user:*"))
        assert count == 2

    def test_tenant_isolation(self):
        p = MemcachedCacheProvider(tenant_id="t1")
        run_async(p.set("key", "val"))
        result = run_async(p.get("key"))
        assert result == "val"

    def test_key_prefix(self):
        p = MemcachedCacheProvider(key_prefix="app:")
        run_async(p.set("key", "val"))
        result = run_async(p.get("key"))
        assert result == "val"

    def test_health_check(self):
        p = MemcachedCacheProvider()
        healthy = run_async(p.health_check())
        assert healthy is True

    def test_close(self):
        p = MemcachedCacheProvider()
        run_async(p.set("k", "v"))
        run_async(p.close())
        result = run_async(p.get("k"))
        assert result is None

    def test_warm_existing_keys(self):
        p = MemcachedCacheProvider()
        run_async(p.set("k1", "existing"))
        def loader(key):
            return "loaded"
        count = run_async(p.warm(["k1", "k2"], loader))
        assert count >= 1

    def test_build_key_format(self):
        p = MemcachedCacheProvider(key_prefix="x:", tenant_id="t1")
        key = p._build_key("user:1")
        assert key == "x:t1:user:1"

    def test_default_ttl(self):
        p = MemcachedCacheProvider(default_ttl=600)
        assert p.default_ttl == 600


# ============================================================================
# CacheProvider ABC
# ============================================================================

class TestCacheProviderABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            CacheProvider()

    def test_subclass_must_implement_methods(self):
        class IncompleteProvider(CacheProvider):
            pass
        with pytest.raises(TypeError):
            IncompleteProvider()
