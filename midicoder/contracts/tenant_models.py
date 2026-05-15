# coding: utf-8
"""
Tenant Models Contract — Re-export từ CP02 Multi-Tenant Architecture Generator.

Module này là bridge giữa generated code và CP02 models.
Templates FastAPI import từ đây thay vì import trực tiếp từ emitters.

CP02: Multi-Tenant Architecture
"""

from midicoder.emitters.core.cp02_multi_tenant.models import (
    TenantContext,
    TenantFilter,
    TenantIsolationStrategy,
)

__all__ = [
    "TenantContext",
    "TenantFilter",
    "TenantIsolationStrategy",
]
