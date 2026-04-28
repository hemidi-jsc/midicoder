"""
Query Models Module.

Module này định nghĩa các models cho Query DSL:
- Query: Main query model với input params, filters, pagination, projection, sort
- AggregationQuery: Query model cho aggregation (COUNT, SUM, AVG, GROUP BY)
- Enums: FilterOp, PaginationType, SortDirection, AggFunction
- Dataclasses: QueryField, QueryGuard, QueryEffect, FilterExpression, SortExpression

Theo SoT E03, authorized_query pattern:
- authorize_permission
- enforce_tenant_scope
- query_records

Theo SoT E06, verification rules:
- Every authorized_query must have enforce_tenant_scope
- Query must filter by tenant_id
- No cross-tenant data access without explicit cross_tenant scope

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# Enums
# ============================================================================


class FilterOp(str, Enum):
    """
    Filter operators cho Query.
    
    Supports 13 operators:
    - Comparison: eq, ne, gt, gte, lt, lte
    - Membership: in, not_in
    - Pattern: like, ilike
    - Range: between
    - Null check: is_null, is_not_null
    """
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class PaginationType(str, Enum):
    """
    Pagination types cho Query.
    
    - OFFSET: Page-based pagination (page, page_size)
    - CURSOR: Cursor-based pagination (cursor, limit)
    """
    OFFSET = "offset"
    CURSOR = "cursor"


class SortDirection(str, Enum):
    """
    Sort direction cho Query.
    
    - ASC: Ascending (tăng dần)
    - DESC: Descending (giảm dần)
    """
    ASC = "asc"
    DESC = "desc"


class AggFunction(str, Enum):
    """
    Aggregation functions cho Query.
    
    - COUNT: Đếm số lượng records
    - SUM: Tổng giá trị
    - AVG: Trung bình
    - MIN: Giá trị nhỏ nhất
    - MAX: Giá trị lớn nhất
    """
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class QueryGuardType(str, Enum):
    """
    Guard types cho Query.
    
    Theo SoT E06:
    - AUTH: Permission check (authorize_permission)
    - TENANT_SCOPE: Tenant isolation (enforce_tenant_scope)
    """
    AUTH = "auth"
    TENANT_SCOPE = "tenant_scope"


class QueryEffectType(str, Enum):
    """
    Effect types cho Query (subset of Command effects).
    
    Theo clarification Q1:
    - WRITE_AUDIT_LOG: Audit trail (RX11: Immutable Audit Evidence)
    - RECORD_METRIC: Metrics (CP15: Observability)
    """
    WRITE_AUDIT_LOG = "write_audit_log"
    RECORD_METRIC = "record_metric"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class QueryField:
    """
    Query input field definition.
    
    Attributes:
        name: Tên field
        field_type: Type của field (str, int, uuid, etc.)
        required: Có bắt buộc không
        description: Mô tả field
        default: Giá trị mặc định (optional)
    """
    name: str
    field_type: str
    required: bool = False
    description: str = ""
    default: Any = None


@dataclass
class QueryGuard:
    """
    Query guard definition.
    
    Attributes:
        guard_type: Loại guard (AUTH, TENANT_SCOPE)
        permission: Permission cho AUTH guard (optional)
        mode: Mode cho TENANT_SCOPE (tenant_isolated, cross_tenant)
    """
    guard_type: QueryGuardType
    permission: str | None = None
    mode: str = "tenant_isolated"


@dataclass
class QueryEffect:
    """
    Query effect definition.
    
    Attributes:
        effect_type: Loại effect (WRITE_AUDIT_LOG, RECORD_METRIC)
        audit_action: Audit action name (cho WRITE_AUDIT_LOG)
        metric_name: Metric name (cho RECORD_METRIC)
        metric_value: Metric value (cho RECORD_METRIC)
    """
    effect_type: QueryEffectType
    audit_action: str | None = None
    metric_name: str | None = None
    metric_value: float = 1.0


@dataclass
class FilterExpression:
    """
    Filter expression cho Query.
    
    Attributes:
        field: Tên field cần filter
        operator: Operator (FilterOp enum)
        value: Giá trị để so sánh
    """
    field: str
    operator: FilterOp
    value: Any

    def to_sqlalchemy(self) -> Any:
        """
        Chuyển filter expression sang SQLAlchemy condition.
        
        Returns:
            SQLAlchemy condition expression
        """
        from sqlalchemy import column

        col = column(self.field)

        if self.operator == FilterOp.EQ:
            return col == self.value
        elif self.operator == FilterOp.NE:
            return col != self.value
        elif self.operator == FilterOp.GT:
            return col > self.value
        elif self.operator == FilterOp.GTE:
            return col >= self.value
        elif self.operator == FilterOp.LT:
            return col < self.value
        elif self.operator == FilterOp.LTE:
            return col <= self.value
        elif self.operator == FilterOp.IN:
            return col.in_(self.value)
        elif self.operator == FilterOp.NOT_IN:
            return col.notin_(self.value)
        elif self.operator == FilterOp.LIKE:
            return col.like(self.value)
        elif self.operator == FilterOp.ILIKE:
            return col.ilike(self.value)
        elif self.operator == FilterOp.BETWEEN:
            return col.between(self.value[0], self.value[1])
        elif self.operator == FilterOp.IS_NULL:
            return col.is_(None)
        elif self.operator == FilterOp.IS_NOT_NULL:
            return col.isnot(None)
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class SortExpression:
    """
    Sort expression cho Query (multi-field support).
    
    Attributes:
        field: Tên field cần sort
        direction: Sort direction (ASC/DESC)
    """
    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class PaginationConfig:
    """
    Pagination configuration cho Query.
    
    Attributes:
        type: Loại pagination (OFFSET/CURSOR)
        page_size: Số records mỗi page (cho OFFSET)
        page: Page number (cho OFFSET)
        offset: Offset (cho OFFSET)
        limit: Limit records (cho CURSOR)
        cursor: Cursor string (cho CURSOR)
    """
    type: PaginationType = PaginationType.OFFSET
    page_size: int = 20
    page: int = 1
    offset: int = 0
    limit: int = 20
    cursor: str | None = None

    def __post_init__(self) -> None:
        """Validate và tính toán offset từ page."""
        if self.type == PaginationType.OFFSET and self.offset == 0 and self.page > 1:
            self.offset = (self.page - 1) * self.page_size


@dataclass
class ProjectionConfig:
    """
    Projection configuration cho Query (field selection).
    
    Attributes:
        include: Danh sách fields cần include
        exclude: Danh sách fields cần exclude
    """
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def get_sensitive_fields_to_exclude(self) -> list[str]:
        """
        Lấy danh sách sensitive fields cần exclude tự động.
        
        Returns:
            Danh sách sensitive field names
        """
        return [
            "password", "secret_key", "token", "api_key",
            "private_key", "credential", "auth_token"
        ]


@dataclass
class AggregationConfig:
    """
    Aggregation configuration cho Query.
    
    Attributes:
        function: Aggregation function (COUNT, SUM, AVG, MIN, MAX)
        agg_field: Field để aggregate (None cho COUNT)
        group_by: Danh sách fields để group by
    """
    function: AggFunction
    agg_field: str | None = None
    group_by: list[str] = field(default_factory=list)


# ============================================================================
# Query Models
# ============================================================================


@dataclass
class Query:
    """
    Query model cho CP01 Domain Model DSL.
    
    Theo SoT E03, authorized_query pattern:
    - authorize_permission (AUTH guard)
    - enforce_tenant_scope (TENANT_SCOPE guard)
    - query_records
    
    Theo SoT E06:
    - Every authorized_query must have enforce_tenant_scope
    - Query must filter by tenant_id
    
    Attributes:
        id: Query ID (PascalCase, ví dụ: GetOrder)
        description: Mô tả query
        reads_from: Entity mà query đọc từ
        input: Danh sách input fields
        filters: Danh sách filter expressions
        pagination: Pagination configuration
        projection: Projection configuration
        sort: Danh sách sort expressions (multi-field)
        guards: Danh sách query guards
        effects: Danh sách query effects
    """
    id: str
    description: str
    reads_from: str
    input: list[QueryField] = field(default_factory=list)
    filters: list[FilterExpression] = field(default_factory=list)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    projection: ProjectionConfig = field(default_factory=ProjectionConfig)
    sort: list[SortExpression] = field(default_factory=list)
    guards: list[QueryGuard] = field(default_factory=list)
    effects: list[QueryEffect] = field(default_factory=list)

    def has_auth_guard(self) -> bool:
        """
        Kiểm tra query có AUTH guard không.
        
        Returns:
            True nếu có AUTH guard
        """
        return any(g.guard_type == QueryGuardType.AUTH for g in self.guards)

    def has_tenant_guard(self) -> bool:
        """
        Kiểm tra query có TENANT_SCOPE guard không.
        
        Returns:
            True nếu có TENANT_SCOPE guard
        """
        return any(g.guard_type == QueryGuardType.TENANT_SCOPE for g in self.guards)

    def has_audit_effects(self) -> bool:
        """
        Kiểm tra query có audit effects không.
        
        Returns:
            True nếu có WRITE_AUDIT_LOG effect
        """
        return any(
            e.effect_type == QueryEffectType.WRITE_AUDIT_LOG
            for e in self.effects
        )

    def get_required_permissions(self) -> list[str]:
        """
        Lấy danh sách required permissions từ AUTH guards.
        
        Returns:
            Danh sách permission strings
        """
        return [
            g.permission for g in self.guards
            if g.guard_type == QueryGuardType.AUTH and g.permission
        ]

    def get_audit_actions(self) -> list[str]:
        """
        Lấy danh sách audit actions từ effects.
        
        Returns:
            Danh sách audit action names
        """
        return [
            e.audit_action for e in self.effects
            if e.effect_type == QueryEffectType.WRITE_AUDIT_LOG and e.audit_action
        ]

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển query sang dict.
        
        Returns:
            Dictionary representation của query
        """
        return {
            "id": self.id,
            "description": self.description,
            "reads_from": self.reads_from,
            "input": [
                {
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "description": f.description,
                    "default": f.default,
                }
                for f in self.input
            ],
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator.value,
                    "value": f.value,
                }
                for f in self.filters
            ],
            "pagination": {
                "type": self.pagination.type.value,
                "page_size": self.pagination.page_size,
                "page": self.pagination.page,
                "offset": self.pagination.offset,
                "limit": self.pagination.limit,
                "cursor": self.pagination.cursor,
            },
            "projection": {
                "include": self.projection.include,
                "exclude": self.projection.exclude,
            },
            "sort": [
                {
                    "field": s.field,
                    "direction": s.direction.value,
                }
                for s in self.sort
            ],
            "guards": [
                {
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "mode": g.mode,
                }
                for g in self.guards
            ],
            "effects": [
                {
                    "effect_type": e.effect_type.value,
                    "audit_action": e.audit_action,
                    "metric_name": e.metric_name,
                    "metric_value": e.metric_value,
                }
                for e in self.effects
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Query":
        """
        Tạo Query từ dict.
        
        Args:
            data: Dictionary với query data
            
        Returns:
            Query instance
        """
        # Parse input fields
        input_fields = [
            QueryField(
                name=f["name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                default=f.get("default"),
            )
            for f in data.get("input", [])
        ]

        # Parse filters
        filters = [
            FilterExpression(
                field=f["field"],
                operator=FilterOp(f["operator"]),
                value=f["value"],
            )
            for f in data.get("filters", [])
        ]

        # Parse pagination
        pagination_data = data.get("pagination", {})
        pagination = PaginationConfig(
            type=PaginationType(pagination_data.get("type", "offset")),
            page_size=pagination_data.get("page_size", 20),
            page=pagination_data.get("page", 1),
            offset=pagination_data.get("offset", 0),
            limit=pagination_data.get("limit", 20),
            cursor=pagination_data.get("cursor"),
        )

        # Parse projection
        projection_data = data.get("projection", {})
        projection = ProjectionConfig(
            include=projection_data.get("include", []),
            exclude=projection_data.get("exclude", []),
        )

        # Parse sort
        sort = [
            SortExpression(
                field=s["field"],
                direction=SortDirection(s.get("direction", "asc")),
            )
            for s in data.get("sort", [])
        ]

        # Parse guards
        guards = [
            QueryGuard(
                guard_type=QueryGuardType(g["guard_type"]),
                permission=g.get("permission"),
                mode=g.get("mode", "tenant_isolated"),
            )
            for g in data.get("guards", [])
        ]

        # Parse effects
        effects = [
            QueryEffect(
                effect_type=QueryEffectType(e["effect_type"]),
                audit_action=e.get("audit_action"),
                metric_name=e.get("metric_name"),
                metric_value=e.get("metric_value", 1.0),
            )
            for e in data.get("effects", [])
        ]

        return cls(
            id=data["id"],
            description=data["description"],
            reads_from=data["reads_from"],
            input=input_fields,
            filters=filters,
            pagination=pagination,
            projection=projection,
            sort=sort,
            guards=guards,
            effects=effects,
        )


@dataclass
class AggregationQuery:
    """
    Aggregation Query model cho COUNT, SUM, AVG, GROUP BY.
    
    Theo clarification Q4: Cần full aggregation model.
    
    Attributes:
        id: Query ID (PascalCase, ví dụ: CountOrders)
        description: Mô tả query
        reads_from: Entity mà query đọc từ
        aggregation: Aggregation configuration
        filters: Danh sách filter expressions (before aggregation)
        pagination: Pagination configuration
        guards: Danh sách query guards
        effects: Danh sách query effects
    """
    id: str
    description: str
    reads_from: str
    aggregation: AggregationConfig
    filters: list[FilterExpression] = field(default_factory=list)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    guards: list[QueryGuard] = field(default_factory=list)
    effects: list[QueryEffect] = field(default_factory=list)

    def has_auth_guard(self) -> bool:
        """Kiểm tra aggregation query có AUTH guard không."""
        return any(g.guard_type == QueryGuardType.AUTH for g in self.guards)

    def has_tenant_guard(self) -> bool:
        """Kiểm tra aggregation query có TENANT_SCOPE guard không."""
        return any(g.guard_type == QueryGuardType.TENANT_SCOPE for g in self.guards)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển aggregation query sang dict.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "reads_from": self.reads_from,
            "aggregation": {
                "function": self.aggregation.function.value,
                "field": self.aggregation.agg_field,
                "group_by": self.aggregation.group_by,
            },
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator.value,
                    "value": f.value,
                }
                for f in self.filters
            ],
            "pagination": {
                "type": self.pagination.type.value,
                "page_size": self.pagination.page_size,
                "page": self.pagination.page,
                "offset": self.pagination.offset,
            },
            "guards": [
                {
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "mode": g.mode,
                }
                for g in self.guards
            ],
            "effects": [
                {
                    "effect_type": e.effect_type.value,
                    "audit_action": e.audit_action,
                }
                for e in self.effects
            ],
        }


# ============================================================================
# Exports
# ============================================================================

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
    "SortExpression",
    "PaginationConfig",
    "ProjectionConfig",
    "AggregationConfig",
    # Query models
    "Query",
    "AggregationQuery",
]