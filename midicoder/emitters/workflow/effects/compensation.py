"""
Mô-đun Compensation Effect.

Cung cấp:
- CompensationEffect: Effect cho rollback/compensation (Saga pattern)

Author: Midicoder Team
Version: 1.0.0
"""

from ..models import Effect, TransitionContext
from .base import EffectResult


class CompensationEffect:
    """
    Effect executor cho compensation/rollback.
    
    Execute compensation actions khi transition fail hoặc cần rollback.
    Implements Saga pattern for distributed transactions.
    
    Usage:
        effect = CompensationEffect()
        result = await effect.execute(effect_def, context)
    """

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        """
        Execute compensation effect.
        
        Args:
            effect: Compensation effect definition
            context: Transition context
            
        Returns:
            EffectResult với compensation result
        """
        # TODO: Implement Saga compensation logic
        rollback = effect.rollback
        
        # Compensation payload
        payload = {
            "rollback_action": rollback,
            "entity_type": context.entity_type,
            "entity_id": str(context.entity_id),
            "original_from_state": context.from_state,
            "original_to_state": context.to_state,
            "transition_id": context.transition.id,
        }
        
        # Execute compensation (placeholder)
        return EffectResult.success(
            effect.type.value,
            message=f"Executed compensation: {rollback}",
            data={"compensation": payload},
        )