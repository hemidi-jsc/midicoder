"""
State Machine Engine — runtime cho entity lifecycle FSM.

Module này cung cấp:
- StateMachineEngine: Engine runtime để validate và execute transitions
- StateRegistry: Registry để quản lý nhiều state machines

Boundary: CP32 = 1 entity FSM (lightweight). CP13 = workflow orchestration.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from datetime import datetime

from .models import (
    StateInstance,
    StateMachineDefinition,
    TransitionAction,
    TransitionRecord,
    TransitionResult,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class StateMachineEngine:
    """Engine runtime cho entity lifecycle state machine.

    Cung cấp:
    - Validate transitions theo StateMachineDefinition
    - Execute transitions với audit trail
    - Tích hợp CP14 (audit log) và CP05 (event publish)

    Ví dụ:
        >>> engine = StateMachineEngine()
        >>> engine.register(state_machine_definition)
        >>> result = engine.transition("order-123", "APPROVED", user_id="admin")
        >>> result.success
        True
    """

    def __init__(
        self,
        audit_logger: Optional[Callable] = None,
        event_publisher: Optional[Callable] = None,
    ) -> None:
        """Khởi tạo engine.

        Args:
            audit_logger: Callback để ghi audit log (CP14 integration).
                Ký hiệu: (action: str, entity: str, metadata: dict) -> None
            event_publisher: Callback để publish event (CP05 integration).
                Ký hiệu: (event_name: str, payload: dict) -> None
        """
        self._definitions: dict[str, StateMachineDefinition] = {}
        self._instances: dict[str, StateInstance] = {}
        self._audit_logger = audit_logger
        self._event_publisher = event_publisher

    def register(self, definition: StateMachineDefinition) -> None:
        """Đăng ký một state machine definition.

        Args:
            definition: StateMachineDefinition cần đăng ký.
        """
        self._definitions[definition.machine_id] = definition

    def unregister(self, machine_id: str) -> None:
        """Hủy đăng ký state machine.

        Args:
            machine_id: ID của state machine.
        """
        if machine_id not in self._definitions:
            raise EM.raise_error(
                ErrorCode.CP32_REGISTRY_NOT_FOUND,
                machine_id=machine_id,
                reason="State machine không tồn tại trong registry",
            )
        del self._definitions[machine_id]

    def get_definition(self, machine_id: str) -> StateMachineDefinition:
        """Lấy state machine definition theo ID.

        Args:
            machine_id: ID của state machine.

        Returns:
            StateMachineDefinition.

        Raises:
            MidicoderError: Nếu không tìm thấy.
        """
        if machine_id not in self._definitions:
            raise EM.raise_error(
                ErrorCode.CP32_REGISTRY_NOT_FOUND,
                machine_id=machine_id,
                reason="State machine không tồn tại trong registry",
            )
        return self._definitions[machine_id]

    def get_valid_transitions(self, machine_id: str, current_state: str) -> list[str]:
        """Lấy danh sách transitions hợp lệ từ một state.

        Args:
            machine_id: ID của state machine.
            current_state: State hiện tại.

        Returns:
            Danh sách states có thể transition đến.
        """
        definition = self.get_definition(machine_id)
        return definition.get_valid_transitions(current_state)

    def create_instance(
        self,
        entity_id: str,
        machine_id: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> StateInstance:
        """Tạo state instance mới cho entity.

        Args:
            entity_id: ID của entity.
            machine_id: ID của state machine.
            tenant_id: ID tenant (nếu có).
            metadata: Metadata bổ sung.

        Returns:
            StateInstance mới tạo ở initial state.
        """
        definition = self.get_definition(machine_id)
        instance = StateInstance(
            entity_id=entity_id,
            entity_type=definition.entity_type,
            current_state=definition.initial_state,
        )
        # Ghi audit log tạo instance
        self._write_audit(
            action="state_instance_created",
            entity_id=entity_id,
            entity_type=definition.entity_type,
            machine_id=machine_id,
            state=definition.initial_state,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        self._instances[entity_id] = instance
        return instance

    def get_instance(self, entity_id: str) -> StateInstance:
        """Lấy state instance theo entity_id.

        Args:
            entity_id: ID của entity.

        Returns:
            StateInstance.

        Raises:
            MidicoderError: Nếu không tìm thấy.
        """
        if entity_id not in self._instances:
            raise EM.raise_error(
                ErrorCode.CP32_INSTANCE_NOT_FOUND,
                entity_id=entity_id,
                reason="State instance không tồn tại",
            )
        return self._instances[entity_id]

    def get_current_state(self, entity_id: str) -> str:
        """Lấy current state của entity.

        Args:
            entity_id: ID của entity.

        Returns:
            Tên state hiện tại.
        """
        instance = self.get_instance(entity_id)
        return instance.current_state

    def can_transition(self, entity_id: str, to_state: str) -> bool:
        """Kiểm tra có thể transition đến state mục tiêu không.

        Args:
            entity_id: ID của entity.
            to_state: State mục tiêu.

        Returns:
            True nếu có thể transition.
        """
        instance = self.get_instance(entity_id)
        definition = self._find_definition(instance.entity_type)
        if definition is None:
            return False
        return definition.is_valid_transition(instance.current_state, to_state)

    def transition(
        self,
        entity_id: str,
        to_state: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: TransitionAction = TransitionAction.TRANSITION,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TransitionResult:
        """Execute transition cho một entity.

        Cách hoạt động:
        1. Lấy current instance
        2. Validate transition hợp lệ
        3. Cập nhật state
        4. Ghi audit log (CP14)
        5. Publish event (CP05)

        Args:
            entity_id: ID của entity.
            to_state: State mục tiêu.
            user_id: ID người thực hiện (nếu có).
            tenant_id: ID tenant (nếu có).
            action: Loại hành động (transition, force, revert).
            metadata: Metadata bổ sung.

        Returns:
            TransitionResult.

        Raises:
            MidicoderError: Nếu transition không hợp lệ.
        """
        instance = self.get_instance(entity_id)
        definition = self._find_definition(instance.entity_type)

        if definition is None:
            raise EM.raise_error(
                ErrorCode.CP32_REGISTRY_NOT_FOUND,
                entity_type=instance.entity_type,
                reason="Không tìm thấy state machine cho entity type",
            )

        from_state = instance.current_state

        # Kiểm tra đã ở state mục tiêu chưa
        if from_state == to_state:
            raise EM.raise_error(
                ErrorCode.CP32_ALREADY_IN_STATE,
                entity_id=entity_id,
                state=from_state,
                reason=f"Entity đã ở state '{from_state}'",
            )

        # Kiểm tra là final state không
        if definition.is_final_state(from_state):
            raise EM.raise_error(
                ErrorCode.CP32_INVALID_TRANSITION,
                entity_id=entity_id,
                from_state=from_state,
                to_state=to_state,
                reason=f"Không thể transition từ final state '{from_state}'",
            )

        # Validate transition — chỉ enforce nếu action là TRANSITION
        if action == TransitionAction.TRANSITION:
            if not definition.is_valid_transition(from_state, to_state):
                valid = definition.get_valid_transitions(from_state)
                raise EM.raise_error(
                    ErrorCode.CP32_INVALID_TRANSITION,
                    entity_id=entity_id,
                    from_state=from_state,
                    to_state=to_state,
                    valid_targets=valid,
                    reason=f"Transition '{from_state}' → '{to_state}' không hợp lệ. Các target hợp lệ: {valid}",
                )

        # Kiểm tra to_state có tồn tại không
        if to_state not in definition.states:
            raise EM.raise_error(
                ErrorCode.CP32_INVALID_STATE,
                to_state=to_state,
                valid_states=definition.states,
                reason=f"State '{to_state}' không tồn tại",
            )

        # Execute: thêm record vào history
        record = instance.add_transition(
            from_state=from_state,
            to_state=to_state,
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            metadata=metadata or {},
        )

        # Ghi audit log (CP14)
        self._write_audit(
            action="state_transition",
            entity_id=entity_id,
            entity_type=definition.entity_type,
            machine_id=definition.machine_id,
            from_state=from_state,
            to_state=to_state,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )

        # Publish event (CP05)
        self._publish_event(
            event_name="entity.state_changed",
            payload={
                "entity_id": entity_id,
                "entity_type": definition.entity_type,
                "machine_id": definition.machine_id,
                "from_state": from_state,
                "to_state": to_state,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "timestamp": record.timestamp.isoformat(),
            },
        )

        return TransitionResult(
            success=True,
            entity_id=entity_id,
            from_state=from_state,
            to_state=to_state,
            machine_id=definition.machine_id,
            timestamp=record.timestamp,
            record=record,
        )

    def get_history(self, entity_id: str) -> list[TransitionRecord]:
        """Lấy lịch sử transitions của entity.

        Args:
            entity_id: ID của entity.

        Returns:
            Danh sách TransitionRecord.
        """
        instance = self.get_instance(entity_id)
        return instance.history

    def list_registered(self) -> list[str]:
        """Lấy danh sách machine_id đã đăng ký.

        Returns:
            Danh sách machine_id.
        """
        return list(self._definitions.keys())

    def _find_definition(self, entity_type: str) -> Optional[StateMachineDefinition]:
        """Tìm state machine definition theo entity type.

        Args:
            entity_type: Tên entity type.

        Returns:
            StateMachineDefinition hoặc None.
        """
        for defn in self._definitions.values():
            if defn.entity_type == entity_type:
                return defn
        return None

    def _write_audit(self, action: str, **kwargs: Any) -> None:
        """Ghi audit log qua callback (CP14 integration).

        Args:
            action: Tên hành động.
            **kwargs: Metadata bổ sung.
        """
        if self._audit_logger:
            try:
                payload = {"action": action, **kwargs}
                self._audit_logger(action, kwargs.get("entity_id", ""), payload)
            except Exception:
                # Không throw — audit là best-effort
                pass

    def _publish_event(self, event_name: str, payload: dict[str, Any]) -> None:
        """Publish event qua callback (CP05 integration).

        Args:
            event_name: Tên event.
            payload: Dữ liệu event.
        """
        if self._event_publisher:
            try:
                self._event_publisher(event_name, payload)
            except Exception:
                # Không throw — event publish là best-effort
                pass
