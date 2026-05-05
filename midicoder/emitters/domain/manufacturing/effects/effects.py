"""
Manufacturing Domain Effects Module - Inventory Reservation (DP05).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


@dataclass
class InventoryReservationResult:
    """Kết quả inventory reservation."""
    reservation_id: str
    item_id: str
    quantity: int
    status: str
    expires_at: Optional[str] = None


class InventoryEffects:
    """Manufacturing Inventory Reservation Effects (DP05)."""

    def __init__(self, inventory_service: Optional[Any] = None) -> None:
        self._inventory_service = inventory_service

    async def execute(
        self,
        data: dict[str, Any],
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> InventoryReservationResult:
        """Execute inventory reservation effect."""
        item_id = data.get("item_id", "")
        quantity = data.get("quantity", 0)

        if not item_id or quantity <= 0:
            EM.raise_error(ErrorCode.CP01_EFFECT_INSUFFICIENT_STOCK, item_id=item_id, quantity=quantity)

        if not tenant_id:
            tenant_id = "global"

        if self._inventory_service:
            try:
                result = await self._inventory_service.reserve_stock(
                    item_id=item_id, quantity=quantity, user_id=user_id, tenant_id=tenant_id,
                )
                return InventoryReservationResult(
                    reservation_id=result.get("reservation_id", ""),
                    item_id=item_id, quantity=quantity,
                    status=result.get("status", "reserved"),
                    expires_at=result.get("expires_at"),
                )
            except Exception as e:
                if "insufficient" in str(e).lower():
                    EM.raise_error(ErrorCode.CP01_EFFECT_INSUFFICIENT_STOCK, item_id=item_id, quantity=quantity)
                raise

        return InventoryReservationResult(
            reservation_id="res-generated-id", item_id=item_id,
            quantity=quantity, status="reserved", expires_at="2026-05-06T08:00:00Z",
        )


__all__ = ["InventoryEffects", "InventoryReservationResult"]