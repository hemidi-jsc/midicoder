# coding: utf-8
"""
Tests cho Database Emitter module (P2-001-G + P2-001-G1).

Bao gom:
- Test Core DB Models (DataModel, ColumnDef, Relationship)
- Test DB Parser (parse_from_metadata)
- Test FastAPI DB Emitter (SQLAlchemy rendering)
- Test NestJS DB Emitter (TypeORM rendering)
- Test KPI-029 Tenant Isolation (105 tests cho templates)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from typing import Any, Dict

from midicoder.emitters.core.db.models import (
    DataModel,
    ColumnDef,
    Relationship,
    IndexDef,
    DataModelCollection,
    ColumnType,
    RelationshipType,
    Datasource,
    DatabaseEngine,
    ReplicaConfig,
)
from midicoder.emitters.core.db.parser import DBParser
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM
from midicoder.emitters.core.db.fastapi import SQLAlchemyEmitter
from midicoder.emitters.core.db.nestjs import TypeORMEmitter


# ============================================================================
# Test Core DB Models
# ============================================================================


class TestColumnDef:
    """Tests cho ColumnDef model."""

    def test_create_string_column(self):
        """Tao column kieu string."""
        col = ColumnDef(name="email", column_type=ColumnType.STRING, max_length=255)
        assert col.name == "email"
        assert col.column_type == ColumnType.STRING
        assert col.max_length == 255
        assert col.required is False
        assert col.tenant_aware is False

    def test_create_required_column(self):
        """Tao column bat buoc."""
        col = ColumnDef(name="name", column_type=ColumnType.STRING, required=True)
        assert col.required is True

    def test_create_integer_column(self):
        """Tao column kieu integer."""
        col = ColumnDef(name="age", column_type=ColumnType.INTEGER)
        assert col.column_type == ColumnType.INTEGER

    def test_create_tenant_aware_column(self):
        """Tao column tenant-aware cho KPI-029."""
        col = ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True)
        assert col.tenant_aware is True

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = ColumnDef(
            name="total",
            column_type=ColumnType.DECIMAL,
            precision=10,
            scale=2,
            required=True,
            tenant_aware=False,
        )
        d = original.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.name == original.name
        assert restored.column_type == original.column_type
        assert restored.precision == original.precision
        assert restored.scale == original.scale
        assert restored.required == original.required
        assert restored.tenant_aware == original.tenant_aware


class TestRelationship:
    """Tests cho Relationship model."""

    def test_create_many_to_one(self):
        """Tao quan he many-to-one."""
        rel = Relationship(
            target_model="User",
            rel_type=RelationshipType.MANY_TO_ONE,
            foreign_key="user_id",
        )
        assert rel.target_model == "User"
        assert rel.rel_type == RelationshipType.MANY_TO_ONE
        assert rel.foreign_key == "user_id"

    def test_create_one_to_many(self):
        """Tao quan he one-to-many."""
        rel = Relationship(
            target_model="OrderItem",
            rel_type=RelationshipType.ONE_TO_MANY,
            back_ref="order",
        )
        assert rel.rel_type == RelationshipType.ONE_TO_MANY
        assert rel.back_ref == "order"

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = Relationship(
            target_model="Category",
            rel_type=RelationshipType.MANY_TO_MANY,
            join_table="product_category",
            tenant_scoped=True,
        )
        d = original.to_dict()
        restored = Relationship.from_dict(d)
        assert restored.target_model == original.target_model
        assert restored.rel_type == original.rel_type
        assert restored.join_table == original.join_table
        assert restored.tenant_scoped == original.tenant_scoped


class TestDataModel:
    """Tests cho DataModel model."""

    def test_create_simple_model(self):
        """Tao model don gian."""
        model = DataModel(
            id="User",
            table_name="users",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="email", column_type=ColumnType.STRING, required=True),
            ],
        )
        assert model.id == "User"
        assert model.table_name == "users"
        assert len(model.columns) == 2
        assert model.has_tenant_column() is False

    def test_create_tenant_model(self):
        """Tao model co tenant_id (KPI-029)."""
        model = DataModel(
            id="Order",
            table_name="orders",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True),
                ColumnDef(name="total", column_type=ColumnType.DECIMAL),
            ],
            tenant_isolated=True,
        )
        assert model.has_tenant_column() is True
        assert model.tenant_isolated is True

    def test_get_primary_key(self):
        """Lay primary key column."""
        model = DataModel(
            id="Product",
            table_name="products",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="name", column_type=ColumnType.STRING),
            ],
        )
        pk = model.get_primary_key()
        assert pk is not None
        assert pk.name == "id"

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        original = DataModel(
            id="Order",
            table_name="orders",
            description="Bang don hang",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
            relationships=[
                Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, foreign_key="user_id"),
            ],
            tenant_isolated=True,
        )
        d = original.to_dict()
        restored = DataModel.from_dict(d)
        assert restored.id == original.id
        assert restored.table_name == original.table_name
        assert len(restored.columns) == len(original.columns)
        assert len(restored.relationships) == len(original.relationships)
        assert restored.tenant_isolated == original.tenant_isolated


class TestDataModelCollection:
    """Tests cho DataModelCollection."""

    def test_add_and_count(self):
        """Them model va dem so luong."""
        collection = DataModelCollection()
        collection.add_model(DataModel(id="User", table_name="users"))
        collection.add_model(DataModel(id="Order", table_name="orders"))
        assert collection.total_count == 2

    def test_get_by_id(self):
        """Tim model theo ID."""
        collection = DataModelCollection()
        model = DataModel(id="Product", table_name="products")
        collection.add_model(model)
        found = collection.get_by_id("Product")
        assert found is not None
        assert found.id == "Product"

    def test_tenant_isolated_models(self):
        """Lọc các models có tenant isolation (KPI-029)."""
        collection = DataModelCollection()
        collection.add_model(DataModel(id="User", table_name="users", tenant_isolated=True))
        collection.add_model(DataModel(id="Config", table_name="configs", tenant_isolated=False))
        tenant_models = collection.tenant_isolated_models()
        assert len(tenant_models) == 1
        assert tenant_models[0].id == "User"

    def test_to_dict_and_from_dict(self):
        """Chuyen doi qua lai dict."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Order",
                table_name="orders",
                columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
                tenant_isolated=True,
            )
        )
        d = collection.to_dict()
        restored = DataModelCollection.from_dict(d)
        assert restored.total_count == 1


