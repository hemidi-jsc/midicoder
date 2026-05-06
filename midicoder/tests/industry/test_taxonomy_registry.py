"""
Tests for TaxonomyRegistry.

Kiểm tra:
- Load taxonomy từ file
- Query packs theo filters
- Dependency resolution (BFS)
- Cycle detection
- Status transition validation
- Blueprint validation
- Adding pack không break existing blueprints
"""

import pytest
from pathlib import Path
import sys

# Add industry/ to path so we can import registry
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "industry"))

from registry import TaxonomyRegistry, Pack, ValidationIssue


TAXONOMY_PATH = Path(__file__).parent.parent.parent.parent / "industry" / "taxonomy.yml"


class TestTaxonomyRegistryLoad:
    """Test taxonomy loading."""

    def test_load_taxonomy(self):
        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        assert registry is not None
        assert len(registry) > 100  # 53 CPs + 36 DPs + 12 RXs = 101

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            TaxonomyRegistry.load("nonexistent.yml")

    def test_pack_count(self):
        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        cps = registry.find_packs(pack_type="core_pack")
        dps = registry.find_packs(pack_type="domain_pack")
        rxs = registry.find_packs(pack_type="regulatory_overlay")
        assert len(cps) == 53
        assert len(dps) == 36
        assert len(rxs) == 12

    def test_all_pack_ids_unique(self):
        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        all_packs = registry.get_all_packs()
        ids = [p.id for p in all_packs]
        assert len(ids) == len(set(ids))  # No duplicates


class TestTaxonomyRegistryQuery:
    """Test query API."""

    def setup_method(self):
        self.registry = TaxonomyRegistry.load(TAXONOMY_PATH)

    def test_find_stable_core_packs(self):
        stable = self.registry.find_packs(pack_type="core_pack", status="stable")
        assert len(stable) == 5  # CP01, CP03, CP04, CP05, CP12

    def test_find_p0_core_packs(self):
        p0 = self.registry.find_packs(pack_type="core_pack", phase="P0")
        assert len(p0) == 8  # CP01, CP02, CP03, CP04, CP07, CP51, CP52, CP53

    def test_find_planned_domain_packs(self):
        planned = self.registry.find_packs(pack_type="domain_pack", status="planned")
        assert len(planned) == 32

    def test_find_developing_domain_packs(self):
        developing = self.registry.find_packs(pack_type="domain_pack", status="developing")
        assert len(developing) == 4  # DP05, DP11, DP12, DP14

    def test_find_planned_regulatory_overlays(self):
        planned = self.registry.find_packs(pack_type="regulatory_overlay", status="planned")
        assert len(planned) == 12

    def test_no_stable_regulatory_overlays(self):
        stable = self.registry.find_packs(pack_type="regulatory_overlay", status="stable")
        assert len(stable) == 0

    def test_no_stable_domain_packs(self):
        stable = self.registry.find_packs(pack_type="domain_pack", status="stable")
        assert len(stable) == 0

    def test_get_existing_pack(self):
        pack = self.registry.get_pack("CP01")
        assert pack is not None
        assert pack.id == "CP01"
        assert pack.status == "stable"
        assert pack.phase == "P0"

    def test_get_nonexistent_pack(self):
        pack = self.registry.get_pack("CP999")
        assert pack is None

    def test_contains_operator(self):
        assert "CP01" in self.registry
        assert "DP01" in self.registry
        assert "RX01" in self.registry
        assert "CP999" not in self.registry

    def test_find_by_category(self):
        security = self.registry.find_packs(pack_type="core_pack", category="security")
        assert len(security) >= 2  # CP03, CP04 at minimum


