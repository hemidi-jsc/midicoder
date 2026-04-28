"""
Mô-đun models cho Entity Emitter.

Cung cấp các dataclass để đại diện:
- Entity: Thực thể domain (User, Order, Product, etc.)
- Field: Trường của entity (id, email, status, etc.)
- Relationship: Quan hệ giữa entities (one-to-one, one-to-many, etc.)
- Constraint: Ràng buộc (unique, check, etc.)
- Index: Index cho fields
- LifecycleHook: Lifecycle event hooks

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FieldType(str, Enum):
    """
    Các loại field được hỗ trợ cho Entity.
    
    Mapping sang SQLAlchemy:
    - string → String
    - integer → Integer
    - float → Float
    - boolean → Boolean
    - datetime → DateTime
    - text → Text
    - uuid → UUID
    - json → JSON
    - decimal → Decimal
    - enum → Enum
    - largebinary → LargeBinary
    - array → ARRAY
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
    LARGE_BINARY = "largebinary"
    ARRAY = "array"


class RelationshipType(str, Enum):
    """
    Các loại relationship được hỗ trợ.
    
    - one-to-one: Mỗi thực thể quan hệ với nhiều nhất 1 thực thể khác
    - one-to-many: Một thực thể quan hệ với nhiều thực thể khác
    - many-to-many: Quan hệ nhiều-nhiều qua bảng trung gian
    - self-referencing: Entity quan hệ với chính nó
    - polymorphic: Relationship có thể trỏ đến multiple types
    """
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_MANY = "many-to-many"
    SELF_REFERENCING = "self-referencing"
    POLYMORPHIC = "polymorphic"


class ConstraintType(str, Enum):
    """
    Các loại constraint được hỗ trợ.
    
    - unique: Unique constraint
    - check: Check constraint
    - foreign_key: Foreign key constraint
    """
    UNIQUE = "unique"
    CHECK = "check"
    FOREIGN_KEY = "foreign_key"


class LifecycleEvent(str, Enum):
    """
    Các lifecycle events được hỗ trợ.
    
    SQLAlchemy event listeners:
    - before_insert: Trước khi insert
    - after_insert: Sau khi insert
    - before_update: Trước khi update
    - after_update: Sau khi update
    - before_delete: Trước khi delete
    - after_delete: Sau khi delete
    """
    BEFORE_INSERT = "before_insert"
    AFTER_INSERT = "after_insert"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"


@dataclass
class Field:
    """
    Đại diện cho một field của Entity.
    
    Attributes:
        name: Tên field (snake_case)
        field_type: Loại field (FieldType enum)
        nullable: Có cho phép null không (default: True)
        unique: Có unique không (default: False)
        primary_key: Có phải primary key không (default: False)
        index: Có tạo index không (default: False)
        default: Giá trị mặc định
        server_default: Server default expression
        length: Độ dài (cho string)
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        enum_values: Danh sách enum values (cho enum type)
        description: Mô tả field
    
    Ví dụ:
        >>> field = Field(
        ...     name="email",
        ...     field_type=FieldType.STRING,
        ...     nullable=False,
        ...     unique=True,
        ...     length=255,
        ... )
    """
    name: str
    field_type: FieldType
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    index: bool = False
    default: Any = None
    server_default: str | None = None
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    enum_values: list[str] | None = None
    description: str | None = None


@dataclass
class Relationship:
    """
    Đại diện cho một relationship giữa entities.
    
    Attributes:
        rel_type: Loại relationship
        target: Tên entity target
        local_field: Field name ở local entity (foreign key field)
        foreign_field: Field name ở target entity
        back_populates: Back-reference field name
        cascade: Cascade options (ví dụ: "all, delete-orphan")
        secondary: Secondary table name (cho many-to-many)
        polymorphic: Có phải polymorphic relationship không
        description: Mô tả relationship
    
    Ví dụ:
        >>> rel = Relationship(
        ...     rel_type=RelationshipType.ONE_TO_MANY,
        ...     target="Order",
        ...     back_populates="user",
        ...     cascade="all, delete-orphan",
        ... )
    """
    rel_type: RelationshipType
    target: str
    local_field: str | None = None
    foreign_field: str | None = None
    back_populates: str | None = None
    cascade: str | None = None
    secondary: str | None = None
    polymorphic: bool = False
    description: str | None = None


@dataclass
class Constraint:
    """
    Đại diện cho một constraint của Entity.
    
    Attributes:
        constraint_type: Loại constraint
        name: Tên constraint (cho check constraint)
        fields: Danh sách fields (cho unique constraint)
        condition: Condition expression (cho check constraint)
        description: Mô tả constraint
    
    Ví dụ:
        >>> constraint = Constraint(
        ...     constraint_type=ConstraintType.CHECK,
        ...     name="check_balance_non_negative",
        ...     condition="balance >= 0",
        ... )
    """
    constraint_type: ConstraintType
    name: str | None = None
    fields: list[str] | None = None
    condition: str | None = None
    description: str | None = None


@dataclass
class Index:
    """
    Đại diện cho một index của Entity.
    
    Attributes:
        name: Tên index
        fields: Danh sách fields
        unique: Có phải unique index không
    
    Ví dụ:
        >>> index = Index(
        ...     name="idx_user_status_created",
        ...     fields=["status", "created_at"],
        ...     unique=False,
        ... )
    """
    name: str | None = None
    fields: list[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class LifecycleHook:
    """
    Đại diện cho một lifecycle hook.
    
    Attributes:
        event: Lifecycle event (before_insert, after_insert, etc.)
        hook_name: Tên hook function
        params: Parameters cho hook
    
    Ví dụ:
        >>> hook = LifecycleHook(
        ...     event=LifecycleEvent.BEFORE_INSERT,
        ...     hook_name="set_default_tenant",
        ...     params={"field": "tenant_id"},
        ... )
    """
    event: LifecycleEvent
    hook_name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """
    Đại diện cho một Entity trong domain model.
    
    Attributes:
        id: Entity ID (PascalCase, ví dụ: "User")
        description: Mô tả entity
        fields: Danh sách fields
        relationships: Danh sách relationships
        constraints: Danh sách constraints
        indexes: Danh sách indexes
        lifecycle_hooks: Danh sách lifecycle hooks
    
    Ví dụ:
        >>> entity = Entity(
        ...     id="User",
        ...     description="User entity",
        ...     fields=[
        ...         Field(name="id", field_type=FieldType.UUID, primary_key=True),
        ...         Field(name="email", field_type=FieldType.STRING, unique=True),
        ...     ],
        ...     relationships=[
        ...         Relationship(
        ...             rel_type=RelationshipType.ONE_TO_MANY,
        ...             target="Order",
        ...             back_populates="user",
        ...         ),
        ...     ],
        ... )
    """
    id: str
    description: str | None = None
    fields: list[Field] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)
    lifecycle_hooks: list[LifecycleHook] = field(default_factory=list)