"""Payments Fraud Validator (DP12)."""

from __future__ import annotations
from typing import Any
from ....core.command.models import ValidationResult


class FraudValidators:
    """Payments Fraud Detection Validators (DP12)."""

    async def validate_fraud_detection(
        self, data: dict[str, Any], tenant_id: str | None = None,
    ) -> ValidationResult:
        """Validate fraud detection rules cho DP12 Payments."""
        result = ValidationResult(is_valid=True)

        velocity_threshold = data.get("velocity_threshold", 10)
        transaction_count = data.get("transaction_count", 0)
        if transaction_count > velocity_threshold:
            result.add_error(f"Vượt velocity threshold: {transaction_count} > {velocity_threshold}")

        amount = data.get("amount", 0)
        amount_threshold = data.get("amount_threshold")
        if amount_threshold is not None:
            try:
                if amount > float(amount_threshold):
                    result.add_error(f"Số tiền vượt ngưỡng: {amount} > {amount_threshold}")
            except (ValueError, TypeError):
                pass

        if data.get("is_anomaly_detected", False):
            result.add_error("Phát hiện pattern bất thường")

        if data.get("external_fraud_blocked", False):
            result.add_error("Giao dịch bị blocked bởi external fraud service")

        return result


__all__ = ["FraudValidators"]