# coding: utf-8
"""
Tests cho CP09 - Cache Emitter module.

Bao gom:
- Test Core Cache Models (5 definitions: CacheProfile, CacheStrategy, CacheInvalidationRule, CacheWarmConfig, CacheMetrics)
- Test Cache Parser (parse_from_metadata, parse YAML)
- Test FastAPI Cache Emitter (generate files)
- Test NestJS Cache Emitter (generate files)
- Test Providers (Redis, Memory)
- Test Decorators (@cache, @cache_tenant, @cache_disable)
- Test Warm-up (CacheWarmer, ScheduledWarmJob)
- Test KPI-029 Tenant Isolation
- Test Error Codes (MDC-CP09-001..005)
- Test Angular Templates
- Test React Templates

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from midicoder.packs.cp09_cache.models import (
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheWarmConfig,
    CacheMetrics,
    CacheBackend,
    InvalidationStrategy,
    CacheCollection,
)
from midicoder.packs.cp09_cache.parser import CacheParser
from midicoder.packs.cp09_cache.fastapi import FastAPICacheEmitter
from midicoder.packs.cp09_cache.nestjs import NestJSCacheEmitter
from midicoder.packs.cp09_cache.cache_decorator import (
    cache,
    cache_tenant,
    cache_disable,
    clear_cache,
)
from midicoder.packs.cp09_cache.warm_up import CacheWarmer
from midicoder.packs.cp09_cache.providers.redis import RedisCacheProvider
from midicoder.packs.cp09_cache.providers.memory import MemoryCacheProvider
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Core Cache Models (5 definitions)
# ============================================================================


class TestCacheProfile:
    """Tests cho CacheProfile model."""

    def test_create_basic_profile(self):
        """Tao cache profile co ban."""
        profile = CacheProfile(id="default", backend=CacheBackend.REDIS)
        assert profile.id == "default"
        assert profile.backend == CacheBackend.REDIS
        assert profile.ttl == 300
        assert profile.tenant_isolated is True

    def test_create_memory_profile(self):
        """Tao memory cache profile."""
        profile = CacheProfile(
            id="local",
            backend=CacheBackend.MEMORY,
            ttl=600,
            max_size=5000,
        )
        assert profile.backend == CacheBackend.MEMORY
        assert profile.max_size == 5000

    def test_tenant_isolated_default_true(self):
        """CacheProfile mac dinh tenant_isolated=True (KPI-029)."""
        profile = CacheProfile(id="test", backend=CacheBackend.REDIS)
        assert profile.tenant_isolated is True

    def test_ttl_validation_must_be_positive(self):
        """TTL phai lon hon 0."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheProfile(id="bad", backend=CacheBackend.REDIS, ttl=0)
        assert exc_info.value.code.value == ErrorCode.CP09_TTL_INVALID.value

    def test_ttl_negative_raises_error(self):
        """TTL am phai raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheProfile(id="bad", backend=CacheBackend.REDIS, ttl=-100)
        assert exc_info.value.code.value == ErrorCode.CP09_TTL_INVALID.value

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheProfile(
            id="session",
            backend=CacheBackend.REDIS,
            ttl=1800,
            max_size=10000,
            serializer="json",
            key_prefix="app:",
            tenant_isolated=True,
            description="Session cache",
        )
        d = original.to_dict()
        restored = CacheProfile.from_dict(d)
        assert restored.id == original.id
        assert restored.backend == original.backend
        assert restored.ttl == original.ttl
        assert restored.max_size == original.max_size
        assert restored.tenant_isolated == original.tenant_isolated
        assert restored.key_prefix == original.key_prefix

    def test_all_attributes(self):
        """CacheProfile voi tat ca attributes."""
        profile = CacheProfile(
            id="full",
            backend=CacheBackend.REDIS,
            ttl=3600,
            max_size=50000,
            serializer="pickle",
            key_prefix="prod:",
            tenant_isolated=True,
            description="Profile day du",
        )
        assert profile.max_size == 50000
        assert profile.serializer == "pickle"
        assert profile.key_prefix == "prod:"


class TestCacheStrategy:
    """Tests cho CacheStrategy model."""

    def test_read_through_strategy(self):
        """Read-through strategy."""
        strategy = CacheStrategy(
            profile_id="default",
            strategy_type="read_through",
        )
        assert strategy.strategy_type == "read_through"
        assert strategy.tenant_scoped is True

    def test_write_through_strategy(self):
        """Write-through strategy."""
        strategy = CacheStrategy(
            profile_id="default",
            strategy_type="write_through",
        )
        assert strategy.strategy_type == "write_through"

    def test_cache_aside_strategy(self):
        """Cache-aside strategy (mac dinh)."""
        strategy = CacheStrategy(profile_id="default")
        assert strategy.strategy_type == "cache_aside"

    def test_invalid_strategy_raises_error(self):
        """Strategy loai khong hop le."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheStrategy(
                profile_id="bad",
                strategy_type="invalid_type",
            )
        assert exc_info.value.code.value == ErrorCode.CP09_PATTERN_INVALID.value

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheStrategy(
            profile_id="default",
            strategy_type="read_through",
            load_from="db",
            tenant_scoped=True,
            description="Read through strategy",
        )
        d = original.to_dict()
        restored = CacheStrategy.from_dict(d)
        assert restored.profile_id == original.profile_id
        assert restored.strategy_type == original.strategy_type
        assert restored.load_from == original.load_from


