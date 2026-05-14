# coding: utf-8
"""
DB Parser - Parse MIR metadata và YAML DSL thành DataModelCollection.

Module này chứa DBParser để parse data models từ MIR metadata hoặc YAML DSL string.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass
from typing import Any

from midicoder.emitters.core.cp08_database.models import (
    DataModel,
    DataModelCollection,
    Datasource,
    DatabaseEngine,
    ReplicaConfig,
    ColumnDef,
    ColumnType,
    Relationship,
    RelationshipType,
    IndexDef,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# Mapping từ type string sang ColumnType enum
_TYPE_MAP = {
    "str": ColumnType.STRING, "string": ColumnType.STRING,
    "int": ColumnType.INTEGER, "integer": ColumnType.INTEGER,
    "bool": ColumnType.BOOLEAN, "boolean": ColumnType.BOOLEAN,
    "decimal": ColumnType.DECIMAL, "float": ColumnType.DECIMAL,
    "text": ColumnType.TEXT,
    "json": ColumnType.JSON,
    "datetime": ColumnType.DATETIME,
    "uuid": ColumnType.UUID,
    "array": ColumnType.ARRAY, "list": ColumnType.ARRAY,
    "bytes": ColumnType.BYTES, "binary": ColumnType.BYTES,
    "time": ColumnType.TIME,
}


# Mapping từ rel_type string sang RelationshipType enum
_REL_TYPE_MAP = {
    "many_to_one": RelationshipType.MANY_TO_ONE,
    "one_to_many": RelationshipType.ONE_TO_MANY,
    "one_to_one": RelationshipType.ONE_TO_ONE,
    "many_to_many": RelationshipType.MANY_TO_MANY,
}


# Mapping từ engine string sang DatabaseEngine enum
_ENGINE_MAP = {
    "postgresql": DatabaseEngine.POSTGRESQL,
    "postgres": DatabaseEngine.POSTGRESQL,
    "mysql": DatabaseEngine.MYSQL,
    "sqlserver": DatabaseEngine.SQLSERVER,
    "mssql": DatabaseEngine.SQLSERVER,
    "oracle": DatabaseEngine.ORACLE,
    "mongodb": DatabaseEngine.MONGODB,
    "mongo": DatabaseEngine.MONGODB,
    "sqlite": DatabaseEngine.SQLITE,
}


@dataclass
class DBParser:
    """
    Parser để convert MIR metadata và YAML DSL thành DataModelCollection.

    Input: Dictionary hoặc YAML string chứa 'datasources' và 'data_models'
    Output: DataModelCollection với tất cả models và datasources đã parse
    """

    def parse(self, raw: str) -> DataModelCollection:
        """
        Parse YAML DSL string thành DataModelCollection.

        Args:
            raw: YAML string chứa cấu hình database

        Returns:
            DataModelCollection với datasources và models

        Raises:
            MidicoderError: Với code MDC-CP08-005 khi YAML parse error
        """
        # Xu ly empty string: tra ve empty collection
        if not raw or not raw.strip():
            return DataModelCollection()

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(ErrorCode.CP08_DSL_PARSE_ERROR, original_error=str(e))

        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.CP08_DSL_PARSE_ERROR, reason="YAML root phai la mapping")

        return self._parse_from_dict(data)

    def _parse_from_dict(self, data: dict[str, Any]) -> DataModelCollection:
        """
        Parse dictionary thành DataModelCollection.

        Args:
            data: Dictionary chứa 'datasources' và/hoặc 'data_models'

        Returns:
            DataModelCollection
        """
        collection = DataModelCollection()

        # Parse datasources
        for ds_data in data.get("datasources", []):
            try:
                datasource = self._parse_datasource(ds_data)
                collection.add_datasource(datasource)
            except Exception:
                continue

        # Parse data models
        for model_dict in data.get("data_models", []):
            try:
                model = self._parse_model(model_dict)
                collection.add_model(model)
            except Exception:
                continue

        return collection

    def parse_from_metadata(self, metadata: dict[str, Any]) -> DataModelCollection:
        """
        Parse data models từ MIR metadata (backward compatible).

        Args:
            metadata: Dictionary chứa 'data_models' key

        Returns:
            DataModelCollection với tất cả models đã parse
        """
        return self._parse_from_dict(metadata)

    def _parse_datasource(self, data: dict[str, Any]) -> Datasource:
        """Parse một datasource dictionary."""
        # Parse read replicas
        replicas = []
        for replica_data in data.get("read_replicas", []):
            replicas.append(ReplicaConfig(
                name=replica_data.get("name", ""),
                connection_string=replica_data.get("connection_string", ""),
                weight=replica_data.get("weight", 1),
            ))

        engine_str = data.get("engine", "postgresql")
        engine = _ENGINE_MAP.get(engine_str, DatabaseEngine.POSTGRESQL)

        return Datasource(
            name=data.get("name", ""),
            engine=engine,
            connection_string=data.get("connection_string", ""),
            pool_size=data.get("pool_size", 10),
            max_overflow=data.get("max_overflow", 20),
            pool_timeout=data.get("pool_timeout", 30),
            pool_recycle=data.get("pool_recycle", 3600),
            read_replicas=replicas,
            ssl_enabled=data.get("ssl_enabled", False),
            description=data.get("description", ""),
        )

    def _parse_model(self, data: dict[str, Any]) -> DataModel:
        """Parse một model dictionary."""
        columns = []
        for col_data in data.get("columns", []):
            col_type = _TYPE_MAP.get(col_data.get("type", "string"), ColumnType.STRING)
            columns.append(ColumnDef(
                name=col_data.get("name", ""),
                column_type=col_type,
                required=col_data.get("required", False),
                default=col_data.get("default"),
                max_length=col_data.get("max_length"),
                precision=col_data.get("precision"),
                scale=col_data.get("scale"),
                primary_key=col_data.get("primary_key", False),
                unique=col_data.get("unique", False),
                indexed=col_data.get("indexed", False),
                tenant_aware=col_data.get("tenant_aware", False),
                description=col_data.get("description", ""),
            ))

        relationships = []
        for rel_data in data.get("relationships", []):
            rel_type = _REL_TYPE_MAP.get(rel_data.get("rel_type", "many_to_one"), RelationshipType.MANY_TO_ONE)
            relationships.append(Relationship(
                target_model=rel_data.get("target_model", ""),
                rel_type=rel_type,
                foreign_key=rel_data.get("foreign_key", ""),
                back_ref=rel_data.get("back_ref", ""),
                join_table=rel_data.get("join_table", ""),
                cascade=rel_data.get("cascade", False),
                lazy=rel_data.get("lazy", False),
                tenant_scoped=rel_data.get("tenant_scoped", True),
                description=rel_data.get("description", ""),
            ))

        indexes = []
        for idx_data in data.get("indexes", []):
            indexes.append(IndexDef(
                name=idx_data.get("name", ""),
                columns=idx_data.get("columns", []),
                unique=idx_data.get("unique", False),
            ))

        return DataModel(
            id=data.get("id", ""),
            table_name=data.get("table_name", ""),
            description=data.get("description", ""),
            columns=columns,
            relationships=relationships,
            indexes=indexes,
            tenant_isolated=data.get("tenant_isolated", True),
        )