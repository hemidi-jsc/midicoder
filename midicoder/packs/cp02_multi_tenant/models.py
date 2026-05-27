# coding: utf-8
"""
Mô-đun models cho CP02 Multi-Tenant Architecture Generator.

Định nghĩa các dataclass biểu diễn:
- TenantMode: Enum các chiều cách tenant isolation (schema/row/subdomain)
- TenantConfig: Cấu hình tenant cho ứng dụng
- TenantContext: Context tenant trong request
- TenantResolver: Giải thích tenant ID từ các nguồn khác nhau

KPI-029: Tenant Isolation - bắt buộc cho tất cả operations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# TenantMode Enum
# ===========================================================================


class TenantIsolationStrategy(str, Enum):
    """
    Chiến lược tenant isolation (physical separation).

    - ROW: Shared schema, row-level filter bằng tenant_id column
    - SCHEMA: Mỗi tenant có PostgreSQL schema riêng
    - DATABASE: Mỗi tenant có database riêng (strongest isolation)
    - HYBRID: Mix of above (vd: system tenant dùng shared, others dùng dedicated)

    Đây là enum chính — dùng trong templates và contracts.
    TenantMode là alias layer (SUBDOMAIN = discovery method, không phải isolation).
    """
    ROW = "row"
    SCHEMA = "schema"
    DATABASE = "database"
    HYBRID = "hybrid"


class TenantMode(str, Enum):
    """
    Enum các cách tenant isolation (legacy alias, map sang TenantIsolationStrategy).

    - SCHEMA: Mỗi tenant có PostgreSQL schema riêng
    - ROW: Tất cả tenant chia cùng bảng, phân biệt bằng tenant_id column
    - SUBDOMAIN: Mỗi tenant có subdomain riêng (tenant1.app.com) — discovery method

    Deprecated: dùng TenantIsolationStrategy cho isolation, subdomain là discovery.
    """
    SCHEMA = "schema"
    ROW = "row"
    SUBDOMAIN = "subdomain"

    @property
    def isolation_strategy(self) -> TenantIsolationStrategy:
        """Map TenantMode → TenantIsolationStrategy."""
        mapping = {
            TenantMode.SCHEMA: TenantIsolationStrategy.SCHEMA,
            TenantMode.ROW: TenantIsolationStrategy.ROW,
            TenantMode.SUBDOMAIN: TenantIsolationStrategy.ROW,
        }
        return mapping[self]


# ===========================================================================
# TenantConfig
# ===========================================================================


@dataclass
class TenantConfig:
    """
    Cấu hình tenant cho ứng dụng.

    Attributes:
        mode: Cách tenant isolation (SCHEMA, ROW, SUBDOMAIN)
        tenant_id_column: Tên column chứa tenant ID (cho ROW mode)
        default_tenant_id: Tenant ID mặc định cho requests không có tenant
        schema_prefix: Prefix cho schema names (cho SCHEMA mode)
        domain: Domain cuối cùng (cho SUBDOMAIN mode)
        cache_ttl: Thời gian cache tenant resolution (giây)
    """
    mode: TenantMode
    tenant_id_column: str = "tenant_id"
    default_tenant_id: str = "default"
    schema_prefix: str = "tenant_"
    domain: str = ""
    cache_ttl: int = 300

    def __post_init__(self) -> None:
        """Validate tenant config sau khi khoi tao."""
        # Kiểm tra tenant_id_column không được để trống cho ROW mode
        if self.mode == TenantMode.ROW and not self.tenant_id_column.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_FILTER_MISSING,
                mode=self.mode.value,
                message="tenant_id_column không được để trống cho ROW mode"
            )
        # Kiểm tra domain không được để trống cho SUBDOMAIN mode
        if self.mode == TenantMode.SUBDOMAIN and not self.domain.strip():
            EM.raise_error(
                ErrorCode.CP02_TENANT_MODE_INVALID,
                mode=self.mode.value,
                message="domain không được để trống cho SUBDOMAIN mode"
            )
        # Cache ttl phải >= 0
        if self.cache_ttl < 0:
            self.cache_ttl = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant config sang dict format."""
        return {
            "mode": self.mode.value,
            "tenant_id_column": self.tenant_id_column,
            "default_tenant_id": self.default_tenant_id,
            "schema_prefix": self.schema_prefix,
            "domain": self.domain,
            "cache_ttl": self.cache_ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantConfig":
        """Tạo TenantConfig từ dict."""
        return cls(
            mode=TenantMode(data.get("mode", "row")),
            tenant_id_column=data.get("tenant_id_column", "tenant_id"),
            default_tenant_id=data.get("default_tenant_id", "default"),
            schema_prefix=data.get("schema_prefix", "tenant_"),
            domain=data.get("domain", ""),
            cache_ttl=data.get("cache_ttl", 300),
        )


# ===========================================================================
# TenantContext
# ===========================================================================


@dataclass
class TenantContext:
    """
    Context tenant trong request.

    Lưu trữ thông tin tenant hiện tại trong request context.
    Được sử dụng để enforce tenant isolation cho tất cả operations.

    Attributes:
        tenant_id: Tenant ID hiện tại
        user_id: User ID hiện tại (optional)
        mode: Cách tenant isolation
        headers: Request headers (optional, cho debugging)
    """
    tenant_id: str | None
    user_id: str | None = None
    mode: TenantMode = TenantMode.ROW
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tenant context sau khi khoi tao."""
        # Tenant ID không được để trống hoặc None
        if not self.tenant_id:
            EM.raise_error(
                ErrorCode.CP02_TENANT_ID_MISSING,
                user_id=self.user_id,
                mode=self.mode.value,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant context sang dict format."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "mode": self.mode.value,
            "headers": self.headers,
        }


# ===========================================================================
# TenantResolver
# ===========================================================================


@dataclass
class TenantResolver:
    """
    Giải thích tenant ID từ các nguồn khác nhau.

    Thực hiện logic để xác định tenant ID từ:
    1. Request header (X-Tenant-ID)
    2. JWT claims (tenant_id claim)
    3. Subdomain (tenant.app.com)
    4. Default tenant id

    Thứ tự ưu tiên: Header > JWT > Subdomain > Default

    Attributes:
        domain: Domain cuối cùng để extract subdomain (cho SUBDOMAIN mode)
        default_tenant_id: Tenant ID mặc định nếu không tìm thấy
        _cache: Cache đã resolve tenant IDs
    """
    domain: str = ""
    default_tenant_id: str = "default"
    _cache: dict[str, str] = field(default_factory=dict, repr=False)

    def resolve(
        self,
        headers: dict[str, str] | None = None,
        jwt_claims: dict[str, Any] | None = None,
        host: str = "",
    ) -> str:
        """
        Resolve tenant ID từ các nguồn khác nhau.

        Thứ tự ưu tiên:
        1. Request header (X-Tenant-ID)
        2. JWT claims (tenant_id)
        3. Subdomain (nếu có domain)
        4. Default tenant ID

        Args:
            headers: Request headers
            jwt_claims: JWT claims
            host: Host header (cho subdomain resolution)

        Returns:
            Tenant ID đã resolve

        Raises:
            MidicoderError: Nếu không thể resolve tenant ID (MDC-CP02-002)
        """
        headers = headers or {}
        jwt_claims = jwt_claims or {}

        # 1. Kiểm tra cache trước
        cache_key = f"{headers.get('X-Tenant-ID', '')}:{host}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        tenant_id: str = ""

        # 2. Resolve từ header (ưu tiên nhất)
        if not tenant_id:
            tenant_id = headers.get("X-Tenant-ID", "")

        # 3. Resolve từ JWT claims
        if not tenant_id:
            tenant_id = jwt_claims.get("tenant_id", "")

        # 4. Resolve từ subdomain
        if not tenant_id and self.domain and host:
            tenant_id = self._extract_subdomain(host)

        # 5. Nếu vẫn không có, throw error
        if not tenant_id:
            EM.raise_error(
                ErrorCode.CP02_TENANT_ID_MISSING,
                headers_provided=bool(headers),
                jwt_provided=bool(jwt_claims),
                host=host,
            )

        # Cache kết quả
        self._cache[cache_key] = tenant_id
        return tenant_id

    def _extract_subdomain(self, host: str) -> str:
        """
        Extract subdomain từ host.

        Ví dụ:
            - "tenant1.app.example.com" với domain="app.example.com" -> "tenant1"
            - "app.example.com" với domain="app.example.com" -> ""

        Args:
            host: Host header

        Returns:
            Subdomain hoặc string rỗng nếu không tìm thấy
        """
        if not self.domain or not host:
            return ""

        # Loại bỏ port nếu có
        host_clean = host.split(":")[0]
        domain_clean = self.domain.split(":")[0]

        # Kiểm tra host có kết thúc bằng domain không
        if host_clean.endswith("." + domain_clean):
            subdomain = host_clean[:-(len(domain_clean) + 1)]
            return subdomain

        return ""

    def clear_cache(self) -> None:
        """Xóa cache tenant resolutions."""
        self._cache.clear()


# ===========================================================================
# Schema-Level Isolation
# ===========================================================================


class SchemaIsolationMode(str, Enum):
    """
    Chiều cách schema-level isolation.

    - dedicated_schema: Mỗi tenant có PostgreSQL schema riêng
    - dedicated_database: Mỗi tenant có database riêng (strongest isolation)
    - shared_schema: Tất cả tenant chia schema (row-level isolation)
    """
    DEDICATED_SCHEMA = "dedicated_schema"
    DEDICATED_DATABASE = "dedicated_database"
    SHARED_SCHEMA = "shared_schema"


@dataclass
class SchemaIsolationConfig:
    """
    Configuration cho schema-level isolation — tenant data separation ở database level.

    Attributes:
        isolation_mode: Mode isolation (dedicated_schema, dedicated_database, shared_schema)
        schema_prefix: Prefix cho schema/database names (vd: "t_")
        create_on_first_access: Có auto-create schema/database khi tenant mới không
        seed_data: Có seed initial data khi create schema không
        migration_strategy: Migration strategy (flyway, alembic, raw_sql)
        max_tenants_per_db: Số tenants tối đa trên 1 database (cho dedicated_schema)
        enable_row_level_security: Có enable RLS PostgreSQL không (extra layer)
        description: Mô tả schema isolation config
    """
    isolation_mode: SchemaIsolationMode = SchemaIsolationMode.DEDICATED_SCHEMA
    schema_prefix: str = "t_"
    create_on_first_access: bool = True
    seed_data: bool = True
    migration_strategy: str = "alembic"
    max_tenants_per_db: int = 1000
    enable_row_level_security: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate schema isolation config sau khi khởi tạo."""
        if not self.schema_prefix:
            self.schema_prefix = "t_"
        if self.max_tenants_per_db < 1:
            self.max_tenants_per_db = 1000

    def to_dict(self) -> dict[str, Any]:
        """Chuyển schema isolation config sang dict."""
        return {
            "isolation_mode": self.isolation_mode.value,
            "schema_prefix": self.schema_prefix,
            "create_on_first_access": self.create_on_first_access,
            "seed_data": self.seed_data,
            "migration_strategy": self.migration_strategy,
            "max_tenants_per_db": self.max_tenants_per_db,
            "enable_row_level_security": self.enable_row_level_security,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaIsolationConfig":
        """Tạo SchemaIsolationConfig từ dict."""
        return cls(
            isolation_mode=SchemaIsolationMode(data.get("isolation_mode", "dedicated_schema")),
            schema_prefix=data.get("schema_prefix", "t_"),
            create_on_first_access=data.get("create_on_first_access", True),
            seed_data=data.get("seed_data", True),
            migration_strategy=data.get("migration_strategy", "alembic"),
            max_tenants_per_db=data.get("max_tenants_per_db", 1000),
            enable_row_level_security=data.get("enable_row_level_security", False),
            description=data.get("description", ""),
        )


# ===========================================================================
# Tenant Provisioning
# ===========================================================================


class ProvisioningStrategy(str, Enum):
    """
    Chiến lược provisioning cho tenant mới.

    - automatic: Auto-create schema/database, seed data, assign defaults
    - manual_review: Create skeleton, require manual approval trước khi active
    - api_driven: Provision qua REST API, trigger CI/CD pipeline
    - terraform: Provision qua Terraform/IaC
    """
    AUTOMATIC = "automatic"
    MANUAL_REVIEW = "manual_review"
    API_DRIVEN = "api_driven"
    TERRAFORM = "terraform"


class TenantStatus(str, Enum):
    """
    Trạng thái tenant.

    - provisioning: Đang provisioning resources
    - active: Active, tenant có thể sử dụng
    - suspended: Suspended, tenant không thể access
    - deleted: Deleted, resources đang cleanup
    """
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class TenantProvisioningConfig:
    """
    Configuration cho tenant provisioning — auto-create tenant resources.

    Attributes:
        strategy: Provisioning strategy (automatic, manual_review, api_driven, terraform)
        default_plan: Plan mặc định (free, starter, pro, enterprise)
        default_features: Features mặc định
        resource_limits: Resource limits (storage_gb, api_calls_per_month, max_users)
        auto_activate: Có auto-activate tenant sau khi provision không
        notification_email: Email notify admin khi tenant mới được provision
        description: Mô tả provisioning config
    """
    strategy: ProvisioningStrategy = ProvisioningStrategy.AUTOMATIC
    default_plan: str = "starter"
    default_features: list[str] = field(default_factory=lambda: ["basic_api", "dashboard"])
    resource_limits: dict[str, Any] = field(default_factory=lambda: {
        "storage_gb": 10,
        "api_calls_per_month": 100000,
        "max_users": 50,
    })
    auto_activate: bool = True
    notification_email: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate provisioning config sau khi khởi tạo."""
        if not self.default_features:
            self.default_features = ["basic_api", "dashboard"]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển provisioning config sang dict."""
        return {
            "strategy": self.strategy.value,
            "default_plan": self.default_plan,
            "default_features": self.default_features,
            "resource_limits": self.resource_limits,
            "auto_activate": self.auto_activate,
            "notification_email": self.notification_email,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantProvisioningConfig":
        """Tạo TenantProvisioningConfig từ dict."""
        return cls(
            strategy=ProvisioningStrategy(data.get("strategy", "automatic")),
            default_plan=data.get("default_plan", "starter"),
            default_features=data.get("default_features", ["basic_api", "dashboard"]),
            resource_limits=data.get("resource_limits", {"storage_gb": 10, "api_calls_per_month": 100000, "max_users": 50}),
            auto_activate=data.get("auto_activate", True),
            notification_email=data.get("notification_email", ""),
            description=data.get("description", ""),
        )


# ===========================================================================
# TenantFilter
# ===========================================================================


@dataclass
class TenantFilter:
    """
    Filter tenant cho query — apply tenant boundary.

    Attributes:
        tenant_id: Tenant ID để filter
        tenant_column: Column name để filter (default: "tenant_id")
        filter_type: Type filter (row, schema, database)
    """
    tenant_id: str
    tenant_column: str = "tenant_id"
    filter_type: str = "row"

    @classmethod
    def create_row_filter(
        cls,
        tenant_id: str,
        tenant_column: str = "tenant_id",
    ) -> "TenantFilter":
        """Tạo row-level tenant filter."""
        return cls(tenant_id=tenant_id, tenant_column=tenant_column, filter_type="row")

    @classmethod
    def create_schema_filter(
        cls,
        tenant_id: str,
        schema_name: str = "",
    ) -> "TenantFilter":
        """Tạo schema-level tenant filter."""
        return cls(tenant_id=tenant_id, tenant_column=schema_name, filter_type="schema")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant filter sang dict."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_column": self.tenant_column,
            "filter_type": self.filter_type,
        }


# ===========================================================================
# Cross-Tenant Access


@dataclass
class CrossTenantAccessRule:
    """
    Rule cho phép cross-tenant data access (rare, strict control).

    Dùng khi tenant A cần read data từ tenant B (vd: service provider,
    platform admin, data sharing agreement).

    Attributes:
        source_tenant: Tenant ID của source (đọc data)
        target_tenant: Tenant ID của target (bị đọc)
        allowed_entities: Entities được phép access (vd: ["orders", "users"])
        read_only: Có chỉ đọc không (không write)
        requires_approval: Có cần approval không
        expires_at: Thời điểm rule hết hiệu lực
        description: Mô tả rule
    """
    source_tenant: str
    target_tenant: str
    allowed_entities: list[str] = field(default_factory=lambda: ["orders"])
    read_only: bool = True
    requires_approval: bool = True
    expires_at: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển cross-tenant rule sang dict."""
        return {
            "source_tenant": self.source_tenant,
            "target_tenant": self.target_tenant,
            "allowed_entities": self.allowed_entities,
            "read_only": self.read_only,
            "requires_approval": self.requires_approval,
            "expires_at": self.expires_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CrossTenantAccessRule":
        """Tạo CrossTenantAccessRule từ dict."""
        return cls(
            source_tenant=data.get("source_tenant", ""),
            target_tenant=data.get("target_tenant", ""),
            allowed_entities=data.get("allowed_entities", ["orders"]),
            read_only=data.get("read_only", True),
            requires_approval=data.get("requires_approval", True),
            expires_at=data.get("expires_at", ""),
            description=data.get("description", ""),
        )