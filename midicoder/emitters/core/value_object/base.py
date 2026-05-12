"""Compat shim — re-exports from domain_model.vo_emitter."""
from midicoder.emitters.core.domain_model.vo_emitter import (
    ValueObjectEmitter, EmittedValueObject, EmittedField,
    EmittedMethod, EmittedValidationRule,
)

__all__ = [
    "ValueObjectEmitter", "EmittedValueObject", "EmittedField",
    "EmittedMethod", "EmittedValidationRule",
]
