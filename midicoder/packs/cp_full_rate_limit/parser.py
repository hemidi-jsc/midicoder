# coding: utf-8
"""
Mô-đun parser cho CP48 — API Rate Limiting & Quota Management.

Parse DSL YAML → typed dataclasses (RateLimitPolicy, QuotaConfig).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.packs.cp_full_rate_limit.models import (
    QuotaConfig,
    QuotaLevel,
    QuotaPeriod,
    RateLimitPolicy,
    RateLimitStrategy,
)


# ===========================================================================
# IR Dataclass
# ===========================================================================


@dataclass
class RateLimitIR:
    """Intermediate Representation cho rate limiting + quota.

    Attributes:
        policies: Danh sách rate limit policies
        quotas: Danh sách quota configs
    """
    policies: list[RateLimitPolicy] = field(default_factory=list)
    quotas: list[QuotaConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển IR sang dict."""
        return {
            "policies": [p.to_dict() for p in self.policies],
            "quotas": [q.to_dict() for q in self.quotas],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RateLimitIR":
        """Tạo IR từ dict."""
        return cls(
            policies=[RateLimitPolicy.from_dict(p) for p in data.get("policies", [])],
            quotas=[QuotaConfig.from_dict(q) for q in data.get("quotas", [])],
        )


# ===========================================================================
# Parser
# ===========================================================================


class RateLimitParser:
    """Parser cho DSL YAML của rate limiting + quota.

    Chuyển đổi YAML dict → typed dataclasses.
    """

    @staticmethod
    def parse_policies(yaml_data: list[dict[str, Any]]) -> list[RateLimitPolicy]:
        """Parse danh sách policies từ YAML.

        Args:
            yaml_data: Danh sách dict từ YAML

        Returns:
            Danh sách RateLimitPolicy

        Raises:
            MidicoderError: Nếu data không hợp lệ
        """
        policies = []
        for item in yaml_data:
            strategy_value = item.get("strategy", "fixed_window")
            try:
                strategy = RateLimitStrategy(strategy_value)
            except ValueError:
                raise EM.raise_error(
                    ErrorCode.MDC-F30_RATE_LIMIT_STRATEGY_INVALID,
                    reason=f"Strategy '{strategy_value}' không hợp lệ. Chấp nhận: {[s.value for s in RateLimitStrategy]}",
                )

            policy = RateLimitPolicy(
                policy_id=item.get("policy_id", item.get("id", "")),
                name=item.get("name", ""),
                strategy=strategy,
                max_requests=item.get("max_requests", 100),
                window_seconds=item.get("window_seconds", 60),
                refill_rate=item.get("refill_rate", 0.0),
                burst_size=item.get("burst_size", 0),
                enabled=item.get("enabled", True),
                bypass_keys=item.get("bypass_keys", []),
                metadata=item.get("metadata", {}),
            )
            policies.append(policy)

        return policies

    @staticmethod
    def parse_quotas(yaml_data: list[dict[str, Any]]) -> list[QuotaConfig]:
        """Parse danh sách quota configs từ YAML.

        Args:
            yaml_data: Danh sách dict từ YAML

        Returns:
            Danh sách QuotaConfig

        Raises:
            MidicoderError: Nếu data không hợp lệ
        """
        quotas = []
        for item in yaml_data:
            level_value = item.get("level", "user")
            try:
                level = QuotaLevel(level_value)
            except ValueError:
                raise EM.raise_error(
                    ErrorCode.MDC-F30_QUOTA_LEVEL_INVALID,
                    reason=f"Level '{level_value}' không hợp lệ. Chấp nhận: {[l.value for l in QuotaLevel]}",
                )

            period_value = item.get("period", "day")
            try:
                period = QuotaPeriod(period_value)
            except ValueError:
                raise EM.raise_error(
                    ErrorCode.MDC-F30_QUOTA_CONFIG_INVALID,
                    reason=f"Period '{period_value}' không hợp lệ. Chấp nhận: {[p.value for p in QuotaPeriod]}",
                )

            config = QuotaConfig(
                config_id=item.get("config_id", item.get("id", "")),
                level=level,
                period=period,
                max_requests=item.get("max_requests", 1000),
                tenant_id=item.get("tenant_id", ""),
                endpoint=item.get("endpoint", ""),
                enabled=item.get("enabled", True),
                metadata=item.get("metadata", {}),
            )
            quotas.append(config)

        return quotas

    @staticmethod
    def parse_to_ir(yaml_dict: dict[str, Any]) -> RateLimitIR:
        """Parse toàn bộ YAML thành IR.

        Args:
            yaml_dict: Dict chứa 'policies' và 'quotas'

        Returns:
            RateLimitIR
        """
        return RateLimitIR(
            policies=RateLimitParser.parse_policies(yaml_dict.get("policies", [])),
            quotas=RateLimitParser.parse_quotas(yaml_dict.get("quotas", [])),
        )


__all__ = [
    "RateLimitIR",
    "RateLimitParser",
]
