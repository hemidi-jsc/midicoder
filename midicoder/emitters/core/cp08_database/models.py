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
    MONGODB = "mongodb"
    SQLITE = "sqlite"


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
    ARRAY = "array"
    BYTES = "bytes"
    TIME = "time"


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


# ===========================================================================
# Spatial Types
# ===========================================================================


class SpatialType(str, Enum):
    """
    Các loại spatial data được hỗ trợ.

    Basic:
        POINT: Một điểm (longitude, latitude)
        LINESTRING: Chuỗi điểm nối nhau thành đường
        POLYGON: Vùng kín được bao bởi linearring
        MULTIPOINT: Nhiều điểm
        MULTILINESTRING: Nhiều đường
        MULTIPOLYGON: Nhiều vùng

    Composite:
        GEOMETRY: Generic spatial (PostGIS geometry — projected CRS)
        GEOGRAPHY: Geographic coordinate (PostGIS geography — lon/lat on spheroid)
        GEOMETRYCOLLECTION: Tập hợp mixed spatial types
    """
    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTIPOINT = "multipoint"
    MULTILINESTRING = "multilinestring"
    MULTIPOLYGON = "multipolygon"
    GEOMETRY = "geometry"
    GEOGRAPHY = "geography"
    GEOMETRYCOLLECTION = "geometrycollection"


@dataclass
class SpatialColumn:
    """
    Column lưu trữ spatial data.

    Attributes:
        name: Tên column (vd: "location", "boundary")
        spatial_type: Loại spatial data (POINT, POLYGON, GEOMETRY, ...)
        srid: Spatial Reference System ID (mặc định: 4326 = WGS84)
        description: Mô tả column
    """
    name: str
    spatial_type: SpatialType
    srid: int = 4326
    description: str = ""

    def __post_init__(self) -> None:
        """Validate spatial column sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="spatial_column.name")
        if self.srid < 1:
            self.srid = 4326

    def to_dict(self) -> dict[str, Any]:
        """Chuyển spatial column sang dict format."""
        return {
            "name": self.name,
            "spatial_type": self.spatial_type.value,
            "srid": self.srid,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpatialColumn":
        """Tạo SpatialColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            spatial_type=SpatialType(data.get("spatial_type", "point")),
            srid=data.get("srid", 4326),
            description=data.get("description", ""),
        )


class SpatialIndexType(str, Enum):
    """
    Loại index cho spatial data.

    - gist: GiST index (mặc định cho PostGIS, hỗ trợ đa dạng operators)
    - spgist: SP-GiST index (tối ưu cho point data, equal/range queries)
    - gin: GIN index (hỗ trợ containment, intersection)
    - brin: BRIN index (mini bounding box, tối ưu cho large tables)
    """
    GIST = "gist"
    SPGIST = "spgist"
    GIN = "gin"
    BRIN = "brin"


