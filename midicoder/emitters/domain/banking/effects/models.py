"""
Banking Domain Models Module.

Module này định nghĩa Banking-specific EffectType.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from enum import Enum


class BankingEffectType(str, Enum):
    """
    Các loại Banking-specific effects (DP11).

    DOUBLE_ENTRY_LEDGER: Double-entry bookkeeping
    """
    DOUBLE_ENTRY_LEDGER = "double_entry_ledger"


__all__ = ["BankingEffectType"]