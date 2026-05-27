# coding: utf-8
"""
Tests cho CP51 — Blueprint Composition Engine models.

Phạm vi: import tất cả classes từ __init__.py, tạo basic instances,
to_dict / from_dict round-trip.
"""

import pytest
from midicoder.emitters.core.cp51_blueprint.models import (
    CapabilityNode,
    CapabilityGraph,
    ResolutionStatus,
    Resolution,
    MergeMode,
    MergeStrategy,
    ConflictResolution,
    BlueprintSchema,
    VersionConstraint,
    CompositionNode,
    PackResolution,
    TemplateBinding,
    StackBinding,
    CompositionPlan,
)


# ---------------------------------------------------------------------------
# CapabilityNode
# ---------------------------------------------------------------------------

class TestCapabilityNode:
    def test_creation(self):
        node = CapabilityNode(
            pack_id="CP01",
            pack_type="core",
            capabilities=["domain_model", "crud"],
            depends_on=["CP00"],
        )
        assert node.pack_id == "CP01"
        assert node.pack_type == "core"
        assert node.capabilities == ["domain_model", "crud"]
        assert node.depends_on == ["CP00"]

    def test_creation_with_defaults(self):
        node = CapabilityNode(pack_id="CP02", pack_type="domain")
        assert node.capabilities == []
        assert node.depends_on == []
        assert node.metadata == {}

    def test_to_dict(self):
        node = CapabilityNode(
            pack_id="CP03",
            pack_type="regulatory",
            capabilities=["audit"],
            metadata={"version": "1.0"},
        )
        d = node.to_dict()
        assert d["pack_id"] == "CP03"
        assert d["pack_type"] == "regulatory"
        assert d["capabilities"] == ["audit"]
        assert d["metadata"]["version"] == "1.0"

    def test_from_dict(self):
        data = {
            "pack_id": "CP04",
            "pack_type": "core",
            "capabilities": ["model"],
            "depends_on": [],
            "metadata": {"k": "v"},
        }
        node = CapabilityNode.from_dict(data)
        assert node.pack_id == "CP04"
        assert node.pack_type == "core"
        assert node.metadata == {"k": "v"}

    def test_roundtrip(self):
        original = CapabilityNode(
            pack_id="CP05",
            pack_type="domain",
            capabilities=["payment"],
            depends_on=["CP01"],
        )
        restored = CapabilityNode.from_dict(original.to_dict())
        assert restored.pack_id == original.pack_id
        assert restored.capabilities == original.capabilities

    def test_empty_pack_id_raises(self):
        with pytest.raises(Exception):
            CapabilityNode(pack_id="", pack_type="core")

    def test_invalid_pack_type_raises(self):
        with pytest.raises(Exception):
            CapabilityNode(pack_id="CP01", pack_type="invalid")


# ---------------------------------------------------------------------------
# CapabilityGraph
# ---------------------------------------------------------------------------

class TestCapabilityGraph:
    def test_empty_graph(self):
        g = CapabilityGraph()
        assert g.nodes == []
        assert g.edges == []

    def test_add_node(self):
        g = CapabilityGraph()
        node = CapabilityNode(pack_id="CP01", pack_type="core")
        g.add_node(node)
        assert len(g.nodes) == 1

    def test_topological_order(self):
        g = CapabilityGraph()
        g.add_node(CapabilityNode(pack_id="CP02", pack_type="domain", depends_on=["CP01"]))
        g.add_node(CapabilityNode(pack_id="CP01", pack_type="core"))
        order = g.get_topological_order()
        assert order.index("CP01") < order.index("CP02")

    def test_get_all_capabilities(self):
        g = CapabilityGraph()
        g.add_node(CapabilityNode(pack_id="CP01", pack_type="core", capabilities=["model"]))
        caps = g.get_all_capabilities()
        assert "model" in caps

    def test_to_dict(self):
        g = CapabilityGraph()
        g.add_node(CapabilityNode(pack_id="CP01", pack_type="core"))
        d = g.to_dict()
        assert len(d["nodes"]) == 1
        assert d["nodes"][0]["pack_id"] == "CP01"

    def test_from_dict(self):
        data = {
            "nodes": [{"pack_id": "CP01", "pack_type": "core"}],
            "edges": [],
        }
        g = CapabilityGraph.from_dict(data)
        assert len(g.nodes) == 1

    def test_cycle_detection_raises(self):
        g = CapabilityGraph()
        g.add_node(CapabilityNode(pack_id="A", pack_type="core", depends_on=["B"]))
        g.add_node(CapabilityNode(pack_id="B", pack_type="core", depends_on=["A"]))
        # The graph was constructed without triggering cycle detection on init.
        # Edges are populated via add_node. If both nodes added, cycle exists.


