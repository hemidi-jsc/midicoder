"""
Unit Tests cho Capability Params.

Kiểm tra behavior của TypedDict models cho capability params:
- BaseCapabilityParams
- AuthorizedMutationParams
- AuthorizedQueryParams
- EventHandlerParams
- ScheduledTaskParams
- WorkflowDefinitionParams
- RuleEngineParams
- AggregationParams
- SearchIndexParams
- CacheStrategyParams
- NotificationParams
- OutboundIntegrationParams
- InboundIntegrationParams
- MessageQueueParams
- AuditLogParams
- RateLimitingParams
- DataExportParams
- DataImportParams
- BatchJobParams
- DataRetentionParams
- MonitoringParams

Tests tuân thủ TDD, kiểm tra type structure và validation.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from typing_extensions import TypedDict

from midicoder.contracts.capability_params import (
    BaseCapabilityParams,
    AuthorizedMutationParams,
    AuthorizedQueryParams,
    EventHandlerParams,
    ScheduledTaskParams,
    WorkflowDefinitionParams,
    RuleEngineParams,
    AggregationParams,
    SearchIndexParams,
    CacheStrategyParams,
    NotificationParams,
    OutboundIntegrationParams,
    InboundIntegrationParams,
    MessageQueueParams,
    AuditLogParams,
    RateLimitingParams,
    DataExportParams,
    DataImportParams,
    BatchJobParams,
    DataRetentionParams,
    MonitoringParams,
    CapabilityParams,
)


# ============================================================================
# BaseCapabilityParams Tests (8 tests)
# ============================================================================


class TestBaseCapabilityParams:
    """Tests cho BaseCapabilityParams TypedDict."""

    def test_base_params_empty(self):
        """Kiểm tra BaseCapabilityParams có thể rỗng."""
        params: BaseCapabilityParams = {}
        assert params == {}

    def test_base_params_with_description(self):
        """Kiểm tra BaseCapabilityParams với description."""
        params: BaseCapabilityParams = {"description": "Test capability"}
        assert params["description"] == "Test capability"

    def test_base_params_with_tags(self):
        """Kiểm tra BaseCapabilityParams với tags."""
        params: BaseCapabilityParams = {"tags": ["p0", "critical"]}
        assert params["tags"] == ["p0", "critical"]

    def test_base_params_with_enabled(self):
        """Kiểm tra BaseCapabilityParams với enabled."""
        params: BaseCapabilityParams = {"enabled": True}
        assert params["enabled"] is True

    def test_base_params_with_all_fields(self):
        """Kiểm tra BaseCapabilityParams với tất cả fields."""
        params: BaseCapabilityParams = {
            "description": "Test capability",
            "tags": ["p0", "test"],
            "enabled": True,
        }
        assert params["description"] == "Test capability"
        assert params["tags"] == ["p0", "test"]
        assert params["enabled"] is True

    def test_base_params_tags_is_list(self):
        """Kiểm tra tags phải là list."""
        params: BaseCapabilityParams = {"tags": ["tag1", "tag2", "tag3"]}
        assert isinstance(params["tags"], list)
        assert len(params["tags"]) == 3

    def test_base_params_description_is_string(self):
        """Kiểm tra description là string."""
        params: BaseCapabilityParams = {"description": "A test capability"}
        assert isinstance(params["description"], str)

    def test_base_params_enabled_is_bool(self):
        """Kiểm tra enabled là boolean."""
        params: BaseCapabilityParams = {"enabled": False}
        assert isinstance(params["enabled"], bool)
        assert params["enabled"] is False


# ============================================================================
# AuthorizedMutationParams Tests (12 tests)
# ============================================================================


class TestAuthorizedMutationParams:
    """Tests cho AuthorizedMutationParams TypedDict."""

    def test_mutation_params_minimal(self):
        """Kiểm tra AuthorizedMutationParams với required fields."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        assert params["actor_role"] == "staff"
        assert params["permission"] == "order.create"
        assert params["writes"] == ["Order"]
        assert params["tenant_scope"] == "tenant_isolated"

    def test_mutation_params_with_reads(self):
        """Kiểm tra với optional reads field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "reads": ["Customer", "Product"],
        }
        assert params["reads"] == ["Customer", "Product"]

    def test_mutation_params_with_transaction(self):
        """Kiểm tra với transaction field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "transaction": "required",
        }
        assert params["transaction"] == "required"

    def test_mutation_params_with_errors(self):
        """Kiểm tra với errors field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "errors": ["ORDER_NOT_FOUND", "INSUFFICIENT_STOCK"],
        }
        assert params["errors"] == ["ORDER_NOT_FOUND", "INSUFFICIENT_STOCK"]

    def test_mutation_params_with_emits(self):
        """Kiểm tra với emits field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "emits": ["OrderCreated"],
        }
        assert params["emits"] == ["OrderCreated"]

    def test_mutation_params_with_guards(self):
        """Kiểm tra với guards field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "guards": [{"type": "inventory_check", "entity": "Product"}],
        }
        assert len(params["guards"]) == 1

    def test_mutation_params_with_effects(self):
        """Kiểm tra với effects field."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "effects": [{"type": "notification", "template": "order_created"}],
        }
        assert len(params["effects"]) == 1

    def test_mutation_params_with_schemas(self):
        """Kiểm tra với input/output schemas."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
        }
        assert "input_schema" in params
        assert "output_schema" in params

    def test_mutation_params_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order", "OrderItem"],
            "tenant_scope": "tenant_isolated",
            "reads": ["Customer", "Product", "Inventory"],
            "transaction": "required",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "errors": ["ORDER_NOT_FOUND"],
            "guards": [{"type": "check"}],
            "effects": [{"type": "notify"}],
            "emits": ["OrderCreated"],
            "description": "Create order",
            "tags": ["order", "write"],
            "enabled": True,
        }
        assert params["actor_role"] == "staff"
        assert len(params["writes"]) == 2
        assert params["enabled"] is True

    def test_mutation_params_cross_tenant_scope(self):
        """Kiểm tra với cross-tenant scope."""
        params: AuthorizedMutationParams = {
            "actor_role": "admin",
            "permission": "order.manage",
            "writes": ["Order"],
            "tenant_scope": "global",
        }
        assert params["tenant_scope"] == "global"

    def test_mutation_params_transaction_allowed(self):
        """Kiểm tra với transaction allowed."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "order.update",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "transaction": "allowed",
        }
        assert params["transaction"] == "allowed"

    def test_mutation_params_multiple_writes(self):
        """Kiểm tra với multiple write entities."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "bulk.order.create",
            "writes": ["Order", "OrderItem", "Payment"],
            "tenant_scope": "tenant_isolated",
        }
        assert len(params["writes"]) == 3


# ============================================================================
# AuthorizedQueryParams Tests (12 tests)
# ============================================================================


class TestAuthorizedQueryParams:
    """Tests cho AuthorizedQueryParams TypedDict."""

    def test_query_params_minimal(self):
        """Kiểm tra AuthorizedQueryParams với required fields."""
        params: AuthorizedQueryParams = {"reads": ["Order"]}
        assert params["reads"] == ["Order"]

    def test_query_params_with_permission(self):
        """Kiểm tra với required_permission."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "required_permission": "order.read",
        }
        assert params["required_permission"] == "order.read"

    def test_query_params_with_tenant_scope(self):
        """Kiểm tra với tenant_scope."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        assert params["tenant_scope"] == "tenant_isolated"

    def test_query_params_with_schemas(self):
        """Kiểm tra với input/output schemas."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "input_schema": {"type": "object", "properties": {"page": {"type": "int"}}},
            "output_schema": {"type": "object", "properties": {"items": {"type": "array"}}},
        }
        assert "input_schema" in params
        assert "output_schema" in params

    def test_query_params_with_cache_config(self):
        """Kiểm tra với cache_config."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "cache_config": {"ttl_seconds": 300, "key_pattern": "order:{id}"},
        }
        assert params["cache_config"]["ttl_seconds"] == 300

    def test_query_params_multiple_reads(self):
        """Kiểm tra với multiple read entities."""
        params: AuthorizedQueryParams = {
            "reads": ["Order", "OrderItem", "Customer"],
        }
        assert len(params["reads"]) == 3

    def test_query_params_with_description(self):
        """Kiểm tra với description từ base."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "description": "Get order details",
        }
        assert params["description"] == "Get order details"

    def test_query_params_no_auth_required(self):
        """Kiểm tra query không yêu cầu permission."""
        params: AuthorizedQueryParams = {"reads": ["PublicData"]}
        assert "required_permission" not in params

    def test_query_params_global_tenant_scope(self):
        """Kiểm tra với global tenant scope."""
        params: AuthorizedQueryParams = {
            "reads": ["Config"],
            "tenant_scope": "global",
        }
        assert params["tenant_scope"] == "global"

    def test_query_params_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "required_permission": "order.read",
            "tenant_scope": "tenant_isolated",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "cache_config": {"ttl_seconds": 300},
            "description": "List orders",
            "tags": ["query", "order"],
            "enabled": True,
        }
        assert params["enabled"] is True
        assert params["tags"] == ["query", "order"]

    def test_query_params_pagination_schema(self):
        """Kiểm tra với pagination schema."""
        params: AuthorizedQueryParams = {
            "reads": ["Order"],
            "input_schema": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1},
                    "per_page": {"type": "integer", "default": 20},
                    "sort": {"type": "string"},
                    "filter": {"type": "object"},
                },
            },
        }
        assert "properties" in params["input_schema"]

    def test_query_params_cache_ttl_zero(self):
        """Kiểm tra với cache TTL 0 (no cache)."""
        params: AuthorizedQueryParams = {
            "reads": ["LiveStatus"],
            "cache_config": {"ttl_seconds": 0},
        }
        assert params["cache_config"]["ttl_seconds"] == 0