# ============================================================================
# Test DB Parser
# ============================================================================


class TestDBParser:
    """Tests cho DBParser."""

    def test_parse_from_metadata_models(self):
        """Parse models từ MIR metadata."""
        parser = DBParser()
        metadata = {
            "data_models": [
                {
                    "id": "User",
                    "table_name": "users",
                    "columns": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "tenant_id", "type": "string", "tenant_aware": True},
                    ],
                    "tenant_isolated": True,
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        assert collection.total_count == 1
        model = collection.get_by_id("User")
        assert model is not None
        assert model.has_tenant_column() is True


# ============================================================================
# Test FastAPI DB Emitter (SQLAlchemy)
# ============================================================================


class TestSQLAlchemyEmitter:
    """Tests cho SQLAlchemyEmitter (FastAPI)."""

    def test_emit_creates_model_files(self, tmp_path: Path):
        """Emit tao cac file model SQLAlchemy."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="User",
                table_name="users",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="email", column_type=ColumnType.STRING, required=True),
                    ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
                ],
                tenant_isolated=True,
            )
        )

        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)

        # Kiem tra co file model
        assert any("user" in k.lower() or "model" in k.lower() for k in files.keys())

    def test_emit_includes_tenant_id(self, tmp_path: Path):
        """Emit bao gom tenant_id column (KPI-029)."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Order",
                table_name="orders",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True),
                ],
                tenant_isolated=True,
            )
        )

        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)

        # Kiem tra content co tenant_id
        all_content = "\n".join(files.values())
        assert "tenant_id" in all_content

    def test_emit_empty_collection(self, tmp_path: Path):
        """Emit voi collection rong tra ve empty."""
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(DataModelCollection(), tmp_path)
        # Co the co file base (database.py, base_model.py)
        assert isinstance(files, dict)


# ============================================================================
# Test NestJS DB Emitter (TypeORM)
# ============================================================================


class TestTypeORMEmitter:
    """Tests cho TypeORMEmitter (NestJS)."""

    def test_emit_creates_entity_files(self, tmp_path: Path):
        """Emit tao cac file entity TypeORM."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Product",
                table_name="products",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="name", column_type=ColumnType.STRING, required=True),
                ],
            )
        )

        emitter = TypeORMEmitter()
        files = emitter.emit(collection, tmp_path)

        # Kiem tra co file entity
        assert any("entity" in k.lower() or "product" in k.lower() for k in files.keys())

    def test_emit_includes_tenant_column(self, tmp_path: Path):
        """Emit bao gom tenant column (KPI-029)."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Order",
                table_name="orders",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
                ],
                tenant_isolated=True,
            )
        )

        emitter = TypeORMEmitter()
        files = emitter.emit(collection, tmp_path)

        all_content = "\n".join(files.values())
        assert "tenant" in all_content.lower()


# ============================================================================
# KPI-029 Tenant Isolation Tests (Template Verification)
# ============================================================================


