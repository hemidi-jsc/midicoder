"""
Mô-đun DAG Executor Engine.

Cung cấp:
- DAGExecutor: Thực thi DAG workflow với topological sort, parallel execution, failure policies
- DAGExecutionState: Trạng thái execution của từng node
- DAGNodeResult: Kết quả execution của một node
- DAGExecutionContext: Context chứa toàn bộ trạng thái execution của DAG

Hỗ trợ các chế độ:
- SEQUENTIAL: Thực thi tuần tự theo topological order
- PARALLEL: Thực thi song song các node độc lập
- PARALLEL_WITH_FANIN: Parallel branches với merge nodes
- DYNAMIC: Dynamic node creation tại runtime

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

import asyncio
import uuid

from ..models import DAGWorkflow, DAGNode, DAGExecutionMode, DAGFailurePolicy
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class DAGExecutionState(str, Enum):
    """
    Trạng thái execution của một node trong DAG.

    Attributes:
        PENDING: Chưa thực thi
        RUNNING: Đang thực thi
        COMPLETED: Hoàn thành thành công
        FAILED: Thất bại
        SKIPPED: Bỏ qua (do failure policy)
        COMPENSATING: Đang chạy compensation
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATING = "compensating"


@dataclass
class DAGNodeResult:
    """
    Kết quả execution của một node.

    Attributes:
        node_id: ID của node
        status: Trạng thái execution
        output: Output data từ node
        error: Lỗi (nếu fail)
        started_at: Thời gian bắt đầu
        completed_at: Thời gian kết thúc
        retry_count: Số lần đã retry
    """
    node_id: str
    status: DAGExecutionState
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0