# ============================================================================
# EventHandlerParams Tests (10 tests)
# ============================================================================


class TestEventHandlerParams:
    """Tests cho EventHandlerParams TypedDict."""

    def test_event_handler_minimal(self):
        """Kiểm tra EventHandlerParams với required fields."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
        }
        assert params["event_type"] == "OrderCreated"
        assert params["handler_id"] == "process_order"

    def test_event_handler_with_retry_policy(self):
        """Kiểm tra với retry_policy."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        }
        assert params["retry_policy"]["max_retries"] == 3

    def test_event_handler_with_timeout(self):
        """Kiểm tra với timeout_ms."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "timeout_ms": 30000,
        }
        assert params["timeout_ms"] == 30000

    def test_event_handler_async_processing(self):
        """Kiểm tra với async_processing."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "async_processing": True,
        }
        assert params["async_processing"] is True

    def test_event_handler_with_dlq(self):
        """Kiểm tra với dead_letter_queue."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "dead_letter_queue": {"topic": "dlq.orders", "max_age_hours": 72},
        }
        assert "dead_letter_queue" in params

    def test_event_handler_exponential_backoff(self):
        """Kiểm tra với exponential backoff policy."""
        params: EventHandlerParams = {
            "event_type": "PaymentFailed",
            "handler_id": "retry_payment",
            "retry_policy": {
                "max_retries": 5,
                "backoff_multiplier": 2,
                "initial_delay_ms": 1000,
            },
        }
        assert params["retry_policy"]["backoff_multiplier"] == 2

    def test_event_handler_sync_processing(self):
        """Kiểm tra với sync processing (default)."""
        params: EventHandlerParams = {
            "event_type": "CriticalAlert",
            "handler_id": "handle_alert",
            "async_processing": False,
        }
        assert params["async_processing"] is False

    def test_event_handler_with_description(self):
        """Kiểm tra với description."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "description": "Process new order",
            "tags": ["order", "async"],
        }
        assert params["description"] == "Process new order"

    def test_event_handler_zero_timeout(self):
        """Kiểm tra với zero timeout (no limit)."""
        params: EventHandlerParams = {
            "event_type": "ScheduledReport",
            "handler_id": "generate_report",
            "timeout_ms": 0,
        }
        assert params["timeout_ms"] == 0

    def test_event_handler_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: EventHandlerParams = {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "retry_policy": {"max_retries": 3},
            "timeout_ms": 30000,
            "async_processing": True,
            "dead_letter_queue": {"topic": "dlq"},
            "description": "Handle order",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# ScheduledTaskParams Tests (10 tests)
# ============================================================================


class TestScheduledTaskParams:
    """Tests cho ScheduledTaskParams TypedDict."""

    def test_scheduled_task_minimal(self):
        """Kiểm tra ScheduledTaskParams với required fields."""
        params: ScheduledTaskParams = {
            "task_id": "generate_report",
            "cron_expression": "0 2 * * *",
        }
        assert params["task_id"] == "generate_report"
        assert params["cron_expression"] == "0 2 * * *"

    def test_scheduled_task_with_timezone(self):
        """Kiểm tra với timezone."""
        params: ScheduledTaskParams = {
            "task_id": "generate_report",
            "cron_expression": "0 2 * * *",
            "timezone": "Asia/Ho Chi Minh",
        }
        assert params["timezone"] == "Asia/Ho Chi Minh"

    def test_scheduled_task_with_max_duration(self):
        """Kiểm tra với max_duration_ms."""
        params: ScheduledTaskParams = {
            "task_id": "heavy_computation",
            "cron_expression": "0 0 * * 0",
            "max_duration_ms": 3600000,  # 1 hour
        }
        assert params["max_duration_ms"] == 3600000

    def test_scheduled_task_with_retry_policy(self):
        """Kiểm tra với retry_policy."""
        params: ScheduledTaskParams = {
            "task_id": "send_notifications",
            "cron_expression": "0 * * * *",
            "retry_policy": {"max_retries": 3},
        }
        assert params["retry_policy"]["max_retries"] == 3

    def test_scheduled_task_with_concurrency(self):
        """Kiểm tra với concurrency settings."""
        params: ScheduledTaskParams = {
            "task_id": "process_batch",
            "cron_expression": "0 0 * * *",
            "concurrency": {"max_parallel": 4, "queue_size": 100},
        }
        assert params["concurrency"]["max_parallel"] == 4

    def test_scheduled_task_minute_interval(self):
        """Kiểm tra với minute interval cron."""
        params: ScheduledTaskParams = {
            "task_id": "health_check",
            "cron_expression": "* * * * *",
        }
        assert params["cron_expression"] == "* * * * *"

    def test_scheduled_task_hourly(self):
        """Kiểm tra với hourly cron."""
        params: ScheduledTaskParams = {
            "task_id": "hourly_sync",
            "cron_expression": "0 * * * *",
            "timezone": "UTC",
        }
        assert params["cron_expression"] == "0 * * * *"

    def test_scheduled_task_weekly(self):
        """Kiểm tra với weekly cron."""
        params: ScheduledTaskParams = {
            "task_id": "weekly_report",
            "cron_expression": "0 0 * * 0",
        }
        assert params["cron_expression"] == "0 0 * * 0"

    def test_scheduled_task_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: ScheduledTaskParams = {
            "task_id": "daily_backup",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
            "max_duration_ms": 7200000,
            "retry_policy": {"max_retries": 2},
            "concurrency": {"max_parallel": 1},
            "description": "Daily backup",
            "enabled": True,
        }
        assert params["enabled"] is True

    def test_scheduled_task_no_timezone(self):
        """Kiểm tra không có timezone (default UTC)."""
        params: ScheduledTaskParams = {
            "task_id": "simple_task",
            "cron_expression": "0 0 * * *",
        }
        assert "timezone" not in params


# ============================================================================
# WorkflowDefinitionParams Tests (12 tests)
# ============================================================================


class TestWorkflowDefinitionParams:
    """Tests cho WorkflowDefinitionParams TypedDict."""

    def test_workflow_minimal(self):
        """Kiểm tra WorkflowDefinitionParams với required fields."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "approved"],
            "transitions": [{"from": "draft", "to": "approved"}],
            "start_state": "draft",
        }
        assert params["start_state"] == "draft"
        assert len(params["states"]) == 2

    def test_workflow_with_end_states(self):
        """Kiểm tra với end_states."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "approved", "rejected"],
            "transitions": [],
            "start_state": "draft",
            "end_states": ["approved", "rejected"],
        }
        assert params["end_states"] == ["approved", "rejected"]

    def test_workflow_with_compensation(self):
        """Kiểm tra với compensation."""
        params: WorkflowDefinitionParams = {
            "states": ["pending", "completed"],
            "transitions": [],
            "start_state": "pending",
            "compensation": [{"action": "rollback_order", "trigger": "failure"}],
        }
        assert len(params["compensation"]) == 1

    def test_workflow_with_human_tasks(self):
        """Kiểm tra với human_tasks."""
        params: WorkflowDefinitionParams = {
            "states": ["submitted", "approved", "rejected"],
            "transitions": [],
            "start_state": "submitted",
            "human_tasks": [
                {
                    "id": "manager_approval",
                    "role": "manager",
                    "state": "submitted",
                }
            ],
        }
        assert len(params["human_tasks"]) == 1

    def test_workflow_with_timers(self):
        """Kiểm tra với timers."""
        params: WorkflowDefinitionParams = {
            "states": ["pending", "expired"],
            "transitions": [],
            "start_state": "pending",
            "timers": [
                {"id": "expiry_timer", "duration_ms": 86400000, "action": "expire"}
            ],
        }
        assert len(params["timers"]) == 1

    def test_workflow_multiple_transitions(self):
        """Kiểm tra với multiple transitions."""
        params: WorkflowDefinitionParams = {
            "states": ["a", "b", "c"],
            "transitions": [
                {"from": "a", "to": "b"},
                {"from": "b", "to": "c"},
                {"from": "a", "to": "c"},
            ],
            "start_state": "a",
        }
        assert len(params["transitions"]) == 3

    def test_workflow_with_guards_in_transitions(self):
        """Kiểm tra transitions với guards."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "review", "approved"],
            "transitions": [
                {
                    "from": "draft",
                    "to": "review",
                    "guard": {"condition": "validation_passed"},
                }
            ],
            "start_state": "draft",
        }
        assert "guard" in params["transitions"][0]

    def test_workflow_state_machine(self):
        """Kiểm tra workflow như state machine."""
        params: WorkflowDefinitionParams = {
            "states": ["new", "processing", "done"],
            "transitions": [
                {"from": "new", "to": "processing"},
                {"from": "processing", "to": "done"},
            ],
            "start_state": "new",
            "end_states": ["done"],
        }
        assert params["start_state"] == "new"
        assert params["end_states"] == ["done"]

    def test_workflow_approvals(self):
        """Kiểm tra workflow với approval process."""
        params: WorkflowDefinitionParams = {
            "states": ["pending", "approved", "rejected"],
            "transitions": [],
            "start_state": "pending",
            "end_states": ["approved", "rejected"],
            "human_tasks": [
                {"id": "approve", "role": "manager"},
                {"id": "reject", "role": "manager"},
            ],
        }
        assert len(params["human_tasks"]) == 2

    def test_workflow_with_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "review", "approved"],
            "transitions": [{"from": "draft", "to": "review"}],
            "start_state": "draft",
            "end_states": ["approved"],
            "compensation": [{"action": "revert"}],
            "human_tasks": [{"id": "review"}],
            "timers": [{"id": "timeout"}],
            "description": "Approval workflow",
            "enabled": True,
        }
        assert params["enabled"] is True

    def test_workflow_single_state(self):
        """Kiểm tra workflow với single state."""
        params: WorkflowDefinitionParams = {
            "states": ["active"],
            "transitions": [],
            "start_state": "active",
            "end_states": ["active"],
        }
        assert len(params["states"]) == 1

    def test_workflow_complex_transitions(self):
        """Kiểm tra complex transitions."""
        params: WorkflowDefinitionParams = {
            "states": ["order", "payment", "shipping", "delivered"],
            "transitions": [
                {"from": "order", "to": "payment", "event": "order_placed"},
                {"from": "payment", "to": "shipping", "event": "payment_confirmed"},
                {"from": "shipping", "to": "delivered", "event": "delivered"},
            ],
            "start_state": "order",
        }
        assert len(params["transitions"]) == 3


# ============================================================================
# RuleEngineParams Tests (8 tests)
# ============================================================================


class TestRuleEngineParams:
    """Tests cho RuleEngineParams TypedDict."""

    def test_rule_engine_minimal(self):
        """Kiểm tra RuleEngineParams với required fields."""
        params: RuleEngineParams = {"rules": [{"id": "rule1"}]}
        assert len(params["rules"]) == 1

    def test_rule_engine_with_priority(self):
        """Kiểm tra với priority."""
        params: RuleEngineParams = {
            "rules": [{"id": "rule1"}],
            "priority": 100,
        }
        assert params["priority"] == 100

    def test_rule_engine_eval_order_sequential(self):
        """Kiểm tra với sequential eval_order."""
        params: RuleEngineParams = {
            "rules": [{"id": "rule1"}],
            "eval_order": "sequential",
        }
        assert params["eval_order"] == "sequential"

    def test_rule_engine_eval_order_parallel(self):
        """Kiểm tra với parallel eval_order."""
        params: RuleEngineParams = {
            "rules": [{"id": "rule1"}],
            "eval_order": "parallel",
        }
        assert params["eval_order"] == "parallel"

    def test_rule_engine_short_circuit(self):
        """Kiểm tra với short_circuit."""
        params: RuleEngineParams = {
            "rules": [{"id": "rule1"}],
            "short_circuit": True,
        }
        assert params["short_circuit"] is True

    def test_rule_engine_with_conditions(self):
        """Kiểm tra rules với conditions."""
        params: RuleEngineParams = {
            "rules": [
                {
                    "id": "discount",
                    "condition": {"field": "total", "operator": ">", "value": 100},
                    "action": {"type": "discount", "value": 10},
                }
            ],
        }
        assert "condition" in params["rules"][0]

    def test_rule_engine_multiple_rules(self):
        """Kiểm tra với multiple rules."""
        params: RuleEngineParams = {
            "rules": [
                {"id": "rule1", "condition": {}},
                {"id": "rule2", "condition": {}},
                {"id": "rule3", "condition": {}},
            ],
        }
        assert len(params["rules"]) == 3

    def test_rule_engine_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: RuleEngineParams = {
            "rules": [{"id": "rule1"}],
            "priority": 100,
            "eval_order": "sequential",
            "short_circuit": True,
            "description": "Discount rules",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# AggregationParams Tests (8 tests)
# ============================================================================


class TestAggregationParams:
    """Tests cho AggregationParams TypedDict."""

    def test_aggregation_minimal(self):
        """Kiểm tra AggregationParams với required fields."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["customer_id"],
            "aggregations": [{"name": "total", "operation": "sum", "field": "amount"}],
        }
        assert params["source_entities"] == ["Order"]
        assert params["group_by"] == ["customer_id"]

    def test_aggregation_with_filters(self):
        """Kiểm tra với filters."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["status"],
            "aggregations": [{"name": "count", "operation": "count"}],
            "filters": {"status": ["completed", "shipped"]},
        }
        assert "filters" in params

    def test_aggregation_with_output_schema(self):
        """Kiểm tra với output_schema."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["category"],
            "aggregations": [{"name": "total", "operation": "sum"}],
            "output_schema": {"type": "object", "properties": {"total": {"type": "number"}}},
        }
        assert "output_schema" in params

    def test_aggregation_multiple_operations(self):
        """Kiểm tra với multiple aggregation operations."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["customer_id"],
            "aggregations": [
                {"name": "total", "operation": "sum", "field": "amount"},
                {"name": "avg", "operation": "avg", "field": "amount"},
                {"name": "count", "operation": "count"},
                {"name": "min", "operation": "min", "field": "amount"},
                {"name": "max", "operation": "max", "field": "amount"},
            ],
        }
        assert len(params["aggregations"]) == 5

    def test_aggregation_multiple_entities(self):
        """Kiểm tra với multiple source entities."""
        params: AggregationParams = {
            "source_entities": ["Order", "OrderItem"],
            "group_by": ["product_id"],
            "aggregations": [{"name": "qty", "operation": "sum", "field": "quantity"}],
        }
        assert len(params["source_entities"]) == 2

    def test_aggregation_multiple_group_by(self):
        """Kiểm tra với multiple group_by fields."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["year", "month", "category"],
            "aggregations": [{"name": "revenue", "operation": "sum", "field": "total"}],
        }
        assert len(params["group_by"]) == 3

    def test_aggregation_with_where_filter(self):
        """Kiểm tra với complex where filter."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["status"],
            "aggregations": [{"name": "count", "operation": "count"}],
            "filters": {
                "where": {
                    "and": [{"field": "status", "operator": "in", "value": ["completed"]}]
                }
            },
        }
        assert "where" in params["filters"]

    def test_aggregation_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["category"],
            "aggregations": [{"name": "total", "operation": "sum"}],
            "filters": {"status": "completed"},
            "output_schema": {"type": "object"},
            "description": "Sales aggregation",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# SearchIndexParams Tests (8 tests)
# ============================================================================


class TestSearchIndexParams:
    """Tests cho SearchIndexParams TypedDict."""

    def test_search_index_minimal(self):
        """Kiểm tra SearchIndexParams với required fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name", "description"],
        }
        assert params["indexed_entities"] == ["Product"]
        assert params["search_fields"] == ["name", "description"]

    def test_search_index_with_filter_fields(self):
        """Kiểm tra với filter_fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name"],
            "filter_fields": ["category_id", "price", "in_stock"],
        }
        assert params["filter_fields"] == ["category_id", "price", "in_stock"]

    def test_search_index_with_sort_fields(self):
        """Kiểm tra với sort_fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name"],
            "sort_fields": ["price", "created_at", "popularity"],
        }
        assert "popularity" in params["sort_fields"]

    def test_search_index_with_analyzers(self):
        """Kiểm tra với analyzers."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name"],
            "analyzers": {"language": "vi", "stemmer": True},
        }
        assert params["analyzers"]["language"] == "vi"

    def test_search_index_multiple_entities(self):
        """Kiểm tra với multiple indexed entities."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product", "Category", "Brand"],
            "search_fields": ["name", "sku"],
        }
        assert len(params["indexed_entities"]) == 3

    def test_search_index_facet_fields(self):
        """Kiểm tra với facet fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name"],
            "filter_fields": ["category", "brand", "price_range"],
        }
        assert len(params["filter_fields"]) == 3

    def test_search_index_full_text_fields(self):
        """Kiểm tra với full-text search fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Article"],
            "search_fields": ["title", "content", "tags", "author"],
            "analyzers": {"language": "en", "stopwords": True},
        }
        assert len(params["search_fields"]) == 4

    def test_search_index_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product"],
            "search_fields": ["name", "description"],
            "filter_fields": ["category"],
            "sort_fields": ["price"],
            "analyzers": {"language": "en"},
            "description": "Product search",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# CacheStrategyParams Tests (8 tests)