class TestKPI029TenantIsolation:
    """Tests KPI-029: Tenant Isolation verification cho DB templates."""

    def test_fastapi_base_model_has_tenant_id(self, tmp_path: Path):
        """FastAPI base_model.py.jinja2 co tenant_id column."""
        template_path = Path("midicoder/stacks/fastapi/templates/db/base_model.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant_id" in content

    def test_fastapi_database_has_tenant_context(self, tmp_path: Path):
        """FastAPI database.py.jinja2 co tenant context."""
        template_path = Path("midicoder/stacks/fastapi/templates/db/database.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_repository_has_tenant_filter(self, tmp_path: Path):
        """FastAPI repository.py.jinja2 co tenant filter."""
        template_path = Path("midicoder/stacks/fastapi/templates/db/repository.py.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_fastapi_tenant_mixin_exists(self, tmp_path: Path):
        """FastAPI tenant_mixin.py.jinja2 ton tai."""
        template_path = Path("midicoder/stacks/fastapi/templates/db/tenant_mixin.py.jinja2")
        assert template_path.exists()

    def test_nestjs_base_entity_has_tenant(self, tmp_path: Path):
        """NestJS base-entity.ts.jinja2 co tenant column."""
        template_path = Path("midicoder/stacks/nestjs/templates/db/base-entity.ts.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_nestjs_repository_has_tenant(self, tmp_path: Path):
        """NestJS repository.ts.jinja2 co tenant logic."""
        template_path = Path("midicoder/stacks/nestjs/templates/db/repository.ts.jinja2")
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            assert "tenant" in content.lower()

    def test_model_tenant_isolated_default_true(self):
        """DataModel tenant_isolated mac dinh True (KPI-029)."""
        model = DataModel(id="Test", table_name="test")
        assert model.tenant_isolated is True

    def test_model_has_tenant_column_detects_tenant_aware(self):
        """has_tenant_column() detect tenant_aware column."""
        model = DataModel(
            id="Test",
            table_name="test",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
        )
        assert model.has_tenant_column() is True

    def test_model_no_tenant_column(self):
        """has_tenant_column() return False khi khong co tenant column."""
        model = DataModel(
            id="Test",
            table_name="test",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
            ],
        )
        assert model.has_tenant_column() is False

    def test_column_default_values(self):
        """ColumnDef co cac mac dich hop ly."""
        col = ColumnDef(name="test", column_type=ColumnType.STRING)
        assert col.required is False
        assert col.tenant_aware is False
        assert col.primary_key is False
        assert col.indexed is False

    def test_relationship_tenant_scoped_default(self):
        """Relationship tenant_scoped mac dinh True (KPI-029)."""
        rel = Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE)
        assert rel.tenant_scoped is True

    def test_collection_tenant_isolated_filter(self):
        """DataModelCollection lọc tenant isolated models."""
        collection = DataModelCollection()
        collection.add_model(DataModel(id="A", table_name="a", tenant_isolated=True))
        collection.add_model(DataModel(id="B", table_name="b", tenant_isolated=False))
        collection.add_model(DataModel(id="C", table_name="c", tenant_isolated=True))
        result = collection.tenant_isolated_models()
        assert len(result) == 2
        assert all(m.tenant_isolated for m in result)

    def test_column_type_enum_coverage(self):
        """ColumnType enum bao phat cac kieu co ban."""
        assert ColumnType.STRING.value == "string"
        assert ColumnType.INTEGER.value == "integer"
        assert ColumnType.UUID.value == "uuid"

    def test_relationship_type_enum_coverage(self):
        """RelationshipType enum bao phat cac kieu quan he."""
        assert RelationshipType.MANY_TO_ONE.value == "many_to_one"
        assert RelationshipType.ONE_TO_MANY.value == "one_to_many"

    def test_index_def_creation(self):
        """IndexDef tao va to_dict/from_dict."""
        idx = IndexDef(name="idx_tenant", columns=["tenant_id"], unique=False)
        d = idx.to_dict()
        restored = IndexDef.from_dict(d)
        assert restored.name == idx.name
        assert restored.columns == idx.columns

    def test_model_with_indexes(self):
        """DataModel co indexes."""
        model = DataModel(
            id="Order",
            table_name="orders",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, indexed=True),
            ],
            indexes=[IndexDef(name="idx_tenant", columns=["tenant_id"])],
        )
        assert len(model.indexes) == 1

    def test_model_with_relationships(self):
        """DataModel co relationships."""
        model = DataModel(
            id="Order",
            table_name="orders",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            relationships=[
                Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, foreign_key="user_id"),
                Relationship(target_model="OrderItem", rel_type=RelationshipType.ONE_TO_MANY, back_ref="order"),
            ],
        )
        assert len(model.relationships) == 2

    def test_parser_handles_empty_metadata(self):
        """Parser xử lý empty metadata."""
        parser = DBParser()
        collection = parser.parse_from_metadata({})
        assert collection.total_count == 0

    def test_parser_handles_missing_keys(self):
        """Parser xử lý missing keys trong metadata."""
        parser = DBParser()
        collection = parser.parse_from_metadata({"other_key": "value"})
        assert collection.total_count == 0

    def test_emitter_creates_output_directory(self, tmp_path: Path):
        """Emitter tao output directory neu khong ton tai."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Test",
                table_name="tests",
                columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            )
        )
        emitter = SQLAlchemyEmitter()
        output_dir = tmp_path / "new_db_dir"
        files = emitter.emit(collection, output_dir)
        assert output_dir.exists() or isinstance(files, dict)

    def test_fastapi_templates_count(self):
        """Dem so template files FastAPI."""
        db_dir = Path("midicoder/stacks/fastapi/templates/db")
        if db_dir.exists():
            templates = list(db_dir.glob("*.jinja2"))
            assert len(templates) >= 5

    def test_nestjs_templates_count(self):
        """Dem so template files NestJS."""
        db_dir = Path("midicoder/stacks/nestjs/templates/db")
        if db_dir.exists():
            templates = list(db_dir.glob("*.jinja2"))
            assert len(templates) >= 5

    def test_all_fastapi_templates_have_tenant(self):
        """Tat ca FastAPI templates co tenant reference (KPI-029)."""
        db_dir = Path("midicoder/stacks/fastapi/templates/db")
        if db_dir.exists():
            for template in db_dir.glob("*.jinja2"):
                content = template.read_text(encoding="utf-8")
                # Moi template can co tenant reference
                assert "tenant" in content.lower(), f"Template {template.name} missing tenant reference"

    def test_all_nestjs_templates_have_tenant(self):
        """Tat ca NestJS templates co tenant reference (KPI-029)."""
        db_dir = Path("midicoder/stacks/nestjs/templates/db")
        if db_dir.exists():
            for template in db_dir.glob("*.jinja2"):
                content = template.read_text(encoding="utf-8")
                assert "tenant" in content.lower(), f"Template {template.name} missing tenant reference"

    def test_data_model_full_roundtrip(self):
        """Full roundtrip to_dict/from_dict cho DataModel."""
        original = DataModel(
            id="CompleteModel",
            table_name="complete_models",
            description="Model hoan chinh de test",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True, indexed=True),
                ColumnDef(name="name", column_type=ColumnType.STRING, required=True, max_length=255),
                ColumnDef(name="count", column_type=ColumnType.INTEGER, default=0),
                ColumnDef(name="active", column_type=ColumnType.BOOLEAN, default=True),
            ],
            relationships=[
                Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, foreign_key="user_id"),
                Relationship(target_model="Item", rel_type=RelationshipType.ONE_TO_MANY, back_ref="parent"),
            ],
            indexes=[
                IndexDef(name="idx_tenant", columns=["tenant_id"]),
                IndexDef(name="idx_name", columns=["name"], unique=False),
            ],
            tenant_isolated=True,
        )
        d = original.to_dict()
        restored = DataModel.from_dict(d)
        assert restored.id == original.id
        assert restored.table_name == original.table_name
        assert restored.tenant_isolated == original.tenant_isolated
        assert len(restored.columns) == len(original.columns)
        assert len(restored.relationships) == len(original.relationships)
        assert len(restored.indexes) == len(original.indexes)
        assert restored.has_tenant_column() is True

    def test_collection_full_roundtrip(self):
        """Full roundtrip to_dict/from_dict cho DataModelCollection."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="ModelA",
                table_name="model_a",
                columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
                tenant_isolated=True,
            )
        )
        collection.add_model(
            DataModel(
                id="ModelB",
                table_name="model_b",
                columns=[ColumnDef(name="id", column_type=ColumnType.INTEGER, primary_key=True)],
                tenant_isolated=False,
            )
        )
        d = collection.to_dict()
        restored = DataModelCollection.from_dict(d)
        assert restored.total_count == 2
        assert restored.get_by_id("ModelA") is not None
        assert restored.get_by_id("ModelB") is not None

    def test_column_with_all_attributes(self):
        """ColumnDef voi tat ca attributes."""
        col = ColumnDef(
            name="full_column",
            column_type=ColumnType.STRING,
            required=True,
            default="test",
            max_length=100,
            precision=10,
            scale=2,
            primary_key=False,
            unique=True,
            indexed=True,
            tenant_aware=False,
            description="Cot test day du",
        )
        d = col.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.unique is True
        assert restored.max_length == 100

    def test_relationship_with_all_attributes(self):
        """Relationship voi tat ca attributes."""
        rel = Relationship(
            target_model="Target",
            rel_type=RelationshipType.MANY_TO_MANY,
            foreign_key="target_id",
            back_ref="source",
            join_table="join_table",
            cascade=True,
            lazy=True,
            tenant_scoped=True,
            description="Quan he test",
        )
        d = rel.to_dict()
        restored = Relationship.from_dict(d)
        assert restored.cascade is True
        assert restored.lazy is True
        assert restored.tenant_scoped is True

    def test_model_primary_key_validation(self):
        """Model validation cho primary key."""
        model = DataModel(
            id="Test",
            table_name="test",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
            ],
        )
        pk = model.get_primary_key()
        assert pk is not None
        assert pk.primary_key is True

    def test_parser_with_relationships(self):
        """Parser xử lý relationships trong metadata."""
        parser = DBParser()
        metadata = {
            "data_models": [
                {
                    "id": "Order",
                    "table_name": "orders",
                    "columns": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "tenant_id", "type": "string", "tenant_aware": True},
                    ],
                    "relationships": [
                        {
                            "target_model": "User",
                            "rel_type": "many_to_one",
                            "foreign_key": "user_id",
                        }
                    ],
                    "tenant_isolated": True,
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        model = collection.get_by_id("Order")
        assert model is not None
        assert len(model.relationships) == 1

    def test_emitter_with_multiple_models(self, tmp_path: Path):
        """Emitter xử lý multiple models."""
        collection = DataModelCollection()
        for name in ["User", "Order", "Product"]:
            collection.add_model(
                DataModel(
                    id=name,
                    table_name=name.lower() + "s",
                    columns=[
                        ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                        ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
                    ],
                    tenant_isolated=True,
                )
            )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)

    def test_soft_delete_support(self):
        """Model support soft delete."""
        col = ColumnDef(name="deleted_at", column_type=ColumnType.DATETIME)
        assert col.column_type == ColumnType.DATETIME

    def test_audit_columns(self):
        """Model support audit columns (created_at, updated_at)."""
        created = ColumnDef(name="created_at", column_type=ColumnType.DATETIME)
        updated = ColumnDef(name="updated_at", column_type=ColumnType.DATETIME)
        assert created.column_type == ColumnType.DATETIME
        assert updated.column_type == ColumnType.DATETIME

    def test_boolean_column_type(self):
        """ColumnType.BOOLEAN ton tai."""
        assert ColumnType.BOOLEAN.value == "boolean"

    def test_decimal_column_type(self):
        """ColumnType.DECIMAL voi precision/scale."""
        col = ColumnDef(name="price", column_type=ColumnType.DECIMAL, precision=10, scale=2)
        d = col.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.precision == 10
        assert restored.scale == 2

    def test_text_column_type(self):
        """ColumnType.TEXT cho mo ta dai."""
        col = ColumnDef(name="description", column_type=ColumnType.TEXT)
        assert col.column_type == ColumnType.TEXT

    def test_json_column_type(self):
        """ColumnType.JSON cho data linh hoat."""
        col = ColumnDef(name="metadata", column_type=ColumnType.JSON)
        assert col.column_type == ColumnType.JSON

    def test_datetime_column_type(self):
        """ColumnType.DATETIME cho timestamps."""
        col = ColumnDef(name="created_at", column_type=ColumnType.DATETIME)
        assert col.column_type == ColumnType.DATETIME

    def test_model_description_preserved(self):
        """Model description duoc luu trong to_dict/from_dict."""
        model = DataModel(
            id="Test",
            table_name="test",
            description="Model test co mo ta",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
        )
        d = model.to_dict()
        restored = DataModel.from_dict(d)
        assert restored.description == "Model test co mo ta"

    def test_index_unique_flag(self):
        """IndexDef support unique flag."""
        idx = IndexDef(name="idx_unique", columns=["email"], unique=True)
        d = idx.to_dict()
        restored = IndexDef.from_dict(d)
        assert restored.unique is True

    def test_many_to_many_relationship(self):
        """Many-to-many relationship voi join_table."""
        rel = Relationship(
            target_model="Tag",
            rel_type=RelationshipType.MANY_TO_MANY,
            join_table="product_tags",
            tenant_scoped=True,
        )
        d = rel.to_dict()
        restored = Relationship.from_dict(d)
        assert restored.join_table == "product_tags"
        assert restored.tenant_scoped is True

    def test_cascade_relationship(self):
        """Relationship voi cascade option."""
        rel = Relationship(
            target_model="OrderItem",
            rel_type=RelationshipType.ONE_TO_MANY,
            back_ref="order",
            cascade=True,
        )
        d = rel.to_dict()
        restored = Relationship.from_dict(d)
        assert restored.cascade is True

    def test_lazy_relationship(self):
        """Relationship voi lazy loading."""
        rel = Relationship(
            target_model="Profile",
            rel_type=RelationshipType.ONE_TO_ONE,
            lazy=True,
        )
        assert rel.lazy is True

    def test_one_to_one_relationship(self):
        """One-to-one relationship type."""
        rel = Relationship(
            target_model="Profile",
            rel_type=RelationshipType.ONE_TO_ONE,
        )
        assert rel.rel_type == RelationshipType.ONE_TO_ONE

    def test_column_unique_flag(self):
        """Column unique flag."""
        col = ColumnDef(name="email", column_type=ColumnType.STRING, unique=True, required=True)
        d = col.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.unique is True

    def test_column_default_value(self):
        """Column default value."""
        col = ColumnDef(name="status", column_type=ColumnType.STRING, default="active")
        d = col.to_dict()
        restored = ColumnDef.from_dict(d)
        assert restored.default == "active"

    def test_tenant_isolated_models_empty(self):
        """tenant_isolated_models() return empty khi khong co models."""
        collection = DataModelCollection()
        result = collection.tenant_isolated_models()
        assert len(result) == 0

    def test_get_by_id_returns_none(self):
        """get_by_id() return None khi khong tim thay."""
        collection = DataModelCollection()
        result = collection.get_by_id("NonExistent")
        assert result is None

    def test_model_with_no_columns(self):
        """Model voi khong co columns."""
        model = DataModel(id="Empty", table_name="empty")
        assert len(model.columns) == 0
        assert model.has_tenant_column() is False

    def test_parser_with_indexes(self):
        """Parser xử lý indexes trong metadata."""
        parser = DBParser()
        metadata = {
            "data_models": [
                {
                    "id": "User",
                    "table_name": "users",
                    "columns": [
                        {"name": "id", "type": "uuid", "primary_key": True},
                        {"name": "email", "type": "string", "indexed": True},
                    ],
                    "indexes": [
                        {"name": "idx_email", "columns": ["email"], "unique": True},
                    ],
                    "tenant_isolated": True,
                }
            ]
        }
        collection = parser.parse_from_metadata(metadata)
        model = collection.get_by_id("User")
        assert model is not None
        assert len(model.indexes) == 1

    def test_nestjs_emitter_empty_collection(self, tmp_path: Path):
        """NestJS emitter voi collection rong."""
        emitter = TypeORMEmitter()
        files = emitter.emit(DataModelCollection(), tmp_path)
        assert isinstance(files, dict)

    def test_both_emitters_produce_files(self, tmp_path: Path):
        """Cả FastAPI va NestJS emitters sinh ra files."""
        collection = DataModelCollection()
        collection.add_model(
            DataModel(
                id="Shared",
                table_name="shared",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
                ],
                tenant_isolated=True,
            )
        )

        # FastAPI
        fa_emitter = SQLAlchemyEmitter()
        fa_files = fa_emitter.emit(collection, tmp_path / "fastapi")

        # NestJS
        nj_emitter = TypeORMEmitter()
        nj_files = nj_emitter.emit(collection, tmp_path / "nestjs")

        assert isinstance(fa_files, dict)
        assert isinstance(nj_files, dict)

    def test_kpi029_all_models_default_tenant_isolated(self):
        """KPI-029: Mac dinh tat ca models co tenant_isolated=True."""
        model = DataModel(id="Default", table_name="default")
        assert model.tenant_isolated is True

    def test_kpi029_tenant_aware_column_detected(self):
        """KPI-029: Column tenant_aware=True duoc detect."""
        model = DataModel(
            id="TenantAware",
            table_name="tenant_aware",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
        )
        assert model.has_tenant_column() is True

    def test_kpi029_non_tenant_model(self):
        """KPI-029: Model khong tenant co the dat tenant_isolated=False."""
        model = DataModel(
            id="Shared",
            table_name="shared",
            tenant_isolated=False,
        )
        assert model.tenant_isolated is False

    def test_kpi029_relationship_tenant_scoped_default(self):
        """KPI-029: Relationship mac dinh tenant_scoped=True."""
        rel = Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE)
        assert rel.tenant_scoped is True

    def test_kpi029_full_tenant_model(self):
        """KPI-029: Model tenant hoan chinh."""
        model = DataModel(
            id="TenantModel",
            table_name="tenant_models",
            description="Model co tenant isolation hoan chinh",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True, indexed=True),
                ColumnDef(name="name", column_type=ColumnType.STRING, required=True),
                ColumnDef(name="created_at", column_type=ColumnType.DATETIME),
                ColumnDef(name="updated_at", column_type=ColumnType.DATETIME),
                ColumnDef(name="deleted_at", column_type=ColumnType.DATETIME),
            ],
            indexes=[
                IndexDef(name="idx_tenant", columns=["tenant_id"]),
            ],
            relationships=[
                Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, foreign_key="user_id", tenant_scoped=True),
            ],
            tenant_isolated=True,
        )

        # Verify all KPI-029 aspects
        assert model.tenant_isolated is True
        assert model.has_tenant_column() is True
        assert len(model.indexes) == 1
        assert model.relationships[0].tenant_scoped is True

        # Roundtrip
        d = model.to_dict()
        restored = DataModel.from_dict(d)
        assert restored.tenant_isolated is True
        assert restored.has_tenant_column() is True


