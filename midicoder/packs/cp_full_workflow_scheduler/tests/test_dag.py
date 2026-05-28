"""
Test suite cho DAG models và DAG Executor Engine.

Mô-đun này test các thành phần DAG workflow:
- DAGExecutionMode, DAGFailurePolicy (enums)
- DAGNode, DAGWorkflow (models)
- DAGExecutor (engine)
- DAGExecutionState, DAGNodeResult, DAGExecutionContext (runtime)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from uuid import uuid4
from datetime import datetime

from midicoder.packs.cp_full_workflow_scheduler.models import (
    DAGWorkflow,
    DAGNode,
    DAGExecutionMode,
    DAGFailurePolicy,
)
from midicoder.packs.cp_full_workflow_scheduler.engine.dag_executor import (
    DAGExecutor,
    DAGExecutionState,
    DAGNodeResult,
    DAGExecutionContext,
)
from midicoder.errors import MidicoderError, ErrorCode


# =============================================================================
# TestDAGExecutionMode
# =============================================================================


class TestDAGExecutionMode:
    """Test enum DAGExecutionMode."""

    def test_sequential_value(self):
        """Giá trị SEQUENTIAL đúng."""
        assert DAGExecutionMode.SEQUENTIAL.value == "sequential"

    def test_parallel_value(self):
        """Giá trị PARALLEL đúng."""
        assert DAGExecutionMode.PARALLEL.value == "parallel"

    def test_parallel_with_fanin_value(self):
        """Giá trị PARALLEL_WITH_FANIN đúng."""
        assert DAGExecutionMode.PARALLEL_WITH_FANIN.value == "parallel_with_fanin"

    def test_dynamic_value(self):
        """Giá trị DYNAMIC đúng."""
        assert DAGExecutionMode.DYNAMIC.value == "dynamic"

    def test_all_four_values_exist(self):
        """Kiểm tra tất cả 4 giá trị enum tồn tại."""
        values = [e.value for e in DAGExecutionMode]
        assert len(values) == 4
        assert "sequential" in values
        assert "parallel" in values
        assert "parallel_with_fanin" in values
        assert "dynamic" in values

    def test_create_from_string(self):
        """Tạo DAGExecutionMode từ string."""
        assert DAGExecutionMode("sequential") == DAGExecutionMode.SEQUENTIAL
        assert DAGExecutionMode("parallel") == DAGExecutionMode.PARALLEL
        assert DAGExecutionMode("parallel_with_fanin") == DAGExecutionMode.PARALLEL_WITH_FANIN
        assert DAGExecutionMode("dynamic") == DAGExecutionMode.DYNAMIC


# =============================================================================
# TestDAGFailurePolicy
# =============================================================================


class TestDAGFailurePolicy:
    """Test enum DAGFailurePolicy."""

    def test_fail_fast_value(self):
        """Giá trị FAIL_FAST đúng."""
        assert DAGFailurePolicy.FAIL_FAST.value == "fail_fast"

    def test_skip_and_continue_value(self):
        """Giá trị SKIP_AND_CONTINUE đúng."""
        assert DAGFailurePolicy.SKIP_AND_CONTINUE.value == "skip_and_continue"

    def test_retry_then_skip_value(self):
        """Giá trị RETRY_THEN_SKIP đúng."""
        assert DAGFailurePolicy.RETRY_THEN_SKIP.value == "retry_then_skip"

    def test_compensate_value(self):
        """Giá trị COMPENSATE đúng."""
        assert DAGFailurePolicy.COMPENSATE.value == "compensate"

    def test_all_four_values_exist(self):
        """Kiểm tra tất cả 4 giá trị enum tồn tại."""
        values = [e.value for e in DAGFailurePolicy]
        assert len(values) == 4
        assert "fail_fast" in values
        assert "skip_and_continue" in values
        assert "retry_then_skip" in values
        assert "compensate" in values

    def test_create_from_string(self):
        """Tạo DAGFailurePolicy từ string."""
        assert DAGFailurePolicy("fail_fast") == DAGFailurePolicy.FAIL_FAST
        assert DAGFailurePolicy("skip_and_continue") == DAGFailurePolicy.SKIP_AND_CONTINUE
        assert DAGFailurePolicy("retry_then_skip") == DAGFailurePolicy.RETRY_THEN_SKIP
        assert DAGFailurePolicy("compensate") == DAGFailurePolicy.COMPENSATE


# =============================================================================
# TestDAGNode
# =============================================================================


class TestDAGNode:
    """Test DAGNode dataclass."""

    def test_create_minimal_node(self):
        """Tạo node với tối thiểu fields."""
        node = DAGNode(node_id="node_1")

        assert node.node_id == "node_1"
        assert node.node_type == "task"
        assert node.handler == ""
        assert node.inputs == {}
        assert node.outputs == []
        assert node.depends_on == []
        assert node.timeout_seconds == 300
        assert node.retry_count == 0
        assert node.description == ""

    def test_create_full_node(self):
        """Tạo node với đầy đủ fields."""
        node = DAGNode(
            node_id="node_full",
            node_type="branch",
            handler="handlers.process_data",
            inputs={"key": "value"},
            outputs=["out1", "out2"],
            depends_on=["node_a", "node_b"],
            timeout_seconds=600,
            retry_count=3,
            description="Node đầy đủ fields",
        )

        assert node.node_id == "node_full"
        assert node.node_type == "branch"
        assert node.handler == "handlers.process_data"
        assert node.inputs == {"key": "value"}
        assert node.outputs == ["out1", "out2"]
        assert node.depends_on == ["node_a", "node_b"]
        assert node.timeout_seconds == 600
        assert node.retry_count == 3
        assert node.description == "Node đầy đủ fields"

    def test_default_node_type(self):
        """Default node_type là 'task'."""
        node = DAGNode(node_id="n")
        assert node.node_type == "task"

    def test_default_timeout(self):
        """Default timeout_seconds là 300."""
        node = DAGNode(node_id="n")
        assert node.timeout_seconds == 300

    def test_default_retry_count(self):
        """Default retry_count là 0."""
        node = DAGNode(node_id="n")
        assert node.retry_count == 0

    def test_to_dict(self):
        """Chuyển node sang dict."""
        node = DAGNode(
            node_id="dict_test",
            node_type="merge",
            handler="merge_handler",
            inputs={"a": 1},
            outputs=["merged"],
            depends_on=["left", "right"],
            timeout_seconds=120,
            retry_count=2,
            description="Test dict",
        )
        d = node.to_dict()

        assert d["node_id"] == "dict_test"
        assert d["node_type"] == "merge"
        assert d["handler"] == "merge_handler"
        assert d["inputs"] == {"a": 1}
        assert d["outputs"] == ["merged"]
        assert d["depends_on"] == ["left", "right"]
        assert d["timeout_seconds"] == 120
        assert d["retry_count"] == 2
        assert d["description"] == "Test dict"

    def test_from_dict(self):
        """Tạo node từ dict."""
        data = {
            "node_id": "from_dict_node",
            "node_type": "condition",
            "handler": "check_condition",
            "inputs": {"threshold": 100},
            "outputs": ["result"],
            "depends_on": ["preprocessor"],
            "timeout_seconds": 500,
            "retry_count": 1,
            "description": "Từ dict",
        }
        node = DAGNode.from_dict(data)

        assert node.node_id == "from_dict_node"
        assert node.node_type == "condition"
        assert node.handler == "check_condition"
        assert node.inputs == {"threshold": 100}
        assert node.outputs == ["result"]
        assert node.depends_on == ["preprocessor"]
        assert node.timeout_seconds == 500
        assert node.retry_count == 1
        assert node.description == "Từ dict"

    def test_to_dict_from_dict_roundtrip(self):
        """Roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        original = DAGNode(
            node_id="roundtrip_node",
            node_type="wait",
            handler="wait_handler",
            inputs={"duration": 30},
            outputs=["done"],
            depends_on=["start"],
            timeout_seconds=900,
            retry_count=5,
            description="Roundtrip test",
        )

        restored = DAGNode.from_dict(original.to_dict())

        assert restored.node_id == original.node_id
        assert restored.node_type == original.node_type
        assert restored.handler == original.handler
        assert restored.inputs == original.inputs
        assert restored.outputs == original.outputs
        assert restored.depends_on == original.depends_on
        assert restored.timeout_seconds == original.timeout_seconds
        assert restored.retry_count == original.retry_count
        assert restored.description == original.description

    def test_from_dict_with_defaults(self):
        """from_dict với dict thiếu fields áp dụng defaults."""
        data = {"node_id": "partial"}
        node = DAGNode.from_dict(data)

        assert node.node_id == "partial"
        assert node.node_type == "task"
        assert node.handler == ""
        assert node.inputs == {}
        assert node.outputs == []
        assert node.depends_on == []
        assert node.timeout_seconds == 300
        assert node.retry_count == 0
        assert node.description == ""


