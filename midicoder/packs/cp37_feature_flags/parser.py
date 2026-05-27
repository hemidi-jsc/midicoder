# coding: utf-8
"""
Mô-đun parser cho CP37 — Feature Flags & Dynamic Config.

Parse DSL dict (từ contract YAML) sang FeatureFlagIR — Intermediate Representation
cho feature flags, A/B experiments, và dynamic configs.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp37_feature_flags.models import (
    ABExperiment,
    ABVariant,
    ConfigScope,
    ConfigValueType,
    ConditionType,
    DynamicConfig,
    FeatureFlag,
    FlagVariantType,
    TargetingRule,
)


@dataclass
class FeatureFlagIR:
    """Intermediate Representation cho CP37.

    Gom tập tất cả cấu hình feature flags, A/B experiments,
    và dynamic configs từ DSL.

    Attributes:
        flags: Danh sách feature flags
        experiments: Danh sách A/B experiments
        configs: Danh sách dynamic configs
    """
    flags: list[FeatureFlag] = field(default_factory=list)
    experiments: list[ABExperiment] = field(default_factory=list)
    configs: list[DynamicConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FeatureFlagIR sang dict."""
        return {
            "flags": [f.to_dict() for f in self.flags],
            "experiments": [e.to_dict() for e in self.experiments],
            "configs": [c.to_dict() for c in self.configs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeatureFlagIR":
        """Tạo FeatureFlagIR từ dict."""
        flags = [FeatureFlag.from_dict(f) for f in data.get("flags", [])]
        experiments = [ABExperiment.from_dict(e) for e in data.get("experiments", [])]
        configs = [DynamicConfig.from_dict(c) for c in data.get("configs", [])]
        return cls(flags=flags, experiments=experiments, configs=configs)


def parse_feature_flags(data: dict[str, Any]) -> list[FeatureFlag]:
    """Parse danh sách feature flags từ DSL dict.

    Args:
        data: DSL dict với key 'feature_flags' hoặc 'flags'

    Returns:
        Danh sách FeatureFlag
    """
    raw_flags = data.get("feature_flags", data.get("flags", []))
    flags = []
    for f in raw_flags:
        rules_data = f.get("targeting_rules", [])
        rules = []
        for r in rules_data:
            rules.append(TargetingRule(
                rule_id=r.get("rule_id", f.get("flag_key", "rule") + "_r1"),
                condition_type=ConditionType(r.get("condition_type", "role")),
                condition=r.get("condition", {}),
                value=r.get("value", True),
                priority=r.get("priority", 0),
            ))

        flags.append(FeatureFlag(
            flag_key=f.get("flag_key", ""),
            name=f.get("name", ""),
            description=f.get("description", ""),
            variant_type=FlagVariantType(f.get("variant_type", "boolean")),
            default_enabled=f.get("default_enabled", False),
            percentage=f.get("percentage", 0),
            targeting_rules=rules,
            environments=f.get("environments", []),
            tenant_overrides=f.get("tenant_overrides", {}),
            is_active=f.get("is_active", True),
        ))
    return flags


def parse_experiments(data: dict[str, Any]) -> list[ABExperiment]:
    """Parse danh sách A/B experiments từ DSL dict.

    Args:
        data: DSL dict với key 'experiments' hoặc 'ab_experiments'

    Returns:
        Danh sách ABExperiment
    """
    raw_experiments = data.get("experiments", data.get("ab_experiments", []))
    experiments = []
    for exp in raw_experiments:
        variants_data = exp.get("variants", [])
        variants = [ABVariant(
            variant_key=v.get("variant_key", "control"),
            name=v.get("name", ""),
            weight=v.get("weight", 50.0),
            metadata=v.get("metadata", {}),
        ) for v in variants_data]

        experiments.append(ABExperiment(
            experiment_key=exp.get("experiment_key", ""),
            name=exp.get("name", ""),
            description=exp.get("description", ""),
            variants=variants,
            is_active=exp.get("is_active", True),
            traffic_percentage=exp.get("traffic_percentage", 100.0),
            success_metric=exp.get("success_metric", "conversion_rate"),
        ))
    return experiments


def parse_configs(data: dict[str, Any]) -> list[DynamicConfig]:
    """Parse danh sách dynamic configs từ DSL dict.

    Args:
        data: DSL dict với key 'dynamic_configs' hoặc 'configs'

    Returns:
        Danh sách DynamicConfig
    """
    raw_configs = data.get("dynamic_configs", data.get("configs", []))
    configs = []
    for c in raw_configs:
        configs.append(DynamicConfig(
            config_key=c.get("config_key", ""),
            value=c.get("value"),
            value_type=ConfigValueType(c.get("value_type", "string")),
            scope=ConfigScope(c.get("scope", "global")),
            tenant_id=c.get("tenant_id"),
            environment=c.get("environment"),
            is_encrypted=c.get("is_encrypted", False),
        ))
    return configs


def parse_to_ir(data: dict[str, Any]) -> FeatureFlagIR:
    """Parse DSL dict thành FeatureFlagIR.

    Args:
        data: DSL dict với feature_flags, experiments, configs

    Returns:
        FeatureFlagIR gom tập tất cả parsed data
    """
    flags = parse_feature_flags(data)
    experiments = parse_experiments(data)
    configs = parse_configs(data)
    return FeatureFlagIR(flags=flags, experiments=experiments, configs=configs)


__all__ = [
    "FeatureFlagIR",
    "parse_feature_flags",
    "parse_experiments",
    "parse_configs",
    "parse_to_ir",
]
