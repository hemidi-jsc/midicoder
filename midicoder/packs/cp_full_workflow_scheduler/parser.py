"""
Mô-đun Parser cho Workflow DSL.

Cung cấp:
- WorkflowParser: Parse YAML workflow definitions thành DSL models
- Validation: Kiểm tra syntax và semantic validation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from .models import (
    WorkflowDefinition,
    Transition,
    Guard,
    Effect,
    GuardType,
    EffectType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class WorkflowParser:
    """
    Parser cho Workflow DSL YAML.
    
    Parse YAML workflow definitions thành WorkflowDefinition objects.
    
    Usage:
        parser = WorkflowParser()
        workflows = parser.parse_file("workflows.yaml")
        
        # Or parse from string
        workflows = parser.parse(yaml_content)
    """

    def parse_file(self, file_path: str | Path) -> list[WorkflowDefinition]:
        """
        Parse workflow definitions từ file.
        
        Args:
            file_path: Path đến YAML file
            
        Returns:
            Danh sách WorkflowDefinition objects
            
        Raises:
            MidicoderError: Nếu file không tồn tại hoặc YAML không hợp lệ
        """
        path = Path(file_path)
        
        if not path.exists():
            EM.raise_error(
                ErrorCode.MDC-B01_WORKFLOW_NOT_FOUND,
                file_path=str(path),
                reason="Workflow YAML file not found",
            )
        
        try:
            content = path.read_text(encoding="utf-8")
            return self.parse(content)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                file_path=str(path),
                error=str(e),
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.MDC-B01_WORKFLOW_NOT_FOUND,
                file_path=str(path),
                error=str(e),
            )

    def parse(self, yaml_content: str) -> list[WorkflowDefinition]:
        """
        Parse workflow definitions từ YAML string.
        
        Args:
            yaml_content: YAML content string
            
        Returns:
            Danh sách WorkflowDefinition objects
            
        Raises:
            MidicoderError: Nếu YAML không hợp lệ
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                error=str(e),
            )
        
        if not data or "workflows" not in data:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                reason="YAML must contain 'workflows' key",
            )
        
        workflows = []
        for workflow_data in data.get("workflows", []):
            workflow = self._parse_workflow(workflow_data)
            workflows.append(workflow)
        
        return workflows

    def _parse_workflow(self, data: dict[str, Any]) -> WorkflowDefinition:
        """
        Parse một workflow definition từ dict.
        
        Args:
            data: Dict chứa workflow data
            
        Returns:
            WorkflowDefinition object
        """
        # Validate required fields
        if "name" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="workflow",
                field="name",
            )
        
        if "states" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="workflow",
                field="states",
            )
        
        if "initial_state" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="workflow",
                field="initial_state",
            )
        
        # Parse transitions
        transitions = []
        for trans_data in data.get("transitions", []):
            transition = self._parse_transition(trans_data)
            transitions.append(transition)
        
        return WorkflowDefinition(
            name=data["name"],
            states=data["states"],
            initial_state=data["initial_state"],
            transitions=transitions,
            entity=data.get("entity"),
            description=data.get("description"),
        )

    def _parse_transition(self, data: dict[str, Any]) -> Transition:
        """
        Parse một transition từ dict.
        
        Args:
            data: Dict chứa transition data
            
        Returns:
            Transition object
        """
        # Validate required fields
        if "from_state" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="transition",
                field="from_state",
            )
        
        if "to_state" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="transition",
                field="to_state",
            )
        
        # Parse guards
        guards = []
        for guard_data in data.get("guards", []):
            guard = self._parse_guard(guard_data)
            guards.append(guard)
        
        # Parse effects
        effects = []
        for effect_data in data.get("effects", []):
            effect = self._parse_effect(effect_data)
            effects.append(effect)
        
        return Transition(
            id=data.get("id"),
            from_state=data["from_state"],
            to_state=data["to_state"],
            event=data.get("event"),
            guards=guards,
            effects=effects,
            async_execution=data.get("async", False),
        )

    def _parse_guard(self, data: dict[str, Any]) -> Guard:
        """
        Parse một guard từ dict.
        
        Args:
            data: Dict chứa guard data
            
        Returns:
            Guard object
        """
        if "type" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="guard",
                field="type",
            )
        
        guard_type = GuardType(data["type"])
        
        return Guard(
            type=guard_type,
            permission=data.get("permission"),
            condition=data.get("condition"),
            check=data.get("check"),
            roles=data.get("roles"),
        )

    def _parse_effect(self, data: dict[str, Any]) -> Effect:
        """
        Parse một effect từ dict.
        
        Args:
            data: Dict chứa effect data
            
        Returns:
            Effect object
        """
        if "type" not in data:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                node_type="effect",
                field="type",
            )
        
        effect_type = EffectType(data["type"])
        
        return Effect(
            type=effect_type,
            publish=data.get("publish"),
            execute=data.get("execute"),
            channel=data.get("channel"),
            template=data.get("template"),
            recipient_field=data.get("recipient_field"),
            action=data.get("action"),
            rollback=data.get("rollback"),
        )


# ===========================================================================
# Scheduler DSL Parser (từ CP31)
# ===========================================================================

from typing import Any as SP_Any, Optional as SP_Optional

