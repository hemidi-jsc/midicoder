"""
Typed Capability Parameters for Midicoder v1.0.0

Module này định nghĩa TypedDict models cho params của mỗi loại capability.
Sử dụng typed params thay vì dict[str, Any] để đảm bảo type safety.

Theo ANALYSIS_DSL_CONTRACT_OVERLAP.md:
- DSL có 101+ TypedDict models với typed structure
- Contracts hiện tại chỉ có params: dict[str, Any] - UNSTRUCTURED
- Giải pháp: Tạo TypedDict cho 20+ capability types

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

if TYPE_CHECKING:
    pass  # Avoid circular imports at runtime


# ============================================================================
# Base Capability Params
# ============================================================================


class BaseCapabilityParams(TypedDict, total=False):
    """
    Base params cho tất cả capabilities.
    
    Fields:
        description: Mô tả capability
        tags: Danh sách tags để categorization
        enabled: Capability có active không
    """

    description: str
    tags: list[str]
    enabled: bool


# ============================================================================
# Core Capability Params (CP01-CP20)
# ============================================================================


class AuthorizedMutationParams(BaseCapabilityParams):
    """
    Params cho authorized_mutation capability (CP01).
    
    Authorized mutation là write operation yêu cầu:
    - Permission check (permission-based authorization)
    - Tenant filter (multi-tenancy isolation)
    - Transaction support (atomicity)
    
    Fields:
        actor_role: Role của actor thực hiện mutation
        permission: Permission string (ví dụ: "order.create")
        writes: Danh sách entity IDs sẽ được modify
        reads: Danh sách entity IDs cần đọc (optional)
        transaction: Transaction requirement ("required" | "allowed" | "forbidden")
        tenant_scope: Tenant scope ("global" | "tenant_isolated" | "tenant_leaked")
        input_schema: Schema cho input parameters
        output_schema: Schema cho output data
        errors: Danh sách error IDs có thể phát sinh
        guards: Danh sách guards cần kiểm tra
        effects: Danh sách effects sau khi execute
        emits: Danh sách event IDs sẽ emit
    
    Example:
        {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order", "OrderItem"],
            "transaction": "required",
            "tenant_scope": "tenant_isolated",
            "input_schema": {...},
            "errors": ["ORDER_NOT_FOUND", "INSUFFICIENT_INVENTORY"],
            "emits": ["OrderCreated"]
        }
    """

    actor_role: str
    permission: str
    writes: list[str]
    reads: NotRequired[list[str]]
    transaction: NotRequired[str]  # "required" | "allowed" | "forbidden"
    tenant_scope: str  # "global" | "tenant_isolated" | "tenant_leaked"
    input_schema: NotRequired[dict[str, Any]]
    output_schema: NotRequired[dict[str, Any]]
    errors: NotRequired[list[str]]
    guards: NotRequired[list[dict[str, Any]]]
    effects: NotRequired[list[dict[str, Any]]]
    emits: NotRequired[list[str]]


class AuthorizedQueryParams(BaseCapabilityParams):
    """
    Params cho authorized_query capability (CP02).
    
    Authorized query là read operation yêu cầu:
    - Permission check (optional)
    - Tenant filter (multi-tenancy isolation)
    
    Fields:
        reads: Danh sách entity IDs sẽ được read
        required_permission: Permission string (optional)
        tenant_scope: Tenant scope
        input_schema: Schema cho input parameters (filters, pagination)
        output_schema: Schema cho output data
        cache_config: Cache configuration (optional)
    
    Example:
        {
            "reads": ["Order", "OrderItem"],
            "required_permission": "order.read",
            "tenant_scope": "tenant_isolated",
            "input_schema": {...},
            "output_schema": {...},
            "cache_config": {"ttl_seconds": 300}
        }
    """

    reads: list[str]
    required_permission: NotRequired[str]
    tenant_scope: NotRequired[str]
    input_schema: NotRequired[dict[str, Any]]
    output_schema: NotRequired[dict[str, Any]]
    cache_config: NotRequired[dict[str, Any]]


class EventHandlerParams(BaseCapabilityParams):
    """
    Params cho event_handler capability (CP03).
    
    Event handler là capability xử lý incoming events.
    
    Fields:
        event_type: Loại event sẽ handle
        handler_id: ID của handler/command để process
        retry_policy: Retry policy khi handle fail
        timeout_ms: Timeout cho event handling
        async_processing: Có process async không
        dead_letter_queue: DLQ configuration (optional)
    
    Example:
        {
            "event_type": "OrderCreated",
            "handler_id": "process_order",
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
            "timeout_ms": 30000,
            "async_processing": true
        }
    """

    event_type: str
    handler_id: str
    retry_policy: NotRequired[dict[str, Any]]
    timeout_ms: NotRequired[int]
    async_processing: NotRequired[bool]
    dead_letter_queue: NotRequired[dict[str, Any]]


class ScheduledTaskParams(BaseCapabilityParams):
    """
    Params cho scheduled_task capability (CP04).
    
    Scheduled task là periodic job chạy theo schedule.
    
    Fields:
        task_id: ID của task/command để execute
        cron_expression: Cron expression cho schedule
        timezone: Timezone cho schedule
        max_duration_ms: Max duration cho task execution
        retry_policy: Retry policy khi task fail
        concurrency: Concurrency settings
    
    Example:
        {
            "task_id": "generate_daily_report",
            "cron_expression": "0 2 * * *",
            "timezone": "UTC",
            "max_duration_ms": 3600000,
            "retry_policy": {"max_retries": 3}
        }
    """

    task_id: str
    cron_expression: str
    timezone: NotRequired[str]
    max_duration_ms: NotRequired[int]
    retry_policy: NotRequired[dict[str, Any]]
    concurrency: NotRequired[dict[str, Any]]


class WorkflowDefinitionParams(BaseCapabilityParams):
    """
    Params cho workflow_definition capability (CP05).
    
    Workflow định nghĩa business process với states và transitions.
    Enhanced với guard conditions, action hooks, parallel states, sub-workflows, và versioning.
    
    Fields:
        states: Danh sách states trong workflow (list[str] hoặc list[dict] cho rich definitions)
        transitions: Danh sách transitions giữa states
        start_state: State bắt đầu
        end_states: Danh sách end states
        compensation: Compensation actions cho rollback
        human_tasks: Human tasks/approvals
        timers: Timers và delays
        # E11-002 Enhancements:
        guard_conditions: Dict mapping transition IDs đến guard conditions (expressions, messages, on_fail)
        action_hooks: Dict với on_entry, on_exit, on_transition hooks cho states/transitions
        parallel_states: Danh sách states chạy song song (cho parallel workflows)
        sub_workflows: Danh sách sub-workflow references (reusable templates)
        versioning: Version info (semantic versioning, backward_compatible, migration_guide)
    
    Example:
        {
            "states": ["draft", "submitted", "approved", "completed"],
            "transitions": [
                {"from": "draft", "to": "submitted"},
                {"from": "submitted", "to": "approved", "guard": "total > 1000"}
            ],
            "start_state": "draft",
            "end_states": ["completed", "rejected"],
            "guard_conditions": {
                "submitted_to_approved": {
                    "expression": "total > 1000",
                    "message": "Đơn hàng trên 1000 cần phê duyệt",
                    "on_fail": "reject_order"
                }
            },
            "action_hooks": {
                "on_entry": {
                    "approved": ["create_invoice", "notify_customer"]
                },
                "on_exit": {
                    "draft": ["cleanup_temp_files"]
                },
                "on_transition": {
                    "submitted_to_approved": ["audit_log", "send_confirmation"]
                }
            },
            "parallel_states": ["payment_verification", "inventory_check"],
            "sub_workflows": [
                {"ref": "manager_approval", "on": "total > 1000000"}
            ],
            "versioning": {
                "type": "semantic",
                "version": "1.0.0",
                "backward_compatible": True
            },
            "compensation": [...],
            "human_tasks": [...],
            "timers": [...]
        }
    """

    states: list[str]
    transitions: list[dict[str, Any]]
    start_state: str
    end_states: NotRequired[list[str]]
    compensation: NotRequired[list[dict[str, Any]]]
    human_tasks: NotRequired[list[dict[str, Any]]]
    timers: NotRequired[list[dict[str, Any]]]
    # E11-002: Enhanced fields for advanced workflows
    guard_conditions: NotRequired[dict[str, dict[str, Any]]]  # Transition ID -> {expression, message, on_fail}
    action_hooks: NotRequired[dict[str, dict[str, list[str]]]]  # {on_entry, on_exit, on_transition} -> state/transition -> actions
    parallel_states: NotRequired[list[str]]  # States that run in parallel
    sub_workflows: NotRequired[list[dict[str, Any] | str]]  # Sub-workflow references with optional conditions
    versioning: NotRequired[dict[str, Any]]  # {type: "semantic", version, backward_compatible, migration_guide}


class RuleEngineParams(BaseCapabilityParams):
    """
    Params cho rule_engine capability (CP06).
    
    Rule engine evaluate business rules với condition và action.
    
    Fields:
        rules: Danh sách rules để evaluate
        priority: Priority của rule set
        enabled: Rule set có active không
        eval_order: Evaluation order ("sequential" | "parallel")
        short_circuit: Stop khi có rule match không
    
    Example:
        {
            "rules": [
                {
                    "id": "discount_threshold",
                    "condition": {"field": "order.total", "operator": ">", "value": 1000},
                    "action": {"type": "discount", "percentage": 10}
                }
            ],
            "eval_order": "sequential",
            "short_circuit": true
        }
    """

    rules: list[dict[str, Any]]
    priority: NotRequired[int]
    eval_order: NotRequired[str]  # "sequential" | "parallel"
    short_circuit: NotRequired[bool]


class AggregationParams(BaseCapabilityParams):
    """
    Params cho aggregation capability (CP07).
    
    Aggregation compute summary từ multiple records.
    
    Fields:
        source_entities: Danh sách entities để aggregate
        group_by: Fields để group
        aggregations: Danh sách aggregation operations
        filters: Filters cho source data
        output_schema: Schema cho aggregated output
    
    Example:
        {
            "source_entities": ["Order"],
            "group_by": ["customer_id", "year"],
            "aggregations": [
                {"name": "total_revenue", "operation": "sum", "field": "total_amount"},
                {"name": "order_count", "operation": "count"}
            ],
            "filters": {"status": "completed"}
        }
    """

    source_entities: list[str]
    group_by: list[str]
    aggregations: list[dict[str, Any]]
    filters: NotRequired[dict[str, Any]]
    output_schema: NotRequired[dict[str, Any]]


class SearchIndexParams(BaseCapabilityParams):
    """
    Params cho search_index capability (CP08).
    
    Search index định nghĩa full-text search configuration.
    
    Fields:
        indexed_entities: Danh sách entities để index
        search_fields: Fields có thể search
        filter_fields: Fields có thể filter
        sort_fields: Fields có thể sort
        analyzers: Text analyzers configuration
    
    Example:
        {
            "indexed_entities": ["Product", "Category"],
            "search_fields": ["name", "description", "sku"],
            "filter_fields": ["category_id", "price", "in_stock"],
            "sort_fields": ["price", "created_at", "popularity"],
            "analyzers": {"language": "en"}
        }
    """

    indexed_entities: list[str]
    search_fields: list[str]
    filter_fields: NotRequired[list[str]]
    sort_fields: NotRequired[list[str]]
    analyzers: NotRequired[dict[str, Any]]


class CacheStrategyParams(BaseCapabilityParams):
    """
    Params cho cache_strategy capability (CP09).
    
    Cache strategy định nghĩa caching configuration.
    
    Fields:
        cache_type: Loại cache ("memory" | "redis" | "memcached")
        ttl_seconds: Default TTL cho cache entries
        invalidation_triggers: Events trigger cache invalidation
        key_pattern: Pattern cho cache keys
        max_size: Max cache size (optional)
    
    Example:
        {
            "cache_type": "redis",
            "ttl_seconds": 300,
            "invalidation_triggers": ["ProductUpdated", "ProductDeleted"],
            "key_pattern": "product:{id}",
            "max_size": 10000
        }
    """

    cache_type: str
    ttl_seconds: int
    invalidation_triggers: NotRequired[list[str]]
    key_pattern: NotRequired[str]
    max_size: NotRequired[int]


class NotificationParams(BaseCapabilityParams):
    """
    Params cho notification capability (CP10).
    
    Notification send messages qua various channels.
    
    Fields:
        channels: Danh sách notification channels
        templates: Template configuration
        triggers: Events trigger notifications
        rate_limits: Rate limiting configuration
    
    Example:
        {
            "channels": ["email", "sms", "push"],
            "templates": {
                "order_confirmed": {"subject": "Order Confirmed", "body": "..."}
            },
            "triggers": ["OrderCreated", "OrderShipped"],
            "rate_limits": {"max_per_minute": 10}
        }
    """

    channels: list[str]
    templates: NotRequired[dict[str, Any]]
    triggers: NotRequired[list[str]]
    rate_limits: NotRequired[dict[str, Any]]


# ============================================================================
# Integration Capability Params (CP11-CP20)
# ============================================================================


class OutboundIntegrationParams(BaseCapabilityParams):
    """
    Params cho outbound_integration capability (CP11).
    
    Outbound integration là outgoing calls đến external systems.
    Enhanced với payment-specific config cho payment gateways.
    
    Fields:
        target_system: Target system ID/name
        endpoint: Endpoint URL
        auth_type: Authentication type ("bearer" | "basic" | "api_key" | "oauth2" | "sig_v4" | "mutual_tls")
        request_template: Request template
        retry_policy: Retry policy
        timeout_ms: Timeout cho request
        transforms: Data transformations
        # E11-003: Payment-specific configuration
        payment_config: Optional payment-specific settings (idempotency, PCI, 3DS, fraud, etc.)
    
    Payment Config Fields:
        idempotency_key: Unique key để prevent duplicate charges
        idempotency_ttl_seconds: TTL cho idempotency key
        pci_compliance: Enable PCI-DSS compliance mode
        pci_mode: "passthrough" | "tokenized"
        3ds_enabled: Enable 3D Secure (3DS) for card payments
        3ds_version: 3DS version (e.g., "2.2.0")
        fraud_check: Enable fraud detection
        fraud_service: Fraud service (e.g., "stripe_radar")
        capture_mode: "auto" | "manual" | "auth_only"
        split_enabled: Enable split payments
        refund_enabled: Enable refunds
    
    Example:
        {
            "target_system": "stripe",
            "endpoint": "https://api.stripe.com/v1/payment_intents",
            "auth_type": "bearer",
            "timeout_ms": 30000,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
            "payment_config": {
                "idempotency_key": "order_{id}_payment",
                "pci_compliance": True,
                "pci_mode": "tokenized",
                "3ds_enabled": True,
                "3ds_version": "2.2.0",
                "fraud_check": True,
                "fraud_service": "stripe_radar",
                "capture_mode": "manual",
                "split_enabled": True,
                "refund_enabled": True
            }
        }
    """

    target_system: str
    endpoint: str
    auth_type: str
    request_template: NotRequired[dict[str, Any]]
    retry_policy: NotRequired[dict[str, Any]]
    timeout_ms: NotRequired[int]
    transforms: NotRequired[list[dict[str, Any]]]
    # E11-003: Payment-specific configuration
    payment_config: NotRequired[dict[str, Any]]  # idempotency, PCI, 3DS, fraud, capture, split, refunds


class InboundIntegrationParams(BaseCapabilityParams):
    """
    Params cho inbound_integration capability (CP12).
    
    Inbound integration là incoming endpoints từ external systems.
    
    Fields:
        path: URL path cho endpoint
        method: HTTP method
        auth_type: Authentication type
        payload_schema: Schema cho incoming payload
        handler_id: Handler/command để process
        rate_limits: Rate limiting configuration
    
    Example:
        {
            "path": "/webhooks/stripe",
            "method": "POST",
            "auth_type": "signature",
            "payload_schema": {...},
            "handler_id": "handle_stripe_webhook",
            "rate_limits": {"max_per_minute": 100}
        }
    """

    path: str
    method: str
    auth_type: str
    payload_schema: NotRequired[dict[str, Any]]
    handler_id: str
    rate_limits: NotRequired[dict[str, Any]]


class MessageQueueParams(BaseCapabilityParams):
    """
    Params cho message_queue capability (CP13).
    
    Message queue publish/subscribe messages.
    
    Fields:
        queue_type: Loại queue ("kafka" | "rabbitmq" | "sqs")
        topic: Topic name
        partition_key: Partition key field
        consumers: Danh sách consumer configurations
        producers: Danh sách producer configurations
    
    Example:
        {
            "queue_type": "kafka",
            "topic": "order-events",
            "partition_key": "tenant_id",
            "consumers": [...],
            "producers": [...]
        }
    """

    queue_type: str
    topic: str
    partition_key: NotRequired[str]
    consumers: NotRequired[list[dict[str, Any]]]
    producers: NotRequired[list[dict[str, Any]]]


class AuditLogParams(BaseCapabilityParams):
    """
    Params cho audit_log capability (CP14).
    
    Audit log track significant operations.
    
    Fields:
        log_events: Events để log
        sensitive_fields: Fields cần mask/redact
        retention_days: Retention period
        compliance_tags: Compliance tags
    
    Example:
        {
            "log_events": ["UserLogin", "DataExport", "PermissionChange"],
            "sensitive_fields": ["password", "ssn", "credit_card"],
            "retention_days": 2555,
            "compliance_tags": ["gdpr", "hipaa"]
        }
    """

    log_events: list[str]
    sensitive_fields: NotRequired[list[str]]
    retention_days: NotRequired[int]
    compliance_tags: NotRequired[list[str]]


class RateLimitingParams(BaseCapabilityParams):
    """
    Params cho rate_limiting capability (CP15).
    
    Rate limiting control request throughput.
    
    Fields:
        limits: Danh sách rate limits
        algorithm: Rate limiting algorithm ("token_bucket" | "sliding_window")
        key_by: Field để key rate limits
    
    Example:
        {
            "limits": [
                {"scope": "user", "requests": 100, "window_seconds": 60},
                {"scope": "global", "requests": 10000, "window_seconds": 60}
            ],
            "algorithm": "token_bucket",
            "key_by": "user_id"
        }
    """

    limits: list[dict[str, Any]]
    algorithm: NotRequired[str]
    key_by: NotRequired[str]


class DataExportParams(BaseCapabilityParams):
    """
    Params cho data_export capability (CP16).
    
    Data export generate data exports.
    
    Fields:
        source_entities: Entities để export
        format: Export format ("csv" | "json" | "parquet")
        schedule: Export schedule
        destination: Export destination
    
    Example:
        {
            "source_entities": ["Order", "Customer"],
            "format": "csv",
            "schedule": {"frequency": "daily", "time": "02:00"},
            "destination": {"type": "s3", "path": "exports/orders"}
        }
    """

    source_entities: list[str]
    format: str
    schedule: NotRequired[dict[str, Any]]
    destination: NotRequired[dict[str, Any]]


class DataImportParams(BaseCapabilityParams):
    """
    Params cho data_import capability (CP17).
    
    Data import process incoming data.
    
    Fields:
        source: Import source
        format: Data format
        target_entities: Entities để write
        validation_rules: Validation rules
        transform_mappings: Data transformations
    
    Example:
        {
            "source": {"type": "s3", "path": "imports/orders"},
            "format": "csv",
            "target_entities": ["Order", "OrderItem"],
            "validation_rules": [...],
            "transform_mappings": [...]
        }
    """

    source: dict[str, Any]
    format: str
    target_entities: list[str]
    validation_rules: NotRequired[list[dict[str, Any]]]
    transform_mappings: NotRequired[list[dict[str, Any]]]


class BatchJobParams(BaseCapabilityParams):
    """
    Params cho batch_job capability (CP18).
    
    Batch job process large datasets.
    
    Fields:
        job_id: ID của batch job
        chunk_size: Số records per chunk
        parallelism: Số parallel workers
        timeout_ms: Timeout cho job
        retry_policy: Retry policy
    
    Example:
        {
            "job_id": "process_monthly_report",
            "chunk_size": 1000,
            "parallelism": 4,
            "timeout_ms": 3600000,
            "retry_policy": {"max_retries": 3}
        }
    """

    job_id: str
    chunk_size: NotRequired[int]
    parallelism: NotRequired[int]
    timeout_ms: NotRequired[int]
    retry_policy: NotRequired[dict[str, Any]]


class DataRetentionParams(BaseCapabilityParams):
    """
    Params cho data_retention capability (CP19).
    
    Data retention enforce data lifecycle policies.
    
    Fields:
        entities: Entities áp dụng retention
        retention_period: Retention period
        archival_strategy: Archival strategy
        deletion_policy: Deletion policy
    
    Example:
        {
            "entities": ["Order", "Log"],
            "retention_period": {"years": 7},
            "archival_strategy": {"type": "s3", "path": "archive"},
            "deletion_policy": "hard_delete"
        }
    """

    entities: list[str]
    retention_period: dict[str, Any]
    archival_strategy: NotRequired[dict[str, Any]]
    deletion_policy: NotRequired[str]


class MonitoringParams(BaseCapabilityParams):
    """
    Params cho monitoring capability (CP20).
    
    Monitoring track system health và performance.
    
    Fields:
        metrics: Danh sách metrics để track
        alerts: Alert configurations
        dashboards: Dashboard configurations
    
    Example:
        {
            "metrics": [
                {"name": "api_latency", "type": "histogram"},
                {"name": "error_rate", "type": "gauge"}
            ],
            "alerts": [...],
            "dashboards": [...]
        }
    """

    metrics: list[dict[str, Any]]
    alerts: NotRequired[list[dict[str, Any]]]
    dashboards: NotRequired[list[dict[str, Any]]]


# ============================================================================
# Union Type cho All Capability Params
# ============================================================================

from typing import Union

CapabilityParams = Union[
    # Core capabilities
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
    # Integration capabilities
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
]

__all__ = [
    # Base
    "BaseCapabilityParams",
    # Core capabilities
    "AuthorizedMutationParams",
    "AuthorizedQueryParams",
    "EventHandlerParams",
    "ScheduledTaskParams",
    "WorkflowDefinitionParams",
    "RuleEngineParams",
    "AggregationParams",
    "SearchIndexParams",
    "CacheStrategyParams",
    "NotificationParams",
    # Integration capabilities
    "OutboundIntegrationParams",
    "InboundIntegrationParams",
    "MessageQueueParams",
    "AuditLogParams",
    "RateLimitingParams",
    "DataExportParams",
    "DataImportParams",
    "BatchJobParams",
    "DataRetentionParams",
    "MonitoringParams",
    # Union type
    "CapabilityParams",
]