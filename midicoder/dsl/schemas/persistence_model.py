from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


PERSISTENCE_ENGINE_CATALOG = {
    "postgres",
    "mysql",
    "redis",
}

PERSISTENCE_CONNECTOR_CATALOG = {
    "sqlalchemy",
    "psycopg",
    "asyncpg",
    "mysqlclient",
    "aiomysql",
    "redis-py",
}

PERSISTENCE_CONSTRAINT_KEY_CATALOG = {
    "primary_key",
    "unique",
    "foreign_key",
    "default",
    "check",
}


class PersistenceDatasource(BaseModel):
    id: str
    engine: str
    connector: Optional[str] = None
    database: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db_schema: Optional[str] = Field(default=None, alias="schema")
    default: bool = False
    options: dict[str, Any] = Field(default_factory=dict)
    integration_id: Optional[str] = None

    model_config = {"extra": "forbid", "populate_by_name": True}


class PersistenceColumn(BaseModel):
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None
    constraints: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class PersistenceIndex(BaseModel):
    name: str
    columns: list[str] = Field(default_factory=list)
    unique: bool = False

    model_config = {"extra": "forbid"}


class PersistenceTable(BaseModel):
    id: str
    description: Optional[str] = None
    datasource: Optional[str] = None
    operation_id: Optional[str] = None
    columns: list[PersistenceColumn] = Field(default_factory=list)
    indexes: list[PersistenceIndex] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="persistence.table",
        usage_en=(
            "Physical persistence table or collection definition used to map "
            "domain entities and read/write storage concerns."
        ),
    )


class PersistenceModelFile(BaseModel):
    datasources: list[PersistenceDatasource] = Field(default_factory=list)
    tables: list[PersistenceTable]

    model_config = {"extra": "forbid"}
