"""
Tests cho Query Emitter Module (CP01-Part4).

Test cases:
- Query models (Query, AggregationQuery, enums) - 7 tests
- QueryGuards - 3 tests
- QueryParser - 5 tests
- QueryAggregation - 3 tests
- FastAPIQueryEmitter - 3 tests
- NestJSQueryEmitter - 3 tests

Total: 24 tests (theo clarification Q7)

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path

import pytest

from midicoder.emitters.core.query import (
    AggregationConfig,
    AggregationQuery,
    AggFunction,
    FilterExpression,
    FilterGroup,
    FilterOp,
    PaginationConfig,
    PaginationType,
    PHIMaskingConfig,
    ProjectionConfig,
    Query,
    QueryEffect,
    QueryEffectType,
    QueryField,
    QueryGuard,
    QueryGuardType,
    QueryGuards,
    SortDirection,
    SortExpression,
    FastAPIQueryEmitter,
    NestJSQueryEmitter,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_get_order_query():
    """Sample GetOrder Query."""
    return Query(
        id="GetOrder",
        description="Lay don hang theo ID",
        reads_from="Order",
        input=[
            QueryField(name="order_id", field_type="uuid", required=True),
        ],
        filters=[
            FilterExpression(field="status", operator=FilterOp.IN, value=["pending", "processing"]),
        ],
        pagination=PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=20,
            page=1,
        ),
        projection=ProjectionConfig(
            include=["id", "customer_id", "status", "total"],
            exclude=["password", "internal_notes"],
        ),
        sort=[
            SortExpression(field="created_at", direction=SortDirection.DESC),
            SortExpression(field="id", direction=SortDirection.ASC),
        ],
        guards=[
            QueryGuard(guard_type=QueryGuardType.AUTH, permission="order.read"),
            QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE, mode="tenant_isolated"),
        ],
        effects=[
            QueryEffect(effect_type=QueryEffectType.WRITE_AUDIT_LOG, audit_action="order_viewed"),
            QueryEffect(effect_type=QueryEffectType.RECORD_METRIC, metric_name="query.duration"),
        ],
    )


@pytest.fixture
def sample_count_orders_query():
    """Sample CountOrders Aggregation Query."""
    return AggregationQuery(
        id="CountOrders",
        description="Dem so luong don hang",
        reads_from="Order",
        aggregation=AggregationConfig(
            function=AggFunction.COUNT,
            group_by=["status"],
        ),
        filters=[
            FilterExpression(field="created_at", operator=FilterOp.GTE, value="2026-01-01"),
        ],
        pagination=PaginationConfig(type=PaginationType.OFFSET, page_size=10),
        guards=[
            QueryGuard(guard_type=QueryGuardType.AUTH, permission="order.read"),
            QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE, mode="tenant_isolated"),
        ],
        effects=[
            QueryEffect(effect_type=QueryEffectType.WRITE_AUDIT_LOG, audit_action="orders_counted"),
        ],
    )


@pytest.fixture
def fastapi_query_emitter():
    """FastAPI Query emitter instance."""
    stack_dir = Path("midicoder/stacks/fastapi/templates")
    return FastAPIQueryEmitter(stack_dir=stack_dir)


@pytest.fixture
def nestjs_query_emitter():
    """NestJS Query emitter instance."""
    stack_dir = Path("midicoder/stacks/nestjs/templates")
    return NestJSQueryEmitter(stack_dir=stack_dir)


# ============================================================================
# TestQueryModels (7 tests)
# ============================================================================


class TestQueryModels:
    """Tests cho Query models."""

    def test_query_has_auth_guard(self, sample_get_order_query: Query):
        """Test: Query.has_auth_guard() tra ve True khi co AUTH guard."""
        assert sample_get_order_query.has_auth_guard() is True

    def test_query_has_tenant_guard(self, sample_get_order_query: Query):
        """Test: Query.has_tenant_guard() tra ve True khi co TENANT_SCOPE guard."""
        assert sample_get_order_query.has_tenant_guard() is True

    def test_query_has_audit_effects(self, sample_get_order_query: Query):
        """Test: Query.has_audit_effects() tra ve True khi co WRITE_AUDIT_LOG effect."""
        assert sample_get_order_query.has_audit_effects() is True

    def test_query_to_dict_and_from_dict(self, sample_get_order_query: Query):
        """Test: Query.to_dict() va from_dict() hoat dong chinh xac."""
        query_dict = sample_get_order_query.to_dict()
        reconstructed = Query.from_dict(query_dict)

        assert reconstructed.id == sample_get_order_query.id
        assert reconstructed.description == sample_get_order_query.description
        assert reconstructed.reads_from == sample_get_order_query.reads_from
        assert len(reconstructed.input) == len(sample_get_order_query.input)
        assert len(reconstructed.filters) == len(sample_get_order_query.filters)
        assert len(reconstructed.sort) == len(sample_get_order_query.sort)
        assert len(reconstructed.guards) == len(sample_get_order_query.guards)
        assert len(reconstructed.effects) == len(sample_get_order_query.effects)

    def test_filter_op_enum(self):
        """Test: FilterOp enum co day du 13 operators."""
        assert FilterOp.EQ.value == "eq"
        assert FilterOp.NE.value == "ne"
        assert FilterOp.GT.value == "gt"
        assert FilterOp.GTE.value == "gte"
        assert FilterOp.LT.value == "lt"
        assert FilterOp.LTE.value == "lte"
        assert FilterOp.IN.value == "in"
        assert FilterOp.NOT_IN.value == "not_in"
        assert FilterOp.LIKE.value == "like"
        assert FilterOp.ILIKE.value == "ilike"
        assert FilterOp.BETWEEN.value == "between"
        assert FilterOp.IS_NULL.value == "is_null"
        assert FilterOp.IS_NOT_NULL.value == "is_not_null"

    def test_pagination_type_enum(self):
        """Test: PaginationType enum co OFFSET va CURSOR."""
        assert PaginationType.OFFSET.value == "offset"
        assert PaginationType.CURSOR.value == "cursor"

    def test_agg_function_enum(self):
        """Test: AggFunction enum co day du aggregation functions."""
        assert AggFunction.COUNT.value == "count"
        assert AggFunction.SUM.value == "sum"
        assert AggFunction.AVG.value == "avg"
        assert AggFunction.MIN.value == "min"
        assert AggFunction.MAX.value == "max"


# ============================================================================
# TestQueryGuards (3 tests)
# ============================================================================


class TestQueryGuards:
    """Tests cho QueryGuards."""

    @pytest.mark.asyncio
    async def test_check_auth_no_user(self, sample_get_order_query: Query):
        """Test: AUTH guard fail khi khong co user_id."""
        guards = QueryGuards(sample_get_order_query)

        with pytest.raises(PermissionError) as exc_info:
            await guards.check_all({}, user_id=None, tenant_id="tenant_001")

        assert "không được xác thực" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_tenant_no_tenant_id(self, sample_get_order_query: Query):
        """Test: TENANT guard fail khi khong co tenant_id."""
        from midicoder.errors import MidicoderError

        guards = QueryGuards(sample_get_order_query)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user_001", tenant_id=None)

        assert exc_info.value.code.value == "MDC-CP01-052"

    @pytest.mark.asyncio
    async def test_check_all_pass(self, sample_get_order_query: Query):
        """Test: Guards pass khi co user_id va tenant_id."""
        guards = QueryGuards(sample_get_order_query)

        # Should not raise
        await guards.check_all(
            {},
            user_id="user_001",
            tenant_id="tenant_001"
        )


# ============================================================================
# TestQueryParser (5 tests)
# ============================================================================


class TestQueryParser:
    """Tests cho query parser functions."""

    def test_parse_filter_expression(self):
        """Test: FilterExpression.to_sqlalchemy() tao condition dung."""
        expr = FilterExpression(field="status", operator=FilterOp.EQ, value="pending")
        condition = expr.to_sqlalchemy()
        assert condition is not None

    def test_parse_pagination_offset(self):
        """Test: PaginationConfig tinh offset tu page."""
        pagination = PaginationConfig(
            type=PaginationType.OFFSET,
            page_size=20,
            page=3,
        )
        assert pagination.offset == 40

    def test_parse_pagination_cursor(self):
        """Test: PaginationConfig voi cursor type."""
        pagination = PaginationConfig(
            type=PaginationType.CURSOR,
            limit=50,
            cursor="abc123",
        )
        assert pagination.type == PaginationType.CURSOR
        assert pagination.limit == 50
        assert pagination.cursor == "abc123"

    def test_parse_projection(self):
        """Test: ProjectionConfig co include va exclude."""
        projection = ProjectionConfig(
            include=["id", "name", "email"],
            exclude=["password", "token"],
        )
        assert "id" in projection.include
        assert "password" in projection.exclude

    def test_parse_sort_multi_field(self):
        """Test: SortExpression support multi-field sorting."""
        sort1 = SortExpression(field="created_at", direction=SortDirection.DESC)
        sort2 = SortExpression(field="id", direction=SortDirection.ASC)

        assert sort1.field == "created_at"
        assert sort1.direction == SortDirection.DESC
        assert sort2.field == "id"
        assert sort2.direction == SortDirection.ASC


# ============================================================================
# TestQueryAggregation (3 tests)
# ============================================================================


class TestQueryAggregation:
    """Tests cho AggregationQuery."""

    def test_count_aggregation(self, sample_count_orders_query: AggregationQuery):
        """Test: COUNT aggregation config."""
        assert sample_count_orders_query.aggregation.function == AggFunction.COUNT
        assert sample_count_orders_query.aggregation.agg_field is None
        assert "status" in sample_count_orders_query.aggregation.group_by

    def test_sum_aggregation(self):
        """Test: SUM aggregation config."""
        agg_query = AggregationQuery(
            id="SumOrderTotals",
            description="Tong doanh thu",
            reads_from="Order",
            aggregation=AggregationConfig(
                function=AggFunction.SUM,
                agg_field="total",
            ),
            guards=[
                QueryGuard(guard_type=QueryGuardType.AUTH, permission="order.read"),
            ],
        )
        assert agg_query.aggregation.function == AggFunction.SUM
        assert agg_query.aggregation.agg_field == "total"

    def test_aggregation_to_dict(self, sample_count_orders_query: AggregationQuery):
        """Test: AggregationQuery.to_dict() hoat dong dung."""
        data = sample_count_orders_query.to_dict()

        assert data["id"] == "CountOrders"
        assert data["aggregation"]["function"] == "count"
        assert "status" in data["aggregation"]["group_by"]


# ============================================================================
# TestFastAPIQueryEmitter (3 tests)
# ============================================================================


class TestFastAPIQueryEmitter:
    """Tests cho FastAPIQueryEmitter."""

    def test_emit_creates_files(
        self,
        fastapi_query_emitter: FastAPIQueryEmitter,
        sample_get_order_query: Query,
    ):
        """Test: emit() tao day du files."""
        files = fastapi_query_emitter.emit(sample_get_order_query, Path("/tmp"))

        assert "get_order.py" in files
        assert "get_order_handler.py" in files
        assert "get_order_validator.py" in files
        assert "get_order_guards.py" in files
        assert "get_order_effects.py" in files
        assert "get_order_output.py" in files
        assert "__init__.py" in files

    def test_emit_content_contains_query_id(
        self,
        fastapi_query_emitter: FastAPIQueryEmitter,
        sample_get_order_query: Query,
    ):
        """Test: Generated content chua query ID."""
        files = fastapi_query_emitter.emit(sample_get_order_query, Path("/tmp"))

        query_content = files["get_order.py"]
        assert "GetOrder" in query_content

    def test_emit_aggregation_creates_files(
        self,
        fastapi_query_emitter: FastAPIQueryEmitter,
        sample_count_orders_query: AggregationQuery,
    ):
        """Test: emit_aggregation() tao aggregation query files."""
        files = fastapi_query_emitter.emit_aggregation(sample_count_orders_query, Path("/tmp"))

        assert "count_orders.py" in files
        assert "count_orders_handler.py" in files
        assert "count_orders_guards.py" in files


# ============================================================================
# TestNestJSQueryEmitter (3 tests)
# ============================================================================


class TestNestJSQueryEmitter:
    """Tests cho NestJSQueryEmitter."""

    def test_emit_creates_files(
        self,
        nestjs_query_emitter: NestJSQueryEmitter,
        sample_get_order_query: Query,
    ):
        """Test: emit() tao day du files cho NestJS."""
        files = nestjs_query_emitter.emit(sample_get_order_query, Path("/tmp"))

        assert "get_order.ts" in files
        assert "get_order.handler.ts" in files
        assert "get_order.validator.ts" in files
        assert "get_order.guards.ts" in files
        assert "get_order.effects.ts" in files
        assert "get_order.output.ts" in files
        assert "index.ts" in files

    def test_emit_content_contains_query_id(
        self,
        nestjs_query_emitter: NestJSQueryEmitter,
        sample_get_order_query: Query,
    ):
        """Test: Generated content chua query ID."""
        files = nestjs_query_emitter.emit(sample_get_order_query, Path("/tmp"))

        query_content = files["get_order.ts"]
        assert "GetOrder" in query_content

    def test_emit_aggregation_creates_files(
        self,
        nestjs_query_emitter: NestJSQueryEmitter,
        sample_count_orders_query: AggregationQuery,
    ):
        """Test: emit_aggregation() tao aggregation query files."""
        files = nestjs_query_emitter.emit_aggregation(sample_count_orders_query, Path("/tmp"))

        assert "count_orders.ts" in files
        assert "count_orders.handler.ts" in files
        assert "count_orders.guards.ts" in files


# ============================================================================
# Tests for FilterGroup (Complex Filters)
# ============================================================================


class TestFilterGroup:
    """Tests cho FilterGroup với AND/OR nested logic."""

    def test_and_group_filter(self):
        """Test: AND group filter kết hợp nhiều conditions."""
        and_group = FilterGroup(
            operator="and",
            filters=[
                FilterExpression("status", FilterOp.EQ, "active"),
                FilterExpression("created_at", FilterOp.GTE, "2026-01-01"),
            ]
        )

        condition = and_group.to_sqlalchemy()
        assert condition is not None

    def test_or_group_filter(self):
        """Test: OR group filter kết hợp nhiều conditions."""
        or_group = FilterGroup(
            operator="or",
            filters=[
                FilterExpression("status", FilterOp.EQ, "active"),
                FilterExpression("status", FilterOp.EQ, "pending"),
            ]
        )

        condition = or_group.to_sqlalchemy()
        assert condition is not None

    def test_nested_group_filter(self):
        """Test: Nested filter groups (AND inside OR)."""
        nested_group = FilterGroup(
            operator="or",
            filters=[
                FilterGroup(
                    operator="and",
                    filters=[
                        FilterExpression("status", FilterOp.EQ, "active"),
                        FilterExpression("created_at", FilterOp.GT, "2026-01-01"),
                    ]
                ),
                FilterExpression("tenant_id", FilterOp.EQ, "abc"),
            ]
        )

        condition = nested_group.to_sqlalchemy()
        assert condition is not None

    def test_empty_group_filter(self):
        """Test: Empty filter group returns true (no filter)."""
        empty_group = FilterGroup(
            operator="and",
            filters=[]
        )

        condition = empty_group.to_sqlalchemy()
        assert condition is not None


# ============================================================================
# Tests for PHIMaskingConfig
# ============================================================================


class TestPHIMasking:
    """Tests cho PHIMaskingConfig (HIPAA compliance)."""

    def test_phi_masking_enabled(self):
        """Test: PHI masking active khi enabled=True."""
        config = PHIMaskingConfig(
            enabled=True,
            default_mask_value="[REDACTED]"
        )

        # SSN field should be masked
        assert config.should_mask("ssn") is True
        assert config.mask_value("ssn", "123-45-6789") == "[REDACTED]"

        # Regular field should not be masked
        assert config.should_mask("patient_name") is False
        assert config.mask_value("patient_name", "John Doe") == "John Doe"

    def test_phi_masking_disabled(self):
        """Test: PHI masking disabled khi enabled=False."""
        config = PHIMaskingConfig(
            enabled=False,
            default_mask_value="[REDACTED]"
        )

        # SSN field should NOT be masked when disabled
        assert config.should_mask("ssn") is False
        assert config.mask_value("ssn", "123-45-6789") == "123-45-6789"

    def test_phi_masking_with_allowed_fields(self):
        """Test: PHI masking respect allowed_fields."""
        config = PHIMaskingConfig(
            enabled=True,
            allowed_fields=["patient_id"],
            default_mask_value="[REDACTED]"
        )

        # patient_id is allowed, should not mask
        assert config.should_mask("patient_id") is False
        assert config.mask_value("patient_id", "P12345") == "P12345"

    def test_phi_masking_with_patterns(self):
        """Test: PHI masking with regex patterns."""
        config = PHIMaskingConfig(
            enabled=True,
            mask_patterns=["^custom_id"],
            default_mask_value="***"
        )

        # custom_id matches pattern
        assert config.should_mask("custom_id") is True
        assert config.mask_value("custom_id", "CID123") == "***"

        # regular_id does not match pattern
        assert config.should_mask("regular_id") is False


# ============================================================================
# Tests for SQLAlchemy Filter Integration
# ============================================================================


class TestSQLAlchemyFilters:
    """Tests cho SQLAlchemy filter integration."""

    def test_eq_filter_sqlalchemy(self):
        """Test: EQ filter to SQLAlchemy."""
        flt = FilterExpression("name", FilterOp.EQ, "John")
        condition = flt.to_sqlalchemy()
        assert condition is not None

    def test_in_filter_sqlalchemy(self):
        """Test: IN filter to SQLAlchemy."""
        flt = FilterExpression("status", FilterOp.IN, ["active", "pending"])
        condition = flt.to_sqlalchemy()
        assert condition is not None

    def test_between_filter_sqlalchemy(self):
        """Test: BETWEEN filter to SQLAlchemy."""
        flt = FilterExpression("amount", FilterOp.BETWEEN, (100, 1000))
        condition = flt.to_sqlalchemy()
        assert condition is not None

    def test_like_filter_sqlalchemy(self):
        """Test: LIKE filter to SQLAlchemy."""
        flt = FilterExpression("email", FilterOp.LIKE, "%@gmail.com")
        condition = flt.to_sqlalchemy()
        assert condition is not None

    def test_is_null_filter_sqlalchemy(self):
        """Test: IS_NULL filter to SQLAlchemy."""
        flt = FilterExpression("deleted_at", FilterOp.IS_NULL, None)
        condition = flt.to_sqlalchemy()
        assert condition is not None

    def test_combined_filters_sqlalchemy(self):
        """Test: Combined filters with FilterGroup."""
        combined = FilterGroup(
            operator="and",
            filters=[
                FilterExpression("tenant_id", FilterOp.EQ, "tenant_001"),
                FilterExpression("status", FilterOp.IN, ["active", "pending"]),
            ]
        )
        condition = combined.to_sqlalchemy()
        assert condition is not None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
