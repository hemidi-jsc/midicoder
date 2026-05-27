# coding: utf-8
"""
Cache Provider - Abstract interface.

Định nghĩa abstract base class cho cache providers.
Tất cả implementations (Redis, Memory) phải implement interface này.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheProvider(ABC):
    """
    Abstract interface cho cache provider.

    Cung cấp các operations cơ bản:
    - get: Lấy giá trị từ cache
    - set: Lưu giá trị vào cache với TTL
    - delete: Xóa key khỏi cache
    - invalidate: Xóa batch keys theo pattern
    - warm: Warm-up cache với danh sách keys
    """

    @abstractmethod
    async def get(self, key: str) -> Any:
        """
        Lấy giá trị từ cache.

        Args:
            key: Cache key

        Returns:
            Giá trị trong cache, None nếu không tồn tại
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Lưu giá trị vào cache với TTL.

        Args:
            key: Cache key
            value: Giá trị để lưu
            ttl: Time-to-live (giây)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Xóa key khỏi cache.

        Args:
            key: Cache key

        Returns:
            True nếu xóa thành công
        """
        pass

    @abstractmethod
    async def invalidate(self, pattern: str) -> int:
        """
        Xóa batch keys theo glob pattern.

        Args:
            pattern: Glob pattern (ví dụ: user:*, order:*)

        Returns:
            Số lượng keys đã xóa
        """
        pass

    @abstractmethod
    async def warm(self, keys: list[str], loader: Any, ttl: int = 300) -> int:
        """
        Warm-up cache với danh sách keys.

        Args:
            keys: Danh sách keys cần warm
            loader: Function/object để load data
            ttl: Time-to-live mặc định (giây)

        Returns:
            Số lượng keys đã warm thành công
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Kiểm tra health của cache backend.

        Returns:
            True nếu backend healthy
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Đóng kết nối đến cache backend."""
        pass