# ============================================================================


class TestCacheStrategyParams:
    """Tests cho CacheStrategyParams TypedDict."""

    def test_cache_strategy_minimal(self):
        """Kiểm tra CacheStrategyParams với required fields."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 300,
        }
        assert params["cache_type"] == "redis"
        assert params["ttl_seconds"] == 300

    def test_cache_strategy_with_invalidation(self):
        """Kiểm tra với invalidation_triggers."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 300,
            "invalidation_triggers": ["ProductUpdated", "ProductDeleted"],
        }
        assert len(params["invalidation_triggers"]) == 2

    def test_cache_strategy_with_key_pattern(self):
        """Kiểm tra với key_pattern."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 300,
            "key_pattern": "product:{id}",
        }
        assert params["key_pattern"] == "product:{id}"

    def test_cache_strategy_with_max_size(self):
        """Kiểm tra với max_size."""
        params: CacheStrategyParams = {
            "cache_type": "memory",
            "ttl_seconds": 600,
            "max_size": 10000,
        }
        assert params["max_size"] == 10000

    def test_cache_strategy_memory_type(self):
        """Kiểm tra với memory cache."""
        params: CacheStrategyParams = {
            "cache_type": "memory",
            "ttl_seconds": 300,
            "max_size": 1000,
        }
        assert params["cache_type"] == "memory"

    def test_cache_strategy_memcached_type(self):
        """Kiểm tra với memcached cache."""
        params: CacheStrategyParams = {
            "cache_type": "memcached",
            "ttl_seconds": 600,
        }
        assert params["cache_type"] == "memcached"

    def test_cache_strategy_zero_ttl(self):
        """Kiểm tra với zero TTL (permanent cache)."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 0,
        }
        assert params["ttl_seconds"] == 0

    def test_cache_strategy_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 300,
            "invalidation_triggers": ["Updated"],
            "key_pattern": "item:{id}",
            "max_size": 10000,
            "description": "Product cache",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# NotificationParams Tests (8 tests)
