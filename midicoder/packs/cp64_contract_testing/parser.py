# coding: utf-8
"""
Mô-đun parser cho CP64 — API Contract Testing (Pact).

Parse DSL dict (từ contract YAML) sang ContractIR — Intermediate Representation
cho consumer specs, provider verifiers, pact broker config, và contract settings.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp64_contract_testing.models import (
    ConsumerSpec,
    PactBrokerConfig,
    ProviderVerifier,
)


@dataclass
class ContractIR:
    """Intermediate Representation cho CP64.

    Gom tập tất cả cấu hình contract testing từ DSL, bao gồm
    consumer specs, provider verifiers, pact broker config,
    và các settings chung.

    Attributes:
        consumer_specs: Danh sách consumer-driven contract specs
        provider_verifiers: Danh sách provider verifier configs
        pact_broker_config: Cấu hình Pact Broker
        default_pact_version: Phiên bản Pact mặc định
        enable_auto_publish: Có bật auto-publish contracts không
    """
    consumer_specs: list[ConsumerSpec] = field(default_factory=list)
    provider_verifiers: list[ProviderVerifier] = field(default_factory=list)
    pact_broker_config: PactBrokerConfig | None = None
    default_pact_version: str = "2.0.0"
    enable_auto_publish: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ContractIR sang dict."""
        result: dict[str, Any] = {
            "consumer_specs": [c.to_dict() for c in self.consumer_specs],
            "provider_verifiers": [p.to_dict() for p in self.provider_verifiers],
            "default_pact_version": self.default_pact_version,
            "enable_auto_publish": self.enable_auto_publish,
        }
        if self.pact_broker_config is not None:
            result["pact_broker_config"] = self.pact_broker_config.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContractIR":
        """Tạo ContractIR từ dict."""
        consumer_specs = [ConsumerSpec.from_dict(c) for c in data.get("consumer_specs", [])]
        provider_verifiers = [ProviderVerifier.from_dict(p) for p in data.get("provider_verifiers", [])]
        broker_data = data.get("pact_broker_config", None)
        pact_broker_config = PactBrokerConfig.from_dict(broker_data) if broker_data else None
        return cls(
            consumer_specs=consumer_specs,
            provider_verifiers=provider_verifiers,
            pact_broker_config=pact_broker_config,
            default_pact_version=data.get("default_pact_version", "2.0.0"),
            enable_auto_publish=data.get("enable_auto_publish", False),
        )


def parse_consumer_specs(data: dict[str, Any]) -> list[ConsumerSpec]:
    """Parse danh sách consumer specs từ DSL dict.

    Args:
        data: DSL dict với key 'consumer_specs' hoặc 'contracts'

    Returns:
        Danh sách ConsumerSpec
    """
    raw = data.get("consumer_specs", data.get("contracts", []))
    return [ConsumerSpec.from_dict(c) for c in raw]


def parse_provider_verifiers(data: dict[str, Any]) -> list[ProviderVerifier]:
    """Parse danh sách provider verifiers từ DSL dict.

    Args:
        data: DSL dict với key 'provider_verifiers' hoặc 'verifiers'

    Returns:
        Danh sách ProviderVerifier
    """
    raw = data.get("provider_verifiers", data.get("verifiers", []))
    return [ProviderVerifier.from_dict(p) for p in raw]


def parse_to_ir(data: dict[str, Any]) -> ContractIR:
    """Parse DSL dict thành ContractIR.

    Args:
        data: DSL dict với consumer_specs, provider_verifiers, pact_broker_config

    Returns:
        ContractIR gom tập tất cả parsed data
    """
    consumer_specs = parse_consumer_specs(data)
    provider_verifiers = parse_provider_verifiers(data)
    broker_data = data.get("pact_broker_config", None)
    pact_broker_config = PactBrokerConfig.from_dict(broker_data) if broker_data else None

    return ContractIR(
        consumer_specs=consumer_specs,
        provider_verifiers=provider_verifiers,
        pact_broker_config=pact_broker_config,
        default_pact_version=data.get("default_pact_version", "2.0.0"),
        enable_auto_publish=data.get("enable_auto_publish", False),
    )


__all__ = [
    "ContractIR",
    "parse_consumer_specs",
    "parse_provider_verifiers",
    "parse_to_ir",
]