@dataclass
class SpatialIndex:
    """
    Index cho spatial column — tối ưu queries như contains, intersects, distance.

    Attributes:
        name: Tên index
        column: Tên spatial column được index
        index_type: Loại spatial index (GIST, SPGIST, GIN, BRIN)
        description: Mô tả index
    """
    name: str
    column: str
    index_type: SpatialIndexType = SpatialIndexType.GIST
    description: str = ""

    def __post_init__(self) -> None:
        """Validate spatial index sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="spatial_index.name")
        if not self.column or not self.column.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="spatial_index.column")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển spatial index sang dict format."""
        return {
            "name": self.name,
            "column": self.column,
            "index_type": self.index_type.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpatialIndex":
        """Tạo SpatialIndex từ dict."""
        return cls(
            name=data.get("name", ""),
            column=data.get("column", ""),
            index_type=SpatialIndexType(data.get("index_type", "gist")),
            description=data.get("description", ""),
        )


# ===========================================================================
# Time-Series
# ===========================================================================


class TimeSeriesGranularity(str, Enum):
    """
    Mức độ granularity của time-series data.

    - second: Dữ liệu mỗi giây
    - minute: Dữ liệu mỗi phút
    - hour: Dữ liệu mỗi giờ
    - day: Dữ liệu mỗi ngày
    - week: Dữ liệu mỗi tuần
    - month: Dữ liệu mỗi tháng
    """
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class RetentionPolicyType(str, Enum):
    """
    Chiến lược retention cho time-series data.

    - time_based: Giữ data trong khoảng thời gian (vd: 90 ngày)
    - count_based: Giữ N bản ghi mới nhất (vd: 10000 records)
    - size_based: Giữ data dưới kích thước (vd: 10GB)
    - partition_based: Drop partition cũ nhất khi vượt threshold
    """
    TIME_BASED = "time_based"
    COUNT_BASED = "count_based"
    SIZE_BASED = "size_based"
    PARTITION_BASED = "partition_based"


@dataclass
class RetentionPolicy:
    """
    Chính sách lưu trữ data time-series — tự động dọn data cũ.

    Attributes:
        name: Tên policy (vd: "metrics_90d")
        policy_type: Loại retention (time_based, count_based, size_based, partition_based)
        threshold: Giá trị threshold (seconds, count, bytes, partitions)
        partition_interval: Interval phân chia partition (vd: "day", "week", "month")
        description: Mô tả policy
    """
    name: str
    policy_type: RetentionPolicyType
    threshold: int = 0
    partition_interval: str = "month"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate retention policy sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="retention_policy.name")
        if self.threshold < 0:
            self.threshold = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển retention policy sang dict format."""
        return {
            "name": self.name,
            "policy_type": self.policy_type.value,
            "threshold": self.threshold,
            "partition_interval": self.partition_interval,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetentionPolicy":
        """Tạo RetentionPolicy từ dict."""
        return cls(
            name=data.get("name", ""),
            policy_type=RetentionPolicyType(data.get("policy_type", "time_based")),
            threshold=data.get("threshold", 0),
            partition_interval=data.get("partition_interval", "month"),
            description=data.get("description", ""),
        )


@dataclass
class TimeSeriesModel:
    """
    Model tối ưu cho time-series data — metrics, logs, events.

    Hỗ trợ partitioning, compression, và retention policies.

    Attributes:
        id: Định danh duy nhất (vd: "cpu_metrics")
        table_name: Tên bảng (vd: "cpu_metrics")
        timestamp_column: Tên column lưu timestamp (vd: "recorded_at")
        grain_columns: Columns phân tách grain (vd: ["host", "cpu_id"])
        value_columns: Columns lưu giá trị (vd: ["usage_percent", "idle"])
        granularity: Mức độ granularity của data
        retention_policy: Policy tự động dọn data cũ
        partition_interval: Interval phân chia partition (vd: "week")
        description: Mô tả model
    """
    id: str
    table_name: str
    timestamp_column: str
    grain_columns: list[str] = field(default_factory=list)
    value_columns: list[str] = field(default_factory=list)
    granularity: TimeSeriesGranularity = TimeSeriesGranularity.MINUTE
    retention_policy: RetentionPolicy | None = None
    partition_interval: str = "week"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate time-series model sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="time_series.id")
        if not self.table_name or not self.table_name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="time_series.table_name")
        if not self.timestamp_column or not self.timestamp_column.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="time_series.timestamp_column")
        if not self.value_columns:
            self.value_columns = []
        if not self.grain_columns:
            self.grain_columns = []

    def to_dict(self) -> dict[str, Any]:
        """Chuyển time-series model sang dict format."""
        return {
            "id": self.id,
            "table_name": self.table_name,
            "timestamp_column": self.timestamp_column,
            "grain_columns": self.grain_columns,
            "value_columns": self.value_columns,
            "granularity": self.granularity.value,
            "retention_policy": self.retention_policy.to_dict() if self.retention_policy else None,
            "partition_interval": self.partition_interval,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeSeriesModel":
        """Tạo TimeSeriesModel từ dict."""
        rp_data = data.get("retention_policy")
        return cls(
            id=data.get("id", ""),
            table_name=data.get("table_name", ""),
            timestamp_column=data.get("timestamp_column", ""),
            grain_columns=data.get("grain_columns", []),
            value_columns=data.get("value_columns", []),
            granularity=TimeSeriesGranularity(data.get("granularity", "minute")),
            retention_policy=RetentionPolicy.from_dict(rp_data) if rp_data else None,
            partition_interval=data.get("partition_interval", "week"),
            description=data.get("description", ""),
        )


# ===========================================================================
# CQRS Read Models
# ===========================================================================


class ReadModelSource(str, Enum):
    """
    Nguồn dữ liệu cho read model.

    - materialized_view: View được compute trước và cache
    - denormalized_table: Bảng đã được flatten, optimized cho read
    - search_index: Index ngoài (Elasticsearch, Meilisearch, ...)
    - cached_computation: Cache kết quả tính toán
    """
    MATERIALIZED_VIEW = "materialized_view"
    DENORMALIZED_TABLE = "denormalized_table"
    SEARCH_INDEX = "search_index"
    CACHED_COMPUTATION = "cached_computation"


class RefreshStrategy(str, Enum):
    """
    Chiến lược refresh read model.

    - real_time: Refresh ngay khi write model thay đổi
    - batch: Refresh theo batch ở intervals cố định
    - lazy: Refresh khi được query lần đầu (cache-aside)
    - event_driven: Refresh khi nhận được domain event
    """
    REAL_TIME = "real_time"
    BATCH = "batch"
    LAZY = "lazy"
    EVENT_DRIVEN = "event_driven"


@dataclass
class ReadModel:
    """
    CQRS read model — bản chiếu của write model, tối ưu cho query.

    Read model được populate từ write model và chỉ dùng cho read operations.

    Attributes:
        id: Định danh duy nhất (vd: "order_summary_view")
        table_name: Tên bảng/view (vd: "order_summary_view")
        source: Nguồn dữ liệu (materialized_view, denormalized_table, ...)
        source_models: Các DataModel nguồn cung cấp data cho read model
        columns: Columns trong read model
        refresh_strategy: Chiến lược refresh (real_time, batch, lazy, event_driven)
        refresh_interval_seconds: Interval refresh (cho batch strategy)
        description: Mô tả read model
    """
    id: str
    table_name: str
    source: ReadModelSource
    source_models: list[str] = field(default_factory=list)
    columns: list[ColumnDef] = field(default_factory=list)
    refresh_strategy: RefreshStrategy = RefreshStrategy.EVENT_DRIVEN
    refresh_interval_seconds: int = 300
    description: str = ""

    def __post_init__(self) -> None:
        """Validate read model sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="read_model.id")
        if not self.table_name or not self.table_name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="read_model.table_name")
        if not self.source_models:
            self.source_models = []

    def to_dict(self) -> dict[str, Any]:
        """Chuyển read model sang dict format."""
        return {
            "id": self.id,
            "table_name": self.table_name,
            "source": self.source.value,
            "source_models": self.source_models,
            "columns": [col.to_dict() for col in self.columns],
            "refresh_strategy": self.refresh_strategy.value,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReadModel":
        """Tạo ReadModel từ dict."""
        return cls(
            id=data.get("id", ""),
            table_name=data.get("table_name", ""),
            source=ReadModelSource(data.get("source", "materialized_view")),
            source_models=data.get("source_models", []),
            columns=[ColumnDef.from_dict(c) for c in data.get("columns", [])],
            refresh_strategy=RefreshStrategy(data.get("refresh_strategy", "event_driven")),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 300),
            description=data.get("description", ""),
        )


