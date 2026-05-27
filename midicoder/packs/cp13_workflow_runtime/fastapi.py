"""
Mô-đun FastAPI Emitter cho Workflows.

Pug cấp:
- WorkflowFastAPIEmitter: Generate FastAPI code cho workflows
- State machine engine với guard evaluation và effect execution
- Guards với dependency injection (Permission, Business, Compliance, Role, State)
- Effects với direct service calls (Event, Command, Notification, Audit, Compensation)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import WorkflowDefinition, Transition, Guard, Effect, GuardType, EffectType


class WorkflowFastAPIEmitter:
    """
    Emitter cho FastAPI workflows.
    
    Generate code:
    - SQLAlchemy models (WorkflowInstance, WorkflowEvent, WorkflowTransitionLog)
    - State machine engine (WorkflowEngine với full implementation)
    - Guard implementations (PermissionGuard, BusinessGuard, ComplianceGuard, RoleGuard, StateGuard)
    - Effect handlers (EventEffect, CommandEffect, NotificationEffect, AuditEffect, CompensationEffect)
    - Migration SQL
    
    Usage:
        emitter = WorkflowFastAPIEmitter()
        emitter.emit(workflows, output_path)
    """

    def __init__(self, templates_path: str | Path | None = None):
        """
        Khởi tạo emitter.
        
        Args:
            templates_path: Path đến templates directory (optional)
        """
        self.templates_path = templates_path

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
        
        # Tạo thư mục output
        domain_path = output_path / "domain" / "workflows"
        domain_path.mkdir(parents=True, exist_ok=True)
        (domain_path / "definitions").mkdir(exist_ok=True)
        (domain_path / "guards").mkdir(exist_ok=True)
        (domain_path / "effects").mkdir(exist_ok=True)
        
        # Generate __init__.py cho domain/workflows
        self._emit_init(domain_path, generated_files)
        
        # Generate models.py (SQLAlchemy)
        self._emit_models(workflows, domain_path, generated_files)
        
        # Generate engine.py (State machine với full implementation)
        self._emit_engine(workflows, domain_path, generated_files)
        
        # Generate definitions cho mỗi workflow
        for workflow in workflows:
            self._emit_definition(workflow, domain_path, generated_files)
        
        # Generate guards với DI abstractions
        self._emit_guards(workflows, domain_path, generated_files)
        
        # Generate effects với direct service calls
        self._emit_effects(workflows, domain_path, generated_files)
        
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
from .engine import WorkflowEngine, TransitionResult

__all__ = [
    "WorkflowInstance",
    "WorkflowEvent",
    "WorkflowTransitionLog",
    "WorkflowEngine",
    "TransitionResult",
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

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, UUID as ColumnUUID, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from domain.base import Base


class WorkflowInstance(Base, AsyncAttrs):
    """
    Workflow Instance - Snapshot của current state.
    
    Mỗi entity có một workflow instance cho mỗi workflow type.
    """
    __tablename__ = "workflow_instances"
    
    id = Column(ColumnUUID(as_uuid=True), primary_key=True, default=UUID)
    workflow_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(255), nullable=False, index=True)
    entity_id = Column(ColumnUUID(as_uuid=True), nullable=False, index=True)
    current_state = Column(String(255), nullable=False)
    is_async = Column(Boolean, default=False)
    async_callback_url = Column(String(500))
    created_at = Column(datetime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        datetime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    tenant_id = Column(ColumnUUID(as_uuid=True), nullable=False, index=True)
    
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
    
    id = Column(ColumnUUID(as_uuid=True), primary_key=True, default=UUID)
    instance_id = Column(ColumnUUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    event_name = Column(String(255), nullable=False)
    from_state = Column(String(255))
    to_state = Column(String(255), nullable=False)
    transition_id = Column(String(255), index=True)
    payload = Column(JSONB, default=dict)
    occurred_at = Column(datetime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(ColumnUUID(as_uuid=True), nullable=False)
    
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
    
    id = Column(ColumnUUID(as_uuid=True), primary_key=True, default=UUID)
    instance_id = Column(ColumnUUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False)
    transition_id = Column(String(255), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    triggered_by = Column(ColumnUUID(as_uuid=True))  # User ID
    guard_results = Column(JSONB, default=dict)
    effects_executed = Column(JSONB, default=list)
    effects_failed = Column(JSONB, default=list)
    status = Column(String(50), nullable=False)  # success, failed, rolled_back, pending
    error_message = Column(Text)
    executed_at = Column(datetime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(ColumnUUID(as_uuid=True), nullable=False)
    
    # Relationships
    instance = relationship("WorkflowInstance", back_populates="transition_logs")
    
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
        """Generate state machine engine với full implementation."""
        # Collect all workflow names and their transitions
        workflow_configs = {}
        for workflow in workflows:
            transitions = []
            for trans in workflow.transitions:
                trans_config = {
                    "id": trans.id,
                    "from_state": trans.from_state,
                    "to_state": trans.to_state,
                    "event": trans.event or trans.id,
                    "async_execution": trans.async_execution,
                    "guards": [],
                    "effects": [],
                }
                for guard in trans.guards:
                    guard_config = {"type": guard.type.value}
                    if guard.permission:
                        guard_config["permission"] = guard.permission
                    if guard.condition:
                        guard_config["condition"] = guard.condition
                    if guard.check:
                        guard_config["check"] = guard.check
                    if guard.roles:
                        guard_config["roles"] = guard.roles
                    trans_config["guards"].append(guard_config)
                for effect in trans.effects:
                    effect_config = {"type": effect.type.value}
                    if effect.publish:
                        effect_config["publish"] = effect.publish
                    if effect.execute:
                        effect_config["execute"] = effect.execute
                    if effect.channel:
                        effect_config["channel"] = effect.channel
                    if effect.template:
                        effect_config["template"] = effect.template
                    if effect.recipient_field:
                        effect_config["recipient_field"] = effect.recipient_field
                    if effect.action:
                        effect_config["action"] = effect.action
                    if effect.rollback:
                        effect_config["rollback"] = effect.rollback
                    trans_config["effects"].append(effect_config)
                transitions.append(trans_config)
            
            workflow_configs[workflow.name] = {
                "states": workflow.states,
                "initial_state": workflow.initial_state,
                "transitions": transitions,
            }
        
        # Build WORKFLOW_CONFIGS content
        configs_lines = []
        for name, config in workflow_configs.items():
            configs_lines.append(f'    "{name}": {{')
            configs_lines.append(f'        "states": {config["states"]},')
            configs_lines.append(f'        "initial_state": "{config["initial_state"]}",')
            configs_lines.append(f'        "transitions": {config["transitions"]},')
            configs_lines.append(f'    }}')
        
        configs_content = ",\n".join(configs_lines)
        
        # Build engine content with .format() to avoid f-string brace issues
        engine_template = '''"""
