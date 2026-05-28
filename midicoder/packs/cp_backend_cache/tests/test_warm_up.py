# coding: utf-8
"""
Comprehensive tests cho CP09 warm_up module.
"""

import pytest
from midicoder.packs.cp_backend_cache.warm_up import CacheWarmer, ScheduledWarmJob
from midicoder.packs.cp_backend_cache.models import CacheWarmConfig
from midicoder.packs.cp_backend_cache.providers.memory import MemoryCacheProvider


def run_async(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCacheWarmer:
    def setup_method(self):
        self.provider = MemoryCacheProvider()
        self.warmer = CacheWarmer(
            provider=self.provider,
            loader=lambda key: f"loaded_{key}",
            default_ttl=300,
        )

    def test_warm_keys_empty(self):
        result = run_async(self.warmer.warm_keys([]))
        assert result == {}

    def test_warm_single_key(self):
        result = run_async(self.warmer.warm_keys(["key1"]))
        assert result["key1"] is True

    def test_warm_multiple_keys(self):
        result = run_async(self.warmer.warm_keys(["k1", "k2", "k3"]))
        assert all(result.values())

    def test_warm_existing_key(self):
        run_async(self.provider.set("existing", "val"))
        result = run_async(self.warmer.warm_keys(["existing"]))
        assert result["existing"] is True

    def test_warm_with_config(self):
        config = CacheWarmConfig(profile_id="p1", keys=["a", "b"])
        result = run_async(self.warmer.warm_from_config(config))
        assert len(result) == 2

    def test_warm_batch_priority(self):
        c1 = CacheWarmConfig(profile_id="p1", keys=["high"], priority=1)
        c2 = CacheWarmConfig(profile_id="p2", keys=["low"], priority=10)
        result = run_async(self.warmer.warm_batch([c2, c1]))
        assert "p1" in result
        assert "p2" in result

    def test_warm_async_loader(self):
        async def async_loader(key):
            return f"async_{key}"
        warmer = CacheWarmer(provider=self.provider, loader=async_loader)
        result = run_async(warmer.warm_keys(["async_key"]))
        assert result["async_key"] is True

    def test_warm_pattern(self):
        def key_loader(*args):
            return ["pk1", "pk2"]
        count = run_async(self.warmer.warm_pattern(key_loader, []))
        assert count == 2


class TestScheduledWarmJob:
    def setup_method(self):
        self.provider = MemoryCacheProvider()
        self.warmer = CacheWarmer(
            provider=self.provider,
            loader=lambda key: f"val_{key}",
        )
        self.config = CacheWarmConfig(profile_id="p1", keys=["s1"], schedule="*/5 * * * *")
        self.job = ScheduledWarmJob(warmer=self.warmer, config=self.config)

    def test_initial_state(self):
        assert self.job.is_running is False
        assert self.job.last_run is None

    def test_run_now(self):
        result = run_async(self.job.run_now())
        assert "s1" in result
        assert self.job.last_run is not None

    def test_start_stop(self):
        async def test_start_stop():
            await self.job.start()
            assert self.job.is_running is True
            await self.job.stop()
            assert self.job.is_running is False
        run_async(test_start_stop())

    def test_start_already_running(self):
        async def test_double_start():
            await self.job.start()
            await self.job.start()  # Should not crash, just warn
            assert self.job.is_running is True
            await self.job.stop()
        run_async(test_double_start())
