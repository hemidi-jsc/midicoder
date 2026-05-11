# coding: utf-8
"""
Cache Emitter Module (CP09).

Module này định nghĩa các emitter cho cache layer:
- Models: CacheProfile, CacheStrategy, CacheInvalidationRule, CacheWarmConfig, CacheMetrics
- Parser: CacheParser để parse MIR metadata và YAML
- FastAPI Emitter: FastAPICacheEmitter
- NestJS Emitter: NestJSCacheEmitter
- Providers: CacheProvider (ABC), RedisCacheProvider, MemoryCacheProvider
- Decorators: @cache, @cache_tenant, @cache_disable
- Warm-up: CacheWarmer, ScheduledWarmJob

Author: Midicoder Team
Version: 1.0.0
"""

# Models (5 definitions)
from midicoder.emitters.core.cache.models import (
    CacheBackend,
    InvalidationStrategy,
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheWarmConfig,
    CacheMetrics,
    CacheCollection,
)

# Parser
from midicoder.emitters.core.cache.parser import CacheParser

# Emitters
from midicoder.emitters.core.cache.fastapi import FastAPICacheEmitter
from midicoder.emitters.core.cache.nestjs import NestJSCacheEmitter

# Providers
from midicoder.emitters.core.cache.providers.base import CacheProvider
from midicoder.emitters.core.cache.providers.redis import RedisCacheProvider
from midicoder.emitters.core.cache.providers.memory import MemoryCacheProvider

# Decorators
from midicoder.emitters.core.cache.cache_decorator import (
    cache,
    cache_tenant,
    cache_disable,
    clear_cache,
)

# Warm-up
from midicoder.emitters.core.cache.warm_up import (
    CacheWarmer,
    ScheduledWarmJob,
)

# Angular Emitter
try:
    from midicoder.emitters.core.cache.angular import (
        AngularEmitter,
        emit_angular_cache,
    )
except ImportError:
    AngularEmitter = None  # type: ignore[misc,assignment]
    emit_angular_cache = None  # type: ignore[misc,assignment]

# React Emitter
try:
    from midicoder.emitters.core.cache.react import (
        ReactEmitter,
        emit_react_cache,
    )
except ImportError:
    ReactEmitter = None  # type: ignore[misc,assignment]
    emit_react_cache = None  # type: ignore[misc,assignment]

__all__ = [
    # Models (5 definitions)
    "CacheBackend",
    "InvalidationStrategy",
    "CacheProfile",
    "CacheStrategy",
    "CacheInvalidationRule",
    "CacheWarmConfig",
    "CacheMetrics",
    "CacheCollection",
    # Parser
    "CacheParser",
    # Emitters
    "FastAPICacheEmitter",
    "NestJSCacheEmitter",
    # Providers
    "CacheProvider",
    "RedisCacheProvider",
    "MemoryCacheProvider",
    # Decorators
    "cache",
    "cache_tenant",
    "cache_disable",
    "clear_cache",
    # Warm-up
    "CacheWarmer",
    "ScheduledWarmJob",
    # Frontend emitters
    "AngularEmitter",
    "emit_angular_cache",
    "ReactEmitter",
    "emit_react_cache",
]