class TestCacheInvalidationRule:
    """Tests cho CacheInvalidationRule model."""

    def test_pattern_invalidation(self):
        """Pattern-based invalidation."""
        rule = CacheInvalidationRule(
            profile_id="default",
            pattern="user:*",
            strategy=InvalidationStrategy.PATTERN,
        )
        assert rule.pattern == "user:*"
        assert rule.strategy == InvalidationStrategy.PATTERN

    def test_tag_invalidation(self):
        """Tag-based invalidation."""
        rule = CacheInvalidationRule(
            profile_id="default",
            tags=["user", "profile"],
            strategy=InvalidationStrategy.TAG,
        )
        assert "user" in rule.tags
        assert rule.strategy == InvalidationStrategy.TAG

    def test_event_invalidation(self):
        """Event-based invalidation."""
        rule = CacheInvalidationRule(
            profile_id="default",
            events=["user.updated", "user.deleted"],
            strategy=InvalidationStrategy.EVENT,
        )
        assert "user.updated" in rule.events

    def test_pattern_strategy_requires_pattern(self):
        """Pattern strategy phai co pattern."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheInvalidationRule(
                profile_id="bad",
                pattern="",
                strategy=InvalidationStrategy.PATTERN,
            )
        assert exc_info.value.code.value == ErrorCode.CP09_PATTERN_INVALID.value

    def test_tag_strategy_requires_tags(self):
        """Tag strategy phai co tags."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheInvalidationRule(
                profile_id="bad",
                tags=[],
                strategy=InvalidationStrategy.TAG,
            )
        assert exc_info.value.code.value == ErrorCode.CP09_PATTERN_INVALID.value

    def test_event_strategy_requires_events(self):
        """Event strategy phai co events."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheInvalidationRule(
                profile_id="bad",
                events=[],
                strategy=InvalidationStrategy.EVENT,
            )
        assert exc_info.value.code.value == ErrorCode.CP09_PATTERN_INVALID.value

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheInvalidationRule(
            profile_id="default",
            pattern="order:*",
            strategy=InvalidationStrategy.PATTERN,
            tenant_scoped=True,
        )
        d = original.to_dict()
        restored = CacheInvalidationRule.from_dict(d)
        assert restored.profile_id == original.profile_id
        assert restored.pattern == original.pattern
        assert restored.tenant_scoped == original.tenant_scoped


class TestCacheWarmConfig:
    """Tests cho CacheWarmConfig model (definition #4)."""

    def test_warm_config_with_keys(self):
        """Tao warm config voi keys."""
        config = CacheWarmConfig(
            profile_id="default",
            keys=["user:1", "user:2", "user:3"],
        )
        assert len(config.keys) == 3
        assert config.priority == 5

    def test_warm_config_with_pattern(self):
        """Tao warm config voi pattern."""
        config = CacheWarmConfig(
            profile_id="default",
            pattern="product:*",
            schedule="0 */5 * * *",
            priority=1,
        )
        assert config.pattern == "product:*"
        assert config.priority == 1

    def test_warm_config_requires_keys_or_pattern(self):
        """Warm config phai co keys hoac pattern."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheWarmConfig(profile_id="bad", keys=[], pattern="")
        assert exc_info.value.code.value == ErrorCode.CP09_KEY_EMPTY.value

    def test_priority_range_validation(self):
        """Priority phai trong range 1-10."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheWarmConfig(
                profile_id="bad",
                keys=["test"],
                priority=15,
            )
        assert exc_info.value.code.value == ErrorCode.CP09_PATTERN_INVALID.value

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheWarmConfig(
            profile_id="default",
            keys=["user:1"],
            schedule="0 * * * *",
            priority=3,
            tenant_scoped=True,
            description="Warm user cache",
        )
        d = original.to_dict()
        restored = CacheWarmConfig.from_dict(d)
        assert restored.keys == original.keys
        assert restored.priority == original.priority
        assert restored.schedule == original.schedule


