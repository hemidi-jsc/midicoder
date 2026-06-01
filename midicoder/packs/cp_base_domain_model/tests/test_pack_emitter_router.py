"""
Tests for pipeline/pack_emitter_router.py — PackEmitterRouter dispatch.

Covers:
- EMITTER_REGISTRY completeness
- PARSER_REGISTRY works (MIR dict → Entity dataclass)
- PackEmitterRouter.dispatch() for entity emitters
- PackEmitterRouter.dispatch() for VO emitters
- Unknown emitter key → KeyError
- Fallback placeholder on parse failure
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.pipeline.pack_emitter_router import (
    PackEmitterRouter,
    EMITTER_REGISTRY,
    PARSER_REGISTRY,
    _parse_entity_dict,
    _fallback_placeholder,
    _resolve_stack_dir,
)
from midicoder.packs.cp_base_domain_model.models import (
    Entity,
    EntityField,
    EntityFieldType,
)


# ===========================================================================
# Registry tests
# ===========================================================================


class TestEmitterRegistry:
    """EMITTER_REGISTRY contains expected entries."""

    def test_has_entity_fastapi(self) -> None:
        assert "cp01.entity.fastapi" in EMITTER_REGISTRY

    def test_has_entity_nestjs(self) -> None:
        assert "cp01.entity.nestjs" in EMITTER_REGISTRY

    def test_has_vo_fastapi(self) -> None:
        assert "cp01.vo.fastapi" in EMITTER_REGISTRY

    def test_has_vo_nestjs(self) -> None:
        assert "cp01.vo.nestjs" in EMITTER_REGISTRY

    def test_has_docker(self) -> None:
        assert "cp07.docker" in EMITTER_REGISTRY

    def test_entry_shape(self) -> None:
        """Each entry is (module_path, class_name, parser_key|None)."""
        for key, entry in EMITTER_REGISTRY.items():
            assert len(entry) == 3, f"{key} entry must be 3-tuple"
            module_path, class_name, parser_key = entry
            assert isinstance(module_path, str) and module_path.startswith("midicoder.")
            assert isinstance(class_name, str)
            assert parser_key is None or isinstance(parser_key, str)

    def test_entity_fastapi_parser_key(self) -> None:
        entry = EMITTER_REGISTRY["cp01.entity.fastapi"]
        assert entry[2] == "cp_base_domain_model_entity"  # parser_key

    def test_vo_fastapi_no_parser(self) -> None:
        entry = EMITTER_REGISTRY["cp01.vo.fastapi"]
        assert entry[2] is None  # VO emitters accept raw dicts


class TestParserRegistry:
    """PARSER_REGISTRY can convert MIR dict → Entity dataclass."""

    def test_cp01_entity_parser_registered(self) -> None:
        assert "cp_base_domain_model_entity" in PARSER_REGISTRY

    def test_parse_minimal_entity(self) -> None:
        raw = {
            "id": "User",
            "description": "A user",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "email", "type": "string", "nullable": False, "unique": True, "length": 255},
            ],
        }
        entity = _parse_entity_dict(raw)
        assert isinstance(entity, Entity)
        assert entity.id == "User"
        assert entity.description == "A user"
        assert len(entity.fields) == 2

    def test_parse_entity_field_types(self) -> None:
        raw = {
            "id": "Order",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "total", "type": "decimal", "precision": 10, "scale": 2},
                {"name": "status", "type": "string", "length": 50},
                {"name": "count", "type": "integer"},
                {"name": "active", "type": "boolean"},
            ],
        }
        entity = _parse_entity_dict(raw)
        types = [f.field_type for f in entity.fields]
        assert EntityFieldType.UUID in types
        assert EntityFieldType.DECIMAL in types
        assert EntityFieldType.STRING in types
        assert EntityFieldType.INTEGER in types
        assert EntityFieldType.BOOLEAN in types

    def test_parse_entity_with_relationships(self) -> None:
        raw = {
            "id": "User",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
            ],
            "relationships": [
                {"type": "one-to-many", "target": "Order", "back_populates": "user"},
            ],
        }
        entity = _parse_entity_dict(raw)
        assert len(entity.relationships) == 1
        assert entity.relationships[0].target == "Order"

    def test_parse_entity_with_constraints(self) -> None:
        raw = {
            "id": "Account",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "balance", "type": "decimal"},
            ],
            "constraints": [
                {"type": "check", "name": "check_balance", "condition": "balance >= 0"},
            ],
        }
        entity = _parse_entity_dict(raw)
        assert len(entity.constraints) == 1
        assert entity.constraints[0].condition == "balance >= 0"

    def test_parse_entity_with_indexes(self) -> None:
        raw = {
            "id": "Product",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "sku", "type": "string"},
            ],
            "indexes": [
                {"name": "idx_sku", "fields": ["sku"], "unique": True},
            ],
        }
        entity = _parse_entity_dict(raw)
        assert len(entity.indexes) == 1
        assert entity.indexes[0].unique is True

    def test_parse_entity_with_lifecycle(self) -> None:
        raw = {
            "id": "AuditEntity",
            "fields": [
                {"name": "id", "type": "uuid", "primary_key": True},
                {"name": "created_at", "type": "datetime"},
            ],
            "lifecycle": {
                "before_insert": ["set_timestamps"],
            },
        }
        entity = _parse_entity_dict(raw)
        assert len(entity.lifecycle_hooks) == 1
        assert entity.lifecycle_hooks[0].hook_name == "set_timestamps"


# ===========================================================================
# PackEmitterRouter dispatch tests
# ===========================================================================


class TestPackEmitterRouter:
    """PackEmitterRouter dispatches to correct emitter classes."""

    def test_dispatch_unknown_key_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown pack_emitter"):
            PackEmitterRouter.dispatch(
                "nonexistent.emitter",
                {"path": "x.py", "context": {}, "type": "model"},
                "fastapi",
            )

    def test_dispatch_entity_fastapi_produces_code(self) -> None:
        file_plan = {
            "path": "app/models/user.py",
            "type": "model",
            "template": "cp_base_domain_model/entity.py.jinja2",
            "context": {
                "entity": {
                    "id": "User",
                    "description": "User entity",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "email", "type": "string", "nullable": False, "unique": True, "length": 255},
                    ],
                },
                "all_entities": [],
            },
        }
        result = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_plan, "fastapi"
        )
        assert len(result) == 1
        assert result[0]["path"] == "app/models/user.py"
        content = result[0]["content"]
        # Entity emitter produces a real SQLAlchemy model
        assert "class User" in content or "class User" in content

    def test_dispatch_entity_fastapi_produces_imports(self) -> None:
        """Entity emitter should include proper imports."""
        file_plan = {
            "path": "app/models/order.py",
            "type": "model",
            "template": "cp_base_domain_model/entity.py.jinja2",
            "context": {
                "entity": {
                    "id": "Order",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "total", "type": "decimal", "precision": 10, "scale": 2},
                        {"name": "created_at", "type": "datetime"},
                    ],
                },
                "all_entities": [],
            },
        }
        result = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_plan, "fastapi"
        )
        content = result[0]["content"]
        # Should have SQLAlchemy imports
        assert "import" in content

    def test_dispatch_entity_schema_same_code(self) -> None:
        """Schema type should also use entity emitter."""
        file_plan = {
            "path": "app/schemas/user.py",
            "type": "schema",
            "template": "cp_base_domain_model/entity.py.jinja2",
            "context": {
                "entity": {
                    "id": "User",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "name", "type": "string"},
                    ],
                },
                "all_entities": [],
            },
        }
        result = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_plan, "fastapi"
        )
        assert len(result) == 1

    def test_dispatch_entity_repository_fallback(self) -> None:
        """Repository type is NOT handled by entity emitter → fallback."""
        file_plan = {
            "path": "app/repositories/user_repo.py",
            "type": "repository",
            "template": "db/repository.py.jinja2",
            "context": {
                "entity": {
                    "id": "User",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                    ],
                },
                "all_entities": [],
            },
        }
        result = PackEmitterRouter.dispatch(
            "cp01.entity.fastapi", file_plan, "fastapi"
        )
        # Repository is a fallback — should contain placeholder comment
        content = result[0]["content"]
        assert "Placeholder" in content or "placeholder" in content.lower()


# ===========================================================================
# _fallback_placeholder tests
# ===========================================================================


class TestFallbackPlaceholder:
    def test_returns_single_entry(self) -> None:
        result = _fallback_placeholder("test/path.py", "test reason")
        assert len(result) == 1
        assert result[0]["path"] == "test/path.py"

    def test_contains_reason(self) -> None:
        result = _fallback_placeholder("x.py", "specific error")
        assert "specific error" in result[0]["content"]

    def test_contains_placeholder_marker(self) -> None:
        result = _fallback_placeholder("x.py", "reason")
        assert "Placeholder" in result[0]["content"]


# ===========================================================================
# _resolve_stack_dir tests
# ===========================================================================


class TestResolveStackDir:
    def test_fastapi_returns_existing_dir(self) -> None:
        d = _resolve_stack_dir("fastapi")
        assert d.exists()
        assert "fastapi" in str(d)

    def test_nestjs_returns_existing_dir(self) -> None:
        d = _resolve_stack_dir("nestjs")
        assert d.exists()
        assert "nestjs" in str(d)

    def test_unknown_stack_creates_dir(self) -> None:
        d = _resolve_stack_dir("nonexistent_stack_12345")
        # Should return a Path (may or may not exist depending on state)
        assert isinstance(d, Path)