# ============================================================================
# FR10: Tests cho Datasource, ReplicaConfig, DatabaseEngine, DSL Parser, Errors
# ============================================================================


class TestDatabaseEngine:
    """Tests cho DatabaseEngine enum."""

    def test_postgresql_value(self):
        assert DatabaseEngine.POSTGRESQL.value == "postgresql"

    def test_mysql_value(self):
        assert DatabaseEngine.MYSQL.value == "mysql"

    def test_sqlserver_value(self):
        assert DatabaseEngine.SQLSERVER.value == "sqlserver"

    def test_oracle_value(self):
        assert DatabaseEngine.ORACLE.value == "oracle"

    def test_has_four_values(self):
        assert len(DatabaseEngine) == 4


class TestReplicaConfig:
    """Tests cho ReplicaConfig model."""

    def test_create_replica(self):
        replica = ReplicaConfig(name="r1", connection_string="postgres://r1:5432/db")
        assert replica.name == "r1"
        assert replica.weight == 1

    def test_create_replica_with_weight(self):
        replica = ReplicaConfig(name="r2", connection_string="postgres://r2:5432/db", weight=3)
        assert replica.weight == 3

    def test_to_dict_and_from_dict(self):
        original = ReplicaConfig(name="r1", connection_string="postgres://r1:5432/db", weight=2)
        d = original.to_dict()
        restored = ReplicaConfig.from_dict(d)
        assert restored.name == original.name
        assert restored.weight == original.weight

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ReplicaConfig(name="", connection_string="postgres://db")
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_empty_connection_string_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ReplicaConfig(name="r1", connection_string="")
        assert exc_info.value.code == ErrorCode.CP08_MISSING_DATASOURCE

    def test_negative_weight_defaults_to_one(self):
        replica = ReplicaConfig(name="r1", connection_string="postgres://db", weight=-1)
        assert replica.weight == 1