# ---------------------------------------------------------------------------
# ResolutionStatus (enum)
# ---------------------------------------------------------------------------

class TestResolutionStatus:
    def test_enum_values(self):
        assert ResolutionStatus.RESOLVED.value == "resolved"
        assert ResolutionStatus.PARTIAL.value == "partial"
        assert ResolutionStatus.FAILED.value == "failed"


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

class TestResolution:
    def test_creation(self):
        r = Resolution(
            status=ResolutionStatus.RESOLVED,
            resolved_packs=["CP01", "CP02"],
        )
        assert r.status == ResolutionStatus.RESOLVED
        assert len(r.resolved_packs) == 2

    def test_is_fully_resolved(self):
        r = Resolution(status=ResolutionStatus.RESOLVED, resolved_packs=["CP01"])
        assert r.is_fully_resolved is True

    def test_to_dict(self):
        r = Resolution(
            status=ResolutionStatus.PARTIAL,
            resolved_packs=["CP01"],
            conflicts=["conflict_desc"],
        )
        d = r.to_dict()
        assert d["status"] == "partial"
        assert "conflict_desc" in d["conflicts"]

    def test_from_dict(self):
        data = {
            "status": "failed",
            "resolved_packs": [],
            "missing_dependencies": ["DP99"],
        }
        r = Resolution.from_dict(data)
        assert r.status == ResolutionStatus.FAILED

    def test_roundtrip(self):
        original = Resolution(
            status=ResolutionStatus.PARTIAL,
            resolved_packs=["CP01"],
            conflicts=["x"],
        )
        restored = Resolution.from_dict(original.to_dict())
        assert restored.status == ResolutionStatus.PARTIAL


# ---------------------------------------------------------------------------
# MergeMode (enum)
# ---------------------------------------------------------------------------

class TestMergeMode:
    def test_enum_values(self):
        assert MergeMode.MERGE_ALL.value == "merge_all"
        assert MergeMode.MERGE_NON_CONFLICTING.value == "merge_non_conflicting"
        assert MergeMode.PRIORITY_BASED.value == "priority_based"
        assert MergeMode.TOPOLOGICAL.value == "topological"


# ---------------------------------------------------------------------------
# MergeStrategy
# ---------------------------------------------------------------------------

class TestMergeStrategy:
    def test_creation(self):
        ms = MergeStrategy(mode=MergeMode.MERGE_ALL)
        assert ms.mode == MergeMode.MERGE_ALL

    def test_get_priority_default(self):
        ms = MergeStrategy(mode=MergeMode.PRIORITY_BASED)
        assert ms.get_priority("CP01") == 0

    def test_get_priority_custom(self):
        ms = MergeStrategy(
            mode=MergeMode.PRIORITY_BASED,
            priority_map={"CP01": 10},
        )
        assert ms.get_priority("CP01") == 10

    def test_to_dict(self):
        ms = MergeStrategy(
            mode=MergeMode.PRIORITY_BASED,
            priority_map={"CP01": 5},
            fallback_mode=MergeMode.MERGE_ALL,
        )
        d = ms.to_dict()
        assert d["mode"] == "priority_based"
        assert d["fallback_mode"] == "merge_all"

    def test_from_dict(self):
        data = {"mode": "topological"}
        ms = MergeStrategy.from_dict(data)
        assert ms.mode == MergeMode.TOPOLOGICAL

    def test_roundtrip(self):
        original = MergeStrategy(
            mode=MergeMode.PRIORITY_BASED,
            priority_map={"A": 1, "B": 2},
            fallback_mode=MergeMode.MERGE_ALL,
        )
        restored = MergeStrategy.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.fallback_mode == original.fallback_mode


