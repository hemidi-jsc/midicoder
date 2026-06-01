"""
Tests cho CP01 Recipes — 10 factory functions.

Mỗi recipe là 1-level pattern macro: concrete value assignment vào CP01 models.
Tests verify rằng recipe trả về proper pattern instances với defaults đúng.

CP01: Domain Model - Recipes
"""

import pytest

from midicoder.packs.cp_base_domain_model import (
    # Pattern models
    Entity, EntityField, EntityFieldType,
    Command, CommandField, CommandFieldType, CommandGuard, CommandEffect, GuardType, EffectType,
    Query, QueryField, QueryGuard, QueryEffect, QueryGuardType, QueryEffectType,
    ValueObject, VOField, VOFieldType,
    AggregateRoot, ConsistencyLevel,
    TemporalEntity, TemporalGranularity,
    EventSourcedAggregate, EventTypeingStrategy,
    Saga, SagaStep, SagaOrchestration,
    PolymorphicEntity, PolymorphismType,
    Projection, ProjectionType,
    PaginationConfig, PaginationType, SortDirection,
    LifecycleHook, LifecycleEvent,
    Index,
    # All 10 recipes
    SimpleEntityRecipe,
    AggregateRootRecipe,
    TemporalEntityRecipe,
    CQRSCommandRecipe,
    CQRSQueryRecipe,
    EventSourcedAggregateRecipe,
    SagaRecipe,
    PolymorphicEntityRecipe,
    ProjectionRecipe,
    ValueObjectRecipe,
)


# ===========================================================================
# SimpleEntityRecipe
# ===========================================================================

class TestSimpleEntityRecipe:
    """Tests cho SimpleEntityRecipe."""

    def test_minimal(self):
        e = SimpleEntityRecipe("User")
        assert isinstance(e, Entity)
        assert e.id == "User"
        assert len(e.fields) >= 4  # id, tenant_id, created_at, updated_at

    def test_with_extra_fields(self):
        e = SimpleEntityRecipe("User", extra_fields=[
            EntityField(name="email", field_type=EntityFieldType.STRING, nullable=False),
        ])
        field_names = [f.name for f in e.fields]
        assert "email" in field_names
        assert "id" in field_names

    def test_with_tenant_default_true(self):
        e = SimpleEntityRecipe("Order")
        field_names = [f.name for f in e.fields]
        assert "tenant_id" in field_names

    def test_without_tenant(self):
        e = SimpleEntityRecipe("PublicConfig", with_tenant=False)
        field_names = [f.name for f in e.fields]
        assert "tenant_id" not in field_names

    def test_has_timestamps(self):
        e = SimpleEntityRecipe("AuditLog")
        field_names = [f.name for f in e.fields]
        assert "created_at" in field_names
        assert "updated_at" in field_names

    def test_id_is_uuid(self):
        e = SimpleEntityRecipe("Record")
        id_field = next((f for f in e.fields if f.name == "id"), None)
        assert id_field is not None
        assert id_field.field_type == EntityFieldType.UUID
        assert id_field.primary_key is True

    def test_has_lifecycle_hooks(self):
        e = SimpleEntityRecipe("Record", with_lifecycle_hooks=True)
        assert len(e.lifecycle_hooks) == 2
        events = [h.event for h in e.lifecycle_hooks]
        assert LifecycleEvent.BEFORE_INSERT in events
        assert LifecycleEvent.BEFORE_UPDATE in events

    def test_without_lifecycle_hooks(self):
        e = SimpleEntityRecipe("Record", with_lifecycle_hooks=False)
        assert len(e.lifecycle_hooks) == 0

    def test_has_index(self):
        e = SimpleEntityRecipe("Record")
        assert len(e.indexes) >= 1

    def test_description_auto_generated(self):
        e = SimpleEntityRecipe("MyEntity")
        assert "MyEntity" in e.description


# ===========================================================================
# AggregateRootRecipe
# ===========================================================================

