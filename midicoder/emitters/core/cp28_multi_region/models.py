# coding: utf-8
"""
Mô-đun models cho CP28 — Multi-Region & Geo-Replication.

Định nghĩa các dataclass biểu diễn:
- RegionConfig: Định nghĩa region với cloud provider, availability zones, endpoint
- ReplicationPolicy: Chính sách replication cross-region (sync/async) với conflict resolution
- GeoRoutingRule: Quy tắc routing dựa trên độ trễ hoặc vị trí địa lý
- FailoverPolicy: Chính sách failover với RTO/RPO và tự động chuyển region
- DataResidencyRule: Quy tắc data residency per region/tenant theo regulation
- RegionHealthCheck: Health check per region với auto-failover threshold

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ===========================================================================
# RegionConfig
# ===========================================================================


@dataclass
class RegionConfig:
    """Định nghĩa region cho multi-region deployment.

    Mô tả một khu vực triển khai bao gồm cloud provider, danh sách
    availability zones, trạng thái primary, và endpoint URL để kết nối.

    Attributes:
        id: ID duy nhất của region
        name: Tên hiển thị của region (vd: "Asia Pacific (Singapore)")
        cloud_provider: Nhà cung cấp cloud (aws, gcp, azure)
        availability_zones: Danh sách availability zone names
        primary: Có phải là region chính không
        endpoint_url: URL endpoint để kết nối đến region
    """
    id: str
    name: str
    cloud_provider: str = "aws"
    availability_zones: list[str] = field(default_factory=list)
    primary: bool = False
    endpoint_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RegionConfig sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "cloud_provider": self.cloud_provider,
            "availability_zones": self.availability_zones,
            "primary": self.primary,
            "endpoint_url": self.endpoint_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegionConfig":
        """Tạo RegionConfig từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            cloud_provider=data.get("cloud_provider", "aws"),
            availability_zones=data.get("availability_zones", []),
            primary=data.get("primary", False),
            endpoint_url=data.get("endpoint_url", ""),
        )


# ===========================================================================
# GeoRegionEntry (nested helper cho GeoRoutingRule)
# ===========================================================================


@dataclass
class GeoRegionEntry:
    """Entry cho region trong geo routing rule.

    Đại diện cho một region cùng với trọng số routing,
    dùng trong GeoRoutingRule để phân phối traffic theo độ trễ hoặc geographic.

    Attributes:
        region: Region ID
        weight: Trọng số routing (mặc định 1)
    """
    region: str
    weight: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "region": self.region,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoRegionEntry":
        return cls(
            region=data["region"],
            weight=data.get("weight", 1),
        )


# ===========================================================================
# ReplicationPolicy
# ===========================================================================


@dataclass
class ReplicationPolicy:
    """Chính sách replication cross-region.

    Định nghĩa cách dữ liệu được nhân bản giữa các region, bao gồm
    mode (sync/async), vùng nguồn, vùng đích, ngưỡng lag, chiến lược
    giải quyết xung đột, và danh sách bảng cần replicate.

    Attributes:
        id: ID duy nhất của replication policy
        name: Tên hiển thị
        mode: Mode replication ("sync" hoặc "async")
        source_region: Region ID của vùng nguồn
        target_regions: Danh sách region IDs đích
        lag_threshold_ms: Ngưỡng lag tối đa (millisecond)
        conflict_resolution: Chiến lược giải quyết xung đột ("source_wins", "target_wins", "timestamp")
        tables: Danh sách table names cần replicate
    """
    id: str
    name: str
    mode: str = "async"
    source_region: str = ""
    target_regions: list[str] = field(default_factory=list)
    lag_threshold_ms: int = 1000
    conflict_resolution: str = "source_wins"
    tables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ReplicationPolicy sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "source_region": self.source_region,
            "target_regions": self.target_regions,
            "lag_threshold_ms": self.lag_threshold_ms,
            "conflict_resolution": self.conflict_resolution,
            "tables": self.tables,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplicationPolicy":
        """Tạo ReplicationPolicy từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            mode=data.get("mode", "async"),
            source_region=data.get("source_region", ""),
            target_regions=data.get("target_regions", []),
            lag_threshold_ms=data.get("lag_threshold_ms", 1000),
            conflict_resolution=data.get("conflict_resolution", "source_wins"),
            tables=data.get("tables", []),
        )


# ===========================================================================
# GeoRoutingRule
# ===========================================================================


@dataclass
class GeoRoutingRule:
    """Quy tắc routing dựa trên độ trễ hoặc vị trí địa lý.

    Định nghĩa cách traffic được phân phối đến các region dựa trên
    chiến lược (latency, geographic, hoặc weight), vùng đích, fallback
    region, và đường dẫn health check.

    Attributes:
        id: ID duy nhất của routing rule
        name: Tên hiển thị
        strategy: Chiến lược routing ("latency", "geographic", "weight")
        regions: Danh sách GeoRegionEntry (region + weight)
        fallback_region: Region ID fallback khi tất cả region khác không khả dụng
        health_check_path: Đường dẫn health check endpoint
    """
    id: str
    name: str
    strategy: str = "latency"
    regions: list[GeoRegionEntry] = field(default_factory=list)
    fallback_region: str = ""
    health_check_path: str = "/health"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển GeoRoutingRule sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "strategy": self.strategy,
            "regions": [r.to_dict() for r in self.regions],
            "fallback_region": self.fallback_region,
            "health_check_path": self.health_check_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoRoutingRule":
        """Tạo GeoRoutingRule từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            strategy=data.get("strategy", "latency"),
            regions=[GeoRegionEntry.from_dict(r) for r in data.get("regions", [])],
            fallback_region=data.get("fallback_region", ""),
            health_check_path=data.get("health_check_path", "/health"),
        )