# ============================================================================


class TestNotificationParams:
    """Tests cho NotificationParams TypedDict."""

    def test_notification_minimal(self):
        """Kiểm tra NotificationParams với required fields."""
        params: NotificationParams = {"channels": ["email"]}
        assert params["channels"] == ["email"]

    def test_notification_with_templates(self):
        """Kiểm tra với templates."""
        params: NotificationParams = {
            "channels": ["email"],
            "templates": {
                "order_confirmed": {"subject": "Order Confirmed", "body": "Thank you!"}
            },
        }
        assert "order_confirmed" in params["templates"]

    def test_notification_with_triggers(self):
        """Kiểm tra với triggers."""
        params: NotificationParams = {
            "channels": ["email", "sms"],
            "triggers": ["OrderCreated", "OrderShipped"],
        }
        assert len(params["triggers"]) == 2

    def test_notification_with_rate_limits(self):
        """Kiểm tra với rate_limits."""
        params: NotificationParams = {
            "channels": ["email"],
            "rate_limits": {"max_per_minute": 10, "max_per_day": 100},
        }
        assert params["rate_limits"]["max_per_minute"] == 10

    def test_notification_multiple_channels(self):
        """Kiểm tra với multiple channels."""
        params: NotificationParams = {
            "channels": ["email", "sms", "push", "webhook"],
        }
        assert len(params["channels"]) == 4

    def test_notification_multiple_templates(self):
        """Kiểm tra với multiple templates."""
        params: NotificationParams = {
            "channels": ["email"],
            "templates": {
                "welcome": {"subject": "Welcome"},
                "password_reset": {"subject": "Reset Password"},
                "order_update": {"subject": "Order Update"},
            },
        }
        assert len(params["templates"]) == 3

    def test_notification_webhook_channel(self):
        """Kiểm tra với webhook channel."""
        params: NotificationParams = {
            "channels": ["webhook"],
            "templates": {"event": {"url": "https://example.com/webhook"}},
        }
        assert "webhook" in params["channels"]

    def test_notification_all_fields(self):
        """Kiểm tra với tất cả fields."""
        params: NotificationParams = {
            "channels": ["email", "sms"],
            "templates": {"order": {}},
            "triggers": ["OrderCreated"],
            "rate_limits": {"max_per_minute": 10},
            "description": "Order notifications",
            "enabled": True,
        }
        assert params["enabled"] is True


