# coding: utf-8
"""
Cache Decorators cho FastAPI.

Cung cấp các decorators:
- @cache: Tự động cache kết quả của function
- @cache_tenant: Cache với tenant isolation (KPI-029)
- @cache_disable: Tắt caching cho function

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import functools
import hashlib
from typing import Any, Optional

_cache_store: dict[str, tuple[Any, float]] = {}
_default_ttl = 300


def cache(
    key: Optional[str] = None,
    ttl: int = _default_ttl,
    tenant_id: Optional[str] = None,
):
    """
    Decorator để cache kết quả của function.

    Args:
        key: Custom cache key (nếu không, tự động generate từ function name + args)
        ttl: Time-to-live (giây)
        tenant_id: Tenant ID cho tenant isolation (KPI-029)

    Returns:
        Decorated function với cache

    Example:
        @cache(key="user_list", ttl=600)
        async def get_users():
            return await db.query(User)
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal key
            if key is None:
                key = _generate_key(func.__name__, args, kwargs)

            full_key = f"{tenant_id}:{key}" if tenant_id else key
            cached = _get_cached(full_key)

            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            _set_cached(full_key, result, ttl)
            return result

        return wrapper

    return decorator


def cache_tenant(ttl: int = _default_ttl):
    """
    Decorator để cache với tenant isolation.

    Tự động lấy tenant_id từ kwargs hoặc header.

    Args:
        ttl: Time-to-live (giây)

    Returns:
        Decorated function với tenant-aware cache

    Example:
        @cache_tenant(ttl=300)
        async def get_products(tenant_id="abc123"):
            return await db.query(Product).where(tenant_id=tenant_id)
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tenant_id = kwargs.get("tenant_id") or kwargs.get("tenant")
            if tenant_id is None:
                return await func(*args, **kwargs)

            cache_key = _generate_key(func.__name__, args, kwargs)
            full_key = f"{tenant_id}:{cache_key}"
            cached = _get_cached(full_key)

            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            _set_cached(full_key, result, ttl)
            return result

        return wrapper

    return decorator


def cache_disable(func):
    """
    Decorator để tắt caching cho function.

    Đặt comment và marker để pipeline biết không nên cache function này.

    Args:
        func: Function để decorate

    Returns:
        Function không thay đổi (no-op)

    Example:
        @cache_disable
        async def create_user(data: dict):
            return await db.insert(data)
    """
    func._cache_disabled = True
    return func


def _generate_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate cache key từ function name và arguments.

    Args:
        func_name: Tên function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Hash string làm cache key
    """
    raw = f"{func_name}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _get_cached(key: str) -> Any:
    """Lấy giá trị từ in-memory cache store."""
    import time

    entry = _cache_store.get(key)
    if entry is None:
        return None

    value, expiry = entry
    if expiry and time.time() > expiry:
        del _cache_store[key]
        return None

    return value


def _set_cached(key: str, value: Any, ttl: int) -> None:
    """Lưu giá trị vào in-memory cache store."""
    import time

    _cache_store[key] = (value, time.time() + ttl if ttl > 0 else 0)


def clear_cache(pattern: str = "*") -> int:
    """
    Xóa entries trong cache store theo pattern.

    Args:
        pattern: Glob pattern để match keys

    Returns:
        Số lượng keys đã xóa
    """
    import fnmatch

    keys_to_delete = [k for k in _cache_store if fnmatch.fnmatch(k, pattern)]
    for key in keys_to_delete:
        del _cache_store[key]
    return len(keys_to_delete)
