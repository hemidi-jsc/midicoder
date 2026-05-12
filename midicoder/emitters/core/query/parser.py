"""Compat shim — re-exports from domain_model.query_parser."""
from midicoder.emitters.core.domain_model.query_parser import (
    parse_filters, parse_pagination, parse_projection,
    build_query_conditions, build_select_fields, VALID_OPERATORS,
)

__all__ = [
    "parse_filters", "parse_pagination", "parse_projection",
    "build_query_conditions", "build_select_fields", "VALID_OPERATORS",
]