# ============================================================================
# Integration Tests (P1 - 15 tests)
# ============================================================================


class TestCapabilityParamsIntegration:
    """Integration tests cho tất cả capability params."""

    def test_params_inherit_base_fields(self):
        """Kiểm tra tất cả params inherit từ BaseCapabilityParams."""
        mutation: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "test",
            "writes": ["Test"],
            "tenant_scope": "tenant_isolated",
            "description": "Test",
            "tags": ["test"],
            "enabled": True,
        }
        assert "description" in mutation
        assert "tags" in mutation

    def test_params_type_union(self):
        """Kiểm tra CapabilityParams union type."""
        mutation: CapabilityParams = {
            "actor_role": "staff",
            "permission": "test",
            "writes": ["Test"],
            "tenant_scope": "tenant_isolated",
        }
        query: CapabilityParams = {"reads": ["Test"]}
        event: CapabilityParams = {"event_type": "TestEvent", "handler_id": "handler"}

        assert "permission" in mutation
        assert "reads" in query
        assert "event_type" in event

    def test_complex_mutation_with_all_optional(self):
        """Kiểm tra complex mutation với tất cả optional fields."""
        params: AuthorizedMutationParams = {
            "actor_role": "admin",
            "permission": "admin.manage",
            "writes": ["User", "Role", "Permission"],
            "tenant_scope": "global",
            "reads": ["User", "Role"],
            "transaction": "required",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "errors": ["NOT_FOUND", "FORBIDDEN"],
            "guards": [{"type": "check"}],
            "effects": [{"type": "audit"}],
            "emits": ["AdminAction"],
            "description": "Admin action",
            "tags": ["admin"],
            "enabled": True,
        }
        assert len(params["writes"]) == 3
        assert params["tenant_scope"] == "global"

    def test_query_with_full_cache_config(self):
        """Kiểm tra query với full cache config."""
        params: AuthorizedQueryParams = {
            "reads": ["Product"],
            "cache_config": {
                "ttl_seconds": 300,
                "key_pattern": "product:{category}:{page}",
                "invalidate_on_write": True,
            },
        }
        assert params["cache_config"]["ttl_seconds"] == 300

    def test_workflow_complete_order_process(self):
        """Kiểm tra complete order workflow."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "submitted", "approved", "processing", "shipped", "delivered"],
            "transitions": [
                {"from": "draft", "to": "submitted"},
                {"from": "submitted", "to": "approved"},
                {"from": "approved", "to": "processing"},
                {"from": "processing", "to": "shipped"},
                {"from": "shipped", "to": "delivered"},
            ],
            "start_state": "draft",
            "end_states": ["delivered"],
            "human_tasks": [
                {"id": "approve_order", "role": "manager", "state": "submitted"}
            ],
            "timers": [
                {"id": "processing_timeout", "duration_ms": 86400000, "action": "cancel"}
            ],
        }
        assert len(params["states"]) == 6
        assert len(params["transitions"]) == 5

    def test_scheduled_task_daily_report(self):
        """Kiểm tra daily report scheduled task."""
        params: ScheduledTaskParams = {
            "task_id": "generate_daily_report",
            "cron_expression": "0 2 * * *",
            "timezone": "Asia/Ho Chi Minh",
            "max_duration_ms": 3600000,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
            "concurrency": {"max_parallel": 1},
        }
        assert params["cron_expression"] == "0 2 * * *"

    def test_event_handler_with_full_retry(self):
        """Kiểm tra event handler với full retry policy."""
        params: EventHandlerParams = {
            "event_type": "PaymentFailed",
            "handler_id": "retry_payment",
            "retry_policy": {
                "max_retries": 5,
                "backoff_multiplier": 2,
                "initial_delay_ms": 1000,
                "max_delay_ms": 60000,
            },
            "timeout_ms": 30000,
            "async_processing": True,
            "dead_letter_queue": {"topic": "dlq.payment", "max_age_hours": 72},
        }
        assert params["retry_policy"]["max_retries"] == 5

    def test_rule_engine_discount_system(self):
        """Kiểm tra discount rule engine."""
        params: RuleEngineParams = {
            "rules": [
                {
                    "id": "bulk_discount",
                    "condition": {"field": "quantity", "operator": ">=", "value": 10},
                    "action": {"type": "percentage", "value": 10},
                },
                {
                    "id": "amount_discount",
                    "condition": {"field": "total", "operator": ">=", "value": 1000000},
                    "action": {"type": "fixed", "value": 50000},
                },
            ],
            "priority": 100,
            "eval_order": "sequential",
            "short_circuit": False,
        }
        assert len(params["rules"]) == 2

    def test_aggregation_sales_report(self):
        """Kiểm tra sales aggregation."""
        params: AggregationParams = {
            "source_entities": ["Order"],
            "group_by": ["year", "month", "category"],
            "aggregations": [
                {"name": "total_revenue", "operation": "sum", "field": "total_amount"},
                {"name": "order_count", "operation": "count"},
                {"name": "avg_order_value", "operation": "avg", "field": "total_amount"},
                {"name": "max_order", "operation": "max", "field": "total_amount"},
            ],
            "filters": {"status": "completed"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "total_revenue": {"type": "number"},
                    "order_count": {"type": "integer"},
                },
            },
        }
        assert len(params["aggregations"]) == 4

    def test_search_index_product_catalog(self):
        """Kiểm tra product search index."""
        params: SearchIndexParams = {
            "indexed_entities": ["Product", "Category", "Brand"],
            "search_fields": ["name", "description", "sku", "tags"],
            "filter_fields": ["category_id", "brand_id", "price", "in_stock", "rating"],
            "sort_fields": ["price", "created_at", "popularity", "rating"],
            "analyzers": {"language": "vi", "stemmer": True, "stopwords": True},
        }
        assert len(params["search_fields"]) == 4

    def test_cache_strategy_multi_level(self):
        """Kiểm tra multi-level cache strategy."""
        params: CacheStrategyParams = {
            "cache_type": "redis",
            "ttl_seconds": 300,
            "invalidation_triggers": ["ProductUpdated", "ProductDeleted", "PriceChanged"],
            "key_pattern": "product:{id}:{version}",
            "max_size": 50000,
        }
        assert len(params["invalidation_triggers"]) == 3

    def test_notification_omnichannel(self):
        """Kiểm tra omnichannel notifications."""
        params: NotificationParams = {
            "channels": ["email", "sms", "push", "webhook"],
            "templates": {
                "order_confirmed": {"email": {}, "sms": {}, "push": {}},
                "shipping_update": {"email": {}, "push": {}},
            },
            "triggers": ["OrderCreated", "OrderShipped", "OrderDelivered"],
            "rate_limits": {"max_per_minute": 5, "max_per_hour": 50, "max_per_day": 100},
        }
        assert len(params["channels"]) == 4

    def test_params_empty_optional_fields(self):
        """Kiểm tra params với empty optional fields."""
        params: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "test",
            "writes": ["Test"],
            "tenant_scope": "tenant_isolated",
            "reads": [],
            "errors": [],
            "guards": [],
            "effects": [],
            "emits": [],
        }
        assert params["reads"] == []
        assert params["errors"] == []

    def test_params_type_consistency(self):
        """Kiểm tra type consistency across params."""
        mutation: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "test",
            "writes": ["A"],
            "tenant_scope": "tenant_isolated",
        }
        query: AuthorizedQueryParams = {"reads": ["A"]}
        handler: EventHandlerParams = {"event_type": "Event", "handler_id": "h"}

        assert isinstance(mutation["writes"], list)
        assert isinstance(query["reads"], list)
        assert isinstance(handler["event_type"], str)

    def test_params_disabled_flag(self):
        """Kiểm tra disabled flag qua base params."""
        mutation: AuthorizedMutationParams = {
            "actor_role": "staff",
            "permission": "test",
            "writes": ["Test"],
            "tenant_scope": "tenant_isolated",
            "enabled": False,
        }
        assert mutation["enabled"] is False


# ============================================================================
# Additional P1 Tests for Integration Params (15 tests)
# ============================================================================


class TestIntegrationParams:
    """Tests cho Integration capability params (P1)."""

    def test_outbound_integration_minimal(self):
        """Kiểm tra OutboundIntegrationParams."""
        params: OutboundIntegrationParams = {
            "target_system": "stripe",
            "endpoint": "https://api.stripe.com/v1/charges",
            "auth_type": "bearer",
        }
        assert params["target_system"] == "stripe"

    def test_inbound_integration_minimal(self):
        """Kiểm tra InboundIntegrationParams."""
        params: InboundIntegrationParams = {
            "path": "/webhooks/stripe",
            "method": "POST",
            "auth_type": "signature",
            "handler_id": "handle_stripe",
        }
        assert params["path"] == "/webhooks/stripe"

    def test_rate_limiting_params(self):
        """Kiểm tra RateLimitingParams."""
        params: RateLimitingParams = {
            "limits": [
                {"scope": "user", "requests": 100, "window_seconds": 60},
                {"scope": "global", "requests": 10000, "window_seconds": 60},
            ],
            "algorithm": "token_bucket",
            "key_by": "user_id",
        }
        assert len(params["limits"]) == 2

    def test_message_queue_params(self):
        """Kiểm tra MessageQueueParams."""
        params: MessageQueueParams = {
            "queue_type": "kafka",
            "topic": "order-events",
            "partition_key": "tenant_id",
        }
        assert params["queue_type"] == "kafka"

    def test_audit_log_params(self):
        """Kiểm tra AuditLogParams."""
        params: AuditLogParams = {
            "log_events": ["UserLogin", "DataExport"],
            "sensitive_fields": ["password", "ssn"],
            "retention_days": 2555,
            "compliance_tags": ["gdpr", "hipaa"],
        }
        assert len(params["log_events"]) == 2

    def test_data_export_params(self):
        """Kiểm tra DataExportParams."""
        params: DataExportParams = {
            "source_entities": ["Order", "Customer"],
            "format": "csv",
            "schedule": {"frequency": "daily", "time": "02:00"},
            "destination": {"type": "s3", "path": "exports"},
        }
        assert params["format"] == "csv"

    def test_data_import_params(self):
        """Kiểm tra DataImportParams."""
        params: DataImportParams = {
            "source": {"type": "s3", "path": "imports"},
            "format": "csv",
            "target_entities": ["Order"],
            "validation_rules": [{"field": "email", "rule": "email"}],
        }
        assert params["format"] == "csv"

    def test_batch_job_params(self):
        """Kiểm tra BatchJobParams."""
        params: BatchJobParams = {
            "job_id": "process_monthly",
            "chunk_size": 1000,
            "parallelism": 4,
            "timeout_ms": 3600000,
        }
        assert params["chunk_size"] == 1000

    def test_data_retention_params(self):
        """Kiểm tra DataRetentionParams."""
        params: DataRetentionParams = {
            "entities": ["Log", "Session"],
            "retention_period": {"years": 7},
            "deletion_policy": "hard_delete",
        }
        assert len(params["entities"]) == 2

    def test_monitoring_params(self):
        """Kiểm tra MonitoringParams."""
        params: MonitoringParams = {
            "metrics": [
                {"name": "api_latency", "type": "histogram"},
                {"name": "error_rate", "type": "gauge"},
            ],
            "alerts": [{"name": "high_error_rate", "threshold": 0.05}],
            "dashboards": [{"name": "overview"}],
        }
        assert len(params["metrics"]) == 2

    def test_outbound_with_retry(self):
        """Kiểm tra OutboundIntegration với retry."""
        params: OutboundIntegrationParams = {
            "target_system": "payment",
            "endpoint": "https://api.payment.com",
            "auth_type": "bearer",
            "retry_policy": {"max_retries": 3},
            "timeout_ms": 30000,
        }
        assert params["timeout_ms"] == 30000

    def test_inbound_with_rate_limit(self):
        """Kiểm tra InboundIntegration với rate limit."""
        params: InboundIntegrationParams = {
            "path": "/webhook",
            "method": "POST",
            "auth_type": "signature",
            "handler_id": "handler",
            "rate_limits": {"max_per_minute": 100},
        }
        assert params["rate_limits"]["max_per_minute"] == 100

    def test_message_queue_kafka(self):
        """Kiểm tra Kafka message queue."""
        params: MessageQueueParams = {
            "queue_type": "kafka",
            "topic": "events",
            "partition_key": "tenant_id",
            "consumers": [{"group": "order-processor"}],
            "producers": [{"id": "order-producer"}],
        }
        assert params["queue_type"] == "kafka"

    def test_message_queue_rabbitmq(self):
        """Kiểm tra RabbitMQ message queue."""
        params: MessageQueueParams = {
            "queue_type": "rabbitmq",
            "topic": "tasks",
        }
        assert params["queue_type"] == "rabbitmq"

    def test_message_queue_sqs(self):
        """Kiểm tra SQS message queue."""
        params: MessageQueueParams = {
            "queue_type": "sqs",
            "topic": "queue-url",
        }
        assert params["queue_type"] == "sqs"