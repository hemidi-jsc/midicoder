"""
CP02: Multi-Tenant Architecture - Core Models.

Module này chứa các core models cho multi-tenant architecture theo SoT:
- TenantIsolationStrategy: Enum cho isolation strategies (database, schema, row, hybrid)
- TenantContext: Dataclass cho tenant context propagation
- TenantFilter: Class cho tenant-scoped queries

Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from sqlalchemy import ColumnElement
from sqlalchemy.sql import operators


# ============================================================================
# TenantIsolationStrategy Enum
# ============================================================================


class TenantIsolationStrategy(str, Enum):
    """
    Tenant Isolation Strategy - Chiến lược isolation cho multi-tenant.

    Theo SoT (E12 CP02), hỗ trợ 4 strategies:
    - DATABASE: Mỗi tenant có database riêng (strongest isolation)
    - SCHEMA: Mỗi tenant có schema riêng trong cùng database
    - ROW: Row-level isolation với tenant_id column (default)
    - HYBRID: Kết hợp row + schema cho performance

    Attributes:
        value: String value của strategy
    """

    DATABASE = "database"
    SCHEMA = "schema"
    ROW = "row"
    HYBRID = "hybrid"

    @classmethod
    def from_string(cls, strategy: str) -> "TenantIsolationStrategy":
        """
        Tạo TenantIsolationStrategy từ string.

        Args:
            strategy: Strategy string (case-insensitive)

        Returns:
            TenantIsolationStrategy instance

        Raises:
            ValueError: Nếu strategy không hợp lệ
        """
        strategy_lower = strategy.lower()

        for strategy_enum in cls:
            if strategy_enum.value.lower() == strategy_lower:
                return strategy_enum

        valid_strategies = [s.value for s in cls]
        raise ValueError(
            f"Invalid tenant isolation strategy: '{strategy}'. "
            f"Must be one of: {', '.join(valid_strategies)}"
        )


# ============================================================================
# TenantContext Dataclass
# ============================================================================


@dataclass
class TenantContext:
    """
    Tenant Context - Context cho tenant propagation.

    Class này đại diện cho context của tenant hiện tại trong request scope.
    Được dùng để propagate tenant information qua các layers.

    Attributes:
        tenant_id: Định danh duy nhất của tenant
        tenant_name: Tên display của tenant (optional)
        strategy: Isolation strategy đang dùng
        subdomain: Subdomain của tenant (nếu dùng subdomain routing)
    """

    tenant_id: str
    tenant_name: Optional[str] = None
    strategy: TenantIsolationStrategy = field(
        default=TenantIsolationStrategy.ROW
    )
    subdomain: Optional[str] = None

    @property
    def is_system_tenant(self) -> bool:
        """
        Kiểm tra nếu đây là system tenant.

        System tenant có tenant_id == "system".

        Returns:
            True nếu là system tenant, False nếu không
        """
        return self.tenant_id == "system"

    @property
    def is_super_tenant(self) -> bool:
        """
        Kiểm tra nếu đây là super tenant.

        Super tenant có tenant_id == "super" và có thể access nhiều tenants.

        Returns:
            True nếu là super tenant, False nếu không
        """
        return self.tenant_id == "super"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert TenantContext sang dict.

        Returns:
            Dict representation của TenantContext
        """
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "strategy": self.strategy.value,
            "subdomain": self.subdomain,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantContext":
        """
        Tạo TenantContext từ dict.

        Args:
            data: Dict với keys: tenant_id, tenant_name, strategy, subdomain

        Returns:
            TenantContext instance
        """
        strategy_value = data.get("strategy", "row")
        strategy = TenantIsolationStrategy.from_string(strategy_value)

        return cls(
            tenant_id=data["tenant_id"],
            tenant_name=data.get("tenant_name"),
            strategy=strategy,
            subdomain=data.get("subdomain"),
        )

    def __str__(self) -> str:
        """Return string representation của TenantContext."""
        parts = [f"tenant_id={self.tenant_id}"]

        if self.tenant_name:
            parts.append(f"tenant_name={self.tenant_name}")

        parts.append(f"strategy={self.strategy.value}")

        if self.subdomain:
            parts.append(f"subdomain={self.subdomain}")

        return f"TenantContext({', '.join(parts)})"

    def __eq__(self, other: object) -> bool:
        """Kiểm tra equality giữa 2 TenantContext."""
        if not isinstance(other, TenantContext):
            return False

        return (
            self.tenant_id == other.tenant_id
            and self.tenant_name == other.tenant_name
            and self.strategy == other.strategy
            and self.subdomain == other.subdomain
        )


# ============================================================================
# TenantFilter Class
# ============================================================================


