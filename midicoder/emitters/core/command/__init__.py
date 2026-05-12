"""
Compat shim for midicoder.emitters.core.command.

This module re-exports all symbols from the unified domain-model package
for backward compatibility. All new code should import from
midicoder.emitters.core.domain_model instead.
"""

from midicoder.emitters.core.domain_model.command_models import (
    Command,
    CommandEffect,
    CommandError as CommandErrorModel,
    CommandGuard,
    EffectType,
    GuardType,
    Field as CommandField,
    FieldType,
    ValidationResult,
)
from midicoder.emitters.core.domain_model.command_validator import CommandValidator
from midicoder.emitters.core.domain_model.command_transaction import TransactionManagerSQL
from midicoder.emitters.core.domain_model.command_guards import CommandGuards
from midicoder.emitters.core.domain_model.command_effects import CommandEffects
from midicoder.emitters.core.domain_model.command_fastapi import FastAPICommandEmitter
from midicoder.emitters.core.domain_model.command_nestjs import NestJSCommandEmitter

# CommandError alias (use model for tests compatibility)
CommandError = CommandErrorModel

__all__ = [
    # Models
    "Command",
    "CommandField",
    "FieldType",
    "ValidationResult",
    # EffectType and GuardType
    "EffectType",
    "GuardType",
    # Guard and Effect dataclasses
    "CommandGuard",
    "CommandEffect",
    "CommandError",
    # Managers and Validators
    "CommandValidator",
    "TransactionManagerSQL",
    "CommandGuards",
    "CommandEffects",
    # Emitters
    "FastAPICommandEmitter",
    "NestJSCommandEmitter",
]