# ===========================================================================
# Distributed Transactions
# ===========================================================================


class DistributedTxProtocol(str, Enum):
    """
    Protocol cho distributed transaction.

    - two_phase_commit: 2PC classical (prepare → commit/abort)
    - saga: Choreographed/orchestrated saga với compensating actions
    - outbox: Transactional outbox pattern (event + DB trong same tx)
    - tcc: Try-Confirm-Cancel (3-phase compensation)
    """
    TWO_PHASE_COMMIT = "two_phase_commit"
    SAGA = "saga"
    OUTBOX = "outbox"
    TCC = "tcc"


class ParticipantStatus(str, Enum):
    """Trạng thái của participant trong distributed transaction."""
    PREPARED = "prepared"
    COMMITTED = "committed"
    ABORTED = "aborted"
    TIMEOUT = "timeout"
    COMPENSATED = "compensated"


@dataclass
class TransactionParticipant:
    """
    Participant trong distributed transaction — 1 datasource tham gia.

    Attributes:
        datasource_name: Tên datasource tham gia (phải match với Datasource.name)
        role: Vai trò (coordinator, participant, observer)
        timeout_seconds: Timeout cho participant này
        can_compensate: Có thể rollback/compensate không
        description: Mô tả participant
    """
    datasource_name: str
    role: str = "participant"
    timeout_seconds: int = 30
    can_compensate: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate participant sau khi khởi tạo."""
        if not self.datasource_name or not self.datasource_name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="transaction_participant.datasource_name")
        if self.timeout_seconds < 1:
            self.timeout_seconds = 30

    def to_dict(self) -> dict[str, Any]:
        """Chuyển participant sang dict format."""
        return {
            "datasource_name": self.datasource_name,
            "role": self.role,
            "timeout_seconds": self.timeout_seconds,
            "can_compensate": self.can_compensate,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransactionParticipant":
        """Tạo TransactionParticipant từ dict."""
        return cls(
            datasource_name=data.get("datasource_name", ""),
            role=data.get("role", "participant"),
            timeout_seconds=data.get("timeout_seconds", 30),
            can_compensate=data.get("can_compensate", True),
            description=data.get("description", ""),
        )


@dataclass
class DistributedTransaction:
    """
    Distributed transaction spanning multiple datasources.

    Đảm bảo consistency khi 1 operation cần modify data ở nhiều datasource.

    Attributes:
        id: Định danh duy nhất (vd: "order_payment_tx")
        protocol: Protocol distributed tx (two_phase_commit, saga, outbox, tcc)
        coordinator_datasource: Datasource đóng vai trò coordinator
        participants: Danh sách participants
        timeout_seconds: Timeout tối đa cho toàn bộ tx
        retry_count: Số lần retry khi prepare/commit thất bại
        description: Mô tả transaction
    """
    id: str
    protocol: DistributedTxProtocol
    coordinator_datasource: str
    participants: list[TransactionParticipant] = field(default_factory=list)
    timeout_seconds: int = 60
    retry_count: int = 3
    description: str = ""

    def __post_init__(self) -> None:
        """Validate distributed transaction sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="distributed_tx.id")
        if not self.coordinator_datasource or not self.coordinator_datasource.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="distributed_tx.coordinator_datasource")
        if self.timeout_seconds < 1:
            self.timeout_seconds = 60
        if self.retry_count < 0:
            self.retry_count = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển distributed transaction sang dict format."""
        return {
            "id": self.id,
            "protocol": self.protocol.value,
            "coordinator_datasource": self.coordinator_datasource,
            "participants": [p.to_dict() for p in self.participants],
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DistributedTransaction":
        """Tạo DistributedTransaction từ dict."""
        return cls(
            id=data.get("id", ""),
            protocol=DistributedTxProtocol(data.get("protocol", "saga")),
            coordinator_datasource=data.get("coordinator_datasource", ""),
            participants=[TransactionParticipant.from_dict(p) for p in data.get("participants", [])],
            timeout_seconds=data.get("timeout_seconds", 60),
            retry_count=data.get("retry_count", 3),
            description=data.get("description", ""),
        )


# ===========================================================================
# JSONB Operations
# ===========================================================================


class JSONBIndexType(str, Enum):
    """
    Loại index cho JSONB column.

    - gin: GIN index (mặc định, hỗ trợ @>, ?, ?|, ?&, jsonb_path_ops)
    - gin_path_ops: GIN với jsonb_path_ops (nhỏ hơn, ít operators)
    - gin_nulls_pruned: GIN bỏ qua null values (PostgreSQL 13+)
    - btree: B-tree trên expression extracted từ JSONB
    """
    GIN = "gin"
    GIN_PATH_OPS = "gin_path_ops"
    GIN_NULLS_PRUNED = "gin_nulls_pruned"
    BTREE = "btree"


@dataclass
class JSONBIndex:
    """
    Index cho JSONB column — tối ưu queries trên nested JSON data.

    Attributes:
        name: Tên index (vd: "idx_order_data_customer")
        column: Tên JSONB column (vd: "data")
        index_type: Loại JSONB index (GIN, gin_path_ops, ...)
        path: JSON path expression (vd: "{customer,name}") — để trống = toàn bộ document
        description: Mô tả index
    """
    name: str
    column: str
    index_type: JSONBIndexType = JSONBIndexType.GIN
    path: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate JSONB index sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="jsonb_index.name")
        if not self.column or not self.column.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="jsonb_index.column")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển JSONB index sang dict format."""
        return {
            "name": self.name,
            "column": self.column,
            "index_type": self.index_type.value,
            "path": self.path,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JSONBIndex":
        """Tạo JSONBIndex từ dict."""
        return cls(
            name=data.get("name", ""),
            column=data.get("column", ""),
            index_type=JSONBIndexType(data.get("index_type", "gin")),
            path=data.get("path", ""),
            description=data.get("description", ""),
        )


class JSONBValidationMode(str, Enum):
    """
    Chế độ validation cho JSONB column.

    - schema: Validate against JSON Schema
    - check_constraint: Check constraint trên JSON path
    - none: Không validate
    """
    SCHEMA = "schema"
    CHECK_CONSTRAINT = "check_constraint"
    NONE = "none"


@dataclass
class JSONBColumn:
    """
    Column lưu trữ JSONB data với validation và indexing.

    JSONB (binary JSON) tối ưu hơn JSON text — hỗ trợ indexing, operators, containment.

    Attributes:
        name: Tên column (vd: "metadata", "attributes", "data")
        validation_mode: Chế độ validation (schema, check_constraint, none)
        json_schema: JSON Schema string để validate data
        check_expression: Check constraint expression (vd: "data->>'status' IN ('active','pending')")
        jsonb_indexes: Danh sách JSONB indexes
        default: Giá trị mặc định (JSON string, vd: "{}" hoặc "[]")
        required: Có bắt buộc không
        description: Mô tả column
    """
    name: str
    validation_mode: JSONBValidationMode = JSONBValidationMode.NONE
    json_schema: str = ""
    check_expression: str = ""
    jsonb_indexes: list[JSONBIndex] = field(default_factory=list)
    default: str = "{}"
    required: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate JSONB column sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP08_EMPTY_NAME, field="jsonb_column.name")
        if self.validation_mode == JSONBValidationMode.SCHEMA and not self.json_schema:
            self.json_schema = "{}"
        if self.validation_mode == JSONBValidationMode.CHECK_CONSTRAINT and not self.check_expression:
            self.check_expression = "true"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển JSONB column sang dict format."""
        return {
            "name": self.name,
            "validation_mode": self.validation_mode.value,
            "json_schema": self.json_schema,
            "check_expression": self.check_expression,
            "jsonb_indexes": [idx.to_dict() for idx in self.jsonb_indexes],
            "default": self.default,
            "required": self.required,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JSONBColumn":
        """Tạo JSONBColumn từ dict."""
        return cls(
            name=data.get("name", ""),
            validation_mode=JSONBValidationMode(data.get("validation_mode", "none")),
            json_schema=data.get("json_schema", ""),
            check_expression=data.get("check_expression", ""),
            jsonb_indexes=[JSONBIndex.from_dict(i) for i in data.get("jsonb_indexes", [])],
            default=data.get("default", "{}"),
            required=data.get("required", False),
            description=data.get("description", ""),
        )