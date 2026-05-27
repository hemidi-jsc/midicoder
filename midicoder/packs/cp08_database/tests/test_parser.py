# coding: utf-8
"""
Tests cho DBParser (CP08).

Bao gồm:
- Parse YAML DSL string
- Parse from MIR metadata dict
- Edge cases: empty, invalid YAML, missing keys
"""

import pytest

from midicoder.packs.cp08_database.parser import DBParser
from midicoder.packs.cp08_database.models import (
    ColumnType,
    DatabaseEngine,
    RelationshipType,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestDBParser:
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
        assert model.has_tenant_column() is True

    def test_parse_empty_yaml(self):
        parser = DBParser()
        collection = parser.parse("")
        assert collection.total_count == 0

    def test_parse_none_input(self):
        parser = DBParser()
        collection = parser.parse(None)
        assert collection.total_count == 0

    def test_parse_invalid_yaml_raises_error(self):
        parser = DBParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse(":::invalid: [yaml")
        assert exc_info.value.code == ErrorCode.CP08_DSL_PARSE_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        parser = DBParser()
        with pytest.raises(MidicoderError) as exc_info:
            parser.parse("- just a list")
        assert exc_info.value.code == ErrorCode.CP08_DSL_PARSE_ERROR

    def test_parse_with_replicas(self):
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
        assert len(ds.read_replicas) == 1
        assert ds.read_replicas[0].weight == 1

    def test_parse_with_relationships_and_indexes(self):
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
        assert len(model.relationships) == 1
        assert len(model.indexes) == 1

    def test_parse_from_metadata(self):
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
        assert model.has_tenant_column() is True

    def test_parse_from_empty_metadata(self):
        parser = DBParser()
        collection = parser.parse_from_metadata({})
        assert collection.total_count == 0

    def test_parse_from_missing_keys(self):
        parser = DBParser()
        collection = parser.parse_from_metadata({"other_key": "value"})
        assert collection.total_count == 0

    def test_parse_all_engine_types(self):
        parser = DBParser()
        for eng_str in ["postgresql", "postgres", "mysql", "sqlserver", "mssql", "oracle"]:
            yaml_str = f"""
datasources:
  - name: primary
    engine: {eng_str}
    connection_string: "conn://db"
"""
            collection = parser.parse(yaml_str)
            assert len(collection.datasources) == 1

    def test_parse_all_column_types(self):
        parser = DBParser()
        for type_str in ["string", "integer", "boolean", "decimal", "text", "json", "datetime", "uuid"]:
            yaml_str = f"""
data_models:
  - id: Test
    table_name: tests
    columns:
      - name: id
        type: uuid
        primary_key: true
      - name: col
        type: {type_str}
"""
            collection = parser.parse(yaml_str)
            assert collection.total_count == 1

    def test_parse_new_column_types(self):
        parser = DBParser()
        yaml_str = """
data_models:
  - id: Test
    table_name: tests
    columns:
      - name: id
        type: uuid
        primary_key: true
      - name: tags
        type: array
      - name: data
        type: bytes
      - name: started_at
        type: time
"""
        collection = parser.parse(yaml_str)
        model = collection.get_by_id("Test")
        types = [c.column_type.value for c in model.columns]
        assert "array" in types
        assert "bytes" in types
        assert "time" in types

    def test_parse_all_relationship_types(self):
        parser = DBParser()
        for rel in ["many_to_one", "one_to_many", "one_to_one", "many_to_many"]:
            yaml_str = f"""
data_models:
  - id: Test
    table_name: tests
    columns:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - target_model: Other
        rel_type: {rel}
"""
            collection = parser.parse(yaml_str)
            model = collection.get_by_id("Test")
            assert model.relationships[0].rel_type.value == rel
