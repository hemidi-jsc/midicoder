# coding: utf-8
"""
Memory Cache Provider.

Implementation của CacheProvider dùng in-memory dict.
Phù hợp cho development, testing, và single-node deployment.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import fnmatch
import json
import time
from typing import Any, Optional


from .base import CacheProvider


class MemoryCacheProvider(CacheProvider):
    """
    Cache provider dùng in-memory dict.

    Attributes:
        max_size: Số lượng keys tối đa
        key_prefix: Prefix cho tất cả cache keys
        tenant_id: Tenant ID để prefix vào keys (KPI-029)
    """

    def __init__(
        self,
        max_size: int = 10_000,
        key_prefix: str = "",
        tenant_id: Optional[str] = None,
    ):
        """
        Khởi tạo memory cache provider.

        Args:
            max_size: Số lượng keys tối đa
            key_prefix: Prefix cho cache keys
            tenant_id: Tenant ID cho tenant isolation (KPI-029)
        """
        self.max_size = max_size
        self.key_prefix = key_prefix
        self.tenant_id = tenant_id
        self._store: dict[str, tuple[Any, float]] = {}

    def _build_key(self, key: str) -> str:
        """
        Xây dựng cache key với prefix và tenant.

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

    async def get(self, key: str) -> Any:
        """
        Lấy giá trị từ memory cache.

        Args:
            key: Cache key

        Returns:
            Giá trị đã được deserialize, None nếu không tồn tại hoặc đã expire
        """
        full_key = self._build_key(key)
        entry = self._store.get(full_key)

        if entry is None:
            return None

        value, expiry = entry
        if expiry and time.time() > expiry:
            del self._store[full_key]
            return None

        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Lưu giá trị vào memory cache.

        Args:
            key: Cache key
            value: Giá trị (sẽ được JSON serialize)
            ttl: Time-to-live (giây)
        """
        from midicoder.errors import MidicoderErrorManager as EM

        full_key = self._build_key(key)

        # Evict if at max capacity
        if len(self._store) >= self.max_size and full_key not in self._store:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]

        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            EM.raise_error("CP09_SERIALIZATION_FAILED", key=key, detail=str(e))

        expiry = time.time() + ttl if ttl > 0 else 0
        self._store[full_key] = (serialized, expiry)

    async def delete(self, key: str) -> bool:
        """
        Xóa key khỏi memory cache.

        Args:
            key: Cache key

        Returns:
            True nếu xóa thành công
        """
        full_key = self._build_key(key)
        if full_key in self._store:
            del self._store[full_key]
            return True
        return False

    async def invalidate(self, pattern: str) -> int:
        """
        Xóa batch keys theo glob pattern.

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
        Kiểm tra memory cache (luôn healthy).

        Returns:
            True (luôn healthy)
        """
        return True

    async def close(self) -> None:
        """Xóa toàn bộ cache."""
        self._store.clear()
