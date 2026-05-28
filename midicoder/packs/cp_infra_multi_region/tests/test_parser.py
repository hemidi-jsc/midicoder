# coding: utf-8
"""
Tests cho I05 — Multi-Region parser.

Kiểm tra:
- MultiRegionIR: to_dict, from_dict
- parse_regions, parse_replication_policies
- parse_geo_routing_rules, parse_failover_policies
- parse_data_residency_rules, parse_health_checks
- parse_to_ir end-to-end

Author: Midicoder Team
Version: 2.0.0
"""

import pytest

from midicoder.packs.cp_infra_multi_region.parser import (
    MultiRegionIR,
    parse_data_residency_rules,
    parse_failover_policies,
    parse_geo_routing_rules,
    parse_health_checks,
    parse_regions,
    parse_replication_policies,
    parse_to_ir,
)


class TestMultiRegionIR:
    """Tests cho MultiRegionIR."""

    def test_empty_ir(self):
        ir = MultiRegionIR()
        assert ir.regions == []
        assert ir.replication_policies == []
        assert ir.health_checks == []

    def test_to_dict_empty(self):
        ir = MultiRegionIR()
        d = ir.to_dict()
        assert d["regions"] == []
        assert d["replication_policies"] == []
        assert isinstance(d, dict)

    def test_from_dict_empty(self):
        ir = MultiRegionIR.from_dict({})
        assert ir.regions == []
        assert ir.replication_policies == []

    def test_from_dict_full(self):
        data = {
            "regions": [
                {"id": "r1", "name": "Region 1", "cloud_provider": "aws", "primary": True},
                {"id": "r2", "name": "Region 2", "cloud_provider": "gcp"},
            ],
            "replication_policies": [
                {"id": "rp1", "name": "Replication", "mode": "sync", "source_region": "r1", "target_regions": ["r2"]},
            ],
            "geo_routing_rules": [
                {"id": "gr1", "name": "Geo Route", "strategy": "latency", "regions": [{"region": "r1"}]},
            ],
            "failover_policies": [
                {"id": "fo1", "name": "Failover", "trigger": "auto", "regions": ["r1", "r2"]},
            ],
            "data_residency_rules": [
                {"id": "dr1", "name": "GDPR", "region": "r1", "allowed_countries": ["DE"]},
            ],
            "health_checks": [
                {"id": "hc1", "region": "r1", "endpoint_url": "https://r1.com/health"},
            ],
        }
        ir = MultiRegionIR.from_dict(data)
        assert len(ir.regions) == 2
        assert len(ir.replication_policies) == 1
        assert len(ir.geo_routing_rules) == 1
        assert len(ir.failover_policies) == 1
        assert len(ir.data_residency_rules) == 1
        assert len(ir.health_checks) == 1

    def test_roundtrip(self):
        data = {
            "regions": [{"id": "r1", "name": "R1"}],
            "replication_policies": [{"id": "rp1", "name": "RP1", "mode": "async"}],
            "geo_routing_rules": [{"id": "gr1", "name": "GR1"}],
            "failover_policies": [{"id": "fo1", "name": "FO1"}],
            "data_residency_rules": [{"id": "dr1", "name": "DR1", "region": "r1"}],
            "health_checks": [{"id": "hc1", "region": "r1", "endpoint_url": "https://test.com"}],
        }
        ir = MultiRegionIR.from_dict(data)
        d = ir.to_dict()
        assert len(d["regions"]) == 1
        assert len(d["health_checks"]) == 1


class TestParseRegions:
    """Tests cho parse_regions."""

    def test_parse_regions(self):
        data = {
            "regions": [
                {"id": "r1", "name": "R1", "primary": True},
                {"id": "r2", "name": "R2"},
            ]
        }
        regions = parse_regions(data)
        assert len(regions) == 2
        assert regions[0].primary is True

    def test_parse_regions_empty(self):
        data = {}
        regions = parse_regions(data)
        assert regions == []