class TestCacheMetrics:
    """Tests cho CacheMetrics model (definition #5)."""

    def test_create_metrics(self):
        """Tao metrics co ban."""
        metrics = CacheMetrics(
            profile_id="default",
            hit_count=100,
            miss_count=10,
        )
        assert metrics.hit_count == 100
        assert metrics.miss_count == 10

    def test_hit_rate_calculation(self):
        """Tinh hit rate."""
        metrics = CacheMetrics(
            profile_id="default",
            hit_count=90,
            miss_count=10,
        )
        assert metrics.hit_rate == 90.0

    def test_hit_rate_zero_when_no_requests(self):
        """Hit rate = 0 khi khong co request."""
        metrics = CacheMetrics(profile_id="default")
        assert metrics.hit_rate == 0.0

    def test_negative_counts_raise_error(self):
        """Counts am phai raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            CacheMetrics(
                profile_id="bad",
                hit_count=-1,
            )
        assert exc_info.value.code.value == ErrorCode.CP09_TTL_INVALID.value

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheMetrics(
            profile_id="default",
            hit_count=500,
            miss_count=50,
            eviction_count=10,
            avg_latency_ms=2.5,
            peak_memory_mb=128.0,
        )
        d = original.to_dict()
        restored = CacheMetrics.from_dict(d)
        assert restored.hit_count == original.hit_count
        assert restored.eviction_count == original.eviction_count
        assert restored.avg_latency_ms == original.avg_latency_ms


class TestCacheCollection:
    """Tests cho CacheCollection."""

    def test_add_profile_and_count(self):
        """Them profile va dem."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))
        assert collection.total_count == 1

    def test_get_by_id(self):
        """Tim profile theo ID."""
        collection = CacheCollection()
        profile = CacheProfile(id="session", backend=CacheBackend.REDIS, ttl=1800)
        collection.add_profile(profile)
        found = collection.get_by_id("session")
        assert found is not None
        assert found.ttl == 1800

    def test_get_by_id_not_found(self):
        """Tim profile khong ton tai."""
        collection = CacheCollection()
        found = collection.get_by_id("nonexistent")
        assert found is None

    def test_tenant_isolated_profiles(self):
        """Loc profiles co tenant isolation (KPI-029)."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="a", backend=CacheBackend.REDIS, tenant_isolated=True))
        collection.add_profile(CacheProfile(id="b", backend=CacheBackend.REDIS, tenant_isolated=False))
        result = collection.tenant_isolated_profiles()
        assert len(result) == 1

    def test_redis_profiles_filter(self):
        """Loc Redis profiles."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="r", backend=CacheBackend.REDIS))
        collection.add_profile(CacheProfile(id="m", backend=CacheBackend.MEMORY))
        assert len(collection.redis_profiles()) == 1

    def test_memory_profiles_filter(self):
        """Loc Memory profiles."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="r", backend=CacheBackend.REDIS))
        collection.add_profile(CacheProfile(id="m", backend=CacheBackend.MEMORY))
        assert len(collection.memory_profiles()) == 1

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS, ttl=300))
        d = collection.to_dict()
        restored = CacheCollection.from_dict(d)
        assert restored.total_count == 1


# ============================================================================
# Test Cache Parser
# ============================================================================


class TestCacheParser:
    """Tests cho CacheParser."""

    def test_parse_profiles(self):
        """Parse cache profiles tu metadata."""
        parser = CacheParser()
        metadata = {
            "cache_profiles": [
                {
                    "id": "default",
                    "backend": "redis",
                    "ttl": 300,
                    "tenant_isolated": True,
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 1

    def test_parse_empty_metadata(self):
        """Parse empty metadata."""
        parser = CacheParser()
        collection = parser.parse_from_metadata({})
        assert collection.total_count == 0

    def test_parse_strategies(self):
        """Parse strategies."""
        parser = CacheParser()
        metadata = {
            "cache_profiles": [{"id": "default", "backend": "redis"}],
            "strategies": [
                {"profile_id": "default", "strategy_type": "read_through"}
            ],
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.strategies) == 1

    def test_parse_invalidation_rules(self):
        """Parse invalidation rules."""
        parser = CacheParser()
        metadata = {
            "cache_profiles": [{"id": "default", "backend": "redis"}],
            "invalidation_rules": [
                {"profile_id": "default", "pattern": "user:*", "strategy": "pattern"}
            ],
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.invalidation_rules) == 1

    def test_parse_warm_configs(self):
        """Parse warm configs."""
        parser = CacheParser()
        metadata = {
            "cache_profiles": [{"id": "default", "backend": "redis"}],
            "warm_configs": [
                {"profile_id": "default", "keys": ["user:1"], "priority": 1}
            ],
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.warm_configs) == 1

    def test_parse_metrics(self):
        """Parse metrics."""
        parser = CacheParser()
        metadata = {
            "cache_profiles": [{"id": "default", "backend": "redis"}],
            "metrics": [
                {"profile_id": "default", "hit_count": 100, "miss_count": 10}
            ],
        }
        collection = parser.parse_from_metadata(metadata)
        assert len(collection.metrics) == 1


# ============================================================================
# Test FastAPI Cache Emitter
# ============================================================================


class TestFastAPICacheEmitter:
    """Tests cho FastAPICacheEmitter."""

    def test_emit_creates_files(self):
        """Emit tao cac file cache."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS, ttl=300))

        emitter = FastAPICacheEmitter()
        files = emitter.generate(collection)
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_emit_includes_tenant(self):
        """Emit bao gom tenant prefix (KPI-029)."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="tenant", backend=CacheBackend.REDIS, tenant_isolated=True))

        emitter = FastAPICacheEmitter()
        files = emitter.generate(collection)
        all_content = "\n".join(files.values())
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self):
        """Emit voi collection rong."""
        emitter = FastAPICacheEmitter()
        files = emitter.generate(CacheCollection())
        assert isinstance(files, dict)
        assert len(files) == 0

    def test_emit_has_redis_file(self):
        """Emit co redis.py khi co Redis profile."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = FastAPICacheEmitter()
        files = emitter.generate(collection)
        assert "cache/redis.py" in files

    def test_emit_has_strategy_file(self):
        """Emit co cache_strategy.py."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = FastAPICacheEmitter()
        files = emitter.generate(collection)
        assert "cache/cache_strategy.py" in files


# ============================================================================
# Test NestJS Cache Emitter
# ============================================================================


class TestNestJSCacheEmitter:
    """Tests cho NestJSCacheEmitter."""

    def test_emit_creates_module(self):
        """Emit tao cache module."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = NestJSCacheEmitter()
        files = emitter.generate(collection)
        assert isinstance(files, dict)
        assert len(files) > 0

    def test_emit_has_cache_service(self):
        """Emit co cache service."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = NestJSCacheEmitter()
        files = emitter.generate(collection)
        assert "cache/cache.service.ts" in files

    def test_emit_empty_collection(self):
        """Emit voi collection rong."""
        emitter = NestJSCacheEmitter()
        files = emitter.generate(CacheCollection())
        assert isinstance(files, dict)
        assert len(files) == 0

    def test_emit_includes_tenant(self):
        """Emit bao gom tenant prefix (KPI-029)."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = NestJSCacheEmitter()
        files = emitter.generate(collection)
        all_content = "\n".join(files.values())
        assert "tenantId" in all_content


