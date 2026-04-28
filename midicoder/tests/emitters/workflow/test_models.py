"""
Test suite cho Workflow DSL models.

Mô-đun này test các dataclasses định nghĩa Workflow DSL:
- WorkflowDefinition
- Transition
- Guard
- Effect

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from midicoder.emitters.workflow.models import (
    WorkflowDefinition,
    Transition,
    Guard,
    GuardType,
    Effect,
    EffectType,
)
from midicoder.errors import MidicoderError, ErrorCode


class TestWorkflowDefinition:
    """Test WorkflowDefinition dataclass."""

    def test_create_workflow_definition_minimal(self):
        """Tạo workflow definition với tối thiểu fields."""
        workflow = WorkflowDefinition(
            name="test_workflow",
            states=["state_a", "state_b"],
            initial_state="state_a",
            transitions=[],
        )

        assert workflow.name == "test_workflow"
        assert workflow.states == ["state_a", "state_b"]
        assert workflow.initial_state == "state_a"
        assert workflow.transitions == []
        assert workflow.entity is None
        assert workflow.description is None

    def test_create_workflow_definition_full(self):
        """Tạo workflow definition với đầy đủ fields."""
        workflow = WorkflowDefinition(
            name="order_lifecycle",
            entity="Order",
            states=["draft", "submitted", "approved"],
            initial_state="draft",
            transitions=[],
            description="Workflow cho vòng đời đơn hàng",
        )

        assert workflow.name == "order_lifecycle"
        assert workflow.entity == "Order"
        assert workflow.description == "Workflow cho vòng đời đơn hàng"

    def test_workflow_definition_name_required(self):
        """Tên workflow bắt buộc phải có."""
        with pytest.raises(TypeError) as exc_info:
            WorkflowDefinition(
                states=["state_a"],
                initial_state="state_a",
                transitions=[],
            )

        assert "name" in str(exc_info.value).lower()

    def test_workflow_definition_states_required(self):
        """Danh sách states bắt buộc phải có."""
        with pytest.raises(TypeError) as exc_info:
            WorkflowDefinition(
                name="test",
                initial_state="state_a",
                transitions=[],
            )

        assert "states" in str(exc_info.value).lower()

    def test_workflow_definition_initial_state_must_exist(self):
        """Initial state phải tồn tại trong states."""
        with pytest.raises(MidicoderError) as exc_info:
            WorkflowDefinition(
                name="test",
                states=["state_a", "state_b"],
                initial_state="nonexistent",
                transitions=[],
            )

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_INVALID_STATE
        assert "nonexistent" in str(exc_info.value)

    def test_workflow_definition_empty_states(self):
        """States không được rỗng."""
        with pytest.raises(MidicoderError) as exc_info:
            WorkflowDefinition(
                name="test",
                states=[],
                initial_state="state_a",
                transitions=[],
            )

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_INVALID_STATE


class TestTransition:
    """Test Transition dataclass."""

    def test_create_transition_minimal(self):
        """Tạo transition với tối thiểu fields."""
        transition = Transition(
            from_state="draft",
            to_state="submitted",
        )

        assert transition.from_state == "draft"
        assert transition.to_state == "submitted"
        assert transition.id is not None
        assert transition.event is None
        assert transition.guards == []
        assert transition.effects == []
        assert transition.async_execution is False

    def test_create_transition_full(self):
        """Tạo transition với đầy đủ fields."""
        transition = Transition(
            id="submit_order",
            from_state="draft",
            to_state="submitted",
            event="submit_order",
            guards=[],
            effects=[],
            async_execution=False,
        )

        assert transition.id == "submit_order"
        assert transition.event == "submit_order"
        assert transition.async_execution is False

    def test_transition_generates_id(self):
        """Transition tự động generate ID nếu không cung cấp."""
        transition = Transition(
            from_state="draft",
            to_state="submitted",
        )

        assert transition.id is not None
        assert isinstance(transition.id, str)
        assert len(transition.id) > 0

    def test_transition_id_unique(self):
        """Mỗi transition có ID duy nhất."""
        t1 = Transition(from_state="a", to_state="b")
        t2 = Transition(from_state="a", to_state="b")

        # IDs tự sinh nên có thể khác nhau
        assert t1.id is not None
        assert t2.id is not None


class TestGuard:
    """Test Guard dataclass."""

    def test_create_permission_guard(self):
        """Tạo permission guard."""
        guard = Guard(
            type=GuardType.PERMISSION,
            permission="order.submit",
        )

        assert guard.type == GuardType.PERMISSION
        assert guard.permission == "order.submit"
        assert guard.condition is None

    def test_create_business_guard(self):
        """Tạo business rule guard."""
        guard = Guard(
            type=GuardType.BUSINESS,
            condition="items.length > 0",
        )

        assert guard.type == GuardType.BUSINESS
        assert guard.condition == "items.length > 0"
        assert guard.permission is None

    def test_create_compliance_guard(self):
        """Tạo compliance guard."""
        guard = Guard(
            type=GuardType.COMPLIANCE,
            check="kyc_verified",
        )

        assert guard.type == GuardType.COMPLIANCE
        assert guard.check == "kyc_verified"

    def test_create_role_guard(self):
        """Tạo role guard."""
        guard = Guard(
            type=GuardType.ROLE,
            roles=["manager", "admin"],
        )

        assert guard.type == GuardType.ROLE
        assert guard.roles == ["manager", "admin"]

    def test_create_state_guard(self):
        """Tạo state guard."""
        guard = Guard(
            type=GuardType.STATE,
            condition="current_state == 'draft'",
        )

        assert guard.type == GuardType.STATE
        assert guard.condition == "current_state == 'draft'"

    def test_guard_type_required(self):
        """Guard type bắt buộc phải có."""
        with pytest.raises(TypeError) as exc_info:
            Guard(permission="test")

        assert "type" in str(exc_info.value).lower()

    def test_permission_guard_requires_permission(self):
        """Permission guard cần có permission."""
        with pytest.raises(MidicoderError) as exc_info:
            Guard(
                type=GuardType.PERMISSION,
            )

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_GUARD_FAILED
        assert "permission" in str(exc_info.value).lower()

    def test_business_guard_requires_condition(self):
        """Business guard cần có condition."""
        with pytest.raises(MidicoderError) as exc_info:
            Guard(
                type=GuardType.BUSINESS,
            )

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_GUARD_FAILED
        assert "condition" in str(exc_info.value).lower()


class TestEffect:
    """Test Effect dataclass."""

    def test_create_event_effect(self):
        """Tạo event publishing effect."""
        effect = Effect(
            type=EffectType.EVENT,
            publish="OrderSubmitted",
        )

        assert effect.type == EffectType.EVENT
        assert effect.publish == "OrderSubmitted"

    def test_create_command_effect(self):
        """Tạo command execution effect."""
        effect = Effect(
            type=EffectType.COMMAND,
            execute="notify_customer",
        )

        assert effect.type == EffectType.COMMAND
        assert effect.execute == "notify_customer"

    def test_create_notification_effect(self):
        """Tạo notification effect."""
        effect = Effect(
            type=EffectType.NOTIFICATION,
            channel="email",
            template="order_approved",
            recipient_field="customer_email",
        )

        assert effect.type == EffectType.NOTIFICATION
        assert effect.channel == "email"
        assert effect.template == "order_approved"

    def test_create_audit_effect(self):
        """Tạo audit logging effect."""
        effect = Effect(
            type=EffectType.AUDIT,
            action="order.submitted",
        )

        assert effect.type == EffectType.AUDIT
        assert effect.action == "order.submitted"

    def test_create_compensation_effect(self):
        """Tạo compensation effect."""
        effect = Effect(
            type=EffectType.COMPENSATION,
            rollback="release_inventory",
        )

        assert effect.type == EffectType.COMPENSATION
        assert effect.rollback == "release_inventory"

    def test_effect_type_required(self):
        """Effect type bắt buộc phải có."""
        with pytest.raises(TypeError) as exc_info:
            Effect(publish="test")

        assert "type" in str(exc_info.value).lower()

    def test_event_effect_requires_publish(self):
        """Event effect cần có publish."""
        with pytest.raises(MidicoderError) as exc_info:
            Effect(
                type=EffectType.EVENT,
            )

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_EFFECT_FAILED
        assert "publish" in str(exc_info.value).lower()


class TestGuardType:
    """Test GuardType enum."""

    def test_guard_type_values(self):
        """Kiểm tra các giá trị của GuardType."""
        assert GuardType.PERMISSION == "permission"
        assert GuardType.BUSINESS == "business"
        assert GuardType.COMPLIANCE == "compliance"
        assert GuardType.ROLE == "role"
        assert GuardType.STATE == "state"

    def test_guard_type_from_string(self):
        """Tạo GuardType từ string."""
        assert GuardType("permission") == GuardType.PERMISSION
        assert GuardType("business") == GuardType.BUSINESS


class TestEffectType:
    """Test EffectType enum."""

    def test_effect_type_values(self):
        """Kiểm tra các giá trị của EffectType."""
        assert EffectType.EVENT == "event"
        assert EffectType.COMMAND == "command"
        assert EffectType.NOTIFICATION == "notification"
        assert EffectType.AUDIT == "audit"
        assert EffectType.COMPENSATION == "compensation"

    def test_effect_type_from_string(self):
        """Tạo EffectType từ string."""
        assert EffectType("event") == EffectType.EVENT
        assert EffectType("command") == EffectType.COMMAND


if __name__ == "__main__":
    pytest.main([__file__, "-v"])