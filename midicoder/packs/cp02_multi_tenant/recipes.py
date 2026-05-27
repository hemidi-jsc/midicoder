# coding: utf-8
"""
Recipes cho CP02 Multi-Tenant Architecture Generator.

Mỗi recipe là một cách gán giá trị cụ thể vào pattern vocabulary —
không phải domain-specific macro, không nested recipe.

Recipe = 1 level duy nhất, call direct tới patterns.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp02_multi_tenant.models import (
    TenantMode,
    TenantConfig,
    SchemaIsolationMode,
    SchemaIsolationConfig,
    ProvisioningStrategy,
    TenantProvisioningConfig,
    CrossTenantAccessRule,
)


# ===========================================================================
# Row-Level Isolation Recipe
# ===========================================================================


def row_level_tenant_recipe(
    tenant_id_column: str = "tenant_id",
    cache_ttl: int = 300,
) -> TenantConfig:
    """
    Recipe cho row-level isolation — chi phí thấp, phù hợp SaaS scale.

    Tất cả tenant chia cùng bảng, phân biệt bằng tenant_id column.
    Đây là strategy phổ biến nhất cho SaaS.

    Args:
        tenant_id_column: Tên column chứa tenant ID
        cache_ttl: Thời gian cache tenant resolution (giây)

    Returns:
        TenantConfig đã được cấu hình sẵn
    """
    return TenantConfig(
        mode=TenantMode.ROW,
        tenant_id_column=tenant_id_column,
        cache_ttl=cache_ttl,
    )


# ===========================================================================
# Schema-Level Isolation Recipe
# ===========================================================================


def schema_level_tenant_recipe(
    schema_prefix: str = "t_",
    enable_rls: bool = False,
) -> tuple[TenantConfig, SchemaIsolationConfig]:
    """
    Recipe cho schema-level isolation — compliance, medium-tier SaaS.

    Mỗi tenant có PostgreSQL schema riêng, chia cùng database.
    Tùy chọn enable Row-Level Security (RLS) làm extra layer.

    Args:
        schema_prefix: Prefix cho schema names
        enable_rls: Có enable PostgreSQL RLS không

    Returns:
        Tuple[TenantConfig, SchemaIsolationConfig]
    """
    config = TenantConfig(
        mode=TenantMode.SCHEMA,
        schema_prefix=schema_prefix,
    )
    isolation = SchemaIsolationConfig(
        isolation_mode=SchemaIsolationMode.DEDICATED_SCHEMA,
        schema_prefix=schema_prefix,
        create_on_first_access=True,
        seed_data=True,
        enable_row_level_security=enable_rls,
    )
    return config, isolation


# ===========================================================================
# Database-Level Isolation Recipe
# ===========================================================================


def database_level_tenant_recipe(
    max_tenants_per_db: int = 100,
) -> tuple[TenantConfig, SchemaIsolationConfig]:
    """
    Recipe cho database-level isolation — enterprise, strongest isolation.

    Mỗi tenant có database riêng (hoặc chia pool DB, max_tenants_per_db).
    Phù hợp enterprise compliance (HIPAA, PCI-DSS, GDPR).

    Args:
        max_tenants_per_db: Số tenants tối đa trên 1 database

    Returns:
        Tuple[TenantConfig, SchemaIsolationConfig]
    """
    config = TenantConfig(
        mode=TenantMode.SCHEMA,
    )
    isolation = SchemaIsolationConfig(
        isolation_mode=SchemaIsolationMode.DEDICATED_DATABASE,
        schema_prefix="tenant_",
        create_on_first_access=True,
        seed_data=True,
        max_tenants_per_db=max_tenants_per_db,
        enable_row_level_security=False,
    )
    return config, isolation


# ===========================================================================
# Auto-Provisioning Recipe
# ===========================================================================


def auto_provisioning_recipe(
    default_plan: str = "starter",
    storage_gb: int = 10,
    api_calls_per_month: int = 100000,
    max_users: int = 50,
) -> TenantProvisioningConfig:
    """
    Recipe cho auto-provisioning — tenant tự động được tạo resources.

    Auto-create schema/database, seed initial data, assign default plan.

    Args:
        default_plan: Plan mặc định (free, starter, pro, enterprise)
        storage_gb: Storage limit (GB)
        api_calls_per_month: API rate limit per month
        max_users: Số users tối đa

    Returns:
        TenantProvisioningConfig
    """
    return TenantProvisioningConfig(
        strategy=ProvisioningStrategy.AUTOMATIC,
        default_plan=default_plan,
        default_features=["basic_api", "dashboard"],
        resource_limits={
            "storage_gb": storage_gb,
            "api_calls_per_month": api_calls_per_month,
            "max_users": max_users,
        },
        auto_activate=True,
    )


# ===========================================================================
# Manual Review Provisioning Recipe
# ===========================================================================


def manual_review_provisioning_recipe(
    notification_email: str = "",
) -> TenantProvisioningConfig:
    """
    Recipe cho manual-review provisioning — require approval trước khi active.

    Tạo skeleton, yêu cầu admin approve, rồi mới active tenant.

    Args:
        notification_email: Email notify admin khi tenant mới

    Returns:
        TenantProvisioningConfig
    """
    return TenantProvisioningConfig(
        strategy=ProvisioningStrategy.MANUAL_REVIEW,
        default_plan="starter",
        default_features=["basic_api"],
        resource_limits={
            "storage_gb": 5,
            "api_calls_per_month": 50000,
            "max_users": 10,
        },
        auto_activate=False,
        notification_email=notification_email,
    )


# ===========================================================================
# Subdomain Discovery Recipe
# ===========================================================================


def subdomain_tenant_recipe(
    domain: str,
) -> TenantConfig:
    """
    Recipe cho subdomain-based tenant discovery.

    Mỗi tenant có subdomain riêng (tenant1.app.com).

    Args:
        domain: Domain chính (vd: "app.example.com")

    Returns:
        TenantConfig
    """
    return TenantConfig(
        mode=TenantMode.SUBDOMAIN,
        domain=domain,
        cache_ttl=600,
    )


# ===========================================================================
# Cross-Tenant Data Sharing Recipe
# ===========================================================================


def cross_tenant_access_recipe(
    source_tenant: str,
    target_tenant: str,
    entities: list[str] | None = None,
    expires_at: str = "",
) -> CrossTenantAccessRule:
    """
    Recipe cho cross-tenant data access — strict, time-limited, approved.

    Dùng khi tenant A cần read data từ tenant B.

    Args:
        source_tenant: Tenant ID của source (đọc data)
        target_tenant: Tenant ID của target (bị đọc)
        entities: Danh sách entities được phép access
        expires_at: Thời điểm rule hết hiệu lực (ISO 8601)

    Returns:
        CrossTenantAccessRule
    """
    return CrossTenantAccessRule(
        source_tenant=source_tenant,
        target_tenant=target_tenant,
        allowed_entities=entities or ["orders"],
        read_only=True,
        requires_approval=True,
        expires_at=expires_at,
    )


__all__ = [
    "row_level_tenant_recipe",
    "schema_level_tenant_recipe",
    "database_level_tenant_recipe",
    "auto_provisioning_recipe",
    "manual_review_provisioning_recipe",
    "subdomain_tenant_recipe",
    "cross_tenant_access_recipe",
]
