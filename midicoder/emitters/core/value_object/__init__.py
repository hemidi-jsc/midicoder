"""
Compat shim for midicoder.emitters.core.value_object.

This module re-exports all symbols from the unified domain-model package
for backward compatibility. All new code should import from
midicoder.emitters.core.domain_model instead.
"""

from midicoder.emitters.core.domain_model.vo_models import (
    ValueObject,
    VOField,
    VOFieldType,
)
from midicoder.emitters.core.domain_model.vo_parser import ValueObjectParser
from midicoder.emitters.core.domain_model.vo_emitter import (
    ValueObjectEmitter,
    EmittedValueObject,
    EmittedField,
    EmittedMethod,
    EmittedValidationRule,
)
from midicoder.emitters.core.domain_model.vo_fastapi import FastAPIValueObjectEmitter
from midicoder.emitters.core.domain_model.vo_nestjs import NestJSValueObjectEmitter
from midicoder.emitters.core.domain_model.vo_types import TypeResolver, TypeMapping
from midicoder.emitters.core.domain_model.vo_inheritance import InheritanceResolver, InheritanceChain
from midicoder.emitters.core.domain_model.vo_computed import ComputedFieldEvaluator, FormulaError

__all__ = [
    "ValueObject",
    "VOField",
    "VOFieldType",
    "ValueObjectParser",
    "ValueObjectEmitter",
    "EmittedValueObject",
    "EmittedField",
    "EmittedMethod",
    "EmittedValidationRule",
    "FastAPIValueObjectEmitter",
    "NestJSValueObjectEmitter",
    "TypeResolver",
    "TypeMapping",
    "InheritanceResolver",
    "InheritanceChain",
    "ComputedFieldEvaluator",
    "FormulaError",
]
