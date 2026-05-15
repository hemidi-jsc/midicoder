"""Manufacturing Safety Validator (DP05)."""

from __future__ import annotations
from typing import Any
from ....core.cp01_domain_model.models import ValidationResult


class SafetyValidators:
    """Manufacturing Safety Check Validators (DP05)."""

    async def validate_safety_check(
        self, data: dict[str, Any], tenant_id: str | None = None,
    ) -> ValidationResult:
        """Validate safety check rules cho DP05 Manufacturing."""
        result = ValidationResult(is_valid=True)
        equipment_id = data.get("equipment_id")
        if equipment_id and not data.get("equipment_safe", True):
            result.add_error(f"Thiết bị không an toàn: {equipment_id}")

        if not data.get("personnel_certified", True):
            result.add_error(f"Nhân sự không có chứng chỉ (user: {data.get('user_id')})")

        if not data.get("process_compliant", True):
            result.add_error("Không tuân thủ quy trình an toàn")

        hazards = data.get("detected_hazards", [])
        if hazards:
            result.add_error(f"Phát hiện nguy cơ: {hazards}")

        return result


__all__ = ["SafetyValidators"]