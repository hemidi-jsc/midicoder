"""
Mô-đun DSL models cho Workflow Emitter.

Cung cấp các dataclasses định nghĩa workflow state machine:
- WorkflowDefinition: Định nghĩa workflow với states và transitions
- Transition: Chuyển trạng thái với guards và effects
- Guard: Điều kiện để transition có thể fire
- Effect: Side effects khi transition fire

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class GuardType(str, Enum):
    """
    Các loại guard cho transition.
    
    Attributes:
        PERMISSION: Kiểm tra permission từ CP03/CP04
        BUSINESS: Business rule validation
        COMPLIANCE: Regulatory compliance check
        ROLE: Role membership check
        STATE: State-based condition
    """
    PERMISSION = "permission"
    BUSINESS = "business"
    COMPLIANCE = "compliance"
    ROLE = "role"
    STATE = "state"


class EffectType(str, Enum):
    """
    Các loại effect khi transition fire.
    
    Attributes:
        EVENT: Publish domain event (CP05)
        COMMAND: Execute command (CP01)
        NOTIFICATION: Send notification (CP12)
        AUDIT: Log audit trail (CP14)
        COMPENSATION: Rollback action (Saga pattern)
    """
    EVENT = "event"
    COMMAND = "command"
    NOTIFICATION = "notification"
    AUDIT = "audit"
    COMPENSATION = "compensation"


@dataclass
class Guard:
    """
    Guard - Điều kiện để transition có thể fire.
    
    Guards được evaluate trước khi transition. Tất cả guards phải pass
    thì transition mới được thực hiện.
    
    Attributes:
        type: Loại guard (permission, business, compliance, role, state)
        permission: Permission string (cho permission guard)
        condition: Business condition expression (cho business/state guard)
        check: Compliance check name (cho compliance guard)
        roles: Danh sách roles (cho role guard)
        
    Example:
        >>> # Permission guard
        >>> Guard(
        ...     type=GuardType.PERMISSION,
        ...     permission="order.approve"
        ... )
        
        >>> # Business rule guard
        >>> Guard(
        ...     type=GuardType.BUSINESS,
        ...     condition="items.length > 0 and total > 0"
        ... )
    """
    type: GuardType
    permission: str | None = None
    condition: str | None = None
    check: str | None = None
    roles: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate guard configuration sau khi init."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate guard có đủ required fields cho type.
        
        Raises:
            MidicoderError: Nếu guard không hợp lệ
        """
        if self.type == GuardType.PERMISSION:
            if not self.permission:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                    guard_type=self.type.value,
                    missing_field="permission",
                    reason="Permission guard requires 'permission' field",
                )
        
        elif self.type == GuardType.BUSINESS:
            if not self.condition:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                    guard_type=self.type.value,
                    missing_field="condition",
                    reason="Business guard requires 'condition' field",
                )
        
        elif self.type == GuardType.COMPLIANCE:
            if not self.check:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                    guard_type=self.type.value,
                    missing_field="check",
                    reason="Compliance guard requires 'check' field",
                )
        
        elif self.type == GuardType.ROLE:
            if not self.roles:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                    guard_type=self.type.value,
                    missing_field="roles",
                    reason="Role guard requires 'roles' field",
                )
        
        elif self.type == GuardType.STATE:
            if not self.condition:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_GUARD_FAILED,
                    guard_type=self.type.value,
                    missing_field="condition",
                    reason="State guard requires 'condition' field",
                )


@dataclass
class Effect:
    """
    Effect - Side effect khi transition fire.
    
    Effects được execute sau khi transition thành công.
    
    Attributes:
        type: Loại effect (event, command, notification, audit, compensation)
        publish: Event name để publish (cho event effect)
        execute: Command name để execute (cho command effect)
        channel: Notification channel (email, sms, push)
        template: Notification template name
        recipient_field: Field chứa recipient info
        action: Audit action name
        rollback: Compensation/rollback action
        
    Example:
        >>> # Event publishing
        >>> Effect(
        ...     type=EffectType.EVENT,
        ...     publish="OrderSubmitted"
        ... )
        
        >>> # Notification
        >>> Effect(
        ...     type=EffectType.NOTIFICATION,
        ...     channel="email",
        ...     template="order_approved",
        ...     recipient_field="customer_email"
        ... )
    """
    type: EffectType
    publish: str | None = None
    execute: str | None = None
    channel: str | None = None
    template: str | None = None
    recipient_field: str | None = None
    action: str | None = None
    rollback: str | None = None

    def __post_init__(self) -> None:
        """Validate effect configuration sau khi init."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate effect có đủ required fields cho type.
        
        Raises:
            MidicoderError: Nếu effect không hợp lệ
        """
        if self.type == EffectType.EVENT:
            if not self.publish:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_EFFECT_FAILED,
                    effect_type=self.type.value,
                    missing_field="publish",
                    reason="Event effect requires 'publish' field",
                )
        
        elif self.type == EffectType.COMMAND:
            if not self.execute:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_EFFECT_FAILED,
                    effect_type=self.type.value,
                    missing_field="execute",
                    reason="Command effect requires 'execute' field",
                )
        
        elif self.type == EffectType.NOTIFICATION:
            if not self.channel:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_EFFECT_FAILED,
                    effect_type=self.type.value,
                    missing_field="channel",
                    reason="Notification effect requires 'channel' field",
                )
        
        elif self.type == EffectType.AUDIT:
            if not self.action:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_EFFECT_FAILED,
                    effect_type=self.type.value,
                    missing_field="action",
                    reason="Audit effect requires 'action' field",
                )
        
        elif self.type == EffectType.COMPENSATION:
            if not self.rollback:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_EFFECT_FAILED,
                    effect_type=self.type.value,
                    missing_field="rollback",
                    reason="Compensation effect requires 'rollback' field",
                )


