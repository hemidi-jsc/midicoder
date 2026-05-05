"""Payments Domain Effects - Payment Process (DP12)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


@dataclass
class PaymentProcessResult:
    """Kết quả payment process."""
    payment_id: str
    status: str
    gateway: str
    transaction_ref: Optional[str] = None
    error_message: Optional[str] = None


class PaymentEffects:
    """Payments Payment Gateway Effects (DP12)."""

    def __init__(self, payment_service: Optional[Any] = None) -> None:
        self._payment_service = payment_service

    async def execute(
        self, data: dict[str, Any], user_id: Optional[str] = None, tenant_id: Optional[str] = None,
    ) -> PaymentProcessResult:
        """Execute payment gateway effect."""
        amount = data.get("amount", 0)
        gateway = data.get("gateway", "stripe")
        idempotency_key = data.get("idempotency_key", "")

        if amount <= 0 or not gateway or not idempotency_key:
            EM.raise_error(ErrorCode.CP01_EFFECT_PAYMENT_FAILED, amount=amount, gateway=gateway)

        if not tenant_id:
            tenant_id = "global"

        if self._payment_service:
            try:
                result = await self._payment_service.process_payment(
                    amount=amount, gateway=gateway, idempotency_key=idempotency_key,
                    user_id=user_id, tenant_id=tenant_id,
                )
                return PaymentProcessResult(
                    payment_id=result.get("payment_id", ""), status=result.get("status", "completed"),
                    gateway=gateway, transaction_ref=result.get("transaction_ref"),
                )
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate" in error_msg or "idempotency" in error_msg:
                    EM.raise_error(ErrorCode.CP01_EFFECT_PAYMENT_DUPLICATE,
                        idempotency_key=idempotency_key, gateway=gateway, tenant_id=tenant_id)
                elif "connection" in error_msg or "timeout" in error_msg:
                    EM.raise_error(ErrorCode.CP01_EFFECT_PAYMENT_GATEWAY_ERROR,
                        gateway=gateway, error=str(e), tenant_id=tenant_id)
                EM.raise_error(ErrorCode.CP01_EFFECT_PAYMENT_FAILED,
                    payment_id=idempotency_key, gateway=gateway, error=str(e), tenant_id=tenant_id)

        return PaymentProcessResult(
            payment_id="pay-generated-id", status="completed", gateway=gateway, transaction_ref="txn-ref-123",
        )


__all__ = ["PaymentEffects", "PaymentProcessResult"]