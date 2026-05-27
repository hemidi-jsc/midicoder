"""
Tests cho CP12 Rate Limiter.

Test coverage: 10 tests
"""

from __future__ import annotations

import pytest
import time
from midicoder.packs.cp12_notification.rate_limiter import RateLimiter
from midicoder.errors import MidicoderError


class TestRateLimiter:
    """Tests cho RateLimiter."""

    def test_default_config(self):
        """Default config: limit 10, window 3600s."""
        rl = RateLimiter()
        assert rl.get_limit("email") == 10
        assert rl._window_seconds == 3600.0

    def test_check_limit_within_quota(self):
        """Check limit khi còn quota."""
        rl = RateLimiter(default_limit=5, window_seconds=60)
        assert rl.check_limit("user@example.com", "email") is True

    def test_check_limit_exceeds_quota(self):
        """Vượt quota raise error."""
        rl = RateLimiter(default_limit=2, window_seconds=60)
        rl.check_limit("user@example.com", "email")
        rl.check_limit("user@example.com", "email")
        with pytest.raises(MidicoderError):
            rl.check_limit("user@example.com", "email")

    def test_custom_channel_limit(self):
        """Set custom limit per channel."""
        rl = RateLimiter(default_limit=10)
        rl.set_channel_limit("sms", 3)
        assert rl.get_limit("sms") == 3
        assert rl.get_limit("email") == 10  # default

    def test_get_remaining(self):
        """Lấy số dispatch còn lại."""
        rl = RateLimiter(default_limit=5, window_seconds=60)
        assert rl.get_remaining("u@e.com", "email") == 5
        rl.check_limit("u@e.com", "email")
        assert rl.get_remaining("u@e.com", "email") == 4

    def test_window_reset(self):
        """Reset count khi qua time window."""
        rl = RateLimiter(default_limit=1, window_seconds=0.1)
        rl.check_limit("u@e.com", "email")
        time.sleep(0.15)
        # Sau window, count reset → còn quota
        assert rl.check_limit("u@e.com", "email") is True

    def test_per_recipient_isolation(self):
        """Rate limit isolate per recipient."""
        rl = RateLimiter(default_limit=1, window_seconds=60)
        rl.check_limit("user1@e.com", "email")
        # user2 vẫn còn quota
        assert rl.check_limit("user2@e.com", "email") is True

    def test_per_channel_isolation(self):
        """Rate limit isolate per channel."""
        rl = RateLimiter(default_limit=1, window_seconds=60)
        rl.check_limit("u@e.com", "email")
        # SMS vẫn còn quota
        assert rl.check_limit("u@e.com", "sms") is True

    def test_reset_all(self):
        """Reset tất cả records."""
        rl = RateLimiter(default_limit=1, window_seconds=60)
        rl.check_limit("u1@e.com", "email")
        rl.check_limit("u2@e.com", "sms")
        rl.reset()
        assert rl.get_remaining("u1@e.com", "email") == 1
        assert rl.get_remaining("u2@e.com", "sms") == 1

    def test_get_stats(self):
        """Lấy rate stats."""
        rl = RateLimiter(default_limit=10, window_seconds=60)
        rl.check_limit("u@e.com", "email")
        rl.check_limit("u@e.com", "email")
        stats = rl.get_stats("u@e.com", "email")
        assert stats["count"] == 2
        assert stats["limit"] == 10
        assert stats["remaining"] == 8
