# coding: utf-8
"""
Tests cho parser module của CP06 — GatewayIR và parse_circuit_breakers.

Kiểm tra:
- GatewayIR dataclass (mặc định, add_circuit_breaker, to_dict, from_dict)
- parse_circuit_breakers helper
- Edge cases và validation

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.emitters.core.cp06_api_gateway.models import (
    CircuitBreakerConfig,
    CircuitBreakerPolicy,
)
from midicoder.emitters.core.cp06_api_gateway.parser import (
    GatewayIR,
    parse_circuit_breakers,
)


# ===========================================================================
# GatewayIR Tests
# ===========================================================================

class TestGatewayIR:
    """Tests cho GatewayIR."""

    def test_default_ir_empty(self):
        """GatewayIR mặc định có circuit_breakers rỗng."""
        ir = GatewayIR()
        assert ir.circuit_breakers == []

    def test_add_circuit_breaker(self):
        """Thêm circuit breaker vào IR."""
        ir = GatewayIR()
        cb = CircuitBreakerConfig(
            id="cb-001",
            name="Test CB",
            target_service="test-service",
        )
        ir.add_circuit_breaker(cb)
        assert len(ir.circuit_breakers) == 1
        assert ir.circuit_breakers[0].id == "cb-001"

    def test_add_multiple_circuit_breakers(self):
        """Thêm nhiều circuit breakers vào IR."""
        ir = GatewayIR()
        cb1 = CircuitBreakerConfig(id="cb-1", name="CB1", target_service="svc1")
        cb2 = CircuitBreakerConfig(id="cb-2", name="CB2", target_service="svc2")
        ir.add_circuit_breaker(cb1)
        ir.add_circuit_breaker(cb2)
        assert len(ir.circuit_breakers) == 2
        assert ir.circuit_breakers[0].id == "cb-1"
        assert ir.circuit_breakers[1].id == "cb-2"

    def test_to_dict_empty(self):
        """to_dict với IR rỗng."""
        ir = GatewayIR()
        d = ir.to_dict()
        assert d == {"circuit_breakers": []}

    def test_to_dict_with_breakers(self):
        """to_dict với circuit breakers."""
        ir = GatewayIR()
        cb = CircuitBreakerConfig(
            id="cb-001",
            name="Test CB",
            target_service="test-service",
            policy=CircuitBreakerPolicy.FAILURE_RATE,
        )
        ir.add_circuit_breaker(cb)
        d = ir.to_dict()
        assert len(d["circuit_breakers"]) == 1
        assert d["circuit_breakers"][0]["id"] == "cb-001"
        assert d["circuit_breakers"][0]["policy"] == "failure_rate"

    def test_from_dict_empty(self):
        """from_dict với dict rỗng."""
        ir = GatewayIR.from_dict({})
        assert ir.circuit_breakers == []

    def test_from_dict_with_breakers(self):
        """from_dict với circuit breakers data."""
        data = {
            "circuit_breakers": [
                {
                    "id": "cb-001",
                    "name": "Parsed CB",
                    "target_service": "parsed-service",
                    "policy": "consecutive_failures",
                    "threshold": 10.0,
                    "timeout_seconds": 60,
                },
            ],
        }
        ir = GatewayIR.from_dict(data)
        assert len(ir.circuit_breakers) == 1
        cb = ir.circuit_breakers[0]
        assert cb.id == "cb-001"
        assert cb.name == "Parsed CB"
        assert cb.target_service == "parsed-service"
        assert cb.policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES
        assert cb.threshold == 10.0
        assert cb.timeout_seconds == 60

    def test_round_trip(self):
        """Round-trip to_dict -> from_dict giữ nguyên dữ liệu."""
        original = GatewayIR()
        original.add_circuit_breaker(
            CircuitBreakerConfig(
                id="cb-rt",
                name="RT CB",
                target_service="rt-svc",
                policy=CircuitBreakerPolicy.AVG_RESPONSE_TIME,
                threshold=200.0,
                timeout_seconds=45,
                monitored_exceptions=["TimeoutError"],
                metadata={"env": "prod"},
            )
        )
        d = original.to_dict()
        restored = GatewayIR.from_dict(d)
        assert len(restored.circuit_breakers) == 1
        assert restored.circuit_breakers[0].id == "cb-rt"
        assert restored.circuit_breakers[0].policy == CircuitBreakerPolicy.AVG_RESPONSE_TIME
        assert restored.circuit_breakers[0].threshold == 200.0
        assert restored.circuit_breakers[0].monitored_exceptions == ["TimeoutError"]
        assert restored.circuit_breakers[0].metadata == {"env": "prod"}


# ===========================================================================
# parse_circuit_breakers Tests
# ===========================================================================

class TestParseCircuitBreakers:
    """Tests cho parse_circuit_breakers helper."""

    def test_parse_empty_list(self):
        """Parse danh sách rỗng trả về list rỗng."""
        result = parse_circuit_breakers([])
        assert result == []
        assert isinstance(result, list)

    def test_parse_single_breaker(self):
        """Parse một circuit breaker."""
        data = [
            {
                "id": "cb-001",
                "name": "Single CB",
                "target_service": "single-service",
            },
        ]
        result = parse_circuit_breakers(data)
        assert len(result) == 1
        assert isinstance(result[0], CircuitBreakerConfig)
        assert result[0].id == "cb-001"
        assert result[0].name == "Single CB"
        assert result[0].target_service == "single-service"

    def test_parse_multiple_breakers(self):
        """Parse nhiều circuit breakers."""
        data = [
            {"id": "cb-1", "name": "CB1", "target_service": "svc1"},
            {"id": "cb-2", "name": "CB2", "target_service": "svc2", "policy": "failure_rate"},
            {"id": "cb-3", "name": "CB3", "target_service": "svc3", "policy": "avg_response_time"},
        ]
        result = parse_circuit_breakers(data)
        assert len(result) == 3
        assert all(isinstance(cb, CircuitBreakerConfig) for cb in result)
        assert result[0].policy == CircuitBreakerPolicy.CONSECUTIVE_FAILURES
        assert result[1].policy == CircuitBreakerPolicy.FAILURE_RATE
        assert result[2].policy == CircuitBreakerPolicy.AVG_RESPONSE_TIME

    def test_parse_with_all_fields(self):
        """Parse circuit breaker với đầy đủ fields."""
        data = [
            {
                "id": "cb-full",
                "name": "Full CB",
                "target_service": "full-service",
                "policy": "failure_rate",
                "threshold": 0.5,
                "timeout_seconds": 120,
                "half_open_max_calls": 5,
                "success_threshold": 3,
                "fallback_function": "full_fallback",
                "monitored_exceptions": ["TimeoutError", "ConnectionError"],
                "metadata": {"env": "production", "team": "backend"},
            },
        ]
        result = parse_circuit_breakers(data)
        cb = result[0]
        assert cb.id == "cb-full"
        assert cb.policy == CircuitBreakerPolicy.FAILURE_RATE
        assert cb.threshold == 0.5
        assert cb.timeout_seconds == 120
        assert cb.half_open_max_calls == 5
        assert cb.success_threshold == 3
        assert cb.fallback_function == "full_fallback"
        assert cb.monitored_exceptions == ["TimeoutError", "ConnectionError"]
        assert cb.metadata == {"env": "production", "team": "backend"}

    def test_parse_invalid_data_raises(self):
        """Parse data không hợp lệ throw error từ validation."""
        data = [
            {"id": "", "name": "Bad", "target_service": "svc"},
        ]
        with pytest.raises(ValueError, match="id không được để trống"):
            parse_circuit_breakers(data)

    def test_parse_invalid_threshold_raises(self):
        """Parse data với threshold không hợp lệ throw error."""
        data = [
            {"id": "cb-bad", "name": "Bad", "target_service": "svc", "threshold": -5},
        ]
        with pytest.raises(ValueError, match="threshold phải lớn hơn 0"):
            parse_circuit_breakers(data)

    def test_parse_invalid_timeout_raises(self):
        """Parse data với timeout_seconds không hợp lệ throw error."""
        data = [
            {"id": "cb-bad", "name": "Bad", "target_service": "svc", "timeout_seconds": 0},
        ]
        with pytest.raises(ValueError, match="timeout_seconds phải lớn hơn 0"):
            parse_circuit_breakers(data)
