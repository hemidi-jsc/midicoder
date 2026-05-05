"""
Domain Effects Models Module.

Module này định nghĩa các domain-specific EffectTypes và GuardTypes
cho 4 domain: Banking (DP11), Manufacturing (DP05), Payments (DP12), Healthcare (DP09).

Các types trong file này là DOMAIN-SPECIFIC và không nằm trong core.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum


# ============================================================================
# Domain EffectType Enum
# ============================================================================

class DomainEffectType(str, Enum):
    """
    Các loại domain-specific effects.

    Banking:
        DOUBLE_ENTRY_LEDGER: Double-entry bookkeeping (DP11)

    Manufacturing:
        INVENTORY_RESERVATION: Inventory reservation (DP05)

    Payments:
        PAYMENT_PROCESS: Payment gateway processing (DP12)

    Healthcare:
        CLINICAL_TRANSITION: Clinical workflow transition (DP09)
    """
    DOUBLE_ENTRY_LEDGER = "double_entry_ledger"
    INVENTORY_RESERVATION = "inventory_reservation"
    PAYMENT_PROCESS = "payment_process"
    CLINICAL_TRANSITION = "clinical_transition"


# ============================================================================
# Domain GuardType Enum
# ============================================================================

class DomainGuardType(str, Enum):
    """
    Các loại domain-specific guards.

    Payments:
        FRAUD_DETECTION: Fraud detection (DP12)

    Manufacturing:
        SAFETY_CHECK: Safety check (DP05)

    Insurance:
        CLAIMS_VALIDATION: Claims validation (DP14)
    """
    FRAUD_DETECTION = "fraud_detection"
    SAFETY_CHECK = "safety_check"
    CLAIMS_VALIDATION = "claims_validation"


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "DomainEffectType",
    "DomainGuardType",
]