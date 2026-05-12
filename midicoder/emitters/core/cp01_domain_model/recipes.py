# coding: utf-8
"""
Recipes cho Domain Model DSL & IR Builder (CP01).

Recipe = 1-level pattern macro — concrete value assignment đến patterns
trong models.py. Không nest, không domain-specific.

Mỗi recipe trả về một instance của pattern vocabulary (Entity, AggregateRoot,
Command, Query, v.v.) đã được configure với concrete values phù hợp với
use case cụ thể.

Recipes:
- SimpleEntityRecipe: Basic entity with ID, timestamps, CRUD hooks
- AggregateRootRecipe: Aggregate with root, children, events, invariants
- TemporalEntityRecipe: Entity with valid_from/valid_to temporal tracking
- CQRSCommandRecipe: Command with auth + tenant guards + transaction
- CQRSQueryRecipe: Query with auth + tenant guards + pagination + projection
- EventSourcedAggregateRecipe: Event-sourced aggregate with append-only log
- SagaRecipe: Long-running transaction with compensating steps
- PolymorphicEntityRecipe: Entity with subtype inheritance (STI)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.cp01_domain_model.models import (
    AggregationConfig,
    AggregationQuery,
    AggregateRoot,
    Command,
    CommandEffect,
    CommandError,
    CommandField,
    CommandFieldType,
    CommandGuard,
    CompensatingActionType,
    ConsistencyLevel,
    Constraint,
    ConstraintType,
    Entity,
    EntityField,
    EntityFieldType,
    EventSourcedAggregate,
    EventTypeingStrategy,
    FilterExpression,
    FilterOp,
    GuardType,
    Index,
    LifecycleEvent,
    LifecycleHook,
    PaginationConfig,
    PaginationType,
    PolymorphicEntity,
    PolymorphismType,
    Projection,
    ProjectionConfig,
    ProjectionType,
    Query,
    QueryEffect,
    QueryEffectType,
    QueryField,
    QueryGuard,
    QueryGuardType,
    Relationship,
    RelationshipType,
    Saga,
    SagaOrchestration,
    SagaStep,
    SortDirection,
    SortExpression,
    TemporalEntity,
    TemporalGranularity,
    ValueObject,
    VOField,
    VOFieldType,
)


# ===========================================================================
# Common building blocks
# ===========================================================================


def _id_field() -> EntityField:
    """UUID primary key — tiêu chuẩn cho mọi entity."""
    return EntityField(
        name="id",
        field_type=EntityFieldType.UUID,
        primary_key=True,
        nullable=False,
        description="Unique identifier",
    )


def _tenant_id_field() -> EntityField:
    """Tenant ID — multi-tenant isolation."""
    return EntityField(
        name="tenant_id",
        field_type=EntityFieldType.UUID,
        nullable=False,
        index=True,
        description="Multi-tenant isolation key",
    )


def _created_at_field() -> EntityField:
    """Created timestamp with server default."""
    return EntityField(
        name="created_at",
        field_type=EntityFieldType.DATETIME,
        nullable=False,
        server_default="NOW()",
        description="Record creation timestamp",
    )


def _updated_at_field() -> EntityField:
    """Updated timestamp with server default."""
    return EntityField(
        name="updated_at",
        field_type=EntityFieldType.DATETIME,
        nullable=False,
        server_default="NOW()",
        description="Record last update timestamp",
    )


def _audit_fields() -> list[EntityField]:
    """Standard audit fields (tenant_id, created_at, updated_at)."""
    return [_tenant_id_field(), _created_at_field(), _updated_at_field()]


def _auth_guard(permission: str) -> CommandGuard:
    """AUTH guard với permission."""
    return CommandGuard(guard_type=GuardType.AUTH, permission=permission)


def _tenant_guard() -> CommandGuard:
    """TENANT_SCOPE guard cho multi-tenant isolation."""
    return CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated")


def _query_auth_guard(permission: str) -> QueryGuard:
    """AUTH guard cho Query."""
    return QueryGuard(guard_type=QueryGuardType.AUTH, permission=permission)


def _query_tenant_guard() -> QueryGuard:
    """TENANT_SCOPE guard cho Query."""
    return QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE, mode="tenant_isolated")


# ===========================================================================
# SimpleEntityRecipe
# ===========================================================================


def SimpleEntityRecipe(
    name: str = "Product",
    extra_fields: list[EntityField] | None = None,
    with_tenant: bool = True,
    with_lifecycle_hooks: bool = True,
) -> Entity:
    """
    Simple entity recipe — CRUD entity với audit fields.

    Concrete value assignment:
    - UUID primary key (id)
    - Optional tenant_id (multi-tenant)
    - created_at, updated_at (audit timestamps)
    - before_insert hook (auto-set tenant_id)
    - before_update hook (auto-update updated_at)

    Args:
        name: Entity name (PascalCase)
        extra_fields: Additional fields specific to the domain
        with_tenant: Include tenant_id field for multi-tenant isolation
        with_lifecycle_hooks: Include before_insert/before_update hooks

    Returns:
        Entity instance with standard audit fields

    Example:
        >>> entity = SimpleEntityRecipe("User", with_tenant=True)
        >>> len(entity.fields)  # id + tenant_id + created_at + updated_at
        4
    """
    fields = [_id_field()]

    if with_tenant:
        fields.append(_tenant_id_field())

    if extra_fields:
        fields.extend(extra_fields)

    fields.extend([_created_at_field(), _updated_at_field()])

    hooks: list[LifecycleHook] = []
    if with_lifecycle_hooks:
        hooks.append(LifecycleHook(
            event=LifecycleEvent.BEFORE_INSERT,
            hook_name="set_created_at",
            params={"field": "created_at", "value": "NOW()"},
        ))
        hooks.append(LifecycleHook(
            event=LifecycleEvent.BEFORE_UPDATE,
            hook_name="set_updated_at",
            params={"field": "updated_at", "value": "NOW()"},
        ))

    return Entity(
        id=name,
        description=f"Simple {name} entity with audit fields",
        fields=fields,
        indexes=[Index(name=f"idx_{name.lower()}_created", fields=["created_at"])],
        lifecycle_hooks=hooks,
    )


# ===========================================================================
# AggregateRootRecipe
# ===========================================================================


def AggregateRootRecipe(
    name: str = "Order",
    root_entity: str = "Order",
    child_entities: list[str] | None = None,
    events: list[str] | None = None,
    invariants: list[str] | None = None,
    consistency: ConsistencyLevel = ConsistencyLevel.STRICT,
) -> AggregateRoot:
    """
    Aggregate root recipe — consistency boundary với invariants.

    Concrete value assignment:
    - Strict consistency (ACID trong aggregate boundary)
    - Child entities chỉ accessible qua root
    - Domain events emit khi state thay đổi
    - Invariants enforce business rules

    Args:
        name: Aggregate name (PascalCase)
        root_entity: Entity name acting as root
        child_entities: Entities within aggregate boundary
        events: Domain events emitted by this aggregate
        invariants: Business rules that must always hold
        consistency: Consistency level (strict/eventual/relaxed)

    Returns:
        AggregateRoot instance

    Example:
        >>> agg = AggregateRootRecipe("Order", child_entities=["OrderItem"],
        ...                            events=["OrderPlaced", "OrderCancelled"])
    """
    return AggregateRoot(
        id=name,
        root_entity=root_entity,
        child_entities=child_entities or [],
        events=events or [],
        consistency=consistency,
        invariants=invariants or [],
        description=f"Aggregate root for {name} consistency boundary",
    )


# ===========================================================================
# TemporalEntityRecipe
# ===========================================================================


def TemporalEntityRecipe(
    name: str = "Price",
    extra_fields: list[EntityField] | None = None,
    granularity: TemporalGranularity = TemporalGranularity.SECOND,
    valid_from_field: str = "valid_from",
    valid_to_field: str = "valid_to",
) -> TemporalEntity:
    """
    Temporal entity recipe — tracking state theo thời gian.

    Concrete value assignment:
    - valid_from/valid_to columns (TIMESTAMPTZ)
    - current_predicate = "valid_to IS NULL" (SCD Type 2)
    - Index on (entity_id, valid_from) cho range query
    - Constraint: valid_from < valid_to

    Args:
        name: Entity name (PascalCase)
        extra_fields: Additional business fields
        granularity: Temporal granularity (second/minute/day/month)
        valid_from_field: Field name for start of validity period
        valid_to_field: Field name for end of validity period

    Returns:
        TemporalEntity instance

    Example:
        >>> temporal = TemporalEntityRecipe("EmployeeSalary",
        ...     extra_fields=[EntityField(name="amount", field_type=EntityFieldType.DECIMAL)])
    """
    fields: list[EntityField] = [_id_field()]

    if extra_fields:
        fields.extend(extra_fields)

    fields.extend([
        EntityField(
            name=valid_from_field,
            field_type=EntityFieldType.DATETIME,
            nullable=False,
            description="Start of validity period",
        ),
        EntityField(
            name=valid_to_field,
            field_type=EntityFieldType.DATETIME,
            nullable=True,
            description="End of validity period (NULL = current)",
        ),
    ])

    return TemporalEntity(
        id=name,
        fields=fields,
        valid_from_field=valid_from_field,
        valid_to_field=valid_to_field,
        granularity=granularity,
        current_predicate=f"{valid_to_field} IS NULL",
        description=f"Temporal entity tracking {name} state over time",
    )


# ===========================================================================
# CQRSCommandRecipe
# ===========================================================================


def CQRSCommandRecipe(
    name: str = "CreateOrder",
    entity: str = "Order",
    permission: str = "order.create",
    input_fields: list[CommandField] | None = None,
    emits_events: list[str] | None = None,
    transaction_required: bool = True,
    category: str = "create",
) -> Command:
    """
    CQRS command recipe — write operation với guards + transaction.

    Concrete value assignment:
    - AUTH guard (authorize_permission)
    - TENANT_SCOPE guard (enforce_tenant_scope)
    - CREATE_RECORD effect
    - PUBLISH_EVENT effect cho mỗi event
    - Transaction: True (ACID)
    - on_error: rollback

    Args:
        name: Command name (PascalCase, imperative: "CreateOrder")
        entity: Target entity name
        permission: Permission string for AUTH guard
        input_fields: Input fields for the command
        emits_events: Domain events to emit after execution
        transaction_required: Whether to wrap in transaction
        category: Command category (create/update/delete/custom)

    Returns:
        Command instance

    Example:
        >>> cmd = CQRSCommandRecipe("CreateOrder", emits_events=["OrderPlaced"])
        >>> len(cmd.guards)  # auth + tenant
        2
    """
    effects: list[CommandEffect] = []

    if category == "create":
        effects.append(CommandEffect(effect_type="create_record", entity=entity))
    elif category == "update":
        effects.append(CommandEffect(effect_type="update_record", entity=entity))
    elif category == "delete":
        effects.append(CommandEffect(effect_type="delete_record", entity=entity))

    if emits_events:
        for evt in emits_events:
            effects.append(CommandEffect(effect_type="publish_event", event=evt))

    return Command(
        id=name,
        description=f"Command to {category} {entity}",
        input=input_fields or [],
        guards=[_auth_guard(permission), _tenant_guard()],
        effects=effects,
        writes_to=[entity],
        transaction_required=transaction_required,
        category=category,
        emits=emits_events or [],
        tenant_scope="tenant_isolated",
        on_error="rollback",
    )


# ===========================================================================
# CQRSQueryRecipe
# ===========================================================================


def CQRSQueryRecipe(
    name: str = "ListOrders",
    entity: str = "Order",
    permission: str = "order.read",
    input_fields: list[QueryField] | None = None,
    include_audit_log: bool = False,
    pagination_type: PaginationType = PaginationType.OFFSET,
    page_size: int = 20,
    default_sort_field: str = "created_at",
    default_sort_direction: SortDirection = SortDirection.DESC,
) -> Query:
    """
    CQRS query recipe — read operation với guards + pagination + projection.

    Concrete value assignment:
    - AUTH guard (authorize_permission)
    - TENANT_SCOPE guard (enforce_tenant_scope)
    - OFFSET pagination (default 20/page)
    - Default sort by created_at DESC
    - Optional audit log effect

    Args:
        name: Query name (PascalCase, imperative: "ListOrders", "GetOrder")
        entity: Source entity name
        permission: Permission string for AUTH guard
        input_fields: Input fields (filters, params)
        include_audit_log: Include WRITE_AUDIT_LOG effect
        pagination_type: Pagination type (OFFSET/CURSOR)
        page_size: Records per page
        default_sort_field: Default sort field
        default_sort_direction: Default sort direction

    Returns:
        Query instance

    Example:
        >>> query = CQRSQueryRecipe("ListOrders", page_size=50)
        >>> len(query.guards)  # auth + tenant
        2
    """
    guards = [_query_auth_guard(permission), _query_tenant_guard()]
    effects: list[QueryEffect] = []

    if include_audit_log:
        effects.append(QueryEffect(
            effect_type=QueryEffectType.WRITE_AUDIT_LOG,
            audit_action=f"query_{entity.lower()}",
        ))

    return Query(
        id=name,
        description=f"Query to read {entity}",
        reads_from=entity,
        input=input_fields or [],
        guards=guards,
        effects=effects,
        pagination=PaginationConfig(
            type=pagination_type,
            page_size=page_size,
            page=1,
        ),
        sort=[SortExpression(
            field=default_sort_field,
            direction=default_sort_direction,
        )],
    )


# ===========================================================================
# EventSourcedAggregateRecipe
# ===========================================================================


def EventSourcedAggregateRecipe(
    name: str = "BankAccount",
    root_entity: str = "BankAccount",
    events: list[str] | None = None,
    snapshot_interval: int = 100,
    versioned: bool = True,
) -> EventSourcedAggregate:
    """
    Event-sourced aggregate recipe — state từ event log.

    Concrete value assignment:
    - Snapshot strategy (every 100 events)
    - Versioned optimistic concurrency control
    - Append-only event log

    Args:
        name: Aggregate name (PascalCase)
        root_entity: Root entity name
        events: Domain events emitted by this aggregate
        snapshot_interval: Number of events between snapshots (0 = no snapshot)
        versioned: Enable optimistic concurrency via version column

    Returns:
        EventSourcedAggregate instance

    Example:
        >>> esa = EventSourcedAggregateRecipe("BankAccount",
        ...     events=["Deposited", "Withdrawn", "Transferred"])
    """
    return EventSourcedAggregate(
        id=name,
        root_entity=root_entity,
        events=events or [],
        eventing_strategy=EventTypeingStrategy.SNAPSHOT,
        snapshot_interval=snapshot_interval,
        versioned=versioned,
        description=f"Event-sourced aggregate for {name}",
    )


# ===========================================================================
# SagaRecipe
# ===========================================================================


def SagaRecipe(
    name: str = "OrderFulfillment",
    steps: list[SagaStep] | None = None,
    orchestration: SagaOrchestration = SagaOrchestration.ORCHESTRATION,
    timeout_seconds: int = 3600,
) -> Saga:
    """
    Saga recipe — long-running transaction với compensating steps.

    Concrete value assignment:
    - Centralized orchestration (orchestrator pattern)
    - Each step has action + compensating_action
    - Default 1-hour timeout
    - Compensating actions: UNDO (reverse operation)

    Args:
        name: Saga name (PascalCase)
        steps: Ordered list of saga steps
        orchestration: Choreography or orchestration
        timeout_seconds: Maximum saga duration in seconds

    Returns:
        Saga instance

    Example:
        >>> saga = SagaRecipe("OrderFulfillment", steps=[
        ...     SagaStep(name="ReserveInventory", action="reserve_inventory",
        ...              compensating_action="release_inventory"),
        ...     SagaStep(name="ProcessPayment", action="charge_payment",
        ...              compensating_action="refund_payment"),
        ... ])
    """
    return Saga(
        id=name,
        orchestration=orchestration,
        steps=steps or [],
        timeout_seconds=timeout_seconds,
        description=f"Long-running saga for {name}",
    )


# ===========================================================================
# PolymorphicEntityRecipe
# ===========================================================================


def PolymorphicEntityRecipe(
    name: str = "Payment",
    subtypes: list[dict[str, Any]] | None = None,
    base_fields: list[EntityField] | None = None,
    polymorphism_type: PolymorphismType = PolymorphismType.SINGLE_TABLE,
    discriminator_field: str = "payment_type",
) -> PolymorphicEntity:
    """
    Polymorphic entity recipe — subtype inheritance.

    Concrete value assignment:
    - Single-table inheritance (default, most common)
    - Discriminator column to distinguish subtypes
    - Base fields shared by all subtypes
    - Each subtype adds its own fields

    Args:
        name: Base entity name (PascalCase)
        subtypes: List of subtype definitions with "name" and "fields"
        base_fields: Fields shared by all subtypes
        polymorphism_type: Inheritance strategy (single_table/joined_table/concrete_table)
        discriminator_field: Column name to distinguish subtypes

    Returns:
        PolymorphicEntity instance

    Example:
        >>> poly = PolymorphicEntityRecipe("Payment", subtypes=[
        ...     {"name": "CreditCardPayment", "fields": ["card_number", "expiry"]},
        ...     {"name": "BankTransferPayment", "fields": ["account_number", "bank_code"]},
        ... ])
    """
    fields = [_id_field()]

    if base_fields:
        fields.extend(base_fields)

    # Add discriminator field
    fields.append(EntityField(
        name=discriminator_field,
        field_type=EntityFieldType.STRING,
        nullable=False,
        description=f"Discriminator for {name} subtypes",
    ))

    fields.extend([_created_at_field(), _updated_at_field()])

    return PolymorphicEntity(
        id=name,
        polymorphism_type=polymorphism_type,
        discriminator_field=discriminator_field,
        base_fields=fields,
        subtypes=subtypes or [],
        description=f"Polymorphic entity {name} with {len(subtypes or [])} subtypes",
    )


# ===========================================================================
# ProjectionRecipe (bonus — CQRS read model)
# ===========================================================================


def ProjectionRecipe(
    name: str = "OrderSummary",
    source_aggregate: str = "Order",
    source_events: list[str] | None = None,
    fields: list[EntityField] | None = None,
    projection_type: ProjectionType = ProjectionType.DENORMALIZED,
) -> Projection:
    """
    CQRS projection recipe — read model derived từ domain events.

    Concrete value assignment:
    - Denormalized read model (default, most common)
    - Subscribe to source aggregate events
    - Fields optimized for query patterns

    Args:
        name: Projection name (PascalCase)
        source_aggregate: Source aggregate root
        source_events: Events that trigger projection update
        fields: Fields in the read model
        projection_type: Projection type (denormalized/materialized_view/search_index/graph)

    Returns:
        Projection instance

    Example:
        >>> proj = ProjectionRecipe("OrderSummary",
        ...     source_events=["OrderPlaced", "OrderCancelled"],
        ...     fields=[EntityField(name="order_id", field_type=EntityFieldType.UUID)])
    """
    return Projection(
        id=name,
        projection_type=projection_type,
        source_aggregate=source_aggregate,
        source_events=source_events or [],
        fields=fields or [],
        description=f"CQRS read model for {name}",
    )


# ===========================================================================
# ValueObjectRecipe (bonus — immutable domain primitive)
# ===========================================================================


def ValueObjectRecipe(
    name: str = "Money",
    fields: list[VOField] | None = None,
    description: str = "",
) -> ValueObject:
    """
    Value object recipe — immutable, equality-by-value domain primitive.

    Concrete value assignment:
    - Immutable (no identity, no lifecycle)
    - Equality by value of all fields
    - Used as embedded value in entities

    Args:
        name: Value object name (PascalCase)
        fields: Value object fields
        description: Description of the value object

    Returns:
        ValueObject instance

    Example:
        >>> vo = ValueObjectRecipe("Money", fields=[
        ...     VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
        ...     VOField(name="currency", field_type=VOFieldType.STRING, required=True),
        ... ])
    """
    return ValueObject(
        id=name,
        fields=fields or [],
        description=description or f"Value object {name}",
    )


__all__ = [
    # Entity recipes
    "SimpleEntityRecipe",
    "AggregateRootRecipe",
    "TemporalEntityRecipe",
    "PolymorphicEntityRecipe",
    # CQRS recipes
    "CQRSCommandRecipe",
    "CQRSQueryRecipe",
    "ProjectionRecipe",
    # Event sourcing recipes
    "EventSourcedAggregateRecipe",
    # Saga recipe
    "SagaRecipe",
    # Value object recipe
    "ValueObjectRecipe",
]
