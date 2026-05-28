"""
Unit tests cho StateMachineEngine.
"""

import pytest
from datetime import datetime

from midicoder.packs.cp_full_state_machine.engine import StateMachineEngine
from midicoder.packs.cp_full_state_machine.models import (
    StateMachineDefinition,
    TransitionAction,
)
from midicoder.errors import MidicoderError


class TestStateMachineEngine:
    """Test StateMachineEngine."""

    def setup_method(self):
        """Setup test fixture."""
        self.engine = StateMachineEngine()
        self.audit_calls = []
        self.event_calls = []

        def audit_logger(action, entity_id, metadata):
            self.audit_calls.append({"action": action, "entity_id": entity_id})

        def event_publisher(event_name, payload):
            self.event_calls.append({"event": event_name, "payload": payload})

        self.engine_with_hooks = StateMachineEngine(
            audit_logger=audit_logger,
            event_publisher=event_publisher,
        )

        # State machine cho Order
        self.order_sm = StateMachineDefinition(
            machine_id="order-lifecycle",
            entity_type="Order",
            states=["DRAFT", "SUBMITTED", "APPROVED", "FULFILLED", "CANCELLED"],
            initial_state="DRAFT",
            transitions={
                "DRAFT": ["SUBMITTED", "CANCELLED"],
                "SUBMITTED": ["APPROVED", "CANCELLED"],
                "APPROVED": ["FULFILLED"],
            },
            final_states=["FULFILLED", "CANCELLED"],
        )

    def test_register_and_get_definition(self):
        """Đăng ký và lấy definition."""
        self.engine.register(self.order_sm)
        defn = self.engine.get_definition("order-lifecycle")
        assert defn.machine_id == "order-lifecycle"
        assert defn.entity_type == "Order"

    def test_unregister(self):
        """Hủy đăng ký state machine."""
        self.engine.register(self.order_sm)
        self.engine.unregister("order-lifecycle")
        with pytest.raises(MidicoderError):
            self.engine.get_definition("order-lifecycle")

    def test_unregister_nonexistent_raises_error(self):
        """Hủy đăng ký không tồn tại throw error."""
        with pytest.raises(MidicoderError):
            self.engine.unregister("nonexistent")

    def test_get_definition_not_found_raises_error(self):
        """Lấy definition không tồn tại throw error."""
        with pytest.raises(MidicoderError):
            self.engine.get_definition("nonexistent")

    def test_create_instance(self):
        """Tạo instance mới."""
        self.engine.register(self.order_sm)
        instance = self.engine.create_instance("order-1", "order-lifecycle")
        assert instance.entity_id == "order-1"
        assert instance.current_state == "DRAFT"

    def test_get_instance_not_found_raises_error(self):
        """Lấy instance không tồn tại throw error."""
        with pytest.raises(MidicoderError):
            self.engine.get_instance("nonexistent")

    def test_get_current_state(self):
        """Lấy current state."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")
        state = self.engine.get_current_state("order-1")
        assert state == "DRAFT"

    def test_valid_transition(self):
        """Valid transition thành công."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")

        result = self.engine.transition("order-1", "SUBMITTED", user_id="admin")

        assert result.success is True
        assert result.from_state == "DRAFT"
        assert result.to_state == "SUBMITTED"

    def test_invalid_transition_raises_error(self):
        """Invalid transition throw error."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")

        with pytest.raises(MidicoderError):
            self.engine.transition("order-1", "FULFILLED")

    def test_already_in_state_raises_error(self):
        """Đã ở state mục tiêu throw error."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")

        with pytest.raises(MidicoderError):
            self.engine.transition("order-1", "DRAFT")

    def test_transition_from_final_state_raises_error(self):
        """Transition từ final state throw error."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")
        self.engine.transition("order-1", "SUBMITTED")
        self.engine.transition("order-1", "APPROVED")
        self.engine.transition("order-1", "FULFILLED")

        with pytest.raises(MidicoderError):
            self.engine.transition("order-1", "DRAFT")

    def test_can_transition_true(self):
        """Can transition trả về True."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")
        assert self.engine.can_transition("order-1", "SUBMITTED") is True

    def test_can_transition_false(self):
        """Can transition trả về False."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")
        assert self.engine.can_transition("order-1", "FULFILLED") is False

    def test_get_valid_transitions(self):
        """Lấy valid transitions."""
        self.engine.register(self.order_sm)
        valid = self.engine.get_valid_transitions("order-lifecycle", "DRAFT")
        assert "SUBMITTED" in valid
        assert "CANCELLED" in valid

    def test_get_history(self):
        """Lấy lịch sử transitions."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")
        self.engine.transition("order-1", "SUBMITTED")
        self.engine.transition("order-1", "APPROVED")

        history = self.engine.get_history("order-1")
        assert len(history) == 2
        assert history[0].to_state == "SUBMITTED"
        assert history[1].to_state == "APPROVED"

    def test_list_registered(self):
        """Lấy danh sách registered machines."""
        self.engine.register(self.order_sm)
        assert "order-lifecycle" in self.engine.list_registered()

    def test_audit_log_integration(self):
        """Audit log được gọi khi transition."""
        self.engine_with_hooks.register(self.order_sm)
        self.engine_with_hooks.create_instance("order-1", "order-lifecycle")
        self.engine_with_hooks.transition("order-1", "SUBMITTED")

        assert len(self.audit_calls) >= 1
        assert self.audit_calls[-1]["action"] == "state_transition"

    def test_event_publish_integration(self):
        """Event được publish khi transition."""
        self.engine_with_hooks.register(self.order_sm)
        self.engine_with_hooks.create_instance("order-1", "order-lifecycle")
        self.engine_with_hooks.transition("order-1", "SUBMITTED")

        assert len(self.event_calls) >= 1
        assert self.event_calls[-1]["event"] == "entity.state_changed"

    def test_force_transition(self):
        """Force transition bỏ qua validation."""
        self.engine.register(self.order_sm)
        self.engine.create_instance("order-1", "order-lifecycle")

        result = self.engine.transition(
            "order-1", "FULFILLED",
            action=TransitionAction.FORCE,
        )
        assert result.success is True
        assert result.to_state == "FULFILLED"
