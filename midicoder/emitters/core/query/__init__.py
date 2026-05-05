"""
Query Emitter Module.

Module này cung cấp các classes cho Query code generation:
- Models: Query, AggregationQuery, và các enums
- Guards: QueryGuards cho AUTH và TENANT_SCOPE validation
- Effects: QueryEffects cho WRITE_AUDIT_LOG và RECORD_METRIC
- Emitters: FastAPIQueryEmitter, NestJSQueryEmitter

Theo SoT E03, authorized_query pattern:
- authorize_permission
- enforce_tenant_scope
- query_records

Theo SoT E06:
- Every authorized_query must have enforce_tenant_scope
- Query must filter by tenant_id

Usage:
    from midicoder.emitters.core.query import (
        Query, QueryGuard, QueryEffect,
        FastAPIQueryEmitter, NestJSQueryEmitter,
    )

Author: Midicoder Team
Version: 1.0.0
"""

from .models import (
    # Enums
    FilterOp,
    PaginationType,
    SortDirection,
    AggFunction,
    QueryGuardType,
    QueryEffectType,
    # Data classes
    QueryField,
    QueryGuard,
    QueryEffect,
    FilterExpression,
    FilterGroup,
    PHIMaskingConfig,
    SortExpression,
    PaginationConfig,
    ProjectionConfig,
    AggregationConfig,
    # Query models
    Query,
    AggregationQuery,
)
from .parser import (
    parse_filters,
    parse_pagination,
    parse_projection,
    build_query_conditions,
    build_select_fields,
    VALID_OPERATORS,
)
from .guards import QueryGuards
from .effects import QueryEffects
from .fastapi import FastAPIQueryEmitter
from .nestjs import NestJSQueryEmitter

__all__ = [
    # Enums
    "FilterOp",
    "PaginationType",
    "SortDirection",
    "AggFunction",
    "QueryGuardType",
    "QueryEffectType",
    # Data classes
    "QueryField",
    "QueryGuard",
    "QueryEffect",
    "FilterExpression",
    "FilterGroup",
    "PHIMaskingConfig",
    "SortExpression",
    "PaginationConfig",
    "ProjectionConfig",
    "AggregationConfig",
    # Query models
    "Query",
    "AggregationQuery",
    # Parser functions
    "parse_filters",
    "parse_pagination",
    "parse_projection",
    "build_query_conditions",
    "build_select_fields",
    "VALID_OPERATORS",
    # Guards and Effects
    "QueryGuards",
    "QueryEffects",
    # Emitters
    "FastAPIQueryEmitter",
    "NestJSQueryEmitter",
]
