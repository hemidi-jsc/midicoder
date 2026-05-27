# coding: utf-8
"""
Mô-đun parser cho CP06 — API Gateway & Service Mesh.

Chứa GatewayIR (Intermediate Representation) và các helper functions
để parse DSL data thành typed models.

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp06_api_gateway.models import (
    CircuitBreakerConfig,
    CircuitBreakerPolicy,
)


# ===========================================================================
# Intermediate Representation (IR)
# ===========================================================================


@dataclass
class GatewayIR:
    """
    Intermediate Representation cho API Gateway.

    Aggregate tất cả các cấu hình gateway từ DSL, bao gồm:
    - Kong Gateway, Service, Route, Upstream, Plugin
    - Consul Service, HealthCheck, Connect
    - HTTP Routes, GraphQL Resolvers, Webhooks (RouteCollection)
    - Circuit Breakers (application-level)

    Attributes:
        circuit_breakers: Danh sách circuit breaker configurations
    """
    circuit_breakers: list[CircuitBreakerConfig] = field(default_factory=list)

    def add_circuit_breaker(self, cb: CircuitBreakerConfig) -> None:
        """
        Thêm circuit breaker vào IR.

        Args:
            cb: CircuitBreakerConfig instance
        """
        self.circuit_breakers.append(cb)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GatewayIR sang dict format."""
        return {
            "circuit_breakers": [cb.to_dict() for cb in self.circuit_breakers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GatewayIR":
        """Tạo GatewayIR từ dict."""
        ir = cls()
        cb_data = data.get("circuit_breakers", [])
        if cb_data:
            ir.circuit_breakers = parse_circuit_breakers(cb_data)
        return ir


# ===========================================================================
# Parser Helpers
# ===========================================================================


def parse_circuit_breakers(data: list[dict[str, Any]]) -> list[CircuitBreakerConfig]:
    """
    Parse danh sách circuit breaker configs từ dict data.

    Args:
        data: List of dictionaries chứa circuit breaker configuration

    Returns:
        List[CircuitBreakerConfig] parsed

    Raises:
        ValueError: Nếu dict data không hợp lệ (thiếu id, threshold <= 0, ...)

    Example:
        >>> cb_list = parse_circuit_breakers([
        ...     {"id": "cb-1", "name": "Order CB", "target_service": "order-service"},
        ... ])
        >>> len(cb_list)
        1
    """
    result: list[CircuitBreakerConfig] = []
    for item in data:
        result.append(CircuitBreakerConfig.from_dict(item))
    return result
