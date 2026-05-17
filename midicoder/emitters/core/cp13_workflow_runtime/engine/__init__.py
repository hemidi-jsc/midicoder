"""
Mô-đun Engine cho Workflow Emitter.

Cung cấp:
- StateMachine: Engine cho state machine execution
- EventStore: Event sourcing persistence
- SagaOrchestrator: Engine cho saga orchestration với compensation
- DAGExecutor: Engine cho DAG workflow execution

Author: Midicoder Team
Version: 1.0.0
"""

from .state_machine import StateMachine, TransitionResult, TransitionContext
from .event_store import EventStore, WorkflowEvent
from .saga_orchestrator import (
    SagaOrchestrator,
    SagaExecutionState,
    SagaStepResult,
    SagaStepStatus,
)
from .dag_executor import (
    DAGExecutor,
    DAGExecutionState,
    DAGNodeResult,
    DAGExecutionContext,
)

__all__ = [
    "StateMachine",
    "TransitionResult",
    "TransitionContext",
    "EventStore",
    "WorkflowEvent",
    "SagaOrchestrator",
    "SagaExecutionState",
    "SagaStepResult",
    "SagaStepStatus",
    "DAGExecutor",
    "DAGExecutionState",
    "DAGNodeResult",
    "DAGExecutionContext",
]