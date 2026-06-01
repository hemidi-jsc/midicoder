# -*- coding: utf-8 -*-
"""
Gap-filling tests for query_parser.py — full branch coverage.

Covers all 5 public functions:
- parse_filters()
- parse_pagination()
- parse_projection()
- build_query_conditions()
- build_select_fields()
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.packs.cp_base_domain_model import (
    FilterExpression,
    FilterOp,
    PaginationConfig,
    PaginationType,
    ProjectionConfig,
    build_query_conditions,
    build_select_fields,
    parse_filters,
    parse_pagination,
    parse_projection,
)


# ============================================================================
# parse_filters()
# ============================================================================


class TestParseFilters:
    """Full branch coverage for parse_filters()."""

    def test_empty_dict_returns_empty_list(self):
        """Empty dict should return empty list."""
        assert parse_filters({}) == []

    def test_none_returns_empty_list(self):
        """None (falsy) should return empty list."""
        assert parse_filters({}) == []

    def test_simple_value_defaults_to_eq(self):
        """Non-dict value should default to EQ operator."""
        result = parse_filters({"status": "pending"})
        assert len(result) == 1
        assert result[0].field == "status"
        assert result[0].operator == FilterOp.EQ
        assert result[0].value == "pending"

    def test_single_operator_in_dict(self):
        """Dict with single operator should produce one FilterExpression."""
        result = parse_filters({"total": {"gte": 100}})
        assert len(result) == 1
        assert result[0].field == "total"
        assert result[0].operator == FilterOp.GTE
        assert result[0].value == 100

    def test_multi_operator_dict(self):
        """Dict with multiple operators should produce multiple FilterExpressions."""
        result = parse_filters({"total": {"gt": 0, "lt": 1000}})
        assert len(result) == 2
        ops = {f.operator for f in result}
        assert FilterOp.GT in ops
        assert FilterOp.LT in ops

    def test_all_valid_operators(self):
        """All operators in VALID_OPERATORS should be accepted."""
        valid_ops = [
            "eq", "ne", "gt", "gte", "lt", "lte",
            "in", "not_in", "like", "ilike",
            "between", "is_null", "is_not_null",
        ]
        filters = {f"field_{op}": {op: "val"} for op in valid_ops}
        result = parse_filters(filters)
        assert len(result) == len(valid_ops)

    def test_invalid_operator_raises_error(self):
        """Invalid operator should raise MidicoderError with B01_QUERY_INVALID_FILTER."""
        with pytest.raises(MidicoderError) as exc_info:
            parse_filters({"status": {"invalid_op": "pending"}})
        assert exc_info.value.code == ErrorCode.B01_QUERY_INVALID_FILTER


# ============================================================================
# parse_pagination()
# ============================================================================


class TestParsePagination:
    """Full branch coverage for parse_pagination()."""

    def test_empty_dict_returns_default_config(self):
        """Empty dict should return default PaginationConfig."""
        result = parse_pagination({})
        assert result.type == PaginationType.OFFSET
        assert result.page_size == 20
        assert result.page == 1

    def test_offset_mode(self):
        """Offset pagination should set correct fields."""
        result = parse_pagination({"type": "offset", "page_size": 20, "page": 1})
        assert result.type == PaginationType.OFFSET
        assert result.page_size == 20
        assert result.page == 1

    def test_cursor_mode(self):
        """Cursor pagination should set correct fields."""
        result = parse_pagination({"type": "cursor", "limit": 50, "cursor": "abc123"})
        assert result.type == PaginationType.CURSOR
        assert result.limit == 50
        assert result.cursor == "abc123"

    def test_page_size_negative_raises_error(self):
        """Negative page_size should raise MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            parse_pagination({"type": "offset", "page_size": -1})
        assert exc_info.value.code == ErrorCode.B01_QUERY_INVALID_PAGINATION

    def test_limit_negative_raises_error(self):
        """Negative limit should raise MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            parse_pagination({"type": "cursor", "limit": -5})
        assert exc_info.value.code == ErrorCode.B01_QUERY_INVALID_PAGINATION

    def test_invalid_pagination_type_raises_error(self):
        """Invalid pagination type should raise MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            parse_pagination({"type": "invalid_type"})
        assert exc_info.value.code == ErrorCode.B01_QUERY_INVALID_PAGINATION


# ============================================================================
# parse_projection()
# ============================================================================


