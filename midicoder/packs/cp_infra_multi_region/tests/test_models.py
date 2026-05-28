# coding: utf-8
"""
Tests cho I05 — Multi-Region models.

Kiểm tra:
- RegionConfig: creation, to_dict, from_dict
- GeoRegionEntry: creation, to_dict, from_dict
- ReplicationPolicy: creation, to_dict, from_dict
- GeoRoutingRule: creation, to_dict, from_dict
- FailoverPolicy: creation, to_dict, from_dict
- DataResidencyRule: creation, to_dict, from_dict
- RegionHealthCheck: creation, to_dict, from_dict

Author: Midicoder Team
Version: 2.0.0
"""

import pytest

from midicoder.packs.cp_infra_multi_region.models import (
    DataResidencyRule,
    FailoverPolicy,
    GeoRegionEntry,
    GeoRoutingRule,
    RegionConfig,
    RegionHealthCheck,
    ReplicationPolicy,
)


class TestRegionConfig:
    """Tests cho RegionConfig dataclass."""

    def test_creation(self):
        rc = RegionConfig(
            id="ap-southeast-1",
            name="Asia Pacific (Singapore)",
            cloud_provider="aws",
            availability_zones=["ap-southeast-1a", "ap-southeast-1b"],
            primary=True,
            endpoint_url="https://example.ap-southeast-1.amazonaws.com",
        )
        assert rc.id == "ap-southeast-1"
        assert rc.cloud_provider == "aws"
        assert rc.primary is True
        assert len(rc.availability_zones) == 2

    def test_creation_defaults(self):
        rc = RegionConfig(id="test", name="Test Region")
        assert rc.cloud_provider == "aws"
        assert rc.availability_zones == []
        assert rc.primary is False
        assert rc.endpoint_url == ""

    def test_to_dict(self):
        rc = RegionConfig(
            id="us-east-1",
            name="US East",
            cloud_provider="gcp",
            availability_zones=["us-east-1a"],
            primary=False,
            endpoint_url="https://example.us-east-1.gcp.com",
        )
        d = rc.to_dict()
        assert d["id"] == "us-east-1"
        assert d["cloud_provider"] == "gcp"
        assert d["primary"] is False
        assert len(d["availability_zones"]) == 1

    def test_from_dict(self):
        data = {
            "id": "eu-west-1",
            "name": "EU West",
            "cloud_provider": "azure",
            "availability_zones": ["eu-west-1a", "eu-west-1b"],
            "primary": True,
            "endpoint_url": "https://example.azure.europe.com",
        }
        rc = RegionConfig.from_dict(data)
        assert rc.id == "eu-west-1"
        assert rc.name == "EU West"
        assert rc.cloud_provider == "azure"
        assert rc.primary is True

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal"}
        rc = RegionConfig.from_dict(data)
        assert rc.cloud_provider == "aws"
        assert rc.availability_zones == []
        assert rc.primary is False

    def test_roundtrip(self):
        rc = RegionConfig(
            id="test-region",
            name="Test",
            cloud_provider="aws",
            availability_zones=["a", "b"],
            primary=True,
            endpoint_url="https://test.com",
        )
        rc2 = RegionConfig.from_dict(rc.to_dict())
        assert rc2.id == rc.id
        assert rc2.name == rc.name
        assert rc2.cloud_provider == rc.cloud_provider
        assert rc2.primary == rc.primary


class TestGeoRegionEntry:
    """Tests cho GeoRegionEntry dataclass."""

    def test_creation(self):
        entry = GeoRegionEntry(region="ap-southeast-1", weight=3)
        assert entry.region == "ap-southeast-1"
        assert entry.weight == 3

    def test_creation_default_weight(self):
        entry = GeoRegionEntry(region="us-east-1")
        assert entry.weight == 1

    def test_to_dict(self):
        entry = GeoRegionEntry(region="eu-west-1", weight=5)
        d = entry.to_dict()
        assert d["region"] == "eu-west-1"
        assert d["weight"] == 5

    def test_from_dict(self):
        data = {"region": "test-region", "weight": 10}
        entry = GeoRegionEntry.from_dict(data)
        assert entry.region == "test-region"
        assert entry.weight == 10

    def test_from_dict_default_weight(self):
        data = {"region": "test-region"}
        entry = GeoRegionEntry.from_dict(data)
        assert entry.weight == 1


