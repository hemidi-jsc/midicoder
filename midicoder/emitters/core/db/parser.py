# coding: utf-8
"""
DB Parser - Parse MIR metadata thành DataModelCollection.

Module nay chua DBParser de parse data models tu MIR metadata.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from midicoder.emitters.core.db.models import (
    DataModel,
    DataModelCollection,
    ColumnDef,
    ColumnType,
    Relationship,
    RelationshipType,
    IndexDef,
)


# Mapping tu type string sang ColumnType enum
_TYPE_MAP = {
    "str": ColumnType.STRING, "string": ColumnType.STRING,
    "int": ColumnType.INTEGER, "integer": ColumnType.INTEGER,
    "bool": ColumnType.BOOLEAN, "boolean": ColumnType.BOOLEAN,
    "decimal": ColumnType.DECIMAL, "float": ColumnType.DECIMAL,
    "text": ColumnType.TEXT,
    "json": ColumnType.JSON,
    "datetime": ColumnType.DATETIME,
    "uuid": ColumnType.UUID,
}


# Mapping tu rel_type string sang RelationshipType enum
_REL_TYPE_MAP = {
    "many_to_one": RelationshipType.MANY_TO_ONE,
    "one_to_many": RelationshipType.ONE_TO_MANY,
    "one_to_one": RelationshipType.ONE_TO_ONE,
    "many_to_many": RelationshipType.MANY_TO_MANY,
}


@dataclass
class DBParser:
    """
    Parser de convert MIR metadata thanh DataModelCollection.

    Input: Dictionary chua 'data_models' key
    Output: DataModelCollection voi tat ca models da parse
    """

    def parse_from_metadata(self, metadata: dict[str, Any]) -> DataModelCollection:
        """
        Parse data models tu MIR metadata.

        Args:
            metadata: Dictionary chua 'data_models' key

        Returns:
            DataModelCollection voi tat ca models da parse
        """
        collection = DataModelCollection()

        for model_dict in metadata.get("data_models", []):
            try:
                model = self._parse_model(model_dict)
                collection.add_model(model)
            except Exception:
                continue

        return collection

    def _parse_model(self, data: dict[str, Any]) -> DataModel:
        """Parse mot model dictionary."""
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