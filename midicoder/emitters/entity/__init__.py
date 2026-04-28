"""
Mô-đun Entity Emitter cho CP01.

Cung cấp:
- EntityParser: Parse DSL YAML → Entity objects
- EntityEmitter: Abstract base class
- FastAPIEntityEmitter: FastAPI implementation
- NestJSEntityEmitter: NestJS implementation

Sử dụng:
    from midicoder.emitters.entity import (
        EntityParser,
        FastAPIEntityEmitter,
        NestJSEntityEmitter,
    )
    
    # Parse DSL
    parser = EntityParser()
    entities = parser.parse(dsl_yaml)
    
    # Emit FastAPI code
    emitter = FastAPIEntityEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
    for entity in entities:
        code = emitter.emit(entity)
        # Write to file...

Author: Midicoder Team
Version: 1.0.0
"""

from .models import (
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
from .parser import EntityParser
from .base import EntityEmitter
from .fastapi import FastAPIEntityEmitter
from .nestjs import NestJSEntityEmitter

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