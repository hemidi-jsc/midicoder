# coding: utf-8
"""
Mô-đun models cho Cache Emitter (CP09).

Định nghĩa các dataclass biểu diễn:
- CacheBackend/InvalidationStrategy: Enum các backend và strategies
- CacheProfile: Profile cache với backend, TTL, max_size, tenant_isolated
- CacheStrategy: Strategy caching (read_through, write_through, cache_aside)
- CacheInvalidationRule: Quy tắc invalidation (pattern, tag, event)
- CacheCollection: Collection chứa tất cả cache profiles

KPI-029: Tenant Isolation - tenant_isolated=True mặc định

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# Enums
# ===========================================================================


class CacheBackend(str, Enum):
    """Enum các cache backends."""
    REDIS = "redis"
    MEMORY = "memory"


class InvalidationStrategy(str, Enum):
    """Enum các strategies cho cache invalidation."""
    PATTERN = "pattern"
    TAG = "tag"
    EVENT = "event"


# ===========================================================================
# CacheProfile
# ===========================================================================


@dataclass
class CacheProfile:
    """
    Profile định nghĩa cấu hình cache.

    Attributes:
        id: Định danh duy nhất của profile
        backend: Backend cache (REDIS, MEMORY)
        ttl: Time-to-live mặc định (giây)
        max_size: Kích thước tối đa của cache
        serializer: Serializer cho cache data (json, pickle)
        key_prefix: Prefix cho cache keys
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        description: Mô tả profile
    """
    id: str
    backend: CacheBackend
    ttl: int = 300
    max_size: int | None = None
    serializer: str = "json"
    key_prefix: str = ""
    tenant_isolated: bool = True  # KPI-029
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển profile sang dict format."""
        return {
            "id": self.id,
            "backend": self.backend.value,
            "ttl": self.ttl,
            "max_size": self.max_size,
            "serializer": self.serializer,
            "key_prefix": self.key_prefix,
            "tenant_isolated": self.tenant_isolated,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheProfile":
        """Tạo CacheProfile từ dict."""
        return cls(
            id=data.get("id", ""),
            backend=CacheBackend(data.get("backend", "redis")),
            ttl=data.get("ttl", 300),
            max_size=data.get("max_size"),
            serializer=data.get("serializer", "json"),
            key_prefix=data.get("key_prefix", ""),
            tenant_isolated=data.get("tenant_isolated", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CacheStrategy
# ===========================================================================


@dataclass
class CacheStrategy:
    """
    Strategy cho caching pattern.

    Attributes:
        profile_id: ID của cache profile
        strategy_type: Loại strategy (read_through, write_through, cache_aside)
        load_from: Nguồn data khi cache miss (db, api)
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        description: Mô tả strategy
    """
    profile_id: str
    strategy_type: str = "cache_aside"
    load_from: str = ""
    tenant_scoped: bool = True  # KPI-029
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển strategy sang dict format."""
        return {
            "profile_id": self.profile_id,
            "strategy_type": self.strategy_type,
            "load_from": self.load_from,
            "tenant_scoped": self.tenant_scoped,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheStrategy":
        """Tạo CacheStrategy từ dict."""
        return cls(
            profile_id=data.get("profile_id", ""),
            strategy_type=data.get("strategy_type", "cache_aside"),
            load_from=data.get("load_from", ""),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CacheInvalidationRule
# ===========================================================================


@dataclass
class CacheInvalidationRule:
    """
    Quy tắc cho cache invalidation.

    Attributes:
        profile_id: ID của cache profile
        pattern: Pattern để match cache keys (chuẩn glob)
        tags: Danh sách tags để invalidate
        events: Danh sách events trigger invalidation
        strategy: Loại invalidation strategy (PATTERN, TAG, EVENT)
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        description: Mô tả rule
    """
    profile_id: str
    pattern: str = ""
    tags: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    strategy: InvalidationStrategy = InvalidationStrategy.PATTERN
    tenant_scoped: bool = True  # KPI-029
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển rule sang dict format."""
        return {
            "profile_id": self.profile_id,
            "pattern": self.pattern,
            "tags": self.tags,
            "events": self.events,
            "strategy": self.strategy.value,
            "tenant_scoped": self.tenant_scoped,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheInvalidationRule":
        """Tạo CacheInvalidationRule từ dict."""
        return cls(
            profile_id=data.get("profile_id", ""),
            pattern=data.get("pattern", ""),
            tags=data.get("tags", []),
            events=data.get("events", []),
            strategy=InvalidationStrategy(data.get("strategy", "pattern")),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CacheCollection
# ===========================================================================


@dataclass
class CacheCollection:
    """
    Collection chứa tất cả cache profiles, strategies, và rules.

    Attributes:
        profiles: Danh sách cache profiles
        strategies: Danh sách cache strategies
        invalidation_rules: Danh sách invalidation rules
    """
    profiles: list[CacheProfile] = field(default_factory=list)
    strategies: list[CacheStrategy] = field(default_factory=list)
    invalidation_rules: list[CacheInvalidationRule] = field(default_factory=list)

    def add_profile(self, profile: CacheProfile) -> None:
        """Thêm profile vào collection."""
        self.profiles.append(profile)

    def add_strategy(self, strategy: CacheStrategy) -> None:
        """Thêm strategy vào collection."""
        self.strategies.append(strategy)

    def add_invalidation_rule(self, rule: CacheInvalidationRule) -> None:
        """Thêm invalidation rule vào collection."""
        self.invalidation_rules.append(rule)

    @property
    def total_count(self) -> int:
        """Tổng số profiles trong collection."""
        return len(self.profiles)

    def get_by_id(self, profile_id: str) -> Optional[CacheProfile]:
        """Tim profile theo ID."""
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None

    def tenant_isolated_profiles(self) -> list[CacheProfile]:
        """Loc các profiles có tenant isolation (KPI-029)."""
        return [p for p in self.profiles if p.tenant_isolated]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "strategies": [s.to_dict() for s in self.strategies],
            "invalidation_rules": [r.to_dict() for r in self.invalidation_rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheCollection":
        """Tạo CacheCollection từ dict."""
        result = cls()
        result.profiles = [CacheProfile.from_dict(p) for p in data.get("profiles", [])]
        result.strategies = [CacheStrategy.from_dict(s) for s in data.get("strategies", [])]
        result.invalidation_rules = [CacheInvalidationRule.from_dict(r) for r in data.get("invalidation_rules", [])]
        return result