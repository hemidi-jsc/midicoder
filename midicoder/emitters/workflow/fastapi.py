"""
Mô-đun FastAPI Emitter cho Workflows.

Cung cấp:
- WorkflowFastAPIEmitter: Generate FastAPI code cho workflows

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, PackageLoader

from .models import WorkflowDefinition
from .parser import WorkflowParser


class WorkflowFastAPIEmitter:
    """
    Emitter cho FastAPI workflows.
    
    Generate code:
    - SQLAlchemy models
    - State machine engine
    - Guard implementations
    - Effect handlers
    - Migration SQL
    
    Usage:
        emitter = WorkflowFastAPIEmitter()
        emitter.emit(workflows, output_path)
    """

    def __init__(self, templates_path: str | Path | None = None):
        """
        Khởi tạo emitter.
        
        Args:
            templates_path: Path đến templates directory
        """
        self.jinja_env = Environment(
            loader=PackageLoader("midicoder.stacks.fastapi.templates", "domain/workflows")
            if templates_path is None
            else FileSystemLoader(str(templates_path)),
            autoescape=True,
        )
        
        # Register filters
        self.jinja_env.filters["snake_case"] = self._snake_case
        self.jinja_env.filters["pascal_case"] = self._pascal_case

    @staticmethod
    def _snake_case(value: str) -> str:
        """Convert to snake_case."""
        result = ""
        for i, char in enumerate(value):
            if char.isupper() and i > 0:
                result += "_"
            result += char.lower()
        return result

    @staticmethod
    def _pascal_case(value: str) -> str:
        """Convert to PascalCase."""
        parts = value.replace("_", " ").replace("-", " ").split()
        return "".join(word.capitalize() for word in parts)

    def emit(self, workflows: list[WorkflowDefinition], output_path: str | Path) -> list[str]:
        """
        Emit workflow code cho FastAPI.
        
        Args:
            workflows: Danh sách workflow definitions
            output_path: Output directory path
            
        Returns:
            Danh sách file paths đã generate
        """
        output_path = Path(output_path)
        generated_files = []
        
        # Create output directories
        domain_path = output_path / "domain" / "workflows"
        domain_path.mkdir(parents=True, exist_ok=True)
        (domain_path / "definitions").mkdir(exist_ok=True)
        (domain_path / "guards").mkdir(exist_ok=True)
        (domain_path / "effects").mkdir(exist_ok=True)
        
        # Generate __init__.py for domain/workflows
        self._emit_init(domain_path, generated_files)
        
        # Generate models.py (SQLAlchemy)
        self._emit_models(workflows, domain_path, generated_files)
        
        # Generate engine.py (State machine)
        self._emit_engine(workflows, domain_path, generated_files)
        
        # Generate definitions
        for workflow in workflows:
            self._emit_definition(workflow, domain_path, generated_files)
        
        # Generate guards
        self._emit_guards(domain_path, generated_files)
        
        # Generate effects
        self._emit_effects(domain_path, generated_files)
        
        # Generate migration SQL
        self._emit_migration(workflows, domain_path, generated_files)
        
        return generated_files

    def _emit_init(self, output_path: Path, generated_files: list[str]) -> None:
        """Generate __init__.py."""
        content = '''"""
Module workflows cho domain models.

Cung cấp state machine engine cho workflow execution.
"""

from .models import WorkflowInstance, WorkflowEvent, WorkflowTransitionLog
from .engine import WorkflowEngine

__all__ = [
    "WorkflowInstance",
    "WorkflowEvent",
    "WorkflowTransitionLog",
    "WorkflowEngine",
]
'''
        path = output_path / "__init__.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_models(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate SQLAlchemy models."""
        content = '''"""
SQLAlchemy models cho workflows.

Cung cấp:
- WorkflowInstance: Snapshot của current state
- WorkflowEvent: Event log cho audit trail
- WorkflowTransitionLog: Log chi tiết transition execution
"""

from sqlalchemy import Column, String, UUID, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from uuid_extensions import uuid7
from datetime import datetime

from .base import Base


class WorkflowInstance(Base, AsyncAttrs):
    """
    Workflow Instance - Snapshot của current state.
    
    Mỗi entity có một workflow instance cho mỗi workflow type.
    """
    __tablename__ = "workflow_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    workflow_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(255), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    current_state = Column(String(255), nullable=False)
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        datetime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Relationships
    events = relationship("WorkflowEvent", back_populates="instance", lazy="dynamic")
    transition_logs = relationship(
        "WorkflowTransitionLog",
        back_populates="instance",
        lazy="dynamic",
    )
    
    __table_args__ = (
        Index("idx_workflow_instance_unique", "workflow_name", "entity_type", "entity_id", "tenant_id", unique=True),
    )


class WorkflowEvent(Base, AsyncAttrs):
    """
    Workflow Event - Event log cho audit trail.
    
    Mỗi transition tạo ra một event.
    """
    __tablename__ = "workflow_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    event_name = Column(String(255), nullable=False)
    from_state = Column(String(255))
    to_state = Column(String(255), nullable=False)
    transition_id = Column(String(255), index=True)
    payload = Column(JSONB, default=dict)
    occurred_at = Column(datetime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    instance = relationship("WorkflowInstance", back_populates="events")
    
    __table_args__ = (
        Index("idx_workflow_event_instance", "instance_id"),
    )


class WorkflowTransitionLog(Base, AsyncAttrs):
    """
    Workflow Transition Log - Log chi tiết transition execution.
    
    Ghi lại guard results, effects executed, và error information.
    """
    __tablename__ = "workflow_transitions_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    transition_id = Column(String(255), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    triggered_by = Column(UUID(as_uuid=True))  # User ID
    guard_results = Column(JSONB, default=dict)
    effects_executed = Column(JSONB, default=list)
    status = Column(String(50), nullable=False)  # success, failed, rolled_back
    error_message = Column(Text)
    executed_at = Column(datetime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    instance = relationship("WorkflowTransitionLog", back_populates="instance")
    
    __table_args__ = (
        Index("idx_transition_log_instance", "instance_id"),
    )
'''
        path = output_path / "models.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_engine(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate state machine engine."""
        # TODO: Implement full engine generation
        content = '''"""
State Machine Engine cho workflows.

Cung cấp:
- WorkflowEngine: Core engine cho workflow execution
- Guard evaluation
- Effect execution
- Event sourcing
"""

from typing import Any
from uuid import UUID
from dataclasses import dataclass


@dataclass
class TransitionResult:
    """Kết quả của transition execution."""
    success: bool
    from_state: str
    to_state: str | None
    transition_id: str
    error: str | None = None
    guards_passed: list[str] = None
    effects_executed: list[str] = None
    
    def __post_init__(self):
        if self.guards_passed is None:
            self.guards_passed = []
        if self.effects_executed is None:
            self.effects_executed = []


class WorkflowEngine:
    """
    Workflow Engine cho state machine execution.
    
    Supports:
    - Sync/Async execution
    - Guard evaluation
    - Effect execution
    - Event sourcing
    """
    
    def __init__(self):
        """Khởi tạo engine."""
        pass
    
    async def transition(
        self,
        instance_id: UUID,
        event_name: str,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """
        Execute transition.
        
        Args:
            instance_id: Workflow instance ID
            event_name: Event name trigger transition
            user_id: User ID (optional)
            tenant_id: Tenant ID (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            TransitionResult
        """
        # TODO: Implement transition logic
        return TransitionResult(
            success=False,
            from_state="",
            to_state=None,
            transition_id="",
            error="Not implemented",
        )
    
    def get_state(self, instance_id: UUID) -> str:
        """Lấy current state của instance."""
        # TODO: Implement
        pass
'''
        path = output_path / "engine.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_definition(
        self,
        workflow: WorkflowDefinition,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate workflow definition."""
        definitions_path = output_path / "definitions"
        filename = f"{workflow.name}.py"
        
        content = f'''"""
