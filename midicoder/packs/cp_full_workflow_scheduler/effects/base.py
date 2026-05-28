"""
Mô-đun Base Effect Executor.

Cung cấp:
- EffectExecutor: Abstract base class cho effect execution
- EffectResult: Kết quả của effect execution

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from ..models import Effect, EffectType
from ..engine.state_machine import TransitionContext


@dataclass
class EffectResult:
    """
    Kết quả của effect execution.

    Attributes:
        success: Có thành công không
        effect_type: Loại effect
        message: Message (nếu có)
        error: Error (nếu fail)
        data: Additional data
    """
    success: bool
    effect_type: str | None = None
    message: str | None = None
    error: str | None = None
    data: dict[str, Any] | None = None

    @staticmethod
    def success(data: dict | None = None, message: str | None = None) -> "EffectResult":
        """Tạo successful EffectResult."""
        return EffectResult(success=True, message=message, data=data)

    @staticmethod
    def failure(error: str) -> "EffectResult":
        """Tạo failed EffectResult."""
        return EffectResult(success=False, error=error)


class EffectExecutor(ABC):
    """
    Abstract base class cho effect execution.

    Tất cả effect executors phải implement method execute().

    Usage:
        class MyEffect(EffectExecutor):
            async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
                return EffectResult.success(data={"ok": True})
    """

    @abstractmethod
    async def execute(
        self,
        effect: Effect,
        context: TransitionContext,
    ) -> EffectResult:
        """
        Execute effect và return kết quả.

        Args:
            effect: Effect definition
            context: Transition context

        Returns:
            EffectResult với success/failure info
        """
        pass

    @classmethod
    def create_executor(cls, effect_type: EffectType) -> "EffectExecutor":
        """
        Factory method để tạo executor phù hợp với effect type.

        Args:
            effect_type: EffectType enum value

        Returns:
            EffectExecutor instance phù hợp

        Raises:
            ValueError: Nếu effect type không được hỗ trợ
        """
        executors = {
            "event": EventExecutor,
            "command": CommandExecutor,
            "notification": NotificationExecutor,
            "audit": AuditExecutor,
            "compensation": CompensationExecutor,
        }

        executor_class = executors.get(effect_type.value)
        if executor_class is None:
            EM.raise_error(
                ErrorCode.MDC-B01_WORKFLOW_EFFECT_FAILED,
                effect_type=effect_type.value,
            )

        return executor_class()

    @staticmethod
    def success(data: dict | None = None, message: str | None = None) -> EffectResult:
        """Tạo successful EffectResult."""
        return EffectResult(success=True, message=message, data=data)

    @staticmethod
    def failure(error: str) -> EffectResult:
        """Tạo failed EffectResult."""
        return EffectResult(success=False, error=error)


class EventExecutor(EffectExecutor):
    """Executor cho event publishing effects."""

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        # TODO: Integrate với CP05 Event Bus
        event_name = effect.publish
        return self.success(message=f"Published event: {event_name}")


class CommandExecutor(EffectExecutor):
    """Executor cho command execution effects."""

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        # TODO: Integrate với CP01 Commands
        command_name = effect.execute
        return self.success(message=f"Executed command: {command_name}")


class NotificationExecutor(EffectExecutor):
    """Executor cho notification effects."""

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        # TODO: Integrate với CP12 Notification
        channel = effect.channel
        return self.success(message=f"Sent notification via {channel}")


class AuditExecutor(EffectExecutor):
    """Executor cho audit logging effects."""

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        # TODO: Integrate với CP14 Audit
        action = effect.action
        return self.success(message=f"Logged audit: {action}")


class CompensationExecutor(EffectExecutor):
    """Executor cho compensation/rollback effects."""

    async def execute(self, effect: Effect, context: TransitionContext) -> EffectResult:
        # TODO: Implement saga compensation logic
        rollback = effect.rollback
        return self.success(message=f"Executed compensation: {rollback}")


__all__ = [
    "EffectResult",
    "EffectExecutor",
    "EventExecutor",
    "CommandExecutor",
    "NotificationExecutor",
    "AuditExecutor",
    "CompensationExecutor",
]