class TestParseReplicationPolicies:
    """Tests cho parse_replication_policies."""

    def test_parse_replication_policies(self):
        data = {
            "replication_policies": [
                {"id": "rp1", "name": "RP1", "mode": "sync"},
            ]
        }
        policies = parse_replication_policies(data)
        assert len(policies) == 1
        assert policies[0].mode == "sync"

    def test_parse_replication_policies_empty(self):
        data = {}
        policies = parse_replication_policies(data)
        assert policies == []


class TestParseGeoRoutingRules:
    """Tests cho parse_geo_routing_rules."""

    def test_parse_geo_routing_rules(self):
        data = {
            "geo_routing_rules": [
                {"id": "gr1", "name": "GR1", "strategy": "latency"},
            ]
        }
        rules = parse_geo_routing_rules(data)
        assert len(rules) == 1
        assert rules[0].strategy == "latency"

    def test_parse_geo_routing_rules_empty(self):
        rules = parse_geo_routing_rules({})
        assert rules == []


class TestParseFailoverPolicies:
    """Tests cho parse_failover_policies."""

    def test_parse_failover_policies(self):
        data = {
            "failover_policies": [
                {"id": "fo1", "name": "FO1", "trigger": "auto"},
            ]
        }
        policies = parse_failover_policies(data)
        assert len(policies) == 1
        assert policies[0].trigger == "auto"

    def test_parse_failover_policies_empty(self):
        policies = parse_failover_policies({})
        assert policies == []


class TestDataResidencyRules:
    """Tests cho parse_data_residency_rules."""

    def test_parse_data_residency_rules(self):
        data = {
            "data_residency_rules": [
                {"id": "dr1", "name": "DR1", "region": "r1", "allowed_countries": ["US"]},
            ]
        }
        rules = parse_data_residency_rules(data)
        assert len(rules) == 1
        assert len(rules[0].allowed_countries) == 1

    def test_parse_data_residency_rules_empty(self):
        rules = parse_data_residency_rules({})
        assert rules == []


class TestParseHealthChecks:
    """Tests cho parse_health_checks."""

    def test_parse_health_checks(self):
        data = {
            "health_checks": [
                {"id": "hc1", "region": "r1", "endpoint_url": "https://test.com", "interval_seconds": 10},
            ]
        }
        checks = parse_health_checks(data)
        assert len(checks) == 1
        assert checks[0].interval_seconds == 10

    def test_parse_health_checks_empty(self):
        checks = parse_health_checks({})
        assert checks == []


class TestParseToIR:
    """Tests cho parse_to_ir end-to-end."""

    def test_parse_to_ir_full(self):
        data = {
            "regions": [
                {"id": "r1", "name": "R1", "primary": True},
            ],
            "replication_policies": [
                {"id": "rp1", "name": "RP1", "mode": "async", "source_region": "r1", "target_regions": ["r2"]},
            ],
            "geo_routing_rules": [
                {"id": "gr1", "name": "GR1", "strategy": "latency", "regions": [{"region": "r1"}]},
            ],
            "failover_policies": [
                {"id": "fo1", "name": "FO1", "trigger": "auto"},
            ],
            "data_residency_rules": [
                {"id": "dr1", "name": "DR1", "region": "r1", "allowed_countries": ["DE"]},
            ],
            "health_checks": [
                {"id": "hc1", "region": "r1", "endpoint_url": "https://r1.com/health"},
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.regions) == 1
        assert len(ir.replication_policies) == 1
        assert len(ir.geo_routing_rules) == 1
        assert len(ir.failover_policies) == 1
        assert len(ir.data_residency_rules) == 1
        assert len(ir.health_checks) == 1

    def test_parse_to_ir_empty(self):
        ir = parse_to_ir({})
        assert ir.regions == []
        assert ir.replication_policies == []
        assert ir.health_checks == []

    def test_parse_to_ir_partial(self):
        data = {
            "regions": [{"id": "r1", "name": "R1"}],
            "health_checks": [{"id": "hc1", "region": "r1", "endpoint_url": "https://r1.com"}],
        }
        ir = parse_to_ir(data)
        assert len(ir.regions) == 1
        assert len(ir.replication_policies) == 0
        assert len(ir.health_checks) == 1
