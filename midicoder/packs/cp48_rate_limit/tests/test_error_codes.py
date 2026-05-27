# coding: utf-8
"""
Tests cho CP48 error codes — xác nhận 10 error codes tồn tại và unique.

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.errors import ErrorCode


class TestCP48ErrorCodes:
    """Test 10 error codes của CP48."""

    def test_rate_limit_policy_not_found(self):
        assert ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND.value == "MDC-CP48-001"

    def test_rate_limit_strategy_invalid(self):
        assert ErrorCode.CP48_RATE_LIMIT_STRATEGY_INVALID.value == "MDC-CP48-002"

    def test_quota_config_invalid(self):
        assert ErrorCode.CP48_QUOTA_CONFIG_INVALID.value == "MDC-CP48-003"

    def test_rate_limit_exceeded(self):
        assert ErrorCode.CP48_RATE_LIMIT_EXCEEDED.value == "MDC-CP48-004"

    def test_quota_exceeded(self):
        assert ErrorCode.CP48_QUOTA_EXCEEDED.value == "MDC-CP48-005"

    def test_window_size_invalid(self):
        assert ErrorCode.CP48_WINDOW_SIZE_INVALID.value == "MDC-CP48-006"

    def test_redis_connection_failed(self):
        assert ErrorCode.CP48_REDIS_CONNECTION_FAILED.value == "MDC-CP48-007"

    def test_rate_limit_key_empty(self):
        assert ErrorCode.CP48_RATE_LIMIT_KEY_EMPTY.value == "MDC-CP48-008"

    def test_quota_level_invalid(self):
        assert ErrorCode.CP48_QUOTA_LEVEL_INVALID.value == "MDC-CP48-009"

    def test_throttling_config_invalid(self):
        assert ErrorCode.CP48_THROTTLING_CONFIG_INVALID.value == "MDC-CP48-010"

    def test_all_codes_unique(self):
        codes = [
            ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND.value,
            ErrorCode.CP48_RATE_LIMIT_STRATEGY_INVALID.value,
            ErrorCode.CP48_QUOTA_CONFIG_INVALID.value,
            ErrorCode.CP48_RATE_LIMIT_EXCEEDED.value,
            ErrorCode.CP48_QUOTA_EXCEEDED.value,
            ErrorCode.CP48_WINDOW_SIZE_INVALID.value,
            ErrorCode.CP48_REDIS_CONNECTION_FAILED.value,
            ErrorCode.CP48_RATE_LIMIT_KEY_EMPTY.value,
            ErrorCode.CP48_QUOTA_LEVEL_INVALID.value,
            ErrorCode.CP48_THROTTLING_CONFIG_INVALID.value,
        ]
        assert len(codes) == len(set(codes)), "Có error code trùng lặp"

    def test_all_codes_start_with_prefix(self):
        codes = [
            ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND.value,
            ErrorCode.CP48_RATE_LIMIT_STRATEGY_INVALID.value,
            ErrorCode.CP48_QUOTA_CONFIG_INVALID.value,
            ErrorCode.CP48_RATE_LIMIT_EXCEEDED.value,
            ErrorCode.CP48_QUOTA_EXCEEDED.value,
            ErrorCode.CP48_WINDOW_SIZE_INVALID.value,
            ErrorCode.CP48_REDIS_CONNECTION_FAILED.value,
            ErrorCode.CP48_RATE_LIMIT_KEY_EMPTY.value,
            ErrorCode.CP48_QUOTA_LEVEL_INVALID.value,
            ErrorCode.CP48_THROTTLING_CONFIG_INVALID.value,
        ]
        for code in codes:
            assert code.startswith("MDC-CP48-"), f"Code {code} không đúng prefix"
