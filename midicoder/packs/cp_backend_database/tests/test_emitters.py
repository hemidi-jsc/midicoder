# coding: utf-8
"""
Tests cho FastAPI (SQLAlchemy) và NestJS (TypeORM) emitters (CP08).

Bao gồm:
- SQLAlchemyEmitter: emit, emit_connection_config, emit_base_repository,
  emit_migration, emit_seed_data
- TypeORMEmitter: emit, emit_connection_config, emit_base_repository,
  emit_migration, emit_seed_data
- Both emitters with tenant isolation (KPI-029)
- Edge cases: empty collection, multiple models, all column types
"""

import pytest
from pathlib import Path

from midicoder.packs.cp_backend_database.models import (
    ColumnDef,
    ColumnType,
    DataModel,
    DataModelCollection,
    DatabaseEngine,
    Datasource,
    Relationship,
    RelationshipType,
    IndexDef,
)
from midicoder.packs.cp_backend_database.fastapi import SQLAlchemyEmitter
from midicoder.packs.cp_backend_database.nestjs import TypeORMEmitter


class TestSQLAlchemyEmitter:
    def test_emit_creates_model_files(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="User", table_name="users",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
        ))
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)
        assert any("user" in k.lower() for k in files.keys())
        # Should also produce __init__.py
        assert any("__init__" in k for k in files.keys())

    def test_emit_includes_tenant_id(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Order", table_name="orders",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True),
            ],
            tenant_isolated=True,
        ))
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "tenant_id" in all_content

    def test_emit_empty_collection(self, tmp_path: Path):
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(DataModelCollection(), tmp_path)
        assert isinstance(files, dict)

    def test_emit_with_relationships(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Order", table_name="orders",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            relationships=[Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, foreign_key="user_id")],
        ))
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "relationship" in all_content

    def test_emit_connection_config(self):
        ds = Datasource(
            name="primary", engine=DatabaseEngine.POSTGRESQL,
            connection_string="postgresql://localhost:5432/mydb",
            pool_size=15,
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_connection_config(ds)
        assert "database.py" in files
        content = files["database.py"]
        assert "create_engine" in content
        assert "pool_size=15" in content

    def test_emit_connection_config_with_replicas(self):
        ds = Datasource(
            name="primary", engine=DatabaseEngine.POSTGRESQL,
            connection_string="pg://db",
            read_replicas=[__import__("midicoder.packs.cp_backend_database.models", fromlist=["ReplicaConfig"]).ReplicaConfig(
                name="r1", connection_string="pg://r1", weight=1
            )],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_connection_config(ds)
        content = files["database.py"]
        assert "r1" in content

    def test_emit_connection_config_ssl(self):
        ds = Datasource(
            name="primary", engine=DatabaseEngine.POSTGRESQL,
            connection_string="pg://db",
            ssl_enabled=True,
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_connection_config(ds)
        content = files["database.py"]
        assert "ssl" in content

    def test_emit_base_repository(self):
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_base_repository()
        assert "repositories/base_repository.py" in files
        content = files["repositories/base_repository.py"]
        assert "BaseRepository" in content
        assert "tenant_id" in content

    def test_emit_migration(self):
        model = DataModel(
            id="User", table_name="users",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            indexes=[IndexDef(name="idx_email", columns=["email"])],
        )
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_migration(model, "abc123")
        assert any("abc123" in k for k in files.keys())
        content = list(files.values())[0]
        assert "create_table" in content
        assert "upgrade" in content
        assert "downgrade" in content

    def test_emit_seed_data(self):
        models = [
            DataModel(id="User", table_name="users", columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]),
            DataModel(id="Order", table_name="orders", columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]),
        ]
        emitter = SQLAlchemyEmitter()
        files = emitter.emit_seed_data(models)
        assert "seed_data.py" in files
        content = files["seed_data.py"]
        assert "users" in content
        assert "orders" in content

    def test_emit_multiple_models(self, tmp_path: Path):
        collection = DataModelCollection()
        for name in ["User", "Order", "Product"]:
            collection.add_model(DataModel(
                id=name, table_name=name.lower() + "s",
                columns=[
                    ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                    ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
                ],
                tenant_isolated=True,
            ))
        emitter = SQLAlchemyEmitter()
        files = emitter.emit(collection, tmp_path)
        assert isinstance(files, dict)
        assert len(files) >= 3  # at least 3 model files + __init__.py


class TestTypeORMEmitter:
    def test_emit_creates_entity_files(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Product", table_name="products",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="name", column_type=ColumnType.STRING, required=True),
            ],
        ))
        emitter = TypeORMEmitter()
        files = emitter.emit(collection, tmp_path)
        assert any("product" in k.lower() for k in files.keys())
        assert any("index" in k.lower() for k in files.keys())

    def test_emit_includes_tenant(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Order", table_name="orders",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
            tenant_isolated=True,
        ))
        emitter = TypeORMEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "tenant" in all_content.lower()

    def test_emit_empty_collection(self, tmp_path: Path):
        emitter = TypeORMEmitter()
        files = emitter.emit(DataModelCollection(), tmp_path)
        assert isinstance(files, dict)

    def test_emit_with_relationships(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Order", table_name="orders",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
            relationships=[Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE)],
        ))
        emitter = TypeORMEmitter()
        files = emitter.emit(collection, tmp_path)
        all_content = "\n".join(files.values())
        assert "ManyToOne" in all_content

    def test_emit_connection_config(self):
        ds = Datasource(
            name="primary", engine=DatabaseEngine.POSTGRESQL,
            connection_string="postgresql://localhost:5432/mydb",
            pool_size=10,
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_connection_config(ds)
        assert "datasource.ts" in files
        content = files["datasource.ts"]
        assert "DataSource" in content
        # Verify f-string interpolation actually works (not hardcoded '${...}')
        assert "'postgresql'" in content
        assert "PRIMARY_URL" in content
        assert "'postgresql://localhost:5432/mydb'" in content

    def test_emit_connection_config_mysql(self):
        ds = Datasource(
            name="main", engine=DatabaseEngine.MYSQL,
            connection_string="mysql://localhost:3306/db",
            pool_size=20,
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_connection_config(ds)
        content = files["datasource.ts"]
        assert "'mysql'" in content
        assert "MAIN_URL" in content

    def test_emit_base_repository(self):
        emitter = TypeORMEmitter()
        files = emitter.emit_base_repository()
        assert "repositories/base-entity-repository.ts" in files
        content = files["repositories/base-entity-repository.ts"]
        assert "BaseEntityRepository" in content
        assert "tenantId" in content

    def test_emit_migration(self):
        model = DataModel(
            id="User", table_name="users",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)],
        )
        emitter = TypeORMEmitter()
        files = emitter.emit_migration(model, "v1")
        content = list(files.values())[0]
        assert "MigrationInterface" in content
        assert "Createusersv1" in content  # emitter uses lowercase table_name

    def test_emit_seed_data(self):
        entities = [DataModel(
            id="User", table_name="users",
            columns=[ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True)]
        )]
        emitter = TypeORMEmitter()
        files = emitter.emit_seed_data(entities)
        assert "seed.ts" in files
        content = files["seed.ts"]
        assert "users" in content

    def test_kebab_case_helper(self):
        emitter = TypeORMEmitter()
        assert TypeORMEmitter._to_kebab_case("UserOrder") == "user-order"
        assert TypeORMEmitter._to_kebab_case("AlreadyKebab") == "already-kebab"

    def test_camel_case_helper(self):
        emitter = TypeORMEmitter()
        assert TypeORMEmitter._to_camel_case("snake_case") == "snakeCase"
        assert TypeORMEmitter._to_camel_case("single") == "single"


