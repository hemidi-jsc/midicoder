"""
Command Models Module.

Module này định nghĩa các models cho Command DSL:
- Command: Định nghĩa command với input, output, guards, effects
- Field: Định nghĩa field trong input/output
- FieldType: Enum cho field types

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# FieldType Enum
# ============================================================================

class FieldType(Enum):
    """
    Enum cho các field types trong Command/Query.

    Types:
        STRING: String type (varchar)
        INTEGER: Integer type (int)
        FLOAT: Float type (float)
        BOOLEAN: Boolean type (bool)
        DATETIME: DateTime type (timestamp)
        TEXT: Text type (text)
        UUID: UUID type (uuid)
        JSON: JSON type (json/jsonb)
        DECIMAL: Decimal type (decimal)
        ENUM: Enum type (custom enum)
        LARGE_BINARY: Large binary type (blob)
        ARRAY: Array type (array)
        OBJECT: Object type (nested object)
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    UUID = "uuid"
    JSON = "json"
    DECIMAL = "decimal"
    ENUM = "enum"
    LARGE_BINARY = "large_binary"
    ARRAY = "array"
    OBJECT = "object"


# ============================================================================
# Field Model
# ============================================================================

@dataclass
class Field:
    """
    Field definition trong Command/Query input/output.

    Attributes:
        name: Tên field
        field_type: Loại dữ liệu (FieldType enum)
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả field
        nullable: Có thể null không
        unique: Có unique constraint không
        primary_key: Có phải primary key không
        index: Có index không
        server_default: Server default value
        length: Max length (cho string)
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        enum_values: Enum values (cho enum type)

    Example:
        >>> f = Field(
        ...     name="order_id",
        ...     field_type=FieldType.STRING,
        ...     required=True
        ... )
    """

    name: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    description: str = ""
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    index: bool = False
    server_default: str = ""
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    enum_values: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Field sang dictionary.

        Returns:
            Dictionary representation của Field
        """
        return {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "nullable": self.nullable,
            "unique": self.unique,
            "primary_key": self.primary_key,
            "index": self.index,
            "server_default": self.server_default,
            "length": self.length,
            "precision": self.precision,
            "scale": self.scale,
            "enum_values": self.enum_values,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Field":
        """
        Tạo Field từ dictionary.

        Args:
            data: Dictionary chứa field data

        Returns:
            Field instance
        """
        type_str = data.get("type", "string")
        field_type = FieldType(type_str) if isinstance(type_str, str) else type_str

        return cls(
            name=data.get("name", ""),
            field_type=field_type,
            required=bool(data.get("required", False)),
            default=data.get("default"),
            description=data.get("description", ""),
            nullable=bool(data.get("nullable", True)),
            unique=bool(data.get("unique", False)),
            primary_key=bool(data.get("primary_key", False)),
            index=bool(data.get("index", False)),
            server_default=data.get("server_default", ""),
            length=data.get("length"),
            precision=data.get("precision"),
            scale=data.get("scale"),
            enum_values=data.get("enum_values"),
        )


# ============================================================================
# Command Model
# ============================================================================

@dataclass
class Command:
    """
    Command definition trong DSL.

    Command đại diện cho một write operation trong hệ thống.
    Mỗi command có input, guards, effects, và errors.

    Attributes:
        id: Định danh duy nhất của command
        description: Mô tả command
        input: Danh sách input fields
        fetches: Danh sách entities cần load trước khi execute
        guards: Danh sách guards cần check
        effects: Danh sách effects sau khi execute
        errors: Danh sách errors có thể phát sinh
        returns: Danh sách return fields
        category: Phân loại command (create, update, delete, custom)
        emits: Danh sách events sẽ emit
        required_roles: Roles cần thiết để execute
        required_permissions: Permissions cần thiết
        writes_to: Danh sách entities sẽ được modify
        transaction: Có cần transaction không
        tenant_scope: Phạm vi multi-tenancy

    Example:
        >>> cmd = Command(
        ...     id="CreateOrder",
        ...     description="Tạo đơn hàng mới",
        ...     input=[Field(name="order_data", field_type=FieldType.OBJECT)],
        ...     writes_to=["Order", "OrderItem"],
        ...     category="create",
        ...     transaction=True
        ... )
    """

    id: str
    description: str = ""
    input: list[Field] = field(default_factory=list)
    fetches: list[str] = field(default_factory=list)
    guards: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    returns: list[Field] = field(default_factory=list)
    category: str = "custom"
    emits: list[str] = field(default_factory=list)
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    writes_to: list[str] = field(default_factory=list)
    transaction: bool = False
    tenant_scope: str = "global"

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Command sang dictionary.

        Returns:
            Dictionary representation của Command
        """
        return {
            "id": self.id,
            "description": self.description,
            "input": [f.to_dict() for f in self.input],
            "fetches": self.fetches,
            "guards": self.guards,
            "effects": self.effects,
            "errors": self.errors,
            "returns": [r.to_dict() for r in self.returns],
            "category": self.category,
            "emits": self.emits,
            "required_roles": self.required_roles,
            "required_permissions": self.required_permissions,
            "writes_to": self.writes_to,
            "transaction": self.transaction,
            "tenant_scope": self.tenant_scope,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Command":
        """
        Tạo Command từ dictionary.

        Args:
            data: Dictionary chứa command data

        Returns:
            Command instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            input=[Field.from_dict(f) for f in data.get("input", [])],
            fetches=data.get("fetches", []),
            guards=data.get("guards", []),
            effects=data.get("effects", []),
            errors=data.get("errors", []),
            returns=[Field.from_dict(r) for r in data.get("returns", [])],
            category=data.get("category", "custom"),
            emits=data.get("emits", []),
            required_roles=data.get("required_roles", []),
            required_permissions=data.get("required_permissions", []),
            writes_to=data.get("writes_to", []),
            transaction=bool(data.get("transaction", False)),
            tenant_scope=data.get("tenant_scope", "global"),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "FieldType",
    "Field",
    "Command",
]