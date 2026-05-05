# coding: utf-8
"""
Tests cho Cache Emitter module (P2-001-H).

Bao gom:
- Test Core Cache Models (CacheProfile, CacheStrategy, CacheInvalidationRule)
- Test Cache Parser (parse_from_metadata)
- Test FastAPI Cache Emitter (Redis + strategy rendering)
- Test NestJS Cache Emitter (CacheModule rendering)
- Test KPI-029 Tenant Isolation cho cache templates

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path

from midicoder.emitters.core.cache.models import (
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    InvalidationStrategy,
    CacheBackend,
    CacheCollection,
)
from midicoder.emitters.core.cache.parser import CacheParser
from midicoder.emitters.core.cache.fastapi import RedisEmitter
from midicoder.emitters.core.cache.nestjs import CacheModuleEmitter


# ============================================================================
# Test Core Cache Models
# ============================================================================


class TestCacheProfile:
    """Tests cho CacheProfile model."""

    def test_create_basic_profile(self):
        """Tao cache profile co ban."""
        profile = CacheProfile(
            id="default",
            backend=CacheBackend.REDIS,
            ttl=300,
        )
        assert profile.id == "default"
        assert profile.backend == CacheBackend.REDIS
        assert profile.ttl == 300

    def test_create_tenant_aware_profile(self):
        """Tao cache profile tenant-aware (KPI-029)."""
        profile = CacheProfile(
            id="tenant_cache",
            backend=CacheBackend.REDIS,
            ttl=600,
            tenant_isolated=True,
        )
        assert profile.tenant_isolated is True

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheProfile(
            id="session",
            backend=CacheBackend.REDIS,
            ttl=1800,
            max_size=10000,
            serializer="json",
            tenant_isolated=True,
        )
        d = original.to_dict()
        restored = CacheProfile.from_dict(d)
        assert restored.id == original.id
        assert restored.backend == original.backend
        assert restored.ttl == original.ttl
        assert restored.tenant_isolated == original.tenant_isolated


class TestCacheStrategy:
    """Tests cho CacheStrategy model."""

    def test_read_through_strategy(self):
        """Read-through strategy."""
        strategy = CacheStrategy(
            profile_id="default",
            strategy_type="read_through",
        )
        assert strategy.strategy_type == "read_through"

    def test_write_through_strategy(self):
        """Write-through strategy."""
        strategy = CacheStrategy(
            profile_id="default",
            strategy_type="write_through",
        )
        assert strategy.strategy_type == "write_through"

    def test_cache_aside_strategy(self):
        """Cache-aside strategy."""
        strategy = CacheStrategy(
            profile_id="default",
            strategy_type="cache_aside",
        )
        assert strategy.strategy_type == "cache_aside"

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = CacheStrategy(
            profile_id="default",
            strategy_type="read_through",
            load_from="db",
            tenant_scoped=True,
        )
        d = original.to_dict()
        restored = CacheStrategy.from_dict(d)
        assert restored.profile_id == original.profile_id
        assert restored.strategy_type == original.strategy_type
        assert restored.tenant_scoped == original.tenant_scoped


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

    def test_tenant_isolated_profiles(self):
        """Loc profiles co tenant isolation (KPI-029)."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="a", backend=CacheBackend.REDIS, tenant_isolated=True))
        collection.add_profile(CacheProfile(id="b", backend=CacheBackend.REDIS, tenant_isolated=False))
        result = collection.tenant_isolated_profiles()
        assert len(result) == 1

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


# ============================================================================
# Test FastAPI Cache Emitter
# ============================================================================