class TestAggregateRootRecipe:
    """Tests cho AggregateRootRecipe."""

    def test_minimal(self):
        a = AggregateRootRecipe("Order")
        assert isinstance(a, AggregateRoot)
        assert a.id == "Order"

    def test_with_child_entities(self):
        a = AggregateRootRecipe("Order", child_entities=["OrderItem", "OrderPayment"])
        assert "OrderItem" in a.child_entities
        assert "OrderPayment" in a.child_entities

    def test_with_events(self):
        a = AggregateRootRecipe("Order", events=["OrderPlaced", "OrderShipped"])
        assert "OrderPlaced" in a.events
        assert "OrderShipped" in a.events

    def test_with_invariants(self):
        a = AggregateRootRecipe("Order", invariants=["total > 0"])
        assert "total > 0" in a.invariants

    def test_consistency_strict(self):
        a = AggregateRootRecipe("Order", consistency=ConsistencyLevel.STRICT)
        assert a.consistency == ConsistencyLevel.STRICT

    def test_consistency_eventual(self):
        a = AggregateRootRecipe("Order", consistency=ConsistencyLevel.EVENTUAL)
        assert a.consistency == ConsistencyLevel.EVENTUAL

    def test_consistency_default_strict(self):
        a = AggregateRootRecipe("Order")
        assert a.consistency == ConsistencyLevel.STRICT

    def test_description(self):
        a = AggregateRootRecipe("Order")
        assert "Order" in a.description


# ===========================================================================
# TemporalEntityRecipe
# ===========================================================================

class TestTemporalEntityRecipe:
    """Tests cho TemporalEntityRecipe."""

    def test_minimal(self):
        t = TemporalEntityRecipe("Price")
        assert isinstance(t, TemporalEntity)
        assert t.id == "Price"

    def test_has_valid_from_to(self):
        t = TemporalEntityRecipe("Price")
        assert t.valid_from_field == "valid_from"
        assert t.valid_to_field == "valid_to"

    def test_with_extra_fields(self):
        t = TemporalEntityRecipe("Price", extra_fields=[
            EntityField(name="amount", field_type=EntityFieldType.DECIMAL, nullable=False),
        ])
        field_names = [f.name for f in t.fields]
        assert "amount" in field_names
        assert "valid_from" in field_names
        assert "valid_to" in field_names

    def test_current_predicate(self):
        t = TemporalEntityRecipe("Price")
        assert t.current_predicate == "valid_to IS NULL"

    def test_custom_valid_fields(self):
        t = TemporalEntityRecipe("Price", valid_from_field="start_date", valid_to_field="end_date")
        assert t.valid_from_field == "start_date"
        assert t.valid_to_field == "end_date"
        assert t.current_predicate == "end_date IS NULL"

    def test_default_granularity(self):
        t = TemporalEntityRecipe("Price")
        assert t.granularity == TemporalGranularity.SECOND

    def test_has_id_field(self):
        t = TemporalEntityRecipe("Price")
        id_field = next((f for f in t.fields if f.name == "id"), None)
        assert id_field is not None


# ===========================================================================
# PolymorphicEntityRecipe
# ===========================================================================

class TestPolymorphicEntityRecipe:
    """Tests cho PolymorphicEntityRecipe."""

    def test_minimal(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[
            {"name": "CreditCard", "fields": [{"name": "card_number", "type": "string"}]},
        ])
        assert isinstance(p, PolymorphicEntity)
        assert p.id == "Payment"
        assert len(p.subtypes) == 1

    def test_multiple_subtypes(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[
            {"name": "CreditCard", "fields": [{"name": "card_number", "type": "string"}]},
            {"name": "BankTransfer", "fields": [{"name": "account", "type": "string"}]},
        ])
        assert len(p.subtypes) == 2

    def test_default_polymorphism_type(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[
            {"name": "CreditCard", "fields": []},
        ])
        assert p.polymorphism_type == PolymorphismType.SINGLE_TABLE

    def test_explicit_polymorphism_type(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[
            {"name": "CreditCard", "fields": []},
        ], polymorphism_type=PolymorphismType.CONCRETE_TABLE)
        assert p.polymorphism_type == PolymorphismType.CONCRETE_TABLE

    def test_discriminator_field(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[
            {"name": "CreditCard", "fields": []},
        ], discriminator_field="type")
        assert p.discriminator_field == "type"
        disc = next((f for f in p.base_fields if f.name == "type"), None)
        assert disc is not None

    def test_has_audit_fields(self):
        p = PolymorphicEntityRecipe("Payment", subtypes=[])
        field_names = [f.name for f in p.base_fields]
        assert "created_at" in field_names
        assert "updated_at" in field_names


