# coding: utf-8
"""
Cache Warm-up Module.

Cung cấp chức năng warm-up cache:
- WarmKeysJob: Warm cache với danh sách keys
- WarmPatternJob: Warm cache theo glob pattern
- ScheduledWarmJob: Warm cache theo cron schedule

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Optional

from midicoder.packs.cp09_cache.providers.base import CacheProvider
from midicoder.packs.cp09_cache.models import CacheWarmConfig

logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    Cache warmer để pre-populate cache với data quan trọng.

    Attributes:
        provider: CacheProvider instance
        loader: Callable để load data
        default_ttl: TTL mặc định cho warmed keys
    """

    def __init__(
        self,
        provider: CacheProvider,
        loader: Callable,
        default_ttl: int = 300,
    ):
        """
        Khởi tạo cache warmer.

        Args:
            provider: CacheProvider instance
            loader: Callable nhận key, trả về value (sync hoặc async)
            default_ttl: TTL mặc định (giây)
        """
        self.provider = provider
        self.loader = loader
        self.default_ttl = default_ttl

    async def warm_keys(
        self,
        keys: list[str],
        ttl: Optional[int] = None,
    ) -> dict[str, bool]:
        """
        Warm cache với danh sách keys.

        Args:
            keys: Danh sách keys cần warm
            ttl: TTL cho warmed keys (mặc định dùng default_ttl)

        Returns:
            Dict {key: success_status}
        """
        actual_ttl = ttl or self.default_ttl
        results: dict[str, bool] = {}

        for key in keys:
            try:
                existing = await self.provider.get(key)
                if existing is None:
                    value = self.loader(key)
                    if hasattr(value, "__await__"):
                        value = await value
                    await self.provider.set(key, value, actual_ttl)
                    logger.debug(f"[CacheWarm] Warmed key: {key}")
                else:
                    logger.debug(f"[CacheWarm] Key already cached: {key}")
                results[key] = True
            except Exception as e:
                logger.error(f"[CacheWarm] Failed to warm key {key}: {e}")
                results[key] = False

        return results

    async def warm_pattern(
        self,
        key_loader: Callable[[str], Any],
        pattern_keys: list[str],
        ttl: Optional[int] = None,
    ) -> int:
        """
        Warm cache với danh sách keys từ pattern loader.

        Args:
            key_loader: Callable trả về danh sách keys cần warm
            pattern_keys: Tham số truyền vào key_loader
            ttl: TTL cho warmed keys

        Returns:
            Số lượng keys đã warm thành công
        """
        actual_ttl = ttl or self.default_ttl
        keys = key_loader(*pattern_keys) if pattern_keys else key_loader()

        if not isinstance(keys, list):
            keys = [keys]

        results = await self.warm_keys(keys, actual_ttl)
        return sum(1 for v in results.values() if v)

    async def warm_from_config(
        self,
        config: CacheWarmConfig,
    ) -> dict[str, bool]:
        """
        Warm cache từ CacheWarmConfig.

        Args:
            config: Warm config chứa keys/pattern

        Returns:
            Dict {key: success_status}
        """
        if config.keys:
            return await self.warm_keys(config.keys)
        elif config.pattern:
            # Với pattern, cần caller cung cấp key list từ pattern
            logger.warning(
                f"[CacheWarm] Pattern warm cần key list. "
                f"Pattern: {config.pattern}"
            )
            return {}
        return {}

    async def warm_batch(
        self,
        configs: list[CacheWarmConfig],
    ) -> dict[str, dict[str, bool]]:
        """
        Warm cache từ nhiều configs, sorted theo priority.

        Configs có priority thấp hơn (số nhỏ) được warm trước.

        Args:
            configs: Danh sách warm configs

        Returns:
            Dict {profile_id: {key: success_status}}
        """
        sorted_configs = sorted(configs, key=lambda c: c.priority)
        all_results: dict[str, dict[str, bool]] = {}

        for config in sorted_configs:
            logger.info(
                f"[CacheWarm] Warming profile {config.profile_id} "
                f"(priority={config.priority})"
            )
            results = await self.warm_from_config(config)
            all_results[config.profile_id] = results

        return all_results


class ScheduledWarmJob:
    """
    Scheduled warm job để tự động warm cache theo cron schedule.

    Attributes:
        warmer: CacheWarmer instance
        config: CacheWarmConfig với cron schedule
        is_running: Đang chạy hay không
    """

    def __init__(
        self,
        warmer: CacheWarmer,
        config: CacheWarmConfig,
    ):
        """
        Khởi tạo scheduled warm job.

        Args:
            warmer: CacheWarmer instance
            config: Warm config có schedule field
        """
        self.warmer = warmer
        self.config = config
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_run: float = 0

    async def start(self) -> None:
        """Bắt đầu scheduled job."""
        if self.is_running:
            logger.warning("[ScheduledWarm] Job already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"[ScheduledWarm] Started job for profile {self.config.profile_id}"
        )

    async def stop(self) -> None:
        """Dừng scheduled job."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(
            f"[ScheduledWarm] Stopped job for profile {self.config.profile_id}"
        )

    async def run_now(self) -> dict[str, bool]:
        """
        Chạy warm job ngay lập tức.

        Returns:
            Dict {key: success_status}
        """
        self._last_run = time.time()
        return await self.warmer.warm_from_config(self.config)

    async def _run_loop(self) -> None:
        """Loop chính cho scheduled job."""
        while self.is_running:
            try:
                await self.run_now()
                # Parse cron schedule để tính khoảng thời gian
                # Đơn giản: mặc định 300s nếu không có schedule
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ScheduledWarm] Error in loop: {e}")
                await asyncio.sleep(60)

    @property
    def last_run(self) -> Optional[float]:
        """Timestamp của lần chạy gần nhất."""
        return self._last_run if self._last_run > 0 else None