class TestRedisEmitter:
    """Tests cho RedisEmitter (FastAPI)."""

    def test_emit_creates_files(self, tmp_path: Path):
        """Emit tao cac file cache."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS, ttl=300))

        emitter = RedisEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)

    def test_emit_includes_tenant(self, tmp_path: Path):
        """Emit bao gom tenant prefix (KPI-029)."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="tenant", backend=CacheBackend.REDIS, tenant_isolated=True))

        emitter = RedisEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong."""
        emitter = RedisEmitter()
        files = emitter.emit(CacheCollection(), tmp_path)
        assert isinstance(files, dict)


# ============================================================================
# Test NestJS Cache Emitter
# ============================================================================


class TestCacheModuleEmitter:
    """Tests cho CacheModuleEmitter (NestJS)."""

    def test_emit_creates_module(self, tmp_path: Path):
        """Emit tao cache module."""
        collection = CacheCollection()
        collection.add_profile(CacheProfile(id="default", backend=CacheBackend.REDIS))

        emitter = CacheModuleEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong."""
        emitter = CacheModuleEmitter()
        files = emitter.emit(CacheCollection(), tmp_path)
        assert isinstance(files, dict)


# ============================================================================
# KPI-029 Tenant Isolation Tests
# ============================================================================


class TestKPI029CacheTenantIsolation:
    """Tests KPI-029: Tenant Isolation cho cache templates."""

    def test_fastapi_redis_template_has_tenant(self):
        """FastAPI redis.py.jinja2 co tenant key prefix."""
        template_path = Path("midicoder/stacks/fastapi/templates/cache/redis.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_cache_strategy_has_tenant(self):
        """FastAPI cache_strategy.py.jinja2 co tenant isolation."""
        template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_strategy.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_cache_decorators_has_tenant(self):
        """FastAPI cache_decorators.py.jinja2 co tenant support."""
        template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_decorators.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_cache_invalidate_has_tenant(self):
        """FastAPI cache_invalidate.py.jinja2 co tenant awareness."""
        template_path = Path("midicoder/stacks/fastapi/templates/cache/cache_invalidate.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_profile_default_tenant_isolated(self):
        """CacheProfile mac dinh tenant_isolated=True (KPI-029)."""
        profile = CacheProfile(id="test", backend=CacheBackend.REDIS)
        assert profile.tenant_isolated is True

    def test_strategy_default_tenant_scoped(self):
        """CacheStrategy mac dinh tenant_scoped=True (KPI-029)."""
        strategy = CacheStrategy(profile_id="test", strategy_type="read_through")
        assert strategy.tenant_scoped is True

    def test_invalidation_default_tenant_scoped(self):
        """CacheInvalidationRule mac dinh tenant_scoped=True (KPI-029)."""
        rule = CacheInvalidationRule(profile_id="test", pattern="*")
        assert rule.tenant_scoped is True

    def test_backend_enum_coverage(self):
        """CacheBackend enum co cac backend."""
        assert CacheBackend.REDIS.value == "redis"
        assert CacheBackend.MEMORY.value == "memory"

    def test_invalidation_strategy_enum_coverage(self):
        """InvalidationStrategy enum co cac strategies."""
        assert InvalidationStrategy.PATTERN.value == "pattern"
        assert InvalidationStrategy.TAG.value == "tag"
        assert InvalidationStrategy.EVENT.value == "event"

    def test_profile_with_all_attributes(self):
        """CacheProfile voi tat ca attributes."""
        profile = CacheProfile(
            id="full",
            backend=CacheBackend.REDIS,
            ttl=3600,
            max_size=50000,
            serializer="json",
            key_prefix="app",
            tenant_isolated=True,
            description="Profile day du",
        )
        d = profile.to_dict()
        restored = CacheProfile.from_dict(d)
        assert restored.max_size == 50000
        assert restored.serializer == "json"

    def test_full_collection_roundtrip(self):
        """Full roundtrip cho CacheCollection."""
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
        d = collection.to_dict()
        restored = CacheCollection.from_dict(d)
        assert restored.total_count == 1

    def test_all_fastapi_cache_templates_have_tenant(self):
        """Tat ca FastAPI cache templates co tenant reference."""
        cache_dir = Path("midicoder/stacks/fastapi/templates/cache")
        if cache_dir.exists():
            for template in cache_dir.glob("*.jinja2"):
                content = template.read_text(encoding="utf-8")
                assert "tenant" in content.lower(), f"Template {template.name} missing tenant reference"