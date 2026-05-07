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

from midicoder.emitters.core.tenant.models import (
    TenantMode,
    TenantConfig,
    TenantContext,
    TenantResolver,
)
from midicoder.emitters.core.tenant.fastapi import FastAPITenantEmitter
from midicoder.emitters.core.tenant.nestjs import NestJSTenantEmitter
from midicoder.emitters.core.tenant.angular import AngularTenantEmitter
from midicoder.emitters.core.tenant.react import ReactTenantEmitter

__all__ = [
    "TenantMode",
    "TenantConfig",
    "TenantContext",
    "TenantResolver",
    "FastAPITenantEmitter",
    "NestJSTenantEmitter",
    "AngularTenantEmitter",
    "ReactTenantEmitter",
]