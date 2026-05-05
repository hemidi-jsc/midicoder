# coding: utf-8
"""
Mô-đun models cho Database Emitter (CP08).

Định nghĩa các dataclass biểu diễn:
- ColumnType/RelationshipType: Enum các kiểu dữ liệu và quan hệ
- ColumnDef: Định nghĩa column với type, constraints, tenant_aware
- Relationship: Quan hệ giữa các models (FK, back_ref, cascade)
- IndexDef: Định nghĩa index
- DataModel: Model hoàn chỉnh với columns, relationships, indexes
- DataModelCollection: Collection chứa tất cả models

KPI-029: Tenant Isolation - tenant_isolated=True mặc định, tenant_scoped=True cho relationships

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# Enums
# ===========================================================================


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

    Biểu diễn một database table với đầy đủ thông tin:
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
    Collection chứa tất cả database models.

    Dùng làm output của DBParser và input cho Stack Emitters.

    Attributes:
        models: Danh sách DataModel
    """
    models: list[DataModel] = field(default_factory=list)

    def add_model(self, model: DataModel) -> None:
        """Thêm model vào collection."""
        self.models.append(model)

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

    def tenant_isolated_models(self) -> list[DataModel]:
        """Lọc các models có tenant isolation (KPI-029)."""
        return [m for m in self.models if m.tenant_isolated]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "models": [m.to_dict() for m in self.models],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataModelCollection":
        """Tạo DataModelCollection từ dict."""
        result = cls()
        result.models = [DataModel.from_dict(m) for m in data.get("models", [])]
        return result