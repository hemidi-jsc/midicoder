"""
Rate Limiter Module.

Module này cung cấp RateLimiter:
- In-memory rate tracking per recipient per channel
- Configurable limits (vd: 3 emails/hour per recipient)
- Raise CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED khi vượt quota
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager


@dataclass
class _RateRecord:
    """Record cho rate tracking."""
    count: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimiter:
    """
    Rate limiter cho notification dispatch.

    Track số lượng dispatch per recipient per channel trong time window.
    Khi vượt quota, raise CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED.
    """

    def __init__(
        self,
        default_limit: int = 10,
        window_seconds: float = 3600.0,
    ) -> None:
        """
        Khởi tạo RateLimiter.

        Args:
            default_limit: Default số dispatch tối đa per window (default: 10)
            window_seconds: Time window tính giây (default: 3600 = 1 giờ)
        """
        self._default_limit = default_limit
        self._window_seconds = window_seconds
        self._records: dict[tuple[str, str], _RateRecord] = defaultdict(_RateRecord)
        self._custom_limits: dict[str, int] = {}

    def set_channel_limit(self, channel: str, limit: int) -> None:
        """Set custom limit cho channel cụ thể."""
        self._custom_limits[channel] = limit

    def get_limit(self, channel: str) -> int:
        """Lấy limit cho channel (custom hoặc default)."""
        return self._custom_limits.get(channel, self._default_limit)

    def check_limit(self, recipient: str, channel: str) -> bool:
        """
        Kiểm tra xem recipient còn quota cho channel không.

        Nếu còn quota: increment count, return True.
        Nếu vượt quota: raise CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED.

        Args:
            recipient: Recipient identifier (email, phone, user_id)
            channel: Channel name

        Returns:
            True nếu còn quota và đã increment

        Raises:
            MidicoderError: Nếu vượt rate limit
        """
        key = (recipient, channel)
        limit = self.get_limit(channel)
        now = time.time()

        record = self._records[key]

        # Reset window nếu đã quá time window
        if now - record.window_start >= self._window_seconds:
            record.count = 0
            record.window_start = now

        # Check limit
        if record.count >= limit:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED,
                recipient=recipient,
                channel=channel,
                limit=limit,
                window_seconds=int(self._window_seconds),
            )

        # Increment count
        record.count += 1
        return True

    def get_remaining(self, recipient: str, channel: str) -> int:
        """Lấy số dispatch còn lại cho recipient trong current window."""
        key = (recipient, channel)
        limit = self.get_limit(channel)
        now = time.time()

        record = self._records[key]

        if now - record.window_start >= self._window_seconds:
            return limit

        remaining = limit - record.count
        return max(0, remaining)

    def reset(self, recipient: str | None = None, channel: str | None = None) -> None:
        """Reset rate records."""
        if recipient is None:
            self._records.clear()
        else:
            keys_to_remove = [k for k in self._records if k[0] == recipient]
            for key in keys_to_remove:
                if channel is None or key[1] == channel:
                    del self._records[key]

    def get_stats(self, recipient: str, channel: str) -> dict[str, Any]:
        """Lấy rate stats cho recipient."""
        key = (recipient, channel)
        limit = self.get_limit(channel)
        remaining = self.get_remaining(recipient, channel)
        record = self._records.get(key, _RateRecord())

        return {
            "recipient": recipient,
            "channel": channel,
            "count": record.count,
            "limit": limit,
            "remaining": remaining,
            "window_seconds": self._window_seconds,
        }
