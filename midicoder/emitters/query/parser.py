"""
Query Parser Module.

Module này cung cấp các hàm để parse Query DSL components:
- Filters: Expression-based filters (GraphQL style)
- Pagination: Offset và Cursor based pagination
- Projection: Include/Exclude field selection

Sử dụng models từ query.models module (FilterOp enum, etc.)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from .models import (
    FilterExpression,
    FilterOp,
    PaginationConfig,
    PaginationType,
    ProjectionConfig,
)


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
        [FilterExpression(field="status", operator=FilterOp.EQ, value="pending"),
         FilterExpression(field="total", operator=FilterOp.GTE, value=100)]
    """
    if not filters:
        return []
    
    result = []
    
    for field, conditions in filters.items():
        if not isinstance(conditions, dict):
            # Default to eq nếu chỉ có value đơn giản
            result.append(FilterExpression(field=field, operator=FilterOp.EQ, value=conditions))
            continue
        
        for operator, value in conditions.items():
            if operator not in VALID_OPERATORS:
                raise ValueError(
                    f"Invalid operator '{operator}' for field '{field}'. "
                    f"Valid operators: {', '.join(sorted(VALID_OPERATORS))}"
                )
            
            result.append(FilterExpression(
                field=field,
                operator=FilterOp(operator),
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
        PaginationConfig(type=PaginationType.OFFSET, page_size=20, page=1, offset=0)
        
        >>> parse_pagination({"type": "cursor", "limit": 50, "cursor": "abc123"})
        PaginationConfig(type=PaginationType.CURSOR, limit=50, cursor="abc123")
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
            type=PaginationType.OFFSET,
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
            type=PaginationType.CURSOR,
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
        if f.operator == FilterOp.BETWEEN:
            conditions.append(f"{f.field} BETWEEN {f.value[0]} AND {f.value[1]}")
        elif f.operator == FilterOp.IN:
            values = ", ".join(str(v) for v in f.value)
            conditions.append(f"{f.field} IN ({values})")
        elif f.operator == FilterOp.NOT_IN:
            values = ", ".join(str(v) for v in f.value)
            conditions.append(f"{f.field} NOT IN ({values})")
        elif f.operator == FilterOp.IS_NULL:
            conditions.append(f"{f.field} IS NULL")
        elif f.operator == FilterOp.IS_NOT_NULL:
            conditions.append(f"{f.field} IS NOT NULL")
        else:
            conditions.append(f"{f.field} {f.operator.value.upper()} {f.value!r}")
    
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


# ============================================================================
# Exports
# ============================================================================

__all__ = [
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