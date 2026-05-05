"""Manufacturing Safety Guard (DP05)."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from ....core.command.models import CommandGuard, GuardType


class SafetyGuards:
    """Manufacturing Safety Check Guards (DP05)."""

    def __init__(self, compliance_service: Optional[Any] = None) -> None:
        self._compliance_service = compliance_service

    async def check_safety(
        self, guard: CommandGuard, data: dict[str, Any],
        user_id: Optional[str], tenant_id: Optional[str],
    ) -> None:
        """Check SAFETY_CHECK guard cho DP05 Manufacturing."""
        if user_id is None:
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)

        if self._compliance_service is None:
            return

        equipment_id = data.get("equipment_id")
        if equipment_id:
            equipment_safe = await self._compliance_service.check_equipment_safety(
                equipment_id=equipment_id, tenant_id=tenant_id
            )
            if not equipment_safe:
                EM.raise_error(ErrorCode.CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE,
                    user_id=user_id, tenant_id=tenant_id, equipment_id=equipment_id)

        personnel_certified = await self._compliance_service.check_personnel_certification(
            user_id=user_id, operation_type=data.get("operation_type"), tenant_id=tenant_id
        )
        if not personnel_certified:
            EM.raise_error(ErrorCode.CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED,
                user_id=user_id, tenant_id=tenant_id, operation_type=data.get("operation_type"))

        if not data.get("process_compliant", True):
            EM.raise_error(ErrorCode.CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT,
                user_id=user_id, tenant_id=tenant_id, operation_type=data.get("operation_type"))

        hazards = await self._compliance_service.detect_hazards(
            operation_data=data, tenant_id=tenant_id
        )
        if hazards:
            EM.raise_error(ErrorCode.CP01_GUARD_SAFETY_HAZARD_DETECTED,
                user_id=user_id, tenant_id=tenant_id, hazards=hazards)


__all__ = ["SafetyGuards"]