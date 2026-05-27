# coding: utf-8
"""
Mô-đun recipes cho CP28 — Multi-Region & Geo-Replication.

Cung cấp các recipe để build MultiRegionIR cho các use case phổ biến:
- basic_multi_region_recipe: 2 region với async replication
- full_geo_replication_recipe: 3+ region, sync replication, geo-routing, auto-failover
- data_residency_recipe: Data residency rules + health checks cho compliance

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp28_multi_region.parser import (
    MultiRegionIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: MultiRegionIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: MultiRegionIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def basic_multi_region_recipe(app_name: str) -> RecipeOutput:
    """Recipe cơ bản: 2 region với async replication.

    - 2 region: Primary (ap-southeast-1) + Secondary (us-east-1)
    - 1 async replication policy từ primary đến secondary
    - 1 health check cho mỗi region

    Args:
        app_name: Tên ứng dụng

    Returns:
        RecipeOutput chứa MultiRegionIR
    """
    primary_endpoint = f"https://{app_name}-primary.ap-southeast-1.amazonaws.com"
    secondary_endpoint = f"https://{app_name}-secondary.us-east-1.amazonaws.com"

    data = {
        "regions": [
            {
                "id": "ap-southeast-1",
                "name": "Asia Pacific (Singapore)",
                "cloud_provider": "aws",
                "availability_zones": ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"],
                "primary": True,
                "endpoint_url": primary_endpoint,
            },
            {
                "id": "us-east-1",
                "name": "US East (N. Virginia)",
                "cloud_provider": "aws",
                "availability_zones": ["us-east-1a", "us-east-1b"],
                "primary": False,
                "endpoint_url": secondary_endpoint,
            },
        ],
        "replication_policies": [
            {
                "id": "repl-primary-to-secondary",
                "name": "Primary to Secondary Async Replication",
                "mode": "async",
                "source_region": "ap-southeast-1",
                "target_regions": ["us-east-1"],
                "lag_threshold_ms": 5000,
                "conflict_resolution": "source_wins",
                "tables": ["users", "orders", "products"],
            }
        ],
        "health_checks": [
            {
                "id": "hc-ap-southeast-1",
                "region": "ap-southeast-1",
                "endpoint_url": f"{primary_endpoint}/health",
                "interval_seconds": 30,
                "timeout_seconds": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2,
                "check_type": "http",
            },
            {
                "id": "hc-us-east-1",
                "region": "us-east-1",
                "endpoint_url": f"{secondary_endpoint}/health",
                "interval_seconds": 30,
                "timeout_seconds": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2,
                "check_type": "http",
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="basic_multi_region_recipe",
        description="2 region (ap-southeast-1 primary, us-east-1 secondary) với async replication",
        ir=ir,
        raw_data=data,
    )


def full_geo_replication_recipe(app_name: str) -> RecipeOutput:
    """Recipe đầy đủ: 3+ region, sync replication, geo-routing, auto-failover.

    - 3 region: APAC (primary), US-East, EU-West
    - Sync replication từ primary đến tất cả secondary
    - Geo routing rule với latency-based strategy
    - Auto-failover policy với RTO 5 phút, RPO 1 phút
    - Health check cho mỗi region

    Args:
        app_name: Tên ứng dụng

    Returns:
        RecipeOutput chứa MultiRegionIR
    """
    apac_endpoint = f"https://{app_name}.ap-southeast-1.cloud.example.com"
    useast_endpoint = f"https://{app_name}.us-east-1.cloud.example.com"
    euwest_endpoint = f"https://{app_name}.eu-west-1.cloud.example.com"

    data = {
        "regions": [
            {
                "id": "ap-southeast-1",
                "name": "Asia Pacific (Singapore)",
                "cloud_provider": "aws",
                "availability_zones": ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"],
                "primary": True,
                "endpoint_url": apac_endpoint,
            },
            {
                "id": "us-east-1",
                "name": "US East (N. Virginia)",
                "cloud_provider": "aws",
                "availability_zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "primary": False,
                "endpoint_url": useast_endpoint,
            },
            {
                "id": "eu-west-1",
                "name": "EU (Ireland)",
                "cloud_provider": "aws",
                "availability_zones": ["eu-west-1a", "eu-west-1b"],
                "primary": False,
                "endpoint_url": euwest_endpoint,
            },
        ],
        "replication_policies": [
            {
                "id": "repl-sync-primary-to-all",
                "name": "Sync Replication from Primary to All Regions",
                "mode": "sync",
                "source_region": "ap-southeast-1",
                "target_regions": ["us-east-1", "eu-west-1"],
                "lag_threshold_ms": 100,
                "conflict_resolution": "timestamp",
                "tables": ["users", "orders", "products", "payments"],
            }
        ],
        "geo_routing_rules": [
            {
                "id": "geo-route-primary",
                "name": "Global Latency-Based Routing",
                "strategy": "latency",
                "regions": [
                    {"region": "ap-southeast-1", "weight": 1},
                    {"region": "us-east-1", "weight": 1},
                    {"region": "eu-west-1", "weight": 1},
                ],
                "fallback_region": "ap-southeast-1",
                "health_check_path": "/health",
            }
        ],
        "failover_policies": [
            {
                "id": "failover-auto",
                "name": "Automated Multi-Region Failover",
                "trigger": "auto",
                "regions": ["ap-southeast-1", "us-east-1", "eu-west-1"],
                "rto_minutes": 5,
                "rpo_minutes": 1,
                "dns_ttl_seconds": 60,
                "auto_failover_enabled": True,
            }
        ],
        "health_checks": [
            {
                "id": "hc-ap-southeast-1",
                "region": "ap-southeast-1",
                "endpoint_url": f"{apac_endpoint}/health",
                "interval_seconds": 10,
                "timeout_seconds": 3,
                "unhealthy_threshold": 2,
                "healthy_threshold": 2,
                "check_type": "http",
            },
            {
                "id": "hc-us-east-1",
                "region": "us-east-1",
                "endpoint_url": f"{useast_endpoint}/health",
                "interval_seconds": 10,
                "timeout_seconds": 3,
                "unhealthy_threshold": 2,
                "healthy_threshold": 2,
                "check_type": "http",
            },
            {
                "id": "hc-eu-west-1",
                "region": "eu-west-1",
                "endpoint_url": f"{euwest_endpoint}/health",
                "interval_seconds": 10,
                "timeout_seconds": 3,
                "unhealthy_threshold": 2,
                "healthy_threshold": 2,
                "check_type": "http",
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_geo_replication_recipe",
        description="3 region với sync replication, latency-based geo-routing, và auto-failover (RTO=5m, RPO=1m)",
        ir=ir,
        raw_data=data,
    )


def data_residency_recipe(app_name: str) -> RecipeOutput:
    """Recipe cho compliance: data residency rules + health checks.

    - 2 region: EU (dành cho tenant EU) và APAC (dành cho tenant APAC)
    - Data residency rules với strict enforcement, phân theo quốc gia
    - Health check cho mỗi region
    - Async replication chỉ trong cùng khu vực pháp lý

    Args:
        app_name: Tên ứng dụng

    Returns:
        RecipeOutput chứa MultiRegionIR
    """
    eu_endpoint = f"https://{app_name}.eu-west-1.cloud.example.com"
    apac_endpoint = f"https://{app_name}.ap-southeast-1.cloud.example.com"

    data = {
        "regions": [
            {
                "id": "eu-west-1",
                "name": "EU (Ireland)",
                "cloud_provider": "aws",
                "availability_zones": ["eu-west-1a", "eu-west-1b", "eu-west-1c"],
                "primary": False,
                "endpoint_url": eu_endpoint,
            },
            {
                "id": "ap-southeast-1",
                "name": "Asia Pacific (Singapore)",
                "cloud_provider": "aws",
                "availability_zones": ["ap-southeast-1a", "ap-southeast-1b"],
                "primary": True,
                "endpoint_url": apac_endpoint,
            },
        ],
        "replication_policies": [
            {
                "id": "repl-intra-eu",
                "name": "Intra-EU Async Replication",
                "mode": "async",
                "source_region": "eu-west-1",
                "target_regions": [],
                "lag_threshold_ms": 3000,
                "conflict_resolution": "source_wins",
                "tables": ["users", "orders", "pii_data"],
            }
        ],
        "data_residency_rules": [
            {
                "id": "dr-eu-gdpr",
                "name": "EU GDPR Data Residency",
                "region": "eu-west-1",
                "allowed_countries": ["DE", "FR", "IE", "NL", "BE", "AT"],
                "tenant_ids": ["tenant-eu-001", "tenant-eu-002"],
                "data_categories": ["pii", "financial", "health"],
                "enforcement": "strict",
            },
            {
                "id": "dr-apac-pdpa",
                "name": "APAC PDPA Data Residency",
                "region": "ap-southeast-1",
                "allowed_countries": ["SG", "MY", "AU", "NZ"],
                "tenant_ids": ["tenant-apac-001", "tenant-apac-002"],
                "data_categories": ["pii", "financial"],
                "enforcement": "strict",
            },
        ],
        "health_checks": [
            {
                "id": "hc-eu-west-1",
                "region": "eu-west-1",
                "endpoint_url": f"{eu_endpoint}/health",
                "interval_seconds": 15,
                "timeout_seconds": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2,
                "check_type": "http",
            },
            {
                "id": "hc-ap-southeast-1",
                "region": "ap-southeast-1",
                "endpoint_url": f"{apac_endpoint}/health",
                "interval_seconds": 15,
                "timeout_seconds": 5,
                "unhealthy_threshold": 3,
                "healthy_threshold": 2,
                "check_type": "http",
            },
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="data_residency_recipe",
        description="Data residency compliance — EU GDPR + APAC PDPA với strict enforcement và health checks",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "basic_multi_region_recipe",
    "full_geo_replication_recipe",
    "data_residency_recipe",
]
