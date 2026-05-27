"""
Public API cho CP32: State Machine Engine.

Exports:
    Models: StateMachineDefinition, StateInstance, TransitionRecord,
            TransitionResult, TransitionAction
    Engine: StateMachineEngine
    Parser: StateMachineParser
    Emitter: StateMachineFastAPIEmitter, StateMachineNestJSEmitter

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp32_state_machine.models import (
    StateInstance,
    StateMachineDefinition,
    TransitionAction,
    TransitionRecord,
    TransitionResult,
)
from midicoder.packs.cp32_state_machine.engine import StateMachineEngine
from midicoder.packs.cp32_state_machine.parser import StateMachineParser
from midicoder.packs.cp32_state_machine.fastapi import StateMachineFastAPIEmitter
from midicoder.packs.cp32_state_machine.nestjs import StateMachineNestJSEmitter

__all__ = [
    # Models
    "StateMachineDefinition",
    "StateInstance",
    "TransitionRecord",
    "TransitionResult",
    "TransitionAction",
    # Engine
    "StateMachineEngine",
    # Parser
    "StateMachineParser",
    # Emitters
    "StateMachineFastAPIEmitter",
    "StateMachineNestJSEmitter",
]
