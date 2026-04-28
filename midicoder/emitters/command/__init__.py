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

from .models import (
    Command,
    CommandField,
    CommandGuard,
    CommandEffect,
    CommandError,
    EffectType,
    GuardType,
    ValidationResult,
)
from .fastapi import FastAPICommandEmitter
from .nestjs import NestJSCommandEmitter
from .transaction import TransactionManager
from .validator import CommandValidator
from .guards import CommandGuards
from .effects import CommandEffects

__all__ = [
    # Models
    "Command",
    "CommandField",
    "CommandGuard",
    "CommandEffect",
    "CommandError",
    "EffectType",
    "GuardType",
    "ValidationResult",
    # Core
    "FastAPICommandEmitter",
    "NestJSCommandEmitter",
    "TransactionManager",
    "CommandValidator",
    "CommandGuards",
    "CommandEffects",
]