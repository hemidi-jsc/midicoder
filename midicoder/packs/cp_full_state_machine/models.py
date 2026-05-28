"""
Mô-đun DSL models cho State Machine Engine.

Cung cấp các dataclasses định nghĩa entity lifecycle state machine:
- StateMachineDefinition: Định nghĩa state machine cho một entity type
- StateInstance: Trạng thái hiện tại của một instance entity
- TransitionRecord: Lịch sử transition
- TransitionResult: Kết quả của một transition

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class TransitionAction(str, Enum):
    """Loại hành động transition."""

    TRANSITION = "transition"
    FORCE = "force"
    REVERT = "revert"


@dataclass
class StateMachineDefinition:
    """Định nghĩa state machine cho một entity type.

    Attributes:
        machine_id: Unique ID của state machine.
        entity_type: Tên entity type (vd: "Order", "Invoice").
        states: Danh sách tên states hợp lệ.
        initial_state: State mặc định khi tạo mới.
        final_states: Danh sách states kết thúc (không thể transition ra).
        transitions: Mapping {from_state: [to_states]}.
        metadata: Metadata bổ sung.
    """

    machine_id: str
    entity_type: str
    states: list[str]
    initial_state: str
    transitions: dict[str, list[str]]
    final_states: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi init."""
        if not self.machine_id or not self.machine_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F13_INVALID_STATE,
                machine_id=self.machine_id,
                reason="machine_id không được rỗng",
            )
        if not self.entity_type or not self.entity_type.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F13_INVALID_STATE,
                machine_id=self.machine_id,
                reason="entity_type không được rỗng",
            )
        if not self.states:
            raise EM.raise_error(
                ErrorCode.MDC-F13_INVALID_STATE,
                machine_id=self.machine_id,
                reason="phải có ít nhất một state",
            )
        if self.initial_state not in self.states:
            raise EM.raise_error(
                ErrorCode.MDC-F13_INVALID_STATE,
                machine_id=self.machine_id,
                initial_state=self.initial_state,
                valid_states=self.states,
                reason=f"initial_state '{self.initial_state}' không nằm trong danh sách states",
            )
        # Validate transitions reference states tồn tại
        for from_state, to_states in self.transitions.items():
            if from_state not in self.states:
                raise EM.raise_error(
                    ErrorCode.MDC-F13_INVALID_TRANSITION,
                    machine_id=self.machine_id,
                    from_state=from_state,
                    valid_states=self.states,
                    reason=f"from_state '{from_state}' không tồn tại trong danh sách states",
                )
            for to_state in to_states:
                if to_state not in self.states:
                    raise EM.raise_error(
                        ErrorCode.MDC-F13_INVALID_TRANSITION,
                        machine_id=self.machine_id,
                        to_state=to_state,
                        valid_states=self.states,
                        reason=f"to_state '{to_state}' không tồn tại trong danh sách states",
                    )
        # Validate final_states
        for fs in self.final_states:
            if fs not in self.states:
                raise EM.raise_error(
                    ErrorCode.MDC-F13_INVALID_STATE,
                    machine_id=self.machine_id,
                    final_state=fs,
                    reason=f"final_state '{fs}' không tồn tại trong danh sách states",
                )

    def is_valid_transition(self, from_state: str, to_state: str) -> bool:
        """Kiểm tra transition có hợp lệ không.

        Args:
            from_state: State nguồn.
            to_state: State đích.

        Returns:
            True nếu transition hợp lệ.
        """
        if from_state not in self.states:
            return False
        if to_state not in self.states:
            return False
        valid_targets = self.transitions.get(from_state, [])
        return to_state in valid_targets

    def get_valid_transitions(self, from_state: str) -> list[str]:
        """Lấy danh sách transitions hợp lệ từ một state.

        Args:
            from_state: State nguồn.

        Returns:
            Danh sách states có thể transition đến.
        """
        if from_state not in self.states:
            return []
        return list(self.transitions.get(from_state, []))

    def is_final_state(self, state: str) -> bool:
        """Kiểm tra xem state có phải final state không.

        Args:
            state: Tên state.

        Returns:
            True nếu là final state.
        """
        return state in self.final_states

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "machine_id": self.machine_id,
            "entity_type": self.entity_type,
            "states": self.states,
            "initial_state": self.initial_state,
            "transitions": self.transitions,
            "final_states": self.final_states,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateMachineDefinition:
        """Tạo StateMachineDefinition từ dict."""
        return cls(
            machine_id=data["machine_id"],
            entity_type=data["entity_type"],
            states=data["states"],
            initial_state=data["initial_state"],
            transitions=data["transitions"],
            final_states=data.get("final_states", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TransitionRecord:
    """Lịch sử một lần transition.

    Attributes:
        entity_id: ID của entity.
        from_state: State nguồn.
        to_state: State đích.
        user_id: ID người thực hiện (nếu có).
        tenant_id: ID tenant (nếu có).
        timestamp: Thời gian transition.
        action: Loại hành động (transition, force, revert).
        metadata: Metadata bổ sung.
    """

    entity_id: str
    from_state: str
    to_state: str
    timestamp: datetime
    action: TransitionAction = TransitionAction.TRANSITION
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "entity_id": self.entity_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value if isinstance(self.action, TransitionAction) else self.action,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionRecord:
        """Tạo TransitionRecord từ dict."""
        action_val = data.get("action", "transition")
        action = TransitionAction(action_val) if isinstance(action_val, str) else action_val

        return cls(
            entity_id=data["entity_id"],
            from_state=data["from_state"],
            to_state=data["to_state"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=action,
            user_id=data.get("user_id"),
            tenant_id=data.get("tenant_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StateInstance:
    """Trạng thái hiện tại của một instance entity.

    Attributes:
        entity_id: ID của entity.
        entity_type: Loại entity.
        current_state: State hiện tại.
        history: Lịch sử transitions.
        created_at: Thời gian tạo.
        updated_at: Thời gian cập nhật cuối.
    """

    entity_id: str
    entity_type: str
    current_state: str
    history: list[TransitionRecord] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate và init timestamps."""
        if not self.entity_id or not self.entity_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F13_INSTANCE_NOT_FOUND,
                entity_id=self.entity_id,
                reason="entity_id không được rỗng",
            )
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: TransitionAction = TransitionAction.TRANSITION,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TransitionRecord:
        """Thêm record vào lịch sử transition.

        Args:
            from_state: State nguồn.
            to_state: State đích.
            user_id: ID người thực hiện (nếu có).
            tenant_id: ID tenant (nếu có).
            action: Loại hành động.
            metadata: Metadata bổ sung.

        Returns:
            TransitionRecord mới tạo.
        """
        now = datetime.utcnow()
        record = TransitionRecord(
            entity_id=self.entity_id,
            from_state=from_state,
            to_state=to_state,
            timestamp=now,
            action=action,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        self.history.append(record)
        self.current_state = to_state
        self.updated_at = now
        return record

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "current_state": self.current_state,
            "history": [r.to_dict() for r in self.history],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateInstance:
        """Tạo StateInstance từ dict."""
        history = []
        for record_data in data.get("history", []):
            history.append(TransitionRecord.from_dict(record_data))

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            current_state=data["current_state"],
            history=history,
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class TransitionResult:
    """Kết quả của một transition.

    Attributes:
        success: Có thành công không.
        entity_id: ID của entity.
        from_state: State nguồn.
        to_state: State đích (nếu success).
        machine_id: ID của state machine.
        timestamp: Thời gian thực hiện.
        error: Lỗi (nếu fail).
        record: TransitionRecord (nếu success).
    """

    success: bool
    entity_id: str
    from_state: str
    machine_id: str
    timestamp: datetime
    to_state: Optional[str] = None
    error: Optional[str] = None
    record: Optional[TransitionRecord] = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển sang dict."""
        result = {
            "success": self.success,
            "entity_id": self.entity_id,
            "from_state": self.from_state,
            "machine_id": self.machine_id,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.to_state:
            result["to_state"] = self.to_state
        if self.error:
            result["error"] = self.error
        if self.record:
            result["record"] = self.record.to_dict()
        return result
