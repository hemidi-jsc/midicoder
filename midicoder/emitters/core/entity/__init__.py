"""
Compat shim for midicoder.emitters.core.entity.

This module re-exports all symbols from the unified domain-model package
for backward compatibility. All new code should import from
midicoder.emitters.core.domain_model instead.
"""

from midicoder.emitters.core.domain_model.entity_models import (
    Entity,
    Field,
    FieldType,
    Relationship,
    RelationshipType,
    Constraint,
    ConstraintType,
    Index,
    LifecycleHook,
    LifecycleEvent,
)
from midicoder.emitters.core.domain_model.entity_parser import EntityParser
from midicoder.emitters.core.domain_model.entity_emitter import EntityEmitter
from midicoder.emitters.core.domain_model.entity_fastapi import FastAPIEntityEmitter
from midicoder.emitters.core.domain_model.entity_nestjs import NestJSEntityEmitter

__all__ = [
    # Models
    "Entity",
    "Field",
    "FieldType",
    "Relationship",
    "RelationshipType",
    "Constraint",
    "ConstraintType",
    "Index",
    "LifecycleHook",
    "LifecycleEvent",
    # Parser
    "EntityParser",
    # Emitters
    "EntityEmitter",
    "FastAPIEntityEmitter",
    "NestJSEntityEmitter",
]