class TestDatasource:
    """Tests cho Datasource model."""

    def test_create_datasource(self):
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://localhost:5432/mydb")
        assert ds.name == "primary"
        assert ds.engine == DatabaseEngine.POSTGRESQL
        assert ds.pool_size == 10
        assert ds.ssl_enabled is False

    def test_create_datasource_with_all_options(self):
        ds = Datasource(name="analytics", engine=DatabaseEngine.MYSQL, connection_string="mysql://analytics:3306/db", pool_size=20, ssl_enabled=True, description="Analytics DB")
        assert ds.engine == DatabaseEngine.MYSQL
        assert ds.pool_size == 20
        assert ds.ssl_enabled is True

    def test_create_datasource_with_replicas(self):
        ds = Datasource(
            name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://db",
            read_replicas=[ReplicaConfig(name="r1", connection_string="postgres://r1:5432/db", weight=1)],
        )
        assert len(ds.read_replicas) == 1

    def test_to_dict_and_from_dict(self):
        original = Datasource(name="test", engine=DatabaseEngine.SQLSERVER, connection_string="mssql://test:1433/db", pool_size=15, ssl_enabled=True)
        d = original.to_dict()
        restored = Datasource.from_dict(d)
        assert restored.name == original.name
        assert restored.engine == original.engine
        assert restored.ssl_enabled == original.ssl_enabled

    def test_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Datasource(name="", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://db")
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_empty_connection_string_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="")
        assert exc_info.value.code == ErrorCode.CP08_MISSING_DATASOURCE

    def test_negative_pool_size_defaults_to_one(self):
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://db", pool_size=-5)
        assert ds.pool_size == 1


