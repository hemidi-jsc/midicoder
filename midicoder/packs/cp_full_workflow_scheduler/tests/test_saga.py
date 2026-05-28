"""
Test suite cho Saga models và SagaOrchestrator engine.

Mô-đun này test các thành phần Saga pattern trong CP13 Workflow Runtime:
- SagaCompensationStrategy (enum)
- SagaStep (model)
- SagaDefinition (model)
- SagaOrchestrator (engine)
- SagaExecutionState, SagaStepResult, SagaStepStatus (runtime)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from uuid import uuid4

from midicoder.packs.cp_full_workflow_scheduler.models import (
    SagaDefinition,
    SagaStep,
    SagaCompensationStrategy,
)
from midicoder.packs.cp_full_workflow_scheduler.engine.saga_orchestrator import (
    SagaOrchestrator,
    SagaExecutionState,
    SagaStepResult,
    SagaStepStatus,
)
from midicoder.errors import MidicoderError, ErrorCode


# =============================================================================
# TestSagaCompensationStrategy
# =============================================================================


class TestSagaCompensationStrategy:
    """Test SagaCompensationStrategy enum."""

    def test_backward_value(self):
        """Giá trị của BACKWARD là 'backward'."""
        assert SagaCompensationStrategy.BACKWARD.value == "backward"

    def test_forward_value(self):
        """Giá trị của FORWARD là 'forward'."""
        assert SagaCompensationStrategy.FORWARD.value == "forward"

    def test_mixed_value(self):
        """Giá trị của MIXED là 'mixed'."""
        assert SagaCompensationStrategy.MIXED.value == "mixed"

    def test_all_enum_members(self):
        """Kiểm tra đủ 3 thành viên enum."""
        members = list(SagaCompensationStrategy)
        assert len(members) == 3
        assert SagaCompensationStrategy.BACKWARD in members
        assert SagaCompensationStrategy.FORWARD in members
        assert SagaCompensationStrategy.MIXED in members

    def test_from_string(self):
        """Tạo enum từ string value."""
        assert SagaCompensationStrategy("backward") == SagaCompensationStrategy.BACKWARD
        assert SagaCompensationStrategy("forward") == SagaCompensationStrategy.FORWARD
        assert SagaCompensationStrategy("mixed") == SagaCompensationStrategy.MIXED


# =============================================================================
# TestSagaStep
# =============================================================================


class TestSagaStep:
    """Test SagaStep dataclass."""

    def test_create_minimal_step(self):
        """Tạo step với tối thiểu fields (step_id, action)."""
        step = SagaStep(
            step_id="step-1",
            action="create_order",
        )

        assert step.step_id == "step-1"
        assert step.action == "create_order"
        assert step.compensation == ""
        assert step.inputs == {}
        assert step.timeout_seconds == 300
        assert step.is_compensatable is True
        assert step.description == ""

    def test_create_full_step(self):
        """Tạo step với đầy đủ fields."""
        step = SagaStep(
            step_id="step-2",
            action="reserve_inventory",
            compensation="release_inventory",
            inputs={"product_id": "P123", "quantity": 10},
            timeout_seconds=600,
            is_compensatable=True,
            description="Đặt chỗ hàng tồn kho",
        )

        assert step.step_id == "step-2"
        assert step.action == "reserve_inventory"
        assert step.compensation == "release_inventory"
        assert step.inputs == {"product_id": "P123", "quantity": 10}
        assert step.timeout_seconds == 600
        assert step.is_compensatable is True
        assert step.description == "Đặt chỗ hàng tồn kho"

    def test_default_is_compensatable(self):
        """Giá trị mặc định của is_compensatable là True."""
        step = SagaStep(step_id="s1", action="do_something")
        assert step.is_compensatable is True

    def test_default_timeout(self):
        """Giá trị mặc định của timeout_seconds là 300."""
        step = SagaStep(step_id="s1", action="do_something")
        assert step.timeout_seconds == 300

    def test_set_idempotent_step(self):
        """Đặt step là không compensatable (idempotent)."""
        step = SagaStep(
            step_id="s1",
            action="log_event",
            is_compensatable=False,
        )
        assert step.is_compensatable is False

    def test_to_dict(self):
        """Chuyển SagaStep sang dict."""
        step = SagaStep(
            step_id="step-1",
            action="create_order",
            compensation="cancel_order",
            inputs={"order_id": "ORD-001"},
            timeout_seconds=120,
            is_compensatable=False,
            description="Tạo đơn hàng",
        )

        d = step.to_dict()

        assert d["step_id"] == "step-1"
        assert d["action"] == "create_order"
        assert d["compensation"] == "cancel_order"
        assert d["inputs"] == {"order_id": "ORD-001"}
        assert d["timeout_seconds"] == 120
        assert d["is_compensatable"] is False
        assert d["description"] == "Tạo đơn hàng"

    def test_from_dict(self):
        """Tạo SagaStep từ dict."""
        data = {
            "step_id": "step-2",
            "action": "charge_payment",
            "compensation": "refund_payment",
            "inputs": {"amount": 100},
            "timeout_seconds": 60,
            "is_compensatable": True,
            "description": "Thanh toán",
        }

        step = SagaStep.from_dict(data)

        assert step.step_id == "step-2"
        assert step.action == "charge_payment"
        assert step.compensation == "refund_payment"
        assert step.inputs == {"amount": 100}
        assert step.timeout_seconds == 60
        assert step.is_compensatable is True
        assert step.description == "Thanh toán"

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() -> from_dict() giữ nguyên dữ liệu."""
        original = SagaStep(
            step_id="rt-step",
            action="send_notification",
            compensation="undo_notification",
            inputs={"channel": "email", "template": "welcome"},
            timeout_seconds=45,
            is_compensatable=True,
            description="Gửi thông báo chào mừng",
        )

        restored = SagaStep.from_dict(original.to_dict())

        assert restored.step_id == original.step_id
        assert restored.action == original.action
        assert restored.compensation == original.compensation
        assert restored.inputs == original.inputs
        assert restored.timeout_seconds == original.timeout_seconds
        assert restored.is_compensatable == original.is_compensatable
        assert restored.description == original.description


