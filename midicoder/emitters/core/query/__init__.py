"""
Compat shim for midicoder.emitters.core.query.

This module re-exports all symbols from the unified domain-model package
for backward compatibility. All new code should import from
midicoder.emitters.core.domain_model instead.
"""

from midicoder.emitters.core.domain_model.query_models import (
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
from midicoder.emitters.core.domain_model.query_parser import (
    parse_filters,
    parse_pagination,
    parse_projection,
    build_query_conditions,
    build_select_fields,
    VALID_OPERATORS,
)
from midicoder.emitters.core.domain_model.query_guards import QueryGuards
from midicoder.emitters.core.domain_model.query_effects import QueryEffects
from midicoder.emitters.core.domain_model.query_fastapi import FastAPIQueryEmitter
from midicoder.emitters.core.domain_model.query_nestjs import NestJSQueryEmitter

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
