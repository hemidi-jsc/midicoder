"""
Mô-đun Compensation Effect.

Cung cấp:
- CompensationEffect: Effect cho rollback/compensation (Saga pattern)

Author: Midicoder Team
Version: 1.0.0
"""

from typing import Any

from .base import EffectResult


class CompensationEffect:
    """
    Effect executor cho compensation/rollback.

    Execute compensation actions khi transition fail hoặc cần rollback.
    Implements Saga pattern for distributed transactions.

    Usage:
        effect = CompensationEffect(rollback="cancel_order")
        result = effect.execute(data={"order_id": "123"})
    """

    def __init__(self, rollback: str | None = None) -> None:
        self.rollback = rollback

    def execute(self, data: dict[str, Any]) -> EffectResult:
        """
        Execute compensation effect.

        Args:
            data: Data dictionary

        Returns:
            EffectResult với compensation result
        """
        # TODO: Implement Saga compensation logic
        rollback = self.rollback

        # Execute compensation (placeholder)
        return EffectResult.success(
            data={"compensation": {"rollback_action": rollback, **data}},
            message=f"Executed compensation: {rollback}",
        )