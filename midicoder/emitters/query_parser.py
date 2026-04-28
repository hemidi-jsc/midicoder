"""
Query Parser Module.

Module này cung cấp các hàm để parse Query DSL components:
- Filters: Expression-based filters (GraphQL style)
- Pagination: Offset và Cursor based pagination
- Projection: Include/Exclude field selection

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class FilterExpression:
    """
    Biểu thức filter cho query.
    
    Attributes:
        field: Tên field cần filter
        operator: Operator (eq, ne, gt, gte, lt, lte, in, not_in, like, ilike, between, is_null, is_not_null)
        value: Giá trị để so sánh
    """
    field: str
    operator: str
    value: Any
    
    def to_sqlalchemy(self) -> Any:
        """
        Chuyển filter expression sang SQLAlchemy condition.
        
        Returns:
            SQLAlchemy condition expression
        """
        from sqlalchemy import column
        
        col = column(self.field)
        
        if self.operator == "eq":
            return col == self.value
        elif self.operator == "ne":
            return col != self.value
        elif self.operator == "gt":
            return col > self.value
        elif self.operator == "gte":
            return col >= self.value
        elif self.operator == "lt":
            return col < self.value
        elif self.operator == "lte":
            return col <= self.value
        elif self.operator == "in":
            return col.in_(self.value)
        elif self.operator == "not_in":
            return col.notin_(self.value)
        elif self.operator == "like":
            return col.like(self.value)
        elif self.operator == "ilike":
            return col.ilike(self.value)
        elif self.operator == "between":
            return col.between(self.value[0], self.value[1])
        elif self.operator == "is_null":
            return col.is_(None)
        elif self.operator == "is_not_null":
            return col.isnot(None)
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class PaginationConfig:
    """
    Cấu hình pagination cho query.
    
    Attributes:
        type: Loại pagination (offset hoặc cursor)
        page_size: Số lượng records mỗi page (cho offset)
        page: Page number (cho offset)
        offset: Offset trực tiếp (cho offset)
        limit: Limit records (cho cursor)
        cursor: Cursor string (cho cursor)
    """
    type: str = "offset"
    page_size: int = 20
    page: int = 1
    offset: int = 0
    limit: int = 20
    cursor: str | None = None
    
    def __post_init__(self) -> None:
        """Validate pagination config sau khi init."""
        if self.type == "offset" and self.offset == 0 and self.page > 1:
            # Tính offset từ page
            self.offset = (self.page - 1) * self.page_size


@dataclass
class ProjectionConfig:
    """
    Cấu hình projection cho query (field selection).
    
    Attributes:
        include: Danh sách fields cần include (nested dict cho relationships)
        exclude: Danh sách fields cần exclude
    """
    include: list[Any] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    
    def get_flat_include_fields(self) -> list[str]:
        """
        Lấy danh sách flat fields từ include (không bao gồm nested).
        
        Returns:
            Danh sách field names
        """
        flat_fields = []
        for item in self.include:
            if isinstance(item, str):
                flat_fields.append(item)
            elif isinstance(item, dict):
                # Nested fields - lấy key chính
                for key in item.keys():
                    flat_fields.append(key)
        return flat_fields
    
    def get_sensitive_fields_to_exclude(self) -> list[str]:
        """
        Lấy danh sách sensitive fields cần exclude tự động.
        
        Returns:
            Danh sách sensitive field names
        """
        sensitive_fields = [
            "password", "secret_key", "token", "api_key", 
            "private_key", "credential", "auth_token"
        ]
        return sensitive_fields


# ============================================================================
# Valid Operators
# ============================================================================

VALID_OPERATORS = {
    "eq", "ne", "gt", "gte", "lt", "lte",
    "in", "not_in", "like", "ilike",
    "between", "is_null", "is_not_null"
}


# ============================================================================
# Parser Functions
# ============================================================================

def parse_filters(filters: dict[str, Any]) -> list[FilterExpression]:
    """
    Parse expression-based filters (GraphQL style).
    
    Args:
        filters: Dict với format {field: {operator: value}}
        
    Returns:
        Danh sách FilterExpression
        
    Raises:
        ValueError: Nếu operator không hợp lệ
        
    Example:
        >>> filters = {
        ...     "status": {"eq": "pending"},
        ...     "total": {"gte": 100}
        ... }
        >>> parse_filters(filters)
        [FilterExpression(field="status", operator="eq", value="pending"),
         FilterExpression(field="total", operator="gte", value=100)]
    """
    if not filters:
        return []
    
    result = []
    
    for field, conditions in filters.items():
        if not isinstance(conditions, dict):
            # Default to eq nếu chỉ có value đơn giản
            result.append(FilterExpression(field=field, operator="eq", value=conditions))
            continue
        
        for operator, value in conditions.items():
            if operator not in VALID_OPERATORS:
                raise ValueError(
                    f"Invalid operator '{operator}' for field '{field}'. "
                    f"Valid operators: {', '.join(sorted(VALID_OPERATORS))}"
                )
            
            result.append(FilterExpression(
                field=field,
                operator=operator,
                value=value
            ))
    
    return result


def parse_pagination(pagination: dict[str, Any]) -> PaginationConfig:
    """
    Parse pagination configuration (offset hoặc cursor).
    
    Args:
        pagination: Dict với pagination config
        
    Returns:
        PaginationConfig instance
        
    Raises:
        ValueError: Nếu pagination type không hợp lệ hoặc page_size âm
        
    Example:
        >>> parse_pagination({"type": "offset", "page_size": 20, "page": 1})
        PaginationConfig(type="offset", page_size=20, page=1, offset=0)
        
        >>> parse_pagination({"type": "cursor", "limit": 50, "cursor": "abc123"})
        PaginationConfig(type="cursor", limit=50, cursor="abc123")
    """
    if not pagination:
        return PaginationConfig()
    
    ptype = pagination.get("type", "offset")
    
    if ptype not in ("offset", "cursor"):
        raise ValueError(
            f"Invalid pagination type '{ptype}'. "
            f"Valid types: 'offset', 'cursor'"
        )
    
    if ptype == "offset":
        page_size = pagination.get("page_size", 20)
        if page_size < 0:
            raise ValueError(f"page_size cannot be negative: {page_size}")
        
        page = pagination.get("page", 1)
        offset = pagination.get("offset", 0)
        
        return PaginationConfig(
            type="offset",
            page_size=page_size,
            page=page,
            offset=offset
        )
    
    else:  # cursor
        limit = pagination.get("limit", 20)
        if limit < 0:
            raise ValueError(f"limit cannot be negative: {limit}")
        
        cursor = pagination.get("cursor")
        
        return PaginationConfig(
            type="cursor",
            limit=limit,
            cursor=cursor
        )


def parse_projection(projection: dict[str, Any]) -> ProjectionConfig:
    """
    Parse projection configuration (include/exclude fields).
    
    Args:
        projection: Dict với include/exclude fields
        
    Returns:
        ProjectionConfig instance
        
    Example:
        >>> parse_projection({"include": ["id", "name"], "exclude": ["password"]})
        ProjectionConfig(include=["id", "name"], exclude=["password"])
        
        >>> parse_projection({"include": ["id", {"customer": ["id", "name"]}]})
        ProjectionConfig(include=["id", {"customer": ["id", "name"]}], exclude=[])
    """
    if not projection:
        return ProjectionConfig()
    
    include = projection.get("include", [])
    exclude = projection.get("exclude", [])
    
    return ProjectionConfig(
        include=include,
        exclude=exclude
    )


# ============================================================================
# Convenience Functions
# ============================================================================

def build_query_conditions(filters: list[FilterExpression]) -> str:
    """
    Build query conditions string từ list của FilterExpression.
    
    Args:
        filters: Danh sách FilterExpression
        
    Returns:
        Query conditions string (pseudo-SQL format)
    """
    if not filters:
        return ""
    
    conditions = []
    for f in filters:
        if f.operator == "between":
            conditions.append(f"{f.field} BETWEEN {f.value[0]} AND {f.value[1]}")
        elif f.operator == "in":
            values = ", ".join(str(v) for v in f.value)
            conditions.append(f"{f.field} IN ({values})")
        elif f.operator == "not_in":
            values = ", ".join(str(v) for v in f.value)
            conditions.append(f"{f.field} NOT IN ({values})")
        elif f.operator == "is_null":
            conditions.append(f"{f.field} IS NULL")
        elif f.operator == "is_not_null":
            conditions.append(f"{f.field} IS NOT NULL")
        else:
            conditions.append(f"{f.field} {f.operator.upper()} {f.value!r}")
    
    return " AND ".join(conditions)


def build_select_fields(projection: ProjectionConfig, all_fields: list[str]) -> list[str]:
    """
    Build SELECT fields list từ projection config.
    
    Args:
        projection: ProjectionConfig instance
        all_fields: Danh sách tất cả fields available
        
    Returns:
        Danh sách fields cần SELECT
    """
    if not projection.include:
        # Không có include - trả về tất cả trừ exclude
        return [f for f in all_fields if f not in projection.exclude]
    
    # Có include - trả về include trừ exclude
    flat_include = projection.get_flat_include_fields()
    return [f for f in flat_include if f not in projection.exclude]


__all__ = [
    # Data models
    "FilterExpression",
    "PaginationConfig",
    "ProjectionConfig",
    # Parser functions
    "parse_filters",
    "parse_pagination",
    "parse_projection",
    # Convenience functions
    "build_query_conditions",
    "build_select_fields",
    # Constants
    "VALID_OPERATORS",
]