# ============================================================================
# Test Cache Decorators
# ============================================================================


class TestCacheDecorators:
    """Tests cho cache decorators."""

    def test_cache_decorator_applies(self):
        """Cache decorator apply vao function."""
        @cache(key="test", ttl=300)
        async def dummy():
            return "value"

        # Deo decorator ton tai
        assert callable(dummy)

    def test_cache_tenant_decorator_applies(self):
        """Cache tenant decorator apply vao function."""
        @cache_tenant(ttl=300)
        async def dummy():
            return "value"

        assert callable(dummy)

    def test_cache_disable_decorator_sets_marker(self):
        """Cache disable decorator dat marker."""
        @cache_disable
        async def dummy():
            return "value"

        assert hasattr(dummy, "_cache_disabled")
        assert dummy._cache_disabled is True

    def test_clear_cache(self):
        """Clear cache."""
        count = clear_cache("*")
        assert isinstance(count, int)


# ============================================================================
# Test Memory Provider
# ============================================================================


class TestMemoryCacheProvider:
    """Tests cho MemoryCacheProvider."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Set va get data."""
        provider = MemoryCacheProvider()
        await provider.set("key1", {"data": "value"}, ttl=300)
        result = await provider.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_delete(self):
        """Xoa data."""
        provider = MemoryCacheProvider()
        await provider.set("key1", "value")
        deleted = await provider.delete("key1")
        assert deleted is True
        assert await provider.get("key1") is None

    @pytest.mark.asyncio
    async def test_tenant_isolation(self):
        """Tenant isolation (KPI-029)."""
        provider = MemoryCacheProvider(tenant_id="tenant-a")
        await provider.set("key1", "value-a")
        result = await provider.get("key1")
        assert result == "value-a"

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Health check luon healthy."""
        provider = MemoryCacheProvider()
        assert await provider.health_check() is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Close provider."""
        provider = MemoryCacheProvider()
        await provider.close()
        assert len(provider._store) == 0


