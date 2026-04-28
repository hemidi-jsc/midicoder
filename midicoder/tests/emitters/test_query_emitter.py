"""
Tests cho Query Emitter (CP01-Part4: Queries).

Module này chứa unit tests và integration tests cho:
- Query parser (filters, pagination, projection)
- FastAPI query templates
- NestJS query templates
- Emitter integration

Tests theo TDD: Red → Green → Refactor

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest
from pathlib import Path

# Mock imports - sẽ được implement sau
try:
    from midicoder.emitters.query_parser import (
        parse_filters,
        parse_pagination,
        parse_projection,
        FilterExpression,
        PaginationConfig,
        ProjectionConfig,
    )
except ImportError:
    # Phase RED: Classes chưa tồn tại, tests sẽ fail
    FilterExpression = None
    PaginationConfig = None
    ProjectionConfig = None


# ============================================================================
# Test Filter Parser
# ============================================================================

class TestParseFilters:
    """Tests cho parse_filters() function."""

    def test_parse_empty_filters(self):
        """Test parse filters rỗng."""
        filters = {}
        result = parse_filters(filters)
        assert result == []

    def test_parse_simple_eq_filter(self):
        """Test parse filter eq đơn giản."""
        filters = {"status": {"eq": "pending"}}
        result = parse_filters(filters)
        assert len(result) == 1
        assert result[0].field == "status"
        assert result[0].operator == "eq"
        assert result[0].value == "pending"

    def test_parse_multiple_filters(self):
        """Test parse nhiều filters."""
        filters = {
            "status": {"eq": "pending"},
            "total": {"gte": 100},
        }
        result = parse_filters(filters)
        assert len(result) == 2

    def test_parse_between_filter(self):
        """Test parse filter between."""
        filters = {
            "created_at": {"between": ["2024-01-01", "2024-12-31"]}
        }
        result = parse_filters(filters)
        assert len(result) == 1
        assert result[0].operator == "between"
        assert result[0].value == ["2024-01-01", "2024-12-31"]

    def test_parse_in_filter(self):
        """Test parse filter in."""
        filters = {"category": {"in": ["electronics", "clothing"]}}
        result = parse_filters(filters)
        assert result[0].operator == "in"
        assert result[0].value == ["electronics", "clothing"]

    def test_parse_is_null_filter(self):
        """Test parse filter is_null."""
        filters = {"deleted_at": {"is_null": True}}
        result = parse_filters(filters)
        assert result[0].operator == "is_null"

    def test_parse_like_filter(self):
        """Test parse filter like."""
        filters = {"name": {"like": "%test%"}}
        result = parse_filters(filters)
        assert result[0].operator == "like"
        assert result[0].value == "%test%"

    def test_parse_ilike_filter(self):
        """Test parse filter ilike (case-insensitive)."""
        filters = {"name": {"ilike": "%TEST%"}}
        result = parse_filters(filters)
        assert result[0].operator == "ilike"

    def test_parse_not_in_filter(self):
        """Test parse filter not_in."""
        filters = {"status": {"not_in": ["cancelled", "refunded"]}}
        result = parse_filters(filters)
        assert result[0].operator == "not_in"

    def test_parse_is_not_null_filter(self):
        """Test parse filter is_not_null."""
        filters = {"email": {"is_not_null": True}}
        result = parse_filters(filters)
        assert result[0].operator == "is_not_null"

    def test_parse_invalid_operator(self):
        """Test parse operator không hợp lệ - nên raise error."""
        filters = {"status": {"invalid_op": "pending"}}
        with pytest.raises(ValueError) as exc_info:
            parse_filters(filters)
        assert "invalid operator" in str(exc_info.value).lower()


# ============================================================================
# Test Pagination Parser
# ============================================================================

class TestParsePagination:
    """Tests cho parse_pagination() function."""

    def test_parse_offset_pagination(self):
        """Test parse offset pagination."""
        pagination = {
            "type": "offset",
            "page_size": 20,
            "page": 1,
        }
        result = parse_pagination(pagination)
        assert result.type == "offset"
        assert result.page_size == 20
        assert result.page == 1
        assert result.offset == 0  # (page - 1) * page_size

    def test_parse_offset_pagination_with_offset(self):
        """Test parse offset pagination với offset trực tiếp."""
        pagination = {
            "type": "offset",
            "page_size": 20,
            "offset": 40,
        }
        result = parse_pagination(pagination)
        assert result.offset == 40

    def test_parse_cursor_pagination(self):
        """Test parse cursor pagination."""
        pagination = {
            "type": "cursor",
            "limit": 20,
            "cursor": "eyJpZCI6MTIzfQ==",
        }
        result = parse_pagination(pagination)
        assert result.type == "cursor"
        assert result.limit == 20
        assert result.cursor == "eyJpZCI6MTIzfQ=="

    def test_parse_default_pagination(self):
        """Test parse pagination mặc định."""
        pagination = {}
        result = parse_pagination(pagination)
        assert result.type == "offset"  # default
        assert result.page_size == 20  # default

    def test_parse_invalid_pagination_type(self):
        """Test parse pagination type không hợp lệ."""
        pagination = {"type": "invalid"}
        with pytest.raises(ValueError) as exc_info:
            parse_pagination(pagination)
        assert "invalid pagination type" in str(exc_info.value).lower()

    def test_parse_negative_page_size(self):
        """Test parse page_size âm - nên raise error."""
        pagination = {"type": "offset", "page_size": -10}
        with pytest.raises(ValueError) as exc_info:
            parse_pagination(pagination)
        assert "page_size" in str(exc_info.value).lower()


# ============================================================================
# Test Projection Parser
# ============================================================================

class TestParseProjection:
    """Tests cho parse_projection() function."""

    def test_parse_simple_include(self):
        """Test parse include đơn giản."""
        projection = {
            "include": ["id", "name", "status"]
        }
        result = parse_projection(projection)
        assert result.include == ["id", "name", "status"]
        assert result.exclude == []

    def test_parse_nested_include(self):
        """Test parse include nested."""
        projection = {
            "include": [
                "id",
                "name",
                {"customer": ["id", "name"]},
            ]
        }
        result = parse_projection(projection)
        assert len(result.include) == 3

    def test_parse_exclude(self):
        """Test parse exclude fields."""
        projection = {
            "exclude": ["password", "secret_key"]
        }
        result = parse_projection(projection)
        assert result.exclude == ["password", "secret_key"]

    def test_parse_include_and_exclude(self):
        """Test parse cả include và exclude."""
        projection = {
            "include": ["id", "name"],
            "exclude": ["password"],
        }
        result = parse_projection(projection)
        assert result.include == ["id", "name"]
        assert result.exclude == ["password"]

    def test_parse_empty_projection(self):
        """Test parse projection rỗng (include tất cả)."""
        projection = {}
        result = parse_projection(projection)
        assert result.include == []
        assert result.exclude == []


# ============================================================================
# Test Integration: Full Query DSL Parsing
# ============================================================================

class TestQueryDSLIntegration:
    """Integration tests cho full Query DSL parsing."""

    def test_parse_full_query_dsl(self):
        """Test parse full Query DSL với tất cả components."""
        query_dsl = {
            "id": "GetOrders",
            "filters": {
                "status": {"eq": "pending"},
                "total": {"gte": 100},
            },
            "pagination": {
                "type": "offset",
                "page_size": 20,
                "page": 1,
            },
            "projection": {
                "include": ["id", "order_number", "status", "total"],
                "exclude": ["internal_notes"],
            },
        }

        # Parse từng component
        filters = parse_filters(query_dsl.get("filters", {}))
        pagination = parse_pagination(query_dsl.get("pagination", {}))
        projection = parse_projection(query_dsl.get("projection", {}))

        # Verify
        assert len(filters) == 2
        assert pagination.type == "offset"
        assert pagination.page_size == 20
        assert len(projection.include) == 4
        assert projection.exclude == ["internal_notes"]

    def test_parse_cursor_pagination_with_filters(self):
        """Test parse cursor pagination với nhiều filters."""
        query_dsl = {
            "filters": {
                "created_at": {"between": ["2024-01-01", "2024-12-31"]},
                "category": {"in": ["electronics", "clothing"]},
                "deleted_at": {"is_null": True},
            },
            "pagination": {
                "type": "cursor",
                "limit": 50,
            },
        }

        filters = parse_filters(query_dsl["filters"])
        pagination = parse_pagination(query_dsl["pagination"])

        assert len(filters) == 3
        assert pagination.type == "cursor"
        assert pagination.limit == 50


# ============================================================================
# Test FastAPI Query Templates (Placeholder - sẽ implement sau)
# ============================================================================

class TestFastAPIQueryTemplates:
    """Tests cho FastAPI query templates."""

    def test_query_template_exists(self):
        """Test query template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/templates/domain/queries/query.py.jinja2")
        assert template_path.exists(), "Query template not found"

    def test_query_handler_template_exists(self):
        """Test query handler template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/templates/domain/queries/query_handler.py.jinja2")
        assert template_path.exists(), "Query handler template not found"

    def test_query_validator_template_exists(self):
        """Test query validator template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/templates/domain/queries/query_validator.py.jinja2")
        assert template_path.exists(), "Query validator template not found"

    def test_query_guards_template_exists(self):
        """Test query guards template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/templates/domain/queries/query_guards.py.jinja2")
        assert template_path.exists(), "Query guards template not found"

    def test_query_output_template_exists(self):
        """Test query output template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/templates/domain/queries/query_output.py.jinja2")
        assert template_path.exists(), "Query output template not found"


