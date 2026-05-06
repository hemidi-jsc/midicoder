# coding: utf-8
"""
Mô-đun models cho Database Emitter (CP08).

Định nghĩa các dataclass biểu diễn:
- DatabaseEngine: Enum các loại database engine
- ReplicaConfig: Cấu hình read replica
- Datasource: Kết nối database với pool config và replica support
- ColumnType/RelationshipType: Enum các kiểu dữ liệu và quan hệ
- ColumnDef: Định nghĩa column với type, constraints, tenant_aware
- Relationship: Quan hệ giữa các models (FK, back_ref, cascade)
- IndexDef: Định nghĩa index
- DataModel: Model hoàn chỉnh với columns, relationships, indexes
- DataModelCollection: Collection chứa tất cả models và datasources

KPI-029: Tenant Isolation - tenant_isolated=True mặc định, tenant_scoped=True cho relationships

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class DatabaseEngine(str, Enum):
    """Enum các loại database engine được hỗ trợ."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"


class ColumnType(str, Enum):
    """Enum các kiểu dữ liệu column."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    TEXT = "text"
    JSON = "json"
    DATETIME = "datetime"
    UUID = "uuid"


class RelationshipType(str, Enum):
    """Enum các kiểu quan hệ giữa models."""
    MANY_TO_ONE = "many_to_one"
    ONE_TO_MANY = "one_to_many"
    ONE_TO_ONE = "one_to_one"
    MANY_TO_MANY = "many_to_many"


# ===========================================================================
# ReplicaConfig
# ===========================================================================


@dataclass
class ReplicaConfig:
    """
    Cấu hình read replica cho datasource.

    Attributes:
        name: Tên replica (vd: "replica1")
        connection_string: URL kết nối đến replica
        weight: Weight cho load balancing (mặc định: 1)
    """
    name: str
    connection_string: str
    weight: int = 1

    def __post_init__(self) -> None:
        """Validate replica config sau khi khởi tạo."""
        # Tên replica không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="replica.name")
        # Connection string không được để trống
        if not self.connection_string or not self.connection_string.strip():
            EM.raise_error(ErrorCode.CP08_MISSING_DATASOURCE, field="replica.connection_string", replica=self.name)
        # Weight phải dương
        if self.weight < 1:
            self.weight = 1

    def to_dict(self) -> dict[str, Any]:
        """Chuyển replica config sang dict format."""
        return {
            "name": self.name,
            "connection_string": self.connection_string,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplicaConfig":
        """Tạo ReplicaConfig từ dict."""
        return cls(
            name=data.get("name", ""),
            connection_string=data.get("connection_string", ""),
            weight=data.get("weight", 1),
        )


# ===========================================================================
# Datasource
# ===========================================================================


@dataclass
class Datasource:
    """
    Cấu hình datasource - kết nối đến database.

    Attributes:
        name: Tên datasource (vd: "primary", "analytics")
        engine: Loại database engine (POSTGRESQL, MYSQL, SQLSERVER, ORACLE)
        connection_string: URL kết nối (support env var interpolation ${VAR})
        pool_size: Connection pool size (mặc định: 10)
        max_overflow: Max overflow connections (mặc định: 20)
        pool_timeout: Pool timeout giây (mặc định: 30)
        pool_recycle: Pool recycle seconds (mặc định: 3600)
        read_replicas: List read replica configs
        ssl_enabled: Có enable SSL không (mặc định: False)
        description: Mô tả datasource
    """
    name: str
    engine: DatabaseEngine
    connection_string: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    read_replicas: list[ReplicaConfig] = field(default_factory=list)
    ssl_enabled: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate datasource sau khi khởi tạo."""
        # Tên datasource không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="datasource.name")
        # Connection string không được để trống
        if not self.connection_string or not self.connection_string.strip():
            EM.raise_error(ErrorCode.CP08_MISSING_DATASOURCE, datasource=self.name)
        # Pool size phải dương
        if self.pool_size < 1:
            self.pool_size = 1
        # Max overflow phải >= 0
        if self.max_overflow < 0:
            self.max_overflow = 0
        # Pool timeout phải dương
        if self.pool_timeout < 1:
            self.pool_timeout = 30
        # Pool recycle phải dương
        if self.pool_recycle < 1:
            self.pool_recycle = 3600

    def to_dict(self) -> dict[str, Any]:
        """Chuyển datasource sang dict format."""
        return {
            "name": self.name,
            "engine": self.engine.value,
            "connection_string": self.connection_string,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "read_replicas": [r.to_dict() for r in self.read_replicas],
            "ssl_enabled": self.ssl_enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Datasource":
        """Tạo Datasource từ dict."""
        return cls(
            name=data.get("name", ""),
            engine=DatabaseEngine(data.get("engine", "postgresql")),
            connection_string=data.get("connection_string", ""),
            pool_size=data.get("pool_size", 10),
            max_overflow=data.get("max_overflow", 20),
            pool_timeout=data.get("pool_timeout", 30),
            pool_recycle=data.get("pool_recycle", 3600),
            read_replicas=[ReplicaConfig.from_dict(r) for r in data.get("read_replicas", [])],
            ssl_enabled=data.get("ssl_enabled", False),
            description=data.get("description", ""),
        )


# ===========================================================================
# ColumnDef
# ===========================================================================


@dataclass
class ColumnDef:
    """
    Định nghĩa column trong database model.

    Attributes:
        name: Tên column
        column_type: Kiểu dữ liệu (STRING, INTEGER, UUID, ...)
        required: Có bắt buộc không (NOT NULL)
        default: Giá trị mặc định
        max_length: Độ dài tối đa (cho STRING/TEXT)
        precision: Độ chính xác (cho DECIMAL)
        scale: Số chữ số thập phân (cho DECIMAL)
        primary_key: Có phải primary key không
        unique: Có unique constraint không
        indexed: Có index không
        tenant_aware: Có phải tenant column không (KPI-029)
        description: Mô tả column
    """
    name: str
    column_type: ColumnType
    required: bool = False
    default: Any = None
    max_length: int | None = None
    precision: int | None = None
    scale: int | None = None
    primary_key: bool = False
    unique: bool = False
    indexed: bool = False
    tenant_aware: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate column sau khi khởi tạo."""
        # Tên column không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="column.name")
        # Precision/scale phải dương nếu có
        if self.precision is not None and self.precision < 1:
            self.precision = 10
        if self.scale is not None and self.scale < 0:
            self.scale = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển column sang dict format."""
        return {
            "name": self.name,
            "type": self.column_type.value,
            "required": self.required,
            "default": self.default,
            "max_length": self.max_length,
            "precision": self.precision,
            "scale": self.scale,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "indexed": self.indexed,
            "tenant_aware": self.tenant_aware,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ColumnDef":
        """Tạo ColumnDef từ dict."""
        return cls(
            name=data.get("name", ""),
            column_type=ColumnType(data.get("type", "string")),
            required=data.get("required", False),
            default=data.get("default"),
            max_length=data.get("max_length"),
            precision=data.get("precision"),
            scale=data.get("scale"),
            primary_key=data.get("primary_key", False),
            unique=data.get("unique", False),
            indexed=data.get("indexed", False),
            tenant_aware=data.get("tenant_aware", False),
            description=data.get("description", ""),
        )


# ===========================================================================
# Relationship
# ===========================================================================


@dataclass
class Relationship:
    """
    Định nghĩa quan hệ giữa các models.

    Attributes:
        target_model: Tên model đích
        rel_type: Kiểu quan hệ (MANY_TO_ONE, ONE_TO_MANY, ...)
        foreign_key: Tên foreign key column
        back_ref: Tên back-reference property
        join_table: Tên join table (cho MANY_TO_MANY)
        cascade: Có cascade operations không
        lazy: Có lazy loading không
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        description: Mô tả quan hệ
    """
    target_model: str
    rel_type: RelationshipType
    foreign_key: str = ""
    back_ref: str = ""
    join_table: str = ""
    cascade: bool = False
    lazy: bool = False
    tenant_scoped: bool = True  # KPI-029: mặc định tenant_scoped
    description: str = ""

    def __post_init__(self) -> None:
        """Validate relationship sau khi khởi tạo."""
        # Target model không được để trống
        if not self.target_model or not self.target_model.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="relationship.target_model")
        # MANY_TO_MANY cần join_table
        if self.rel_type == RelationshipType.MANY_TO_MANY and not self.join_table:
            self.join_table = f"{self.__class__.__name__}_{self.target_model.lower()}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển relationship sang dict format."""
        return {
            "target_model": self.target_model,
            "rel_type": self.rel_type.value,
            "foreign_key": self.foreign_key,
            "back_ref": self.back_ref,
            "join_table": self.join_table,
            "cascade": self.cascade,
            "lazy": self.lazy,
            "tenant_scoped": self.tenant_scoped,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        """Tạo Relationship từ dict."""
        return cls(
            target_model=data.get("target_model", ""),
            rel_type=RelationshipType(data.get("rel_type", "many_to_one")),
            foreign_key=data.get("foreign_key", ""),
            back_ref=data.get("back_ref", ""),
            join_table=data.get("join_table", ""),
            cascade=data.get("cascade", False),
            lazy=data.get("lazy", False),
            tenant_scoped=data.get("tenant_scoped", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# IndexDef
# ===========================================================================


@dataclass
class IndexDef:
    """
    Định nghĩa index cho model.

    Attributes:
        name: Tên index
        columns: Danh sách columns trong index
        unique: Có unique constraint không
    """
    name: str
    columns: list[str] = field(default_factory=list)
    unique: bool = False

    def __post_init__(self) -> None:
        """Validate index sau khi khởi tạo."""
        # Tên index không được để trống
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="index.name")
        # Columns không được để trống
        if not self.columns:
            self.columns = []

    def to_dict(self) -> dict[str, Any]:
        """Chuyển index sang dict format."""
        return {
            "name": self.name,
            "columns": self.columns,
            "unique": self.unique,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexDef":
        """Tạo IndexDef từ dict."""
        return cls(
            name=data.get("name", ""),
            columns=data.get("columns", []),
            unique=data.get("unique", False),
        )


# ===========================================================================
# DataModel
# ===========================================================================


@dataclass
class DataModel:
    """
    Database model hoàn chỉnh.

    Bieu diễn một database table với đầy đủ thông tin:
    columns, relationships, indexes, và tenant isolation config.

    Attributes:
        id: Định danh duy nhất của model
        table_name: Tên bảng trong database
        description: Mô tả model (tiếng Việt)
        columns: Danh sách columns
        relationships: Danh sách relationships
        indexes: Danh sách indexes
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
    """
    id: str
    table_name: str
    description: str = ""
    columns: list[ColumnDef] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    indexes: list[IndexDef] = field(default_factory=list)
    tenant_isolated: bool = True  # KPI-029: mặc định tenant isolated

    def __post_init__(self) -> None:
        """Validate data model sau khi khởi tạo."""
        # ID không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="model.id")
        # Table name không được để trống
        if not self.table_name or not self.table_name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="model.table_name", model=self.id)
        # Kiểm tra duplicate column names
        if self._has_duplicate_columns():
            EM.raise_error(ErrorCode.CP08_DUPLICATE_COLUMN_NAME, model=self.id)
        # Kiểm tra missing primary key (nếu có columns)
        if self.columns and not self.get_primary_key():
            EM.raise_error(ErrorCode.CP08_MISSING_PRIMARY_KEY, model=self.id, table=self.table_name)

    def _has_duplicate_columns(self) -> bool:
        """Kiểm tra có duplicate column names không."""
        names = [c.name for c in self.columns]
        return len(names) != len(set(names))

    def has_tenant_column(self) -> bool:
        """
        Kiểm tra model có tenant column không.

        Returns:
            True nếu có column với tenant_aware=True
        """
        return any(col.tenant_aware for col in self.columns)

    def get_primary_key(self) -> Optional[ColumnDef]:
        """
        Lấy primary key column.

        Returns:
            Primary key column hoặc None
        """
        for col in self.columns:
            if col.primary_key:
                return col
        return None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển model sang dict format."""
        return {
            "id": self.id,
            "table_name": self.table_name,
            "description": self.description,
            "columns": [col.to_dict() for col in self.columns],
            "relationships": [rel.to_dict() for rel in self.relationships],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "tenant_isolated": self.tenant_isolated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataModel":
        """Tạo DataModel từ dict."""
        return cls(
            id=data.get("id", ""),
            table_name=data.get("table_name", ""),
            description=data.get("description", ""),
            columns=[ColumnDef.from_dict(c) for c in data.get("columns", [])],
            relationships=[Relationship.from_dict(r) for r in data.get("relationships", [])],
            indexes=[IndexDef.from_dict(i) for i in data.get("indexes", [])],
            tenant_isolated=data.get("tenant_isolated", True),
        )


# ===========================================================================
# DataModelCollection
# ===========================================================================


@dataclass
class DataModelCollection:
    """
    Collection chứa tất cả database models va datasources.

    Dùng làm output của DBParser và input cho Stack Emitters.

    Attributes:
        models: Danh sách DataModel
        datasources: Danh sách Datasource
    """
    models: list[DataModel] = field(default_factory=list)
    datasources: list[Datasource] = field(default_factory=list)

    def add_model(self, model: DataModel) -> None:
        """Thêm model vào collection."""
        # Kiểm tra duplicate table_name
        if self.get_by_table_name(model.table_name):
            EM.raise_error(ErrorCode.CP08_DUPLICATE_TABLE_NAME, table=model.table_name)
        self.models.append(model)

    def add_datasource(self, datasource: Datasource) -> None:
        """Thêm datasource vào collection."""
        self.datasources.append(datasource)

    @property
    def total_count(self) -> int:
        """Tổng số models trong collection."""
        return len(self.models)

    def get_by_id(self, model_id: str) -> Optional[DataModel]:
        """Tìm model theo ID."""
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def get_by_table_name(self, table_name: str) -> Optional[DataModel]:
        """Tìm model theo table_name."""
        for model in self.models:
            if model.table_name == table_name:
                return model
        return None

    def get_primary_datasource(self) -> Optional[Datasource]:
        """Lấy primary datasource (datasource đầu tiên hoặc có name='primary')."""
        for ds in self.datasources:
            if ds.name == "primary":
                return ds
        if self.datasources:
            return self.datasources[0]
        return None

    def tenant_isolated_models(self) -> list[DataModel]:
        """Loc các models có tenant isolation (KPI-029)."""
        return [m for m in self.models if m.tenant_isolated]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "datasources": [ds.to_dict() for ds in self.datasources],
            "models": [m.to_dict() for m in self.models],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataModelCollection":
        """Tạo DataModelCollection từ dict."""
        result = cls()
        result.datasources = [Datasource.from_dict(d) for d in data.get("datasources", [])]
        result.models = [DataModel.from_dict(m) for m in data.get("models", [])]
        return result