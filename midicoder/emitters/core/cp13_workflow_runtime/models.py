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


# ===========================================================================
# Job & Worker Config
# ===========================================================================


@dataclass
class JobSpec:
    """
    JobSpec - Đặc tả công việc nền (background job).

    Định nghĩa một job cần thực thi ở nền, bao gồm thông tin schedule,
    retry policy, priority, và metadata kèm theo.

    Attributes:
        job_id: ID duy nhất của job
        task_name: Tên task/handler để thực thi
        payload: Dữ liệu đầu vào cho job
        schedule: Cấu hình schedule (cron_expr hoặc interval_seconds)
        retry_policy: Chính sách retry khi job thất bại
        timeout_seconds: Timeout tối đa cho job (giây)
        priority: Mức độ ưu tiên (critical, high, normal, low)
        enabled: Job có được kích hoạt không
        metadata: Metadata bổ sung cho job
    """
    job_id: str
    task_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    schedule: dict[str, Any] | None = None
    retry_policy: dict[str, Any] | None = None
    timeout_seconds: int = 3600
    priority: str = "normal"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate job specification sau khi init."""
        if not self.job_id:
            EM.raise_error(
                ErrorCode.CP13_JOB_SPEC_INVALID,
                reason="job_id must not be empty",
            )
        if not self.task_name:
            EM.raise_error(
                ErrorCode.CP13_JOB_SPEC_INVALID,
                reason="task_name must not be empty",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển JobSpec sang dict."""
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "payload": self.payload,
            "schedule": self.schedule,
            "retry_policy": self.retry_policy,
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobSpec":
        """Tạo JobSpec từ dict."""
        return cls(
            job_id=data.get("job_id", ""),
            task_name=data.get("task_name", ""),
            payload=data.get("payload", {}),
            schedule=data.get("schedule", None),
            retry_policy=data.get("retry_policy", None),
            timeout_seconds=data.get("timeout_seconds", 3600),
            priority=data.get("priority", "normal"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WorkerConfig:
    """
    WorkerConfig - Cấu hình worker pool.

    Định nghĩa cách worker pool hoạt động: kích thước pool, số job
    chạy song song tối đa, queue bindings, và các tham số giao tiếp.

    Attributes:
        pool_size: Số worker trong pool
        max_concurrent: Số job tối đa chạy song song
        queue_bindings: Danh sách queue mà worker sẽ lắng nghe
        prefetch_count: Số job prefetch từ queue
        heartbeat_seconds: Interval heartbeat (giây)
        auto_ack: Tự động acknowledge job sau khi nhận
        timeout_seconds: Timeout tối đa cho một job (giây)
    """
    pool_size: int = 4
    max_concurrent: int = 10
    queue_bindings: list[str] = field(default_factory=list)
    prefetch_count: int = 1
    heartbeat_seconds: int = 30
    auto_ack: bool = False
    timeout_seconds: int = 3600

    def __post_init__(self) -> None:
        """Validate worker config sau khi init."""
        if self.pool_size <= 0:
            EM.raise_error(
                ErrorCode.CP13_WORKER_CONFIG_INVALID,
                reason="pool_size must be greater than 0",
            )
        if self.max_concurrent <= 0:
            EM.raise_error(
                ErrorCode.CP13_WORKER_CONFIG_INVALID,
                reason="max_concurrent must be greater than 0",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WorkerConfig sang dict."""
        return {
            "pool_size": self.pool_size,
            "max_concurrent": self.max_concurrent,
            "queue_bindings": self.queue_bindings,
            "prefetch_count": self.prefetch_count,
            "heartbeat_seconds": self.heartbeat_seconds,
            "auto_ack": self.auto_ack,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkerConfig":
        """Tạo WorkerConfig từ dict."""
        return cls(
            pool_size=data.get("pool_size", 4),
            max_concurrent=data.get("max_concurrent", 10),
            queue_bindings=data.get("queue_bindings", []),
            prefetch_count=data.get("prefetch_count", 1),
            heartbeat_seconds=data.get("heartbeat_seconds", 30),
            auto_ack=data.get("auto_ack", False),
            timeout_seconds=data.get("timeout_seconds", 3600),
        )


@dataclass
class TimeoutPolicy:
    """
    TimeoutPolicy - Chính sách timeout cho các bước trong workflow.

    Định nghĩa ngưỡng timeout ở nhiều mức độ (step, workflow, idle)
    và hành vi khi vượt quá timeout.

    Attributes:
        step_timeout_seconds: Timeout cho từng step (giây)
        workflow_timeout_seconds: Timeout cho toàn bộ workflow (giây)
        idle_timeout_seconds: Timeout khi không có hoạt động (giây)
        on_timeout: Hành vi khi timeout (fail/skip/compensate)
    """
    step_timeout_seconds: int = 300
    workflow_timeout_seconds: int = 3600
    idle_timeout_seconds: int = 600
    on_timeout: str = "fail"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TimeoutPolicy sang dict."""
        return {
            "step_timeout_seconds": self.step_timeout_seconds,
            "workflow_timeout_seconds": self.workflow_timeout_seconds,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "on_timeout": self.on_timeout,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeoutPolicy":
        """Tạo TimeoutPolicy từ dict."""
        return cls(
            step_timeout_seconds=data.get("step_timeout_seconds", 300),
            workflow_timeout_seconds=data.get("workflow_timeout_seconds", 3600),
            idle_timeout_seconds=data.get("idle_timeout_seconds", 600),
            on_timeout=data.get("on_timeout", "fail"),
        )


@dataclass
class DeadlockDetection:
    """
    DeadlockDetection - Cấu hình phát hiện deadlock.

    Định nghĩa cơ chế phát hiện và xử lý deadlock khi có nhiều
    workflow/job cạnh tranh tài nguyên.

    Attributes:
        enabled: Có bật deadlock detection không
        check_interval_seconds: Khoảng thời gian kiểm tra (giây)
        max_wait_seconds: Thời gian chờ tối đa trước khi coi là deadlock
        on_deadlock: Hành vi khi phát hiện deadlock (abort_youngest/abort_all/notify)
    """
    enabled: bool = True
    check_interval_seconds: int = 10
    max_wait_seconds: int = 300
    on_deadlock: str = "abort_youngest"

    def __post_init__(self) -> None:
        """Validate deadlock detection config sau khi init."""
        valid_strategies = ("abort_youngest", "abort_all", "notify")
        if self.on_deadlock not in valid_strategies:
            EM.raise_error(
                ErrorCode.CP13_DEADLOCK_CONFIG_INVALID,
                reason=f"on_deadlock must be one of {valid_strategies}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DeadlockDetection sang dict."""
        return {
            "enabled": self.enabled,
            "check_interval_seconds": self.check_interval_seconds,
            "max_wait_seconds": self.max_wait_seconds,
            "on_deadlock": self.on_deadlock,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeadlockDetection":
        """Tạo DeadlockDetection từ dict."""
        return cls(
            enabled=data.get("enabled", True),
            check_interval_seconds=data.get("check_interval_seconds", 10),
            max_wait_seconds=data.get("max_wait_seconds", 300),
            on_deadlock=data.get("on_deadlock", "abort_youngest"),
        )


# ===========================================================================
# DAG Workflow Execution
# ===========================================================================


class DAGExecutionMode(str, Enum):
    """
    Chế độ thực thi DAG.

    - sequential: Chạy nodes tuần tự theo topological order
    - parallel: Chạy nodes independent song song
    - parallel_with_fanin: Parallel branches, fan-in vào merge node
    - dynamic: Dynamic node creation at runtime
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PARALLEL_WITH_FANIN = "parallel_with_fanin"
    DYNAMIC = "dynamic"


class DAGFailurePolicy(str, Enum):
    """
    Chính sách xử lý failure trong DAG.

    - fail_fast: Stop toàn bộ DAG khi node fail
    - skip_and_continue: Skip node fail, continue nodes khác
    - retry_then_skip: Retry node, skip nếu vẫn fail
    - compensate: Chạy compensation step (saga undo)
    """
    FAIL_FAST = "fail_fast"
    SKIP_AND_CONTINUE = "skip_and_continue"
    RETRY_THEN_SKIP = "retry_then_skip"
    COMPENSATE = "compensate"


@dataclass
class DAGNode:
    """
    Node trong DAG workflow — step/operation cần thực hiện.

    Attributes:
        node_id: ID duy nhất của node
        node_type: Loại node (task, branch, merge, wait, condition)
        handler: Handler function/class để execute
        inputs: Input parameters cho node
        outputs: Output data từ node
        depends_on: Danh sách node IDs mà node này phụ thuộc
        timeout_seconds: Timeout cho node execution
        retry_count: Số lần retry nếu fail
        description: Mô tả node
    """
    node_id: str
    node_type: str = "task"
    handler: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DAG node sang dict."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "handler": self.handler,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "depends_on": self.depends_on,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DAGNode":
        """Tạo DAGNode từ dict."""
        return cls(
            node_id=data.get("node_id", ""),
            node_type=data.get("node_type", "task"),
            handler=data.get("handler", ""),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", []),
            depends_on=data.get("depends_on", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 0),
            description=data.get("description", ""),
        )


@dataclass
class DAGWorkflow:
    """
    DAG workflow — directed acyclic graph của các nodes.

    Attributes:
        workflow_id: ID duy nhất của workflow
        name: Tên workflow
        execution_mode: Chế độ execution (sequential, parallel, parallel_with_fanin, dynamic)
        failure_policy: Failure policy (fail_fast, skip_and_continue, retry_then_skip, compensate)
        nodes: Danh sách nodes trong DAG
        entry_points: Node IDs bắt đầu (roots)
        exit_points: Node IDs kết thúc (leaves)
        max_parallelism: Số nodes tối đa chạy song song
        description: Mô tả workflow
    """
    workflow_id: str
    name: str
    execution_mode: DAGExecutionMode = DAGExecutionMode.SEQUENTIAL
    failure_policy: DAGFailurePolicy = DAGFailurePolicy.FAIL_FAST
    nodes: list[DAGNode] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    exit_points: list[str] = field(default_factory=list)
    max_parallelism: int = 4
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DAG workflow sang dict."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "execution_mode": self.execution_mode.value,
            "failure_policy": self.failure_policy.value,
            "nodes": [n.to_dict() for n in self.nodes],
            "entry_points": self.entry_points,
            "exit_points": self.exit_points,
            "max_parallelism": self.max_parallelism,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DAGWorkflow":
        """Tạo DAGWorkflow từ dict."""
        return cls(
            workflow_id=data.get("workflow_id", ""),
            name=data.get("name", ""),
            execution_mode=DAGExecutionMode(data.get("execution_mode", "sequential")),
            failure_policy=DAGFailurePolicy(data.get("failure_policy", "fail_fast")),
            nodes=[DAGNode.from_dict(n) for n in data.get("nodes", [])],
            entry_points=data.get("entry_points", []),
            exit_points=data.get("exit_points", []),
            max_parallelism=data.get("max_parallelism", 4),
            description=data.get("description", ""),
        )


# ===========================================================================
# Saga Pattern
# ===========================================================================


class SagaCompensationStrategy(str, Enum):
    """
    Chiến lược compensation cho saga.

    - backward: Undo steps từ cuối về đầu (reverse order)
    - forward: Continue và fix (forward recovery)
    - mixed: Kết hợp backward + forward
    """
    BACKWARD = "backward"
    FORWARD = "forward"
    MIXED = "mixed"


@dataclass
class SagaStep:
    """
    Step trong saga — action + compensation pair.

    Mỗi step có action (làm) và compensation (undo). Khi step fail,
    saga orchestration chạy compensation cho tất cả steps đã hoàn thành.

    Attributes:
        step_id: ID duy nhất của step
        action: Action handler (làm)
        compensation: Compensation handler (undo)
        inputs: Input parameters
        timeout_seconds: Timeout cho step
        is_compensatable: Có thể compensate không (một số operations là idempotent)
        description: Mô tả step
    """
    step_id: str
    action: str
    compensation: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    is_compensatable: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển saga step sang dict."""
        return {
            "step_id": self.step_id,
            "action": self.action,
            "compensation": self.compensation,
            "inputs": self.inputs,
            "timeout_seconds": self.timeout_seconds,
            "is_compensatable": self.is_compensatable,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SagaStep":
        """Tạo SagaStep từ dict."""
        return cls(
            step_id=data.get("step_id", ""),
            action=data.get("action", ""),
            compensation=data.get("compensation", ""),
            inputs=data.get("inputs", {}),
            timeout_seconds=data.get("timeout_seconds", 300),
            is_compensatable=data.get("is_compensatable", True),
            description=data.get("description", ""),
        )


@dataclass
class SagaDefinition:
    """
    Saga definition — sequence của steps với compensation.

    Attributes:
        saga_id: ID duy nhất của saga
        name: Tên saga
        steps: Danh sách saga steps (action + compensation)
        compensation_strategy: Chiến lược compensation (backward, forward, mixed)
        enable_saga_log: Có ghi saga log không (cho audit/debug)
        max_retry_on_failure: Số lần retry toàn bộ saga
        description: Mô tả saga
    """
    saga_id: str
    name: str
    steps: list[SagaStep] = field(default_factory=list)
    compensation_strategy: SagaCompensationStrategy = SagaCompensationStrategy.BACKWARD
    enable_saga_log: bool = True
    max_retry_on_failure: int = 0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển saga definition sang dict."""
        return {
            "saga_id": self.saga_id,
            "name": self.name,
            "steps": [s.to_dict() for s in self.steps],
            "compensation_strategy": self.compensation_strategy.value,
            "enable_saga_log": self.enable_saga_log,
            "max_retry_on_failure": self.max_retry_on_failure,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SagaDefinition":
        """Tạo SagaDefinition từ dict."""
        return cls(
            saga_id=data.get("saga_id", ""),
            name=data.get("name", ""),
            steps=[SagaStep.from_dict(s) for s in data.get("steps", [])],
            compensation_strategy=SagaCompensationStrategy(data.get("compensation_strategy", "backward")),
            enable_saga_log=data.get("enable_saga_log", True),
            max_retry_on_failure=data.get("max_retry_on_failure", 0),
            description=data.get("description", ""),
        )