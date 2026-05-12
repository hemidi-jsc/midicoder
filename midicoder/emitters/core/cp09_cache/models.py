# coding: utf-8
"""
Mô-đun models cho Cache Emitter (CP09).

Định nghĩa các dataclass biểu diễn:
- CacheBackend: Enum các backend (redis, memory)
- InvalidationStrategy: Enum các strategies (pattern, tag, event)
- CacheProfile: Profile cache với backend, TTL, max_size, tenant_isolated
- CacheStrategy: Strategy caching (read_through, write_through, cache_aside)
- CacheInvalidationRule: Quy tắc invalidation (pattern, tag, event)
- CacheWarmConfig: Cấu hình warm-up cache
- CacheMetrics: Metrics theo dõi hiệu suất cache
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
    """Enum các backend cache được hỗ trợ."""
    REDIS = "redis"
    MEMORY = "memory"


class InvalidationStrategy(str, Enum):
    """Enum các strategies cho cache invalidation."""
    PATTERN = "pattern"
    TAG = "tag"
    EVENT = "event"


# Mapping từ string sang enum
_BACKEND_MAP = {
    "redis": CacheBackend.REDIS,
    "memory": CacheBackend.MEMORY,
}

_STRATEGY_MAP = {
    "pattern": InvalidationStrategy.PATTERN,
    "tag": InvalidationStrategy.TAG,
    "event": InvalidationStrategy.EVENT,
}


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
        ttl: Time-to-live mặc định (giây). Phải > 0
        max_size: Kích thước tối đa của cache (optional)
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
    tenant_isolated: bool = True  # KPI-029: mặc định isolate
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Backend không hợp lệ
        - TTL <= 0
        - max_size < 0
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate backend
        if self.backend not in CacheBackend:
            EM.raise_error(
                ErrorCode.CP09_BACKEND_INVALID,
                profile_id=self.id,
                backend=str(self.backend),
            )

        # Validate TTL > 0
        if self.ttl <= 0:
            EM.raise_error(
                ErrorCode.CP09_TTL_INVALID,
                profile_id=self.id,
                ttl=self.ttl,
            )

        # Validate max_size >= 0 nếu có
        if self.max_size is not None and self.max_size < 0:
            EM.raise_error(
                ErrorCode.CP09_TTL_INVALID,
                profile_id=self.id,
                detail="max_size không thể âm",
            )

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
        backend_val = data.get("backend", "redis")
        backend = _BACKEND_MAP.get(backend_val, CacheBackend.REDIS)
        return cls(
            id=data.get("id", ""),
            backend=backend,
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
    tenant_scoped: bool = True  # KPI-029: mặc định scoped
    description: str = ""

    def __post_init__(self):
        """Validation sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate strategy_type
        valid_strategies = {"read_through", "write_through", "cache_aside"}
        if self.strategy_type not in valid_strategies:
            EM.raise_error(
                ErrorCode.CP09_PATTERN_INVALID,
                profile_id=self.profile_id,
                strategy_type=self.strategy_type,
            )

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
        pattern: Pattern để match cache keys (glob format)
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
    tenant_scoped: bool = True  # KPI-029: mặc định scoped
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Pattern không hợp lệ (strategy=PATTERN nhưng pattern trống)
        - Tags trống (strategy=TAG nhưng tags trống)
        - Events trống (strategy=EVENT nhưng events trống)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Validate pattern-based invalidation
        if self.strategy == InvalidationStrategy.PATTERN and not self.pattern:
            EM.raise_error(
                ErrorCode.CP09_PATTERN_INVALID,
                profile_id=self.profile_id,
                detail="Pattern không được để trống khi dùng strategy=pattern",
            )

        # Validate tag-based invalidation
        if self.strategy == InvalidationStrategy.TAG and not self.tags:
            EM.raise_error(
                ErrorCode.CP09_PATTERN_INVALID,
                profile_id=self.profile_id,
                detail="Tags không được để trống khi dùng strategy=tag",
            )

        # Validate event-based invalidation
        if self.strategy == InvalidationStrategy.EVENT and not self.events:
            EM.raise_error(
                ErrorCode.CP09_PATTERN_INVALID,
                profile_id=self.profile_id,
                detail="Events không được để trống khi dùng strategy=event",
            )

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
        strategy_val = data.get("strategy", "pattern")
        strategy = _STRATEGY_MAP.get(strategy_val, InvalidationStrategy.PATTERN)
        return cls(
            profile_id=data.get("profile_id", ""),
            pattern=data.get("pattern", ""),
            tags=data.get("tags", []),
            events=data.get("events", []),
            strategy=strategy,
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CacheWarmConfig
# ===========================================================================


@dataclass
class CacheWarmConfig:
    """
    Cấu hình warm-up cache.

    Attributes:
        profile_id: ID của cache profile
        keys: Danh sách keys cần warm
        pattern: Pattern glob để match keys cần warm
        schedule: Cron expression cho warm-up schedule (optional)
        priority: Priority của warm-up job (1=cao nhất)
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        description: Mô tả config
    """
    profile_id: str
    keys: list[str] = field(default_factory=list)
    pattern: str = ""
    schedule: str = ""
    priority: int = 5
    tenant_scoped: bool = True  # KPI-029: mặc định scoped
    description: str = ""

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Không có keys và không có pattern
        - Priority không trong range 1-10
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Phải có keys hoặc pattern
        if not self.keys and not self.pattern:
            EM.raise_error(
                ErrorCode.CP09_KEY_EMPTY,
                profile_id=self.profile_id,
                detail="Warm config phải có keys hoặc pattern",
            )

        # Priority phải trong range 1-10
        if self.priority < 1 or self.priority > 10:
            EM.raise_error(
                ErrorCode.CP09_PATTERN_INVALID,
                profile_id=self.profile_id,
                detail="Priority phải trong range 1-10",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển warm config sang dict format."""
        return {
            "profile_id": self.profile_id,
            "keys": self.keys,
            "pattern": self.pattern,
            "schedule": self.schedule,
            "priority": self.priority,
            "tenant_scoped": self.tenant_scoped,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheWarmConfig":
        """Tạo CacheWarmConfig từ dict."""
        return cls(
            profile_id=data.get("profile_id", ""),
            keys=data.get("keys", []),
            pattern=data.get("pattern", ""),
            schedule=data.get("schedule", ""),
            priority=data.get("priority", 5),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# CacheMetrics
# ===========================================================================


@dataclass
class CacheMetrics:
    """
    Metrics theo dõi hiệu suất cache.

    Attributes:
        profile_id: ID của cache profile
        hit_count: Số lần cache hit
        miss_count: Số lần cache miss
        eviction_count: Số lần eviction
        avg_latency_ms: Latency trung bình (ms)
        peak_memory_mb: Peak memory usage (MB)
        tenant_scoped: Có enforce tenant scope không (KPI-029)
    """
    profile_id: str
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    avg_latency_ms: float = 0.0
    peak_memory_mb: float = 0.0
    tenant_scoped: bool = True  # KPI-029: mặc định scoped

    def __post_init__(self):
        """
        Validation sau khi khởi tạo.

        Throw MidicoderError nếu:
        - Counts âm
        - Latency/memory âm
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if self.hit_count < 0 or self.miss_count < 0 or self.eviction_count < 0:
            EM.raise_error(
                ErrorCode.CP09_TTL_INVALID,
                profile_id=self.profile_id,
                detail="Metric counts không thể âm",
            )

        if self.avg_latency_ms < 0 or self.peak_memory_mb < 0:
            EM.raise_error(
                ErrorCode.CP09_TTL_INVALID,
                profile_id=self.profile_id,
                detail="Latency và memory không thể âm",
            )

    @property
    def hit_rate(self) -> float:
        """Tính toán hit rate (phần trăm)."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return round(self.hit_count / total * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển metrics sang dict format."""
        return {
            "profile_id": self.profile_id,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "eviction_count": self.eviction_count,
            "avg_latency_ms": self.avg_latency_ms,
            "peak_memory_mb": self.peak_memory_mb,
            "tenant_scoped": self.tenant_scoped,
            "hit_rate": self.hit_rate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheMetrics":
        """Tạo CacheMetrics từ dict."""
        return cls(
            profile_id=data.get("profile_id", ""),
            hit_count=data.get("hit_count", 0),
            miss_count=data.get("miss_count", 0),
            eviction_count=data.get("eviction_count", 0),
            avg_latency_ms=data.get("avg_latency_ms", 0.0),
            peak_memory_mb=data.get("peak_memory_mb", 0.0),
            tenant_scoped=data.get("tenant_scoped", True),
        )


# ===========================================================================
# CacheCollection
# ===========================================================================


@dataclass
class CacheCollection:
    """
    Collection chứa tất cả cache profiles, strategies, rules, warm configs, metrics.

    Attributes:
        profiles: Danh sách cache profiles
        strategies: Danh sách cache strategies
        invalidation_rules: Danh sách invalidation rules
        warm_configs: Danh sách warm-up configs
        metrics: Danh sách cache metrics
    """
    profiles: list[CacheProfile] = field(default_factory=list)
    strategies: list[CacheStrategy] = field(default_factory=list)
    invalidation_rules: list[CacheInvalidationRule] = field(default_factory=list)
    warm_configs: list[CacheWarmConfig] = field(default_factory=list)
    metrics: list[CacheMetrics] = field(default_factory=list)

    def add_profile(self, profile: CacheProfile) -> None:
        """Thêm profile vào collection."""
        self.profiles.append(profile)

    def add_strategy(self, strategy: CacheStrategy) -> None:
        """Thêm strategy vào collection."""
        self.strategies.append(strategy)

    def add_invalidation_rule(self, rule: CacheInvalidationRule) -> None:
        """Thêm invalidation rule vào collection."""
        self.invalidation_rules.append(rule)

    def add_warm_config(self, config: CacheWarmConfig) -> None:
        """Thêm warm config vào collection."""
        self.warm_configs.append(config)

    def add_metrics(self, metrics: CacheMetrics) -> None:
        """Thêm metrics vào collection."""
        self.metrics.append(metrics)

    @property
    def total_count(self) -> int:
        """Tổng số profiles trong collection."""
        return len(self.profiles)

    def get_by_id(self, profile_id: str) -> Optional[CacheProfile]:
        """Tìm profile theo ID."""
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None

    def get_strategies_for(self, profile_id: str) -> list[CacheStrategy]:
        """Lấy tất cả strategies của một profile."""
        return [s for s in self.strategies if s.profile_id == profile_id]

    def get_invalidation_rules_for(self, profile_id: str) -> list[CacheInvalidationRule]:
        """Lấy tất cả invalidation rules của một profile."""
        return [r for r in self.invalidation_rules if r.profile_id == profile_id]

    def tenant_isolated_profiles(self) -> list[CacheProfile]:
        """Lọc các profiles có tenant isolation (KPI-029)."""
        return [p for p in self.profiles if p.tenant_isolated]

    def redis_profiles(self) -> list[CacheProfile]:
        """Lọc các profiles dùng Redis backend."""
        return [p for p in self.profiles if p.backend == CacheBackend.REDIS]

    def memory_profiles(self) -> list[CacheProfile]:
        """Lọc các profiles dùng Memory backend."""
        return [p for p in self.profiles if p.backend == CacheBackend.MEMORY]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "strategies": [s.to_dict() for s in self.strategies],
            "invalidation_rules": [r.to_dict() for r in self.invalidation_rules],
            "warm_configs": [w.to_dict() for w in self.warm_configs],
            "metrics": [m.to_dict() for m in self.metrics],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheCollection":
        """Tạo CacheCollection từ dict."""
        result = cls()
        result.profiles = [CacheProfile.from_dict(p) for p in data.get("profiles", [])]
        result.strategies = [CacheStrategy.from_dict(s) for s in data.get("strategies", [])]
        result.invalidation_rules = [
            CacheInvalidationRule.from_dict(r) for r in data.get("invalidation_rules", [])
        ]
        result.warm_configs = [
            CacheWarmConfig.from_dict(w) for w in data.get("warm_configs", [])
        ]
        result.metrics = [CacheMetrics.from_dict(m) for m in data.get("metrics", [])]
        return result