class TestBothEmitters:
    """Compare FastAPI vs NestJS output for same input."""

    def test_both_emitters_produce_files(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="Shared", table_name="shared",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True),
            ],
            tenant_isolated=True,
        ))

        fa_emitter = SQLAlchemyEmitter()
        fa_files = fa_emitter.emit(collection, tmp_path / "fastapi")

        nj_emitter = TypeORMEmitter()
        nj_files = nj_emitter.emit(collection, tmp_path / "nestjs")

        assert isinstance(fa_files, dict)
        assert isinstance(nj_files, dict)
        assert len(fa_files) > 0
        assert len(nj_files) > 0

    def test_kpi029_both_emitters_tenant(self, tmp_path: Path):
        collection = DataModelCollection()
        collection.add_model(DataModel(
            id="TenantModel", table_name="tenant_models",
            columns=[
                ColumnDef(name="id", column_type=ColumnType.UUID, primary_key=True),
                ColumnDef(name="tenant_id", column_type=ColumnType.STRING, tenant_aware=True, required=True, indexed=True),
            ],
            indexes=[IndexDef(name="idx_tenant", columns=["tenant_id"])],
            relationships=[Relationship(target_model="User", rel_type=RelationshipType.MANY_TO_ONE, tenant_scoped=True)],
            tenant_isolated=True,
        ))

        fa = SQLAlchemyEmitter()
        fa_content = "\n".join(fa.emit(collection, tmp_path / "fa").values())
        assert "tenant" in fa_content.lower()

        nj = TypeORMEmitter()
        nj_content = "\n".join(nj.emit(collection, tmp_path / "nj").values())
        assert "tenant" in nj_content.lower()
