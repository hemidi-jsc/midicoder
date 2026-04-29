"""
Value Object Models Module.

Module này định nghĩa các models cho Value Object DSL:
- ValueObject: Định nghĩa VO với fields
- VOField: Định nghĩa field trong VO
- VOFieldType: Enum cho VO field types

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# VOFieldType Enum
# ============================================================================

class VOFieldType(Enum):
    """
    Enum cho các field types trong Value Object.

    Types:
        STRING: String type
        INTEGER: Integer type
        FLOAT: Float type
        BOOLEAN: Boolean type
        DATETIME: DateTime type
        TEXT: Text type
        UUID: UUID type
        JSON: JSON type
        DECIMAL: Decimal type
        ENUM: Enum type

    Note: Value Objects thường không cần LARGE_BINARY, ARRAY, OBJECT
    vì chúng là primitive/immutable values.
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


# ============================================================================
# VOField Model
# ============================================================================

@dataclass
class VOField:
    """
    Field definition trong Value Object.

    Attributes:
        name: Tên field
        field_type: Loại dữ liệu (VOFieldType enum)
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả field
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        min_length: Min length (cho string)
        max_length: Max length (cho string)
        pattern: Regex pattern (cho string)
        enum_values: Enum values (cho enum type)

    Example:
        >>> f = VOField(
        ...     name="amount",
        ...     field_type=VOFieldType.DECIMAL,
        ...     precision=10,
        ...     scale=2,
        ...     required=True
        ... )
    """

    name: str
    field_type: VOFieldType
    required: bool = False
    default: Any = None
    description: str = ""
    precision: int | None = None
    scale: int | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển VOField sang dictionary.

        Returns:
            Dictionary representation của VOField
        """
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
        }

        # Add optional fields only if set
        if self.default is not None:
            result["default"] = self.default
        if self.description:
            result["description"] = self.description
        if self.precision is not None:
            result["precision"] = self.precision
        if self.scale is not None:
            result["scale"] = self.scale
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.enum_values is not None:
            result["enum_values"] = self.enum_values

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VOField":
        """
        Tạo VOField từ dictionary.

        Args:
            data: Dictionary chứa field data

        Returns:
            VOField instance
        """
        type_str = data.get("type", "string")
        field_type = VOFieldType(type_str) if isinstance(type_str, str) else type_str

        return cls(
            name=data.get("name", ""),
            field_type=field_type,
            required=bool(data.get("required", False)),
            default=data.get("default"),
            description=data.get("description", ""),
            precision=data.get("precision"),
            scale=data.get("scale"),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            pattern=data.get("pattern"),
            enum_values=data.get("enum_values"),
        )


# ============================================================================
# ValueObject Model
# ============================================================================

@dataclass
class ValueObject:
    """
    Value Object definition trong DSL.

    Value Object là immutable object đại diện cho một concept domain
    với identity dựa trên attributes thay vì ID.

    Attributes:
        id: Định danh duy nhất của VO
        description: Mô tả VO
        fields: Danh sách fields
        immutable: Có bất biến không (default: False)
        comparable: Có thể so sánh không (default: False)
        extends: Parent VO ID (cho inheritance)

    Example:
        >>> vo = ValueObject(
        ...     id="Money",
        ...     description="Giá tiền với currency",
        ...     fields=[
        ...         VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
        ...         VOField(name="currency", field_type=VOFieldType.STRING, required=True)
        ...     ],
        ...     immutable=True
        ... )
    """

    id: str
    description: str = ""
    fields: list[VOField] = field(default_factory=list)
    immutable: bool = False
    comparable: bool = False
    extends: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển ValueObject sang dictionary.

        Returns:
            Dictionary representation của ValueObject
        """
        result: dict[str, Any] = {
            "id": self.id,
            "fields": [f.to_dict() for f in self.fields],
            "immutable": self.immutable,
            "comparable": self.comparable,
        }

        # Add optional fields only if set
        if self.description:
            result["description"] = self.description
        if self.extends is not None:
            result["extends"] = self.extends

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValueObject":
        """
        Tạo ValueObject từ dictionary.

        Args:
            data: Dictionary chứa VO data

        Returns:
            ValueObject instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            fields=[VOField.from_dict(f) for f in data.get("fields", [])],
            immutable=bool(data.get("immutable", False)),
            comparable=bool(data.get("comparable", False)),
            extends=data.get("extends"),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "VOFieldType",
    "VOField",
    "ValueObject",
]