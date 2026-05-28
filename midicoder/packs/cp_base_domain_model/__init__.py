"""
Unified Domain Model package for B01.

Combines entity, command, query, and value_object modules into a single
flat namespace with namespaced file names.

Re-exports all public symbols from:
- Entity models, parsers, and emitters
- Command models, parsers, validators, guards, effects, and transaction
- Query models, parsers, guards, and effects
- Value Object models, parsers, emitters, types, inheritance, computed

Usage:
    from midicoder.packs.cp_base_domain_model import (
        Entity, EntityEmitter, FastAPIEntityEmitter, NestJSEntityEmitter, EntityParser,
        Command, CommandValidator, CommandEffects, CommandGuards, TransactionManagerSQL,
        Query, QueryGuards, QueryEffects, FastAPIQueryEmitter, NestJSQueryEmitter,
        ValueObject, ValueObjectEmitter, FastAPIValueObjectEmitter, NestJSValueObjectEmitter,
    )

Author: Midicoder Team
Version: 3.0.0
"""

# ===========================================================================
# Advanced Domain Patterns
# ===========================================================================
from .models import (
    DomainEventType,
    DomainEvent,
    ConsistencyLevel,
    AggregateRoot,
    ProjectionType,
    Projection,
    EventTypeingStrategy,
    EventSourcedAggregate,
    TemporalGranularity,
    TemporalEntity,
    PolymorphismType,
    PolymorphicEntity,
    SagaOrchestration,
    CompensatingActionType,
    SagaStep,
    Saga,
    EntityField,
    EntityFieldType,
)

# ===========================================================================
# Entity
# ===========================================================================
from .models import (
    Entity,
    EntityField as Field,
    EntityFieldType as FieldType,
    Relationship,
    RelationshipType,
    Constraint,
    ConstraintType,
    Index,
    LifecycleHook,
    LifecycleEvent,
    EntityField,
    EntityFieldType,
)
from .entity_parser import EntityParser
from .entity_emitter import EntityEmitter
from .entity_fastapi import FastAPIEntityEmitter
from .entity_nestjs import NestJSEntityEmitter

# ===========================================================================
# Command
# ===========================================================================
from .models import (
    Command,
    CommandField,
    CommandFieldType,
    EffectType,
    GuardType,
    CommandGuard,
    CommandEffect,
    CommandError,
    ValidationResult,
)
from .command_parser import CommandParser
from .command_validator import CommandValidator
from .command_effects import CommandEffects
from .command_guards import CommandGuards
from .command_transaction import TransactionInfo, TransactionManagerSQL
from .command_fastapi import FastAPICommandEmitter
from .command_nestjs import NestJSCommandEmitter

# ===========================================================================
# Query
# ===========================================================================
from .models import (
    Query,
    AggregationQuery,
    QueryField,
    QueryGuard,
    QueryEffect,
    FilterOp,
    PaginationType,
    SortDirection,
    AggFunction,
    QueryGuardType,
    QueryEffectType,
    FilterExpression,
    FilterGroup,
    PHIMaskingConfig,
    SortExpression,
    PaginationConfig,
    ProjectionConfig,
    AggregationConfig,
)
from .query_parser import (
    parse_filters,
    parse_pagination,
    parse_projection,
    build_query_conditions,
    build_select_fields,
    VALID_OPERATORS,
)
from .query_guards import QueryGuards
from .query_effects import QueryEffects
from .query_fastapi import FastAPIQueryEmitter
from .query_nestjs import NestJSQueryEmitter

# ===========================================================================
# Value Object
# ===========================================================================
from .models import (
    ValueObject,
    VOField,
    VOFieldType,
)
from .vo_parser import ValueObjectParser
from .vo_emitter import (
    ValueObjectEmitter,
    EmittedValueObject,
    EmittedField,
    EmittedMethod,
    EmittedValidationRule,
)
from .vo_fastapi import FastAPIValueObjectEmitter
from .vo_nestjs import NestJSValueObjectEmitter
from .vo_types import TypeResolver, TypeMapping
from .vo_inheritance import InheritanceResolver, InheritanceChain
from .vo_computed import ComputedFieldEvaluator, FormulaError