class TestParseProjection:
    """Full branch coverage for parse_projection()."""

    def test_empty_dict_returns_default_config(self):
        """Empty dict should return default ProjectionConfig."""
        result = parse_projection({})
        assert result.include == []
        assert result.exclude == []

    def test_include_fields(self):
        """Include fields should be set correctly."""
        result = parse_projection({"include": ["id", "name"]})
        assert result.include == ["id", "name"]
        assert result.exclude == []

    def test_exclude_fields(self):
        """Exclude fields should be set correctly."""
        result = parse_projection({"exclude": ["password"]})
        assert result.include == []
        assert result.exclude == ["password"]

    def test_include_and_exclude_together(self):
        """Both include and exclude should be set correctly."""
        result = parse_projection({"include": ["id", "name"], "exclude": ["password"]})
        assert result.include == ["id", "name"]
        assert result.exclude == ["password"]


# ============================================================================
# build_query_conditions()
# ============================================================================


class TestBuildQueryConditions:
    """Full branch coverage for build_query_conditions()."""

    def test_empty_list_returns_empty_string(self):
        """Empty filter list should return empty string."""
        assert build_query_conditions([]) == ""

    def test_between_operator(self):
        """BETWEEN operator should format as field BETWEEN x AND y."""
        expr = FilterExpression(field="age", operator=FilterOp.BETWEEN, value=[18, 65])
        result = build_query_conditions([expr])
        assert "age BETWEEN 18 AND 65" in result

    def test_in_operator(self):
        """IN operator should format as field IN (x, y, z)."""
        expr = FilterExpression(field="status", operator=FilterOp.IN, value=["a", "b"])
        result = build_query_conditions([expr])
        assert "status IN (a, b)" in result

    def test_not_in_operator(self):
        """NOT_IN operator should format as field NOT IN (x, y)."""
        expr = FilterExpression(field="status", operator=FilterOp.NOT_IN, value=["x", "y"])
        result = build_query_conditions([expr])
        assert "status NOT IN (x, y)" in result

    def test_is_null_operator(self):
        """IS_NULL operator should format as field IS NULL."""
        expr = FilterExpression(field="deleted_at", operator=FilterOp.IS_NULL, value=None)
        result = build_query_conditions([expr])
        assert "deleted_at IS NULL" in result

    def test_is_not_null_operator(self):
        """IS_NOT_NULL operator should format as field IS NOT NULL."""
        expr = FilterExpression(field="id", operator=FilterOp.IS_NOT_NULL, value=None)
        result = build_query_conditions([expr])
        assert "id IS NOT NULL" in result

    def test_default_operator_eq(self):
        """Default operator (EQ) should format as field EQ 'value'."""
        expr = FilterExpression(field="name", operator=FilterOp.EQ, value="alice")
        result = build_query_conditions([expr])
        assert "name EQ" in result
        assert "alice" in result

    def test_default_operator_gt(self):
        """Default operator (GT) should format as field GT value."""
        expr = FilterExpression(field="total", operator=FilterOp.GT, value=100)
        result = build_query_conditions([expr])
        assert "total GT 100" in result

    def test_multiple_conditions_joined_with_and(self):
        """Multiple conditions should be joined with AND."""
        exprs = [
            FilterExpression(field="status", operator=FilterOp.EQ, value="active"),
            FilterExpression(field="total", operator=FilterOp.GT, value=0),
        ]
        result = build_query_conditions(exprs)
        assert " AND " in result


# ============================================================================
# build_select_fields()
# ============================================================================


class TestBuildSelectFields:
    """Full branch coverage for build_select_fields()."""

    def test_no_include_returns_all_minus_exclude(self):
        """No include: return all_fields minus exclude."""
        proj = ProjectionConfig(include=[], exclude=["password"])
        result = build_select_fields(proj, ["id", "name", "password"])
        assert result == ["id", "name"]

    def test_no_projection_returns_all_fields(self):
        """Empty ProjectionConfig should return all fields."""
        proj = ProjectionConfig()
        result = build_select_fields(proj, ["id", "name", "email"])
        assert result == ["id", "name", "email"]

    def test_include_with_flat_include_minus_exclude(self):
        """With include: return include minus exclude."""
        proj = ProjectionConfig(include=["id", "name", "email"], exclude=["email"])
        result = build_select_fields(proj, ["id", "name", "email", "password"])
        assert result == ["id", "name"]

    def test_include_with_nested_fields(self):
        """Nested fields in include should be preserved via get_flat_include_fields."""
        proj = ProjectionConfig(include=["id", "profile.email", "profile.name"], exclude=[])
        result = build_select_fields(proj, ["id", "profile.email", "profile.name"])
        assert "id" in result
        assert "profile.email" in result
        assert "profile.name" in result

    def test_exclude_removes_from_included_fields(self):
        """Exclude should filter out fields from include list."""
        proj = ProjectionConfig(include=["id", "name", "password", "token"], exclude=["password", "token"])
        result = build_select_fields(proj, ["id", "name", "password", "token"])
        assert "password" not in result
        assert "token" not in result
        assert "id" in result
        assert "name" in result
