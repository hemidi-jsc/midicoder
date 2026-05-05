"""
Midicoder Domain Emitters Package.

Package này chứa tất cả domain-specific emitters:
- banking: Double-entry bookkeeping (DP11)
- manufacturing: Inventory & Safety (DP05)
- payments: Payment & Fraud (DP12)
- insurance: Claims validation (DP14)

Domain↔Core Integration:
1. Core Emitter đọc DSL blueprint → parse Commands với EffectType/GuardType
2. Khi gặp domain-specific type, core dispatch đến Domain Effects qua registry
3. Domain Effects implement execution logic thật (gọi external service, write DB)
4. Stack Emitter là integration layer ghép Core + Domain
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ClinicalTransitionResult:
    """Kết quả clinical workflow transition."""
    case_id: str
    from_state: str
    to_state: str
    transitioned: bool
    audit_log_id: Optional[str] = None


class DomainEffects:
    """
    Backward-compatible wrapper cho Domain Effects.

    DEPRECATED: Sử dụng individual domain effects thay vì class này:
    - banking.effects.DoubleEntryEffects
    - manufacturing.effects.InventoryEffects
    - payments.effects.PaymentEffects
    """

    def __init__(
        self,
        ledger_service: Optional[Any] = None,
        inventory_service: Optional[Any] = None,
        payment_service: Optional[Any] = None,
        clinical_service: Optional[Any] = None,
    ) -> None:
        from .banking.effects.effects import DoubleEntryEffects
        from .manufacturing.effects.effects import InventoryEffects
        from .payments.effects.effects import PaymentEffects

        self._double_entry = DoubleEntryEffects(ledger_service=ledger_service)
        self._inventory = InventoryEffects(inventory_service=inventory_service)
        self._payment = PaymentEffects(payment_service=payment_service)
        self._clinical_service = clinical_service

    async def execute_double_entry(
        self, data: dict[str, Any], user_id: Optional[str] = None, tenant_id: Optional[str] = None
    ):
        return await self._double_entry.execute(data, user_id, tenant_id)

    async def execute_inventory_reservation(
        self, data: dict[str, Any], user_id: Optional[str] = None, tenant_id: Optional[str] = None
    ):
        return await self._inventory.execute(data, user_id, tenant_id)

    async def execute_payment_process(
        self, data: dict[str, Any], user_id: Optional[str] = None, tenant_id: Optional[str] = None
    ):
        return await self._payment.execute(data, user_id, tenant_id)

    async def execute_clinical_transition(
        self, data: dict[str, Any], user_id: Optional[str] = None, tenant_id: Optional[str] = None
    ):
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        case_id = data.get("case_id", "")
        from_state = data.get("from_state", "")
        to_state = data.get("to_state", "")

        if not case_id or not from_state or not to_state:
            EM.raise_error(
                ErrorCode.CP01_EFFECT_INVALID_STATE_TRANSITION,
                case_id=case_id, from_state=from_state, to_state=to_state
            )

        if not tenant_id:
            tenant_id = "global"

        if self._clinical_service is None:
            return ClinicalTransitionResult(
                case_id=case_id, from_state=from_state, to_state=to_state,
                transitioned=True, audit_log_id="audit-generated-id",
            )

        # Verify provider credentials
        certified = await self._clinical_service.verify_provider_credentials(
            user_id=user_id, tenant_id=tenant_id
        )
        if not certified:
            EM.raise_error(
                ErrorCode.CP01_EFFECT_PROVIDER_NOT_CERTIFIED,
                user_id=user_id, tenant_id=tenant_id
            )

        # Clinical decision check
        check_passed = await self._clinical_service.check_clinical_decision(
            case_id=case_id, check_type=data.get("check_type", ""),
            from_state=from_state, to_state=to_state, tenant_id=tenant_id,
        )
        if not check_passed:
            EM.raise_error(
                ErrorCode.CP01_EFFECT_CLINICAL_CHECK_FAILED,
                case_id=case_id, tenant_id=tenant_id
            )

        # Log PHI access
        audit_id = await self._clinical_service.log_phi_access(
            case_id=case_id, user_id=user_id,
            phi_fields=data.get("phi_fields", []),
            action="state_transition", tenant_id=tenant_id,
        )

        # Execute transition
        result = await self._clinical_service.transition_state(
            case_id=case_id, from_state=from_state, to_state=to_state,
            user_id=user_id, tenant_id=tenant_id,
        )
        return ClinicalTransitionResult(
            case_id=case_id, from_state=from_state, to_state=to_state,
            transitioned=result.get("transitioned", True), audit_log_id=audit_id,
        )


__all__ = [
    "DomainEffects",
    "ClinicalTransitionResult",
]