"""Payments Fraud Detection Guard (DP12)."""

from __future__ import annotations
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from ....core.command.models import CommandGuard, GuardType


class FraudGuards:
    """Payments Fraud Detection Guards (DP12)."""

    def __init__(self, compliance_service: Optional[Any] = None) -> None:
        self._compliance_service = compliance_service

    async def check_fraud_detection(
        self, guard: CommandGuard, data: dict[str, Any],
        user_id: Optional[str], tenant_id: Optional[str],
    ) -> None:
        """Check FRAUD_DETECTION guard cho DP12 Payments."""
        if user_id is None:
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)
        if self._compliance_service is None:
            return

        velocity_exceeded = await self._compliance_service.check_transaction_velocity(
            user_id=user_id, tenant_id=tenant_id,
            threshold=guard.limit or 10, window=guard.window or "1h"
        )
        if velocity_exceeded:
            EM.raise_error(ErrorCode.CP01_GUARD_FRAUD_VELOCITY_EXCEEDED,
                user_id=user_id, tenant_id=tenant_id)

        amount = data.get("amount", 0)
        if data.get("is_anomaly_detected", False):
            EM.raise_error(ErrorCode.CP01_GUARD_FRAUD_PATTERN_ANOMALY,
                user_id=user_id, tenant_id=tenant_id)


__all__ = ["FraudGuards"]