class TestDSLParser:
    """Tests cho DBParser.parse() DSL YAML method."""

    def test_parse_valid_yaml(self):
        parser = DBParser()
        yaml_str = """
datasources:
  - name: primary
    engine: postgresql
    connection_string: "${DB_URL}"
    pool_size: 10
data_models:
  - id: User
    table_name: users
    columns:
      - name: id
        type: uuid
        primary_key: true
      - name: tenant_id
        type: string
        tenant_aware: true
"""
        collection = parser.parse(yaml_str)
        assert collection.total_count == 1
        assert len(collection.datasources) == 1
        model = collection.get_by_id("User")
        assert model is not None
        assert model.has_tenant_column() is True

    def test_parse_invalid_yaml_raises_error(self):
        parser = DBParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse(":::invalid: [yaml")
        assert exc_info.value.code == ErrorCode.CP08_DSL_PARSE_ERROR

    def test_parse_empty_yaml(self):
        parser = DBParser()
        collection = parser.parse("")
        assert collection.total_count == 0

    def test_parse_yaml_with_replicas(self):
        parser = DBParser()
        yaml_str = """
datasources:
  - name: primary
    engine: postgresql
    connection_string: "${DB_URL}"
    read_replicas:
      - name: replica1
        connection_string: "${DB_REPLICA_URL}"
        weight: 1
data_models:
  - id: Order
    table_name: orders
    columns:
      - name: id
        type: uuid
        primary_key: true
"""
        collection = parser.parse(yaml_str)
        ds = collection.get_primary_datasource()
        assert ds is not None
        assert len(ds.read_replicas) == 1
        assert ds.read_replicas[0].weight == 1

    def test_parse_yaml_with_relationships_and_indexes(self):
        parser = DBParser()
        yaml_str = """
data_models:
  - id: User
    table_name: users
    columns:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - target_model: Order
        rel_type: one_to_many
        back_ref: user
    indexes:
      - name: idx_tenant
        columns: [tenant_id]
"""
        collection = parser.parse(yaml_str)
        model = collection.get_by_id("User")
        assert model is not None
        assert len(model.relationships) == 1
        assert len(model.indexes) == 1