# ============================================================================
# Test CacheWarmConfig
# ============================================================================


class TestCacheWarmer:
    """Tests cho CacheWarmer."""

    @pytest.mark.asyncio
    async def test_warm_keys(self):
        """Warm keys thanh cong."""
        provider = MemoryCacheProvider()

        async def loader(key):
            return {"key": key, "loaded": True}

        warmer = CacheWarmer(provider, loader, default_ttl=300)
        results = await warmer.warm_keys(["key1", "key2"])

        assert results["key1"] is True
        assert results["key2"] is True


# ============================================================================
# KPI-029 Tenant Isolation Tests
# ============================================================================


class TestKPI029TenantIsolation:
    """Tests KPI-029: Tenant Isolation cho cache."""

    def test_profile_default_tenant_isolated(self):
        """CacheProfile mac dinh tenant_isolated=True."""
        profile = CacheProfile(id="test", backend=CacheBackend.REDIS)
        assert profile.tenant_isolated is True

    def test_strategy_default_tenant_scoped(self):
        """CacheStrategy mac dinh tenant_scoped=True."""
        strategy = CacheStrategy(profile_id="test")
        assert strategy.tenant_scoped is True

    def test_invalidation_default_tenant_scoped(self):
        """CacheInvalidationRule mac dinh tenant_scoped=True."""
        rule = CacheInvalidationRule(profile_id="test", pattern="*")
        assert rule.tenant_scoped is True

    def test_warm_config_default_tenant_scoped(self):
        """CacheWarmConfig mac dinh tenant_scoped=True."""
        config = CacheWarmConfig(profile_id="test", keys=["test"])
        assert config.tenant_scoped is True

    def test_metrics_default_tenant_scoped(self):
        """CacheMetrics mac dinh tenant_scoped=True."""
        metrics = CacheMetrics(profile_id="test")
        assert metrics.tenant_scoped is True

    def test_backend_enum_coverage(self):
        """CacheBackend enum co cac backends."""
        assert CacheBackend.REDIS.value == "redis"
        assert CacheBackend.MEMORY.value == "memory"

    def test_invalidation_strategy_enum_coverage(self):
        """InvalidationStrategy enum co cac strategies."""
        assert InvalidationStrategy.PATTERN.value == "pattern"
        assert InvalidationStrategy.TAG.value == "tag"
        assert InvalidationStrategy.EVENT.value == "event"


# ============================================================================
# Test Angular Templates
# ============================================================================


class TestAngularCacheTemplates:
    """Tests cho Angular cache templates."""

    def test_cache_service_template_exists(self):
        """Cache service template ton tai."""
        template_path = Path("midicoder/stacks/angular/cp09_cache/cache.service.ts.jinja2")
        assert template_path.exists()

    def test_cache_service_has_tenant(self):
        """Cache service co tenant reference."""
        template_path = Path("midicoder/stacks/angular/cp09_cache/cache.service.ts.jinja2")
        content = template_path.read_text(encoding="utf-8")
        assert "tenantId" in content

    def test_cache_interceptor_template_exists(self):
        """Cache interceptor template ton tai."""
        template_path = Path("midicoder/stacks/angular/cp09_cache/cache.interceptor.ts.jinja2")
        assert template_path.exists()

    def test_cache_module_template_exists(self):
        """Cache module template ton tai."""
        template_path = Path("midicoder/stacks/angular/cp09_cache/cache.module.ts.jinja2")
        assert template_path.exists()


