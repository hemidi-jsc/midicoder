"""
Mô-đun State Machine Engine cho Workflow Emitter.

Cung cấp:
- StateMachine: Engine cho state machine execution
- EventStore: Event sourcing persistence

Author: Midicoder Team
Version: 1.0.0
"""

from .state_machine import StateMachine, TransitionResult, TransitionContext
from .event_store import EventStore, WorkflowEvent

__all__ = [
    "StateMachine",
    "TransitionResult",
    "TransitionContext",
    "EventStore",
    "WorkflowEvent",
]