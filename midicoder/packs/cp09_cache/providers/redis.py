# coding: utf-8
"""
Redis Cache Provider.

Implementation của CacheProvider dùng Redis backend.
Hỗ trợ connection pooling, tenant-aware keys, và batch operations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from .base import CacheProvider


class RedisCacheProvider(CacheProvider):
    """
    Cache provider dùng Redis.

    Attributes:
        redis_url: Redis connection URL
        pool_max_connections: Số kết nối tối đa trong pool
        key_prefix: Prefix cho tất cả cache keys
        tenant_id: Tenant ID để prefix vào keys (KPI-029)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        pool_max_connections: int = 10,
        key_prefix: str = "",
        tenant_id: Optional[str] = None,
    ):
        """
        Khởi tạo Redis cache provider.

        Args:
            redis_url: Redis URL (mặc định từ env REDIS_URL)
            pool_max_connections: Số kết nối pool tối đa
            key_prefix: Prefix cho cache keys
            tenant_id: Tenant ID cho tenant isolation (KPI-029)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.pool_max_connections = pool_max_connections
        self.key_prefix = key_prefix
        self.tenant_id = tenant_id
        self._redis = None

    def _build_key(self, key: str) -> str:
        """
        Xây dựng cache key với prefix và tenant.

        Format: {key_prefix}{tenant_id}:{key}

        Args:
            key: Cache key gốc

        Returns:
            Cache key đã được prefix
        """
        parts = []
        if self.key_prefix:
            parts.append(self.key_prefix)
        if self.tenant_id:
            parts.append(f"{self.tenant_id}:")
        parts.append(key)
        return "".join(parts)

    async def _get_redis(self):
        """Lấy hoặc tạo Redis client async."""
        if self._redis is None:
            from redis.asyncio import Redis, ConnectionPool

            pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.pool_max_connections,
                decode_responses=True,
            )
            self._redis = Redis(connection_pool=pool)
        return self._redis

    async def get(self, key: str) -> Any:
        """
        Lấy giá trị từ Redis cache.

        Args:
            key: Cache key

        Returns:
            Giá trị đã được deserialize, None nếu không tồn tại
        """
        redis = await self._get_redis()
        full_key = self._build_key(key)
        raw = await redis.get(full_key)

        if raw is None:
            return None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Lưu giá trị vào Redis cache.

        Args:
            key: Cache key
            value: Giá trị (sẽ được JSON serialize)
            ttl: Time-to-live (giây)
        """
        from midicoder.errors import MidicoderErrorManager as EM

        redis = await self._get_redis()
        full_key = self._build_key(key)

        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            EM.raise_error("CP09_SERIALIZATION_FAILED", key=key, detail=str(e))

        await redis.setex(full_key, ttl, serialized)

    async def delete(self, key: str) -> bool:
        """
        Xóa key khỏi Redis cache.

        Args:
            key: Cache key

        Returns:
            True nếu xóa thành công
        """
        redis = await self._get_redis()
        full_key = self._build_key(key)
        deleted = await redis.delete(full_key)
        return deleted > 0

    async def invalidate(self, pattern: str) -> int:
        """
        Xóa batch keys theo glob pattern.

        Sử dụng SCAN để tránh block Redis.

        Args:
            pattern: Glob pattern (ví dụ: user:*)

        Returns:
            Số lượng keys đã xóa
        """
        redis = await self._get_redis()
        prefix_pattern = self._build_key(pattern)
        deleted_count = 0
        cursor = "0"

        while True:
            cursor, keys = await redis.scan(cursor, match=prefix_pattern, count=100)
            if keys:
                await redis.delete(*keys)
                deleted_count += len(keys)
            if cursor == "0":
                break

        return deleted_count

    async def warm(self, keys: list[str], loader: Any, ttl: int = 300) -> int:
        """
        Warm-up cache với danh sách keys.

        Args:
            keys: Danh sách keys cần warm
            loader: Callable để load data cho key
            ttl: Time-to-live mặc định (giây)

        Returns:
            Số lượng keys đã warm thành công
        """
        success_count = 0

        for key in keys:
            try:
                existing = await self.get(key)
                if existing is None:
                    if callable(loader):
                        value = loader(key)
                        if hasattr(value, "__await__"):
                            value = await value
                        await self.set(key, value, ttl)
                    success_count += 1
                else:
                    success_count += 1
            except Exception:
                continue

        return success_count

    async def health_check(self) -> bool:
        """
        Kiểm tra kết nối Redis.

        Returns:
            True nếu Redis đang hoạt động
        """
        try:
            redis = await self._get_redis()
            await redis.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Đóng Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