class TestReplicationPolicy:
    """Tests cho ReplicationPolicy dataclass."""

    def test_creation(self):
        rp = ReplicationPolicy(
            id="repl-1",
            name="Primary to Secondary",
            mode="sync",
            source_region="ap-southeast-1",
            target_regions=["us-east-1", "eu-west-1"],
            lag_threshold_ms=100,
            conflict_resolution="timestamp",
            tables=["users", "orders"],
        )
        assert rp.id == "repl-1"
        assert rp.mode == "sync"
        assert len(rp.target_regions) == 2

    def test_creation_defaults(self):
        rp = ReplicationPolicy(id="test", name="Test")
        assert rp.mode == "async"
        assert rp.source_region == ""
        assert rp.lag_threshold_ms == 1000
        assert rp.conflict_resolution == "source_wins"

    def test_to_dict(self):
        rp = ReplicationPolicy(
            id="repl-2",
            name="Async Replication",
            mode="async",
            source_region="us-east-1",
            target_regions=["eu-west-1"],
            lag_threshold_ms=5000,
            conflict_resolution="source_wins",
            tables=["products"],
        )
        d = rp.to_dict()
        assert d["id"] == "repl-2"
        assert d["mode"] == "async"
        assert d["lag_threshold_ms"] == 5000

    def test_from_dict(self):
        data = {
            "id": "repl-full",
            "name": "Full Replication",
            "mode": "sync",
            "source_region": "primary",
            "target_regions": ["secondary-1", "secondary-2"],
            "lag_threshold_ms": 50,
            "conflict_resolution": "timestamp",
            "tables": ["all_tables"],
        }
        rp = ReplicationPolicy.from_dict(data)
        assert rp.mode == "sync"
        assert len(rp.tables) == 1

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal"}
        rp = ReplicationPolicy.from_dict(data)
        assert rp.mode == "async"
        assert rp.conflict_resolution == "source_wins"

    def test_roundtrip(self):
        rp = ReplicationPolicy(
            id="rt-test",
            name="Roundtrip",
            mode="sync",
            source_region="src",
            target_regions=["dst1"],
            lag_threshold_ms=200,
            conflict_resolution="timestamp",
            tables=["t1"],
        )
        rp2 = ReplicationPolicy.from_dict(rp.to_dict())
        assert rp2.id == rp.id
        assert rp2.mode == rp.mode
        assert rp2.tables == rp.tables


class TestGeoRoutingRule:
    """Tests cho GeoRoutingRule dataclass."""

    def test_creation(self):
        rule = GeoRoutingRule(
            id="geo-1",
            name="Global Routing",
            strategy="latency",
            regions=[GeoRegionEntry("ap-southeast-1", 1), GeoRegionEntry("us-east-1", 2)],
            fallback_region="ap-southeast-1",
            health_check_path="/health",
        )
        assert rule.strategy == "latency"
        assert len(rule.regions) == 2

    def test_creation_defaults(self):
        rule = GeoRoutingRule(id="test", name="Test")
        assert rule.strategy == "latency"
        assert rule.regions == []
        assert rule.health_check_path == "/health"

    def test_to_dict(self):
        rule = GeoRoutingRule(
            id="geo-2",
            name="Weighted Routing",
            strategy="weight",
            regions=[GeoRegionEntry("r1", 5)],
            fallback_region="r1",
        )
        d = rule.to_dict()
        assert d["strategy"] == "weight"
        assert len(d["regions"]) == 1
        assert d["regions"][0]["weight"] == 5

    def test_from_dict(self):
        data = {
            "id": "geo-full",
            "name": "Full Geo",
            "strategy": "geographic",
            "regions": [
                {"region": "ap-southeast-1", "weight": 1},
                {"region": "us-east-1", "weight": 1},
            ],
            "fallback_region": "ap-southeast-1",
            "health_check_path": "/ping",
        }
        rule = GeoRoutingRule.from_dict(data)
        assert rule.strategy == "geographic"
        assert len(rule.regions) == 2
        assert rule.health_check_path == "/ping"

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal"}
        rule = GeoRoutingRule.from_dict(data)
        assert rule.strategy == "latency"
        assert rule.regions == []

    def test_roundtrip(self):
        rule = GeoRoutingRule(
            id="rt",
            name="RT",
            strategy="latency",
            regions=[GeoRegionEntry("r1", 3)],
            fallback_region="r1",
        )
        rule2 = GeoRoutingRule.from_dict(rule.to_dict())
        assert rule2.strategy == rule.strategy
        assert len(rule2.regions) == 1
        assert rule2.regions[0].weight == 3


class TestFailoverPolicy:
    """Tests cho FailoverPolicy dataclass."""

    def test_creation(self):
        fp = FailoverPolicy(
            id="failover-1",
            name="Auto Failover",
            trigger="auto",
            regions=["ap-southeast-1", "us-east-1"],
            rto_minutes=5,
            rpo_minutes=1,
            dns_ttl_seconds=60,
            auto_failover_enabled=True,
        )
        assert fp.trigger == "auto"
        assert fp.rto_minutes == 5

    def test_creation_defaults(self):
        fp = FailoverPolicy(id="test", name="Test")
        assert fp.trigger == "health_check"
        assert fp.rto_minutes == 5
        assert fp.auto_failover_enabled is True

    def test_to_dict(self):
        fp = FailoverPolicy(
            id="fo-1",
            name="Manual Failover",
            trigger="manual",
            regions=["r1"],
            rto_minutes=10,
            rpo_minutes=5,
        )
        d = fp.to_dict()
        assert d["trigger"] == "manual"
        assert d["rto_minutes"] == 10

    def test_from_dict(self):
        data = {
            "id": "fo-full",
            "name": "Full",
            "trigger": "auto",
            "regions": ["r1", "r2"],
            "rto_minutes": 3,
            "rpo_minutes": 1,
            "dns_ttl_seconds": 30,
            "auto_failover_enabled": True,
        }
        fp = FailoverPolicy.from_dict(data)
        assert fp.trigger == "auto"
        assert len(fp.regions) == 2
        assert fp.dns_ttl_seconds == 30

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal"}
        fp = FailoverPolicy.from_dict(data)
        assert fp.trigger == "health_check"
        assert fp.auto_failover_enabled is True

    def test_roundtrip(self):
        fp = FailoverPolicy(
            id="rt",
            name="RT",
            trigger="auto",
            regions=["a", "b"],
            rto_minutes=5,
            rpo_minutes=1,
        )
        fp2 = FailoverPolicy.from_dict(fp.to_dict())
        assert fp2.trigger == fp.trigger
        assert fp2.rto_minutes == fp.rto_minutes


