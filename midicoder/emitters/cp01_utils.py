"""
Mô-đun utilities cho CP01 Entity Model Emitter.

Cung cấp:
- Field type mapping (field type → SQLAlchemy type)
- Relationship helpers
- Lifecycle event validation
- Constraint helpers

Sử dụng:
    from midicoder.emitters.cp01_utils import (
        get_sqlalchemy_type,
        get_python_type,
        validate_relationship,
        get_relationship_options,
    )
    
    # Map field type sang SQLAlchemy type
    sa_type = get_sqlalchemy_type("uuid")  # UUID(as_uuid=True)
    py_type = get_python_type("uuid")  # UUID
    
    # Validate relationship
    validate_relationship({"type": "one-to-many", "target": "OrderItem"})

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    Index,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    UUID as SQLUUID,
    text,
)
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import Mapped, relationship

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Field Type Constants
# ============================================================================

# Định nghĩa tất cả field types được hỗ trợ
SUPPORTED_FIELD_TYPES = {
    "string",
    "integer",
    "float",
    "boolean",
    "datetime",
    "text",
    "uuid",
    "json",
    "enum",
    "decimal",
    "largebinary",
    "array",
}

# Mapping từ field type sang SQLAlchemy type
SQLALCHEMY_TYPE_MAP = {
    "string": String,
    "integer": Integer,
    "float": Float,
    "boolean": Boolean,
    "datetime": DateTime,
    "text": Text,
    "uuid": SQLUUID,
    "json": JSON,
    "enum": SQLEnum,
    "decimal": DECIMAL,
    "largebinary": LargeBinary,
    "array": ARRAY,
}

# Mapping từ field type sang Python type
PYTHON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "datetime": "datetime",  # String reference
    "text": str,
    "uuid": UUID,
    "json": "dict | list",  # String reference
    "enum": "Enum",  # String reference
    "decimal": Decimal,
    "largebinary": bytes,
    "array": "list",  # String reference
}

# Giá trị mặc định cho field types
DEFAULT_TYPE_CONFIGS = {
    "string": {"length": 255},
    "integer": {},
    "float": {},
    "boolean": {"default": False},
    "datetime": {},
    "text": {},
    "uuid": {"as_uuid": True},
    "json": {},
    "decimal": {"precision": 10, "scale": 2},
    "largebinary": {},
    "array": {},
}


# ============================================================================
# Lifecycle Event Constants
# ============================================================================

# Danh sách lifecycle events được hỗ trợ
VALID_LIFECYCLE_EVENTS = {
    "before_insert",
    "after_insert",
    "before_update",
    "after_update",
    "before_delete",
    "after_delete",
}


# ============================================================================
# Relationship Types
# ============================================================================

# Định nghĩa relationship types
SUPPORTED_RELATIONSHIP_TYPES = {
    "one-to-one",
    "one-to-many",
    "many-to-many",
}


# ============================================================================
# Type Mapping Functions
# ============================================================================

def get_sqlalchemy_type(
    field_type: str,
    field_config: dict[str, Any] | None = None,
) -> Any:
    """
    Lấy SQLAlchemy type từ field type name.
    
    Args:
        field_type: Tên field type (ví dụ: "string", "uuid")
        field_config: Config cho field (precision, scale, length, etc.)
        
    Returns:
        SQLAlchemy type instance
        
    Raises:
        MidicoderError: Nếu field_type không được hỗ trợ
        
    Ví dụ:
        >>> get_sqlalchemy_type("string")
        String(255)
        >>> get_sqlalchemy_type("uuid")
        UUID(as_uuid=True)
        >>> get_sqlalchemy_type("decimal", {"precision": 12, "scale": 4})
        Decimal(12, 4)
    """
    field_type = field_type.lower()
    
    if field_type not in SUPPORTED_FIELD_TYPES:
        EM.raise_error(
            ErrorCode.CP01_INVALID_FIELD_TYPE,
            field_type=field_type,
            supported_types=list(SUPPORTED_FIELD_TYPES),
        )
    
    config = field_config or {}
    default_config = DEFAULT_TYPE_CONFIGS.get(field_type, {})
    merged_config = {**default_config, **config}
    
    try:
        type_class = SQLALCHEMY_TYPE_MAP[field_type]
        
        # Handle special cases
        if field_type == "string":
            length = merged_config.get("length", 255)
            return String(length)
            
        elif field_type == "uuid":
            return SQLUUID(as_uuid=True)
            
        elif field_type == "decimal":
            precision = merged_config.get("precision", 10)
            scale = merged_config.get("scale", 2)
            return DECIMAL(precision, scale)
            
        elif field_type == "enum":
            enum_class = config.get("enum_class")
            if not enum_class:
                EM.raise_error(
                    ErrorCode.CP01_INVALID_FIELD_TYPE,
                    field_type=field_type,
                    reason="enum_class is required for enum type",
                )
            return SQLEnum(enum_class)
            
        elif field_type == "array":
            # Default to String array
            item_type = config.get("item_type", "string")
            item_sqla_type = get_sqlalchemy_type(item_type)
            return ARRAY(item_sqla_type)
            
        else:
            # Generic case
            return type_class()
            
    except Exception as e:
        EM.raise_error(
            ErrorCode.CP01_INVALID_FIELD_TYPE,
            field_type=field_type,
            error=str(e),
        )


def get_python_type(field_type: str) -> str:
    """
    Lấy Python type annotation string từ field type.
    
    Args:
        field_type: Tên field type
        
    Returns:
        Python type annotation string
        
    Ví dụ:
        >>> get_python_type("uuid")
        "UUID"
        >>> get_python_type("datetime")
        "datetime"
    """
    field_type = field_type.lower()
    
    if field_type not in PYTHON_TYPE_MAP:
        return "Any"
        
    return PYTHON_TYPE_MAP[field_type]


def get_field_imports(fields: list[dict[str, Any]]) -> set[str]:
    """
    Lấy danh sách imports cần thiết cho các fields.
    
    Args:
        fields: Danh sách field definitions
        
    Returns:
        Set của import statements
        
    Ví dụ:
        >>> get_field_imports([{"type": "uuid"}, {"type": "datetime"}])
        {"from uuid import UUID", "from datetime import datetime"}
    """
    imports = set()
    
    for field in fields:
        field_type = field.get("type", "string").lower()
        
        if field_type == "uuid":
            imports.add("from uuid import UUID")
        elif field_type == "datetime":
            imports.add("from datetime import datetime")
        elif field_type == "decimal":
            imports.add("from decimal import Decimal")
        elif field_type == "json":
            imports.add("from typing import Any")
        elif field_type == "array":
            imports.add("from typing import List")
        elif field_type == "enum":
            enum_class = field.get("enum_class")
            if enum_class:
                imports.add(f"from enum import Enum")
                
    return imports


# ============================================================================
# Relationship Helpers
# ============================================================================

@dataclass
class RelationshipConfig:
    """
    Cấu hình cho relationship.
    
    Attributes:
        rel_type: Loại relationship (one-to-one, one-to-many, many-to-many)
        target: Tên entity target
        local_field: Field name ở local entity
        foreign_field: Field name ở target entity
        back_populates: Back-reference field name
        cascade: Cascade options (ví dụ: "all, delete-orphan")
        secondary: Secondary table name (cho many-to-many)
    """
    rel_type: str
    target: str
    local_field: str
    foreign_field: str
    back_populates: str
    cascade: str = ""
    secondary: str = ""


def validate_relationship(rel_config: dict[str, Any]) -> None:
    """
    Validate relationship configuration.
    
    Args:
        rel_config: Relationship config dict
        
    Raises:
        MidicoderError: Nếu config không hợp lệ
    """
    rel_type = rel_config.get("type", "").lower()
    
    if rel_type not in SUPPORTED_RELATIONSHIP_TYPES:
        EM.raise_error(
            ErrorCode.CP01_RELATIONSHIP_TARGET_NOT_FOUND,
            rel_type=rel_type,
            supported_types=list(SUPPORTED_RELATIONSHIP_TYPES),
        )
        
    # Check required fields
    required_fields = ["type", "target", "back_populates"]
    for field in required_fields:
        if field not in rel_config:
            EM.raise_error(
                ErrorCode.CP01_RELATIONSHIP_TARGET_NOT_FOUND,
                missing_field=field,
            )
            
    # Check many-to-many requires secondary table
    if rel_type == "many-to-many" and not rel_config.get("secondary"):
        EM.raise_error(
            ErrorCode.CP01_RELATIONSHIP_TARGET_NOT_FOUND,
            rel_type=rel_type,
            reason="secondary table required for many-to-many",
        )


def get_relationship_options(rel_config: dict[str, Any]) -> dict[str, Any]:
    """
    Lấy SQLAlchemy relationship options từ config.
    
    Args:
        rel_config: Relationship config dict
        
    Returns:
        Dict của relationship options
        
    Ví dụ:
        >>> get_relationship_options({"type": "one-to-one", "target": "Profile"})
        {"uselist": False}
        >>> get_relationship_options({"type": "one-to-many", "target": "OrderItem"})
        {"uselist": True}
        >>> get_relationship_options({
        ...     "type": "many-to-many", 
        ...     "target": "Category",
        ...     "secondary": "product_categories"
        ... })
        {"secondary": "product_categories"}
    """
    rel_type = rel_config.get("type", "").lower()
    options: dict[str, Any] = {}
    
    # Set uselist based on relationship type
    if rel_type == "one-to-one":
        options["uselist"] = False
    else:  # one-to-many, many-to-many
        options["uselist"] = True
        
    # Add secondary for many-to-many
    if rel_type == "many-to-many" and rel_config.get("secondary"):
        options["secondary"] = rel_config["secondary"]
        
    # Add cascade if specified
    if rel_config.get("cascade"):
        options["cascade"] = rel_config["cascade"]
        
    return options


def get_relationship_type_hint(rel_config: dict[str, Any]) -> str:
    """
    Lấy type hint cho relationship field.
    
    Args:
        rel_config: Relationship config dict
        
    Returns:
        Type hint string
        
    Ví dụ:
        >>> get_relationship_type_hint({"type": "one-to-one", "target": "Profile"})
        "Mapped[Profile]"
        >>> get_relationship_type_hint({"type": "one-to-many", "target": "OrderItem"})
        "Mapped[list[OrderItem]]"
    """
    rel_type = rel_config.get("type", "").lower()
    target = rel_config.get("target", "Entity")
    
    if rel_type == "one-to-one":
        return f"Mapped[{target}]"
    else:  # one-to-many, many-to-many
        return f"Mapped[list[{target}]]"


# ============================================================================
# Lifecycle Event Helpers
# ============================================================================

def validate_lifecycle_event(event_name: str) -> None:
    """
    Validate lifecycle event name.
    
    Args:
        event_name: Tên event
        
    Raises:
        MidicoderError: Nếu event không hợp lệ
    """
    if event_name not in VALID_LIFECYCLE_EVENTS:
        EM.raise_error(
            ErrorCode.CP01_INVALID_LIFECYCLE_EVENT,
            event_name=event_name,
            valid_events=list(VALID_LIFECYCLE_EVENTS),
        )


def get_event_decorator_code(event_name: str, model_name: str) -> str:
    """
    Generate decorator code cho lifecycle event.
    
    Args:
        event_name: Tên event
        model_name: Tên model class
        
    Returns:
        Decorator code string
        
    Ví dụ:
        >>> get_event_decorator_code("before_insert", "User")
        "@event.listens_for(User, 'before_insert')"
    """
    validate_lifecycle_event(event_name)
    return f"@event.listens_for({model_name}, '{event_name}')"


# ============================================================================
# Constraint Helpers
# ============================================================================

def get_column_constraints(field_config: dict[str, Any]) -> dict[str, Any]:
    """
    Lấy column constraints từ field config.
    
    Args:
        field_config: Field configuration dict
        
    Returns:
        Dict của constraints cho Column()
        
    Ví dụ:
        >>> get_column_constraints({"nullable": False, "unique": True})
        {"nullable": False, "unique": True}
    """
    constraints: dict[str, Any] = {}
    
    # Map config keys to SQLAlchemy constraint params
    if "nullable" in field_config:
        constraints["nullable"] = field_config["nullable"]
        
    if field_config.get("primary_key"):
        constraints["primary_key"] = True
        
    if field_config.get("unique"):
        constraints["unique"] = True
        
    if field_config.get("index"):
        constraints["index"] = True
        
    if "default" in field_config:
        default_val = field_config["default"]
        # Handle callable defaults
        if callable(default_val):
            constraints["default"] = default_val
        else:
            constraints["default"] = default_val
            
    if "server_default" in field_config:
        constraints["server_default"] = text(field_config["server_default"])
        
    if "check" in field_config:
        # Check constraint will be handled separately
        pass
        
    return constraints


def get_check_constraint(field_name: str, condition: str) -> str:
    """
    Generate check constraint code.
    
    Args:
        field_name: Tên field
        condition: Condition expression
        
    Returns:
        Check constraint code string
    """
    return f"CheckConstraint('{condition}')"


def get_index_code(fields: list[str], name: str | None = None) -> str:
    """
    Generate index code.
    
    Args:
        fields: Danh sách field names
        name: Tên index (optional)
        
    Returns:
        Index code string
    """
    if name:
        return f"Index('{name}', {', '.join(fields)})"
    else:
        index_name = f"idx_{'_'.join(fields)}"
        return f"Index('{index_name}', {', '.join(fields)})"


# ============================================================================
# Utility Functions
# ============================================================================

def to_snake_case(name: str) -> str:
    """
    Chuyển string sang snake_case.
    
    Args:
        name: Tên cần chuyển
        
    Returns:
        Snake case string
        
    Ví dụ:
        >>> to_snake_case("OrderItem")
        "order_item"
        >>> to_snake_case("UserID")
        "user_id"
    """
    # Handle camelCase và PascalCase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_table_name(entity_name: str) -> str:
    """
    Chuyển entity name sang table name.
    
    Args:
        entity_name: Tên entity
        
    Returns:
        Table name (plural, snake_case)
        
    Ví dụ:
        >>> to_table_name("Order")
        "orders"
        >>> to_table_name("OrderItem")
        "order_items"
    """
    snake = to_snake_case(entity_name)
    
    # Pluralize simple cases
    if not snake.endswith("s"):
        snake += "s"
        
    return snake


def get_model_imports(
    fields: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> set[str]:
    """
    Lấy tất cả imports cần thiết cho model.
    
    Args:
        fields: Danh sách fields
        relationships: Danh sách relationships
        
    Returns:
        Set của import statements
    """
    imports = {
        "from sqlalchemy import Column",
        "from sqlalchemy.orm import Mapped, relationship",
        "from api.app.database import Base",
    }
    
    # Add field-specific imports
    imports.update(get_field_imports(fields))
    
    # Add relationship imports if needed
    if relationships:
        imports.add("from typing import TYPE_CHECKING")
        
    return imports