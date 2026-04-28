"""
Command Guards với auth, tenant, và compliance support.

Hỗ trợ:
- AUTH guard: Permission checking
- TENANT_SCOPE guard: Tenant isolation
- RATE_LIMIT guard: Rate limiting
- KYC_CHECK guard: KYC compliance
- AML_SCREENING guard: AML screening
- HIPAA_ACCESS guard: HIPAA compliance

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from .models import Command, CommandGuard, GuardType


class CommandGuards:
    """
    Guards manager cho Command.

    Cung cấp:
    - check_all(): Check tất cả guards
    - check_auth(): Check permission
    - check_tenant(): Check tenant isolation
    - check_rate_limit(): Check rate limiting
    - check_compliance(): Check compliance gates

    Usage:
        guards = CommandGuards(command, auth_service, tenant_service)
        await guards.check_all(command_data, user_id, tenant_id)
    """

    def __init__(
        self,
        command: Command,
        auth_service: Optional[Any] = None,
        tenant_service: Optional[Any] = None,
        compliance_service: Optional[Any] = None,
    ) -> None:
        """
        Khởi tạo CommandGuards.

        Args:
            command: Command definition
            auth_service: Auth service instance (optional)
            tenant_service: Tenant service instance (optional)
            compliance_service: Compliance service instance (optional)
        """
        self._command = command
        self._auth_service = auth_service
        self._tenant_service = tenant_service
        self._compliance_service = compliance_service

    async def check_all(
        self,
        data: dict[str, Any],
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Check tất cả guards theo thứ tự ưu tiên.

        Order:
        1. Auth guard (permission check)
        2. Tenant guard (isolation check)
        3. Rate limit guard
        4. Compliance guards (KYC, AML, HIPAA)

        Args:
            data: Command data
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: Client IP address

        Raises:
            PermissionError: Nếu không có permission
            ValueError: Nếu vi phạm tenant scope
            RuntimeError: Nếu vi phạm compliance
        """
        for guard in self._command.guards:
            if guard.guard_type == GuardType.AUTH:
                await self._check_auth(guard, user_id)
            elif guard.guard_type == GuardType.TENANT_SCOPE:
                await self._check_tenant(guard, data, tenant_id)
            elif guard.guard_type == GuardType.RATE_LIMIT:
                await self._check_rate_limit(guard, user_id, ip_address)
            elif guard.guard_type == GuardType.KYC_CHECK:
                await self._check_kyc(guard, user_id)
            elif guard.guard_type == GuardType.AML_SCREENING:
                await self._check_aml(guard, data, user_id)
            elif guard.guard_type == GuardType.HIPAA_ACCESS:
                await self._check_hipaa(guard, user_id)

    async def _check_auth(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
    ) -> None:
        """
        Check AUTH guard (permission).

        Args:
            guard: Guard definition
            user_id: User ID

        Raises:
            PermissionError: Nếu không có permission
        """
        if user_id is None:
            raise PermissionError("User không được xác thực")

        if guard.permission is None:
            return  # No permission required

        # Integrate with auth service
        if self._auth_service:
            has_permission = await self._auth_service.check_permission(
                user_id=user_id,
                permission=guard.permission,
            )
            if not has_permission:
                raise PermissionError(
                    f"User không có permission: {guard.permission}"
                )
        else:
            # Fallback: TODO stub for generated code
            # In generated code, this will be replaced with actual auth service call
            pass

    async def _check_tenant(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check TENANT_SCOPE guard (isolation).

        Args:
            guard: Guard definition
            data: Command data
            tenant_id: Tenant ID

        Raises:
            ValueError: Nếu vi phạm tenant scope
        """
        if tenant_id is None:
            raise ValueError("Tenant ID không được xác định")

        mode = guard.mode or "tenant_isolated"

        if mode == "tenant_isolated":
            # Check data belongs to tenant
            if self._tenant_service:
                is_belong = await self._tenant_service.belongs_to_tenant(
                    data=data,
                    tenant_id=tenant_id,
                )
                if not is_belong:
                    raise ValueError("Data không thuộc tenant")
            # Fallback: Generated code will have tenant check in effects

        elif mode == "tenant_shared":
            # Shared tenant mode - allow cross-tenant access with permission
            pass

        elif mode == "global":
            # Global mode - super admin
            pass

    async def _check_rate_limit(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
        ip_address: Optional[str],
    ) -> None:
        """
        Check RATE_LIMIT guard.

        Args:
            guard: Guard definition
            user_id: User ID
            ip_address: IP address

        Raises:
            RuntimeError: Nếu vượt quá rate limit
        """
        limit = guard.limit or 100
        window = guard.window or "60s"

        # Rate limiting logic (placeholder)
        # In production, use Redis or similar
        if self._auth_service:
            is_limited = await self._auth_service.check_rate_limit(
                user_id=user_id,
                ip_address=ip_address,
                limit=limit,
                window=window,
            )
            if is_limited:
                raise RuntimeError(
                    f"Vượt quá giới hạn {limit} requests/{window}"
                )

    async def _check_kyc(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
    ) -> None:
        """
        Check KYC compliance guard (RX03).

        Args:
            guard: Guard definition
            user_id: User ID

        Raises:
            RuntimeError: Nếu KYC chưa hoàn thành
        """
        if user_id is None:
            raise RuntimeError("User không được xác thực")

        if self._compliance_service:
            is_kyc_verified = await self._compliance_service.check_kyc(
                user_id=user_id,
            )
            if not is_kyc_verified:
                raise RuntimeError("KYC chưa được xác minh")

    async def _check_aml(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        user_id: Optional[str],
    ) -> None:
        """
        Check AML screening guard (RX03).

        Args:
            guard: Guard definition
            data: Command data
            user_id: User ID

        Raises:
            RuntimeError: Nếu AML screening failed
        """
        if user_id is None:
            raise RuntimeError("User không được xác thực")

        if self._compliance_service:
            is_aml_clear = await self._compliance_service.check_aml(
                user_id=user_id,
                transaction_data=data,
            )
            if not is_aml_clear:
                raise RuntimeError("AML screening failed - giao dịch bị từ chối")

    async def _check_hipaa(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
    ) -> None:
        """
        Check HIPAA access guard (RX04).

        Args:
            guard: Guard definition
            user_id: User ID

        Raises:
            RuntimeError: Nếu không có HIPAA clearance
        """
        if user_id is None:
            raise RuntimeError("User không được xác thực")

        if self._compliance_service:
            has_hipaa_clearance = (
                await self._compliance_service.check_hipaa_clearance(user_id=user_id)
            )
            if not has_hipaa_clearance:
                raise RuntimeError("Không có HIPAA clearance để truy cập dữ liệu y tế")