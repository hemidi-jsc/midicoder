"""
Value Object Emitter Module

Module này cung cấp core emitter infrastructure cho Value Object generation.
Support cho 100 industries với complex fields, inheritance, methods, và validation.

Các thành phần chính:
- Base Emitter: Abstract base class cho FastAPI/NestJS implementations
- Type Resolver: Mapping từ DSL types → Python/TypeScript types
- Inheritance Resolver: Resolution cho extends hierarchy
- Computed Evaluator: Formula evaluation cho computed fields

Author: Midicoder Team
Version: 2.0.0
"""

from .base import (
    ValueObjectEmitter,
    EmittedValueObject,
    EmittedField,
    EmittedMethod,
    EmittedValidationRule,
)
from .type_resolver import TypeResolver, TypeMapping
from .inheritance import InheritanceResolver, InheritanceChain
from .computed import ComputedFieldEvaluator, FormulaError
from .fastapi import FastAPIValueObjectEmitter
from .nestjs import NestJSValueObjectEmitter

__all__ = [
    "ValueObjectEmitter",
    "EmittedValueObject",
    "EmittedField",
    "EmittedMethod",
    "EmittedValidationRule",
    "TypeResolver",
    "TypeMapping",
    "InheritanceResolver",
    "InheritanceChain",
    "ComputedFieldEvaluator",
    "FormulaError",
    "FastAPIValueObjectEmitter",
    "NestJSValueObjectEmitter",
]
