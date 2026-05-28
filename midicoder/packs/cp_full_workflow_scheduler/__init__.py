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
- Cron scheduling & calendar engine (từ CP31)

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

# ===========================================================================
# Scheduler & Cron Engine imports (từ CP31)
# ===========================================================================

from midicoder.packs.cp_full_workflow_scheduler.models import (
    CalendarException,
    CalendarSchedule,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
    ScheduleType,
)
from midicoder.packs.cp_full_workflow_scheduler.parser import SchedulerParser
from midicoder.packs.cp_full_workflow_scheduler.cron_parser import CronParser, ParsedCron
from midicoder.packs.cp_full_workflow_scheduler.calendar_engine import (
    CalendarEngine,
    BusinessDayCalculator,
)
from midicoder.packs.cp_full_workflow_scheduler.timezone_resolver import TimeZoneResolver

# Scheduler emitters — optional import
try:
    from midicoder.packs.cp_full_workflow_scheduler.fastapi import SchedulerFastAPIEmitter
except ImportError:
    SchedulerFastAPIEmitter = None  # type: ignore

try:
    from midicoder.packs.cp_full_workflow_scheduler.nestjs import SchedulerNestJSEmitter
except ImportError:
    SchedulerNestJSEmitter = None  # type: ignore


__all__ = [
    # Workflow Models
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
    # Worker
    "JobSpec",
    "WorkerConfig",
    "TimeoutPolicy",
    "DeadlockDetection",
    # Parser
    "WorkflowParser",
    # Emitters
    "WorkflowFastAPIEmitter",
    "WorkflowNestJSEmitter",
    # ===========================================================================
    # CP31: Scheduler & Cron Engine exports
    # ===========================================================================
    # Models
    "CronSchedule",
    "RecurrenceSchedule",
    "CalendarSchedule",
    "CalendarException",
    "CalendarSet",
    "ScheduleType",
    "RecurrenceFrequency",
    "ExceptionType",
    # Parser
    "SchedulerParser",
    # Cron
    "CronParser",
    "ParsedCron",
    # Calendar
    "CalendarEngine",
    "BusinessDayCalculator",
    # Timezone
    "TimeZoneResolver",
    # Scheduler Emitters
    "SchedulerFastAPIEmitter",
    "SchedulerNestJSEmitter",
]
