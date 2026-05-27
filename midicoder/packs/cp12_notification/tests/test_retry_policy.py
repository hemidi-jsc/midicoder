"""
Tests cho CP12 Retry Policy.

Test coverage: 8 tests
"""

from __future__ import annotations

import pytest
from midicoder.packs.cp12_notification.retry_policy import RetryPolicy
from midicoder.packs.cp12_notification.models import DispatchResult


class TestRetryPolicy:
    """Tests cho RetryPolicy."""

    def test_success_first_try(self):
        """Thành công lần đầu."""
        rp = RetryPolicy(max_retries=3, base_delay=0.01)

        def func():
            return DispatchResult(dispatch_id="d1", status="sent")

        result = rp.execute_with_retry(func)
        assert result.status == "sent"

    def test_success_after_retry(self):
        """Thành công sau 2 retries."""
        rp = RetryPolicy(max_retries=3, base_delay=0.01)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temp error")
            return DispatchResult(dispatch_id="d1", status="sent")

        result = rp.execute_with_retry(func)
        assert result.status == "sent"
        assert call_count == 3

    def test_all_retries_exhausted(self):
        """Tất cả retries fail → raise exception."""
        rp = RetryPolicy(max_retries=2, base_delay=0.01)

        def func():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            rp.execute_with_retry(func)

    def test_max_retries_property(self):
        """Property max_retries."""
        rp = RetryPolicy(max_retries=5)
        assert rp.max_retries == 5

    def test_base_delay_property(self):
        """Property base_delay."""
        rp = RetryPolicy(base_delay=2.0)
        assert rp.base_delay == 2.0

    def test_get_delay_for_attempt(self):
        """Exponential backoff delays."""
        rp = RetryPolicy(base_delay=1.0, max_delay=10.0)
        assert rp.get_delay_for_attempt(0) == 1.0  # 1 * 2^0
        assert rp.get_delay_for_attempt(1) == 2.0  # 1 * 2^1
        assert rp.get_delay_for_attempt(2) == 4.0  # 1 * 2^2
        assert rp.get_delay_for_attempt(3) == 8.0  # 1 * 2^3

    def test_max_delay_cap(self):
        """Delay không vượt max_delay."""
        rp = RetryPolicy(base_delay=1.0, max_delay=5.0)
        assert rp.get_delay_for_attempt(10) == 5.0  # capped

    def test_execute_with_args(self):
        """Execute với args/kwargs."""
        rp = RetryPolicy(max_retries=0, base_delay=0.01)

        def func(a, b, key=""):
            return DispatchResult(dispatch_id=f"{a}{b}{key}", status="sent")

        result = rp.execute_with_retry(func, 1, 2, key="x")
        assert result.dispatch_id == "12x"