# ===========================================================================
# FailoverPolicy
# ===========================================================================


@dataclass
class FailoverPolicy:
    """Chính sách failover tự động.

    Định nghĩa cách hệ thống chuyển region khi xảy ra sự cố, bao gồm
    trigger mechanism, danh sách region theo thứ tự ưu tiên, RTO/RPO
    targets, DNS TTL, và trạng thái tự động failover.

    Attributes:
        id: ID duy nhất của failover policy
        name: Tên hiển thị
        trigger: Trigger mechanism ("health_check", "manual", "auto")
        regions: Danh sách region IDs theo thứ tự ưu tiên failover
        rto_minutes: Recovery Time Objective (phút)
        rpo_minutes: Recovery Point Objective (phút)
        dns_ttl_seconds: DNS TTL để đảm bảo failover nhanh
        auto_failover_enabled: Có bật failover tự động không
    """
    id: str
    name: str
    trigger: str = "health_check"
    regions: list[str] = field(default_factory=list)
    rto_minutes: int = 5
    rpo_minutes: int = 1
    dns_ttl_seconds: int = 60
    auto_failover_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FailoverPolicy sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "trigger": self.trigger,
            "regions": self.regions,
            "rto_minutes": self.rto_minutes,
            "rpo_minutes": self.rpo_minutes,
            "dns_ttl_seconds": self.dns_ttl_seconds,
            "auto_failover_enabled": self.auto_failover_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FailoverPolicy":
        """Tạo FailoverPolicy từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            trigger=data.get("trigger", "health_check"),
            regions=data.get("regions", []),
            rto_minutes=data.get("rto_minutes", 5),
            rpo_minutes=data.get("rpo_minutes", 1),
            dns_ttl_seconds=data.get("dns_ttl_seconds", 60),
            auto_failover_enabled=data.get("auto_failover_enabled", True),
        )


# ===========================================================================
# DataResidencyRule
# ===========================================================================


@dataclass
class DataResidencyRule:
    """Quy tắc data residency per region/tenant.

    Thực thi chính sách data residency để đảm bảo dữ liệu được lưu trữ
    trong các khu vực địa lý tuân thủ regulation (GDPR, CCPA, v.v.).

    Attributes:
        id: ID duy nhất của data residency rule
        name: Tên hiển thị
        region: Region ID áp dụng quy tắc này
        allowed_countries: Danh sách mã quốc gia được phép lưu trữ dữ liệu
        tenant_ids: Danh sách tenant IDs áp dụng quy tắc
        data_categories: Danh sách category dữ liệu (pi, financial, health, v.v.)
        enforcement: Chế độ thực thi ("strict" hoặc "log_only")
    """
    id: str
    name: str
    region: str
    allowed_countries: list[str] = field(default_factory=list)
    tenant_ids: list[str] = field(default_factory=list)
    data_categories: list[str] = field(default_factory=list)
    enforcement: str = "strict"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DataResidencyRule sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "allowed_countries": self.allowed_countries,
            "tenant_ids": self.tenant_ids,
            "data_categories": self.data_categories,
            "enforcement": self.enforcement,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataResidencyRule":
        """Tạo DataResidencyRule từ dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            region=data["region"],
            allowed_countries=data.get("allowed_countries", []),
            tenant_ids=data.get("tenant_ids", []),
            data_categories=data.get("data_categories", []),
            enforcement=data.get("enforcement", "strict"),
        )


# ===========================================================================
# RegionHealthCheck
# ===========================================================================


@dataclass
class RegionHealthCheck:
    """Health check per region với auto-failover threshold.

    Định nghĩa health probe cho từng region để phát hiện sự cố và
    kích hoạt failover khi vượt quá ngưỡng unhealthy threshold.

    Attributes:
        id: ID duy nhất của health check
        region: Region ID cần kiểm tra
        endpoint_url: URL endpoint để thực hiện health check
        interval_seconds: Khoảng thời gian giữa các lần check (giây)
        timeout_seconds: Timeout cho mỗi lần check (giây)
        unhealthy_threshold: Số lần check thất bại liên tiếp để đánh dấu unhealthy
        healthy_threshold: Số lần check thành công liên tiếp để đánh dấu healthy
        check_type: Loại health check ("http", "tcp", "custom")
    """
    id: str
    region: str
    endpoint_url: str
    interval_seconds: int = 30
    timeout_seconds: int = 5
    unhealthy_threshold: int = 3
    healthy_threshold: int = 2
    check_type: str = "http"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RegionHealthCheck sang dict."""
        return {
            "id": self.id,
            "region": self.region,
            "endpoint_url": self.endpoint_url,
            "interval_seconds": self.interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "unhealthy_threshold": self.unhealthy_threshold,
            "healthy_threshold": self.healthy_threshold,
            "check_type": self.check_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegionHealthCheck":
        """Tạo RegionHealthCheck từ dict."""
        return cls(
            id=data["id"],
            region=data["region"],
            endpoint_url=data["endpoint_url"],
            interval_seconds=data.get("interval_seconds", 30),
            timeout_seconds=data.get("timeout_seconds", 5),
            unhealthy_threshold=data.get("unhealthy_threshold", 3),
            healthy_threshold=data.get("healthy_threshold", 2),
            check_type=data.get("check_type", "http"),
        )
