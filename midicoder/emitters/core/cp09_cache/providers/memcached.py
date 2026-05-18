# coding: utf-8
"""
Memcached Cache Provider.

Implementation của CacheProvider dùng Memcached backend.
Phù hợp cho high-throughput, distributed caching scenarios.

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

import fnmatch
import json
import time
from typing import Any, Optional

from .base import CacheProvider


class MemcachedCacheProvider(CacheProvider):
    """
    Cache provider dùng Memcached.

    Attributes:
        servers: Danh sách Memcached server URLs
        key_prefix: Prefix cho tất cả cache keys
        tenant_id: Tenant ID để prefix vào keys (KPI-029)
        default_ttl: TTL mặc định (giây)
    """

    def __init__(
        self,
        servers: list[str] | None = None,
        key_prefix: str = "",
        tenant_id: Optional[str] = None,
        default_ttl: int = 300,
    ):
        """
        Khởi tạo Memcached cache provider.

        Args:
            servers: Danh sách Memcached server (mặc định: localhost:11211)
            key_prefix: Prefix cho cache keys
            tenant_id: Tenant ID cho tenant isolation (KPI-029)
            default_ttl: TTL mặc định (giây)
        """
        self.servers = servers or ["localhost:11211"]
        self.key_prefix = key_prefix
        self.tenant_id = tenant_id
        self.default_ttl = default_ttl
        self._client = None
        self._store: dict[str, tuple[Any, float]] = {}

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

    async def _get_client(self):
        """Lấy hoặc tạo Memcached client.

        Falls back to in-memory dict if pymemcache is not available.
        """
        if self._client is not None:
            return self._client

        try:
            from pymemcache.client.hash import HashClient

            self._client = HashClient(
                self.servers,
                default_noretry=True,
                connect_timeout=3,
                timeout=5,
                no_block=True,
            )
            return self._client
        except ImportError:
            # Fallback to in-memory store if pymemcache not installed
            return None

    async def get(self, key: str) -> Any:
        """
        Lấy giá trị từ Memcached cache.

        Args:
            key: Cache key

        Returns:
            Giá trị đã được deserialize, None nếu không tồn tại
        """
        full_key = self._build_key(key)
        client = await self._get_client()

        if client is None:
            # Fallback to in-memory store
            entry = self._store.get(full_key)
            if entry is None:
                return None
            value, expiry = entry
            if expiry and time.time() > expiry:
                del self._store[full_key]
                return None
            try:
                return json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                return value

        try:
            raw = client.get(full_key)
            if raw is None:
                return None
            return json.loads(raw) if isinstance(raw, bytes) else raw
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Lưu giá trị vào Memcached cache.

        Args:
            key: Cache key
            value: Giá trị (sẽ được JSON serialize)
            ttl: Time-to-live (giây)
        """
        from midicoder.errors import MidicoderErrorManager as EM

        full_key = self._build_key(key)
        actual_ttl = ttl if ttl > 0 else self.default_ttl

        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            EM.raise_error("CP09_SERIALIZATION_FAILED", key=key, detail=str(e))

        client = await self._get_client()
        if client is None:
            # Fallback to in-memory store
            expiry = time.time() + actual_ttl if actual_ttl > 0 else 0
            self._store[full_key] = (serialized, expiry)
            return

        try:
            client.set(full_key, serialized, expire=actual_ttl)
        except Exception:
            # Fallback on error
            expiry = time.time() + actual_ttl if actual_ttl > 0 else 0
            self._store[full_key] = (serialized, expiry)

    async def delete(self, key: str) -> bool:
        """
        Xóa key khỏi Memcached cache.

        Args:
            key: Cache key

        Returns:
            True nếu xóa thành công
        """
        full_key = self._build_key(key)
        client = await self._get_client()

        if client is None:
            if full_key in self._store:
                del self._store[full_key]
                return True
            return False

        try:
            result = client.delete(full_key)
            return bool(result)
        except Exception:
            if full_key in self._store:
                del self._store[full_key]
                return True
            return False

    async def invalidate(self, pattern: str) -> int:
        """
        Xóa batch keys theo glob pattern.

        Memcached không hỗ trợ SCAN, nên dùng in-memory fallback.

        Args:
            pattern: Glob pattern (ví dụ: user:*)

        Returns:
            Số lượng keys đã xóa
        """
        prefix_pattern = self._build_key(pattern)
        keys_to_delete = [
            k for k in self._store if fnmatch.fnmatch(k, prefix_pattern)
        ]

        for key in keys_to_delete:
            del self._store[key]

        # Also try to delete via client for known keys
        client = await self._get_client()
        if client:
            for key in keys_to_delete:
                try:
                    client.delete(key)
                except Exception:
                    pass

        return len(keys_to_delete)

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
        Kiểm tra kết nối Memcached.

        Returns:
            True nếu Memcached đang hoạt động
        """
        client = await self._get_client()
        if client is None:
            return True  # In-memory fallback is always healthy

        try:
            client.version()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Đóng Memcached connection."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._store.clear()