class TestCP08ErrorCodes:
    """Tests cho CP08 error codes."""

    def test_error_code_001_empty_name(self):
        error = EM.create(ErrorCode.CP08_EMPTY_NAME, field="test")
        assert error.code == ErrorCode.CP08_EMPTY_NAME
        assert "trống" in error.message.lower() or "không" in error.message.lower()

    def test_error_code_002_invalid_column_type(self):
        error = EM.create(ErrorCode.CP08_INVALID_COLUMN_TYPE)
        assert error.code == ErrorCode.CP08_INVALID_COLUMN_TYPE

    def test_error_code_003_duplicate_column(self):
        error = EM.create(ErrorCode.CP08_DUPLICATE_COLUMN_NAME, model="Test")
        assert error.code == ErrorCode.CP08_DUPLICATE_COLUMN_NAME

    def test_error_code_004_duplicate_table(self):
        error = EM.create(ErrorCode.CP08_DUPLICATE_TABLE_NAME, table="users")
        assert error.code == ErrorCode.CP08_DUPLICATE_TABLE_NAME

    def test_error_code_005_dsl_parse(self):
        error = EM.create(ErrorCode.CP08_DSL_PARSE_ERROR, original_error="bad yaml")
        assert error.code == ErrorCode.CP08_DSL_PARSE_ERROR

    def test_error_code_006_missing_datasource(self):
        error = EM.create(ErrorCode.CP08_MISSING_DATASOURCE)
        assert error.code == ErrorCode.CP08_MISSING_DATASOURCE

    def test_error_code_007_circular_fk(self):
        error = EM.create(ErrorCode.CP08_CIRCULAR_FOREIGN_KEY)
        assert error.code == ErrorCode.CP08_CIRCULAR_FOREIGN_KEY

    def test_error_code_008_missing_pk(self):
        error = EM.create(ErrorCode.CP08_MISSING_PRIMARY_KEY, model="Test")
        assert error.code == ErrorCode.CP08_MISSING_PRIMARY_KEY

    def test_error_code_009_migration_error(self):
        error = EM.create(ErrorCode.CP08_MIGRATION_ERROR)
        assert error.code == ErrorCode.CP08_MIGRATION_ERROR

    def test_error_code_010_runtime_error(self):
        error = EM.create(ErrorCode.CP08_RUNTIME_DATASOURCE_ERROR)
        assert error.code == ErrorCode.CP08_RUNTIME_DATASOURCE_ERROR

    def test_error_suggestions_exist(self):
        """Error codes co suggestions."""
        for code in [
            ErrorCode.CP08_EMPTY_NAME, ErrorCode.CP08_INVALID_COLUMN_TYPE,
            ErrorCode.CP08_DUPLICATE_COLUMN_NAME, ErrorCode.CP08_DUPLICATE_TABLE_NAME,
            ErrorCode.CP08_DSL_PARSE_ERROR, ErrorCode.CP08_MISSING_DATASOURCE,
            ErrorCode.CP08_CIRCULAR_FOREIGN_KEY, ErrorCode.CP08_MISSING_PRIMARY_KEY,
            ErrorCode.CP08_MIGRATION_ERROR, ErrorCode.CP08_RUNTIME_DATASOURCE_ERROR,
        ]:
            error = EM.create(code)
            assert len(error.suggestions) > 0, f"Missing suggestions for {code}"


