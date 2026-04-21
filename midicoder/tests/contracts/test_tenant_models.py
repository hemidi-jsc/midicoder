"""
Tests cho CP02: Multi-Tenant Architecture - Tenant Models.

Viết theo TDD, bám sát SoT (requirement.md - E12 CP02):
- Tenant isolation strategies (database, schema, row-level)
- Tenant context propagation
- Tenant-scoped queries
- Cross-tenant operations (controlled)

Không dùng mock, test với real implementations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.contracts.tenant_models import (
    TenantContext,
    TenantFilter,
    TenantIsolationStrategy,
)


# ============================================================================
# Test TenantIsolationStrategy Enum
# ============================================================================


class TestTenantIsolationStrategy:
    """Tests cho TenantIsolationStrategy enum theo SoT CP02."""

    def test_database_strategy_exists(self) -> None:
        """Kiểm tra database isolation strategy tồn tại."""
        assert hasattr(TenantIsolationStrategy, "DATABASE")
        assert TenantIsolationStrategy.DATABASE.value == "database"

    def test_schema_strategy_exists(self) -> None:
        """Kiểm tra schema isolation strategy tồn tại."""
        assert hasattr(TenantIsolationStrategy, "SCHEMA")
        assert TenantIsolationStrategy.SCHEMA.value == "schema"

    def test_row_strategy_exists(self) -> None:
        """Kiểm tra row-level isolation strategy tồn tại."""
        assert hasattr(TenantIsolationStrategy, "ROW")
        assert TenantIsolationStrategy.ROW.value == "row"

    def test_hybrid_strategy_exists(self) -> None:
        """Kiểm tra hybrid isolation strategy tồn tại."""
        assert hasattr(TenantIsolationStrategy, "HYBRID")
        assert TenantIsolationStrategy.HYBRID.value == "hybrid"

    def test_strategy_values_are_unique(self) -> None:
        """Kiểm tra tất cả strategy values đều unique."""
        values = [strategy.value for strategy in TenantIsolationStrategy]
        assert len(values) == len(set(values)), "Strategy values phải unique"

    def test_strategy_from_string(self) -> None:
        """Kiểm tra create strategy từ string."""
        # Test valid strings
        assert TenantIsolationStrategy.from_string("database") == TenantIsolationStrategy.DATABASE
        assert TenantIsolationStrategy.from_string("schema") == TenantIsolationStrategy.SCHEMA
        assert TenantIsolationStrategy.from_string("row") == TenantIsolationStrategy.ROW
        assert TenantIsolationStrategy.from_string("hybrid") == TenantIsolationStrategy.HYBRID

        # Test case-insensitive
        assert TenantIsolationStrategy.from_string("DATABASE") == TenantIsolationStrategy.DATABASE
        assert TenantIsolationStrategy.from_string("Row") == TenantIsolationStrategy.ROW

    def test_strategy_from_string_invalid(self) -> None:
        """Kiểm tra throw error khi string không hợp lệ."""
        with pytest.raises(ValueError) as exc_info:
            TenantIsolationStrategy.from_string("invalid_strategy")

        assert "invalid_strategy" in str(exc_info.value).lower()


# ============================================================================
# Test TenantContext Class
# ============================================================================


class TestTenantContext:
    """Tests cho TenantContext class theo SoT CP02."""

    def test_create_context_minimal(self) -> None:
        """Kiểm tra tạo context với minimal fields."""
        context = TenantContext(tenant_id="tenant-001")

        assert context.tenant_id == "tenant-001"
        assert context.tenant_name is None
        assert context.strategy == TenantIsolationStrategy.ROW  # Default

    def test_create_context_full(self) -> None:
        """Kiểm tra tạo context với đầy đủ fields."""
        context = TenantContext(
            tenant_id="tenant-001",
            tenant_name="Acme Corp",
            strategy=TenantIsolationStrategy.DATABASE,
        )

        assert context.tenant_id == "tenant-001"
        assert context.tenant_name == "Acme Corp"
        assert context.strategy == TenantIsolationStrategy.DATABASE

    def test_create_context_with_subdomain(self) -> None:
        """Kiểm tra tạo context với subdomain."""
        context = TenantContext(
            tenant_id="tenant-001",
            subdomain="acme",
        )

        assert context.tenant_id == "tenant-001"
        assert context.subdomain == "acme"

    def test_context_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        context = TenantContext(
            tenant_id="tenant-001",
            tenant_name="Acme Corp",
            strategy=TenantIsolationStrategy.SCHEMA,
            subdomain="acme",
        )

        context_dict = context.to_dict()

        assert context_dict["tenant_id"] == "tenant-001"
        assert context_dict["tenant_name"] == "Acme Corp"
        assert context_dict["strategy"] == "schema"
        assert context_dict["subdomain"] == "acme"

    def test_context_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        context_dict = {
            "tenant_id": "tenant-002",
            "tenant_name": "Globex Corp",
            "strategy": "database",
            "subdomain": "globex",
        }

        context = TenantContext.from_dict(context_dict)

        assert context.tenant_id == "tenant-002"
        assert context.tenant_name == "Globex Corp"
        assert context.strategy == TenantIsolationStrategy.DATABASE
        assert context.subdomain == "globex"

    def test_context_str_format(self) -> None:
        """Kiểm tra str format."""
        context = TenantContext(
            tenant_id="tenant-001",
            tenant_name="Acme Corp",
            strategy=TenantIsolationStrategy.ROW,
        )

        context_str = str(context)

        assert "tenant-001" in context_str
        assert "Acme Corp" in context_str
        assert "row" in context_str

    def test_context_equality(self) -> None:
        """Kiểm tra equality."""
        context1 = TenantContext(tenant_id="tenant-001", tenant_name="Acme")
        context2 = TenantContext(tenant_id="tenant-001", tenant_name="Acme")
        context3 = TenantContext(tenant_id="tenant-002", tenant_name="Acme")

        assert context1 == context2
        assert context1 != context3

    def test_context_is_system_tenant(self) -> None:
        """Kiểm tra system tenant detection."""
        system_context = TenantContext(tenant_id="system")
        regular_context = TenantContext(tenant_id="tenant-001")

        assert system_context.is_system_tenant is True
        assert regular_context.is_system_tenant is False

    def test_context_is_super_tenant(self) -> None:
        """Kiểm tra super tenant detection."""
        super_context = TenantContext(tenant_id="super")
        regular_context = TenantContext(tenant_id="tenant-001")

        assert super_context.is_super_tenant is True
        assert regular_context.is_super_tenant is False


# ============================================================================
# Test TenantFilter Class
# ============================================================================


class TestTenantFilter:
    """Tests cho TenantFilter class theo SoT CP02."""

    def test_create_row_filter(self) -> None:
        """Kiểm tra tạo row-level filter."""
        filter_obj = TenantFilter.create_row_filter(
            tenant_id="tenant-001",
            tenant_column="tenant_id",
        )

        assert filter_obj.tenant_id == "tenant-001"
        assert filter_obj.tenant_column == "tenant_id"
        assert filter_obj.filter_type == "row"

    def test_create_schema_filter(self) -> None:
        """Kiểm tra tạo schema-level filter."""
        filter_obj = TenantFilter.create_schema_filter(
            tenant_id="tenant-001",
            schema_name="tenant_001",
        )

        assert filter_obj.tenant_id == "tenant-001"
        assert filter_obj.schema_name == "tenant_001"
        assert filter_obj.filter_type == "schema"

    def test_filter_to_sqlalchemy_row(self) -> None:
        """Kiểm tra convert row filter sang SQLAlchemy."""
        filter_obj = TenantFilter.create_row_filter(
            tenant_id="tenant-001",
            tenant_column="tenant_id",
        )

        # Import để test
        from sqlalchemy import column

        sql_filter = filter_obj.to_sqlalchemy(column("tenant_id"))

        # Check filter structure
        assert sql_filter is not None

    def test_filter_to_sqlalchemy_schema(self) -> None:
        """Kiểm tra convert schema filter sang SQLAlchemy."""
        filter_obj = TenantFilter.create_schema_filter(
            tenant_id="tenant-001",
            schema_name="tenant_001",
        )

        # Schema filter không cần SQLAlchemy filter
        # (schema đã được set ở connection level)
        sql_filter = filter_obj.to_sqlalchemy(None)

        assert sql_filter is None

    def test_filter_is_cross_tenant(self) -> None:
        """Kiểm tra cross-tenant filter detection."""
        row_filter = TenantFilter.create_row_filter(
            tenant_id="tenant-001",
            tenant_column="tenant_id",
        )

        cross_tenant_filter = TenantFilter.create_cross_tenant_filter(
            tenant_ids=["tenant-001", "tenant-002"],
            tenant_column="tenant_id",
        )

        assert row_filter.is_cross_tenant is False
        assert cross_tenant_filter.is_cross_tenant is True

    def test_cross_tenant_filter_multiple_tenants(self) -> None:
        """Kiểm tra cross-tenant filter với multiple tenants."""
        filter_obj = TenantFilter.create_cross_tenant_filter(
            tenant_ids=["tenant-001", "tenant-002", "tenant-003"],
            tenant_column="tenant_id",
        )

        assert filter_obj.tenant_ids == ["tenant-001", "tenant-002", "tenant-003"]
        assert filter_obj.filter_type == "cross_tenant"

    def test_filter_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        filter_obj = TenantFilter.create_row_filter(
            tenant_id="tenant-001",
            tenant_column="tenant_id",
        )

        filter_dict = filter_obj.to_dict()

        assert filter_dict["tenant_id"] == "tenant-001"
        assert filter_dict["tenant_column"] == "tenant_id"
        assert filter_dict["filter_type"] == "row"

    def test_filter_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        filter_dict = {
            "tenant_id": "tenant-001",
            "tenant_column": "tenant_id",
            "filter_type": "row",
        }

        filter_obj = TenantFilter.from_dict(filter_dict)

        assert filter_obj.tenant_id == "tenant-001"
        assert filter_obj.tenant_column == "tenant_id"
        assert filter_obj.filter_type == "row"


# ============================================================================
# Test Integration: Context + Filter
# ============================================================================


class TestTenantIntegration:
    """Tests cho integration giữa TenantContext và TenantFilter."""

    def test_create_filter_from_context_row(self) -> None:
        """Kiểm tra tạo filter từ context (row strategy)."""
        context = TenantContext(
            tenant_id="tenant-001",
            strategy=TenantIsolationStrategy.ROW,
        )

        filter_obj = TenantFilter.from_context(context, tenant_column="tenant_id")

        assert filter_obj.tenant_id == "tenant-001"
        assert filter_obj.filter_type == "row"

    def test_create_filter_from_context_schema(self) -> None:
        """Kiểm tra tạo filter từ context (schema strategy)."""
        context = TenantContext(
            tenant_id="tenant-001",
            strategy=TenantIsolationStrategy.SCHEMA,
        )

        filter_obj = TenantFilter.from_context(context, schema_name="tenant_001")

        assert filter_obj.filter_type == "schema"

    def test_create_filter_from_context_database(self) -> None:
        """Kiểm tra tạo filter từ context (database strategy)."""
        context = TenantContext(
            tenant_id="tenant-001",
            strategy=TenantIsolationStrategy.DATABASE,
        )

        filter_obj = TenantFilter.from_context(context)

        # Database strategy không cần filter (separate connection)
        assert filter_obj is None

    def test_create_filter_from_context_hybrid(self) -> None:
        """Kiểm tra tạo filter từ context (hybrid strategy)."""
        context = TenantContext(
            tenant_id="tenant-001",
            strategy=TenantIsolationStrategy.HYBRID,
        )

        filter_obj = TenantFilter.from_context(context, tenant_column="tenant_id")

        # Hybrid sử dụng row-level filter làm fallback
        assert filter_obj is not None