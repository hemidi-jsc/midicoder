"""
Mô-đun Saga Orchestrator Engine.

Cung cấp:
- SagaOrchestrator: Engine thực thi saga với action/compensation pairs
- SagaStepStatus: Trạng thái của từng step trong saga
- SagaStepResult: Kết quả thực thi của một step
- SagaExecutionState: Trạng thái tổng thể của saga execution

Hỗ trợ ba chiến lược compensation:
- Backward: Undo từ step bị fail trở về đầu (reverse order)
- Forward: Bỏ qua step fail, tiếp tục các step còn lại
- Mixed: Compensate các step compensatable, skip các step idempotent

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from ..models import SagaDefinition, SagaStep, SagaCompensationStrategy
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class SagaStepStatus(str, Enum):
    """
    Trạng thái của từng step trong saga.

    Attributes:
        PENDING: Chưa thực thi
        EXECUTING: Đang thực thi action
        COMPLETED: Action thành công
        FAILED: Action thất bại
        COMPENSATING: Đang thực thi compensation
        COMPENSATED: Compensation hoàn tất
        SKIPPED: Bỏ qua step (idempotent hoặc forward recovery)
    """
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    SKIPPED = "skipped"


@dataclass
class SagaStepResult:
    """
    Kết quả thực thi của một saga step.

    Lưu trữ trạng thái và output của cả action và compensation.

    Attributes:
        step_id: ID của step
        action_status: Trạng thái action execution
        compensation_status: Trạng thái compensation execution
        action_output: Output từ action
        action_error: Lỗi từ action (nếu có)
        compensation_output: Output từ compensation
        compensation_error: Lỗi từ compensation (nếu có)
        started_at: Thời điểm bắt đầu step
        completed_at: Thời điểm hoàn tất step
    """
    step_id: str
    action_status: SagaStepStatus = SagaStepStatus.PENDING
    compensation_status: SagaStepStatus = SagaStepStatus.PENDING
    action_output: dict[str, Any] = field(default_factory=dict)
    action_error: str | None = None
    compensation_output: dict[str, Any] = field(default_factory=dict)
    compensation_error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class SagaExecutionState:
    """
    Trạng thái tổng thể của saga execution.

    Theo dõi tiến độ và kết quả của toàn bộ saga.

    Attributes:
        execution_id: ID duy nhất của lần thực thi
        saga: Saga definition
        step_results: Kết quả của từng step
        status: Trạng thái tổng thể (COMPLETED/FAILED/COMPENSATING/COMPENSATED)
        started_at: Thời điểm bắt đầu saga
        completed_at: Thời điểm hoàn tất saga
        error: Lỗi tổng thể (nếu có)
        input_data: Dữ liệu đầu vào
        tenant_id: Tenant ID (optional)
    """
    execution_id: str
    saga: SagaDefinition
    step_results: list[SagaStepResult] = field(default_factory=list)
    status: str = "PENDING"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None


class SagaOrchestrator:
    """
    Saga Orchestrator Engine cho workflow execution.

    Thực thi saga với các bước action/compensation theo thứ tự tuần tự.
    Khi một step thất bại, orchestrator kích hoạt compensation dựa trên
    chiến lược đã định nghĩa (backward, forward, hoặc mixed).

    Hỗ trợ:
    - Sync execution
    - Async execution (qua asyncio)
    - Custom step handler và compensation handler
    - Saga log cho audit/debug

    Usage:
        orchestrator = SagaOrchestrator(saga_definition)
        state = orchestrator.execute(input_data, tenant_id="tenant-1")
    """

    def __init__(
        self,
        saga_definition: SagaDefinition,
        step_handler: Callable[[SagaStep, dict[str, Any]], dict[str, Any]] | None = None,
        compensation_handler: Callable[[SagaStep, dict[str, Any]], dict[str, Any]] | None = None,
    ):
        """
        Khởi tạo SagaOrchestrator.

        Args:
            saga_definition: Định nghĩa saga cần thực thi
            step_handler: Handler tùy chỉnh để execute action (optional)
            compensation_handler: Handler tùy chỉnh để execute compensation (optional)
        """
        self.saga_definition = saga_definition
        self.step_handler = step_handler
        self.compensation_handler = compensation_handler
        self._execution_state: SagaExecutionState | None = None
        self._saga_log: list[dict[str, Any]] = []

    def validate_saga(self) -> None:
        """
        Validate saga definition hợp lệ.

        Checks:
        - Steps không rỗng
        - Mỗi step phải có action
        - Các step compensatable phải có compensation handler

        Raises:
            MidicoderError: Nếu saga không hợp lệ
        """
        if not self.saga_definition.steps:
            EM.raise_error(
                ErrorCode.CP13_WORKFLOW_STATE_MACHINE_ERROR,
                saga_id=self.saga_definition.saga_id,
                saga_name=self.saga_definition.name,
                reason="Saga must have at least one step",
            )

        for step in self.saga_definition.steps:
            # Kiểm tra mỗi step phải có action
            if not step.action:
                EM.raise_error(
                    ErrorCode.CP13_WORKFLOW_INVALID_TRANSITION,
                    saga_id=self.saga_definition.saga_id,
                    step_id=step.step_id,
                    reason="Saga step must have an action",
                )

            # Kiểm tra step compensatable phải có compensation
            if step.is_compensatable and not step.compensation:
                EM.raise_error(
                    ErrorCode.CP13_WORKFLOW_INVALID_TRANSITION,
                    saga_id=self.saga_definition.saga_id,
                    step_id=step.step_id,
                    reason="Compensatable step must have a compensation action",
                )

    def execute(self, input_data: dict[str, Any], tenant_id: str | None = None) -> SagaExecutionState:
        """
        Thực thi saga từ đầu đến cuối.

        Thực hiện các bước action tuần tự. Nếu một step thất bại,
        kích hoạt compensation dựa trên chiến lược đã định nghĩa.

        Args:
            input_data: Dữ liệu đầu vào cho saga
            tenant_id: Tenant ID (optional)

        Returns:
            SagaExecutionState chứa kết quả thực thi

        Raises:
            MidicoderError: Nếu saga definition không hợp lệ
        """
        # Validate saga trước khi thực thi
        self.validate_saga()

        # Tạo execution state mới
        execution_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        self._execution_state = SagaExecutionState(
            execution_id=execution_id,
            saga=self.saga_definition,
            status="PENDING",
            started_at=now,
            input_data=input_data,
            tenant_id=tenant_id,
        )

        # Init step results
        for step in self.saga_definition.steps:
            self._execution_state.step_results.append(
                SagaStepResult(step_id=step.step_id)
            )

        self._log_event("saga_started", {
            "execution_id": execution_id,
            "saga_id": self.saga_definition.saga_id,
            "saga_name": self.saga_definition.name,
            "strategy": self.saga_definition.compensation_strategy.value,
        })

        failed_step_index: int | None = None

        # Thực thi từng step tuần tự
        for index, step in enumerate(self.saga_definition.steps):
            result = self._execution_state.step_results[index]

            try:
                result = self._execute_step(step, input_data)
                self._execution_state.step_results[index] = result

                if result.action_status == SagaStepStatus.FAILED:
                    failed_step_index = index
                    self._execution_state.status = "FAILED"
                    self._execution_state.error = result.action_error
                    break
                elif result.action_status == SagaStepStatus.COMPLETED:
                    self._execution_state.status = "COMPLETED"

            except Exception as e:
                # Xử lý exception không mong đợi
                result.action_status = SagaStepStatus.FAILED
                result.action_error = str(e)
                result.completed_at = datetime.now(timezone.utc)
                self._execution_state.step_results[index] = result

                failed_step_index = index
                self._execution_state.status = "FAILED"
                self._execution_state.error = str(e)
                break

        # Nếu có step fail, kích hoạt compensation
        if failed_step_index is not None:
            self._execution_state.status = "COMPENSATING"

            try:
                strategy = self.saga_definition.compensation_strategy

                if strategy == SagaCompensationStrategy.BACKWARD:
                    self._backward_compensate(self._execution_state, failed_step_index)
                elif strategy == SagaCompensationStrategy.FORWARD:
                    self._forward_recovery(self._execution_state, failed_step_index)
                elif strategy == SagaCompensationStrategy.MIXED:
                    self._mixed_compensate(self._execution_state, failed_step_index)

                # Kiểm tra xem compensation có thành công hoàn toàn không
                if self._all_compensated():
                    self._execution_state.status = "COMPENSATED"
                else:
                    self._execution_state.status = "FAILED"

            except Exception as e:
                self._execution_state.status = "FAILED"
                self._execution_state.error = f"Compensation failed: {str(e)}"
                EM.raise_error(
                    ErrorCode.CP01_WORKFLOW_COMPENSATION_FAILED,
                    saga_id=self.saga_definition.saga_id,
                    execution_id=execution_id,
                    strategy=self.saga_definition.compensation_strategy.value,
                    failed_step_index=failed_step_index,
                    reason=f"Compensation execution failed: {str(e)}",
                )

        # Đánh dấu hoàn tất
        self._execution_state.completed_at = datetime.now(timezone.utc)

        self._log_event("saga_completed", {
            "execution_id": execution_id,
            "final_status": self._execution_state.status,
            "error": self._execution_state.error,
        })

        return self._execution_state

    def _execute_step(self, step: SagaStep, input_data: dict[str, Any]) -> SagaStepResult:
        """
        Thực thi action của một step.

        Args:
            step: Saga step cần thực thi
            input_data: Dữ liệu đầu vào

        Returns:
            SagaStepResult chứa kết quả thực thi
        """
        now = datetime.now(timezone.utc)
        result = SagaStepResult(
            step_id=step.step_id,
            action_status=SagaStepStatus.EXECUTING,
            started_at=now,
        )

        self._log_event("step_started", {
            "step_id": step.step_id,
            "action": step.action,
        })

        # Build context cho step
        context = {
            "step_id": step.step_id,
            "action": step.action,
            "inputs": step.inputs,
            "saga_input": input_data,
            "timeout_seconds": step.timeout_seconds,
        }

        try:
            # Sử dụng custom handler nếu có
            if self.step_handler:
                output = self.step_handler(step, context)
            else:
                # Default handler: log action và trả về thành công
                output = {"action": step.action, "status": "executed"}

            result.action_status = SagaStepStatus.COMPLETED
            result.action_output = output if isinstance(output, dict) else {"result": output}
            result.completed_at = datetime.now(timezone.utc)

            self._log_event("step_completed", {
                "step_id": step.step_id,
                "output": result.action_output,
            })

        except Exception as e:
            result.action_status = SagaStepStatus.FAILED
            result.action_error = str(e)
            result.completed_at = datetime.now(timezone.utc)

            self._log_event("step_failed", {
                "step_id": step.step_id,
                "error": str(e),
            })

        return result

    def _compensate_step(self, step: SagaStep, context: dict[str, Any]) -> SagaStepResult:
        """
        Thực thi compensation của một step.

        Args:
            step: Saga step cần compensate
            context: Context chứa thông tin compensation

        Returns:
            SagaStepResult với compensation status được cập nhật

        Raises:
            MidicoderError: Nếu compensation thất bại
        """
        now = datetime.now(timezone.utc)
        result = SagaStepResult(
            step_id=step.step_id,
            action_status=SagaStepStatus.COMPLETED,  # Action đã chạy trước đó
            compensation_status=SagaStepStatus.COMPENSATING,
            started_at=now,
        )

        self._log_event("compensation_started", {
            "step_id": step.step_id,
            "compensation": step.compensation,
        })

        # Build context cho compensation
        comp_context = {
            "step_id": step.step_id,
            "compensation": step.compensation,
            "inputs": step.inputs,
            "original_context": context,
            "timeout_seconds": step.timeout_seconds,
        }

        try:
            # Sử dụng custom compensation handler nếu có
            if self.compensation_handler:
                output = self.compensation_handler(step, comp_context)
            else:
                # Default handler: log compensation và trả về thành công
                output = {"compensation": step.compensation, "status": "compensated"}

            result.compensation_status = SagaStepStatus.COMPENSATED
            result.compensation_output = output if isinstance(output, dict) else {"result": output}
            result.completed_at = datetime.now(timezone.utc)

            self._log_event("compensation_completed", {
                "step_id": step.step_id,
                "output": result.compensation_output,
            })

        except Exception as e:
            result.compensation_status = SagaStepStatus.FAILED
            result.compensation_error = str(e)
            result.completed_at = datetime.now(timezone.utc)

            self._log_event("compensation_failed", {
                "step_id": step.step_id,
                "error": str(e),
            })

            EM.raise_error(
                ErrorCode.CP01_WORKFLOW_COMPENSATION_FAILED,
                saga_id=self.saga_definition.saga_id,
                step_id=step.step_id,
                compensation=step.compensation,
                reason=f"Compensation for step '{step.step_id}' failed: {str(e)}",
            )

        return result

    def _backward_compensate(self, saga_state: SagaExecutionState, failed_step_index: int) -> None:
        """
        Backward compensation - undo từ step bị fail về đầu.

        Duyệt ngược từ step trước step fail, execute compensation
        cho từng step đã hoàn thành.

        Args:
            saga_state: Execution state hiện tại
            failed_step_index: Index của step bị fail
        """
        # Duyệt ngược từ step trước step fail về 0
        for i in range(failed_step_index - 1, -1, -1):
            step = saga_state.saga.steps[i]
            result = saga_state.step_results[i]

            # Chỉ compensate các step đã completed
            if result.action_status == SagaStepStatus.COMPLETED:
                comp_context = {
                    "saga_state": saga_state,
                    "step_index": i,
                    "strategy": "backward",
                }

                comp_result = self._compensate_step(step, comp_context)
                # Cập nhật compensation status vào result
                saga_state.step_results[i].compensation_status = comp_result.compensation_status
                saga_state.step_results[i].compensation_output = comp_result.compensation_output
                saga_state.step_results[i].compensation_error = comp_result.compensation_error

    def _forward_recovery(self, saga_state: SagaExecutionState, failed_step_index: int) -> None:
        """
        Forward recovery - tiếp tục từ step sau step fail.

        Đánh dấu step fail là SKIPPED, cố gắng tiếp tục thực thi
        các step còn lại. Không execute compensation cho các step đã completed.

        Args:
            saga_state: Execution state hiện tại
            failed_step_index: Index của step bị fail
        """
        # Đánh dấu step fail là skipped
        saga_state.step_results[failed_step_index].action_status = SagaStepStatus.SKIPPED

        # Tiếp tục thực thi các step còn lại
        context = dict(saga_state.input_data)

        for i in range(failed_step_index + 1, len(saga_state.saga.steps)):
            step = saga_state.saga.steps[i]
            result = saga_state.step_results[i]

            try:
                result = self._execute_step(step, context)
                saga_state.step_results[i] = result

                if result.action_status == SagaStepStatus.FAILED:
                    # Forward recovery không retry - đánh dấu skipped và tiếp tục
                    saga_state.step_results[i].action_status = SagaStepStatus.SKIPPED
                    self._log_event("step_skipped_forward", {
                        "step_id": step.step_id,
                        "reason": "forward_recovery_skip",
                        "error": result.action_error,
                    })

            except Exception as e:
                saga_state.step_results[i].action_status = SagaStepStatus.SKIPPED
                self._log_event("step_skipped_forward", {
                    "step_id": step.step_id,
                    "reason": f"forward_recovery_error: {str(e)}",
                })

    def _mixed_compensate(self, saga_state: SagaExecutionState, failed_step_index: int) -> None:
        """
        Mixed compensation - kết hợp backward và forward.

        Compensate các step compensatable, skip các step idempotent
        (is_compensatable=False).

        Args:
            saga_state: Execution state hiện tại
            failed_step_index: Index của step bị fail
        """
        # Duyệt ngược từ step trước step fail
        for i in range(failed_step_index - 1, -1, -1):
            step = saga_state.saga.steps[i]
            result = saga_state.step_results[i]

            # Chỉ xử lý các step đã completed
            if result.action_status != SagaStepStatus.COMPLETED:
                continue

            if step.is_compensatable:
                # Execute compensation cho step compensatable
                comp_context = {
                    "saga_state": saga_state,
                    "step_index": i,
                    "strategy": "mixed",
                }

                comp_result = self._compensate_step(step, comp_context)
                saga_state.step_results[i].compensation_status = comp_result.compensation_status
                saga_state.step_results[i].compensation_output = comp_result.compensation_output
                saga_state.step_results[i].compensation_error = comp_result.compensation_error
            else:
                # Skip step idempotent
                result.compensation_status = SagaStepStatus.SKIPPED
                self._log_event("step_skipped_idempotent", {
                    "step_id": step.step_id,
                    "reason": "idempotent_operation",
                })

    def _all_compensated(self) -> bool:
        """
        Kiểm tra tất cả steps cần compensate đã hoàn tất.

        Returns:
            True nếu tất cả steps đã completed hoặc compensated
        """
        if not self._execution_state:
            return False

        for result in self._execution_state.step_results:
            if result.action_status == SagaStepStatus.FAILED:
                continue  # Step fail không cần compensate
            if result.action_status == SagaStepStatus.COMPLETED:
                # Step completed: không cần compensation hoặc đã compensated
                if result.compensation_status == SagaStepStatus.COMPENSATING:
                    return False
                # COMPLETED, COMPENSATED, SKIPPED, PENDING đều OK

        return True

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Ghi event vào saga log.

        Args:
            event_type: Loại event
            data: Dữ liệu event
        """
        if self.saga_definition.enable_saga_log:
            self._saga_log.append({
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data,
            })

    def get_saga_log(self) -> list[dict[str, Any]]:
        """
        Lấy saga log cho audit/debug.

        Returns:
            Danh sách events trong saga log
        """
        return list(self._saga_log)
