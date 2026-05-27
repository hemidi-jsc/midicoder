# coding: utf-8
"""
Comprehensive tests cho CP09 cache decorators.
"""

import pytest
from midicoder.packs.cp09_cache.cache_decorator import (
    cache,
    cache_tenant,
    cache_disable,
    clear_cache,
    _cache_store,
)


def run_async(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCacheDecorator:
    def setup_method(self):
        _cache_store.clear()

    def test_cache_basic(self):
        @cache(key="test_key", ttl=300)
        async def get_data():
            return {"data": "value"}

        result = run_async(get_data())
        assert result == {"data": "value"}

    def test_cache_repeats_call(self):
        call_count = 0

        @cache(key="count_key", ttl=300)
        async def count_calls():
            nonlocal call_count
            call_count += 1
            return call_count

        r1 = run_async(count_calls())
        r2 = run_async(count_calls())
        assert r1 == 1
        assert r2 == 1  # Cache hit, không gọi lại function

    def test_cache_auto_key(self):
        @cache()
        async def func_with_auto_key():
            return "auto"

        result = run_async(func_with_auto_key())
        assert result == "auto"

    def test_cache_disable(self):
        @cache_disable
        async def no_cache():
            return "no_cache"

        result = run_async(no_cache())
        assert result == "no_cache"
        assert hasattr(no_cache, "_cache_disabled") is True


class TestCacheTenant:
    def setup_method(self):
        _cache_store.clear()

    def test_cache_tenant_with_id(self):
        @cache_tenant(ttl=300)
        async def get_tenant_data(tenant_id="t1"):
            return {"tenant": tenant_id}

        result = run_async(get_tenant_data(tenant_id="t1"))
        assert result == {"tenant": "t1"}

    def test_cache_tenant_without_id(self):
        @cache_tenant(ttl=300)
        async def get_no_tenant():
            return {"no_tenant": True}

        result = run_async(get_no_tenant())
        assert result == {"no_tenant": True}


class TestClearCache:
    def setup_method(self):
        _cache_store.clear()

    def test_clear_all(self):
        _cache_store["key1"] = ("val1", 0)
        _cache_store["key2"] = ("val2", 0)
        count = clear_cache("*")
        assert count == 2
        assert len(_cache_store) == 0

    def test_clear_pattern(self):
        _cache_store["user:1"] = ("a", 0)
        _cache_store["user:2"] = ("b", 0)
        _cache_store["order:1"] = ("c", 0)
        count = clear_cache("user:*")
        assert count == 2
        assert "order:1" in _cache_store

    def test_clear_empty(self):
        count = clear_cache("*")
        assert count == 0
