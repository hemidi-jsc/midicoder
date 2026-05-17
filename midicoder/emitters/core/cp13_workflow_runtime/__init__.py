"""
Mô-đun Workflow Emitter cho CP13: Background Job & Workflow Generator.

Module này cung cấp implementation cho State Machine workflows với:
- DSL models (WorkflowDefinition, Transition, Guard, Effect)
- YAML parser cho workflow definitions
- State machine engine (sync + async execution)
- Event sourcing persistence
- Guards (Permission, Business, Compliance, Role, State)
- Effects (Event, Command, Notification, Audit, Compensation)
- Job scheduling (JobDefinition, JobInstance, SchedulePolicy)

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
    JobSpec,
    WorkerConfig,
    TimeoutPolicy,
    DeadlockDetection,
)
from .parser import WorkflowParser
from .scheduler import (
    JobPriority,
    SchedulePolicy,
    JobDefinition,
    JobInstance,
    RetryPolicy,
    DeadLetterQueue,
    JobRetryTracker,
)
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
    # Scheduler
    "JobPriority",
    "SchedulePolicy",
    "JobDefinition",
    "JobInstance",
    "RetryPolicy",
    "DeadLetterQueue",
    "JobRetryTracker",
    # Parser
    "WorkflowParser",
    # Emitters
    "WorkflowFastAPIEmitter",
    "WorkflowNestJSEmitter",
]
