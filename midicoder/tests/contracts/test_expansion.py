"""
Unit Tests cho Expansion Contracts.

Kiểm tra behavior của:
- ExpansionTrace class
- ExpansionStep class
- ExpansionReport class

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.expansion import (
    ExpansionTrace,
    ExpansionStep,
    ExpansionReport,
)


class TestExpansionTrace:
    """Tests cho ExpansionTrace class."""

    def test_trace_created_with_required_fields(self):
        """Kiểm tra ExpansionTrace được tạo với source_id và source_type."""
        trace = ExpansionTrace(
            source_id="create_order",
            source_type="authorized_mutation",
        )

        assert trace.source_id == "create_order"
        assert trace.source_type == "authorized_mutation"
        assert trace.target_ids == []
        assert trace.params_mapping == {}
        assert trace.obligations_added == []
        assert trace.config_applied == {}

    def test_trace_created_with_all_fields(self):
        """Kiểm tra ExpansionTrace được tạo với tất cả fields."""
        trace = ExpansionTrace(
            source_id="create_order",
            source_type="authorized_mutation",
            target_ids=["auth_001", "tenant_001", "create_001"],
            params_mapping={"permission": "order.create"},
            obligations_added=["permission_check_required"],
            config_applied={"timeout": 30000},
        )

        assert len(trace.target_ids) == 3
        assert trace.params_mapping == {"permission": "order.create"}
        assert trace.obligations_added == ["permission_check_required"]
        assert trace.config_applied == {"timeout": 30000}

    def test_trace_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        trace = ExpansionTrace(
            source_id="test_trace",
            source_type="macro_type",
            target_ids=["core1", "core2"],
            params_mapping={"key": "value"},
            obligations_added=["oblig1"],
            config_applied={"timeout": 10000},
        )
        trace_dict = trace.to_dict()

        assert trace_dict["source_id"] == "test_trace"
        assert trace_dict["source_type"] == "macro_type"
        assert trace_dict["target_ids"] == ["core1", "core2"]
        assert trace_dict["params_mapping"] == {"key": "value"}
        assert trace_dict["obligations_added"] == ["oblig1"]
        assert trace_dict["config_applied"] == {"timeout": 10000}

    def test_trace_from_dict_creates_trace(self):
        """Kiểm tra from_dict tạo ExpansionTrace đúng."""
        trace_data = {
            "source_id": "test_from_dict",
            "source_type": "authorized_query",
            "target_ids": ["query_001"],
            "params_mapping": {"entity": "Order"},
            "obligations_added": ["tenant_filter_required"],
            "config_applied": {},
        }

        trace = ExpansionTrace.from_dict(trace_data)

        assert trace.source_id == "test_from_dict"
        assert trace.source_type == "authorized_query"
        assert trace.target_ids == ["query_001"]

    def test_trace_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = ExpansionTrace(
            source_id="test_roundtrip",
            source_type="mutation",
            target_ids=["op1", "op2", "op3"],
            params_mapping={"param1": "value1"},
            obligations_added=["oblig1", "oblig2"],
            config_applied={"timeout": 5000},
        )

        trace_dict = original.to_dict()
        reconstructed = ExpansionTrace.from_dict(trace_dict)

        assert reconstructed.source_id == original.source_id
        assert reconstructed.source_type == original.source_type
        assert reconstructed.target_ids == original.target_ids
        assert reconstructed.params_mapping == original.params_mapping
        assert reconstructed.obligations_added == original.obligations_added
        assert reconstructed.config_applied == original.config_applied


class TestExpansionStep:
    """Tests cho ExpansionStep class."""

    def test_step_created_with_required_fields(self):
        """Kiểm tra ExpansionStep được tạo với step_name và step_number."""
        step = ExpansionStep(
            step_name="resolve_macro",
            step_number=1,
        )

        assert step.step_name == "resolve_macro"
        assert step.step_number == 1
        assert step.input_refs == []
        assert step.output_refs == []
        assert step.status == "success"
        assert step.trace is None
        assert step.error is None

    def test_step_created_with_trace(self):
        """Kiểm tra ExpansionStep với trace."""
        trace = ExpansionTrace(
            source_id="create_order",
            source_type="authorized_mutation",
            target_ids=["auth_001"],
        )
        step = ExpansionStep(
            step_name="resolve_macro",
            step_number=1,
            trace=trace,
        )

        assert step.trace is not None
        assert step.trace.source_id == "create_order"

    def test_step_created_with_error(self):
        """Kiểm tra ExpansionStep với error."""
        step = ExpansionStep(
            step_name="generate_cores",
            step_number=2,
            status="failed",
            error="Macro not found",
        )

        assert step.status == "failed"
        assert step.error == "Macro not found"
        assert step.is_failed is True

    def test_step_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        trace = ExpansionTrace(
            source_id="test",
            source_type="macro",
        )
        step = ExpansionStep(
            step_name="test_step",
            step_number=1,
            input_refs=["input1"],
            output_refs=["output1"],
            status="success",
            trace=trace,
        )
        step_dict = step.to_dict()

        assert step_dict["step_name"] == "test_step"
        assert step_dict["step_number"] == 1
        assert step_dict["input_refs"] == ["input1"]
        assert step_dict["output_refs"] == ["output1"]
        assert step_dict["status"] == "success"
        assert "trace" in step_dict

    def test_step_to_dict_with_error(self):
        """Kiểm tra to_dict với error."""
        step = ExpansionStep(
            step_name="test_step",
            step_number=1,
            status="failed",
            error="Error message",
        )
        step_dict = step.to_dict()

        assert step_dict["error"] == "Error message"

    def test_step_from_dict_creates_step(self):
        """Kiểm tra from_dict tạo ExpansionStep đúng."""
        step_data = {
            "step_name": "resolve_macro",
            "step_number": 1,
            "input_refs": ["instance:create_order"],
            "output_refs": ["macro:authorized_mutation"],
            "status": "success",
            "trace": {
                "source_id": "create_order",
                "source_type": "authorized_mutation",
            },
        }

        step = ExpansionStep.from_dict(step_data)

        assert step.step_name == "resolve_macro"
        assert step.step_number == 1
        assert step.trace is not None

    def test_step_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        trace = ExpansionTrace(
            source_id="test",
            source_type="macro",
            target_ids=["core1"],
        )
        original = ExpansionStep(
            step_name="test_step",
            step_number=2,
            input_refs=["input1"],
            output_refs=["output1"],
            status="success",
            trace=trace,
        )

        step_dict = original.to_dict()
        reconstructed = ExpansionStep.from_dict(step_dict)

        assert reconstructed.step_name == original.step_name
        assert reconstructed.step_number == original.step_number
        assert reconstructed.status == original.status
        assert reconstructed.trace is not None

    def test_is_success_property(self):
        """Kiểm tra is_success property."""
        success_step = ExpansionStep(
            step_name="test",
            step_number=1,
            status="success",
        )
        failed_step = ExpansionStep(
            step_name="test",
            step_number=1,
            status="failed",
        )

        assert success_step.is_success is True
        assert failed_step.is_success is False

    def test_is_failed_property(self):
        """Kiểm tra is_failed property."""
        success_step = ExpansionStep(
            step_name="test",
            step_number=1,
            status="success",
        )
        failed_step = ExpansionStep(
            step_name="test",
            step_number=1,
            status="failed",
        )

        assert success_step.is_failed is False
        assert failed_step.is_failed is True


class TestExpansionReport:
    """Tests cho ExpansionReport class."""

    def test_report_created_empty(self):
        """Kiểm tra ExpansionReport có thể được tạo rỗng."""
        report = ExpansionReport()

        assert report is not None
        assert report.source_instance_id == ""
        assert report.source_macro_type == ""
        assert report.steps == []
        assert report.final_core_instances == []
        assert report.total_obligations == []
        assert report.expansion_time_ms is None

    def test_report_created_with_all_fields(self):
        """Kiểm tra ExpansionReport được tạo với tất cả fields."""
        step1 = ExpansionStep(step_name="resolve_macro", step_number=1)
        step2 = ExpansionStep(step_name="generate_cores", step_number=2)
        report = ExpansionReport(
            source_instance_id="create_order",
            source_macro_type="authorized_mutation",
            steps=[step1, step2],
            final_core_instances=["auth_001", "create_001"],
            total_obligations=["permission_check_required"],
            expansion_time_ms=150,
        )

        assert report.source_instance_id == "create_order"
        assert len(report.steps) == 2
        assert len(report.final_core_instances) == 2
        assert report.expansion_time_ms == 150

    def test_report_add_step(self):
        """Kiểm tra add_step thêm step vào report."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )

        step = report.add_step(
            step_name="resolve_macro",
            step_number=1,
            status="success",
        )

        assert len(report.steps) == 1
        assert report.get_step("resolve_macro") is not None

    def test_report_get_step(self):
        """Kiểm tra get_step trả về step đúng."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="resolve_macro", step_number=1)
        report.add_step(step_name="generate_cores", step_number=2)

        step = report.get_step("generate_cores")
        assert step is not None
        assert step.step_number == 2

    def test_report_get_step_by_number(self):
        """Kiểm tra get_step_by_number trả về step đúng."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="resolve_macro", step_number=1)
        report.add_step(step_name="generate_cores", step_number=2)

        step = report.get_step_by_number(2)
        assert step is not None
        assert step.step_name == "generate_cores"

    def test_report_is_successful(self):
        """Kiểm tra is_successful returns True khi tất cả steps thành công."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="step1", step_number=1, status="success")
        report.add_step(step_name="step2", step_number=2, status="success")

        assert report.is_successful() is True

    def test_report_is_successful_with_failed_step(self):
        """Kiểm tra is_successful returns False khi có step failed."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="step1", step_number=1, status="success")
        report.add_step(step_name="step2", step_number=2, status="failed", error="Error")

        assert report.is_successful() is False

    def test_report_get_failed_steps(self):
        """Kiểm tra get_failed_steps trả về danh sách failed steps."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="step1", step_number=1, status="success")
        report.add_step(step_name="step2", step_number=2, status="failed", error="Error1")
        report.add_step(step_name="step3", step_number=3, status="failed", error="Error2")

        failed = report.get_failed_steps()
        assert len(failed) == 2

    def test_report_get_all_trace(self):
        """Kiểm tra get_all_trace trả về tất cả traces."""
        trace1 = ExpansionTrace(source_id="id1", source_type="type1")
        trace2 = ExpansionTrace(source_id="id2", source_type="type2")
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
        )
        report.add_step(step_name="step1", step_number=1, trace=trace1)
        report.add_step(step_name="step2", step_number=2, trace=trace2)
        report.add_step(step_name="step3", step_number=3)

        traces = report.get_all_trace()
        assert len(traces) == 2

    def test_report_obligation_summary(self):
        """Kiểm tra get_obligation_summary trả về summary đúng."""
        trace1 = ExpansionTrace(
            source_id="id1",
            source_type="type1",
            obligations_added=["oblig1"],
        )
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
            total_obligations=["oblig1", "oblig2"],
        )
        report.add_step(step_name="step1", step_number=1, trace=trace1)

        summary = report.get_obligation_summary()
        assert summary["total_obligations"] == 2
        assert "oblig1" in summary["obligations"]

    def test_report_core_instance_summary(self):
        """Kiểm tra get_core_instance_summary trả về summary đúng."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
            final_core_instances=["core1", "core2", "core3"],
        )

        summary = report.get_core_instance_summary()
        assert summary["total_cores"] == 3

    def test_report_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        report = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
            final_core_instances=["core1"],
            expansion_time_ms=100,
        )
        report_dict = report.to_dict()

        assert "source_instance_id" in report_dict
        assert "source_macro_type" in report_dict
        assert "steps" in report_dict
        assert "final_core_instances" in report_dict
        assert "total_obligations" in report_dict
        assert "expansion_time_ms" in report_dict

    def test_report_from_dict_creates_report(self):
        """Kiểm tra from_dict tạo ExpansionReport đúng."""
        # Note: This test may need metadata param fix in ExpansionReport.from_dict
        report_data = {
            "type": "expansion_report",
            "version": "1.0.0",
            "metadata": {},
            "source_instance_id": "test",
            "source_macro_type": "macro",
            "steps": [
                {
                    "step_name": "resolve_macro",
                    "step_number": 1,
                    "status": "success",
                }
            ],
            "final_core_instances": ["core1"],
            "total_obligations": ["oblig1"],
            "expansion_time_ms": 100,
        }

        report = ExpansionReport.from_dict(report_data)

        assert report is not None
        assert report.source_instance_id == "test"
        assert report.source_macro_type == "macro"
        assert len(report.steps) == 1
        assert report.expansion_time_ms == 100

    def test_report_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        trace = ExpansionTrace(
            source_id="test",
            source_type="macro",
            target_ids=["core1"],
        )
        original = ExpansionReport(
            source_instance_id="test",
            source_macro_type="macro",
            final_core_instances=["core1", "core2"],
            total_obligations=["oblig1"],
            expansion_time_ms=150,
        )
        original.add_step(step_name="resolve_macro", step_number=1, trace=trace)

        report_dict = original.to_dict()
        reconstructed = ExpansionReport.from_dict(report_dict)

        assert reconstructed.source_instance_id == original.source_instance_id
        assert reconstructed.source_macro_type == original.source_macro_type
        assert len(reconstructed.steps) == len(original.steps)
        assert reconstructed.final_core_instances == original.final_core_instances
        assert reconstructed.total_obligations == original.total_obligations