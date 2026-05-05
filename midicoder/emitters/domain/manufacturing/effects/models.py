"""
Manufacturing Domain Models Module.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum


class ManufacturingEffectType(str, Enum):
    """Manufacturing-specific effects (DP05)."""
    INVENTORY_RESERVATION = "inventory_reservation"


class ManufacturingGuardType(str, Enum):
    """Manufacturing-specific guards (DP05)."""
    SAFETY_CHECK = "safety_check"


__all__ = ["ManufacturingEffectType", "ManufacturingGuardType"]