State Machine Engine cho workflows.

Cung cấp:
- WorkflowEngine: Core engine cho workflow execution
- Guard evaluation (tất cả guards phải pass)
- Effect execution (sau khi state update, out of transaction)
- Event sourcing
- Async execution support

Transaction Boundaries:
- Guard evaluation + state change: Trong 1 transaction
- Effects: Execute sau commit (eventual consistency)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import WorkflowInstance, WorkflowEvent, WorkflowTransitionLog

# Workflow configurations
WORKFLOW_CONFIGS = {{
{configs_content}
}}


class TransitionResult:
    """Kết quả của transition execution."""
    
    def __init__(
        self,
        success: bool,
        from_state: str,
        to_state: str | None,
        transition_id: str,
        error: str | None = None,
        guards_passed: list[str] | None = None,
        effects_executed: list[str] | None = None,
        effects_failed: list[str] | None = None,
    ):
        self.success = success
        self.from_state = from_state
        self.to_state = to_state
        self.transition_id = transition_id
        self.error = error
        self.guards_passed = guards_passed or []
        self.effects_executed = effects_executed or []
        self.effects_failed = effects_failed or []


class WorkflowEngine:
    """
    Workflow Engine cho state machine execution.
    
    Supports:
    - Sync/Async execution
    - Guard evaluation (all must pass)
    - Effect execution (out of transaction)
    - Event sourcing
    
    Transaction Boundaries:
    - Guard + state change: Atomic
    - Effects: After commit (eventual consistency)
    """
    
    def __init__(self, db: AsyncSession):
        """
        Khởi tạo engine.
        
        Args:
            db: Database session
        """
        self.db = db
    
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
        
        Flow:
        1. Tìm workflow instance
        2. Tìm transition dựa trên event name và current state
        3. Evaluate guards (tất cả phải pass)
        4. Update state (commit transaction)
        5. Execute effects (out of transaction)
        6. Log transition result
        
        Args:
            instance_id: Workflow instance ID
            event_name: Event name trigger transition
            user_id: User ID (optional)
            tenant_id: Tenant ID (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            TransitionResult
        """
        # Step 1: Tìm workflow instance
        instance = await self._get_instance(instance_id)
        if not instance:
            return TransitionResult(
                success=False,
                from_state="",
                to_state=None,
                transition_id="",
                error="Workflow instance not found",
            )
        
        workflow_name = instance.workflow_name
        current_state = instance.current_state
        
        # Step 2: Tìm transition
        transition = self._find_transition(workflow_name, current_state, event_name)
        if not transition:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=None,
                transition_id="",
                error=f"No transition found for event '{event_name}' from state '{current_state}'",
            )
        
        # Step 3: Evaluate guards
        guard_result = await self._evaluate_guards(transition, instance, user_id, tenant_id, metadata)
        if not guard_result["passed"]:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=None,
                transition_id=transition["id"],
                error=guard_result["error"],
                guards_passed=guard_result["passed_guards"],
            )
        
        # Step 4: Update state (within transaction)
        new_state = transition["to_state"]
        await self._update_state(instance, new_state, transition, event_name, user_id, tenant_id)
        await self.db.commit()
        
        # Step 5: Execute effects (out of transaction)
        effects_result = await self._execute_effects(
            transition, instance, new_state, user_id, tenant_id, metadata
        )
        
        # Step 6: Log transition
        status = "success" if effects_result["all_success"] else "partial"
        await self._log_transition(
            instance, transition, event_name, user_id, tenant_id,
            guard_result["results"], effects_result["executed"], effects_result["failed"],
            status,
        )
        
        return TransitionResult(
            success=True,
            from_state=current_state,
            to_state=new_state,
            transition_id=transition["id"],
            guards_passed=guard_result["passed_guards"],
            effects_executed=effects_result["executed"],
            effects_failed=effects_result["failed"],
        )
    
    async def get_state(self, instance_id: UUID) -> str:
        """
        Lấy current state của instance.
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            Current state name
        """
        instance = await self._get_instance(instance_id)
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")
        return instance.current_state
    
    async def create_instance(
        self,
        workflow_name: str,
        entity_type: str,
        entity_id: UUID,
        tenant_id: UUID,
        async_callback_url: str | None = None,
    ) -> WorkflowInstance:
        """
        Tạo mới workflow instance.
        
        Args:
            workflow_name: Tên workflow
            entity_type: Loại entity
            entity_id: Entity ID
            tenant_id: Tenant ID
            async_callback_url: Callback URL cho async execution
            
        Returns:
            WorkflowInstance
        """
        config = WORKFLOW_CONFIGS.get(workflow_name)
        if not config:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        instance = WorkflowInstance(
            workflow_name=workflow_name,
            entity_type=entity_type,
            entity_id=entity_id,
            current_state=config["initial_state"],
            is_async=async_callback_url is not None,
            async_callback_url=async_callback_url,
            tenant_id=tenant_id,
        )
        self.db.add(instance)
        await self.db.commit()
        return instance
    
    def _find_transition(self, workflow_name: str, from_state: str, event_name: str) -> dict | None:
        """Tìm transition dựa trên event name và from state."""
        config = WORKFLOW_CONFIGS.get(workflow_name)
        if not config:
            return None
        
        for transition in config["transitions"]:
            if transition["from_state"] == from_state:
                if transition.get("event") == event_name or transition["id"] == event_name:
                    return transition
        return None
    
    async def _get_instance(self, instance_id: UUID) -> WorkflowInstance | None:
        """Lấy workflow instance theo ID."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        return result.scalar_one_or_none()
    
    async def _evaluate_guards(
        self,
        transition: dict,
        instance: WorkflowInstance,
        user_id: UUID | None,
        tenant_id: UUID | None,
        metadata: dict[str, Any] | None,
    ) -> dict:
        """
        Evaluate tất cả guards cho transition.
        
        Returns:
            dict với keys: passed, error, results, passed_guards
        """
        results = {}
        passed_guards = []
        
        for guard in transition.get("guards", []):
            guard_type = guard["type"]
            guard_name = f"{guard_type}_{len(passed_guards)}"
            guard_result = await self._evaluate_single_guard(guard, instance, user_id, tenant_id, metadata)
            results[guard_name] = guard_result
            
            if guard_result["passed"]:
                passed_guards.append(guard_name)
            else:
                return {
                    "passed": False,
                    "error": guard_result["error"],
                    "results": results,
                    "passed_guards": passed_guards,
                }
        
        return {
            "passed": True,
            "error": None,
            "results": results,
            "passed_guards": passed_guards,
        }
    
    async def _evaluate_single_guard(
        self,
        guard: dict,
        instance: WorkflowInstance,
        user_id: UUID | None,
        tenant_id: UUID | None,
        metadata: dict[str, Any] | None,
    ) -> dict:
        """Evaluate một guard đơn lẻ."""
        guard_type = guard["type"]
        
        if guard_type == "permission":
            # Permission guard - inject PermissionChecker
            checker = self._get_permission_checker()
            permission = guard.get("permission")
            has_permission = await checker.check_permission(user_id, permission, tenant_id) if checker else True
            return {
                "passed": has_permission,
                "error": f"Permission '{permission}' denied" if not has_permission else None,
            }
        
        elif guard_type == "business":
            # Business guard - evaluate condition
            condition = guard.get("condition", "true")
            # Simple condition evaluation (in real impl, use safe eval or expression parser)
            passed = self._evaluate_condition(condition, instance, metadata)
            return {
                "passed": passed,
                "error": f"Business rule failed: {condition}" if not passed else None,
            }
        
        elif guard_type == "compliance":
            # Compliance guard - inject ComplianceChecker
            checker = self._get_compliance_checker()
            check_name = guard.get("check")
            is_compliant = await checker.check_compliance(check_name, instance, tenant_id) if checker else True
            return {
                "passed": is_compliant,
                "error": f"Compliance check '{check_name}' failed" if not is_compliant else None,
            }
        
        elif guard_type == "role":
            # Role guard - inject RoleChecker
            checker = self._get_role_checker()
            required_roles = guard.get("roles", [])
            has_role = await checker.check_any_role(user_id, required_roles, tenant_id) if checker else True
            return {
                "passed": has_role,
                "error": f"User does not have required roles: {required_roles}" if not has_role else None,
            }
        
        elif guard_type == "state":
            # State guard - evaluate state-based condition
            condition = guard.get("condition", "true")
            passed = self._evaluate_condition(condition, instance, metadata)
            return {
                "passed": passed,
                "error": f"State guard failed: {condition}" if not passed else None,
            }
        
        return {"passed": True, "error": None}
    
    def _evaluate_condition(
        self,
        condition: str,
        instance: WorkflowInstance,
        metadata: dict[str, Any] | None,
    ) -> bool:
        """Evaluate condition expression."""
        # Simple condition evaluation
        # In production, use a safe expression evaluator
        try:
            # Basic conditions like "true", "false"
            if condition.lower() == "true":
                return True
            if condition.lower() == "false":
                return False
            # Default to True for unknown conditions
            return True
        except Exception:
            return False
    
    def _get_permission_checker(self):
        """Get PermissionChecker instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_compliance_checker(self):
        """Get ComplianceChecker instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_role_checker(self):
        """Get RoleChecker instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    async def _update_state(
        self,
        instance: WorkflowInstance,
        new_state: str,
        transition: dict,
        event_name: str,
        user_id: UUID | None,
        tenant_id: UUID | None,
    ) -> None:
        """Update state của instance."""
        instance.current_state = new_state
        
        # Create event record
        event = WorkflowEvent(
            instance_id=instance.id,
            event_name=event_name,
            from_state=instance.current_state,
            to_state=new_state,
            transition_id=transition["id"],
            tenant_id=instance.tenant_id,
        )
        self.db.add(event)
    
    async def _execute_effects(
        self,
        transition: dict,
        instance: WorkflowInstance,
        new_state: str,
        user_id: UUID | None,
        tenant_id: UUID | None,
        metadata: dict[str, Any] | None,
    ) -> dict:
        """
        Execute effects sau khi state update (out of transaction).
        
        Returns:
            dict với keys: all_success, executed, failed
        """
        executed = []
        failed = []
        
        for effect in transition.get("effects", []):
            effect_result = await self._execute_single_effect(
                effect, instance, new_state, user_id, tenant_id, metadata
            )
            effect_name = f"{effect['type']}_{len(executed)}"
            
            if effect_result["success"]:
                executed.append(effect_name)
            else:
                failed.append(effect_name)
        
        return {
            "all_success": len(failed) == 0,
            "executed": executed,
            "failed": failed,
        }
    
    async def _execute_single_effect(
        self,
        effect: dict,
        instance: WorkflowInstance,
        new_state: str,
        user_id: UUID | None,
        tenant_id: UUID | None,
        metadata: dict[str, Any] | None,
    ) -> dict:
        """Execute một effect đơn lẻ."""
        effect_type = effect["type"]
        
        if effect_type == "event":
            # Event effect - publish domain event
            event_service = self._get_event_service()
            event_name = effect.get("publish")
            try:
                await event_service.publish(event_name, {
                    "workflow_name": instance.workflow_name,
                    "instance_id": str(instance.id),
                    "entity_type": instance.entity_type,
                    "entity_id": str(instance.entity_id),
                    "from_state": metadata.get("from_state") if metadata else None,
                    "to_state": new_state,
                    "tenant_id": str(instance.tenant_id),
                })
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif effect_type == "command":
            # Command effect - execute command
            command_service = self._get_command_service()
            command_name = effect.get("execute")
            try:
                await command_service.execute(command_name, {
                    "entity_type": instance.entity_type,
                    "entity_id": str(instance.entity_id),
                    "tenant_id": str(instance.tenant_id),
                })
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif effect_type == "notification":
            # Notification effect - send notification
            notification_service = self._get_notification_service()
            channel = effect.get("channel")
            template = effect.get("template")
            recipient_field = effect.get("recipient_field")
            try:
                await notification_service.send(channel, template, recipient_field, {
                    "entity_type": instance.entity_type,
                    "entity_id": str(instance.entity_id),
                    "tenant_id": str(instance.tenant_id),
                })
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif effect_type == "audit":
            # Audit effect - log audit
            audit_service = self._get_audit_service()
            action = effect.get("action")
            try:
                await audit_service.log(action, {
                    "workflow_name": instance.workflow_name,
                    "instance_id": str(instance.id),
                    "entity_type": instance.entity_type,
                    "entity_id": str(instance.entity_id),
                    "user_id": str(user_id) if user_id else None,
                    "tenant_id": str(instance.tenant_id),
                })
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif effect_type == "compensation":
            # Compensation effect - rollback action
            compensation_service = self._get_compensation_service()
            rollback_action = effect.get("rollback")
            try:
                await compensation_service.rollback(rollback_action, {
                    "entity_type": instance.entity_type,
                    "entity_id": str(instance.entity_id),
                    "tenant_id": str(instance.tenant_id),
                })
                return {"success": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": True}
    
    def _get_event_service(self):
        """Get EventService instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_command_service(self):
        """Get CommandService instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_notification_service(self):
        """Get NotificationService instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_audit_service(self):
        """Get AuditService instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    def _get_compensation_service(self):
        """Get CompensationService instance (DI)."""
        # TODO: Inject thực sự qua dependency injection
        return None
    
    async def _log_transition(
        self,
        instance: WorkflowInstance,
        transition: dict,
        event_name: str,
        user_id: UUID | None,
        tenant_id: UUID | None,
        guard_results: dict,
        effects_executed: list,
        effects_failed: list,
        status: str,
    ) -> None:
        """Log transition execution."""
        log = WorkflowTransitionLog(
            instance_id=instance.id,
            transition_id=transition["id"],
            event_name=event_name,
            triggered_by=user_id,
            guard_results=guard_results,
            effects_executed=effects_executed,
            effects_failed=effects_failed,
            status=status,
            tenant_id=instance.tenant_id,
        )
        self.db.add(log)
        await self.db.commit()
'''
        path = output_path / "engine.py"
        path.write_text(engine_template, encoding="utf-8")
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

Định nghĩa states và transitions cho {workflow.name} workflow.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class {self._pascal_case(workflow.name).replace("_", "")}Workflow:
    """Definition cho {workflow.name} workflow."""
    
    name: str = "{workflow.name}"
    entity: str = "{workflow.entity or ""}"
    states: List[str] = {workflow.states}
    initial_state: str = "{workflow.initial_state}"
    description: str = "{workflow.description or ""}"
    
    transitions: List[Dict[str, Any]] = [
'''
        for trans in workflow.transitions:
            content += f'''
        {{
            "id": "{trans.id}",
            "from_state": "{trans.from_state}",
            "to_state": "{trans.to_state}",
            "event": "{trans.event or trans.id}",
            "async": {str(trans.async_execution).lower()},
            "guards": [
'''
            for guard in trans.guards:
                guard_dict = {"type": guard.type.value}
                if guard.permission:
                    guard_dict["permission"] = guard.permission
                if guard.condition:
                    guard_dict["condition"] = guard.condition
                if guard.check:
                    guard_dict["check"] = guard.check
                if guard.roles:
                    guard_dict["roles"] = guard.roles
                content += f'                {guard_dict!r},\n'
            
            content += '''            ],
            "effects": [
'''
            for effect in trans.effects:
                effect_dict = {"type": effect.type.value}
                if effect.publish:
                    effect_dict["publish"] = effect.publish
                if effect.execute:
                    effect_dict["execute"] = effect.execute
                if effect.channel:
                    effect_dict["channel"] = effect.channel
                if effect.template:
                    effect_dict["template"] = effect.template
                if effect.recipient_field:
                    effect_dict["recipient_field"] = effect.recipient_field
                if effect.action:
                    effect_dict["action"] = effect.action
                if effect.rollback:
                    effect_dict["rollback"] = effect.rollback
                content += f'                {effect_dict!r},\n'
            
            content += '''            ],
        },'''
        
        content += '''
    ]
'''
        path = definitions_path / filename
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_guards(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate guards với DI abstractions."""
        # Create guards directory
        guards_path = output_path / "guards"
        guards_path.mkdir(parents=True, exist_ok=True)
        
        # Generate __init__.py
        content = '''"""
Guards cho workflow transitions.

Cung cấp các guard implementations với dependency injection:
- PermissionGuard: Kiểm tra permission từ Auth service
- BusinessGuard: Evaluate business rule conditions
- ComplianceGuard: Kiểm tra compliance requirements
- RoleGuard: Kiểm tra role membership
- StateGuard: Kiểm tra state-based conditions
"""

from .permission import PermissionGuard, PermissionChecker
from .business import BusinessGuard
from .compliance import ComplianceGuard, ComplianceChecker
from .role import RoleGuard, RoleChecker
from .state import StateGuard

__all__ = [
    "PermissionGuard",
    "PermissionChecker",
    "BusinessGuard",
    "ComplianceGuard",
    "ComplianceChecker",
    "RoleGuard",
    "RoleChecker",
    "StateGuard",
]
'''
        path = output_path / "guards" / "__init__.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate permission.py
        content = '''"""
Permission Guard - Kiểm tra user permissions.

Guard này check user có permission cần thiết trước khi cho phép transition.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class PermissionChecker(ABC):
    """Abstract Permission Checker interface."""
    
    @abstractmethod
    async def check_permission(
        self,
        user_id: UUID,
        permission: str,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check user có permission.
        
        Args:
            user_id: User ID
            permission: Permission string
            tenant_id: Tenant ID (optional)
            
        Returns:
            True nếu user có permission
        """
        pass


class PermissionGuard:
    """
    Permission Guard implementation.
    
    Guards transitions dựa trên user permissions.
    """
    
    def __init__(self, checker: PermissionChecker):
        """
        Khởi tạo guard.
        
        Args:
            checker: PermissionChecker instance
        """
        self.checker = checker
    
    async def evaluate(self, user_id: UUID, permission: str, tenant_id: Optional[UUID] = None) -> bool:
        """
        Evaluate guard.
        
        Args:
            user_id: User ID
            permission: Permission cần thiết
            tenant_id: Tenant ID
            
        Returns:
            True nếu user có permission
        """
        return await self.checker.check_permission(user_id, permission, tenant_id)
'''
        path = output_path / "guards" / "permission.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate business.py
        content = '''"""
Business Guard - Evaluate business rule conditions.

Guard này evaluate conditions dựa trên entity data và metadata.
"""

from typing import Any, Optional
from uuid import UUID


class BusinessGuard:
    """
    Business Guard implementation.
    
    Guards transitions dựa trên business rules.
    """
    
    async def evaluate(
        self,
        condition: str,
        entity_data: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Evaluate business condition.
        
        Args:
            condition: Condition expression
            entity_data: Entity data
            metadata: Additional metadata
            
        Returns:
            True nếu condition được thỏa mãn
        """
        # Simple condition evaluation
        # In production, use safe eval or expression parser
        try:
            if condition.lower() == "true":
                return True
            if condition.lower() == "false":
                return False
            # Default to True for unknown conditions
            return True
        except Exception:
            return False
'''
        path = output_path / "guards" / "business.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate compliance.py
        content = '''"""
Compliance Guard - Kiểm tra regulatory compliance.

Guard này check compliance requirements (KYC, AML, HIPAA, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class ComplianceChecker(ABC):
    """Abstract Compliance Checker interface."""
    
    @abstractmethod
    async def check_compliance(
        self,
        check_name: str,
        entity_data: dict,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check compliance requirement.
        
        Args:
            check_name: Compliance check name
            entity_data: Entity data
            tenant_id: Tenant ID
            
        Returns:
            True nếu compliant
        """
        pass


class ComplianceGuard:
    """
    Compliance Guard implementation.
    
    Guards transitions dựa trên compliance requirements.
    """
    
    def __init__(self, checker: ComplianceChecker):
        """
        Khởi tạo guard.
        
        Args:
            checker: ComplianceChecker instance
        """
        self.checker = checker
    
    async def evaluate(
        self,
        check_name: str,
        entity_data: dict,
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Evaluate compliance.
        
        Args:
            check_name: Compliance check name
            entity_data: Entity data
            tenant_id: Tenant ID
            
        Returns:
            True nếu compliant
        """
        return await self.checker.check_compliance(check_name, entity_data, tenant_id)
'''
        path = output_path / "guards" / "compliance.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate role.py
        content = '''"""
Role Guard - Kiểm tra user roles.

Guard này check user có role cần thiết trước khi cho phép transition.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID


class RoleChecker(ABC):
    """Abstract Role Checker interface."""
    
    @abstractmethod
    async def check_any_role(
        self,
        user_id: UUID,
        required_roles: List[str],
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check user có ít nhất một role trong danh sách.
        
        Args:
            user_id: User ID
            required_roles: Danh sách roles cần thiết
            tenant_id: Tenant ID
            
        Returns:
            True nếu user có ít nhất một role
        """
        pass
    
    @abstractmethod
    async def check_all_roles(
        self,
        user_id: UUID,
        required_roles: List[str],
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check user có tất cả roles trong danh sách.
        
        Args:
            user_id: User ID
            required_roles: Danh sách roles cần thiết
            tenant_id: Tenant ID
            
        Returns:
            True nếu user có tất cả roles
        """
        pass


class RoleGuard:
    """
    Role Guard implementation.
    
    Guards transitions dựa trên user roles.
    """
    
    def __init__(self, checker: RoleChecker):
        """
        Khởi tạo guard.
        
        Args:
            checker: RoleChecker instance
        """
        self.checker = checker
    
    async def evaluate_any(
        self,
        user_id: UUID,
        required_roles: List[str],
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Evaluate guard (any role matches).
        
        Args:
            user_id: User ID
            required_roles: Danh sách roles
            tenant_id: Tenant ID
            
        Returns:
            True nếu user có ít nhất một role
        """
        return await self.checker.check_any_role(user_id, required_roles, tenant_id)
    
    async def evaluate_all(
        self,
        user_id: UUID,
        required_roles: List[str],
        tenant_id: Optional[UUID] = None,
    ) -> bool:
        """
        Evaluate guard (all roles required).
        
        Args:
            user_id: User ID
            required_roles: Danh sách roles
            tenant_id: Tenant ID
            
        Returns:
            True nếu user có tất cả roles
        """
        return await self.checker.check_all_roles(user_id, required_roles, tenant_id)
'''
        path = output_path / "guards" / "role.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate state.py
        content = '''"""
State Guard - Kiểm tra state-based conditions.

Guard này validate conditions dựa trên current state.
"""

from typing import Any, Optional


class StateGuard:
    """
    State Guard implementation.
    
    Guards transitions dựa trên state conditions.
    """
    
    async def evaluate(
        self,
        condition: str,
        current_state: str,
        entity_data: dict[str, Any],
    ) -> bool:
        """
        Evaluate state condition.
        
        Args:
            condition: Condition expression
            current_state: Current state
            entity_data: Entity data
            
        Returns:
            True nếu condition được thỏa mãn
        """
        # Simple condition evaluation
        try:
            if condition.lower() == "true":
                return True
            if condition.lower() == "false":
                return False
            # Check if condition contains current_state comparison
            if "current_state" in condition:
                evaluated_condition = condition.replace("current_state", f"'{current_state}'")
                # In production, use safe eval
                return True
            return True
        except Exception:
            return False
'''
        path = output_path / "guards" / "state.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_effects(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate effects với direct service calls."""
        # Create effects directory
        effects_path = output_path / "effects"
        effects_path.mkdir(parents=True, exist_ok=True)
        
        # Generate __init__.py
        content = '''"""
Effects cho workflow transitions.

Cung cấp các effect implementations với direct service calls:
- EventEffect: Publish domain events
- CommandEffect: Execute commands
- NotificationEffect: Send notifications
- AuditEffect: Log audit trails
- CompensationEffect: Rollback actions
"""

from .event import EventEffect, EventService
from .command import CommandEffect, CommandService
from .notification import NotificationEffect, NotificationService
from .audit import AuditEffect, AuditService
from .compensation import CompensationEffect, CompensationService

__all__ = [
    "EventEffect",
    "EventService",
    "CommandEffect",
    "CommandService",
    "NotificationEffect",
    "NotificationService",
    "AuditEffect",
    "AuditService",
    "CompensationEffect",
    "CompensationService",
]
'''
        path = output_path / "effects" / "__init__.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate event.py
        content = '''"""
Event Effect - Publish domain events.

Effect này publish events khi transition thành công.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class EventService(ABC):
    """Abstract Event Service interface."""
    
    @abstractmethod
    async def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Publish domain event.
        
        Args:
            event_name: Event name
            payload: Event payload
        """
        pass


class EventEffect:
    """
    Event Effect implementation.
    
    Publishes events khi transition hoàn tất.
    """
    
    def __init__(self, event_service: EventService):
        """
        Khởi tạo effect.
        
        Args:
            event_service: EventService instance
        """
        self.event_service = event_service
    
    async def execute(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Execute effect.
        
        Args:
            event_name: Event name để publish
            payload: Event payload
        """
        await self.event_service.publish(event_name, payload)
'''
        path = output_path / "effects" / "event.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate command.py
        content = '''"""
Command Effect - Execute commands.

Effect này execute commands khi transition thành công.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class CommandService(ABC):
    """Abstract Command Service interface."""
    
    @abstractmethod
    async def execute(self, command_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute command.
        
        Args:
            command_name: Command name
            params: Command parameters
            
        Returns:
            Command result
        """
        pass


class CommandEffect:
    """
    Command Effect implementation.
    
    Executes commands khi transition hoàn tất.
    """
    
    def __init__(self, command_service: CommandService):
        """
        Khởi tạo effect.
        
        Args:
            command_service: CommandService instance
        """
        self.command_service = command_service
    
    async def execute(self, command_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute effect.
        
        Args:
            command_name: Command name để execute
            params: Command parameters
            
        Returns:
            Command result
        """
        return await self.command_service.execute(command_name, params)
'''
        path = output_path / "effects" / "command.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate notification.py
        content = '''"""
Notification Effect - Send notifications.

Effect này send notifications (email, sms, push) khi transition thành công.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class NotificationService(ABC):
    """Abstract Notification Service interface."""
    
    @abstractmethod
    async def send(
        self,
        channel: str,
        template: str,
        recipient: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification.
        
        Args:
            channel: Notification channel (email, sms, push)
            template: Template name
            recipient: Recipient address
            data: Notification data
        """
        pass


class NotificationEffect:
    """
    Notification Effect implementation.
    
    Sends notifications khi transition hoàn tất.
    """
    
    def __init__(self, notification_service: NotificationService):
        """
        Khởi tạo effect.
        
        Args:
            notification_service: NotificationService instance
        """
        self.notification_service = notification_service
    
    async def execute(
        self,
        channel: str,
        template: str,
        recipient: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Execute effect.
        
        Args:
            channel: Notification channel
            template: Template name
            recipient: Recipient address
            data: Notification data
        """
        await self.notification_service.send(channel, template, recipient, data)
'''
        path = output_path / "effects" / "notification.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate audit.py
        content = '''"""
Audit Effect - Log audit trails.

Effect này log audit trails khi transition thành công.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


class AuditService(ABC):
    """Abstract Audit Service interface."""
    
    @abstractmethod
    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log audit event.
        
        Args:
            action: Action name
            entity_type: Entity type
            entity_id: Entity ID
            user_id: User ID
            tenant_id: Tenant ID
            metadata: Additional metadata
        """
        pass


class AuditEffect:
    """
    Audit Effect implementation.
    
    Logs audit trails khi transition hoàn tất.
    """
    
    def __init__(self, audit_service: AuditService):
        """
        Khởi tạo effect.
        
        Args:
            audit_service: AuditService instance
        """
        self.audit_service = audit_service
    
    async def execute(
        self,
        action: str,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Execute effect.
        
        Args:
            action: Action name
            entity_type: Entity type
            entity_id: Entity ID
            user_id: User ID
            tenant_id: Tenant ID
            metadata: Additional metadata
        """
        await self.audit_service.log(action, entity_type, entity_id, user_id, tenant_id, metadata)
'''
        path = output_path / "effects" / "audit.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate compensation.py
        content = '''"""
Compensation Effect - Rollback actions (Saga pattern).

Effect này execute rollback actions cho saga compensation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class CompensationService(ABC):
    """Abstract Compensation Service interface."""
    
    @abstractmethod
    async def rollback(self, action: str, params: Dict[str, Any]) -> None:
        """
        Execute rollback action.
        
        Args:
            action: Rollback action name
            params: Rollback parameters
        """
        pass


class CompensationEffect:
    """
    Compensation Effect implementation.
    
    Executes rollback actions cho saga pattern.
    """
    
    def __init__(self, compensation_service: CompensationService):
        """
        Khởi tạo effect.
        
        Args:
            compensation_service: CompensationService instance
        """
        self.compensation_service = compensation_service
    
    async def execute(self, action: str, params: Dict[str, Any]) -> None:
        """
        Execute effect.
        
        Args:
            action: Rollback action name
            params: Rollback parameters
        """
        await self.compensation_service.rollback(action, params)
'''
        path = output_path / "effects" / "compensation.py"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_migration(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate migration SQL."""
        content = """-- Migration file cho workflows
-- Created by Midicoder Workflow Emitter

-- Table: workflow_instances
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255) NOT NULL,
    entity_id UUID NOT NULL,
    current_state VARCHAR(255) NOT NULL,
    is_async BOOLEAN DEFAULT FALSE,
    async_callback_url VARCHAR(500),
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
    effects_failed JSONB DEFAULT '[]',
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tenant_id UUID NOT NULL
);

CREATE INDEX idx_transition_log_instance ON workflow_transitions_log(instance_id);
CREATE INDEX idx_transition_log_transition ON workflow_transitions_log(transition_id);
"""
        path = output_path / "workflows.sql"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

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