class TestDataResidencyRule:
    """Tests cho DataResidencyRule dataclass."""

    def test_creation(self):
        dr = DataResidencyRule(
            id="dr-1",
            name="EU GDPR",
            region="eu-west-1",
            allowed_countries=["DE", "FR", "IE"],
            tenant_ids=["tenant-eu-001"],
            data_categories=["pii", "financial"],
            enforcement="strict",
        )
        assert dr.enforcement == "strict"
        assert len(dr.allowed_countries) == 3

    def test_creation_defaults(self):
        dr = DataResidencyRule(id="test", name="Test", region="r1")
        assert dr.allowed_countries == []
        assert dr.enforcement == "strict"

    def test_to_dict(self):
        dr = DataResidencyRule(
            id="dr-2",
            name="APAC PDPA",
            region="ap-southeast-1",
            allowed_countries=["SG", "MY"],
            enforcement="log_only",
        )
        d = dr.to_dict()
        assert d["enforcement"] == "log_only"
        assert len(d["allowed_countries"]) == 2

    def test_from_dict(self):
        data = {
            "id": "dr-full",
            "name": "Full",
            "region": "us-east-1",
            "allowed_countries": ["US"],
            "tenant_ids": ["t1", "t2"],
            "data_categories": ["health"],
            "enforcement": "strict",
        }
        dr = DataResidencyRule.from_dict(data)
        assert dr.region == "us-east-1"
        assert len(dr.tenant_ids) == 2

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal", "region": "r1"}
        dr = DataResidencyRule.from_dict(data)
        assert dr.enforcement == "strict"
        assert dr.data_categories == []

    def test_roundtrip(self):
        dr = DataResidencyRule(
            id="rt",
            name="RT",
            region="r1",
            allowed_countries=["US", "CA"],
            enforcement="strict",
        )
        dr2 = DataResidencyRule.from_dict(dr.to_dict())
        assert dr2.allowed_countries == dr.allowed_countries
        assert dr2.enforcement == dr.enforcement


class TestRegionHealthCheck:
    """Tests cho RegionHealthCheck dataclass."""

    def test_creation(self):
        hc = RegionHealthCheck(
            id="hc-1",
            region="ap-southeast-1",
            endpoint_url="https://example.com/health",
            interval_seconds=10,
            timeout_seconds=3,
            unhealthy_threshold=2,
            healthy_threshold=2,
            check_type="http",
        )
        assert hc.interval_seconds == 10
        assert hc.check_type == "http"

    def test_creation_defaults(self):
        hc = RegionHealthCheck(
            id="test",
            region="r1",
            endpoint_url="https://test.com",
        )
        assert hc.interval_seconds == 30
        assert hc.timeout_seconds == 5
        assert hc.unhealthy_threshold == 3

    def test_to_dict(self):
        hc = RegionHealthCheck(
            id="hc-2",
            region="us-east-1",
            endpoint_url="https://test.com/health",
            interval_seconds=15,
            timeout_seconds=5,
            check_type="tcp",
        )
        d = hc.to_dict()
        assert d["check_type"] == "tcp"
        assert d["interval_seconds"] == 15

    def test_from_dict(self):
        data = {
            "id": "hc-full",
            "region": "eu-west-1",
            "endpoint_url": "https://eu.com/health",
            "interval_seconds": 5,
            "timeout_seconds": 2,
            "unhealthy_threshold": 1,
            "healthy_threshold": 3,
            "check_type": "custom",
        }
        hc = RegionHealthCheck.from_dict(data)
        assert hc.unhealthy_threshold == 1
        assert hc.healthy_threshold == 3

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "region": "r1", "endpoint_url": "https://m.com"}
        hc = RegionHealthCheck.from_dict(data)
        assert hc.interval_seconds == 30
        assert hc.check_type == "http"

    def test_roundtrip(self):
        hc = RegionHealthCheck(
            id="rt",
            region="r1",
            endpoint_url="https://rt.com",
            interval_seconds=10,
            unhealthy_threshold=2,
        )
        hc2 = RegionHealthCheck.from_dict(hc.to_dict())
        assert hc2.interval_seconds == hc.interval_seconds
        assert hc2.region == hc.region