# ===========================================================================
# Error Handler
# ===========================================================================
from .error_handler_models import (
    ErrorHandlingStrategy,
    ErrorLevel,
    ErrorLoggingConfig,
    ErrorMapper,
    ErrorNotificationConfig,
    GlobalErrorHandler,
)
from .error_handler_fastapi import FastAPIErrorHandlerEmitter

# ===========================================================================
# Recipes
# ===========================================================================
from .recipes import (
    SimpleEntityRecipe,
    AggregateRootRecipe,
    TemporalEntityRecipe,
    PolymorphicEntityRecipe,
    CQRSCommandRecipe,
    CQRSQueryRecipe,
    EventSourcedAggregateRecipe,
    SagaRecipe,
    ProjectionRecipe,
    ValueObjectRecipe,
    GlobalErrorHandlerRecipe,
)

# ===========================================================================
# Public API
# ===========================================================================
__all__ = [
    # -- Advanced Domain Patterns --
    "DomainEventType",
    "DomainEvent",
    "ConsistencyLevel",
    "AggregateRoot",
    "ProjectionType",
    "Projection",
    "EventTypeingStrategy",
    "EventSourcedAggregate",
    "TemporalGranularity",
    "TemporalEntity",
    "PolymorphismType",
    "PolymorphicEntity",
    "SagaOrchestration",
    "CompensatingActionType",
    "SagaStep",
    "Saga",
    # -- Entity --
    "Entity",
    "Field",
    "EntityFieldType",
    "Relationship",
    "RelationshipType",
    "Constraint",
    "ConstraintType",
    "Index",
    "LifecycleHook",
    "LifecycleEvent",
    "EntityParser",
    "EntityEmitter",
    "FastAPIEntityEmitter",
    "NestJSEntityEmitter",
    # -- Command --
    "Command",
    "CommandField",
    "CommandFieldType",
    "EffectType",
    "GuardType",
    "CommandGuard",
    "CommandEffect",
    "CommandError",
    "ValidationResult",
    "CommandParser",
    "CommandValidator",
    "CommandEffects",
    "CommandGuards",
    "TransactionInfo",
    "TransactionManagerSQL",
    "FastAPICommandEmitter",
    "NestJSCommandEmitter",
    # -- Query --
    "Query",
    "AggregationQuery",
    "QueryField",
    "QueryGuard",
    "QueryEffect",
    "FilterOp",
    "PaginationType",
    "SortDirection",
    "AggFunction",
    "QueryGuardType",
    "QueryEffectType",
    "FilterExpression",
    "FilterGroup",
    "PHIMaskingConfig",
    "SortExpression",
    "PaginationConfig",
    "ProjectionConfig",
    "AggregationConfig",
    "parse_filters",
    "parse_pagination",
    "parse_projection",
    "build_query_conditions",
    "build_select_fields",
    "VALID_OPERATORS",
    "QueryGuards",
    "QueryEffects",
    "FastAPIQueryEmitter",
    "NestJSQueryEmitter",
    # -- Value Object --
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
    # -- Recipes --
    "SimpleEntityRecipe",
    "AggregateRootRecipe",
    "TemporalEntityRecipe",
    "PolymorphicEntityRecipe",
    "CQRSCommandRecipe",
    "CQRSQueryRecipe",
    "EventSourcedAggregateRecipe",
    "SagaRecipe",
    "ProjectionRecipe",
    "ValueObjectRecipe",
    "GlobalErrorHandlerRecipe",
    # -- Error Handler --
    "ErrorLevel",
    "ErrorHandlingStrategy",
    "GlobalErrorHandler",
    "ErrorMapper",
    "ErrorLoggingConfig",
    "ErrorNotificationConfig",
    "FastAPIErrorHandlerEmitter",
]