# ===========================================================================
# CQRSCommandRecipe
# ===========================================================================

class TestCQRSCommandRecipe:
    """Tests cho CQRSCommandRecipe."""

    def test_minimal(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert isinstance(c, Command)
        assert c.id == "CreateOrder"

    def test_has_auth_guard(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        guard_types = [g.guard_type for g in c.guards]
        assert GuardType.AUTH in guard_types

    def test_has_tenant_guard(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        guard_types = [g.guard_type for g in c.guards]
        assert GuardType.TENANT_SCOPE in guard_types

    def test_transaction_required(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert c.transaction_required is True

    def test_with_input_fields(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order", input_fields=[
            CommandField(name="item_count", field_type=CommandFieldType.INTEGER, required=True),
        ])
        field_names = [f.name for f in c.input]
        assert "item_count" in field_names

    def test_with_emits_events(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order", emits_events=["OrderPlaced"])
        assert "OrderPlaced" in c.emits

    def test_guard_count(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert len(c.guards) == 2  # auth + tenant

    def test_create_category_effect(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order", category="create")
        effect_types = [str(e.effect_type) for e in c.effects]
        assert "create_record" in effect_types

    def test_update_category_effect(self):
        c = CQRSCommandRecipe("UpdateOrder", entity="Order", category="update")
        effect_types = [str(e.effect_type) for e in c.effects]
        assert "update_record" in effect_types

    def test_delete_category_effect(self):
        c = CQRSCommandRecipe("DeleteOrder", entity="Order", category="delete")
        effect_types = [str(e.effect_type) for e in c.effects]
        assert "delete_record" in effect_types

    def test_writes_to(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert "Order" in c.writes_to

    def test_on_error_rollback(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert c.on_error == "rollback"

    def test_tenant_scope(self):
        c = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert c.tenant_scope == "tenant_isolated"


# ===========================================================================
# CQRSQueryRecipe
# ===========================================================================

class TestCQRSQueryRecipe:
    """Tests cho CQRSQueryRecipe."""

    def test_minimal(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        assert isinstance(q, Query)
        assert q.id == "ListOrders"

    def test_has_auth_guard(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        guard_types = [g.guard_type for g in q.guards]
        assert QueryGuardType.AUTH in guard_types

    def test_has_tenant_guard(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        guard_types = [g.guard_type for g in q.guards]
        assert QueryGuardType.TENANT_SCOPE in guard_types

    def test_default_pagination(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        assert q.pagination.page_size == 20
        assert q.pagination.type == PaginationType.OFFSET

    def test_custom_page_size(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order", page_size=50)
        assert q.pagination.page_size == 50

    def test_with_audit_log(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order", include_audit_log=True)
        effect_types = [e.effect_type for e in q.effects]
        assert QueryEffectType.WRITE_AUDIT_LOG in effect_types

    def test_without_audit_log(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order", include_audit_log=False)
        assert len(q.effects) == 0

    def test_guard_count(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        assert len(q.guards) == 2  # auth + tenant

    def test_default_sort(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        assert len(q.sort) == 1
        assert q.sort[0].field == "created_at"
        assert q.sort[0].direction == SortDirection.DESC

    def test_reads_from(self):
        q = CQRSQueryRecipe("ListOrders", entity="Order")
        assert q.reads_from == "Order"


# ===========================================================================
# EventSourcedAggregateRecipe
# ===========================================================================

class TestEventSourcedAggregateRecipe:
    """Tests cho EventSourcedAggregateRecipe."""

    def test_minimal(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"])
        assert isinstance(e, EventSourcedAggregate)
        assert e.id == "BankAccount"

    def test_versioned(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"])
        assert e.versioned is True

    def test_default_snapshot_interval(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"])
        assert e.snapshot_interval == 100

    def test_with_multiple_events(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited", "Withdrawn", "Transferred"])
        assert "Deposited" in e.events
        assert "Withdrawn" in e.events
        assert "Transferred" in e.events

    def test_strategy_snapshot(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"])
        assert e.eventing_strategy == EventTypeingStrategy.SNAPSHOT

    def test_no_version(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"], versioned=False)
        assert e.versioned is False

    def test_no_snapshot(self):
        e = EventSourcedAggregateRecipe("BankAccount", events=["Deposited"], snapshot_interval=0)
        assert e.snapshot_interval == 0


# ===========================================================================
# SagaRecipe
# ===========================================================================

class TestSagaRecipe:
    """Tests cho SagaRecipe."""

    def test_minimal(self):
        s = SagaRecipe("OrderFulfillment")
        assert isinstance(s, Saga)
        assert s.id == "OrderFulfillment"

    def test_with_steps(self):
        s = SagaRecipe("OrderFulfillment", steps=[
            SagaStep(name="ReserveInventory", action="reserve", compensating_action="release"),
            SagaStep(name="ProcessPayment", action="charge", compensating_action="refund"),
        ])
        assert len(s.steps) == 2
        assert s.steps[0].name == "ReserveInventory"
        assert s.steps[1].compensating_action == "refund"

    def test_empty_steps(self):
        s = SagaRecipe("OrderFulfillment")
        assert len(s.steps) == 0

    def test_default_orchestration(self):
        s = SagaRecipe("OrderFulfillment")
        assert s.orchestration == SagaOrchestration.ORCHESTRATION

    def test_default_timeout(self):
        s = SagaRecipe("OrderFulfillment")
        assert s.timeout_seconds == 3600


# ===========================================================================
# ProjectionRecipe
# ===========================================================================

class TestProjectionRecipe:
    """Tests cho ProjectionRecipe."""

    def test_minimal(self):
        p = ProjectionRecipe("OrderSummary", source_events=["OrderPlaced"])
        assert isinstance(p, Projection)
        assert p.id == "OrderSummary"

    def test_source_aggregate_derived(self):
        p = ProjectionRecipe("OrderSummary", source_aggregate="Order", source_events=["OrderPlaced"])
        assert p.source_aggregate == "Order"

    def test_with_fields(self):
        p = ProjectionRecipe("OrderSummary", source_events=["OrderPlaced"], fields=[
            EntityField(name="total_amount", field_type=EntityFieldType.DECIMAL),
        ])
        assert len(p.fields) == 1
        assert p.fields[0].name == "total_amount"

    def test_default_projection_type(self):
        p = ProjectionRecipe("OrderSummary", source_events=["OrderPlaced"])
        assert p.projection_type == ProjectionType.DENORMALIZED

    def test_materialized_view_type(self):
        p = ProjectionRecipe("OrderSummary", source_events=["OrderPlaced"],
                              projection_type=ProjectionType.MATERIALIZED_VIEW)
        assert p.projection_type == ProjectionType.MATERIALIZED_VIEW

    def test_default_source_aggregate(self):
        p = ProjectionRecipe("OrderSummary", source_events=["OrderPlaced"])
        assert p.source_aggregate == "Order"


# ===========================================================================
# ValueObjectRecipe
# ===========================================================================

class TestValueObjectRecipe:
    """Tests cho ValueObjectRecipe."""

    def test_minimal(self):
        v = ValueObjectRecipe("Money")
        assert isinstance(v, ValueObject)
        assert v.id == "Money"

    def test_with_fields(self):
        v = ValueObjectRecipe("Money", fields=[
            VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
            VOField(name="currency", field_type=VOFieldType.STRING, required=True),
        ])
        field_names = [f.name for f in v.fields]
        assert "amount" in field_names
        assert "currency" in field_names

    def test_with_description(self):
        v = ValueObjectRecipe("Money", description="Represents monetary value")
        assert v.description == "Represents monetary value"

    def test_default_description(self):
        v = ValueObjectRecipe("Money")
        assert "Money" in v.description


# ===========================================================================
# Cross-recipe integration
# ===========================================================================

class TestRecipeIntegration:
    """Integration tests cho recipe ecosystem."""

    def test_command_writes_to_aggregate(self):
        """Command từ recipe phải có writes_to đúng aggregate."""
        cmd = CQRSCommandRecipe("CreateOrder", entity="Order")
        assert "Order" in cmd.writes_to

    def test_query_reads_from_aggregate(self):
        """Query từ recipe phải có reads_from đúng aggregate."""
        qry = CQRSQueryRecipe("ListOrders", entity="Order")
        assert qry.reads_from == "Order"

    def test_recipe_can_chain_to_saga(self):
        """Multiple commands từ recipes có thể tham gia saga."""
        saga = SagaRecipe("OrderFulfillment", steps=[
            SagaStep(name="CreateOrder", action="CreateOrder", compensating_action="CancelOrder"),
            SagaStep(name="ReserveInventory", action="ReserveInventory", compensating_action="ReleaseInventory"),
        ])
        assert len(saga.steps) == 2

    def test_all_10_recipes_importable(self):
        """Tất cả 10 recipes phải importable từ __init__."""
        from midicoder.packs.cp_base_domain_model import (
            SimpleEntityRecipe, AggregateRootRecipe, TemporalEntityRecipe,
            CQRSCommandRecipe, CQRSQueryRecipe, EventSourcedAggregateRecipe,
            SagaRecipe, PolymorphicEntityRecipe, ProjectionRecipe, ValueObjectRecipe,
        )
        assert SimpleEntityRecipe is not None
        assert AggregateRootRecipe is not None
        assert TemporalEntityRecipe is not None
        assert CQRSCommandRecipe is not None
        assert CQRSQueryRecipe is not None
        assert EventSourcedAggregateRecipe is not None
        assert SagaRecipe is not None
        assert PolymorphicEntityRecipe is not None
        assert ProjectionRecipe is not None
        assert ValueObjectRecipe is not None


# ===========================================================================
# Gap-Filling Tests: recipes.py uncovered lines
# ===========================================================================


class TestAuditFieldsHelper:
    """Tests cho _audit_fields() — line 143."""

    def test_audit_fields_returns_three_fields(self):
        """Test: _audit_fields trả về 3 fields: tenant_id, created_at, updated_at."""
        from midicoder.packs.cp_base_domain_model.recipes import _audit_fields

        fields = _audit_fields()
        assert len(fields) == 3
        names = [f.name for f in fields]
        assert "tenant_id" in names
        assert "created_at" in names
        assert "updated_at" in names


class TestCQRSCommandRecipeCustomCategory:
    """Tests cho CQRSCommandRecipe — branch 395→398 (custom category, no effect_type match)."""

    def test_custom_category_no_record_effect(self):
        """Test: category='custom' không tạo create/update/delete effect."""
        c = CQRSCommandRecipe("CustomAction", entity="Order", category="custom")
        # No create/update/delete effect should be added for custom category
        record_effects = [e for e in c.effects if e.effect_type in ("create_record", "update_record", "delete_record")]
        assert len(record_effects) == 0
        assert c.category == "custom"


class TestPolymorphicEntityRecipeWithBaseFields:
    """Tests cho PolymorphicEntityRecipe — line 621 (if base_fields branch)."""

    def test_with_base_fields(self):
        """Test: PolymorphicEntityRecipe với base_fields — field được extend."""
        p = PolymorphicEntityRecipe(
            "Payment",
            base_fields=[
                EntityField(name="amount", field_type=EntityFieldType.DECIMAL, nullable=False),
            ],
            subtypes=[],
        )
        base_field_names = [f.name for f in p.base_fields]
        assert "id" in base_field_names
        assert "amount" in base_field_names
        assert "payment_type" in base_field_names  # discriminator


class TestGlobalErrorHandlerRecipe:
    """Tests cho GlobalErrorHandlerRecipe — lines 775-860 (entire function)."""

    def test_minimal_recipe(self):
        """Test: GlobalErrorHandlerRecipe với params tối thiểu."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("AppHandler")

        assert "handler" in result
        assert "mappers" in result
        assert "logging_config" in result
        assert "notification_config" in result

    def test_handler_defaults(self):
        """Test: Handler có đúng defaults."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe
        from midicoder.packs.cp_base_domain_model.error_handler_models import (
            ErrorHandlingStrategy,
            ErrorLevel,
        )

        result = GlobalErrorHandlerRecipe("TestHandler")
        h = result["handler"]

        assert h.id == "testhandler"
        assert h.name == "TestHandler"
        assert h.strategy == ErrorHandlingStrategy.FALLBACK
        assert h.log_level == ErrorLevel.ERROR
        assert h.include_stack_trace is False

    def test_common_mappers_included(self):
        """Test: common_mappers=True tạo 6 mappers phổ biến."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("TestHandler", common_mappers=True)
        mappers = result["mappers"]

        assert len(mappers) == 6
        exc_types = [m.exception_type for m in mappers]
        assert "ValueError" in exc_types
        assert "KeyError" in exc_types
        assert "PermissionError" in exc_types
        assert "TypeError" in exc_types
        assert "ConnectionError" in exc_types
        assert "TimeoutError" in exc_types

    def test_no_common_mappers(self):
        """Test: common_mappers=False không tạo mappers."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("TestHandler", common_mappers=False)
        assert len(result["mappers"]) == 0

    def test_with_logging_true(self):
        """Test: with_logging=True tạo ErrorLoggingConfig."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("TestHandler", with_logging=True)
        assert result["logging_config"] is not None
        assert result["logging_config"].log_format == "structured"
        assert "password" in result["logging_config"].redact_fields

    def test_with_logging_false(self):
        """Test: with_logging=False không tạo logging config."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("TestHandler", with_logging=False)
        assert result["logging_config"] is None

    def test_with_notification_true(self):
        """Test: with_notification=True tạo ErrorNotificationConfig."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe(
            "TestHandler",
            with_notification=True,
            sentry_dsn="https://key@sentry.io/1",
        )
        assert result["notification_config"] is not None
        assert result["notification_config"].include_sentry_integration is True

    def test_with_notification_false(self):
        """Test: with_notification=False không tạo notification config."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe("TestHandler", with_notification=False)
        assert result["notification_config"] is None

    def test_custom_error_pages(self):
        """Test: custom_error_pages được forward đúng."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe

        result = GlobalErrorHandlerRecipe(
            "TestHandler",
            custom_error_pages={404: "/404", 500: "/500"},
        )
        assert result["handler"].custom_error_pages[404] == "/404"
        assert result["handler"].custom_error_pages[500] == "/500"

    def test_custom_strategy_and_level(self):
        """Test: Custom strategy và log_level."""
        from midicoder.packs.cp_base_domain_model import GlobalErrorHandlerRecipe
        from midicoder.packs.cp_base_domain_model.error_handler_models import (
            ErrorHandlingStrategy,
            ErrorLevel,
        )

        result = GlobalErrorHandlerRecipe(
            "TestHandler",
            strategy=ErrorHandlingStrategy.CIRCUIT_BREAKER,
            log_level=ErrorLevel.CRITICAL,
        )
        assert result["handler"].strategy == ErrorHandlingStrategy.CIRCUIT_BREAKER
        assert result["handler"].log_level == ErrorLevel.CRITICAL