class TestTaxonomyRegistryDependencies:
    """Test dependency resolution."""

    def setup_method(self):
        self.registry = TaxonomyRegistry.load(TAXONOMY_PATH)

    def test_find_dependents_cp01(self):
        """CP01 is depended on by ALL DPs and all RXs."""
        dependents = self.registry.find_dependents("CP01")
        assert len(dependents) >= 36  # All 36 DPs + 12 RXs

    def test_find_dependents_cp03(self):
        """CP03 is depended on by most DPs."""
        dependents = self.registry.find_dependents("CP03")
        assert len(dependents) >= 30

    def test_find_dependents_nonexistent(self):
        with pytest.raises(KeyError):
            self.registry.find_dependents("CP999")

    def test_resolve_dependencies_cp04(self):
        """CP04 depends on CP02, CP03 which depends on CP01, CP02."""
        deps = self.registry.resolve_dependencies("CP04")
        assert "CP02" in deps
        assert "CP03" in deps
        assert "CP01" in deps

    def test_resolve_dependencies_cp01(self):
        """CP01 has no dependencies."""
        deps = self.registry.resolve_dependencies("CP01")
        assert len(deps) == 0

    def test_no_cycles_in_taxonomy(self):
        """Current taxonomy must have no dependency cycles."""
        cycles = self.registry.detect_cycles()
        assert len(cycles) == 0


class TestTaxonomyRegistryStatus:
    """Test status transition validation."""

    def setup_method(self):
        self.registry = TaxonomyRegistry.load(TAXONOMY_PATH)

    def test_valid_transition_planned_to_developing(self):
        assert self.registry.is_valid_transition("planned", "developing")

    def test_valid_transition_developing_to_stable(self):
        assert self.registry.is_valid_transition("developing", "stable")

    def test_valid_transition_stable_to_deprecated(self):
        assert self.registry.is_valid_transition("stable", "deprecated")

    def test_invalid_transition_planned_to_stable(self):
        assert not self.registry.is_valid_transition("planned", "stable")

    def test_invalid_transition_deprecated_to_anything(self):
        assert not self.registry.is_valid_transition("deprecated", "stable")

    def test_validate_pack_status_valid(self):
        issues = self.registry.validate_pack_status("CP02", "stable")
        # CP02 is "developing", transitioning to "stable" is valid
        # But CP02 depends on CP01 which is "stable" - so no planned dependency issue
        assert len(issues) == 0

    def test_validate_pack_status_invalid_transition(self):
        issues = self.registry.validate_pack_status("CP01", "deprecated")
        # CP01 is "stable", can go to "deprecated" - valid
        assert len(issues) == 0

    def test_validate_nonexistent_pack(self):
        issues = self.registry.validate_pack_status("CP999", "stable")
        assert len(issues) == 1
        assert issues[0].rule == "pack_exists"


class TestTaxonomyRegistryBlueprint:
    """Test blueprint validation."""

    def setup_method(self):
        self.registry = TaxonomyRegistry.load(TAXONOMY_PATH)

    def test_minimal_valid_blueprint(self):
        """Minimal blueprint with all P0 CPs and universal RXs."""
        p0_packs = self.registry.find_packs(pack_type="core_pack", phase="P0")
        blueprint = {
            "core_packs": [{"id": p.id} for p in p0_packs],
            "domain_packs": [{"id": "DP01"}],
            "regulatory_overlays": [{"id": "RX01"}, {"id": "RX11"}],
        }
        issues = self.registry.validate_pack_combination(blueprint)
        # Should not have missing P0 or missing universal RX errors
        error_rules = [i.rule for i in issues if i.severity == "error"]
        assert "blueprint_must_include_p0_core_packs" not in error_rules
        assert "universal_regulatory_overlays_included" not in error_rules

    def test_missing_p0_packs(self):
        blueprint = {
            "core_packs": [{"id": "CP01"}],  # Missing other P0 packs
            "domain_packs": [{"id": "DP01"}],
            "regulatory_overlays": [{"id": "RX01"}, {"id": "RX11"}],
        }
        issues = self.registry.validate_pack_combination(blueprint)
        error_rules = [i.rule for i in issues if i.severity == "error"]
        assert "blueprint_must_include_p0_core_packs" in error_rules

    def test_missing_universal_rx(self):
        p0_packs = self.registry.find_packs(pack_type="core_pack", phase="P0")
        blueprint = {
            "core_packs": [{"id": p.id} for p in p0_packs],
            "domain_packs": [{"id": "DP01"}],
            "regulatory_overlays": [{"id": "RX01"}],  # Missing RX11
        }
        issues = self.registry.validate_pack_combination(blueprint)
        error_rules = [i.rule for i in issues if i.severity == "error"]
        assert "universal_regulatory_overlays_included" in error_rules

    def test_nonexistent_pack_in_blueprint(self):
        p0_packs = self.registry.find_packs(pack_type="core_pack", phase="P0")
        blueprint = {
            "core_packs": [{"id": p.id} for p in p0_packs],
            "domain_packs": [{"id": "DP999"}],  # Does not exist
            "regulatory_overlays": [{"id": "RX01"}, {"id": "RX11"}],
        }
        issues = self.registry.validate_pack_combination(blueprint)
        error_rules = [i.rule for i in issues if i.severity == "error"]
        assert "all_referenced_packs_exist" in error_rules