@dataclass
class TenantFilter:
    """
    Tenant Filter - Filter cho tenant-scoped queries.

    Class này đại diện cho filter để scope queries về tenant hiện tại.
    Hỗ trợ row-level, schema-level, và cross-tenant filters.

    Attributes:
        tenant_id: Tenant ID để filter
        tenant_column: Column name cho row-level filter
        schema_name: Schema name cho schema-level filter
        tenant_ids: Danh sách tenant IDs cho cross-tenant filter
        filter_type: Loại filter (row, schema, cross_tenant)
    """

    tenant_id: str
    tenant_column: Optional[str] = None
    schema_name: Optional[str] = None
    tenant_ids: Optional[list[str]] = None
    filter_type: str = "row"

    @classmethod
    def create_row_filter(
        cls, tenant_id: str, tenant_column: str
    ) -> "TenantFilter":
        """
        Tạo row-level tenant filter.

        Args:
            tenant_id: Tenant ID để filter
            tenant_column: Column name trong table

        Returns:
            TenantFilter với filter_type="row"
        """
        return cls(
            tenant_id=tenant_id,
            tenant_column=tenant_column,
            filter_type="row",
        )

    @classmethod
    def create_schema_filter(
        cls, tenant_id: str, schema_name: str
    ) -> "TenantFilter":
        """
        Tạo schema-level tenant filter.

        Args:
            tenant_id: Tenant ID
            schema_name: Schema name để use

        Returns:
            TenantFilter với filter_type="schema"
        """
        return cls(
            tenant_id=tenant_id,
            schema_name=schema_name,
            filter_type="schema",
        )

    @classmethod
    def create_cross_tenant_filter(
        cls, tenant_ids: list[str], tenant_column: str
    ) -> "TenantFilter":
        """
        Tạo cross-tenant filter (multiple tenants).

        CHỈ DÙNG KHI CÓ EXPLICIT SCOPE cho cross-tenant operations.

        Args:
            tenant_ids: Danh sách tenant IDs để filter
            tenant_column: Column name trong table

        Returns:
            TenantFilter với filter_type="cross_tenant"
        """
        return cls(
            tenant_id=tenant_ids[0] if tenant_ids else "",
            tenant_column=tenant_column,
            tenant_ids=tenant_ids,
            filter_type="cross_tenant",
        )

    @classmethod
    def from_context(
        cls,
        context: TenantContext,
        tenant_column: Optional[str] = None,
        schema_name: Optional[str] = None,
    ) -> Optional["TenantFilter"]:
        """
        Tạo TenantFilter từ TenantContext.

        Args:
            context: TenantContext hiện tại
            tenant_column: Column name cho row-level filter
            schema_name: Schema name cho schema-level filter

        Returns:
            TenantFilter hoặc None nếu database strategy (separate connection)
        """
        if context.strategy == TenantIsolationStrategy.DATABASE:
            # Database strategy không cần filter (separate connection)
            return None

        if context.strategy == TenantIsolationStrategy.SCHEMA:
            return cls.create_schema_filter(
                tenant_id=context.tenant_id,
                schema_name=schema_name or f"{context.tenant_id}_schema",
            )

        if context.strategy == TenantIsolationStrategy.HYBRID:
            # Hybrid sử dụng row-level filter làm fallback
            if tenant_column:
                return cls.create_row_filter(
                    tenant_id=context.tenant_id,
                    tenant_column=tenant_column,
                )
            return None

        # Default: row-level
        if tenant_column:
            return cls.create_row_filter(
                tenant_id=context.tenant_id,
                tenant_column=tenant_column,
            )

        return None

    @property
    def is_cross_tenant(self) -> bool:
        """
        Kiểm tra nếu đây là cross-tenant filter.

        Returns:
            True nếu filter_type == "cross_tenant"
        """
        return self.filter_type == "cross_tenant"

    def to_sqlalchemy(
        self, column: Any
    ) -> Optional[ColumnElement[Any]]:
        """
        Convert TenantFilter sang SQLAlchemy filter.

        Args:
            column: SQLAlchemy column object

        Returns:
            SQLAlchemy filter hoặc None nếu schema/database strategy
        """
        if self.filter_type == "schema":
            # Schema filter không cần SQLAlchemy filter
            return None

        if self.filter_type == "cross_tenant" and self.tenant_ids:
            # Cross-tenant filter: tenant_id IN (...)
            return column.in_(self.tenant_ids)

        # Row-level filter: tenant_id = :value
        if column is not None:
            return column == self.tenant_id

        return None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert TenantFilter sang dict.

        Returns:
            Dict representation của TenantFilter
        """
        return {
            "tenant_id": self.tenant_id,
            "tenant_column": self.tenant_column,
            "schema_name": self.schema_name,
            "tenant_ids": self.tenant_ids,
            "filter_type": self.filter_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantFilter":
        """
        Tạo TenantFilter từ dict.

        Args:
            data: Dict với keys: tenant_id, tenant_column, schema_name, etc.

        Returns:
            TenantFilter instance
        """
        return cls(
            tenant_id=data["tenant_id"],
            tenant_column=data.get("tenant_column"),
            schema_name=data.get("schema_name"),
            tenant_ids=data.get("tenant_ids"),
            filter_type=data.get("filter_type", "row"),
        )