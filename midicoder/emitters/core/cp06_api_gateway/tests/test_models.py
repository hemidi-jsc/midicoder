# coding: utf-8
"""
Tests cho Circuit Breaker models của CP06.

Kiểm tra:
- CircuitState enum
- CircuitBreakerPolicy enum
- CircuitBreakerConfig validation (__post_init__)
- CircuitBreakerConfig to_dict / from_dict round-trip
- Edge cases

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.emitters.core.cp06_api_gateway.models import (
    CircuitBreakerConfig,
    CircuitBreakerPolicy,
    CircuitState,
)


# ===========================================================================
# CircuitState Enum Tests
# ===========================================================================

class TestCircuitState:
    """Tests cho CircuitState enum."""

    def test_closed_value(self):
        """CircuitState.CLOSED có giá trị đúng."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self):
        """CircuitState.OPEN có giá trị đúng."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self):
        """CircuitState.HALF_OPEN có giá trị đúng."""
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_all_states_exist(self):
        """Tất cả các trạng thái tồn tại."""
        states = [s.value for s in CircuitState]
        assert "closed" in states
        assert "open" in states
        assert "half_open" in states


# ===========================================================================
# CircuitBreakerPolicy Enum Tests
# ===========================================================================

class TestCircuitBreakerPolicy:
    """Tests cho CircuitBreakerPolicy enum."""

    def test_consecutive_failures_value(self):
        """CircuitBreakerPolicy.CONSECUTIVE_FAILURES có giá trị đúng."""
        assert CircuitBreakerPolicy.CONSECUTIVE_FAILURES.value == "consecutive_failures"

    def test_failure_rate_value(self):
        """CircuitBreakerPolicy.FAILURE_RATE có giá trị đúng."""
        assert CircuitBreakerPolicy.FAILURE_RATE.value == "failure_rate"

    def test_avg_response_time_value(self):
        """CircuitBreakerPolicy.AVG_RESPONSE_TIME có giá trị đúng."""
        assert CircuitBreakerPolicy.AVG_RESPONSE_TIME.value == "avg_response_time"

    def test_parse_from_string(self):
        """Parse policy từ string value."""
        policy = CircuitBreakerPolicy("failure_rate")
        assert policy == CircuitBreakerPolicy.FAILURE_RATE


# ===========================================================================
# CircuitBreakerConfig Tests
# ===========================================================================

class TestCircuitBreakerConfig:
    """Tests cho CircuitBreakerConfig model."""

    def test_create_valid_config_defaults(self):
        """Tạo config hợp lệ với các giá trị mặc định."""
        cb = CircuitBreakerConfig(
            id="cb-001",
            name="Order Circuit Breaker",
            target_service="order-service",
        )
        assert cb.id == "cb-001"
        assert cb.name == "Order Circuit Breaker"
        assert cb.target_service == "order-service"
        assert cb.policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES
        assert cb.threshold == 5.0
        assert cb.timeout_seconds == 30
        assert cb.half_open_max_calls == 3
        assert cb.success_threshold == 2
        assert cb.fallback_function == ""
        assert cb.monitored_exceptions == []
        assert cb.metadata == {}

    def test_create_config_custom_values(self):
        """Tạo config với tất cả fields tùy chỉnh."""
        cb = CircuitBreakerConfig(
            id="cb-002",
            name="Payment CB",
            target_service="payment-service",
            policy=CircuitBreakerPolicy.FAILURE_RATE,
            threshold=0.5,
            timeout_seconds=60,
            half_open_max_calls=5,
            success_threshold=3,
            fallback_function="payment_fallback",
            monitored_exceptions=["TimeoutError", "ConnectionError"],
            metadata={"env": "production"},
        )
        assert cb.policy == CircuitBreakerPolicy.FAILURE_RATE
        assert cb.threshold == 0.5
        assert cb.timeout_seconds == 60
        assert cb.half_open_max_calls == 5
        assert cb.success_threshold == 3
        assert cb.fallback_function == "payment_fallback"
        assert cb.monitored_exceptions == ["TimeoutError", "ConnectionError"]
        assert cb.metadata == {"env": "production"}

    def test_empty_id_raises(self):
        """ID rỗng throw error."""
        with pytest.raises(ValueError, match="id không được để trống"):
            CircuitBreakerConfig(id="", name="bad", target_service="svc")

    def test_whitespace_id_raises(self):
        """ID chỉ whitespace throw error."""
        with pytest.raises(ValueError, match="id không được để trống"):
            CircuitBreakerConfig(id="   ", name="bad", target_service="svc")

    def test_zero_threshold_raises(self):
        """Threshold bằng 0 throw error."""
        with pytest.raises(ValueError, match="threshold phải lớn hơn 0"):
            CircuitBreakerConfig(id="cb", name="bad", target_service="svc", threshold=0)

    def test_negative_threshold_raises(self):
        """Threshold âm throw error."""
        with pytest.raises(ValueError, match="threshold phải lớn hơn 0"):
            CircuitBreakerConfig(id="cb", name="bad", target_service="svc", threshold=-1)

    def test_zero_timeout_raises(self):
        """timeout_seconds bằng 0 throw error."""
        with pytest.raises(ValueError, match="timeout_seconds phải lớn hơn 0"):
            CircuitBreakerConfig(id="cb", name="bad", target_service="svc", timeout_seconds=0)

    def test_negative_timeout_raises(self):
        """timeout_seconds âm throw error."""
        with pytest.raises(ValueError, match="timeout_seconds phải lớn hơn 0"):
            CircuitBreakerConfig(id="cb", name="bad", target_service="svc", timeout_seconds=-10)

    def test_to_dict(self):
        """to_dict trả về dict đầy đủ fields."""
        cb = CircuitBreakerConfig(
            id="cb-001",
            name="Test CB",
            target_service="test-service",
            policy=CircuitBreakerPolicy.FAILURE_RATE,
            threshold=0.3,
        )
        d = cb.to_dict()
        assert d["id"] == "cb-001"
        assert d["name"] == "Test CB"
        assert d["target_service"] == "test-service"
        assert d["policy"] == "failure_rate"
        assert d["threshold"] == 0.3
        assert d["timeout_seconds"] == 30
        assert d["half_open_max_calls"] == 3
        assert d["success_threshold"] == 2
        assert d["fallback_function"] == ""
        assert d["monitored_exceptions"] == []
        assert d["metadata"] == {}

    def test_from_dict(self):
        """from_dict tạo config từ dict."""
        data = {
            "id": "cb-003",
            "name": "Parsed CB",
            "target_service": "parsed-service",
            "policy": "avg_response_time",
            "threshold": 200.0,
            "timeout_seconds": 45,
            "half_open_max_calls": 4,
            "success_threshold": 2,
            "fallback_function": "my_fallback",
            "monitored_exceptions": ["ValueError"],
            "metadata": {"key": "value"},
        }
        cb = CircuitBreakerConfig.from_dict(data)
        assert cb.id == "cb-003"
        assert cb.name == "Parsed CB"
        assert cb.target_service == "parsed-service"
        assert cb.policy == CircuitBreakerPolicy.AVG_RESPONSE_TIME
        assert cb.threshold == 200.0
        assert cb.timeout_seconds == 45
        assert cb.half_open_max_calls == 4
        assert cb.success_threshold == 2
        assert cb.fallback_function == "my_fallback"
        assert cb.monitored_exceptions == ["ValueError"]
        assert cb.metadata == {"key": "value"}

    def test_from_dict_defaults(self):
        """from_dict với dict không đầy đủ dùng defaults."""
        data = {
            "id": "cb-minimal",
            "name": "Minimal CB",
            "target_service": "svc",
        }
        cb = CircuitBreakerConfig.from_dict(data)
        assert cb.policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES
        assert cb.threshold == 5.0
        assert cb.timeout_seconds == 30

    def test_round_trip(self):
        """Round-trip to_dict -> from_dict giữ nguyên dữ liệu."""
        original = CircuitBreakerConfig(
            id="cb-rt",
            name="RoundTrip CB",
            target_service="rt-service",
            policy=CircuitBreakerPolicy.AVG_RESPONSE_TIME,
            threshold=150.0,
            timeout_seconds=120,
            half_open_max_calls=5,
            success_threshold=4,
            fallback_function="rt_fallback",
            monitored_exceptions=["TimeoutError"],
            metadata={"version": "2.0"},
        )
        d = original.to_dict()
        restored = CircuitBreakerConfig.from_dict(d)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.target_service == original.target_service
        assert restored.policy == original.policy
        assert restored.threshold == original.threshold
        assert restored.timeout_seconds == original.timeout_seconds
        assert restored.half_open_max_calls == original.half_open_max_calls
        assert restored.success_threshold == original.success_threshold
        assert restored.fallback_function == original.fallback_function
        assert restored.monitored_exceptions == original.monitored_exceptions
        assert restored.metadata == original.metadata

    def test_all_policies_valid(self):
        """Tất cả policies tạo config hợp lệ."""
        for policy in CircuitBreakerPolicy:
            cb = CircuitBreakerConfig(
                id=f"cb-{policy.value}",
                name=f"{policy.value} CB",
                target_service="svc",
                policy=policy,
            )
            assert cb.policy == policy
