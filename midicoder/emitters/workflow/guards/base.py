"""
Mô-đun Base Guard Evaluator.

Cung cấp:
- GuardEvaluator: Abstract base class cho tất cả guard evaluators

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from ..models import Guard, TransitionContext


class GuardEvaluator(ABC):
    """
    Abstract base class cho guard evaluation.
    
    Tất cả guard evaluators phải implement method evaluate().
    
    Usage:
        class MyGuard(GuardEvaluator):
            async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
                return True  # Guard passed
    """

    @abstractmethod
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        """
        Evaluate guard và return kết quả.
        
        Args:
            guard: Guard definition
            context: Transition context
            
        Returns:
            True nếu guard pass, False nếu fail
            
        Raises:
            MidicoderError: Nếu có lỗi khi evaluate
        """
        pass

    @classmethod
    def create_evaluator(cls, guard: Guard) -> "GuardEvaluator":
        """
        Factory method để tạo evaluator phù hợp với guard type.
        
        Args:
            guard: Guard definition
            
        Returns:
            GuardEvaluator instance phù hợp
            
        Raises:
            ValueError: Nếu guard type không được hỗ trợ
        """
        evaluators = {
            "permission": PermissionEvaluator,
            "business": BusinessEvaluator,
            "compliance": ComplianceEvaluator,
            "role": RoleEvaluator,
            "state": StateEvaluator,
        }
        
        evaluator_class = evaluators.get(guard.type.value)
        if evaluator_class is None:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                guard_type=guard.type.value,
            )

        return evaluator_class()


class PermissionEvaluator(GuardEvaluator):
    """Evaluator cho permission guards."""
    
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        # TODO: Integrate với CP03/CP04 Auth system
        # Check if user has the required permission
        return True  # Default: pass


class BusinessEvaluator(GuardEvaluator):
    """Evaluator cho business rule guards."""
    
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        # TODO: Evaluate business condition expression
        # Use a safe expression evaluator
        return True  # Default: pass


class ComplianceEvaluator(GuardEvaluator):
    """Evaluator cho compliance guards."""
    
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        # TODO: Check compliance requirements (RX01-RX12)
        return True  # Default: pass


class RoleEvaluator(GuardEvaluator):
    """Evaluator cho role guards."""
    
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        # TODO: Check if user has any of the required roles
        return True  # Default: pass


class StateEvaluator(GuardEvaluator):
    """Evaluator cho state-based guards."""
    
    async def evaluate(self, guard: Guard, context: TransitionContext) -> bool:
        # TODO: Evaluate state condition
        return True  # Default: pass


# Export all evaluators
__all__ = [
    "GuardEvaluator",
    "PermissionEvaluator",
    "BusinessEvaluator",
    "ComplianceEvaluator",
    "RoleEvaluator",
    "StateEvaluator",
]