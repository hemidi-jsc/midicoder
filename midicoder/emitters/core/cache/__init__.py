# coding: utf-8
"""
Cache Emitter Module.

Module nay dinh nghia cac emitter cho cache layer (CP09):
- Models: CacheProfile, CacheStrategy, CacheInvalidationRule, CacheCollection
- Parser: CacheParser de parse MIR metadata
- FastAPI Emitter: RedisEmitter (Redis client, strategies, decorators)
- NestJS Emitter: CacheModuleEmitter (CacheModule, Interceptors)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cache.models import (
    CacheBackend,
    InvalidationStrategy,
    CacheProfile,
    CacheStrategy,
    CacheInvalidationRule,
    CacheCollection,
)
from midicoder.emitters.core.cache.parser import CacheParser
from midicoder.emitters.core.cache.fastapi import RedisEmitter
from midicoder.emitters.core.cache.nestjs import CacheModuleEmitter

__all__ = [
    "CacheBackend",
    "InvalidationStrategy",
    "CacheProfile",
    "CacheStrategy",
    "CacheInvalidationRule",
    "CacheCollection",
    "CacheParser",
    "RedisEmitter",
    "CacheModuleEmitter",
]