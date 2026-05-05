"""Payments Domain Models (DP12)."""

from __future__ import annotations
from enum import Enum


class PaymentEffectType(str, Enum):
    """Payments-specific effects (DP12)."""
    PAYMENT_PROCESS = "payment_process"


class PaymentGuardType(str, Enum):
    """Payments-specific guards (DP12)."""
    FRAUD_DETECTION = "fraud_detection"


__all__ = ["PaymentEffectType", "PaymentGuardType"]