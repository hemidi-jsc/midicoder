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
                ErrorCode.CP01_WORKFLOW_NOT_FOUND,
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
                ErrorCode.CP01_WORKFLOW_NOT_FOUND,
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