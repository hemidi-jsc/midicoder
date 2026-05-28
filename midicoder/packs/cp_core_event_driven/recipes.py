"""
Event-Driven Architecture Recipes.

Module này cung cấp các pre-configured recipes cho event infrastructure.
Mỗi recipe là một cách gán giá trị cụ thể vào pattern vocabulary — không phải domain logic.

Recipes:
    - KafkaTransport: Apache Kafka (high throughput, partitioned, durable)
    - RabbitMQTransport: RabbitMQ (AMQP, flexible routing, dead letter)
    - RedisPubSub: Redis Streams (in-memory, low latency)
    - InMemoryTransport: In-process event bus (testing, single-process)
    - SQSTransport: AWS SQS (managed, FIFO, DLQ built-in)
    - SNSTransport: AWS SNS (fan-out, pub/sub, multi-protocol)
    - EventSourcingRecipe: Event store + snapshot + optimistic locking
    - OutboxRecipe: Transactional outbox pattern
    - DLQRecipe: Dead letter queue with alerting
    - DLQManagementRecipe: Centralized DLQ management with dashboard
    - IdempotentConsumerRecipe: Dedup + checkpoint

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from .models import (
    DeliveryGuarantee,
    DLQConfig,
    DLQDashboardConfig,
    DLQManagementConfig,
    DLQPolicy,
    DLQStatus,
    EventStoreBackend,
    EventStoreConfig,
    IdempotencyStrategy,
    IdempotentConsumer,
    RetryPolicy,
    RetryStrategy,
    SnapshotStrategy,
    TransportConfig,
    TransportType,
)


# ============================================================================
# Transport Recipes
# ============================================================================


def kafka_transport(
    brokers: str = "localhost:9092",
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.EXACTLY_ONCE,
    batch_size: int = 500,
    enable_tls: bool = True,
) -> TransportConfig:
    """
    Apache Kafka transport recipe.

    Kafka là choice cho high-throughput, partitioned, durable event streaming.
    Support exactly-once semantics với idempotent producer + transactional outbox.

    Args:
        brokers: Kafka broker connection string (vd: "broker1:9092,broker2:9092")
        delivery_guarantee: Delivery guarantee (default: exactly_once)
        batch_size: Số events trong 1 batch publish
        enable_tls: Enable TLS cho connection

    Returns:
        TransportConfig configured for Kafka
    """
    return TransportConfig(
        transport_type=TransportType.KAFKA,
        connection_string=brokers,
        delivery_guarantee=delivery_guarantee,
        max_retries=5,
        retry_backoff_ms=2000,
        batch_size=batch_size,
        batch_timeout_ms=500,
        enable_tls=enable_tls,
        description="Apache Kafka transport (high throughput, partitioned, durable)",
    )


def rabbitmq_transport(
    host: str = "localhost",
    port: int = 5672,
    vhost: str = "/",
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
    enable_tls: bool = False,
) -> TransportConfig:
    """
    RabbitMQ transport recipe.

    RabbitMQ là choice cho flexible routing, AMQP protocol, dead letter exchange.
    Support topic exchange, headers exchange, và priority queues.

    Args:
        host: RabbitMQ host
        port: RabbitMQ port (default: 5672)
        vhost: Virtual host (default: "/")
        delivery_guarantee: Delivery guarantee (default: at_least_once)
        enable_tls: Enable TLS cho connection

    Returns:
        TransportConfig configured for RabbitMQ
    """
    return TransportConfig(
        transport_type=TransportType.RABBITMQ,
        connection_string=f"amqp://localhost:{port}{vhost}",
        delivery_guarantee=delivery_guarantee,
        max_retries=3,
        retry_backoff_ms=1000,
        batch_size=100,
        batch_timeout_ms=1000,
        enable_tls=enable_tls,
        description="RabbitMQ transport (AMQP, flexible routing, dead letter)",
    )


def redis_pubsub(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_MOST_ONCE,
) -> TransportConfig:
    """
    Redis Streams transport recipe.

    Redis là choice cho in-memory, low-latency pub/sub.
    Good cho real-time notifications, WebSocket backend, và local development.

    Args:
        host: Redis host
        port: Redis port (default: 6379)
        db: Redis database number (default: 0)
        delivery_guarantee: Delivery guarantee (default: at_most_once — Redis is fire-and-forget)

    Returns:
        TransportConfig configured for Redis
    """
    return TransportConfig(
        transport_type=TransportType.REDIS,
        connection_string=f"redis://localhost:{port}/{db}",
        delivery_guarantee=delivery_guarantee,
        max_retries=1,
        retry_backoff_ms=500,
        batch_size=50,
        batch_timeout_ms=100,
        enable_tls=False,
        description="Redis Streams transport (in-memory, low latency)",
    )


def in_memory_transport() -> TransportConfig:
    """
    In-memory transport recipe.

    Dùng cho testing, development, và single-process applications.
    Không persist events — mất khi process restart.

    Returns:
        TransportConfig configured for in-memory
    """
    return TransportConfig(
        transport_type=TransportType.IN_MEMORY,
        connection_string="",
        delivery_guarantee=DeliveryGuarantee.EXACTLY_ONCE,
        max_retries=0,
        retry_backoff_ms=0,
        batch_size=100,
        batch_timeout_ms=0,
        enable_tls=False,
        description="In-memory event bus (testing, single-process)",
    )


def sqs_transport(
    region: str = "us-east-1",
    fifo: bool = True,
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
) -> TransportConfig:
    """
    AWS SQS transport recipe.

    SQS là managed queue service của AWS. FIFO queue support content-based
    deduplication và in-order delivery.

    Args:
        region: AWS region
        fifo: Use FIFO queue (default: True — for ordering + dedup)
        delivery_guarantee: Delivery guarantee (default: at_least_once)

    Returns:
        TransportConfig configured for AWS SQS
    """
    return TransportConfig(
        transport_type=TransportType.SQS,
        connection_string=f"aws://{region}",
        delivery_guarantee=delivery_guarantee,
        max_retries=5,
        retry_backoff_ms=2000,
        batch_size=10,  # SQS max batch size is 10
        batch_timeout_ms=5000,
        enable_tls=True,
        description="AWS SQS transport (managed, FIFO, DLQ built-in)",
    )


def sns_transport(
    region: str = "us-east-1",
) -> TransportConfig:
    """
    AWS SNS transport recipe.

    SNS là pub/sub service của AWS — fan-out đến multiple protocols
    (SQS, Lambda, HTTP/S, Email, SMS).

    Args:
        region: AWS region

    Returns:
        TransportConfig configured for AWS SNS
    """
    return TransportConfig(
        transport_type=TransportType.SNS,
        connection_string=f"aws://{region}",
        delivery_guarantee=DeliveryGuarantee.AT_LEAST_ONCE,
        max_retries=3,
        retry_backoff_ms=2000,
        batch_size=10,  # SNS max batch size is 10
        batch_timeout_ms=5000,
        enable_tls=True,
        description="AWS SNS transport (fan-out, pub/sub, multi-protocol)",
    )


# ============================================================================
# Event Sourcing Recipe
# ============================================================================


def event_sourcing_recipe(
    backend: EventStoreBackend = EventStoreBackend.DATABASE,
    connection_string: str = "",
    snapshot_interval: int = 100,
    enable_outbox: bool = True,
) -> EventStoreConfig:
    """
    Event sourcing recipe.

    Event store là backbone của event-sourced system — lưu sequence immutable
    events, replay để tái tạo state của aggregate root.

    Args:
        backend: Backend cho event store (database, kafka, dynamodb, mongodb)
        connection_string: Connection string cho backend
        snapshot_interval: Interval giữa snapshots (số events)
        enable_outbox: Enable outbox pattern cho reliable delivery

    Returns:
        EventStoreConfig configured for event sourcing
    """
    return EventStoreConfig(
        backend=backend,
        connection_string=connection_string,
        snapshot_strategy=SnapshotStrategy.PERIODIC,
        snapshot_interval=snapshot_interval,
        enable_optimistic_locking=True,
        enable_outbox=enable_outbox,
        max_batch_size=50,
        description="Event sourcing backbone with snapshot and optimistic locking",
    )


# ============================================================================
# Outbox Recipe
# ============================================================================


def outbox_recipe(
    visibility_delay: int = 0,
    max_retries: int = 5,
    transport: TransportConfig | None = None,
) -> dict:
    """
    Transactional outbox recipe.

    Outbox pattern đảm bảo event không bị mất khi database transaction
    commit thành công nhưng publish thất bại.

    Args:
        visibility_delay: Delay (giây) trước khi event có thể được publish
        max_retries: Số lần retry tối đa
        transport: Transport config (optional — nếu không có, dùng default)

    Returns:
        Dict with outbox configuration
    """
    return {
        "visibility_delay": visibility_delay,
        "max_retries": max_retries,
        "transport": transport.to_dict() if transport else None,
        "description": "Transactional outbox for reliable event delivery",
    }


# ============================================================================
# DLQ Recipe
# ============================================================================


def dlq_recipe(
    queue_name: str = "events.dlq",
    policy: DLQPolicy = DLQPolicy.MOVE_AFTER_RETRIES,
    max_retries_before_dlq: int = 5,
    retention_hours: int = 168,
    alert_channels: list[str] | None = None,
) -> DLQConfig:
    """
    Dead letter queue recipe.

    DLQ thu thập messages không thể process được — để debug, retry manual,
    hoặc alert team.

    Args:
        queue_name: Tên DLQ queue (vd: "events.dlq")
        policy: Policy xử lý DLQ
        max_retries_before_dlq: Số retries trước khi move sang DLQ
        retention_hours: Bao lâu giữ messages trong DLQ (default: 168 = 7 days)
        alert_channels: Channels alert (default: ["slack"])

    Returns:
        DLQConfig configured for dead letter queue
    """
    return DLQConfig(
        enabled=True,
        queue_name=queue_name,
        policy=policy,
        max_retries_before_dlq=max_retries_before_dlq,
        retention_hours=retention_hours,
        alert_on_dlq=True,
        alert_channels=alert_channels or ["slack"],
        description="Dead letter queue with alerting and retention policy",
    )


# ============================================================================
# Idempotent Consumer Recipe
# ============================================================================


def idempotent_consumer_recipe(
    strategy: IdempotencyStrategy = IdempotencyStrategy.DEDUP_BY_EVENT_ID,
    business_key_fields: list[str] | None = None,
    dedup_window_seconds: int = 3600,
) -> IdempotentConsumer:
    """
    Idempotent consumer recipe.

    Đảm bảo consumer không xử lý event trùng lặp — critical cho financial,
    inventory, và các domain where duplicate processing causes data corruption.

    Args:
        strategy: Chiến lược idempotency
        business_key_fields: Các fields dùng làm business key (vd: ["order_id"])
        dedup_window_seconds: Cửa sổ thời gian giữ dedup keys (default: 3600 = 1 hour)

    Returns:
        IdempotentConsumer configured for dedup
    """
    return IdempotentConsumer(
        strategy=strategy,
        dedup_window_seconds=dedup_window_seconds,
        business_key_fields=business_key_fields or [],
        enable_checkpoint=True,
        checkpoint_interval=100,
        description="Idempotent consumer with dedup and checkpoint",
    )


# ============================================================================
# Retry Policy Recipe
# ============================================================================


def retry_policy_recipe(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER,
    retryable_errors: list[str] | None = None,
) -> RetryPolicy:
    """
    Retry policy recipe.

    Args:
        max_attempts: Số lần retry tối đa
        strategy: Chiến lược retry
        retryable_errors: Danh sách error codes có thể retry

    Returns:
        RetryPolicy configured for retry
    """
    return RetryPolicy(
        strategy=strategy,
        max_attempts=max_attempts,
        initial_delay_ms=1000,
        max_delay_ms=30000,
        multiplier=2.0,
        retryable_errors=retryable_errors or ["timeout", "connection_error", "rate_limit"],
        description="Retry policy with exponential backoff and jitter",
    )


# ============================================================================
# DLQ Management Recipe (Centralized)
# ============================================================================


def dlq_management_recipe(
    dlq_id: str = "dlq.central",
    dlq_name: str = "Central DLQ",
    source_topic: str = "events.failed",
    max_retries: int = 3,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay_seconds: int = 10,
    max_delay_seconds: int = 3600,
    retention_days: int = 7,
    auto_purge: bool = False,
    alert_on_threshold: int = 100,
    dashboard_id: str = "dlq.dashboard",
    dashboard_name: str = "DLQ Management Dashboard",
    auto_retry: bool = False,
    retry_batch_size: int = 10,
    slack_webhook: str = "",
    email_recipients: list[str] | None = None,
) -> dict:
    """
    Centralized DLQ management recipe với exponential backoff, auto-purge, dashboard.

    Recipe này cung cấp cấu hình DLQ centralized — thu thập tất cả messages
    không thể process từ nhiều topics, với retry tự động, dashboard quản lý,
    và notification qua Slack/email.

    Args:
        dlq_id: Unique ID cho DLQ management config
        dlq_name: Tên hiển thị của DLQ
        source_topic: Topic/source mà DLQ nhận messages
        max_retries: Số lần retry tối đa
        retry_strategy: Chiến lược retry
        initial_delay_seconds: Delay ban đầu giữa retries (giây)
        max_delay_seconds: Delay tối đa giữa retries (giây)
        retention_days: Số ngày giữ messages trong DLQ
        auto_purge: Có tự động purge messages sau retention_days không
        alert_on_threshold: Alert khi DLQ vượt quá số messages này
        dashboard_id: Unique ID cho dashboard config
        dashboard_name: Tên hiển thị của dashboard
        auto_retry: Có tự động retry messages trong DLQ không
        retry_batch_size: Số messages retry cùng lúc
        slack_webhook: Webhook URL cho Slack notification
        email_recipients: Danh sách email để nhận notification

    Returns:
        Dict với DLQ management config, dashboard config, và metadata
    """
    return {
        "dlq_config": DLQManagementConfig(
            id=dlq_id,
            name=dlq_name,
            source_topic=source_topic,
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            initial_delay_seconds=initial_delay_seconds,
            max_delay_seconds=max_delay_seconds,
            retention_days=retention_days,
            auto_purge=auto_purge,
            alert_on_threshold=alert_on_threshold,
            description="Centralized DLQ with exponential backoff and auto-purge",
        ),
        "dashboard_config": DLQDashboardConfig(
            id=dashboard_id,
            name=dashboard_name,
            enabled=True,
            auto_retry=auto_retry,
            retry_batch_size=retry_batch_size,
            purge_after_days=retention_days,
            notification_on_new_message=True,
            slack_webhook=slack_webhook,
            email_recipients=email_recipients or [],
            description="Centralized DLQ management dashboard with Slack/email notification",
        ),
        "status": DLQStatus.ACTIVE.value,
        "description": "Centralized DLQ management with exponential backoff, auto-purge, and dashboard",
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Transport recipes
    "kafka_transport",
    "rabbitmq_transport",
    "redis_pubsub",
    "in_memory_transport",
    "sqs_transport",
    "sns_transport",
    # Event sourcing
    "event_sourcing_recipe",
    # Outbox
    "outbox_recipe",
    # DLQ
    "dlq_recipe",
    "dlq_management_recipe",
    # Idempotent consumer
    "idempotent_consumer_recipe",
    # Retry policy
    "retry_policy_recipe",
]
