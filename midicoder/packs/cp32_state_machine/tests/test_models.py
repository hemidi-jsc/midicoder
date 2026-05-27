"""
Unit tests cho CP32 models.
"""

import pytest
from datetime import datetime

from midicoder.packs.cp32_state_machine.models import (
    StateMachineDefinition,
    StateInstance,
    TransitionAction,
    TransitionRecord,
    TransitionResult,
)
from midicoder.errors import MidicoderError


class TestStateMachineDefinition:
    """Test StateMachineDefinition."""

    def test_create_valid_definition(self):
        """Tạo definition hợp lệ."""
        sm = StateMachineDefinition(
            machine_id="order-lifecycle",
            entity_type="Order",
            states=["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED"],
            initial_state="DRAFT",
            transitions={
                "DRAFT": ["SUBMITTED"],
                "SUBMITTED": ["APPROVED"],
                "APPROVED": ["FULFILLED"],
            },
            final_states=["FULFILLED"],
        )
        assert sm.machine_id == "order-lifecycle"
        assert sm.entity_type == "Order"
        assert len(sm.states) == 4

    def test_empty_machine_id_raises_error(self):
        """machine_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="",
                entity_type="Order",
                states=["DRAFT"],
                initial_state="DRAFT",
                transitions={},
            )

    def test_empty_entity_type_raises_error(self):
        """entity_type rỗng throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="test",
                entity_type="",
                states=["DRAFT"],
                initial_state="DRAFT",
                transitions={},
            )

    def test_empty_states_raises_error(self):
        """states rỗng throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="test",
                entity_type="Order",
                states=[],
                initial_state="DRAFT",
                transitions={},
            )

    def test_initial_state_not_in_states_raises_error(self):
        """initial_state không trong states throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="test",
                entity_type="Order",
                states=["DRAFT", "SUBMITTED"],
                initial_state="UNKNOWN",
                transitions={},
            )

    def test_invalid_from_state_in_transitions_raises_error(self):
        """from_state không trong states throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="test",
                entity_type="Order",
                states=["DRAFT", "SUBMITTED"],
                initial_state="DRAFT",
                transitions={"UNKNOWN": ["DRAFT"]},
            )

    def test_invalid_to_state_in_transitions_raises_error(self):
        """to_state không trong states throw error."""
        with pytest.raises(MidicoderError):
            StateMachineDefinition(
                machine_id="test",
                entity_type="Order",
                states=["DRAFT", "SUBMITTED"],
                initial_state="DRAFT",
                transitions={"DRAFT": ["UNKNOWN"]},
            )

    def test_is_valid_transition(self):
        """Kiểm tra transition hợp lệ."""
        sm = StateMachineDefinition(
            machine_id="test",
            entity_type="Order",
            states=["DRAFT", "SUBMITTED", "APPROVED"],
            initial_state="DRAFT",
            transitions={"DRAFT": ["SUBMITTED"], "SUBMITTED": ["APPROVED"]},
        )
        assert sm.is_valid_transition("DRAFT", "SUBMITTED") is True
        assert sm.is_valid_transition("DRAFT", "APPROVED") is False
        assert sm.is_valid_transition("UNKNOWN", "DRAFT") is False

    def test_get_valid_transitions(self):
        """Lấy valid transitions từ state."""
        sm = StateMachineDefinition(
            machine_id="test",
            entity_type="Order",
            states=["DRAFT", "SUBMITTED", "CANCELLED"],
            initial_state="DRAFT",
            transitions={"DRAFT": ["SUBMITTED", "CANCELLED"]},
        )
        assert sm.get_valid_transitions("DRAFT") == ["SUBMITTED", "CANCELLED"]
        assert sm.get_valid_transitions("UNKNOWN") == []

    def test_is_final_state(self):
        """Kiểm tra final state."""
        sm = StateMachineDefinition(
            machine_id="test",
            entity_type="Order",
            states=["DRAFT", "FULFILLED"],
            initial_state="DRAFT",
            transitions={"DRAFT": ["FULFILLED"]},
            final_states=["FULFILLED"],
        )
        assert sm.is_final_state("FULFILLED") is True
        assert sm.is_final_state("DRAFT") is False

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        sm = StateMachineDefinition(
            machine_id="test",
            entity_type="Order",
            states=["DRAFT", "APPROVED"],
            initial_state="DRAFT",
            transitions={"DRAFT": ["APPROVED"]},
            final_states=["APPROVED"],
            metadata={"version": "1.0"},
        )
        data = sm.to_dict()
        restored = StateMachineDefinition.from_dict(data)
        assert restored.machine_id == sm.machine_id
        assert restored.states == sm.states
        assert restored.transitions == sm.transitions
        assert restored.metadata == sm.metadata


class TestTransitionRecord:
    """Test TransitionRecord."""

    def test_create_record(self):
        """Tạo transition record."""
        now = datetime.utcnow()
        record = TransitionRecord(
            entity_id="order-1",
            from_state="DRAFT",
            to_state="SUBMITTED",
            timestamp=now,
            user_id="admin",
        )
        assert record.entity_id == "order-1"
        assert record.from_state == "DRAFT"
        assert record.action == TransitionAction.TRANSITION

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        now = datetime.utcnow()
        record = TransitionRecord(
            entity_id="order-1",
            from_state="DRAFT",
            to_state="SUBMITTED",
            timestamp=now,
            action=TransitionAction.TRANSITION,
            user_id="admin",
            tenant_id="t1",
            metadata={"note": "test"},
        )
        data = record.to_dict()
        restored = TransitionRecord.from_dict(data)
        assert restored.entity_id == record.entity_id
        assert restored.from_state == record.from_state
        assert restored.to_state == record.to_state
        assert restored.user_id == record.user_id


class TestStateInstance:
    """Test StateInstance."""

    def test_create_instance(self):
        """Tạo state instance."""
        instance = StateInstance(
            entity_id="order-1",
            entity_type="Order",
            current_state="DRAFT",
        )
        assert instance.current_state == "DRAFT"
        assert len(instance.history) == 0
        assert instance.created_at is not None

    def test_empty_entity_id_raises_error(self):
        """entity_id rỗng throw error."""
        with pytest.raises(MidicoderError):
            StateInstance(
                entity_id="",
                entity_type="Order",
                current_state="DRAFT",
            )

    def test_add_transition(self):
        """Thêm transition vào history."""
        instance = StateInstance(
            entity_id="order-1",
            entity_type="Order",
            current_state="DRAFT",
        )
        record = instance.add_transition(
            from_state="DRAFT",
            to_state="SUBMITTED",
            user_id="admin",
        )
        assert instance.current_state == "SUBMITTED"
        assert len(instance.history) == 1
        assert instance.history[0].to_state == "SUBMITTED"

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip."""
        instance = StateInstance(
            entity_id="order-1",
            entity_type="Order",
            current_state="DRAFT",
        )
        instance.add_transition("DRAFT", "SUBMITTED", user_id="admin")

        data = instance.to_dict()
        restored = StateInstance.from_dict(data)
        assert restored.entity_id == instance.entity_id
        assert restored.current_state == instance.current_state
        assert len(restored.history) == 1


class TestTransitionResult:
    """Test TransitionResult."""

    def test_success_result(self):
        """Tạo kết quả thành công."""
        result = TransitionResult(
            success=True,
            entity_id="order-1",
            from_state="DRAFT",
            to_state="SUBMITTED",
            machine_id="order-lifecycle",
            timestamp=datetime.utcnow(),
        )
        assert result.success is True
        assert result.to_state == "SUBMITTED"

    def test_failure_result(self):
        """Tạo kết quả thất bại."""
        result = TransitionResult(
            success=False,
            entity_id="order-1",
            from_state="DRAFT",
            machine_id="order-lifecycle",
            timestamp=datetime.utcnow(),
            error="Invalid transition",
        )
        assert result.success is False
        assert result.to_state is None
        assert result.error == "Invalid transition"

    def test_to_dict(self):
        """Serialization to dict."""
        result = TransitionResult(
            success=True,
            entity_id="order-1",
            from_state="DRAFT",
            to_state="SUBMITTED",
            machine_id="order-lifecycle",
            timestamp=datetime.utcnow(),
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["to_state"] == "SUBMITTED"
        assert data["entity_id"] == "order-1"
