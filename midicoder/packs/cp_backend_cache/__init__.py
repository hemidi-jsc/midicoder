# coding: utf-8
"""
Cache Emitter Module (CP09).

Module này định nghĩa các emitter cho cache layer:
- Models: CacheProfile, CacheStrategy, CacheInvalidationRule, CacheWarmConfig, CacheMetrics
- Models (Advanced): CDNCacheLayer, StampedePrevention, CacheTier, CacheWarmupConfig
- Parser: CacheParser để parse MIR metadata và YAML
- FastAPI Emitter: FastAPICacheEmitter
- NestJS Emitter: NestJSCacheEmitter
- Angular Emitter: AngularEmitter
- React Emitter: ReactEmitter
- Providers: CacheProvider (ABC), RedisCacheProvider, MemoryCacheProvider, MemcachedCacheProvider
- Decorators: @cache, @cache_tenant, @cache_disable
- Warm-up: CacheWarmer, ScheduledWarmJob

Author: Midicoder Team
Version: 1.1.0
"""

# Models (core definitions)
from midicoder.packs.cp_backend_cache.models import (
    CacheBackend,
    InvalidationStrategy,
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheWarmConfig,
    CacheMetrics,
    CacheCollection,
)

# Models (advanced definitions)
from midicoder.packs.cp_backend_cache.models import (
    CDNCacheControlDirective,
    CDNCacheLayer,
    StampedePreventionStrategy,
    StampedePrevention,
    CacheTier,
    CacheWarmupStrategy,
    CacheWarmupConfig,
)

# Parser
from midicoder.packs.cp_backend_cache.parser import CacheParser

# Emitters
from midicoder.packs.cp_backend_cache.fastapi import FastAPICacheEmitter
from midicoder.packs.cp_backend_cache.nestjs import NestJSCacheEmitter

# Providers
from midicoder.packs.cp_backend_cache.providers.base import CacheProvider
from midicoder.packs.cp_backend_cache.providers.redis import RedisCacheProvider
from midicoder.packs.cp_backend_cache.providers.memory import MemoryCacheProvider
from midicoder.packs.cp_backend_cache.providers.memcached import MemcachedCacheProvider

# Decorators
from midicoder.packs.cp_backend_cache.cache_decorator import (
    cache,
    cache_tenant,
    cache_disable,
    clear_cache,
)

# Warm-up
from midicoder.packs.cp_backend_cache.warm_up import (
    CacheWarmer,
    ScheduledWarmJob,
)

# Angular Emitter
try:
    from midicoder.packs.cp_backend_cache.angular import (
        AngularEmitter,
        emit_angular_cache,
    )
except ImportError:
    AngularEmitter = None  # type: ignore[misc,assignment]
    emit_angular_cache = None  # type: ignore[misc,assignment]

# React Emitter
try:
    from midicoder.packs.cp_backend_cache.react import (
        ReactEmitter,
        emit_react_cache,
    )
except ImportError:
    ReactEmitter = None  # type: ignore[misc,assignment]
    emit_react_cache = None  # type: ignore[misc,assignment]

__all__ = [
    # Models (core)
    "CacheBackend",
    "InvalidationStrategy",
    "CacheProfile",
    "CacheStrategy",
    "CacheInvalidationRule",
    "CacheWarmConfig",
    "CacheMetrics",
    "CacheCollection",
    # Models (advanced)
    "CDNCacheControlDirective",
    "CDNCacheLayer",
    "StampedePreventionStrategy",
    "StampedePrevention",
    "CacheTier",
    "CacheWarmupStrategy",
    "CacheWarmupConfig",
    # Parser
    "CacheParser",
    # Emitters
    "FastAPICacheEmitter",
    "NestJSCacheEmitter",
    # Providers
    "CacheProvider",
    "RedisCacheProvider",
    "MemoryCacheProvider",
    "MemcachedCacheProvider",
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
