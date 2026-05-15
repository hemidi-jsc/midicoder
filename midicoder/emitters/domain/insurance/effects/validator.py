"""Insurance Claims Validator (DP14)."""

from __future__ import annotations
from typing import Any
from ....core.cp01_domain_model.models import ValidationResult


class ClaimsValidators:
    """Insurance Claims Validation Validators (DP14)."""

    async def validate_claims_validation(
        self, data: dict[str, Any], tenant_id: str | None = None,
    ) -> ValidationResult:
        """Validate claims validation rules cho DP14 Insurance."""
        result = ValidationResult(is_valid=True)

        policy_id = data.get("policy_id")
        claim_type = data.get("claim_type")

        if not policy_id:
            result.add_error("Thiếu policy_id")
            return result

        if not claim_type:
            result.add_error("Thiếu claim_type")
            return result

        if not data.get("is_covered", True):
            result.add_error(f"Claim type '{claim_type}' không nằm trong phạm vi bảo hiểm")

        incident_date = data.get("incident_date")
        if incident_date and not data.get("within_coverage_period", True):
            result.add_error(f"Incident date '{incident_date}' nằm ngoài thời hạn hiệu lực")

        claim_amount = data.get("amount", 0)
        if not data.get("within_limit", True):
            result.add_error(f"Số tiền claim {claim_amount} vượt quá policy limit")

        if data.get("is_excluded", False):
            result.add_error(f"Claim bị loại trừ theo điều khoản hợp đồng")

        return result


__all__ = ["ClaimsValidators"]