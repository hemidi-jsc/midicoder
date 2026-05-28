# coding: utf-8
"""
Mô-đun parser cho I05 — Multi-Region & Geo-Replication.

Parse DSL dict (từ contract YAML) sang MultiRegionIR — Intermediate Representation
cho region configs, replication policies, geo routing rules, failover policies,
data residency rules, và health checks.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_infra_multi_region.models import (
    DataResidencyRule,
    FailoverPolicy,
    GeoRoutingRule,
    RegionConfig,
    RegionHealthCheck,
    ReplicationPolicy,
)


@dataclass
class MultiRegionIR:
    """Intermediate Representation cho CP28.

    Gom tập tất cả cấu hình multi-region và geo-replication từ DSL,
    bao gồm region configs, replication policies, geo routing rules,
    failover policies, data residency rules, và health checks.

    Attributes:
        regions: Danh sách RegionConfig
        replication_policies: Danh sách ReplicationPolicy
        geo_routing_rules: Danh sách GeoRoutingRule
        failover_policies: Danh sách FailoverPolicy
        data_residency_rules: Danh sách DataResidencyRule
        health_checks: Danh sách RegionHealthCheck
    """
    regions: list[RegionConfig] = field(default_factory=list)
    replication_policies: list[ReplicationPolicy] = field(default_factory=list)
    geo_routing_rules: list[GeoRoutingRule] = field(default_factory=list)
    failover_policies: list[FailoverPolicy] = field(default_factory=list)
    data_residency_rules: list[DataResidencyRule] = field(default_factory=list)
    health_checks: list[RegionHealthCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MultiRegionIR sang dict."""
        return {
            "regions": [r.to_dict() for r in self.regions],
            "replication_policies": [rp.to_dict() for rp in self.replication_policies],
            "geo_routing_rules": [gr.to_dict() for gr in self.geo_routing_rules],
            "failover_policies": [fp.to_dict() for fp in self.failover_policies],
            "data_residency_rules": [dr.to_dict() for dr in self.data_residency_rules],
            "health_checks": [hc.to_dict() for hc in self.health_checks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultiRegionIR":
        """Tạo MultiRegionIR từ dict."""
        return cls(
            regions=[RegionConfig.from_dict(r) for r in data.get("regions", [])],
            replication_policies=[ReplicationPolicy.from_dict(rp) for rp in data.get("replication_policies", [])],
            geo_routing_rules=[GeoRoutingRule.from_dict(gr) for gr in data.get("geo_routing_rules", [])],
            failover_policies=[FailoverPolicy.from_dict(fp) for fp in data.get("failover_policies", [])],
            data_residency_rules=[DataResidencyRule.from_dict(dr) for dr in data.get("data_residency_rules", [])],
            health_checks=[RegionHealthCheck.from_dict(hc) for hc in data.get("health_checks", [])],
        )


def parse_regions(data: dict[str, Any]) -> list[RegionConfig]:
    """Parse danh sách region configs từ DSL dict.

    Args:
        data: DSL dict với key 'regions'

    Returns:
        Danh sách RegionConfig
    """
    raw = data.get("regions", [])
    return [RegionConfig.from_dict(r) for r in raw]


def parse_replication_policies(data: dict[str, Any]) -> list[ReplicationPolicy]:
    """Parse danh sách replication policies từ DSL dict.

    Args:
        data: DSL dict với key 'replication_policies'

    Returns:
        Danh sách ReplicationPolicy
    """
    raw = data.get("replication_policies", [])
    return [ReplicationPolicy.from_dict(rp) for rp in raw]


def parse_geo_routing_rules(data: dict[str, Any]) -> list[GeoRoutingRule]:
    """Parse danh sách geo routing rules từ DSL dict.

    Args:
        data: DSL dict với key 'geo_routing_rules'

    Returns:
        Danh sách GeoRoutingRule
    """
    raw = data.get("geo_routing_rules", [])
    return [GeoRoutingRule.from_dict(gr) for gr in raw]


def parse_failover_policies(data: dict[str, Any]) -> list[FailoverPolicy]:
    """Parse danh sách failover policies từ DSL dict.

    Args:
        data: DSL dict với key 'failover_policies'

    Returns:
        Danh sách FailoverPolicy
    """
    raw = data.get("failover_policies", [])
    return [FailoverPolicy.from_dict(fp) for fp in raw]


def parse_data_residency_rules(data: dict[str, Any]) -> list[DataResidencyRule]:
    """Parse danh sách data residency rules từ DSL dict.

    Args:
        data: DSL dict với key 'data_residency_rules'

    Returns:
        Danh sách DataResidencyRule
    """
    raw = data.get("data_residency_rules", [])
    return [DataResidencyRule.from_dict(dr) for dr in raw]


def parse_health_checks(data: dict[str, Any]) -> list[RegionHealthCheck]:
    """Parse danh sách region health checks từ DSL dict.

    Args:
        data: DSL dict với key 'health_checks'

    Returns:
        Danh sách RegionHealthCheck
    """
    raw = data.get("health_checks", [])
    return [RegionHealthCheck.from_dict(hc) for hc in raw]


def parse_to_ir(data: dict[str, Any]) -> MultiRegionIR:
    """Parse DSL dict thành MultiRegionIR.

    Args:
        data: DSL dict với regions, replication_policies, geo_routing_rules,
              failover_policies, data_residency_rules, health_checks

    Returns:
        MultiRegionIR gom tập tất cả parsed data
    """
    return MultiRegionIR(
        regions=parse_regions(data),
        replication_policies=parse_replication_policies(data),
        geo_routing_rules=parse_geo_routing_rules(data),
        failover_policies=parse_failover_policies(data),
        data_residency_rules=parse_data_residency_rules(data),
        health_checks=parse_health_checks(data),
    )


__all__ = [
    "MultiRegionIR",
    "parse_regions",
    "parse_replication_policies",
    "parse_geo_routing_rules",
    "parse_failover_policies",
    "parse_data_residency_rules",
    "parse_health_checks",
    "parse_to_ir",
]
