"""
Public API cho CP31: Scheduler & Cron Engine.

Exports:
    Models: CronSchedule, RecurrenceSchedule, CalendarSchedule,
            CalendarException, CalendarSet, ScheduleType,
            RecurrenceFrequency, ExceptionType
    Parser: SchedulerParser
    Cron: CronParser, ParsedCron
    Calendar: CalendarEngine, BusinessDayCalculator
    Timezone: TimeZoneResolver
    Emitter: SchedulerFastAPIEmitter, SchedulerNestJSEmitter

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp31_scheduler.models import (
    CalendarException,
    CalendarSchedule,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
    ScheduleType,
)
from midicoder.emitters.core.cp31_scheduler.parser import SchedulerParser
from midicoder.emitters.core.cp31_scheduler.cron_parser import CronParser, ParsedCron
from midicoder.emitters.core.cp31_scheduler.calendar_engine import (
    CalendarEngine,
    BusinessDayCalculator,
)
from midicoder.emitters.core.cp31_scheduler.timezone_resolver import TimeZoneResolver

# Emitters — optional import
try:
    from midicoder.emitters.core.cp31_scheduler.fastapi import SchedulerFastAPIEmitter
except ImportError:
    SchedulerFastAPIEmitter = None  # type: ignore

try:
    from midicoder.emitters.core.cp31_scheduler.nestjs import SchedulerNestJSEmitter
except ImportError:
    SchedulerNestJSEmitter = None  # type: ignore

__all__ = [
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
    # Emitters
    "SchedulerFastAPIEmitter",
    "SchedulerNestJSEmitter",
]