# ============================================================================
# Test NestJS Query Templates (Placeholder - sẽ implement sau)
# ============================================================================

class TestNestJSQueryTemplates:
    """Tests cho NestJS query templates."""

    def test_query_template_exists(self):
        """Test query template file tồn tại."""
        template_path = Path("midicoder/stacks/nestjs/templates/domain/queries/query.ts.jinja2")
        assert template_path.exists(), "NestJS query template not found"

    def test_query_handler_template_exists(self):
        """Test query handler template file tồn tại."""
        template_path = Path("midicoder/stacks/nestjs/templates/domain/queries/query.handler.ts.jinja2")
        assert template_path.exists(), "NestJS query handler template not found"


# ============================================================================
# Test Emitter Integration (Placeholder - sẽ implement sau)
# ============================================================================

class TestEmitterIntegration:
    """Integration tests cho emitter."""

    def test_backend_fastapi_emitter_has_emit_query(self):
        """Test BackendFastAPIEmitter có method _emit_query."""
        from midicoder.emitters.backend_fastapi import BackendFastAPIEmitter
        assert hasattr(BackendFastAPIEmitter, "_emit_query"), "_emit_query method not found"

    def test_backend_nestjs_emitter_has_emit_query(self):
        """Test BackendNestJSEmitter có method _emit_query."""
        from midicoder.emitters.backend_nestjs import BackendNestJSEmitter
        assert hasattr(BackendNestJSEmitter, "_emit_query"), "_emit_query method not found"