# ============================================================================
# Test React Templates
# ============================================================================


class TestReactCacheTemplates:
    """Tests cho React cache templates."""

    def test_use_cache_template_exists(self):
        """useCache template ton tai."""
        template_path = Path("midicoder/stacks/react/cp09_cache/useCache.ts.jinja2")
        assert template_path.exists()

    def test_use_cache_has_tenant(self):
        """useCache co tenant reference."""
        template_path = Path("midicoder/stacks/react/cp09_cache/useCache.ts.jinja2")
        content = template_path.read_text(encoding="utf-8")
        assert "tenantId" in content

    def test_cache_provider_template_exists(self):
        """CacheProvider template ton tai."""
        template_path = Path("midicoder/stacks/react/cp09_cache/CacheProvider.tsx.jinja2")
        assert template_path.exists()

    def test_cache_utils_template_exists(self):
        """cacheUtils template ton tai."""
        template_path = Path("midicoder/stacks/react/cp09_cache/cache-utils.ts.jinja2")
        assert template_path.exists()


# ============================================================================
# Test Error Codes
# ============================================================================


class TestCP09ErrorCodes:
    """Tests cho CP09 error codes."""

    def test_cp09_backend_invalid_exists(self):
        """CP09_BACKEND_INVALID ton tai."""
        assert hasattr(ErrorCode, "CP09_BACKEND_INVALID")
        assert ErrorCode.CP09_BACKEND_INVALID.value == "MDC-CP09-001"

    def test_cp09_ttl_invalid_exists(self):
        """CP09_TTL_INVALID ton tai."""
        assert hasattr(ErrorCode, "CP09_TTL_INVALID")
        assert ErrorCode.CP09_TTL_INVALID.value == "MDC-CP09-002"

    def test_cp09_key_empty_exists(self):
        """CP09_KEY_EMPTY ton tai."""
        assert hasattr(ErrorCode, "CP09_KEY_EMPTY")
        assert ErrorCode.CP09_KEY_EMPTY.value == "MDC-CP09-003"

    def test_cp09_pattern_invalid_exists(self):
        """CP09_PATTERN_INVALID ton tai."""
        assert hasattr(ErrorCode, "CP09_PATTERN_INVALID")
        assert ErrorCode.CP09_PATTERN_INVALID.value == "MDC-CP09-004"

    def test_cp09_serialization_failed_exists(self):
        """CP09_SERIALIZATION_FAILED ton tai."""
        assert hasattr(ErrorCode, "CP09_SERIALIZATION_FAILED")
        assert ErrorCode.CP09_SERIALIZATION_FAILED.value == "MDC-CP09-005"


# ============================================================================
# Test Pack.yml
# ============================================================================


class TestPackYml:
    """Tests cho pack.yml."""

    def test_pack_yml_exists(self):
        """pack.yml ton tai."""
        pack_path = Path("midicoder/packs/cp09_cache/pack.yml")
        assert pack_path.exists()

    def test_changelog_exists(self):
        """CHANGELOG.md ton tai."""
        changelog_path = Path("midicoder/packs/cp09_cache/CHANGELOG.md")
        assert changelog_path.exists()


# ============================================================================
# Full Collection Roundtrip
# ============================================================================


class TestFullCollection:
    """Tests cho full CacheCollection."""

    def test_full_collection_roundtrip(self):
        """Full roundtrip cho CacheCollection voi tat ca definitions."""
        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="main", backend=CacheBackend.REDIS, ttl=300, tenant_isolated=True)
        )
        collection.add_strategy(
            CacheStrategy(profile_id="main", strategy_type="read_through", tenant_scoped=True)
        )
        collection.add_invalidation_rule(
            CacheInvalidationRule(profile_id="main", pattern="main:*", tenant_scoped=True)
        )
        collection.add_warm_config(
            CacheWarmConfig(profile_id="main", keys=["main:1"], priority=1)
        )
        collection.add_metrics(
            CacheMetrics(profile_id="main", hit_count=100, miss_count=10)
        )

        d = collection.to_dict()
        restored = CacheCollection.from_dict(d)

        assert restored.total_count == 1
        assert len(restored.strategies) == 1
        assert len(restored.invalidation_rules) == 1
        assert len(restored.warm_configs) == 1
        assert len(restored.metrics) == 1


