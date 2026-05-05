"""
Test suite cho Workflow Parser.

Mô-đun này test WorkflowParser:
- Parse YAML workflow definitions
- Validate required fields
- Handle errors

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from midicoder.emitters.core.workflow.parser import WorkflowParser
from midicoder.emitters.core.workflow.models import (
    WorkflowDefinition,
    Transition,
    Guard,
    Effect,
    GuardType,
    EffectType,
)
from midicoder.errors import MidicoderError, ErrorCode


SAMPLE_WORKFLOW_YAML = """
workflows:
  - name: order_lifecycle
    entity: Order
    description: Vòng đời đơn hàng
    states:
      - draft
      - submitted
      - approved
      - rejected
      - shipped
    initial_state: draft
    transitions:
      - id: submit_order
        from_state: draft
        to_state: submitted
        event: submit_order
        guards:
          - type: permission
            permission: order.submit
          - type: business
            condition: "items.length > 0"
        effects:
          - type: event
            publish: OrderSubmitted
          - type: audit
            action: order.submitted

      - id: approve_order
        from_state: submitted
        to_state: approved
        event: approve_order
        async: true
        guards:
          - type: permission
            permission: order.approve
            roles:
              - manager
              - admin
          - type: compliance
            check: kyc_verified
        effects:
          - type: event
            publish: OrderApproved
          - type: command
            execute: notify_customer_approved
          - type: notification
            channel: email
            template: order_approved
            recipient_field: customer_email
"""


class TestWorkflowParser:
    """Test WorkflowParser class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = WorkflowParser()

    def test_parse_simple_workflow(self):
        """Parse workflow đơn giản không có transitions."""
        yaml_content = """
workflows:
  - name: simple_workflow
    states:
      - state_a
      - state_b
    initial_state: state_a
"""
        workflows = self.parser.parse(yaml_content)

        assert len(workflows) == 1
        assert workflows[0].name == "simple_workflow"
        assert workflows[0].states == ["state_a", "state_b"]
        assert workflows[0].initial_state == "state_a"
        assert workflows[0].transitions == []

    def test_parse_full_workflow(self):
        """Parse workflow đầy đủ với transitions, guards, effects."""
        workflows = self.parser.parse(SAMPLE_WORKFLOW_YAML)

        assert len(workflows) == 1
        workflow = workflows[0]

        assert workflow.name == "order_lifecycle"
        assert workflow.entity == "Order"
        assert workflow.description == "Vòng đời đơn hàng"
        assert len(workflow.states) == 5
        assert workflow.initial_state == "draft"
        assert len(workflow.transitions) == 2

    def test_parse_transition_with_guards(self):
        """Parse transition với guards."""
        workflows = self.parser.parse(SAMPLE_WORKFLOW_YAML)
        workflow = workflows[0]

        submit_transition = workflow.transitions[0]
        assert submit_transition.id == "submit_order"
        assert submit_transition.from_state == "draft"
        assert submit_transition.to_state == "submitted"
        assert len(submit_transition.guards) == 2

        # Check permission guard
        perm_guard = submit_transition.guards[0]
        assert perm_guard.type == GuardType.PERMISSION
        assert perm_guard.permission == "order.submit"

        # Check business guard
        business_guard = submit_transition.guards[1]
        assert business_guard.type == GuardType.BUSINESS
        assert business_guard.condition == "items.length > 0"

    def test_parse_transition_with_effects(self):
        """Parse transition với effects."""
        workflows = self.parser.parse(SAMPLE_WORKFLOW_YAML)
        workflow = workflows[0]

        submit_transition = workflow.transitions[0]
        assert len(submit_transition.effects) == 2

        # Check event effect
        event_effect = submit_transition.effects[0]
        assert event_effect.type == EffectType.EVENT
        assert event_effect.publish == "OrderSubmitted"

        # Check audit effect
        audit_effect = submit_transition.effects[1]
        assert audit_effect.type == EffectType.AUDIT
        assert audit_effect.action == "order.submitted"

    def test_parse_async_transition(self):
        """Parse async transition."""
        workflows = self.parser.parse(SAMPLE_WORKFLOW_YAML)
        workflow = workflows[0]

        approve_transition = workflow.transitions[1]
        assert approve_transition.async_execution is True

    def test_parse_file(self):
        """Parse workflow từ file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_WORKFLOW_YAML)
            temp_path = f.name

        try:
            workflows = self.parser.parse_file(temp_path)
            assert len(workflows) == 1
            assert workflows[0].name == "order_lifecycle"
        finally:
            Path(temp_path).unlink()

    def test_parse_file_not_found(self):
        """Error khi file không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse_file("nonexistent.yaml")

        assert exc_info.value.code == ErrorCode.CP01_WORKFLOW_NOT_FOUND

    def test_parse_invalid_yaml(self):
        """Error khi YAML không hợp lệ."""
        invalid_yaml = """
workflows:
  - name: test
    states: [invalid yaml
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)

        assert exc_info.value.code == ErrorCode.DSL_YAML_PARSE_ERROR

    def test_parse_missing_workflows_key(self):
        """Error khi thiếu workflows key."""
        yaml_content = """
name: test
states: [a, b]
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_YAML_PARSE_ERROR

    def test_parse_missing_workflow_name(self):
        """Error khi workflow thiếu name."""
        yaml_content = """
workflows:
  - states: [a, b]
    initial_state: a
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "name"

    def test_parse_missing_states(self):
        """Error khi workflow thiếu states."""
        yaml_content = """
workflows:
  - name: test
    initial_state: a
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "states"

    def test_parse_missing_initial_state(self):
        """Error khi workflow thiếu initial_state."""
        yaml_content = """
workflows:
  - name: test
    states: [a, b]
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "initial_state"

    def test_parse_transition_missing_from_state(self):
        """Error khi transition thiếu from_state."""
        yaml_content = """
workflows:
  - name: test
    states: [a, b]
    initial_state: a
    transitions:
      - to_state: b
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "from_state"

    def test_parse_guard_missing_type(self):
        """Error khi guard thiếu type."""
        yaml_content = """
workflows:
  - name: test
    states: [a, b]
    initial_state: a
    transitions:
      - from_state: a
        to_state: b
        guards:
          - permission: test
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "type"

    def test_parse_effect_missing_type(self):
        """Error khi effect thiếu type."""
        yaml_content = """
workflows:
  - name: test
    states: [a, b]
    initial_state: a
    transitions:
      - from_state: a
        to_state: b
        effects:
          - publish: TestEvent
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_content)

        assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        assert exc_info.value.context.get("field") == "type"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])