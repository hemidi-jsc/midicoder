from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta

RELIABILITY_TARGET_KIND_CATALOG = {
    "command",
    "workflow",
    "integration",
    "integration_operation",
}


class TimeoutConfig(BaseModel):
    connect_ms: Optional[int] = None
    read_ms: Optional[int] = None
    total_ms: Optional[int] = None

    model_config = {"extra": "forbid"}


class RetryConfig(BaseModel):
    max_attempts: int = 1
    backoff_ms: int = 0
    max_backoff_ms: Optional[int] = None
    jitter: bool = False

    model_config = {"extra": "forbid"}


class CircuitBreakerConfig(BaseModel):
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 30

    model_config = {"extra": "forbid"}


class ReliabilityPolicy(BaseModel):
    id: str
    target_kind: str
    target_ref: str
    timeout: Optional[TimeoutConfig] = None
    retry: Optional[RetryConfig] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    idempotency_key_field: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ReliabilityPoliciesFile(BaseModel):
    reliability_policies: list[ReliabilityPolicy]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="ops.reliability",
        usage_en=(
            "Reliability policy definitions for timeout, retry, backoff, circuit "
            "breaker and idempotency constraints."
        ),
    )