from .models import (
    CalendarException,
    CalendarSchedule,
    CalendarSet,
    CronSchedule,
    ExceptionType,
    RecurrenceFrequency,
    RecurrenceSchedule,
    ScheduleType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class SchedulerParser:
    """Parser cho scheduler DSL.

    Convert YAML/dict sang typed model objects.

    Ví dụ:
        >>> parser = SchedulerParser()
        >>> data = {"type": "cron", "schedule_id": "daily-backup", "cron_expression": "0 2 * * *"}
        >>> schedule = parser.parse(data)
        >>> isinstance(schedule, CronSchedule)
        True
    """

    def parse(self, data: dict[str, SP_Any]) -> SP_Any:
        """Parse một schedule dict thành model object.

        Args:
            data: Dict chứa schedule data với field "type".

        Returns:
            CronSchedule, RecurrenceSchedule, CalendarSchedule, CalendarSet,
            hoặc CalendarException tùy theo type.

        Raises:
            MidicoderError: Nếu data invalid hoặc type không known.
        """
        if not data or not isinstance(data, dict):
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="Data phải là dict không rỗng",
            )

        # Ưu tiên schedule_type để tránh conflict với ExceptionType.type
        item_type = data.get("schedule_type")
        if item_type is None:
            # Fallback: dùng "type" nhưng chỉ khi data KHÔNG có các keys của exception
            if "exception_id" in data:
                item_type = "exception"
            elif "calendar_set_id" in data and "name" in data and "exceptions" in data:
                item_type = "calendar_set"
            else:
                item_type = data.get("type")

        if item_type == "calendar_set":
            return self._parse_calendar_set(data)
        elif item_type == "exception":
            return self._parse_exception(data)
        elif not item_type:
            # Try auto-detect
            if "cron_expression" in data:
                return self._parse_cron(data)
            elif "frequency" in data:
                return self._parse_recurrence(data)
            elif "calendar_set_id" in data:
                return self._parse_calendar_schedule(data)
            else:
                raise EM.raise_error(
                    ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                    data=str(data)[:200],
                    reason="Không xác định được loại schedule — thiếu field 'type'",
                )

        type_map = {
            "cron": self._parse_cron,
            "recurrence": self._parse_recurrence,
            "calendar": self._parse_calendar_schedule,
        }

        parser_fn = type_map.get(item_type)
        if not parser_fn:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                type=item_type,
                known=list(type_map.keys()),
            )

        return parser_fn(data)

    def parse_list(self, data_list: list[dict[str, SP_Any]]) -> list[SP_Any]:
        """Parse danh sách schedule dicts.

        Args:
            data_list: Danh sách dict chứa schedule data.

        Returns:
            Danh sách model objects.
        """
        return [self.parse(d) for d in data_list]

    def _parse_cron(self, data: dict[str, SP_Any]) -> CronSchedule:
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="CronSchedule cần field 'schedule_id'",
            )
        if "cron_expression" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CronSchedule cần field 'cron_expression'",
            )

        return CronSchedule(
            schedule_id=data["schedule_id"],
            cron_expression=data["cron_expression"],
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def _parse_recurrence(self, data: dict[str, SP_Any]) -> RecurrenceSchedule:
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="RecurrenceSchedule cần field 'schedule_id'",
            )

        from datetime import date as date_type

        freq_val = data.get("frequency", "daily")
        frequency = RecurrenceFrequency(freq_val) if isinstance(freq_val, str) else freq_val

        start_date = None
        if data.get("start_date"):
            start_date = date_type.fromisoformat(data["start_date"])

        end_date = None
        if data.get("end_date"):
            end_date = date_type.fromisoformat(data["end_date"])

        return RecurrenceSchedule(
            schedule_id=data["schedule_id"],
            frequency=frequency,
            interval=data.get("interval", 1),
            days_of_week=data.get("days_of_week", []),
            day_of_month=data.get("day_of_month"),
            start_date=start_date,
            end_date=end_date,
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def _parse_calendar_schedule(self, data: dict[str, SP_Any]) -> CalendarSchedule:
        if "schedule_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="CalendarSchedule cần field 'schedule_id'",
            )
        if "calendar_set_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CalendarSchedule cần field 'calendar_set_id'",
            )
        if "base_schedule" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                schedule_id=data.get("schedule_id"),
                reason="CalendarSchedule cần field 'base_schedule'",
            )

        return CalendarSchedule(
            schedule_id=data["schedule_id"],
            base_schedule=data["base_schedule"],
            calendar_set_id=data["calendar_set_id"],
            skip_holidays=data.get("skip_holidays", True),
            business_days_only=data.get("business_days_only", False),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def _parse_calendar_set(self, data: dict[str, SP_Any]) -> CalendarSet:
        if "calendar_set_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="CalendarSet cần field 'calendar_set_id'",
            )
        if "name" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                calendar_set_id=data.get("calendar_set_id"),
                reason="CalendarSet cần field 'name'",
            )

        exceptions = []
        for exc_data in data.get("exceptions", []):
            exceptions.append(self._parse_exception(exc_data))

        return CalendarSet(
            calendar_set_id=data["calendar_set_id"],
            name=data["name"],
            exceptions=exceptions,
            country=data.get("country", ""),
        )

    def _parse_exception(self, data: dict[str, SP_Any]) -> CalendarException:
        if "exception_id" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                reason="CalendarException cần field 'exception_id'",
            )
        if "date" not in data:
            raise EM.raise_error(
                ErrorCode.MDC-F20_DSL_PARSE_ERROR,
                exception_id=data.get("exception_id"),
                reason="CalendarException cần field 'date'",
            )

        from datetime import date as date_type

        type_val = data.get("type", "holiday")
        exc_type = ExceptionType(type_val) if isinstance(type_val, str) else type_val

        override_date = None
        if data.get("override_date"):
            override_date = date_type.fromisoformat(data["override_date"])

        return CalendarException(
            exception_id=data["exception_id"],
            date=date_type.fromisoformat(data["date"]),
            type=exc_type,
            label=data.get("label", ""),
            override_date=override_date,
        )