@dataclass
class DAGExecutionContext:
    """
    Context chứa toàn bộ trạng thái execution của DAG.

    Attributes:
        execution_id: ID duy nhất của lần execution
        dag_workflow: DAG workflow definition
        node_results: Kết quả của từng node (keyed by node_id)
        input_data: Input data truyền vào DAG
        tenant_id: Tenant ID (optional)
        metadata: Metadata bổ sung
    """
    execution_id: str
    dag_workflow: DAGWorkflow
    node_results: dict[str, DAGNodeResult] = field(default_factory=dict)
    input_data: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DAGExecutor:
    """
    DAG Executor — Thực thi DAG workflow với topological sort và parallel execution.

    Hỗ trợ:
    - Topological sort để xác định thứ tự execution
    - Parallel execution cho các node độc lập
    - Failure policies: fail_fast, skip_and_continue, retry_then_skip, compensate
    - Cycle detection

    Usage:
        executor = DAGExecutor(dag_workflow, node_handler=handler)
        executor.validate_dag()
        result = executor.execute(input_data={"key": "value"}, tenant_id="tenant-1")
    """

    def __init__(
        self,
        dag_workflow: DAGWorkflow,
        node_handler: Optional[Callable[[DAGNode, dict[str, Any]], dict[str, Any]]] = None,
    ):
        """
        Khởi tạo DAGExecutor.

        Args:
            dag_workflow: DAG workflow definition
            node_handler: Optional callable để execute node, nhận (node, context) -> output dict.
                         Nếu không cung cấp, mặc định trả về dict rỗng.
        """
        self.dag_workflow = dag_workflow
        self.node_handler = node_handler or self._default_node_handler

        # Build adjacency map cho quick lookup
        self._node_map: dict[str, DAGNode] = {n.node_id: n for n in dag_workflow.nodes}
        self._adjacency: dict[str, list[str]] = self._build_adjacency()

    def _default_node_handler(
        self, node: DAGNode, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Default node handler khi không có custom handler.

        Args:
            node: Node cần execute
            context: Execution context

        Returns:
            Output dict rỗng
        """
        return {}

    def _build_adjacency(self) -> dict[str, list[str]]:
        """
        Xây dựng adjacency list từ DAG nodes.

        Returns:
            Adjacency dict: node_id -> danh sách node IDs phụ thuộc vào node này
        """
        adj: dict[str, list[str]] = {n.node_id: [] for n in self.dag_workflow.nodes}
        for node in self.dag_workflow.nodes:
            for dep in node.depends_on:
                if dep in adj:
                    adj[dep].append(node.node_id)
        return adj

    def topological_sort(self) -> list[str]:
        """
        Sắp xếp topological các nodes trong DAG.

        Sử dụng Kahn's algorithm để sắp xếp. Nếu phát hiện cycle,
        sẽ raise lỗi CP13_WORKFLOW_STATE_MACHINE_ERROR.

        Returns:
            Danh sách node IDs theo topological order

        Raises:
            MidicoderError: Nếu DAG có cycle
        """
        # Tính in-degree cho mỗi node
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.dag_workflow.nodes}
        for node in self.dag_workflow.nodes:
            for dep in node.depends_on:
                if dep in in_degree:
                    in_degree[node.node_id] += 1

        # Bắt đầu từ các nodes có in-degree = 0
        queue: list[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        result: list[str] = []

        while queue:
            # Sắp xếp để có thứ tự deterministic
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Giảm in-degree của các node phụ thuộc
            for neighbor in self._adjacency.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Nếu số nodes trong kết quả ít hơn tổng số nodes -> có cycle
        if len(result) != len(self.dag_workflow.nodes):
            EM.raise_error(
                ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR,
                workflow_id=self.dag_workflow.workflow_id,
                reason="DAG contains a cycle, topological sort failed",
            )

        return result

    def validate_dag(self) -> None:
        """
        Validate DAG workflow definition.

        Checks:
        - Tất cả depends_on references tồn tại trong nodes
        - Không có cycle
        - Entry points không có dependencies
        - Exit points là leaf nodes (không node nào phụ thuộc vào chúng)

        Raises:
            MidicoderError: Nếu validation thất bại
        """
        node_ids = {n.node_id for n in self.dag_workflow.nodes}

        # Kiểm tra tất cả depends_on references tồn tại
        for node in self.dag_workflow.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    EM.raise_error(
                        ErrorCode.MDC-F20_JOB_NOT_FOUND,
                        node_id=node.node_id,
                        missing_dependency=dep,
                        reason=f"Node '{node.node_id}' depends on non-existent node '{dep}'",
                    )

        # Kiểm tra cycle
        if self._has_cycle():
            EM.raise_error(
                ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR,
                workflow_id=self.dag_workflow.workflow_id,
                reason="DAG contains a cycle",
            )

        # Kiểm tra entry points: không có dependencies
        for entry in self.dag_workflow.entry_points:
            if entry not in node_ids:
                EM.raise_error(
                    ErrorCode.MDC-F20_JOB_NOT_FOUND,
                    node_id=entry,
                    reason=f"Entry point '{entry}' not found in nodes",
                )
            node = self._node_map[entry]
            if node.depends_on:
                EM.raise_error(
                    ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR,
                    workflow_id=self.dag_workflow.workflow_id,
                    entry_point=entry,
                    reason=f"Entry point '{entry}' should have no dependencies",
                )

        # Kiểm tra exit points: là leaf nodes (không có node nào phụ thuộc)
        for exit_pt in self.dag_workflow.exit_points:
            if exit_pt not in node_ids:
                EM.raise_error(
                    ErrorCode.MDC-F20_JOB_NOT_FOUND,
                    node_id=exit_pt,
                    reason=f"Exit point '{exit_pt}' not found in nodes",
                )
            # Kiểm tra xem có node nào phụ thuộc vào exit point không
            for node in self.dag_workflow.nodes:
                if exit_pt in node.depends_on:
                    EM.raise_error(
                        ErrorCode.MDC-F20_WORKFLOW_STATE_MACHINE_ERROR,
                        workflow_id=self.dag_workflow.workflow_id,
                        exit_point=exit_pt,
                        reason=f"Exit point '{exit_pt}' is depended upon by '{node.node_id}', not a leaf",
                    )

    def _has_cycle(self) -> bool:
        """
        Phát hiện cycle trong DAG sử dụng DFS.

        Returns:
            True nếu có cycle, False nếu không
        """
        VISITING = "visiting"
        VISITED = "visited"
        state: dict[str, str] = {n.node_id: "" for n in self.dag_workflow.nodes}

        def dfs(node_id: str) -> bool:
            """DFS helper để phát hiện cycle."""
            if state[node_id] == VISITING:
                return True  # Cycle detected
            if state[node_id] == VISITED:
                return False

            state[node_id] = VISITING

            node = self._node_map.get(node_id)
            if node:
                for dep in node.depends_on:
                    if dep in state and dfs(dep):
                        return True

            state[node_id] = VISITED
            return False

        for node_id in state:
            if not state[node_id]:
                if dfs(node_id):
                    return True

        return False

    def get_execution_plan(self) -> list[list[str]]:
        """
        Tạo execution plan — danh sách các nhóm nodes có thể chạy song song.

        Mỗi nhóm chứa các nodes độc lập (không phụ thuộc lẫn nhau)
        và chỉ phụ thuộc vào các nhóm trước đó.

        Returns:
            Danh sách các nhóm nodes. Mỗi nhóm là list của node IDs
            có thể thực thi song song.
        """
        # Tính in-degree
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.dag_workflow.nodes}
        for node in self.dag_workflow.nodes:
            for dep in node.depends_on:
                if dep in in_degree:
                    in_degree[node.node_id] += 1

        # Group nodes theo level (nodes có cùng in-degree=0 sau khi remove previous level)
        plan: list[list[str]] = []
        remaining: dict[str, int] = dict(in_degree)

        while remaining:
            # Tìm tất cả nodes có in-degree = 0
            current_level = [nid for nid, deg in remaining.items() if deg == 0]
            if not current_level:
                # Không còn node nào có in-degree 0 -> có cycle (đã validate trước đó)
                break

            current_level.sort()  # Deterministic order
            plan.append(current_level)

            # Remove các nodes trong level này và cập nhật in-degree
            for nid in current_level:
                del remaining[nid]
                for neighbor in self._adjacency.get(nid, []):
                    if neighbor in remaining:
                        remaining[neighbor] -= 1

        return plan

    def execute(
        self,
        input_data: dict[str, Any],
        tenant_id: str | None = None,
    ) -> DAGExecutionContext:
        """
        Thực thi toàn bộ DAG workflow.

        Execute các nodes theo execution_mode của workflow:
        - SEQUENTIAL: tuần tự theo topological order
        - PARALLEL: song song các nodes độc lập
        - PARALLEL_WITH_FANIN: parallel branches với fan-in
        - DYNAMIC: sequential với dynamic node support

        Args:
            input_data: Input data truyền vào DAG
            tenant_id: Tenant ID (optional)

        Returns:
            DAGExecutionContext chứa kết quả của tất cả nodes

        Raises:
            MidicoderError: Nếu DAG không hợp lệ
        """
        # Validate DAG trước khi execute
        self.validate_dag()

        execution_id = str(uuid.uuid4())
        context = DAGExecutionContext(
            execution_id=execution_id,
            dag_workflow=self.dag_workflow,
            input_data=input_data,
            tenant_id=tenant_id,
        )

        # Khởi tạo node results với trạng thái PENDING
        for node in self.dag_workflow.nodes:
            context.node_results[node.node_id] = DAGNodeResult(
                node_id=node.node_id,
                status=DAGExecutionState.PENDING,
            )

        # Execute theo mode
        mode = self.dag_workflow.execution_mode

        if mode == DAGExecutionMode.SEQUENTIAL:
            self._execute_sequential(context)
        elif mode == DAGExecutionMode.PARALLEL:
            self._execute_parallel(context)
        elif mode == DAGExecutionMode.PARALLEL_WITH_FANIN:
            self._execute_parallel_with_fanin(context)
        elif mode == DAGExecutionMode.DYNAMIC:
            self._execute_dynamic(context)
        else:
            EM.raise_error(
                ErrorCode.MDC-F20_WORKFLOW_INVALID_TRANSITION,
                workflow_id=self.dag_workflow.workflow_id,
                execution_mode=mode.value,
                reason=f"Unknown execution mode: {mode.value}",
            )

        return context

    def _execute_sequential(self, context: DAGExecutionContext) -> None:
        """
        Thực thi DAG theo thứ tự tuần tự (topological order).

        Args:
            context: Execution context
        """
        order = self.topological_sort()

        for node_id in order:
            # Kiểm tra xem node có nên bị skip không (do dependency fail)
            node = self._node_map[node_id]

            # Kiểm tra dependencies đã hoàn thành chưa
            should_skip = False
            for dep_id in node.depends_on:
                dep_result = context.node_results.get(dep_id)
                if dep_result and dep_result.status in (
                    DAGExecutionState.FAILED,
                    DAGExecutionState.SKIPPED,
                ):
                    should_skip = True
                    break

            if should_skip:
                context.node_results[node_id] = DAGNodeResult(
                    node_id=node_id,
                    status=DAGExecutionState.SKIPPED,
                    error="Skipped due to failed dependency",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                continue

            result = self._execute_node(node_id, context)
            context.node_results[node_id] = result

            # Xử lý failure theo policy
            if result.status == DAGExecutionState.FAILED:
                self._handle_failure(result, context)

    def _execute_parallel(self, context: DAGExecutionContext) -> None:
        """
        Thực thi DAG song song — các nodes độc lập chạy cùng lúc.

        Sử dụng asyncio.gather để chạy các nodes trong cùng một level.

        Args:
            context: Execution context
        """
        plan = self.get_execution_plan()

        for level in plan:
            # Kiểm tra xem có node nào trong level nên bị skip
            active_nodes = []
            for node_id in level:
                node = self._node_map[node_id]
                should_skip = False
                for dep_id in node.depends_on:
                    dep_result = context.node_results.get(dep_id)
                    if dep_result and dep_result.status in (
                        DAGExecutionState.FAILED,
                        DAGExecutionState.SKIPPED,
                    ):
                        should_skip = True
                        break

                if should_skip:
                    context.node_results[node_id] = DAGNodeResult(
                        node_id=node_id,
                        status=DAGExecutionState.SKIPPED,
                        error="Skipped due to failed dependency",
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )
                else:
                    active_nodes.append(node_id)

            if not active_nodes:
                continue

            # Chạy song song các nodes trong level
            try:
                loop = asyncio.get_running_loop()
                tasks = [
                    self._execute_node_async(node_id, context)
                    for node_id in active_nodes
                ]
                results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            except RuntimeError:
                # Không có event loop, chạy sync
                results = [
                    self._execute_node(node_id, context)
                    for node_id in active_nodes
                ]

            # Xử lý kết quả
            for i, node_id in enumerate(active_nodes):
                result = results[i]
                if isinstance(result, Exception):
                    error_msg = str(result)
                    context.node_results[node_id] = DAGNodeResult(
                        node_id=node_id,
                        status=DAGExecutionState.FAILED,
                        error=error_msg,
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )
                    self._handle_failure(context.node_results[node_id], context)
                elif isinstance(result, DAGNodeResult):
                    context.node_results[node_id] = result
                    if result.status == DAGExecutionState.FAILED:
                        self._handle_failure(result, context)

    def _execute_parallel_with_fanin(self, context: DAGExecutionContext) -> None:
        """
        Thực thi DAG với parallel branches và fan-in tại merge nodes.

        Các branches độc lập chạy song song, sau đó merge tại các nodes
        có nhiều incoming dependencies.

        Args:
            context: Execution context
        """
        plan = self.get_execution_plan()

        for level in plan:
            active_nodes = []
            for node_id in level:
                node = self._node_map[node_id]
                should_skip = False
                for dep_id in node.depends_on:
                    dep_result = context.node_results.get(dep_id)
                    if dep_result and dep_result.status in (
                        DAGExecutionState.FAILED,
                        DAGExecutionState.SKIPPED,
                    ):
                        should_skip = True
                        break

                if should_skip:
                    context.node_results[node_id] = DAGNodeResult(
                        node_id=node_id,
                        status=DAGExecutionState.SKIPPED,
                        error="Skipped due to failed dependency",
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )
                else:
                    active_nodes.append(node_id)

            if not active_nodes:
                continue

            # Gather input từ tất cả upstream nodes cho fan-in
            for node_id in active_nodes:
                node = self._node_map[node_id]

                # Nếu node có nhiều dependencies, đây là fan-in node
                if len(node.depends_on) > 1:
                    merged_input: dict[str, Any] = {}
                    for dep_id in node.depends_on:
                        dep_result = context.node_results.get(dep_id)
                        if dep_result and dep_result.status == DAGExecutionState.COMPLETED:
                            merged_input[dep_id] = dep_result.output
                    # Thêm merged input vào node inputs
                    node.inputs["_fanin_inputs"] = merged_input

            # Chạy song song
            try:
                loop = asyncio.get_running_loop()
                tasks = [
                    self._execute_node_async(node_id, context)
                    for node_id in active_nodes
                ]
                results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            except RuntimeError:
                results = [
                    self._execute_node(node_id, context)
                    for node_id in active_nodes
                ]

            for i, node_id in enumerate(active_nodes):
                result = results[i]
                if isinstance(result, Exception):
                    error_msg = str(result)
                    context.node_results[node_id] = DAGNodeResult(
                        node_id=node_id,
                        status=DAGExecutionState.FAILED,
                        error=error_msg,
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )
                    self._handle_failure(context.node_results[node_id], context)
                elif isinstance(result, DAGNodeResult):
                    context.node_results[node_id] = result
                    if result.status == DAGExecutionState.FAILED:
                        self._handle_failure(result, context)

    def _execute_dynamic(self, context: DAGExecutionContext) -> None:
        """
        Thực thi DAG với dynamic node creation support.

        Tương tự sequential, nhưng sau mỗi node có thể tạo thêm nodes
        dựa trên output của node trước đó.

        Args:
            context: Execution context
        """
        order = self.topological_sort()

        for node_id in order:
            node = self._node_map.get(node_id)
            if not node:
                # Node được tạo dynamic, skip nếu không có trong map
                continue

            # Kiểm tra dependencies
            should_skip = False
            for dep_id in node.depends_on:
                dep_result = context.node_results.get(dep_id)
                if dep_result and dep_result.status in (
                    DAGExecutionState.FAILED,
                    DAGExecutionState.SKIPPED,
                ):
                    should_skip = True
                    break

            if should_skip:
                context.node_results[node_id] = DAGNodeResult(
                    node_id=node_id,
                    status=DAGExecutionState.SKIPPED,
                    error="Skipped due to failed dependency",
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                continue

            result = self._execute_node(node_id, context)
            context.node_results[node_id] = result

            # Xử lý failure theo policy
            if result.status == DAGExecutionState.FAILED:
                self._handle_failure(result, context)

    def _execute_node(
        self, node_id: str, context: DAGExecutionContext
    ) -> DAGNodeResult:
        """
        Thực thi một node duy nhất.

        Args:
            node_id: ID của node cần thực thi
            context: Execution context

        Returns:
            DAGNodeResult chứa kết quả execution
        """
        node = self._node_map.get(node_id)
        if not node:
            EM.raise_error(
                ErrorCode.MDC-F20_JOB_NOT_FOUND,
                node_id=node_id,
                reason=f"Node '{node_id}' not found in workflow",
            )

        started_at = datetime.now(timezone.utc)

        # Đánh dấu node đang chạy
        result = DAGNodeResult(
            node_id=node_id,
            status=DAGExecutionState.RUNNING,
            started_at=started_at,
        )

        # Build context cho node handler
        node_context: dict[str, Any] = {
            "execution_id": context.execution_id,
            "input_data": context.input_data,
            "tenant_id": context.tenant_id,
            "metadata": context.metadata,
            "node_inputs": node.inputs,
            "sibling_outputs": {},
        }

        # Gather output từ các node đã hoàn thành (dependencies)
        for dep_id in node.depends_on:
            dep_result = context.node_results.get(dep_id)
            if dep_result and dep_result.status == DAGExecutionState.COMPLETED:
                node_context["sibling_outputs"][dep_id] = dep_result.output

        try:
            output = self.node_handler(node, node_context)
            result.status = DAGExecutionState.COMPLETED
            result.output = output if isinstance(output, dict) else {}
        except Exception as e:
            result.status = DAGExecutionState.FAILED
            result.error = str(e)
        finally:
            result.completed_at = datetime.now(timezone.utc)

        return result

    async def _execute_node_async(
        self, node_id: str, context: DAGExecutionContext
    ) -> DAGNodeResult:
        """
        Thực thi một node duy nhất (async version).

        Args:
            node_id: ID của node cần thực thi
            context: Execution context

        Returns:
            DAGNodeResult chứa kết quả execution
        """
        # Fallback đến sync execution nếu handler không phải async
        return self._execute_node(node_id, context)

    def _handle_failure(
        self, node_result: DAGNodeResult, context: DAGExecutionContext
    ) -> None:
        """
        Xử lý failure theo failure_policy của workflow.

        Policies:
        - FAIL_FAST: Dừng execution, đánh dấu các node còn lại là SKIPPED
        - SKIP_AND_CONTINUE: Bỏ qua node fail, tiếp tục nodes khác
        - RETRY_THEN_SKIP: Retry một lần, sau đó skip nếu vẫn fail
        - COMPENSATE: Chạy compensation cho các nodes đã hoàn thành

        Args:
            node_result: Kết quả của node đã fail
            context: Execution context
        """
        policy = self.dag_workflow.failure_policy

        if policy == DAGFailurePolicy.FAIL_FAST:
            # Đánh dấu tất cả nodes chưa execute là SKIPPED
            for nid, r in context.node_results.items():
                if r.status == DAGExecutionState.PENDING:
                    context.node_results[nid] = DAGNodeResult(
                        node_id=nid,
                        status=DAGExecutionState.SKIPPED,
                        error=f"Skipped due to FAIL_FAST policy (node '{node_result.node_id}' failed)",
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )

        elif policy == DAGFailurePolicy.SKIP_AND_CONTINUE:
            # Đổi status từ FAILED sang SKIPPED để nodes downstream biết
            node_result.status = DAGExecutionState.SKIPPED

        elif policy == DAGFailurePolicy.RETRY_THEN_SKIP:
            if node_result.retry_count < 1:
                # Retry một lần
                node_result.retry_count += 1
                node = self._node_map.get(node_result.node_id)
                if node:
                    retry_result = self._execute_node(node_result.node_id, context)
                    if retry_result.status == DAGExecutionState.COMPLETED:
                        context.node_results[node_result.node_id] = retry_result
                        return
                    else:
                        # Vẫn fail sau retry -> skip
                        retry_result.status = DAGExecutionState.SKIPPED
                        retry_result.error = f"Skipped after retry: {retry_result.error}"
                        context.node_results[node_result.node_id] = retry_result
            else:
                node_result.status = DAGExecutionState.SKIPPED

        elif policy == DAGFailurePolicy.COMPENSATE:
            # Chạy compensation cho các nodes đã hoàn thành (reverse order)
            completed_nodes = [
                nid for nid, r in context.node_results.items()
                if r.status == DAGExecutionState.COMPLETED
            ]

            # Compensate theo thứ tự ngược
            for nid in reversed(completed_nodes):
                context.node_results[nid].status = DAGExecutionState.COMPENSATING
                node = self._node_map.get(nid)
                if node and node.handler:
                    # Attempt compensation (best-effort)
                    try:
                        comp_context: dict[str, Any] = {
                            "execution_id": context.execution_id,
                            "compensating": True,
                            "original_output": context.node_results[nid].output,
                            "failure_node": node_result.node_id,
                            "failure_error": node_result.error,
                        }
                        self.node_handler(node, comp_context)
                    except Exception:
                        # Compensation là best-effort, không throw
                        pass
                context.node_results[nid].status = DAGExecutionState.SKIPPED

        else:
            EM.raise_error(
                ErrorCode.MDC-F20_WORKFLOW_INVALID_TRANSITION,
                workflow_id=self.dag_workflow.workflow_id,
                failure_policy=policy.value,
                reason=f"Unknown failure policy: {policy.value}",
            )