Workflow definition for {workflow.name}.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class {self._pascal_case(workflow.name)}Workflow:
    """Definition cho {workflow.name} workflow."""
    
    states = {workflow.states}
    initial_state = "{workflow.initial_state}"
    
    transitions = [
'''
        for trans in workflow.transitions:
            content += f'''
        {{
            "id": "{trans.id}",
            "from_state": "{trans.from_state}",
            "to_state": "{trans.to_state}",
            "event": "{trans.event or trans.id}",
            "async": {str(trans.async_execution).lower()},
        }},'''
        
        content += '''
    ]
'''
        path = definitions_path / filename
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_guards(self, output_path: Path, generated_files: list[str]) -> None:
        """Generate guards __init__.py."""
        content = '''"""
Guards cho workflow transitions.
"""

from .permission import PermissionGuard
from .business import BusinessGuard
from .compliance import ComplianceGuard

__all__ = [
    "PermissionGuard",
    "BusinessGuard",
    "ComplianceGuard",
]
'''
        path = output_path / "guards" / "__init__.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_effects(self, output_path: Path, generated_files: list[str]) -> None:
        """Generate effects __init__.py."""
        content = '''"""
Effects cho workflow transitions.
"""

from .event import EventEffect
from .command import CommandEffect
from .notification import NotificationEffect
from .audit import AuditEffect

__all__ = [
    "EventEffect",
    "CommandEffect",
    "NotificationEffect",
    "AuditEffect",
]
'''
        path = output_path / "effects" / "__init__.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_migration(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate migration SQL."""
        content = '''-- Migration file cho workflows
-- Created by Midicoder Workflow Emitter

-- Table: workflow_instances
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_id UUID NOT NULL,
    current_state VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id UUID NOT NULL
);

CREATE INDEX idx_workflow_instances_workflow ON workflow_instances(workflow_name);
CREATE INDEX idx_workflow_instances_entity ON workflow_instances(entity_type, entity_id);
CREATE INDEX idx_workflow_instances_tenant ON workflow_instances(tenant_id);
CREATE UNIQUE INDEX idx_workflow_instances_unique ON workflow_instances(workflow_name, entity_type, entity_id, tenant_id);

-- Table: workflow_events
CREATE TABLE IF NOT EXISTS workflow_events (
    id UUID PRIMARY KEY,
    instance_id UUID REFERENCES workflow_instances(id) ON DELETE CASCADE,
    event_name VARCHAR(255) NOT NULL,
    from_state VARCHAR(255),
    to_state VARCHAR(255) NOT NULL,
    transition_id VARCHAR(255),
    payload JSONB DEFAULT '{}',
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id UUID NOT NULL
);

CREATE INDEX idx_workflow_events_instance ON workflow_events(instance_id);
CREATE INDEX idx_workflow_events_transition ON workflow_events(transition_id);

-- Table: workflow_transitions_log
CREATE TABLE IF NOT EXISTS workflow_transitions_log (
    id UUID PRIMARY KEY,
    instance_id UUID REFERENCES workflow_instances(id) ON DELETE CASCADE,
    transition_id VARCHAR(255) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    triggered_by UUID,
    guard_results JSONB DEFAULT '{}',
    effects_executed JSONB DEFAULT '[]',
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id UUID NOT NULL
);

CREATE INDEX idx_transition_log_instance ON workflow_transitions_log(instance_id);
CREATE INDEX idx_transition_log_transition ON workflow_transitions_log(transition_id);
'''
        path = output_path / "workflows.sql"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))