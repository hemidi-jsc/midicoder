"""
Mô-đun Command Emitter cho CP01 Domain Model.

Module này cung cấp implementation hoàn chỉnh cho Command pattern với:
- Transaction management (begin/commit/rollback)
- Guards integration (auth, tenant_scope, compliance)
- Đầy đủ Effect types (19+ types)
- Complex validation (cross-field, business rules, formulas)
- Compliance gates (RX01-RX12 support)
- Error handling (retry, circuit breaker, compensation)

Author: Midicoder Team
Version: 2.0.0
"""

# Import models
from .models import (
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

# Import validators và managers
from .validator import CommandValidator
from .transaction import TransactionManagerSQL
from .guards import CommandGuards
from .effects import CommandEffects

# Import emitters
try:
    from .fastapi import FastAPICommandEmitter
    from .nestjs import NestJSCommandEmitter
except ImportError as e:
    FastAPICommandEmitter = None
    NestJSCommandEmitter = None

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
    # Managers và Validators
    "CommandValidator",
    "TransactionManagerSQL",
    "CommandGuards",
    "CommandEffects",
    # Emitters
    "FastAPICommandEmitter",
    "NestJSCommandEmitter",
]
