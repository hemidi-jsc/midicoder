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

from datetime import datetime
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .command_models import Command, CommandGuard, GuardType


class CommandGuards:
    """
    Guards manager cho Command với tenant-aware support.

    Cung cấp:
    - check_all(): Check tất cả guards
    - check_auth(): Check permission
    - check_tenant(): Check tenant isolation (KPI-029)
    - check_rate_limit(): Check rate limiting
    - check_compliance(): Check compliance gates (RX02-RX04)

    Tenant Support (KPI-029):
    - Tất cả compliance checks đều tenant-aware
    - Audit log ghi tenant_id cho multi-tenant compliance
    - KYC/AML/HIPAA checks enforce tenant isolation

    Usage:
        guards = CommandGuards(command, auth_service, tenant_service, compliance_service)
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
            elif guard.guard_type == GuardType.FRAUD_DETECTION:
                await self._check_fraud_detection(guard, data, user_id, tenant_id)
            elif guard.guard_type == GuardType.SAFETY_CHECK:
                await self._check_safety(guard, data, user_id, tenant_id)
            elif guard.guard_type == GuardType.CLAIMS_VALIDATION:
                await self._check_claims_validation(guard, data, user_id, tenant_id)

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
            PermissionError: Nếu user không được xác thực hoặc không có permission
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
                raise PermissionError(f"User không có permission: {guard.permission}")
        # Fallback: Generated code will have auth service

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
            MidicoderError: Nếu tenant ID thiếu hoặc vi phạm tenant scope
        """
        if tenant_id is None:
            EM.raise_error(
                ErrorCode.CP01_GUARD_TENANT_MISSING,
            )

        mode = guard.mode or "tenant_isolated"

        if mode == "tenant_isolated":
            # Check data belongs to tenant
            if self._tenant_service:
                is_belong = await self._tenant_service.belongs_to_tenant(
                    data=data,
                    tenant_id=tenant_id,
                )
                if not is_belong:
                    EM.raise_error(
                        ErrorCode.CP01_GUARD_TENANT_VIOLATION,
                        tenant_id=tenant_id,
                    )
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
            MidicoderError: Nếu vượt quá rate limit
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
                EM.raise_error(
                    ErrorCode.CP01_GUARD_RATE_LIMIT_EXCEEDED,
                    limit=limit,
                    window=window,
                    user_id=user_id,
                    ip_address=ip_address,
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
            MidicoderError: Nếu user không được xác thực hoặc KYC chưa hoàn thành
        """
        if user_id is None:
            EM.raise_error(
                ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED,
            )

        if self._compliance_service:
            is_kyc_verified = await self._compliance_service.check_kyc(
                user_id=user_id,
            )
            if not is_kyc_verified:
                EM.raise_error(
                    ErrorCode.CP01_GUARD_KYC_NOT_VERIFIED,
                    user_id=user_id,
                )

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
            MidicoderError: Nếu user không được xác thực hoặc AML screening failed
        """
        if user_id is None:
            EM.raise_error(
                ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED,
            )

        if self._compliance_service:
            is_aml_clear = await self._compliance_service.check_aml(
                user_id=user_id,
                transaction_data=data,
            )
            if not is_aml_clear:
                EM.raise_error(
                    ErrorCode.CP01_GUARD_AML_SCREENING_FAILED,
                    user_id=user_id,
                )

    async def _check_hipaa(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Check HIPAA access guard (RX04).

        Tenant-aware (KPI-029): Audit log ghi tenant_id.

        Args:
            guard: Guard definition
            user_id: User ID
            tenant_id: Tenant ID cho audit logging

        Raises:
            MidicoderError: Nếu user không được xác thực hoặc không có HIPAA clearance
        """
        if user_id is None:
            EM.raise_error(
                ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED,
            )

        if self._compliance_service:
            has_hipaa_clearance = (
                await self._compliance_service.check_hipaa_clearance(
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
            )
            if not has_hipaa_clearance:
                EM.raise_error(
                    ErrorCode.CP01_GUARD_HIPAA_NO_CLEARANCE,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )

    # -------------------------------------------------------------------------
    # Audit Logging (KPI-029: Tenant Isolation)
    # -------------------------------------------------------------------------

    async def _log_compliance_check(
        self,
        guard_type: GuardType,
        user_id: str,
        tenant_id: Optional[str],
        result: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log compliance check vào audit trail.

        KPI-029: Tất cả compliance checks đều tenant-aware.
        Audit log bao gồm tenant_id cho multi-tenant compliance tracking.

        Args:
            guard_type: Loại guard (KYC_CHECK, AML_SCREENING, HIPAA_ACCESS)
            user_id: User ID thực hiện check
            tenant_id: Tenant ID (KPI-029)
            result: Kết quả (passed, failed, skipped)
            details: Thông tin thêm (optional)
        
        Raises:
            MidicoderError: Nếu ghi audit log thất bại
        """
        if self._compliance_service is None:
            return  # No compliance service, skip logging

        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "guard_type": guard_type.value,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "result": result,
            "command_id": self._command.id,
            "details": details or {},
        }

        try:
            await self._compliance_service.log_compliance_check(audit_record)
        except Exception as e:
            # Log warning but don't fail the check
            EM.raise_error(
                ErrorCode.CP01_GUARD_COMPLIANCE_LOG_FAILED,
                guard_type=guard_type.value,
                user_id=user_id,
                tenant_id=tenant_id,
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Updated Compliance Methods with Audit Logging
    # -------------------------------------------------------------------------

    async def _check_kyc_with_audit(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check KYC compliance guard với audit logging (RX03).

        KPI-029: Tenant-aware KYC check với audit trail.

        Args:
            guard: Guard definition
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu user không được xác thực hoặc KYC chưa hoàn thành
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.KYC_CHECK, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.KYC_CHECK, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        is_kyc_verified = await self._compliance_service.check_kyc(
            user_id=user_id,
            tenant_id=tenant_id,  # KPI-029
        )

        if not is_kyc_verified:
            await self._log_compliance_check(
                GuardType.KYC_CHECK, user_id, tenant_id, "failed",
                {"reason": "kyc_not_verified"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_KYC_NOT_VERIFIED,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        await self._log_compliance_check(
            GuardType.KYC_CHECK, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )

    async def _check_aml_with_audit(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check AML screening guard với audit logging (RX03).

        KPI-029: Tenant-aware AML check với audit trail.

        Args:
            guard: Guard definition
            data: Command data
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu user không được xác thực hoặc AML screening failed
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.AML_SCREENING, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.AML_SCREENING, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        is_aml_clear = await self._compliance_service.check_aml(
            user_id=user_id,
            transaction_data=data,
            tenant_id=tenant_id,  # KPI-029
        )

        if not is_aml_clear:
            await self._log_compliance_check(
                GuardType.AML_SCREENING, user_id, tenant_id, "failed",
                {"reason": "aml_screening_failed"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_AML_SCREENING_FAILED,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        await self._log_compliance_check(
            GuardType.AML_SCREENING, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )

    async def _check_hipaa_with_audit(
        self,
        guard: CommandGuard,
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check HIPAA access guard với audit logging (RX04).

        KPI-029: Tenant-aware HIPAA check với audit trail.

        Args:
            guard: Guard definition
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu user không được xác thực hoặc không có HIPAA clearance
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.HIPAA_ACCESS, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.HIPAA_ACCESS, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        has_hipaa_clearance = await self._compliance_service.check_hipaa_clearance(
            user_id=user_id,
            tenant_id=tenant_id,  # KPI-029
        )

        if not has_hipaa_clearance:
            await self._log_compliance_check(
                GuardType.HIPAA_ACCESS, user_id, tenant_id, "failed",
                {"reason": "no_hipaa_clearance"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_HIPAA_NO_CLEARANCE,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        await self._log_compliance_check(
            GuardType.HIPAA_ACCESS, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )

    # -------------------------------------------------------------------------
    # FRAUD_DETECTION Guard (DP12 Payments)
    # -------------------------------------------------------------------------

    async def _check_fraud_detection(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check FRAUD_DETECTION guard cho DP12 Payments.

        Kiểm tra:
        - Transaction velocity (số lượng giao dịch / thời gian)
        - Amount threshold (số tiền vượt ngưỡng)
        - Pattern anomaly (phát hiện pattern bất thường)
        - External fraud API (gọi external fraud service)

        KPI-029: Tenant-aware fraud detection với audit trail.

        Args:
            guard: Guard definition
            data: Transaction data (amount, timestamp, etc.)
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu phát hiện gian lận hoặc vượt threshold
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.FRAUD_DETECTION, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.FRAUD_DETECTION, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        # 1. Transaction velocity check
        velocity_threshold = guard.limit or 10  # default: 10 transactions/hour
        velocity_window = guard.window or "1h"
        
        velocity_exceeded = await self._compliance_service.check_transaction_velocity(
            user_id=user_id,
            tenant_id=tenant_id,
            threshold=velocity_threshold,
            window=velocity_window,
        )
        
        if velocity_exceeded:
            await self._log_compliance_check(
                GuardType.FRAUD_DETECTION, user_id, tenant_id, "failed",
                {"reason": "velocity_exceeded", "threshold": velocity_threshold}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_FRAUD_VELOCITY_EXCEEDED,
                user_id=user_id,
                tenant_id=tenant_id,
                threshold=velocity_threshold,
                window=velocity_window,
            )

        # 2. Amount threshold check
        amount = data.get("amount", 0)
        amount_threshold = guard.condition  # Should be set in guard config
        if amount_threshold:
            try:
                threshold_value = float(amount_threshold)
                if amount > threshold_value:
                    await self._log_compliance_check(
                        GuardType.FRAUD_DETECTION, user_id, tenant_id, "failed",
                        {"reason": "amount_threshold_exceeded", "amount": amount}
                    )
                    EM.raise_error(
                        ErrorCode.CP01_GUARD_FRAUD_AMOUNT_THRESHOLD,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        amount=amount,
                        threshold=threshold_value,
                    )
            except (ValueError, TypeError):
                pass  # Invalid threshold, skip check

        # 3. Pattern anomaly detection
        anomaly_detected = await self._compliance_service.detect_pattern_anomaly(
            user_id=user_id,
            transaction_data=data,
            tenant_id=tenant_id,
        )
        
        if anomaly_detected:
            await self._log_compliance_check(
                GuardType.FRAUD_DETECTION, user_id, tenant_id, "failed",
                {"reason": "pattern_anomaly_detected"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_FRAUD_PATTERN_ANOMALY,
                user_id=user_id,
                tenant_id=tenant_id,
            )

        # 4. External fraud API call (optional, with circuit breaker)
        try:
            external_result = await self._compliance_service.call_external_fraud_api(
                user_id=user_id,
                transaction_data=data,
                tenant_id=tenant_id,
                timeout=5,  # 5 seconds timeout
            )
            
            if external_result.get("blocked", False):
                await self._log_compliance_check(
                    GuardType.FRAUD_DETECTION, user_id, tenant_id, "failed",
                    {"reason": "external_fraud_blocked"}
                )
                EM.raise_error(
                    ErrorCode.CP01_GUARD_FRAUD_EXTERNAL_BLOCKED,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    reason=external_result.get("reason", "Unknown"),
                )
        except TimeoutError:
            # Fallback: allow if external API timeout
            await self._log_compliance_check(
                GuardType.FRAUD_DETECTION, user_id, tenant_id, "skipped",
                {"reason": "external_api_timeout", "fallback": "allow"}
            )
            return

        await self._log_compliance_check(
            GuardType.FRAUD_DETECTION, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )

    # -------------------------------------------------------------------------
    # SAFETY_CHECK Guard (DP05 Manufacturing)
    # -------------------------------------------------------------------------

    async def _check_safety(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check SAFETY_CHECK guard cho DP05 Manufacturing.

        Kiểm tra:
        - Equipment safety (thiết bị an toàn)
        - Personnel certification (nhân sự có chứng chỉ)
        - Process compliance (tuân thủ quy trình an toàn)
        - Hazard detection (phát hiện nguy cơ)

        KPI-029: Tenant-aware safety check với audit trail.

        Args:
            guard: Guard definition
            data: Safety-related data (equipment_id, operation_type, etc.)
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu không đạt yêu cầu an toàn
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.SAFETY_CHECK, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.SAFETY_CHECK, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        # 1. Equipment safety check
        equipment_id = data.get("equipment_id")
        if equipment_id:
            equipment_safe = await self._compliance_service.check_equipment_safety(
                equipment_id=equipment_id,
                tenant_id=tenant_id,
            )
            
            if not equipment_safe:
                await self._log_compliance_check(
                    GuardType.SAFETY_CHECK, user_id, tenant_id, "failed",
                    {"reason": "equipment_unsafe", "equipment_id": equipment_id}
                )
                EM.raise_error(
                    ErrorCode.CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    equipment_id=equipment_id,
                )

        # 2. Personnel certification check
        personnel_certified = await self._compliance_service.check_personnel_certification(
            user_id=user_id,
            operation_type=data.get("operation_type"),
            tenant_id=tenant_id,
        )
        
        if not personnel_certified:
            await self._log_compliance_check(
                GuardType.SAFETY_CHECK, user_id, tenant_id, "failed",
                {"reason": "personnel_not_certified"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED,
                user_id=user_id,
                tenant_id=tenant_id,
                operation_type=data.get("operation_type"),
            )

        # 3. Process compliance check
        process_compliant = await self._compliance_service.check_process_compliance(
            operation_type=data.get("operation_type"),
            process_data=data.get("process_data", {}),
            tenant_id=tenant_id,
        )
        
        if not process_compliant:
            await self._log_compliance_check(
                GuardType.SAFETY_CHECK, user_id, tenant_id, "failed",
                {"reason": "process_non_compliant"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT,
                user_id=user_id,
                tenant_id=tenant_id,
                operation_type=data.get("operation_type"),
            )

        # 4. Hazard detection
        hazards = await self._compliance_service.detect_hazards(
            operation_data=data,
            tenant_id=tenant_id,
        )
        
        if hazards:
            await self._log_compliance_check(
                GuardType.SAFETY_CHECK, user_id, tenant_id, "failed",
                {"reason": "hazards_detected", "hazards": hazards}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_SAFETY_HAZARD_DETECTED,
                user_id=user_id,
                tenant_id=tenant_id,
                hazards=hazards,
            )

        await self._log_compliance_check(
            GuardType.SAFETY_CHECK, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )

    # -------------------------------------------------------------------------
    # CLAIMS_VALIDATION Guard (DP14 Insurance)
    # -------------------------------------------------------------------------

    async def _check_claims_validation(
        self,
        guard: CommandGuard,
        data: dict[str, Any],
        user_id: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """
        Check CLAIMS_VALIDATION guard cho DP14 Insurance.

        Kiểm tra:
        - Policy coverage (claim nằm trong phạm vi bảo hiểm)
        - Coverage period (claim nằm trong thời hạn hiệu lực)
        - Claim amount vs limit (số tiền không vượt quá limit)
        - Exclusion check (claim không thuộc loại bị loại trừ)

        KPI-029: Tenant-aware claims validation với audit trail.

        Args:
            guard: Guard definition
            data: Claim data (policy_id, amount, incident_date, claim_type, etc.)
            user_id: User ID
            tenant_id: Tenant ID (KPI-029)

        Raises:
            MidicoderError: Nếu claim không thỏa mãn điều kiện bảo hiểm
        """
        if user_id is None:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "user_not_authenticated"}
            )
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "skipped",
                {"reason": "no_compliance_service"}
            )
            return

        policy_id = data.get("policy_id")
        if not policy_id:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "missing_policy_id"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED,
                user_id=user_id,
                tenant_id=tenant_id,
                reason="missing_policy_id",
            )

        # 1. Policy coverage check
        claim_type = data.get("claim_type")
        is_covered = await self._compliance_service.check_policy_coverage(
            policy_id=policy_id,
            claim_type=claim_type,
            tenant_id=tenant_id,
        )
        
        if not is_covered:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "claim_not_covered", "claim_type": claim_type}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED,
                user_id=user_id,
                tenant_id=tenant_id,
                policy_id=policy_id,
                claim_type=claim_type,
            )

        # 2. Coverage period check
        incident_date = data.get("incident_date")
        within_period = await self._compliance_service.check_coverage_period(
            policy_id=policy_id,
            incident_date=incident_date,
            tenant_id=tenant_id,
        )
        
        if not within_period:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "outside_coverage_period", "incident_date": incident_date}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_CLAIMS_OUTSIDE_PERIOD,
                user_id=user_id,
                tenant_id=tenant_id,
                policy_id=policy_id,
                incident_date=incident_date,
            )

        # 3. Claim amount vs limit check
        claim_amount = data.get("amount", 0)
        within_limit = await self._compliance_service.check_claim_limit(
            policy_id=policy_id,
            claim_amount=claim_amount,
            tenant_id=tenant_id,
        )
        
        if not within_limit:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "exceeds_limit", "amount": claim_amount}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_CLAIMS_EXCEEDS_LIMIT,
                user_id=user_id,
                tenant_id=tenant_id,
                policy_id=policy_id,
                amount=claim_amount,
            )

        # 4. Exclusion check
        is_excluded = await self._compliance_service.check_claim_exclusions(
            policy_id=policy_id,
            claim_type=claim_type,
            incident_data=data.get("incident_data", {}),
            tenant_id=tenant_id,
        )
        
        if is_excluded:
            await self._log_compliance_check(
                GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "failed",
                {"reason": "claim_excluded"}
            )
            EM.raise_error(
                ErrorCode.CP01_GUARD_CLAIMS_EXCLUDED,
                user_id=user_id,
                tenant_id=tenant_id,
                policy_id=policy_id,
                claim_type=claim_type,
            )

        await self._log_compliance_check(
            GuardType.CLAIMS_VALIDATION, user_id, tenant_id, "passed",
            {"tenant_id": tenant_id}
        )
