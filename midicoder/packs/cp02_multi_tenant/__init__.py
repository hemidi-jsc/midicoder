# coding: utf-8
"""
CP02: Multi-Tenant Architecture Generator.

Cung cấp 2 capabilities:
- enforce_tenant_scope: Tự động inject tenant filter vào queries
- tenant_isolation: Bắt buộc tenant isolation cho tất cả operations

Support 3 isolation strategies:
- Schema: Mỗi tenant có PostgreSQL schema riêng
- Row: Tất cả tenant chia cùng bảng, phân biệt bằng tenant_id column
- Subdomain: Mỗi tenant có subdomain riêng

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp02_multi_tenant.models import (
    TenantMode,
    TenantConfig,
    TenantContext,
    TenantResolver,
    TenantIsolationStrategy,
    TenantFilter,
    SchemaIsolationMode,
    SchemaIsolationConfig,
    ProvisioningStrategy,
    TenantStatus,
    TenantProvisioningConfig,
    CrossTenantAccessRule,
)
from midicoder.packs.cp02_multi_tenant.fastapi import FastAPITenantEmitter
from midicoder.packs.cp02_multi_tenant.nestjs import NestJSTenantEmitter
from midicoder.packs.cp02_multi_tenant.angular import AngularTenantEmitter
from midicoder.packs.cp02_multi_tenant.react import ReactTenantEmitter

__all__ = [
    # Models
    "TenantMode",
    "TenantConfig",
    "TenantContext",
    "TenantResolver",
    "TenantIsolationStrategy",
    "TenantFilter",
    "SchemaIsolationMode",
    "SchemaIsolationConfig",
    "ProvisioningStrategy",
    "TenantStatus",
    "TenantProvisioningConfig",
    "CrossTenantAccessRule",
    # Emitters
    "FastAPITenantEmitter",
    "NestJSTenantEmitter",
    "AngularTenantEmitter",
    "ReactTenantEmitter",
]