class TestTaxonomyRegistryBackwardCompat:
    """Test backward compatibility — adding new packs doesn't break existing queries."""

    def setup_method(self):
        # Load raw data and simulate adding a new pack
        import yaml
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            self.raw_data = yaml.safe_load(f)

    def test_adding_pack_does_not_break_existing_queries(self):
        """Adding a new pack should not affect queries for existing packs."""
        original_registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        original_cp01 = original_registry.get_pack("CP01")
        original_stable = len(original_registry.find_packs(status="stable"))

        # Simulate adding a new pack
        self.raw_data["core_packs"].append({
            "id": "CP999",
            "name": "Test Pack",
            "internal_id": "cp999-test",
            "phase": "P4",
            "description": "Test pack",
            "definitions_count": 1,
            "obligations_count": 0,
            "depends_on": [],
            "category": "test",
            "status": "experimental",
        })
        modified_registry = TaxonomyRegistry(self.raw_data)

        # Existing pack still works
        modified_cp01 = modified_registry.get_pack("CP01")
        assert modified_cp01.id == original_cp01.id
        assert modified_cp01.status == original_cp01.status

        # Stable count unchanged (new pack is experimental)
        modified_stable = len(modified_registry.find_packs(status="stable"))
        assert modified_stable == original_stable

        # Total count increased
        assert len(modified_registry) == len(original_registry) + 1

    def test_adding_pack_does_not_break_dependency_resolution(self):
        """Adding a new pack should not break dependency resolution for existing packs."""
        original_registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        original_deps = original_registry.resolve_dependencies("CP04")

        # Add a pack that doesn't affect CP04
        self.raw_data["core_packs"].append({
            "id": "CP998",
            "name": "Another Test Pack",
            "internal_id": "cp998-test",
            "phase": "P4",
            "description": "Another test",
            "definitions_count": 1,
            "obligations_count": 0,
            "depends_on": [],
            "category": "test",
            "status": "planned",
        })
        modified_registry = TaxonomyRegistry(self.raw_data)
        modified_deps = modified_registry.resolve_dependencies("CP04")

        assert modified_deps == original_deps


class TestTaxonomyRegistryStatistics:
    """Test statistics and metadata."""

    def setup_method(self):
        self.registry = TaxonomyRegistry.load(TAXONOMY_PATH)

    def test_statistics_not_empty(self):
        stats = self.registry.get_statistics()
        assert "core_packs" in stats
        assert "domain_packs" in stats
        assert "regulatory_overlays" in stats

    def test_statistics_core_pack_count(self):
        stats = self.registry.get_statistics()
        assert stats["core_packs"]["total"] == 53

    def test_statistics_domain_pack_count(self):
        stats = self.registry.get_statistics()
        assert stats["domain_packs"]["total"] == 36

    def test_statistics_rx_count(self):
        stats = self.registry.get_statistics()
        assert stats["regulatory_overlays"]["total"] == 12

    def test_repr(self):
        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        repr_str = repr(registry)
        assert "TaxonomyRegistry" in repr_str
        assert "packs=" in repr_str

    def test_to_json(self):
        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        json_str = registry.to_json()
        assert "core_packs" in json_str
        assert "CP01" in json_str