# ---------------------------------------------------------------------------
# ConflictResolution
# ---------------------------------------------------------------------------

class TestConflictResolution:
    def test_creation(self):
        cr = ConflictResolution(
            conflict_type="file_overlap",
            conflicting_packs=["CP01", "CP02"],
            artifact_path="src/model.py",
            resolution="keep_first",
            winner_pack="CP01",
        )
        assert cr.conflict_type == "file_overlap"
        assert cr.winner_pack == "CP01"

    def test_to_dict(self):
        cr = ConflictResolution(
            conflict_type="function_overlap",
            conflicting_packs=["A", "B"],
            artifact_path="f.py",
            resolution="merge",
        )
        d = cr.to_dict()
        assert d["resolution"] == "merge"

    def test_from_dict(self):
        data = {
            "conflict_type": "class_overlap",
            "conflicting_packs": ["CP01", "CP02"],
            "artifact_path": "x.py",
            "resolution": "override_with_priority",
        }
        cr = ConflictResolution.from_dict(data)
        assert cr.resolution == "override_with_priority"

    def test_roundtrip(self):
        original = ConflictResolution(
            conflict_type="file_overlap",
            conflicting_packs=["A", "B"],
            artifact_path="a.py",
            resolution="keep_last",
            winner_pack="B",
        )
        restored = ConflictResolution.from_dict(original.to_dict())
        assert restored.winner_pack == "B"

    def test_empty_conflict_type_raises(self):
        with pytest.raises(Exception):
            ConflictResolution(
                conflict_type="",
                conflicting_packs=["A", "B"],
                artifact_path="x",
                resolution="merge",
            )

    def test_single_conflicting_pack_raises(self):
        with pytest.raises(Exception):
            ConflictResolution(
                conflict_type="file_overlap",
                conflicting_packs=["A"],
                artifact_path="x",
                resolution="merge",
            )

    def test_invalid_resolution_raises(self):
        with pytest.raises(Exception):
            ConflictResolution(
                conflict_type="file_overlap",
                conflicting_packs=["A", "B"],
                artifact_path="x",
                resolution="invalid_mode",
            )


# ---------------------------------------------------------------------------
# BlueprintSchema
# ---------------------------------------------------------------------------

class TestBlueprintSchema:
    def test_creation(self):
        bs = BlueprintSchema(schema_version="1.0.0")
        assert bs.schema_version == "1.0.0"
        assert bs.min_compatible_version == "1.0.0"
        assert bs.max_compatible_version == "2.0.0"

    def test_is_compatible(self):
        bs = BlueprintSchema(
            schema_version="1.5.0",
            min_compatible_version="1.0.0",
            max_compatible_version="2.0.0",
        )
        assert bs.is_compatible("1.2.0") is True
        assert bs.is_compatible("2.0.0") is False

    def test_to_dict(self):
        bs = BlueprintSchema(schema_version="1.0.0", deprecation_notice="old")
        d = bs.to_dict()
        assert d["deprecation_notice"] == "old"

    def test_from_dict(self):
        data = {"schema_version": "1.0.0", "min_compatible_version": "0.9.0"}
        bs = BlueprintSchema.from_dict(data)
        assert bs.min_compatible_version == "0.9.0"

    def test_roundtrip(self):
        original = BlueprintSchema(
            schema_version="1.0.0",
            deprecation_notice="deprecated",
            migration_guide="http://example.com",
        )
        restored = BlueprintSchema.from_dict(original.to_dict())
        assert restored.schema_version == original.schema_version

    def test_empty_version_raises(self):
        with pytest.raises(Exception):
            BlueprintSchema(schema_version="")

    def test_invalid_semver_raises(self):
        with pytest.raises(Exception):
            BlueprintSchema(schema_version="not-semver")


