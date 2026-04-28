"""
Mô-đun Workflow Emitter cho CP01 Domain Model.

Module này cung cấp implementation cho State Machine workflows với:
- DSL models (WorkflowDefinition, Transition, Guard, Effect)
- YAML parser cho workflow definitions
- State machine engine (sync + async execution)
- Event sourcing persistence
- Guards (Permission, Business, Compliance, Role, State)
- Effects (Event, Command, Notification, Audit, Compensation)

Author: Midicoder Team
Version: 1.0.0
"""

from .models import (
    WorkflowDefinition,
    Transition,
    Guard,
    Effect,
    GuardType,
    EffectType,
)
from .parser import WorkflowParser
from .fastapi import WorkflowFastAPIEmitter
from .nestjs import WorkflowNestJSEmitter

__all__ = [
    # Models
    "WorkflowDefinition",
    "Transition",
    "Guard",
    "Effect",
    "GuardType",
    "EffectType",
    # Parser
    "WorkflowParser",
    # Emitters
    "WorkflowFastAPIEmitter",
    "WorkflowNestJSEmitter",
]
