"""
Retry Policy Module.

Module nay cung cap RetryPolicy voi exponential backoff.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.errors import MidicoderError

logger = logging.getLogger(__name__)


class RetryPolicy:
    """
    Retry policy voi exponential backoff cho notification dispatch.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        """
        Khoi tao RetryPolicy.

        Args:
            max_retries: So lan retry toi da (default: 3)
            base_delay: Delay ban dau tinh giay (default: 1.0)
            max_delay: Delay toi da tinh giay (default: 60.0)
        """
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

    def execute_with_retry(
        self,
        func: Callable[..., DispatchResult],
        *args: Any,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Execute function voi retry policy.

        Args:
            func: Function can execute (phai return DispatchResult)
            *args: Positional arguments cho func
            **kwargs: Keyword arguments cho func

        Returns:
            DispatchResult tu func

        Raises:
            Exception: Exception cuoi cung neu tat ca retries fail
        """
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_exception = e

                if attempt < self._max_retries:
                    delay = min(
                        self._base_delay * (2 ** attempt),
                        self._max_delay,
                    )
                    logger.warning(
                        "Notification dispatch failed (attempt %d/%d). "
                        "Retrying in %.1fs: %s",
                        attempt + 1,
                        self._max_retries,
                        delay,
                        str(e),
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Notification dispatch failed after %d attempts: %s",
                        self._max_retries + 1,
                        str(e),
                    )

        if last_exception:
            raise last_exception

        return DispatchResult(
            dispatch_id="unknown",
            status="failed",
            error_code="MDC-CP12-005",
        )

    @property
    def max_retries(self) -> int:
        """So lan retry toi da."""
        return self._max_retries

    @property
    def base_delay(self) -> float:
        """Base delay tinh giay."""
        return self._base_delay

    def get_delay_for_attempt(self, attempt: int) -> float:
        """
        Tinh delay cho attempt cu the.

        Args:
            attempt: Attempt number (0-based)

        Returns:
            Delay tinh giay
        """
        return min(self._base_delay * (2 ** attempt), self._max_delay)