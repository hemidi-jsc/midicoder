"""Compat shim — re-exports from domain_model.entity_models."""
from midicoder.emitters.core.domain_model.entity_models import *  # noqa: F401,F403
from midicoder.emitters.core.domain_model.entity_models import (
    Entity, Field, FieldType, Relationship, RelationshipType,
    Constraint, ConstraintType, Index, LifecycleHook, LifecycleEvent,
)
