# coding: utf-8
"""
Mô-đun recipes cho CP06 — API Gateway & Service Mesh.

Cung cấp các recipe để build GatewayIR cho các use case phổ biến:
- circuit_breaker_recipe: Application-level circuit breaker configuration

Tác giả: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp06_api_gateway.models import (
    CircuitBreakerConfig,
    CircuitBreakerPolicy,
)
from midicoder.emitters.core.cp06_api_gateway.parser import GatewayIR


# ===========================================================================
# Recipe Output
# ===========================================================================


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: GatewayIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: GatewayIR
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


# ===========================================================================
# Recipes
# ===========================================================================


def circuit_breaker_recipe(
    cb_id: str = "cb_default",
    name: str = "Default Circuit Breaker",
    target_service: str = "backend-service",
    policy: CircuitBreakerPolicy = CircuitBreakerPolicy.CONSECUTIVE_FAILURES,
    threshold: float = 5.0,
    timeout_seconds: int = 30,
    half_open_max_calls: int = 3,
    success_threshold: int = 2,
    fallback_function: str = "",
    monitored_exceptions: list[str] | None = None,
) -> RecipeOutput:
    """Recipe: Application-level circuit breaker configuration.

    Tạo circuit breaker để bảo vệ các cuộc gọi đến service backend
    khỏi failure cascade.

    Args:
        cb_id: Định danh duy nhất của circuit breaker
        name: Tên hiển thị
        target_service: Tên service backend được bảo vệ
        policy: Chính sách kích hoạt breaker
        threshold: Ngưỡng kích hoạt
        timeout_seconds: Thời gian ở trạng thái OPEN
        half_open_max_calls: Số probe calls trong HALF_OPEN
        success_threshold: Số probe thành công để closed
        fallback_function: Tên fallback function
        monitored_exceptions: Danh sách exception types theo dõi

    Returns:
        RecipeOutput chứa GatewayIR với circuit breaker config
    """
    if monitored_exceptions is None:
        monitored_exceptions = []

    cb = CircuitBreakerConfig(
        id=cb_id,
        name=name,
        target_service=target_service,
        policy=policy,
        threshold=threshold,
        timeout_seconds=timeout_seconds,
        half_open_max_calls=half_open_max_calls,
        success_threshold=success_threshold,
        fallback_function=fallback_function,
        monitored_exceptions=monitored_exceptions,
    )

    ir = GatewayIR()
    ir.add_circuit_breaker(cb)

    raw = cb.to_dict()

    return RecipeOutput(
        name="circuit_breaker",
        description=f"Circuit breaker '{name}' for {target_service} ({policy.value})",
        ir=ir,
        raw_data=raw,
    )


__all__ = [
    "RecipeOutput",
    "circuit_breaker_recipe",
]
