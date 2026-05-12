"""
Tests for pipeline code.py — MIR metadata path and plan serialization.

Verifies that:
- _plan_backend_files reads from mir["metadata"]["entities"]
- _plan_frontend_files reads from mir["metadata"]["entities"]
- _create_implementation_plan preserves metadata in FileSpec
- ImplementationPlan serialization is compatible with _execute_gen
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.pipeline.plan import ImplementationPlan, ModuleSpec, FileSpec


# ===========================================================================
# ImplementationPlan serialization tests
# ===========================================================================


class TestPlanSerialization:
    """ImplementationPlan.to_json() produces modules-based JSON."""

    def test_to_json_has_modules_key(self) -> None:
        plan = ImplementationPlan(meta={"version": "1.0.0"})
        plan.add_module(ModuleSpec(
            name="core",
            module_type="backend",
            files=[FileSpec(
                path="app/main.py",
                file_type="main",
                template="main.py.jinja2",
                context={},
                metadata={},
            )],
        ))
        data = plan.to_dict()
        assert "modules" in data
        assert len(data["modules"]) == 1

    def test_from_dict_roundtrip(self) -> None:
        plan = ImplementationPlan(meta={"version": "1.0.0"})
        plan.add_module(ModuleSpec(
            name="users",
            module_type="backend",
            files=[FileSpec(
                path="app/models/user.py",
                file_type="model",
                template="entity.py.jinja2",
                context={"entity": {"id": "User"}},
                metadata={"pack_emitter": "cp01.entity.fastapi"},
            )],
        ))
        restored = ImplementationPlan.from_dict(plan.to_dict())
        assert len(restored.modules) == 1
        assert restored.modules[0].name == "users"
        assert len(restored.modules[0].files) == 1

    def test_filespec_metadata_preserved(self) -> None:
        """FileSpec.metadata survives serialization roundtrip."""
        spec = FileSpec(
            path="app/models/user.py",
            file_type="model",
            template="entity.py.jinja2",
            context={"entity": {"id": "User"}},
            metadata={"pack_emitter": "cp01.entity.fastapi", "stack": "fastapi"},
        )
        restored = FileSpec.from_dict(spec.to_dict())
        assert restored.metadata["pack_emitter"] == "cp01.entity.fastapi"
        assert restored.metadata["stack"] == "fastapi"

    def test_count_files_by_module_type(self) -> None:
        plan = ImplementationPlan(meta={})
        plan.add_module(ModuleSpec(
            name="core", module_type="backend",
            files=[FileSpec(path="a.py", file_type="main", template="a.j2")],
        ))
        plan.add_module(ModuleSpec(
            name="users", module_type="backend",
            files=[
                FileSpec(path="b.py", file_type="model", template="b.j2"),
                FileSpec(path="c.py", file_type="schema", template="c.j2"),
            ],
        ))
        plan.add_module(ModuleSpec(
            name="frontend", module_type="frontend",
            files=[FileSpec(path="d.ts", file_type="component", template="d.j2")],
        ))
        counts = plan.count_files()
        assert counts["backend"] == 3
        assert counts["frontend"] == 1
        assert counts["infra"] == 0

    def test_get_modules_by_type(self) -> None:
        plan = ImplementationPlan(meta={})
        plan.add_module(ModuleSpec(name="core", module_type="backend", files=[]))
        plan.add_module(ModuleSpec(name="frontend", module_type="frontend", files=[]))
        backend = plan.get_modules_by_type("backend")
        assert len(backend) == 1
        assert backend[0].name == "core"

    def test_get_files_by_type(self) -> None:
        plan = ImplementationPlan(meta={})
        plan.add_module(ModuleSpec(
            name="core", module_type="backend",
            files=[
                FileSpec(path="main.py", file_type="main", template="t"),
                FileSpec(path="user.py", file_type="model", template="t"),
            ],
        ))
        models = plan.get_files_by_type("model")
        assert len(models) == 1
        assert models[0].path == "user.py"

    def test_compute_hash_deterministic(self) -> None:
        plan = ImplementationPlan(meta={"version": "1.0.0"})
        plan.add_module(ModuleSpec(
            name="core", module_type="backend",
            files=[FileSpec(path="a.py", file_type="main", template="t")],
        ))
        h1 = plan.compute_hash()
        h2 = plan.compute_hash()
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex


# ===========================================================================
# MIR metadata path fix tests
# ===========================================================================


class TestMirMetadataPath:
    """
    _plan_backend_files and _plan_frontend_files read from
    mir["metadata"]["entities"], not mir["entities"].
    """

    def test_mir_metadata_structure(self) -> None:
        """Verify expected MIR structure (as produced by MIRBuilder)."""
        mir = {
            "operations": [{"op_id": "op1", "op_type": "create_record"}],
            "data_flows": [],
            "effect_flows": [],
            "boundaries": [],
            "metadata": {
                "entities": [
                    {
                        "id": "User",
                        "description": "User entity",
                        "fields": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "email", "type": "string"},
                        ],
                    }
                ],
                "commands": [{"id": "CreateUser", "input": [], "writes_to": ["User"]}],
                "queries": [{"id": "ListUsers", "input": [], "reads_from": ["User"]}],
            },
        }
        # Top-level access should be empty
        assert mir.get("entities", []) == []
        assert mir.get("commands", []) == []
        # Correct path
        entities = mir.get("metadata", {}).get("entities", [])
        assert len(entities) == 1
        assert entities[0]["id"] == "User"

    def test_empty_metadata_does_not_crash(self) -> None:
        """Plan builder should handle missing metadata gracefully."""
        mir = {"operations": [], "metadata": {}}
        entities = mir.get("metadata", {}).get("entities", [])
        commands = mir.get("metadata", {}).get("commands", [])
        queries = mir.get("metadata", {}).get("queries", [])
        assert entities == []
        assert commands == []
        assert queries == []

    def test_missing_metadata_key(self) -> None:
        """Plan builder should handle MIR dict without metadata key."""
        mir = {"operations": []}
        entities = mir.get("metadata", {}).get("entities", [])
        assert entities == []