# ============================================================================
# Test Angular Cache Emitter
# ============================================================================


class TestAngularCacheEmitter:
    """Tests cho Angular cache emitter."""

    def test_angular_emitter_import(self):
        """AngularEmitter co the import."""
        from midicoder.packs.cp09_cache.angular import AngularEmitter
        assert AngularEmitter is not None

    def test_angular_emitter_emit_files(self, tmp_path):
        """Emit tao cac file cache cho Angular."""
        from midicoder.packs.cp09_cache.angular import AngularEmitter

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS, ttl=300)
        )

        emitter = AngularEmitter(stack_dir=Path("midicoder/stacks/angular"))
        files = emitter.emit(collection, tmp_path)

        assert len(files) > 0
        paths = [f.path.name for f in files]
        assert "cache.service.ts" in paths
        assert "cache.interceptor.ts" in paths
        assert "cache.module.ts" in paths

    def test_angular_emitter_has_tenant(self, tmp_path):
        """Emit bao gom tenant reference (KPI-029)."""
        from midicoder.packs.cp09_cache.angular import AngularEmitter

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS)
        )

        emitter = AngularEmitter(stack_dir=Path("midicoder/stacks/angular"))
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "tenantId" in all_content or "tenant_id" in all_content

    def test_angular_emitter_empty_raises(self):
        """Emit voi collection rong phai raise error."""
        from midicoder.packs.cp09_cache.angular import AngularEmitter

        emitter = AngularEmitter(stack_dir=Path("midicoder/stacks/angular"))
        with pytest.raises(MidicoderError):
            emitter.emit(CacheCollection(), Path("/tmp"))


# ============================================================================
# Test React Cache Emitter
# ============================================================================


class TestReactCacheEmitter:
    """Tests cho React cache emitter."""

    def test_react_emitter_import(self):
        """ReactEmitter co the import."""
        from midicoder.packs.cp09_cache.react import ReactEmitter
        assert ReactEmitter is not None

    def test_react_emitter_emit_files(self, tmp_path):
        """Emit tao cac file cache cho React."""
        from midicoder.packs.cp09_cache.react import ReactEmitter

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS, ttl=300)
        )

        emitter = ReactEmitter(stack_dir=Path("midicoder/stacks/react"))
        files = emitter.emit(collection, tmp_path)

        assert len(files) > 0
        paths = [f.path.name for f in files]
        assert "CacheProvider.tsx" in paths
        assert "useCache.ts" in paths
        assert "cache-utils.ts" in paths
        assert "cache.types.ts" in paths

    def test_react_emitter_has_tenant(self, tmp_path):
        """Emit bao gom tenant reference (KPI-029)."""
        from midicoder.packs.cp09_cache.react import ReactEmitter

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS)
        )

        emitter = ReactEmitter(stack_dir=Path("midicoder/stacks/react"))
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "tenantId" in all_content or "tenant_id" in all_content

    def test_react_emitter_empty_raises(self):
        """Emit voi collection rong phai raise error."""
        from midicoder.packs.cp09_cache.react import ReactEmitter

        emitter = ReactEmitter(stack_dir=Path("midicoder/stacks/react"))
        with pytest.raises(MidicoderError):
            emitter.emit(CacheCollection(), Path("/tmp"))


# ============================================================================
# Test Convenience Functions
# ============================================================================


class TestConvenienceFunctions:
    """Tests cho convenience functions."""

    def test_emit_angular_cache_function(self, tmp_path):
        """emit_angular_cache function co the goi duoc."""
        from midicoder.packs.cp09_cache import emit_angular_cache

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS)
        )

        files = emit_angular_cache(
            collection,
            stack_dir=Path("midicoder/stacks/angular"),
            output_dir=tmp_path,
        )
        assert len(files) > 0

    def test_emit_react_cache_function(self, tmp_path):
        """emit_react_cache function co the goi duoc."""
        from midicoder.packs.cp09_cache import emit_react_cache

        collection = CacheCollection()
        collection.add_profile(
            CacheProfile(id="default", backend=CacheBackend.REDIS)
        )

        files = emit_react_cache(
            collection,
            stack_dir=Path("midicoder/stacks/react"),
            output_dir=tmp_path,
        )
        assert len(files) > 0
