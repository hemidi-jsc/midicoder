"""Insurance Domain Models (DP14)."""

from __future__ import annotations
from enum import Enum


class InsuranceGuardType(str, Enum):
    """Insurance-specific guards (DP14)."""
    CLAIMS_VALIDATION = "claims_validation"


__all__ = ["InsuranceGuardType"]