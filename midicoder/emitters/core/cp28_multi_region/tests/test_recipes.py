# coding: utf-8
"""
Tests cho CP28 — Multi-Region recipes.

Kiểm tra:
- RecipeOutput dataclass
- basic_multi_region_recipe
- full_geo_replication_recipe
- data_residency_recipe

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp28_multi_region.recipes import (
    RecipeOutput,
    basic_multi_region_recipe,
    data_residency_recipe,
    full_geo_replication_recipe,
)


class TestRecipeOutput:
    """Tests cho RecipeOutput dataclass."""

    def test_creation(self):
        from midicoder.emitters.core.cp28_multi_region.parser import MultiRegionIR
        ro = RecipeOutput(
            name="test_recipe",
            description="Test recipe",
            ir=MultiRegionIR(),
            raw_data={},
        )
        assert ro.name == "test_recipe"
        assert ro.description == "Test recipe"

    def test_to_dict(self):
        from midicoder.emitters.core.cp28_multi_region.parser import MultiRegionIR
        ro = RecipeOutput(
            name="test",
            description="Test",
            ir=MultiRegionIR(),
            raw_data={"key": "value"},
        )
        d = ro.to_dict()
        assert d["name"] == "test"
        assert d["raw_data"]["key"] == "value"
        assert "ir" in d


class TestBasicMultiRegionRecipe:
    """Tests cho basic_multi_region_recipe."""

    def test_returns_recipe_output(self):
        ro = basic_multi_region_recipe("test-app")
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "basic_multi_region_recipe"

    def test_has_two_regions(self):
        ro = basic_multi_region_recipe("test-app")
        assert len(ro.ir.regions) == 2

    def test_has_primary_region(self):
        ro = basic_multi_region_recipe("test-app")
        primaries = [r for r in ro.ir.regions if r.primary]
        assert len(primaries) == 1
        assert primaries[0].id == "ap-southeast-1"

    def test_has_replication_policy(self):
        ro = basic_multi_region_recipe("test-app")
        assert len(ro.ir.replication_policies) == 1
        assert ro.ir.replication_policies[0].mode == "async"

    def test_has_health_checks(self):
        ro = basic_multi_region_recipe("test-app")
        assert len(ro.ir.health_checks) == 2

    def test_has_raw_data(self):
        ro = basic_multi_region_recipe("test-app")
        assert "regions" in ro.raw_data
        assert "replication_policies" in ro.raw_data

    def test_app_name_in_endpoints(self):
        ro = basic_multi_region_recipe("myapp")
        for region in ro.ir.regions:
            assert "myapp" in region.endpoint_url

    def test_to_dict_roundtrip(self):
        ro = basic_multi_region_recipe("test-app")
        d = ro.to_dict()
        assert d["name"] == "basic_multi_region_recipe"
        assert len(d["ir"]["regions"]) == 2


class TestFullGeoReplicationRecipe:
    """Tests cho full_geo_replication_recipe."""

    def test_returns_recipe_output(self):
        ro = full_geo_replication_recipe("test-app")
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "full_geo_replication_recipe"

    def test_has_three_regions(self):
        ro = full_geo_replication_recipe("test-app")
        assert len(ro.ir.regions) == 3

    def test_has_sync_replication(self):
        ro = full_geo_replication_recipe("test-app")
        assert len(ro.ir.replication_policies) == 1
        assert ro.ir.replication_policies[0].mode == "sync"

    def test_has_geo_routing_rules(self):
        ro = full_geo_replication_recipe("test-app")
        assert len(ro.ir.geo_routing_rules) == 1
        assert ro.ir.geo_routing_rules[0].strategy == "latency"

    def test_has_failover_policy(self):
        ro = full_geo_replication_recipe("test-app")
        assert len(ro.ir.failover_policies) == 1
        assert ro.ir.failover_policies[0].trigger == "auto"
        assert ro.ir.failover_policies[0].auto_failover_enabled is True

    def test_has_three_health_checks(self):
        ro = full_geo_replication_recipe("test-app")
        assert len(ro.ir.health_checks) == 3

    def test_rto_rpo(self):
        ro = full_geo_replication_recipe("test-app")
        fo = ro.ir.failover_policies[0]
        assert fo.rto_minutes == 5
        assert fo.rpo_minutes == 1


class TestDataResidencyRecipe:
    """Tests cho data_residency_recipe."""

    def test_returns_recipe_output(self):
        ro = data_residency_recipe("test-app")
        assert isinstance(ro, RecipeOutput)
        assert ro.name == "data_residency_recipe"

    def test_has_two_regions(self):
        ro = data_residency_recipe("test-app")
        assert len(ro.ir.regions) == 2

    def test_has_data_residency_rules(self):
        ro = data_residency_recipe("test-app")
        assert len(ro.ir.data_residency_rules) == 2

    def test_strict_enforcement(self):
        ro = data_residency_recipe("test-app")
        for rule in ro.ir.data_residency_rules:
            assert rule.enforcement == "strict"

    def test_has_health_checks(self):
        ro = basic_multi_region_recipe("test-app")
        assert len(ro.ir.health_checks) == 2

    def test_allowed_countries(self):
        ro = data_residency_recipe("test-app")
        eu_rule = [r for r in ro.ir.data_residency_rules if "eu" in r.id.lower()][0]
        assert "DE" in eu_rule.allowed_countries or "FR" in eu_rule.allowed_countries

    def test_has_replication(self):
        ro = data_residency_recipe("test-app")
        assert len(ro.ir.replication_policies) == 1