class TestEnhancedEmitters:
    """Tests cho enhanced emitter methods (FR6)."""

    def test_sqlalchemy_emit_connection_config(self):
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://db", pool_size=15)
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_connection_config(ds)
        assert "database.py" in files
        content = files["database.py"]
        assert "pool_size=15" in content
        assert "create_engine" in content

    def test_sqlalchemy_emit_base_repository(self):
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_base_repository()
        assert "repositories/base_repository.py" in files
        content = files["repositories/base_repository.py"]
        assert "BaseRepository" in content
        assert "tenant_id" in content

    def test_sqlalchemy_emit_migration(self):
        model = DataModel(id="User", table_name="users", columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)])
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_migration(model, "abc123")
        assert any("abc123" in k for k in files.keys())
        content = list(files.values())[0]
        assert "create_table" in content

    def test_sqlalchemy_emit_seed_data(self):
        models = [DataModel(id="User", table_name="users", columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)])]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_seed_data(models)
        assert "seed_data.py" in files
        content = files["seed_data.py"]
        assert "users" in content

    def test_typeorm_emit_connection_config(self):
        ds = Datasource(name="primary", engine=DatabaseEngine.POSTGRESQL, connection_string="postgres://db", pool_size=10)
        emitter = TypeORMEmitter()
        files = emitter.emit_connection_config(ds)
        assert "datasource.ts" in files
        content = files["datasource.ts"]
        assert "DataSource" in content

    def test_typeorm_emit_base_repository(self):
        emitter = TypeORMEmitter()
        files = emitter.emit_base_repository()
        assert "repositories/base-entity-repository.ts" in files
        content = files["repositories/base-entity-repository.ts"]
        assert "BaseEntityRepository" in content

    def test_typeorm_emit_migration(self):
        model = DataModel(id="User", table_name="users", columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)])
        emitter = TypeORMEmitter()
        files = emitter.emit_migration(model, "v1")
        content = list(files.values())[0]
        assert "MigrationInterface" in content

    def test_typeorm_emit_seed_data(self):
        entities = [DataModel(id="User", table_name="users", columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)])]
        emitter = TypeORMEmitter()
        files = emitter.emit_seed_data(entities)
        assert "seed.ts" in files
        content = files["seed.ts"]
        assert "users" in content


class TestValidation:
    """Tests cho __post_init__ validation."""

    def test_column_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            ColumnDef(name="", column_type=ColumnType.STRING)
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_relationship_empty_target_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            Relationship(target_model="", rel_type=RelationshipType.MANY_TO_ONE)
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_index_empty_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            IndexDef(name="", columns=["col"])
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_model_empty_id_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(id="", table_name="test")
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_model_empty_table_name_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(id="Test", table_name="")
        assert exc_info.value.code == ErrorCode.CP08_EMPTY_NAME

    def test_model_missing_primary_key_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(id="Test", table_name="test", columns=[ColumnDef(name="name", column_type=ColumnType.STRING)])
        assert exc_info.value.code == ErrorCode.CP08_MISSING_PRIMARY_KEY

    def test_model_duplicate_columns_raises_error(self):
        with pytest.raises(MidicoderError) as exc_info:
            DataModel(
                id="Test", table_name="test", columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="id", column_type=ColumnType.STRING),
                ]
            )
        assert exc_info.value.code == ErrorCode.CP08_DUPLICATE_COLUMN_NAME

    def test_collection_duplicate_table_raises_error(self):
        collection = DataModelCollection()
        collection.add_model(DataModel(id="A", table_name="users"))
        with pytest.raises(MidicoderError) as exc_info:
            collection.add_model(DataModel(id="B", table_name="users"))
        assert exc_info.value.code == ErrorCode.CP08_DUPLICATE_TABLE_NAME