@dataclass
class Transition:
    """
    Transition - Chuyển trạng thái trong workflow.
    
    Transition xác định cách entity chuyển từ state này sang state khác,
    bao gồm guards (điều kiện) và effects (side effects).
    
    Attributes:
        id: Transition ID (tự generate nếu không có)
        from_state: State nguồn
        to_state: State đích
        event: Event name trigger transition (optional)
        guards: Danh sách guards phải pass
        effects: Danh sách effects khi transition fire
        async_execution: Có execute async không (dùng CP13)
        
    Example:
        >>> Transition(
        ...     id="submit_order",
        ...     from_state="draft",
        ...     to_state="submitted",
        ...     event="submit_order",
        ...     guards=[
        ...         Guard(type=GuardType.PERMISSION, permission="order.submit")
        ...     ],
        ...     effects=[
        ...         Effect(type=EffectType.EVENT, publish="OrderSubmitted")
        ...     ]
        ... )
    """
    from_state: str
    to_state: str
    id: str | None = None
    event: str | None = None
    guards: list[Guard] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    async_execution: bool = False

    def __post_init__(self) -> None:
        """Generate ID nếu chưa có."""
        if not self.id:
            # Generate ID từ from_state và to_state
            self.id = f"{self.from_state}_to_{self.to_state}"


@dataclass
class WorkflowDefinition:
    """
    Workflow Definition - Định nghĩa state machine hoàn chỉnh.
    
    Workflow definition bao gồm tất cả states và transitions,
    cùng với metadata như entity association và description.
    
    Attributes:
        name: Tên workflow (unique)
        states: Danh sách states
        initial_state: State khởi đầu
        transitions: Danh sách transitions
        entity: Entity name association (optional)
        description: Mô tả workflow (optional)
        
    Example:
        >>> WorkflowDefinition(
        ...     name="order_lifecycle",
        ...     entity="Order",
        ...     states=["draft", "submitted", "approved", "shipped"],
        ...     initial_state="draft",
        ...     transitions=[
        ...         Transition(
        ...             from_state="draft",
        ...             to_state="submitted",
        ...             guards=[...],
        ...             effects=[...]
        ...         )
        ...     ],
        ...     description="Vòng đời đơn hàng từ draft đến shipped"
        ... )
    """
    name: str
    states: list[str]
    initial_state: str
    transitions: list[Transition]
    entity: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate workflow definition sau khi init."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate workflow definition hợp lệ.
        
        Checks:
        - States không rỗng
        - Initial state tồn tại trong states
        - All transitions có valid from/to states
        
        Raises:
            MidicoderError: Nếu workflow không hợp lệ
        """
        # Check states không rỗng
        if not self.states:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_INVALID_STATE,
                workflow_name=self.name,
                reason="Workflow must have at least one state",
            )
        
        # Check initial state tồn tại
        if self.initial_state not in self.states:
            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_INVALID_STATE,
                workflow_name=self.name,
                initial_state=self.initial_state,
                available_states=self.states,
                reason=f"Initial state '{self.initial_state}' not in states",
            )
        
        # Validate transitions
        for transition in self.transitions:
            if transition.from_state not in self.states:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_INVALID_TRANSITION,
                    workflow_name=self.name,
                    transition_id=transition.id,
                    from_state=transition.from_state,
                    available_states=self.states,
                    reason=f"Transition from state not in workflow states",
                )
            
            if transition.to_state not in self.states:
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_INVALID_TRANSITION,
                    workflow_name=self.name,
                    transition_id=transition.id,
                    to_state=transition.to_state,
                    available_states=self.states,
                    reason=f"Transition to state not in workflow states",
                )

    def get_transitions_from(self, state: str) -> list[Transition]:
        """
        Lấy danh sách transitions từ một state.
        
        Args:
            state: State name
            
        Returns:
            Danh sách transitions từ state này
        """
        return [t for t in self.transitions if t.from_state == state]

    def get_transitions_to(self, state: str) -> list[Transition]:
        """
        Lấy danh sách transitions đến một state.
        
        Args:
            state: State name
            
        Returns:
            Danh sách transitions đến state này
        """
        return [t for t in self.transitions if t.to_state == state]

    def is_final_state(self, state: str) -> bool:
        """
        Kiểm tra state có phải final state không (không có outgoing transitions).
        
        Args:
            state: State name
            
        Returns:
            True nếu là final state
        """
        return len(self.get_transitions_from(state)) == 0