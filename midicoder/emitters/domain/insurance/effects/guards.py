"""Insurance Claims Validation Guard (DP14)."""

from __future__ import annotations
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from ....core.cp01_domain_model.models import CommandGuard, GuardType


class ClaimsGuards:
    """Insurance Claims Validation Guards (DP14)."""

    def __init__(self, compliance_service: Optional[Any] = None) -> None:
        self._compliance_service = compliance_service

    async def check_claims_validation(
        self, guard: CommandGuard, data: dict[str, Any],
        user_id: Optional[str], tenant_id: Optional[str],
    ) -> None:
        """Check CLAIMS_VALIDATION guard cho DP14 Insurance."""
        if user_id is None:
            EM.raise_error(ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED)
        if self._compliance_service is None:
            return

        policy_id = data.get("policy_id")
        if not policy_id:
            EM.raise_error(ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED,
                user_id=user_id, tenant_id=tenant_id, reason="missing_policy_id")

        claim_type = data.get("claim_type")
        is_covered = await self._compliance_service.check_policy_coverage(
            policy_id=policy_id, claim_type=claim_type, tenant_id=tenant_id
        )
        if not is_covered:
            EM.raise_error(ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED,
                user_id=user_id, tenant_id=tenant_id, policy_id=policy_id, claim_type=claim_type)

        incident_date = data.get("incident_date")
        if incident_date:
            within_period = await self._compliance_service.check_coverage_period(
                policy_id=policy_id, incident_date=incident_date, tenant_id=tenant_id
            )
            if not within_period:
                EM.raise_error(ErrorCode.CP01_GUARD_CLAIMS_OUTSIDE_PERIOD,
                    user_id=user_id, tenant_id=tenant_id, policy_id=policy_id, incident_date=incident_date)

        claim_amount = data.get("amount", 0)
        within_limit = await self._compliance_service.check_claim_limit(
            policy_id=policy_id, claim_amount=claim_amount, tenant_id=tenant_id
        )
        if not within_limit:
            EM.raise_error(ErrorCode.CP01_GUARD_CLAIMS_EXCEEDS_LIMIT,
                user_id=user_id, tenant_id=tenant_id, policy_id=policy_id, amount=claim_amount)

        is_excluded = await self._compliance_service.check_claim_exclusions(
            policy_id=policy_id, claim_type=claim_type,
            incident_data=data.get("incident_data", {}), tenant_id=tenant_id
        )
        if is_excluded:
            EM.raise_error(ErrorCode.CP01_GUARD_CLAIMS_EXCLUDED,
                user_id=user_id, tenant_id=tenant_id, policy_id=policy_id, claim_type=claim_type)


__all__ = ["ClaimsGuards"]