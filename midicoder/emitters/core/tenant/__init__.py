# coding: utf-8
"""
CP02: Multi-Tenant Architecture Generator.

Cung cap 2 capabilities:
- enforce_tenant_scope: Tu dong inject tenant filter vao queries
- tenant_isolation: Bat buoc tenant isolation cho tat ca operations

Support 3 isolation strategies:
- Schema: Moi tenant co PostgreSQL schema rieng
- Row: Tat ca tenant chia will bang, phan biet bang tenant_id column
- Subdomain: Moi tenant co subdomain rieng

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