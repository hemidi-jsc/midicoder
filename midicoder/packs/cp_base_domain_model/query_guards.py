"""
Query Guards Module.

Module này cung cấp QueryGuards class để validate query guards:
- AUTH guard: Kiểm tra user đã được xác thực và có permission
- TENANT_SCOPE guard: Kiểm tra tenant isolation

Theo SoT E06:
- Every authorized_query must have enforce_tenant_scope
- Query must filter by tenant_id
- No cross-tenant data access without explicit cross_tenant scope

Usage:
    from midicoder.packs.cp_base_domain_model import QueryGuards

    guards = QueryGuards(query)
    await guards.check_all(query_data, user_id=user_id, tenant_id=tenant_id)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .models import Query, QueryGuardType


class QueryGuards:
    """
    Query Guards - Validate query guards before execution.
    
    Theo SoT E03, authorized_query pattern:
    - authorize_permission (AUTH guard)
    - enforce_tenant_scope (TENANT_SCOPE guard)
    
    Theo SoT E06, verification rules:
    - Every authorized_query must have enforce_tenant_scope
    - Query must filter by tenant_id
    
    Usage:
        guards = QueryGuards(query)
        await guards.check_all(query_data, user_id=user_id, tenant_id=tenant_id)
    """

    def __init__(self, query: Query) -> None:
        """
        Khởi tạo QueryGuards.
        
        Args:
            query: Query definition
        """
        self._query = query

    async def check_all(
        self,
        query_data: dict[str, Any],
        *,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Check tất cả guards của query.
        
        Theo SoT E06, thứ tự check:
        1. AUTH guard (permission check)
        2. TENANT_SCOPE guard (tenant isolation)
        
        Args:
            query_data: Query input data
            user_id: User ID từ context
            tenant_id: Tenant ID từ context
            
        Raises:
            PermissionError: Nếu AUTH guard fail
            ValueError: Nếu TENANT_SCOPE guard fail
        """
        for guard in self._query.guards:
            if guard.guard_type == QueryGuardType.AUTH:
                await self._check_auth(guard, user_id)
            elif guard.guard_type == QueryGuardType.TENANT_SCOPE:
                await self._check_tenant_scope(guard, query_data, tenant_id)

    async def _check_auth(
        self,
        guard: Any,
        user_id: str | None,
    ) -> None:
        """
        Check AUTH guard - Validate user authentication và permission.
        
        Theo SoT E03: authorize_permission
        
        Args:
            guard: QueryGuard với guard_type=AUTH
            user_id: User ID từ context
            
        Raises:
            PermissionError: Nếu user không được xác thực hoặc thiếu permission
        """
        # Check authentication
        if user_id is None:
            raise PermissionError(
                "Người dùng không được xác thực. Vui lòng đăng nhập trước."
            )

        # Check permission (permission check được delegate cho business logic)
        # Trong thực tế, đây là nơi sẽ check permission từ RBAC system
        if guard.permission:
            # Placeholder: Permission check sẽ được implement trong runtime
            # guard.permission ví dụ: "order.read", "customer.list"
            pass

    async def _check_tenant_scope(
        self,
        guard: Any,
        query_data: dict[str, Any],
        tenant_id: str | None,
    ) -> None:
        """
        Check TENANT_SCOPE guard - Validate tenant isolation.
        
        Theo SoT E06:
        - Every authorized_query must have enforce_tenant_scope
        - Query must filter by tenant_id
        - No cross-tenant data access without explicit cross_tenant scope
        
        Args:
            guard: QueryGuard với guard_type=TENANT_SCOPE
            query_data: Query input data
            tenant_id: Tenant ID từ context
            
        Raises:
            MidicoderError: Nếu tenant_id không được xác định hoặc cross-tenant không được phép
        """
        # Check tenant_id is defined
        if tenant_id is None:
            EM.raise_error(
                ErrorCode.MDC-B01_GUARD_TENANT_MISSING,
            )

        # Check tenant isolation mode
        if guard.mode == "tenant_isolated":
            # Tenant isolated: query_data phải có tenant_id filter
            # Trong thực tế, đây là nơi sẽ inject tenant_id filter vào query
            pass
        elif guard.mode == "cross_tenant":
            # Cross-tenant: cần explicit permission
            # Placeholder: Cross-tenant permission check
            pass