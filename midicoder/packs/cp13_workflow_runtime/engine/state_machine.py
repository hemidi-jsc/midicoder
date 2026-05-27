"""
Mô-đun State Machine Engine.

Cung cấp:
- StateMachine: Core engine cho state machine execution
- TransitionContext: Context cho transition execution
- TransitionResult: Kết quả của transition

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import UUID, uuid4

from ..models import WorkflowDefinition, Transition, Guard, Effect
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


@dataclass
class TransitionContext:
    """
    Context cho transition execution.
    
    Chứa tất cả thông tin cần thiết để evaluate guards và execute effects.
    
    Attributes:
        workflow_name: Tên workflow
        instance_id: Instance ID
        entity_type: Entity type
        entity_id: Entity ID
        from_state: State nguồn
        to_state: State đích
        transition: Transition definition
        user_id: User ID (optional)
        tenant_id: Tenant ID
        metadata: Additional metadata
    """
    workflow_name: str
    instance_id: UUID
    entity_type: str
    entity_id: UUID
    from_state: str
    to_state: str
    transition: Transition
    user_id: UUID | None = None
    tenant_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionResult:
    """
    Kết quả của transition execution.
    
    Attributes:
        success: Có thành công không
        from_state: State nguồn
        to_state: State đích (nếu success)
        transition_id: Transition ID
        instance_id: Instance ID
        timestamp: Thời gian execute
        error: Error message (nếu fail)
        guards_passed: Danh sách guards đã pass
        effects_executed: Danh sách effects đã execute
    """
    success: bool
    from_state: str
    to_state: str | None
    transition_id: str
    instance_id: UUID
    timestamp: datetime
    error: str | None = None
    guards_passed: list[str] = field(default_factory=list)
    effects_executed: list[str] = field(default_factory=list)


class StateMachine:
    """
    State Machine Engine cho workflow execution.
    
    Hỗ trợ:
    - Sync execution
    - Async execution (queue-based)
    - Guard evaluation
    - Effect execution
    - Event sourcing
    
    Usage:
        sm = StateMachine(workflow_definition)
        result = sm.transition(instance_id, "submit_order", user_id, tenant_id)
    """

    def __init__(
        self,
        workflow: WorkflowDefinition,
        guard_evaluator: Callable[[Guard, TransitionContext], bool] | None = None,
        effect_executor: Callable[[Effect, TransitionContext], bool] | None = None,
    ):
        """
        Khởi tạo StateMachine.
        
        Args:
            workflow: Workflow definition
            guard_evaluator: Custom guard evaluator (optional)
            effect_executor: Custom effect executor (optional)
        """
        self.workflow = workflow
        self.guard_evaluator = guard_evaluator or self._default_guard_evaluator
        self.effect_executor = effect_executor or self._default_effect_executor
        
        # In-memory state storage (should be replaced with database)
        self._instances: dict[UUID, str] = {}
        self._event_log: list[dict[str, Any]] = []

    def _default_guard_evaluator(self, guard: Guard, context: TransitionContext) -> bool:
        """
        Default guard evaluator.
        
        TODO: Implement actual guard logic for each type.
        Currently returns True for all guards.
        
        Args:
            guard: Guard to evaluate
            context: Transition context
            
        Returns:
            True if guard passes, False otherwise
        """
        # TODO: Implement guard types:
        # - PERMISSION: Check user permissions
        # - BUSINESS: Evaluate business condition
        # - COMPLIANCE: Check compliance requirements
        # - ROLE: Check user roles
        # - STATE: Check state conditions
        return True

    def _default_effect_executor(self, effect: Effect, context: TransitionContext) -> bool:
        """
        Default effect executor.
        
        TODO: Implement actual effect logic for each type.
        Currently returns True for all effects.
        
        Args:
            effect: Effect to execute
            context: Transition context
            
        Returns:
            True if effect executes successfully
        """
        # TODO: Implement effect types:
        # - EVENT: Publish domain event
        # - COMMAND: Execute command
        # - NOTIFICATION: Send notification
        # - AUDIT: Log audit trail
        # - COMPENSATION: Execute rollback
        return True

    def get_state(self, instance_id: UUID) -> str:
        """
        Lấy current state của instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Current state name
            
        Raises:
            MidicoderError: Nếu instance không tồn tại
        """
        if instance_id not in self._instances:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_NOT_FOUND,
                instance_id=str(instance_id),
                reason="Workflow instance not found",
            )
        return self._instances[instance_id]

    def create_instance(self, entity_type: str, entity_id: UUID) -> UUID:
        """
        Tạo workflow instance mới.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            
        Returns:
            Instance ID
        """
        instance_id = uuid4()
        self._instances[instance_id] = self.workflow.initial_state
        
        # Log creation event
        self._event_log.append({
            "event_type": "instance_created",
            "instance_id": str(instance_id),
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "state": self.workflow.initial_state,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return instance_id

    def get_transition(self, event_name: str, from_state: str | None = None) -> Transition | None:
        """
        Tìm transition bằng event name hoặc from_state.
        
        Args:
            event_name: Event name
            from_state: Optional from state filter
            
        Returns:
            Transition hoặc None nếu không tìm thấy
        """
        for transition in self.workflow.transitions:
            if transition.event == event_name:
                if from_state is None or transition.from_state == from_state:
                    return transition
        return None

    def can_transition(self, instance_id: UUID, event_name: str) -> bool:
        """
        Kiểm tra có thể transition không (không execute).
        
        Args:
            instance_id: Instance ID
            event_name: Event name
            
        Returns:
            True nếu có thể transition
        """
        current_state = self.get_state(instance_id)
        transition = self.get_transition(event_name, current_state)
        
        if transition is None:
            return False
        
        # Create mock context for guard evaluation
        context = TransitionContext(
            workflow_name=self.workflow.name,
            instance_id=instance_id,
            entity_type="",
            entity_id=uuid4(),
            from_state=current_state,
            to_state=transition.to_state,
            transition=transition,
        )
        
        # Evaluate all guards
        for guard in transition.guards:
            if not self.guard_evaluator(guard, context):
                return False
        
        return True

    def transition(
        self,
        instance_id: UUID,
        event_name: str,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        entity_type: str = "",
        entity_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """
        Execute transition.
        
        Args:
            instance_id: Instance ID
            event_name: Event name trigger transition
            user_id: User ID (optional)
            tenant_id: Tenant ID (optional)
            entity_type: Entity type (optional)
            entity_id: Entity ID (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            TransitionResult
            
        Raises:
            MidicoderError: Nếu transition không hợp lệ
        """
        current_state = self.get_state(instance_id)
        transition = self.get_transition(event_name, current_state)
        
        if transition is None:
            # Try to find transition without event name
            for t in self.workflow.transitions:
                if t.from_state == current_state and t.id == event_name:
                    transition = t
                    break
        
        if transition is None:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_INVALID_TRANSITION,
                workflow_name=self.workflow.name,
                instance_id=str(instance_id),
                current_state=current_state,
                event_name=event_name,
                reason="No valid transition found for event",
            )
        
        # Check if already in target state
        if transition.to_state == current_state:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_ALREADY_IN_STATE,
                workflow_name=self.workflow.name,
                instance_id=str(instance_id),
                state=current_state,
                reason="Instance already in target state",
            )
        
        # Create context
        context = TransitionContext(
            workflow_name=self.workflow.name,
            instance_id=instance_id,
            entity_type=entity_type or "",
            entity_id=entity_id or uuid4(),
            from_state=current_state,
            to_state=transition.to_state,
            transition=transition,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        
        # Evaluate guards
        guards_passed = []
        for guard in transition.guards:
            try:
                if self.guard_evaluator(guard, context):
                    guards_passed.append(f"{guard.type.value}")
                else:
                    return TransitionResult(
                        success=False,
                        from_state=current_state,
                        to_state=None,
                        transition_id=transition.id,
                        instance_id=instance_id,
                        timestamp=datetime.utcnow(),
                        error=f"Guard failed: {guard.type.value}",
                        guards_passed=guards_passed,
                    )
            except Exception as e:
                return TransitionResult(
                    success=False,
                    from_state=current_state,
                    to_state=None,
                    transition_id=transition.id,
                    instance_id=instance_id,
                    timestamp=datetime.utcnow(),
                    error=f"Guard evaluation error: {str(e)}",
                    guards_passed=guards_passed,
                )
        
        # Execute effects
        effects_executed = []
        for effect in transition.effects:
            try:
                if self.effect_executor(effect, context):
                    effects_executed.append(f"{effect.type.value}")
            except Exception as e:
                # Log error but continue (effects are best-effort)
                pass
        
        # Update state
        self._instances[instance_id] = transition.to_state
        
        # Log transition event
        self._event_log.append({
            "event_type": "transition",
            "instance_id": str(instance_id),
            "transition_id": transition.id,
            "from_state": current_state,
            "to_state": transition.to_state,
            "event_name": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id) if user_id else None,
            "guards_passed": guards_passed,
            "effects_executed": effects_executed,
        })
        
        return TransitionResult(
            success=True,
            from_state=current_state,
            to_state=transition.to_state,
            transition_id=transition.id,
            instance_id=instance_id,
            timestamp=datetime.utcnow(),
            guards_passed=guards_passed,
            effects_executed=effects_executed,
        )

    def get_event_log(self, instance_id: UUID) -> list[dict[str, Any]]:
        """
        Lấy event log cho instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Danh sách events
        """
        return [
            e for e in self._event_log
            if e.get("instance_id") == str(instance_id)
        ]

    def rebuild_state(self, instance_id: UUID) -> str:
        """
        Rebuild state từ event log (event sourcing).
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Rebuilt state
        """
        events = self.get_event_log(instance_id)
        
        if not events:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_EVENT_STORE_ERROR,
                instance_id=str(instance_id),
                reason="No events found for instance",
            )
        
        # Find creation event
        creation = next(
            (e for e in events if e.get("event_type") == "instance_created"),
            None,
        )
        
        if not creation:
            return self.workflow.initial_state
        
        current_state = creation.get("state", self.workflow.initial_state)
        
        # Apply all transition events
        for event in events:
            if event.get("event_type") == "transition":
                current_state = event.get("to_state", current_state)
        
        return current_state