# =============================================================================
# TestDAGWorkflow
# =============================================================================


class TestDAGWorkflow:
    """Test DAGWorkflow dataclass."""

    def test_create_minimal_workflow(self):
        """Tạo workflow với tối thiểu fields."""
        wf = DAGWorkflow(workflow_id="wf_1", name="Test")

        assert wf.workflow_id == "wf_1"
        assert wf.name == "Test"
        assert wf.execution_mode == DAGExecutionMode.SEQUENTIAL
        assert wf.failure_policy == DAGFailurePolicy.FAIL_FAST
        assert wf.nodes == []
        assert wf.entry_points == []
        assert wf.exit_points == []
        assert wf.max_parallelism == 4
        assert wf.description == ""

    def test_create_full_workflow(self):
        """Tạo workflow với đầy đủ fields."""
        nodes = [
            DAGNode(node_id="n1"),
            DAGNode(node_id="n2", depends_on=["n1"]),
            DAGNode(node_id="n3", depends_on=["n2"]),
        ]
        wf = DAGWorkflow(
            workflow_id="wf_full",
            name="Full Workflow",
            execution_mode=DAGExecutionMode.PARALLEL,
            failure_policy=DAGFailurePolicy.COMPENSATE,
            nodes=nodes,
            entry_points=["n1"],
            exit_points=["n3"],
            max_parallelism=8,
            description="Workflow đầy đủ",
        )

        assert wf.workflow_id == "wf_full"
        assert wf.name == "Full Workflow"
        assert wf.execution_mode == DAGExecutionMode.PARALLEL
        assert wf.failure_policy == DAGFailurePolicy.COMPENSATE
        assert len(wf.nodes) == 3
        assert wf.entry_points == ["n1"]
        assert wf.exit_points == ["n3"]
        assert wf.max_parallelism == 8
        assert wf.description == "Workflow đầy đủ"

    def test_default_execution_mode(self):
        """Default execution_mode là SEQUENTIAL."""
        wf = DAGWorkflow(workflow_id="w", name="w")
        assert wf.execution_mode == DAGExecutionMode.SEQUENTIAL

    def test_default_failure_policy(self):
        """Default failure_policy là FAIL_FAST."""
        wf = DAGWorkflow(workflow_id="w", name="w")
        assert wf.failure_policy == DAGFailurePolicy.FAIL_FAST

    def test_default_max_parallelism(self):
        """Default max_parallelism là 4."""
        wf = DAGWorkflow(workflow_id="w", name="w")
        assert wf.max_parallelism == 4

    def test_to_dict(self):
        """Chuyển workflow sang dict."""
        wf = DAGWorkflow(
            workflow_id="dict_wf",
            name="Dict Workflow",
            execution_mode=DAGExecutionMode.DYNAMIC,
            failure_policy=DAGFailurePolicy.RETRY_THEN_SKIP,
            nodes=[DAGNode(node_id="a"), DAGNode(node_id="b", depends_on=["a"])],
            entry_points=["a"],
            exit_points=["b"],
            max_parallelism=2,
            description="Dict test",
        )
        d = wf.to_dict()

        assert d["workflow_id"] == "dict_wf"
        assert d["name"] == "Dict Workflow"
        assert d["execution_mode"] == "dynamic"
        assert d["failure_policy"] == "retry_then_skip"
        assert len(d["nodes"]) == 2
        assert d["entry_points"] == ["a"]
        assert d["exit_points"] == ["b"]
        assert d["max_parallelism"] == 2
        assert d["description"] == "Dict test"

    def test_from_dict(self):
        """Tạo workflow từ dict."""
        data = {
            "workflow_id": "from_dict_wf",
            "name": "From Dict",
            "execution_mode": "parallel_with_fanin",
            "failure_policy": "skip_and_continue",
            "nodes": [
                {"node_id": "x", "depends_on": []},
                {"node_id": "y", "depends_on": []},
                {"node_id": "z", "depends_on": ["x", "y"]},
            ],
            "entry_points": ["x", "y"],
            "exit_points": ["z"],
            "max_parallelism": 6,
            "description": "Fan-in workflow",
        }
        wf = DAGWorkflow.from_dict(data)

        assert wf.workflow_id == "from_dict_wf"
        assert wf.name == "From Dict"
        assert wf.execution_mode == DAGExecutionMode.PARALLEL_WITH_FANIN
        assert wf.failure_policy == DAGFailurePolicy.SKIP_AND_CONTINUE
        assert len(wf.nodes) == 3
        assert wf.entry_points == ["x", "y"]
        assert wf.exit_points == ["z"]
        assert wf.max_parallelism == 6

    def test_to_dict_from_dict_roundtrip(self):
        """Roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        original = DAGWorkflow(
            workflow_id="rt_wf",
            name="Roundtrip",
            execution_mode=DAGExecutionMode.PARALLEL,
            failure_policy=DAGFailurePolicy.FAIL_FAST,
            nodes=[
                DAGNode(node_id="s1", node_type="task", handler="h1"),
                DAGNode(node_id="s2", node_type="task", handler="h2", depends_on=["s1"]),
            ],
            entry_points=["s1"],
            exit_points=["s2"],
            max_parallelism=3,
            description="Roundtrip",
        )

        restored = DAGWorkflow.from_dict(original.to_dict())

        assert restored.workflow_id == original.workflow_id
        assert restored.name == original.name
        assert restored.execution_mode == original.execution_mode
        assert restored.failure_policy == original.failure_policy
        assert len(restored.nodes) == len(original.nodes)
        for i, n in enumerate(restored.nodes):
            assert n.node_id == original.nodes[i].node_id
            assert n.node_type == original.nodes[i].node_type
            assert n.handler == original.nodes[i].handler
            assert n.depends_on == original.nodes[i].depends_on
        assert restored.entry_points == original.entry_points
        assert restored.exit_points == original.exit_points
        assert restored.max_parallelism == original.max_parallelism
        assert restored.description == original.description

    def test_from_dict_with_defaults(self):
        """from_dict với dict thiếu fields áp dụng defaults."""
        data = {"workflow_id": "min", "name": "min"}
        wf = DAGWorkflow.from_dict(data)

        assert wf.workflow_id == "min"
        assert wf.name == "min"
        assert wf.execution_mode == DAGExecutionMode.SEQUENTIAL
        assert wf.failure_policy == DAGFailurePolicy.FAIL_FAST
        assert wf.nodes == []
        assert wf.entry_points == []
        assert wf.exit_points == []
        assert wf.max_parallelism == 4
        assert wf.description == ""


# =============================================================================
# TestDAGExecutorInit
# =============================================================================


class TestDAGExecutorInit:
    """Test khởi tạo DAGExecutor."""

    def test_create_executor_with_workflow(self):
        """Tạo executor từ DAGWorkflow."""
        wf = DAGWorkflow(
            workflow_id="wf_1",
            name="Test",
            nodes=[DAGNode(node_id="a"), DAGNode(node_id="b", depends_on=["a"])],
            entry_points=["a"],
            exit_points=["b"],
        )
        executor = DAGExecutor(wf)

        assert executor.dag_workflow == wf
        assert len(executor._node_map) == 2
        assert "a" in executor._node_map
        assert "b" in executor._node_map

    def test_create_executor_with_custom_node_handler(self):
        """Tạo executor với custom node_handler."""
        wf = DAGWorkflow(
            workflow_id="wf_2",
            name="Test Handler",
            nodes=[DAGNode(node_id="x")],
            entry_points=["x"],
            exit_points=["x"],
        )

        def custom_handler(node, context):
            return {"handled": True, "node_id": node.node_id}

        executor = DAGExecutor(wf, node_handler=custom_handler)

        assert executor.node_handler is custom_handler
        assert executor.node_handler is not executor._default_node_handler

    def test_node_map_built_correctly(self):
        """Node map được build đúng từ workflow nodes."""
        nodes = [
            DAGNode(node_id="n1"),
            DAGNode(node_id="n2"),
            DAGNode(node_id="n3"),
        ]
        wf = DAGWorkflow(
            workflow_id="wf_map",
            name="Map Test",
            nodes=nodes,
            entry_points=["n1"],
            exit_points=["n3"],
        )
        executor = DAGExecutor(wf)

        assert len(executor._node_map) == 3
        for n in nodes:
            assert executor._node_map[n.node_id] is n

    def test_adjacency_built_correctly(self):
        """Adjacency list được build đúng."""
        wf = DAGWorkflow(
            workflow_id="wf_adj",
            name="Adj Test",
            nodes=[
                DAGNode(node_id="a"),
                DAGNode(node_id="b", depends_on=["a"]),
                DAGNode(node_id="c", depends_on=["a"]),
            ],
            entry_points=["a"],
            exit_points=["c"],
        )
        executor = DAGExecutor(wf)

        # 'a' có b, c phụ thuộc
        assert "b" in executor._adjacency["a"]
        assert "c" in executor._adjacency["a"]
        # 'b' và 'c' là leaf
        assert executor._adjacency["b"] == []
        assert executor._adjacency["c"] == []


# =============================================================================
# TestDAGExecutorTopologicalSort
# =============================================================================


class TestDAGExecutorTopologicalSort:
    """Test topological sort của DAGExecutor."""

    def test_linear_dag(self):
        """DAG tuyến tính A → B → C."""
        wf = DAGWorkflow(
            workflow_id="linear",
            name="Linear",
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["B"]),
            ],
            entry_points=["A"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf)
        order = executor.topological_sort()

        assert order.index("A") < order.index("B") < order.index("C")

    def test_diamond_dag(self):
        """DAG kim cương A → B, A → C, B → D, C → D."""
        wf = DAGWorkflow(
            workflow_id="diamond",
            name="Diamond",
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["A"]),
                DAGNode(node_id="D", depends_on=["B", "C"]),
            ],
            entry_points=["A"],
            exit_points=["D"],
        )
        executor = DAGExecutor(wf)
        order = executor.topological_sort()

        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")

    def test_parallel_dag(self):
        """DAG song song A, B độc lập → C."""
        wf = DAGWorkflow(
            workflow_id="parallel",
            name="Parallel",
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B"),
                DAGNode(node_id="C", depends_on=["A", "B"]),
            ],
            entry_points=["A", "B"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf)
        order = executor.topological_sort()

        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("C")

    def test_single_node(self):
        """DAG với một node duy nhất."""
        wf = DAGWorkflow(
            workflow_id="single",
            name="Single",
            nodes=[DAGNode(node_id="only")],
            entry_points=["only"],
            exit_points=["only"],
        )
        executor = DAGExecutor(wf)
        order = executor.topological_sort()

        assert order == ["only"]

    def test_cycle_detection_raises_error(self):
        """Phát hiện cycle và throw CP13_WORKFLOW_STATE_MACHINE_ERROR."""
        wf = DAGWorkflow(
            workflow_id="cycle_wf",
            name="Cycle",
            nodes=[
                DAGNode(node_id="X", depends_on=["Z"]),
                DAGNode(node_id="Y", depends_on=["X"]),
                DAGNode(node_id="Z", depends_on=["Y"]),
            ],
            entry_points=["X"],
            exit_points=["Z"],
        )
        executor = DAGExecutor(wf)

        with pytest.raises(MidicoderError) as exc_info:
            executor.topological_sort()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR


# =============================================================================
# TestDAGExecutorValidate
# =============================================================================


class TestDAGExecutorValidate:
    """Test validate_dag của DAGExecutor."""

    def test_valid_dag_passes(self):
        """DAG hợp lệ thông qua validate."""
        wf = DAGWorkflow(
            workflow_id="valid",
            name="Valid",
            nodes=[
                DAGNode(node_id="a"),
                DAGNode(node_id="b", depends_on=["a"]),
            ],
            entry_points=["a"],
            exit_points=["b"],
        )
        executor = DAGExecutor(wf)
        # Không throw exception
        executor.validate_dag()

    def test_missing_dependency_raises_error(self):
        """Node phụ thuộc vào node không tồn tại throw CP13_JOB_NOT_FOUND."""
        wf = DAGWorkflow(
            workflow_id="missing_dep",
            name="Missing Dep",
            nodes=[
                DAGNode(node_id="a", depends_on=["nonexistent"]),
            ],
            entry_points=["a"],
            exit_points=["a"],
        )
        executor = DAGExecutor(wf)

        with pytest.raises(MidicoderError) as exc_info:
            executor.validate_dag()

        assert exc_info.value.code == ErrorCode.MDC-F20_JOB_NOT_FOUND

    def test_cycle_detected_raises_error(self):
        """Cycle được phát hiện trong validate throw CP13_WORKFLOW_STATE_MACHINE_ERROR."""
        wf = DAGWorkflow(
            workflow_id="cycle_val",
            name="Cycle Val",
            nodes=[
                DAGNode(node_id="p", depends_on=["q"]),
                DAGNode(node_id="q", depends_on=["p"]),
            ],
            entry_points=["p"],
            exit_points=["q"],
        )
        executor = DAGExecutor(wf)

        with pytest.raises(MidicoderError) as exc_info:
            executor.validate_dag()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR

    def test_entry_points_have_no_dependencies(self):
        """Entry points không có dependencies."""
        wf = DAGWorkflow(
            workflow_id="entry_dep",
            name="Entry Dep",
            nodes=[
                DAGNode(node_id="start", depends_on=["other"]),
                DAGNode(node_id="other"),
            ],
            entry_points=["start"],
            exit_points=["other"],
        )
        executor = DAGExecutor(wf)

        with pytest.raises(MidicoderError) as exc_info:
            executor.validate_dag()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR

    def test_exit_points_are_leaves(self):
        """Exit points là leaf nodes — không node nào phụ thuộc vào chúng."""
        wf = DAGWorkflow(
            workflow_id="exit_leaf",
            name="Exit Leaf",
            nodes=[
                DAGNode(node_id="mid"),
                DAGNode(node_id="end", depends_on=["mid"]),
            ],
            entry_points=["mid"],
            exit_points=["mid"],  # mid có end phụ thuộc -> không phải leaf
        )
        executor = DAGExecutor(wf)

        with pytest.raises(MidicoderError) as exc_info:
            executor.validate_dag()

        assert exc_info.value.code == ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR

    def test_valid_entry_and_exit_points(self):
        """Entry/exit points hợp lệ: entry no deps, exit is leaf."""
        wf = DAGWorkflow(
            workflow_id="good_eo",
            name="Good Entry/Exit",
            nodes=[
                DAGNode(node_id="root"),
                DAGNode(node_id="leaf", depends_on=["root"]),
            ],
            entry_points=["root"],
            exit_points=["leaf"],
        )
        executor = DAGExecutor(wf)
        executor.validate_dag()  # Should not raise


# =============================================================================
# TestDAGExecutorExecute
# =============================================================================


class TestDAGExecutorExecute:
    """Test execute của DAGExecutor."""

    def test_sequential_execution_order(self):
        """Sequential: nodes chạy theo topological order."""
        execution_order = []

        def handler(node, context):
            execution_order.append(node.node_id)
            return {"executed": node.node_id}

        wf = DAGWorkflow(
            workflow_id="seq_test",
            name="Sequential",
            execution_mode=DAGExecutionMode.SEQUENTIAL,
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["B"]),
            ],
            entry_points=["A"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf, node_handler=handler)
        result = executor.execute(input_data={})

        assert execution_order == ["A", "B", "C"]
        assert result.node_results["A"].status == DAGExecutionState.COMPLETED
        assert result.node_results["B"].status == DAGExecutionState.COMPLETED
        assert result.node_results["C"].status == DAGExecutionState.COMPLETED

    def test_parallel_execution_independent_nodes(self):
        """Parallel: nodes độc lập chạy cùng level."""
        execution_order = []

        def handler(node, context):
            execution_order.append(node.node_id)
            return {"executed": node.node_id}

        wf = DAGWorkflow(
            workflow_id="par_test",
            name="Parallel",
            execution_mode=DAGExecutionMode.PARALLEL,
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B"),
                DAGNode(node_id="C", depends_on=["A", "B"]),
            ],
            entry_points=["A", "B"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf, node_handler=handler)
        result = executor.execute(input_data={})

        # A và B chạy trước C
        assert result.node_results["A"].status == DAGExecutionState.COMPLETED
        assert result.node_results["B"].status == DAGExecutionState.COMPLETED
        assert result.node_results["C"].status == DAGExecutionState.COMPLETED
        assert "C" in execution_order

    def test_fail_fast_remaining_nodes_skipped(self):
        """FAIL_FAST: nodes còn lại bị SKIPPED khi node fail."""

        def failing_handler(node, context):
            if node.node_id == "B":
                raise RuntimeError("B failed")
            return {"ok": True}

        wf = DAGWorkflow(
            workflow_id="fail_fast",
            name="Fail Fast",
            execution_mode=DAGExecutionMode.SEQUENTIAL,
            failure_policy=DAGFailurePolicy.FAIL_FAST,
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["B"]),
            ],
            entry_points=["A"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf, node_handler=failing_handler)
        result = executor.execute(input_data={})

        assert result.node_results["A"].status == DAGExecutionState.COMPLETED
        assert result.node_results["B"].status == DAGExecutionState.FAILED
        assert result.node_results["C"].status == DAGExecutionState.SKIPPED

    def test_skip_and_continue(self):
        """SKIP_AND_CONTINUE: node fail bị skip, nodes còn lại tiếp tục."""

        def partial_handler(node, context):
            if node.node_id == "B":
                raise RuntimeError("B failed")
            return {"ok": True}

        wf = DAGWorkflow(
            workflow_id="skip_cont",
            name="Skip Continue",
            execution_mode=DAGExecutionMode.SEQUENTIAL,
            failure_policy=DAGFailurePolicy.SKIP_AND_CONTINUE,
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["B"]),
            ],
            entry_points=["A"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf, node_handler=partial_handler)
        result = executor.execute(input_data={})

        assert result.node_results["A"].status == DAGExecutionState.COMPLETED
        # B bị skip sau khi fail (policy đổi FAILED -> SKIPPED)
        assert result.node_results["B"].status == DAGExecutionState.SKIPPED
        # C bị skip vì dependency B là SKIPPED
        assert result.node_results["C"].status == DAGExecutionState.SKIPPED

    def test_retry_then_skip(self):
        """RETRY_THEN_SKIP: retry một lần rồi skip nếu vẫn fail."""
        call_count = {"count": 0}

        def always_fail_handler(node, context):
            call_count["count"] += 1
            raise RuntimeError("Always fails")

        wf = DAGWorkflow(
            workflow_id="retry_skip",
            name="Retry Skip",
            execution_mode=DAGExecutionMode.SEQUENTIAL,
            failure_policy=DAGFailurePolicy.RETRY_THEN_SKIP,
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
            ],
            entry_points=["A"],
            exit_points=["B"],
        )
        executor = DAGExecutor(wf, node_handler=always_fail_handler)
        result = executor.execute(input_data={})

        # A là node fail -> được retry 1 lần rồi skip
        assert result.node_results["A"].status == DAGExecutionState.SKIPPED
        # Error message có chứa thông tin retry
        assert "retry" in result.node_results["A"].error.lower()
        # Handler được gọi 2 lần cho node A (ban đầu + retry)
        assert call_count["count"] == 2
        # B bị skip vì dependency A là SKIPPED
        assert result.node_results["B"].status == DAGExecutionState.SKIPPED

    def test_compensate_completed_nodes(self):
        """COMPENSATE: nodes đã hoàn thành được compensate."""

        def compensating_handler(node, context):
            if node.node_id == "C":
                raise RuntimeError("C failed")
            return {"ok": True}

        wf = DAGWorkflow(
            workflow_id="compensate_wf",
            name="Compensate",
            execution_mode=DAGExecutionMode.SEQUENTIAL,
            failure_policy=DAGFailurePolicy.COMPENSATE,
            nodes=[
                DAGNode(node_id="A", handler="h_a"),
                DAGNode(node_id="B", depends_on=["A"], handler="h_b"),
                DAGNode(node_id="C", depends_on=["B"], handler="h_c"),
            ],
            entry_points=["A"],
            exit_points=["C"],
        )
        executor = DAGExecutor(wf, node_handler=compensating_handler)
        result = executor.execute(input_data={})

        assert result.node_results["C"].status == DAGExecutionState.FAILED
        # A và B đã hoàn thành -> được compensate -> skip
        assert result.node_results["A"].status == DAGExecutionState.SKIPPED
        assert result.node_results["B"].status == DAGExecutionState.SKIPPED

    def test_custom_node_handler_receives_correct_inputs(self):
        """Custom node_handler nhận đúng inputs."""
        received_contexts = []

        def tracking_handler(node, context):
            received_contexts.append({
                "node_id": node.node_id,
                "execution_id": context["execution_id"],
                "input_data": context["input_data"],
                "node_inputs": node.inputs,
            })
            return {"result": node.node_id}

        wf = DAGWorkflow(
            workflow_id="handler_test",
            name="Handler Test",
            nodes=[
                DAGNode(node_id="step1", inputs={"x": 10}),
                DAGNode(node_id="step2", depends_on=["step1"], inputs={"y": 20}),
            ],
            entry_points=["step1"],
            exit_points=["step2"],
        )
        executor = DAGExecutor(wf, node_handler=tracking_handler)
        executor.execute(input_data={"global_key": "global_val"})

        assert len(received_contexts) == 2
        # step1
        assert received_contexts[0]["node_id"] == "step1"
        assert received_contexts[0]["input_data"] == {"global_key": "global_val"}
        assert received_contexts[0]["node_inputs"] == {"x": 10}
        # step2
        assert received_contexts[1]["node_id"] == "step2"
        assert received_contexts[1]["node_inputs"] == {"y": 20}

    def test_execution_context_has_execution_id(self):
        """Execution context có execution_id hợp lệ."""
        wf = DAGWorkflow(
            workflow_id="ctx_test",
            name="Context Test",
            nodes=[DAGNode(node_id="only")],
            entry_points=["only"],
            exit_points=["only"],
        )
        executor = DAGExecutor(wf)
        result = executor.execute(input_data={})

        assert result.execution_id is not None
        assert len(result.execution_id) > 0

    def test_node_result_has_timestamps(self):
        """Node result có started_at và completed_at."""
        wf = DAGWorkflow(
            workflow_id="ts_test",
            name="Timestamp Test",
            nodes=[DAGNode(node_id="ts")],
            entry_points=["ts"],
            exit_points=["ts"],
        )
        executor = DAGExecutor(wf)
        result = executor.execute(input_data={})

        ts_result = result.node_results["ts"]
        assert ts_result.started_at is not None
        assert ts_result.completed_at is not None
        assert isinstance(ts_result.started_at, datetime)
        assert isinstance(ts_result.completed_at, datetime)

    def test_tenant_id_passed_to_context(self):
        """Tenant ID được truyền vào execution context."""
        wf = DAGWorkflow(
            workflow_id="tenant_test",
            name="Tenant Test",
            nodes=[DAGNode(node_id="t")],
            entry_points=["t"],
            exit_points=["t"],
        )
        executor = DAGExecutor(wf)
        result = executor.execute(input_data={}, tenant_id="tenant-123")

        assert result.tenant_id == "tenant-123"


# =============================================================================
# TestDAGExecutorExecutionPlan
# =============================================================================


class TestDAGExecutorExecutionPlan:
    """Test get_execution_plan của DAGExecutor."""

    def test_get_execution_plan_returns_groups(self):
        """get_execution_plan trả về danh sách các nhóm song song."""
        wf = DAGWorkflow(
            workflow_id="plan_test",
            name="Plan Test",
            nodes=[
                DAGNode(node_id="a"),
                DAGNode(node_id="b", depends_on=["a"]),
            ],
            entry_points=["a"],
            exit_points=["b"],
        )
        executor = DAGExecutor(wf)
        plan = executor.get_execution_plan()

        assert isinstance(plan, list)
        assert len(plan) == 2
        assert plan[0] == ["a"]
        assert plan[1] == ["b"]

    def test_linear_dag_each_group_one_node(self):
        """DAG tuyến tính: mỗi nhóm có 1 node."""
        wf = DAGWorkflow(
            workflow_id="linear_plan",
            name="Linear Plan",
            nodes=[
                DAGNode(node_id="1"),
                DAGNode(node_id="2", depends_on=["1"]),
                DAGNode(node_id="3", depends_on=["2"]),
            ],
            entry_points=["1"],
            exit_points=["3"],
        )
        executor = DAGExecutor(wf)
        plan = executor.get_execution_plan()

        assert len(plan) == 3
        assert plan[0] == ["1"]
        assert plan[1] == ["2"]
        assert plan[2] == ["3"]

    def test_parallel_dag_independent_nodes_same_group(self):
        """DAG song song: nodes độc lập trong cùng nhóm."""
        wf = DAGWorkflow(
            workflow_id="parallel_plan",
            name="Parallel Plan",
            nodes=[
                DAGNode(node_id="L1"),
                DAGNode(node_id="L2"),
                DAGNode(node_id="L3"),
                DAGNode(node_id="R1", depends_on=["L1", "L2", "L3"]),
            ],
            entry_points=["L1", "L2", "L3"],
            exit_points=["R1"],
        )
        executor = DAGExecutor(wf)
        plan = executor.get_execution_plan()

        assert len(plan) == 2
        # Level 0: L1, L2, L3 cùng nhóm
        assert set(plan[0]) == {"L1", "L2", "L3"}
        # Level 1: R1
        assert plan[1] == ["R1"]

    def test_diamond_dag_plan(self):
        """DAG kim cương: plan có 3 level."""
        wf = DAGWorkflow(
            workflow_id="diamond_plan",
            name="Diamond Plan",
            nodes=[
                DAGNode(node_id="A"),
                DAGNode(node_id="B", depends_on=["A"]),
                DAGNode(node_id="C", depends_on=["A"]),
                DAGNode(node_id="D", depends_on=["B", "C"]),
            ],
            entry_points=["A"],
            exit_points=["D"],
        )
        executor = DAGExecutor(wf)
        plan = executor.get_execution_plan()

        assert len(plan) == 3
        assert plan[0] == ["A"]
        assert set(plan[1]) == {"B", "C"}
        assert plan[2] == ["D"]

    def test_single_node_plan(self):
        """DAG một node: plan có 1 nhóm."""
        wf = DAGWorkflow(
            workflow_id="single_plan",
            name="Single Plan",
            nodes=[DAGNode(node_id="only")],
            entry_points=["only"],
            exit_points=["only"],
        )
        executor = DAGExecutor(wf)
        plan = executor.get_execution_plan()

        assert len(plan) == 1
        assert plan[0] == ["only"]


# =============================================================================
# TestDAGNodeResult
# =============================================================================


class TestDAGNodeResult:
    """Test DAGNodeResult dataclass."""

    def test_all_fields_exist(self):
        """Tất cả fields của DAGNodeResult tồn tại."""
        result = DAGNodeResult(
            node_id="test_node",
            status=DAGExecutionState.COMPLETED,
        )

        assert result.node_id == "test_node"
        assert result.status == DAGExecutionState.COMPLETED
        assert result.output == {}
        assert result.error == ""
        assert result.started_at is None
        assert result.completed_at is None
        assert result.retry_count == 0

    def test_create_with_all_fields(self):
        """Tạo DAGNodeResult với đầy đủ fields."""
        now = datetime.now()
        result = DAGNodeResult(
            node_id="full_node",
            status=DAGExecutionState.FAILED,
            output={"partial": True},
            error="Something went wrong",
            started_at=now,
            completed_at=now,
            retry_count=2,
        )

        assert result.node_id == "full_node"
        assert result.status == DAGExecutionState.FAILED
        assert result.output == {"partial": True}
        assert result.error == "Something went wrong"
        assert result.started_at == now
        assert result.completed_at == now
        assert result.retry_count == 2

    def test_status_enum_values(self):
        """Kiểm tra các giá trị enum của DAGExecutionState."""
        assert DAGExecutionState.PENDING.value == "pending"
        assert DAGExecutionState.RUNNING.value == "running"
        assert DAGExecutionState.COMPLETED.value == "completed"
        assert DAGExecutionState.FAILED.value == "failed"
        assert DAGExecutionState.SKIPPED.value == "skipped"
        assert DAGExecutionState.COMPENSATING.value == "compensating"

    def test_status_all_six_values_exist(self):
        """Có đủ 6 giá trị trạng thái."""
        values = [s.value for s in DAGExecutionState]
        assert len(values) == 6
        assert "pending" in values
        assert "running" in values
        assert "completed" in values
        assert "failed" in values
        assert "skipped" in values
        assert "compensating" in values


# =============================================================================
# TestDAGExecutionContext
# =============================================================================


class TestDAGExecutionContext:
    """Test DAGExecutionContext dataclass."""

    def test_create_context_minimal(self):
        """Tạo context với tối thiểu fields."""
        wf = DAGWorkflow(workflow_id="ctx_wf", name="Ctx")
        ctx = DAGExecutionContext(
            execution_id="exec-1",
            dag_workflow=wf,
        )

        assert ctx.execution_id == "exec-1"
        assert ctx.dag_workflow == wf
        assert ctx.node_results == {}
        assert ctx.input_data == {}
        assert ctx.tenant_id is None
        assert ctx.metadata == {}

    def test_create_context_full(self):
        """Tạo context với đầy đủ fields."""
        wf = DAGWorkflow(workflow_id="ctx_wf2", name="Ctx2")
        ctx = DAGExecutionContext(
            execution_id="exec-2",
            dag_workflow=wf,
            node_results={"n1": DAGNodeResult(node_id="n1", status=DAGExecutionState.COMPLETED)},
            input_data={"key": "val"},
            tenant_id="tenant-42",
            metadata={"run_by": "test"},
        )

        assert ctx.execution_id == "exec-2"
        assert len(ctx.node_results) == 1
        assert ctx.input_data == {"key": "val"}
        assert ctx.tenant_id == "tenant-42"
        assert ctx.metadata == {"run_by": "test"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