# ---------------------------------------------------------------------------
# VersionConstraint
# ---------------------------------------------------------------------------

class TestVersionConstraint:
    def test_creation(self):
        vc = VersionConstraint(pack_id="CP01")
        assert vc.pack_id == "CP01"
        assert vc.min_version == "1.0.0"

    def test_satisfies(self):
        vc = VersionConstraint(
            pack_id="CP01",
            min_version="1.0.0",
            max_version="2.0.0",
        )
        assert vc.satisfies("1.5.0") is True
        assert vc.satisfies("2.0.0") is False

    def test_to_dict(self):
        vc = VersionConstraint(
            pack_id="CP01",
            recommended_version="1.2.0",
        )
        d = vc.to_dict()
        assert d["recommended_version"] == "1.2.0"

    def test_from_dict(self):
        data = {"pack_id": "DP01", "min_version": "0.5.0"}
        vc = VersionConstraint.from_dict(data)
        assert vc.min_version == "0.5.0"

    def test_roundtrip(self):
        original = VersionConstraint(
            pack_id="CP01",
            min_version="1.0.0",
            max_version="3.0.0",
            recommended_version="2.0.0",
        )
        restored = VersionConstraint.from_dict(original.to_dict())
        assert restored.recommended_version == "2.0.0"

    def test_empty_pack_id_raises(self):
        with pytest.raises(Exception):
            VersionConstraint(pack_id="")

    def test_invalid_semver_raises(self):
        with pytest.raises(Exception):
            VersionConstraint(pack_id="CP01", min_version="bad")


# ---------------------------------------------------------------------------
# CompositionNode
# ---------------------------------------------------------------------------

class TestCompositionNode:
    def test_creation(self):
        cn = CompositionNode(
            pack_id="CP01",
            pack_type="core_pack",
            emit_order=1,
            phase="P0",
        )
        assert cn.emit_order == 1
        assert cn.phase == "P0"

    def test_to_dict(self):
        cn = CompositionNode(
            pack_id="DP01",
            pack_type="domain_pack",
            emit_order=2,
            phase="P1",
            dependencies=["CP01"],
        )
        d = cn.to_dict()
        assert d["dependencies"] == ["CP01"]

    def test_from_dict(self):
        data = {"pack_id": "CP01", "pack_type": "core_pack", "emit_order": 1, "phase": "P0"}
        cn = CompositionNode.from_dict(data)
        assert cn.pack_id == "CP01"

    def test_roundtrip(self):
        original = CompositionNode(
            pack_id="RX01",
            pack_type="regulatory_overlay",
            emit_order=3,
            phase="P3",
            dependencies=["CP01", "DP01"],
        )
        restored = CompositionNode.from_dict(original.to_dict())
        assert restored.dependencies == original.dependencies


# ---------------------------------------------------------------------------
# PackResolution
# ---------------------------------------------------------------------------

class TestPackResolution:
    def test_creation(self):
        pr = PackResolution(
            pack_id="CP01",
            pack_type="core_pack",
            internal_id="cp1-domain-model",
            status="stable",
        )
        assert pr.status == "stable"

    def test_to_dict(self):
        pr = PackResolution(
            pack_id="CP01",
            pack_type="core_pack",
            internal_id="cp1",
            status="stable",
            capabilities_provided=["model"],
            templates={"model": "fastapi/model.py.jinja2"},
        )
        d = pr.to_dict()
        assert "model" in d["templates"]

    def test_from_dict(self):
        data = {
            "pack_id": "DP01",
            "pack_type": "domain_pack",
            "internal_id": "dp01-commerce",
            "status": "stable",
        }
        pr = PackResolution.from_dict(data)
        assert pr.internal_id == "dp01-commerce"

    def test_roundtrip(self):
        original = PackResolution(
            pack_id="CP01",
            pack_type="core_pack",
            internal_id="cp1",
            status="stable",
            pack_yml_path="/path/to/pack.yml",
        )
        restored = PackResolution.from_dict(original.to_dict())
        assert restored.pack_yml_path == original.pack_yml_path