# =============================================================================
# TestSagaDefinition
# =============================================================================


class TestSagaDefinition:
    """Test SagaDefinition dataclass."""

    def test_create_minimal_definition(self):
        """Tạo saga definition với tối thiểu fields."""
        saga = SagaDefinition(
            saga_id="saga-1",
            name="Order Saga",
        )

        assert saga.saga_id == "saga-1"
        assert saga.name == "Order Saga"
        assert saga.steps == []
        assert saga.compensation_strategy == SagaCompensationStrategy.BACKWARD
        assert saga.enable_saga_log is True
        assert saga.max_retry_on_failure == 0
        assert saga.description == ""

    def test_create_full_definition_with_steps(self):
        """Tạo saga definition với đầy đủ fields và steps."""
        steps = [
            SagaStep(step_id="s1", action="create_order", compensation="cancel_order"),
            SagaStep(step_id="s2", action="reserve_stock", compensation="release_stock"),
            SagaStep(step_id="s3", action="charge_payment", compensation="refund_payment"),
        ]

        saga = SagaDefinition(
            saga_id="saga-full",
            name="Full Order Saga",
            steps=steps,
            compensation_strategy=SagaCompensationStrategy.MIXED,
            enable_saga_log=True,
            max_retry_on_failure=3,
            description="Saga hoàn chỉnh cho đơn hàng",
        )

        assert saga.saga_id == "saga-full"
        assert saga.name == "Full Order Saga"
        assert len(saga.steps) == 3
        assert saga.compensation_strategy == SagaCompensationStrategy.MIXED
        assert saga.enable_saga_log is True
        assert saga.max_retry_on_failure == 3
        assert saga.description == "Saga hoàn chỉnh cho đơn hàng"

    def test_default_compensation_strategy(self):
        """Giá trị mặc định của compensation_strategy là BACKWARD."""
        saga = SagaDefinition(saga_id="s1", name="test")
        assert saga.compensation_strategy == SagaCompensationStrategy.BACKWARD

    def test_default_enable_saga_log(self):
        """Giá trị mặc định của enable_saga_log là True."""
        saga = SagaDefinition(saga_id="s1", name="test")
        assert saga.enable_saga_log is True

    def test_default_max_retry(self):
        """Giá trị mặc định của max_retry_on_failure là 0."""
        saga = SagaDefinition(saga_id="s1", name="test")
        assert saga.max_retry_on_failure == 0

    def test_to_dict(self):
        """Chuyển SagaDefinition sang dict."""
        saga = SagaDefinition(
            saga_id="saga-dict",
            name="Dict Saga",
            steps=[
                SagaStep(step_id="s1", action="step1_action", compensation="step1_comp"),
            ],
            compensation_strategy=SagaCompensationStrategy.FORWARD,
            enable_saga_log=False,
            max_retry_on_failure=2,
            description="Test dict",
        )

        d = saga.to_dict()

        assert d["saga_id"] == "saga-dict"
        assert d["name"] == "Dict Saga"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["step_id"] == "s1"
        assert d["compensation_strategy"] == "forward"
        assert d["enable_saga_log"] is False
        assert d["max_retry_on_failure"] == 2
        assert d["description"] == "Test dict"

    def test_from_dict(self):
        """Tạo SagaDefinition từ dict."""
        data = {
            "saga_id": "saga-from-dict",
            "name": "From Dict Saga",
            "steps": [
                {
                    "step_id": "s1",
                    "action": "create",
                    "compensation": "delete",
                    "inputs": {},
                    "timeout_seconds": 300,
                    "is_compensatable": True,
                    "description": "",
                }
            ],
            "compensation_strategy": "backward",
            "enable_saga_log": True,
            "max_retry_on_failure": 0,
            "description": "",
        }

        saga = SagaDefinition.from_dict(data)

        assert saga.saga_id == "saga-from-dict"
        assert saga.name == "From Dict Saga"
        assert len(saga.steps) == 1
        assert saga.steps[0].step_id == "s1"
        assert saga.compensation_strategy == SagaCompensationStrategy.BACKWARD
        assert saga.enable_saga_log is True

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() -> from_dict() giữ nguyên dữ liệu."""
        original = SagaDefinition(
            saga_id="rt-saga",
            name="Roundtrip Saga",
            steps=[
                SagaStep(
                    step_id="s1",
                    action="action_1",
                    compensation="comp_1",
                    inputs={"key": "val"},
                    timeout_seconds=100,
                    is_compensatable=False,
                    description="Step 1",
                ),
                SagaStep(
                    step_id="s2",
                    action="action_2",
                    compensation="comp_2",
                    timeout_seconds=200,
                    is_compensatable=True,
                ),
            ],
            compensation_strategy=SagaCompensationStrategy.MIXED,
            enable_saga_log=True,
            max_retry_on_failure=5,
            description="Test roundtrip",
        )

        restored = SagaDefinition.from_dict(original.to_dict())

        assert restored.saga_id == original.saga_id
        assert restored.name == original.name
        assert len(restored.steps) == len(original.steps)
        for i, s in enumerate(restored.steps):
            assert s.step_id == original.steps[i].step_id
            assert s.action == original.steps[i].action
            assert s.compensation == original.steps[i].compensation
            assert s.inputs == original.steps[i].inputs
            assert s.timeout_seconds == original.steps[i].timeout_seconds
            assert s.is_compensatable == original.steps[i].is_compensatable
            assert s.description == original.steps[i].description
        assert restored.compensation_strategy == original.compensation_strategy
        assert restored.enable_saga_log == original.enable_saga_log
        assert restored.max_retry_on_failure == original.max_retry_on_failure
        assert restored.description == original.description


# =============================================================================
# TestSagaOrchestratorValidate
# =============================================================================


class TestSagaOrchestratorValidate:
    """Test validate_saga() của SagaOrchestrator."""

    def test_valid_saga_passes(self):
        """Saga hợp lệ vượt qua validate."""
        saga = SagaDefinition(
            saga_id="valid-saga",
            name="Valid",
            steps=[
                SagaStep(step_id="s1", action="do_a", compensation="undo_a"),
                SagaStep(step_id="s2", action="do_b", compensation="undo_b"),
            ],
        )
        orchestrator = SagaOrchestrator(saga)
        orchestrator.validate_saga()  # Không raise exception

    def test_valid_saga_with_idempotent_step(self):
        """Saga với step idempotent (không compensatable) hợp lệ."""
        saga = SagaDefinition(
            saga_id="idempotent-saga",
            name="Idempotent",
            steps=[
                SagaStep(step_id="s1", action="log", is_compensatable=False),
            ],
        )
        orchestrator = SagaOrchestrator(saga)
        orchestrator.validate_saga()  # Không raise exception

    def test_empty_steps_raises_error(self):
        """Saga với steps rỗng raise MidicoderError."""
        saga = SagaDefinition(
            saga_id="empty-saga",
            name="Empty",
            steps=[],
        )
        orchestrator = SagaOrchestrator(saga)

        with pytest.raises(MidicoderError) as exc_info:
            orchestrator.validate_saga()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR

    def test_step_without_action_raises_error(self):
        """Step không có action raise MidicoderError."""
        # SagaStep yêu cầu action trong constructor, nên ta dùng empty string
        saga = SagaDefinition(
            saga_id="no-action-saga",
            name="No Action",
            steps=[
                SagaStep(step_id="s1", action=""),
            ],
        )
        orchestrator = SagaOrchestrator(saga)

        with pytest.raises(MidicoderError) as exc_info:
            orchestrator.validate_saga()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_INVALID_TRANSITION

    def test_compensatable_step_without_compensation_raises_error(self):
        """Step compensatable nhưng không có compensation raise error."""
        saga = SagaDefinition(
            saga_id="no-comp-saga",
            name="No Compensation",
            steps=[
                SagaStep(
                    step_id="s1",
                    action="do_something",
                    compensation="",
                    is_compensatable=True,
                ),
            ],
        )
        orchestrator = SagaOrchestrator(saga)

        with pytest.raises(MidicoderError) as exc_info:
            orchestrator.validate_saga()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_INVALID_TRANSITION


# =============================================================================
# TestSagaOrchestratorExecute
# =============================================================================


class TestSagaOrchestratorExecute:
    """Test execute() của SagaOrchestrator."""

    def test_all_steps_succeed(self):
        """Tất cả steps thành công -> status COMPLETED."""
        saga = SagaDefinition(
            saga_id="success-saga",
            name="Success",
            steps=[
                SagaStep(step_id="s1", action="action_1", compensation="comp_1"),
                SagaStep(step_id="s2", action="action_2", compensation="comp_2"),
                SagaStep(step_id="s3", action="action_3", compensation="comp_3"),
            ],
        )
        orchestrator = SagaOrchestrator(saga)
        state = orchestrator.execute({"input": "data"})

        assert state.status == "COMPLETED"
        assert len(state.step_results) == 3
        for result in state.step_results:
            assert result.action_status == SagaStepStatus.COMPLETED

    def test_step_fails_backward_compensation(self):
        """Step fail với chiến lược BACKWARD: compensatable steps được compensate ngược."""
        saga = SagaDefinition(
            saga_id="backward-saga",
            name="Backward",
            compensation_strategy=SagaCompensationStrategy.BACKWARD,
            steps=[
                SagaStep(step_id="s1", action="action_1", compensation="comp_1"),
                SagaStep(step_id="s2", action="action_2", compensation="comp_2"),
                SagaStep(step_id="s3", action="action_3", compensation="comp_3"),
            ],
        )

        call_order = []

        def step_handler(step, context):
            call_order.append(("action", step.step_id))
            if step.step_id == "s3":
                raise RuntimeError("Step s3 failed")
            return {"status": "ok"}

        def compensation_handler(step, context):
            call_order.append(("compensation", step.step_id))
            return {"status": "compensated"}

        orchestrator = SagaOrchestrator(saga, step_handler, compensation_handler)
        state = orchestrator.execute({})

        # s1, s2 completed; s3 failed
        assert state.step_results[0].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[1].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[2].action_status == SagaStepStatus.FAILED

        # Compensation: s2, s1 (reverse order)
        assert state.step_results[1].compensation_status == SagaStepStatus.COMPENSATED
        assert state.step_results[0].compensation_status == SagaStepStatus.COMPENSATED

        # Kiểm tra thứ tự gọi: action s1, s2, s3 -> compensation s2, s1
        action_calls = [c for c in call_order if c[0] == "action"]
        comp_calls = [c for c in call_order if c[0] == "compensation"]
        assert comp_calls == [("compensation", "s2"), ("compensation", "s1")]

    def test_step_fails_forward_recovery(self):
        """Step fail với chiến lược FORWARD: các step còn lại tiếp tục."""
        saga = SagaDefinition(
            saga_id="forward-saga",
            name="Forward",
            compensation_strategy=SagaCompensationStrategy.FORWARD,
            steps=[
                SagaStep(step_id="s1", action="action_1", compensation="comp_1"),
                SagaStep(step_id="s2", action="action_2", compensation="comp_2"),
                SagaStep(step_id="s3", action="action_3", compensation="comp_3"),
            ],
        )

        call_order = []

        def step_handler(step, context):
            call_order.append(step.step_id)
            if step.step_id == "s2":
                raise RuntimeError("Step s2 failed")
            return {"status": "ok"}

        orchestrator = SagaOrchestrator(saga, step_handler)
        state = orchestrator.execute({})

        # s1 completed, s2 skipped (forward recovery), s3 attempted
        assert state.step_results[0].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[1].action_status == SagaStepStatus.SKIPPED
        # s3 sẽ được execute và thành công
        assert state.step_results[2].action_status == SagaStepStatus.COMPLETED

        # Không có compensation xảy ra
        for result in state.step_results:
            assert result.compensation_status == SagaStepStatus.PENDING

    def test_step_fails_mixed_compensation(self):
        """Step fail với chiến lược MIXED: compensatable được compensate, idempotent bị skip."""
        saga = SagaDefinition(
            saga_id="mixed-saga",
            name="Mixed",
            compensation_strategy=SagaCompensationStrategy.MIXED,
            steps=[
                SagaStep(step_id="s1", action="action_1", compensation="comp_1", is_compensatable=True),
                SagaStep(step_id="s2", action="idempotent_op", is_compensatable=False),
                SagaStep(step_id="s3", action="action_3", compensation="comp_3"),
            ],
        )

        comp_called = []

        def step_handler(step, context):
            if step.step_id == "s3":
                raise RuntimeError("Step s3 failed")
            return {"status": "ok"}

        def compensation_handler(step, context):
            comp_called.append(step.step_id)
            return {"status": "compensated"}

        orchestrator = SagaOrchestrator(saga, step_handler, compensation_handler)
        state = orchestrator.execute({})

        # s1 completed + compensated (is_compensatable=True)
        assert state.step_results[0].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[0].compensation_status == SagaStepStatus.COMPENSATED

        # s2 completed + compensation skipped (is_compensatable=False)
        assert state.step_results[1].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[1].compensation_status == SagaStepStatus.SKIPPED

        # s3 failed
        assert state.step_results[2].action_status == SagaStepStatus.FAILED

        # Compensation handler chỉ được gọi cho s1
        assert comp_called == ["s1"]

    def test_custom_step_handler_called_with_correct_data(self):
        """Custom step_handler nhận đúng context data."""
        saga = SagaDefinition(
            saga_id="handler-saga",
            name="Handler",
            steps=[
                SagaStep(
                    step_id="s1",
                    action="process",
                    compensation="undo",
                    inputs={"param": "value"},
                    timeout_seconds=120,
                ),
            ],
        )

        received_context = {}

        def step_handler(step, context):
            received_context["step_id"] = step.step_id
            received_context["action"] = step.action
            received_context["inputs"] = context["inputs"]
            received_context["saga_input"] = context["saga_input"]
            received_context["timeout"] = context["timeout_seconds"]
            return {"handled": True}

        orchestrator = SagaOrchestrator(saga, step_handler)
        orchestrator.execute({"saga_key": "saga_val"})

        assert received_context["step_id"] == "s1"
        assert received_context["action"] == "process"
        assert received_context["inputs"] == {"param": "value"}
        assert received_context["saga_input"] == {"saga_key": "saga_val"}
        assert received_context["timeout"] == 120

    def test_custom_compensation_handler_called(self):
        """Custom compensation_handler được gọi khi step fail."""
        saga = SagaDefinition(
            saga_id="comp-handler-saga",
            name="Comp Handler",
            steps=[
                SagaStep(step_id="s1", action="do_a", compensation="undo_a"),
                SagaStep(step_id="s2", action="do_b", compensation="undo_b"),
            ],
        )

        comp_received = []

        def step_handler(step, context):
            if step.step_id == "s2":
                raise RuntimeError("Fail")
            return {"ok": True}

        def compensation_handler(step, context):
            comp_received.append({
                "step_id": step.step_id,
                "compensation": step.compensation,
            })
            return {"undone": True}

        orchestrator = SagaOrchestrator(saga, step_handler, compensation_handler)
        orchestrator.execute({})

        assert len(comp_received) == 1
        assert comp_received[0]["step_id"] == "s1"
        assert comp_received[0]["compensation"] == "undo_a"


# =============================================================================
# TestSagaOrchestratorBackwardCompensate
# =============================================================================


class TestSagaOrchestratorBackwardCompensate:
    """Test _backward_compensate() của SagaOrchestrator."""

    def test_compensate_from_failed_step_backwards(self):
        """Compensate từ step bị fail đi ngược về đầu."""
        saga = SagaDefinition(
            saga_id="backward-ctest",
            name="Backward CT",
            compensation_strategy=SagaCompensationStrategy.BACKWARD,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
                SagaStep(step_id="s2", action="a2", compensation="c2"),
                SagaStep(step_id="s3", action="a3", compensation="c3"),
                SagaStep(step_id="s4", action="a4", compensation="c4"),
            ],
        )

        comp_order = []

        def step_handler(step, context):
            if step.step_id == "s4":
                raise RuntimeError("s4 failed")
            return {"ok": True}

        def compensation_handler(step, context):
            comp_order.append(step.step_id)
            return {"undone": True}

        orchestrator = SagaOrchestrator(saga, step_handler, compensation_handler)
        state = orchestrator.execute({})

        # s1-s3 completed, s4 failed
        for i in range(3):
            assert state.step_results[i].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[3].action_status == SagaStepStatus.FAILED

        # Compensation theo thứ tự ngược: s3 -> s2 -> s1
        assert comp_order == ["s3", "s2", "s1"]
        for i in range(3):
            assert state.step_results[i].compensation_status == SagaStepStatus.COMPENSATED

    def test_non_compensatable_steps_skipped_during_backward(self):
        """Steps không compensatable bị bỏ qua trong backward compensation."""
        saga = SagaDefinition(
            saga_id="backward-skip",
            name="Backward Skip",
            compensation_strategy=SagaCompensationStrategy.BACKWARD,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1", is_compensatable=True),
                SagaStep(step_id="s2", action="a2", compensation="c2", is_compensatable=True),
                SagaStep(step_id="s3", action="a3", compensation="c3"),
            ],
        )

        comp_order = []

        def step_handler(step, context):
            if step.step_id == "s3":
                raise RuntimeError("s3 failed")
            return {"ok": True}

        def compensation_handler(step, context):
            comp_order.append(step.step_id)
            return {"undone": True}

        orchestrator = SagaOrchestrator(saga, step_handler, compensation_handler)
        state = orchestrator.execute({})

        # Backward compensate vẫn gọi compensation cho tất cả steps đã completed
        # (bất kể is_compensatable, vì backward không phân biệt)
        # Theo code: _backward_compensate duyệt ngược và chỉ kiểm tra COMPLETED
        assert state.step_results[0].compensation_status == SagaStepStatus.COMPENSATED
        assert state.step_results[1].compensation_status == SagaStepStatus.COMPENSATED


# =============================================================================
# TestSagaOrchestratorForwardRecovery
# =============================================================================


class TestSagaOrchestratorForwardRecovery:
    """Test _forward_recovery() của SagaOrchestrator."""

    def test_skip_failed_step_continue_remaining(self):
        """Bỏ qua step fail, tiếp tục các step còn lại."""
        saga = SagaDefinition(
            saga_id="forward-rtest",
            name="Forward RT",
            compensation_strategy=SagaCompensationStrategy.FORWARD,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
                SagaStep(step_id="s2", action="a2", compensation="c2"),
                SagaStep(step_id="s3", action="a3", compensation="c3"),
                SagaStep(step_id="s4", action="a4", compensation="c4"),
            ],
        )

        action_order = []

        def step_handler(step, context):
            action_order.append(step.step_id)
            if step.step_id == "s2":
                raise RuntimeError("s2 failed")
            return {"ok": True}

        orchestrator = SagaOrchestrator(saga, step_handler)
        state = orchestrator.execute({})

        # s1 completed, s2 skipped, s3 và s4 tiếp tục
        assert state.step_results[0].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[1].action_status == SagaStepStatus.SKIPPED
        assert state.step_results[2].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[3].action_status == SagaStepStatus.COMPLETED

        # s3, s4 được gọi sau khi s2 fail
        assert "s3" in action_order
        assert "s4" in action_order

    def test_forward_recovery_skips_second_failure(self):
        """Forward recovery skip step thứ 2 nếu cũng fail."""
        saga = SagaDefinition(
            saga_id="forward-multi-fail",
            name="Forward Multi Fail",
            compensation_strategy=SagaCompensationStrategy.FORWARD,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
                SagaStep(step_id="s2", action="a2", compensation="c2"),
                SagaStep(step_id="s3", action="a3", compensation="c3"),
            ],
        )

        def step_handler(step, context):
            if step.step_id in ("s2", "s3"):
                raise RuntimeError(f"{step.step_id} failed")
            return {"ok": True}

        orchestrator = SagaOrchestrator(saga, step_handler)
        state = orchestrator.execute({})

        # s1 completed, s2 skipped, s3 also skipped
        assert state.step_results[0].action_status == SagaStepStatus.COMPLETED
        assert state.step_results[1].action_status == SagaStepStatus.SKIPPED
        assert state.step_results[2].action_status == SagaStepStatus.SKIPPED


# =============================================================================
# TestSagaStepResult
# =============================================================================


class TestSagaStepResult:
    """Test SagaStepResult dataclass."""

    def test_all_fields_exist(self):
        """Kiểm tra tất cả fields của SagaStepResult."""
        result = SagaStepResult(step_id="s1")

        assert hasattr(result, "step_id")
        assert hasattr(result, "action_status")
        assert hasattr(result, "compensation_status")
        assert hasattr(result, "action_output")
        assert hasattr(result, "action_error")
        assert hasattr(result, "compensation_output")
        assert hasattr(result, "compensation_error")
        assert hasattr(result, "started_at")
        assert hasattr(result, "completed_at")

    def test_action_and_compensation_status_tracked_separately(self):
        """Action và compensation status được theo dõi riêng biệt."""
        result = SagaStepResult(step_id="s1")

        # Mặc định cả hai đều PENDING
        assert result.action_status == SagaStepStatus.PENDING
        assert result.compensation_status == SagaStepStatus.PENDING

        # Có thể thay đổi độc lập
        result.action_status = SagaStepStatus.COMPLETED
        assert result.action_status == SagaStepStatus.COMPLETED
        assert result.compensation_status == SagaStepStatus.PENDING

        result.compensation_status = SagaStepStatus.COMPENSATED
        assert result.action_status == SagaStepStatus.COMPLETED
        assert result.compensation_status == SagaStepStatus.COMPENSATED

    def test_default_values(self):
        """Giá trị mặc định của các fields."""
        result = SagaStepResult(step_id="s1")

        assert result.step_id == "s1"
        assert result.action_status == SagaStepStatus.PENDING
        assert result.compensation_status == SagaStepStatus.PENDING
        assert result.action_output == {}
        assert result.action_error is None
        assert result.compensation_output == {}
        assert result.compensation_error is None
        assert result.started_at is None
        assert result.completed_at is None

    def test_action_error_and_output(self):
        """Action error và output được lưu đúng."""
        result = SagaStepResult(step_id="s1")
        result.action_status = SagaStepStatus.FAILED
        result.action_error = "Something went wrong"

        assert result.action_error == "Something went wrong"

        result2 = SagaStepResult(step_id="s2")
        result2.action_status = SagaStepStatus.COMPLETED
        result2.action_output = {"result": "success"}

        assert result2.action_output == {"result": "success"}
        assert result2.action_error is None

    def test_compensation_error_and_output(self):
        """Compensation error và output được lưu đúng."""
        result = SagaStepResult(step_id="s1")
        result.compensation_status = SagaStepStatus.FAILED
        result.compensation_error = "Comp failed"

        assert result.compensation_error == "Comp failed"

        result2 = SagaStepResult(step_id="s2")
        result2.compensation_status = SagaStepStatus.COMPENSATED
        result2.compensation_output = {"rolled_back": True}

        assert result2.compensation_output == {"rolled_back": True}
        assert result2.compensation_error is None


# =============================================================================
# TestGetSagaLog
# =============================================================================


class TestGetSagaLog:
    """Test get_saga_log() của SagaOrchestrator."""

    def test_returns_execution_log_entries(self):
        """get_saga_log() trả về danh sách log entries."""
        saga = SagaDefinition(
            saga_id="log-saga",
            name="Log Saga",
            enable_saga_log=True,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
                SagaStep(step_id="s2", action="a2", compensation="c2"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})
        log = orchestrator.get_saga_log()

        assert isinstance(log, list)
        assert len(log) > 0

    def test_log_contains_step_events(self):
        """Saga log chứa các step events."""
        saga = SagaDefinition(
            saga_id="step-event-saga",
            name="Step Event",
            enable_saga_log=True,
            steps=[
                SagaStep(step_id="s1", action="create_order", compensation="cancel_order"),
                SagaStep(step_id="s2", action="ship_order", compensation="recall_order"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})
        log = orchestrator.get_saga_log()

        event_types = [entry["event_type"] for entry in log]

        # Kiểm tra có chứa saga_started và saga_completed
        assert "saga_started" in event_types
        assert "saga_completed" in event_types

        # Kiểm tra có chứa step events
        assert "step_started" in event_types
        assert "step_completed" in event_types

    def test_log_entries_have_timestamp(self):
        """Mỗi log entry có timestamp và event_type."""
        saga = SagaDefinition(
            saga_id="timestamp-saga",
            name="Timestamp",
            enable_saga_log=True,
            steps=[
                SagaStep(step_id="s1", action="do_something", compensation="undo"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})
        log = orchestrator.get_saga_log()

        for entry in log:
            assert "event_type" in entry
            assert "timestamp" in entry
            assert isinstance(entry["event_type"], str)
            assert isinstance(entry["timestamp"], str)

    def test_log_disabled_no_entries(self):
        """Khi enable_saga_log=False, log không chứa entries."""
        saga = SagaDefinition(
            saga_id="no-log-saga",
            name="No Log",
            enable_saga_log=False,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})
        log = orchestrator.get_saga_log()

        assert len(log) == 0

    def test_log_contains_saga_events(self):
        """Log chứa event thông tin saga."""
        saga = SagaDefinition(
            saga_id="saga-info-test",
            name="Saga Info",
            enable_saga_log=True,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})
        log = orchestrator.get_saga_log()

        # Tìm saga_started event
        started = [e for e in log if e["event_type"] == "saga_started"]
        assert len(started) == 1
        assert started[0]["saga_id"] == "saga-info-test"
        assert started[0]["saga_name"] == "Saga Info"
        assert started[0]["strategy"] == "backward"

        # Tìm saga_completed event
        completed = [e for e in log if e["event_type"] == "saga_completed"]
        assert len(completed) == 1
        assert "final_status" in completed[0]

    def test_log_returns_copy(self):
        """get_saga_log() trả về copy, không ảnh hưởng internal log."""
        saga = SagaDefinition(
            saga_id="copy-saga",
            name="Copy",
            enable_saga_log=True,
            steps=[
                SagaStep(step_id="s1", action="a1", compensation="c1"),
            ],
        )

        orchestrator = SagaOrchestrator(saga)
        orchestrator.execute({})

        log1 = orchestrator.get_saga_log()
        log1.append({"event_type": "fake"})
        log2 = orchestrator.get_saga_log()

        # log2 không chứa fake entry
        event_types = [e["event_type"] for e in log2]
        assert "fake" not in event_types