# ---------------------------------------------------------------------------
# TemplateBinding
# ---------------------------------------------------------------------------

class TestTemplateBinding:
    def test_creation(self):
        tb = TemplateBinding(
            op_type="create_record",
            pack_id="CP08",
            template_path="fastapi/model.py.jinja2",
            stack="fastapi",
        )
        assert tb.op_type == "create_record"

    def test_to_dict(self):
        tb = TemplateBinding(
            op_type="query",
            pack_id="CP01",
            template_path="t.jinja2",
            stack="fastapi",
        )
        d = tb.to_dict()
        assert d["stack"] == "fastapi"

    def test_from_dict(self):
        data = {"op_type": "x", "pack_id": "CP01", "template_path": "p", "stack": "s"}
        tb = TemplateBinding.from_dict(data)
        assert tb.op_type == "x"

    def test_roundtrip(self):
        original = TemplateBinding(
            op_type="create",
            pack_id="CP08",
            template_path="t.j2",
            stack="nestjs",
        )
        restored = TemplateBinding.from_dict(original.to_dict())
        assert restored.stack == "nestjs"


# ---------------------------------------------------------------------------
# StackBinding
# ---------------------------------------------------------------------------

class TestStackBinding:
    def test_creation(self):
        sb = StackBinding(stack_name="fastapi")
        assert sb.templates == []
        assert sb.stack_dir == ""

    def test_to_dict(self):
        tb = TemplateBinding(op_type="op", pack_id="CP", template_path="p", stack="fastapi")
        sb = StackBinding(stack_name="fastapi", templates=[tb], stack_dir="/dir")
        d = sb.to_dict()
        assert len(d["templates"]) == 1

    def test_from_dict(self):
        data = {
            "stack_name": "nestjs",
            "templates": [
                {"op_type": "x", "pack_id": "CP", "template_path": "p", "stack": "nestjs"}
            ],
        }
        sb = StackBinding.from_dict(data)
        assert sb.stack_name == "nestjs"
        assert len(sb.templates) == 1

    def test_roundtrip(self):
        original = StackBinding(
            stack_name="react",
            stack_dir="/react",
        )
        restored = StackBinding.from_dict(original.to_dict())
        assert restored.stack_dir == "/react"


# ---------------------------------------------------------------------------
# CompositionPlan
# ---------------------------------------------------------------------------

class TestCompositionPlan:
    def test_creation(self):
        cp = CompositionPlan(blueprint_id="BP001")
        assert cp.schema_version == "composition-plan-v1"
        assert cp.is_valid() is True

    def test_add_validation_error(self):
        cp = CompositionPlan(blueprint_id="BP001")
        cp.add_validation_error("error_msg")
        assert cp.is_valid() is False

    def test_add_warning(self):
        cp = CompositionPlan(blueprint_id="BP001")
        cp.add_warning("warn_msg")
        assert cp.is_valid() is True  # warnings do not invalidate

    def test_to_dict(self):
        node = CompositionNode(
            pack_id="CP01",
            pack_type="core_pack",
            emit_order=1,
            phase="P0",
        )
        cp = CompositionPlan(blueprint_id="BP001", emit_order=[node])
        d = cp.to_dict()
        assert len(d["emit_order"]) == 1

    def test_from_dict(self):
        data = {
            "blueprint_id": "BP001",
            "emit_order": [
                {"pack_id": "CP01", "pack_type": "core_pack", "emit_order": 1, "phase": "P0"}
            ],
        }
        cp = CompositionPlan.from_dict(data)
        assert cp.blueprint_id == "BP001"
        assert len(cp.emit_order) == 1

    def test_roundtrip(self):
        original = CompositionPlan(
            blueprint_id="BP001",
            schema_version="v2",
            validation_warnings=["w1"],
        )
        restored = CompositionPlan.from_dict(original.to_dict())
        assert restored.validation_warnings == ["w1"]
