"""
Event Models Module.

Module này định nghĩa các models cho Event DSL:
- EventDefinition: Định nghĩa event với event_name, payload_fields, topic, version, tenant_id

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# EventDefinition Model
# ============================================================================


@dataclass
class EventDefinition:
    """
    Event definition trong DSL.

    Event đại diện cho một event trong hệ thống event-driven.
    Mỗi event có event_name, payload_fields, topic, version, và tenant_id.

    Attributes:
        event_name: Định danh duy nhất của event (ví dụ: "order.created")
        payload_fields: Danh sách field names trong event payload
        topic: Topic để route event (default: "default")
        version: Version của event schema (default: "1.0")
        tenant_id: Tenant ID cho multi-tenant isolation (KPI-029, optional)
        schema_fields: Schema definition cho payload validation (optional)

    Example:
        >>> event = EventDefinition(
        ...     event_name="order.created",
        ...     payload_fields=["order_id", "customer_id", "total"],
        ...     topic="orders",
        ...     version="1.0",
        ... )
    """

    event_name: str
    payload_fields: list[str] = field(default_factory=list)
    topic: str = "default"
    version: str = "1.0"
    tenant_id: str | None = None
    schema_fields: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate event_name không được empty."""
        if not self.event_name or not self.event_name.strip():
            raise ValueError("event_name không được để trống")

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển EventDefinition sang dictionary.

        Returns:
            Dictionary representation của EventDefinition
        """
        result: dict[str, Any] = {
            "event_name": self.event_name,
            "payload_fields": self.payload_fields,
            "topic": self.topic,
            "version": self.version,
        }
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
        if self.schema_fields is not None:
            result["schema_fields"] = self.schema_fields
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventDefinition":
        """
        Tạo EventDefinition từ dictionary.

        Args:
            data: Dictionary chứa event data

        Returns:
            EventDefinition instance
        """
        return cls(
            event_name=data.get("event_name", ""),
            payload_fields=data.get("payload_fields", []),
            topic=data.get("topic", "default"),
            version=data.get("version", "1.0"),
            tenant_id=data.get("tenant_id"),
            schema_fields=data.get("schema_fields"),
        )


# ============================================================================
# OutboxEntry Model
# ============================================================================


@dataclass
class OutboxEntry:
    """
    Outbox entry cho reliable event delivery (Outbox pattern).

    OutboxEntry đại diện cho một event đã được ghi vào outbox table
    nhưng chưa được publish. Pattern này đảm bảo event không bị mất
    khi database transaction commit thành công nhưng publish thất bại.

    Attributes:
        event_name: Tên của event
        payload: Payload data của event
        topic: Topic để route event
        transaction_id: Transaction ID để link với business transaction
        visibility_delay: Delay (giây) trước khi event có thể được publish
        status: Trạng thái của outbox entry (pending, published, failed)
        created_at: Thời điểm tạo entry
        published_at: Thời điểm publish thành công (optional)
    """

    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    topic: str = "default"
    transaction_id: str | None = None
    visibility_delay: int = 0
    status: str = "pending"
    retries: int = 0
    created_at: str | None = None
    published_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển OutboxEntry sang dictionary.

        Returns:
            Dictionary representation của OutboxEntry
        """
        result: dict[str, Any] = {
            "event_name": self.event_name,
            "payload": self.payload,
            "topic": self.topic,
            "status": self.status,
        }
        if self.transaction_id is not None:
            result["transaction_id"] = self.transaction_id
        if self.visibility_delay > 0:
            result["visibility_delay"] = self.visibility_delay
        if self.created_at is not None:
            result["created_at"] = self.created_at
        if self.published_at is not None:
            result["published_at"] = self.published_at
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutboxEntry":
        """
        Tạo OutboxEntry từ dictionary.

        Args:
            data: Dictionary chứa outbox entry data

        Returns:
            OutboxEntry instance
        """
        return cls(
            event_name=data.get("event_name", ""),
            payload=data.get("payload", {}),
            topic=data.get("topic", "default"),
            transaction_id=data.get("transaction_id"),
            visibility_delay=data.get("visibility_delay", 0),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            published_at=data.get("published_at"),
        )


# ============================================================================
# Transport Abstraction
# ============================================================================


class TransportType(str, Enum):
    """
    Loại message transport.

    - kafka: Apache Kafka (high throughput, partitioned, durable)
    - rabbitmq: RabbitMQ (AMQP, flexible routing, dead letter)
    - sqs: AWS SQS (managed, FIFO, DLQ built-in)
    - sns: AWS SNS (fan-out, pub/sub, multi-protocol)
    - redis: Redis Streams (in-memory, low latency)
    - in_memory: In-process event bus (testing, single-process)
    """
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    SQS = "sqs"
    SNS = "sns"
    REDIS = "redis"
    IN_MEMORY = "in_memory"


class DeliveryGuarantee(str, Enum):
    """
    Delivery guarantee cho event transport.

    - at_most_once: Event được deliver nhiều nhất 1 lần (có thể mất)
    - at_least_once: Event được deliver ít nhất 1 lần (có thể duplicate)
    - exactly_once: Event được deliver đúng 1 lần (đắt giá nhất)
    """
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class TransportConfig:
    """
    Configuration cho event transport.

    Abstraction layer cho message broker — swap giữa Kafka, RabbitMQ, SQS
    không cần thay đổi business logic.

    Attributes:
        transport_type: Loại transport (kafka, rabbitmq, sqs, sns, redis, in_memory)
        connection_string: Connection string (vd: "kafka://broker:9092")
        delivery_guarantee: Delivery guarantee (at_most_once, at_least_once, exactly_once)
        max_retries: Số lần retry tối đa khi publish thất bại
        retry_backoff_ms: Backoff giữa retries (milliseconds)
        batch_size: Số events trong 1 batch publish
        batch_timeout_ms: Timeout trước khi flush batch (milliseconds)
        enable_tls: Enable TLS cho connection
        description: Mô tả transport
    """
    transport_type: TransportType = TransportType.KAFKA
    connection_string: str = ""
    delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    max_retries: int = 3
    retry_backoff_ms: int = 1000
    batch_size: int = 100
    batch_timeout_ms: int = 1000
    enable_tls: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate transport config sau khi khởi tạo."""
        if self.max_retries < 0:
            self.max_retries = 0
        if self.retry_backoff_ms < 1:
            self.retry_backoff_ms = 1000
        if self.batch_size < 1:
            self.batch_size = 100

    def to_dict(self) -> dict[str, Any]:
        """Chuyển transport config sang dict format."""
        return {
            "transport_type": self.transport_type.value,
            "connection_string": self.connection_string,
            "delivery_guarantee": self.delivery_guarantee.value,
            "max_retries": self.max_retries,
            "retry_backoff_ms": self.retry_backoff_ms,
            "batch_size": self.batch_size,
            "batch_timeout_ms": self.batch_timeout_ms,
            "enable_tls": self.enable_tls,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransportConfig":
        """Tạo TransportConfig từ dict."""
        return cls(
            transport_type=TransportType(data.get("transport_type", "kafka")),
            connection_string=data.get("connection_string", ""),
            delivery_guarantee=DeliveryGuarantee(data.get("delivery_guarantee", "at_least_once")),
            max_retries=data.get("max_retries", 3),
            retry_backoff_ms=data.get("retry_backoff_ms", 1000),
            batch_size=data.get("batch_size", 100),
            batch_timeout_ms=data.get("batch_timeout_ms", 1000),
            enable_tls=data.get("enable_tls", True),
            description=data.get("description", ""),
        )


# ============================================================================
# Dead Letter Queue (DLQ)
# ============================================================================


class DLQPolicy(str, Enum):
    """
    Chính sách xử lý dead letter queue.

    - move_after_retries: Move message sang DLQ sau khi hết retries
    - move_on_permanent_error: Move ngay khi gặp permanent error
    - hold_for_review: Keep trong queue, flag cho manual review
    - alert_only: Chỉ alert, không move
    """
    MOVE_AFTER_RETRIES = "move_after_retries"
    MOVE_ON_PERMANENT_ERROR = "move_on_permanent_error"
    HOLD_FOR_REVIEW = "hold_for_review"
    ALERT_ONLY = "alert_only"


@dataclass
class DLQConfig:
    """
    Configuration cho Dead Letter Queue.

    DLQ thu thập messages không thể process được — để debug, retry manual,
    hoặc alert team.

    Attributes:
        enabled: Có enable DLQ không
        queue_name: Tên DLQ queue (vd: "events.dlq")
        policy: Policy xử lý DLQ (move_after_retries, move_on_permanent_error, ...)
        max_retries_before_dlq: Số retries trước khi move sang DLQ
        retention_hours: Bao lâu giữ messages trong DLQ
        alert_on_dlq: Có alert khi message vào DLQ không
        alert_channels: Channels alert (vd: ["slack", "pagerduty"])
        description: Mô tả DLQ config
    """
    enabled: bool = True
    queue_name: str = ""
    policy: DLQPolicy = DLQPolicy.MOVE_AFTER_RETRIES
    max_retries_before_dlq: int = 5
    retention_hours: int = 168
    alert_on_dlq: bool = True
    alert_channels: list[str] = field(default_factory=lambda: ["slack"])
    description: str = ""

    def __post_init__(self) -> None:
        """Validate DLQ config sau khi khởi tạo."""
        if self.max_retries_before_dlq < 1:
            self.max_retries_before_dlq = 5
        if self.retention_hours < 1:
            self.retention_hours = 168
        if not self.alert_channels:
            self.alert_channels = ["slack"]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DLQ config sang dict format."""
        return {
            "enabled": self.enabled,
            "queue_name": self.queue_name,
            "policy": self.policy.value,
            "max_retries_before_dlq": self.max_retries_before_dlq,
            "retention_hours": self.retention_hours,
            "alert_on_dlq": self.alert_on_dlq,
            "alert_channels": self.alert_channels,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DLQConfig":
        """Tạo DLQConfig từ dict."""
        return cls(
            enabled=data.get("enabled", True),
            queue_name=data.get("queue_name", ""),
            policy=DLQPolicy(data.get("policy", "move_after_retries")),
            max_retries_before_dlq=data.get("max_retries_before_dlq", 5),
            retention_hours=data.get("retention_hours", 168),
            alert_on_dlq=data.get("alert_on_dlq", True),
            alert_channels=data.get("alert_channels", ["slack"]),
            description=data.get("description", ""),
        )


# ============================================================================
# Event Sourcing
# ============================================================================


class EventStoreBackend(str, Enum):
    """
    Backend cho event store.

    - database: Relational database (PostgreSQL, MySQL)
    - kafka: Kafka với compacted topic
    - dynamodb: DynamoDB table
    - mongodb: MongoDB collection
    """
    DATABASE = "database"
    KAFKA = "kafka"
    DYNAMODB = "dynamodb"
    MONGODB = "mongodb"


class SnapshotStrategy(str, Enum):
    """
    Chiến lược snapshot cho event-sourced aggregate.

    - periodic: Snapshot mỗi N events
    - size_based: Snapshot khi event log vượt kích thước
    - version_based: Snapshot mỗi N versions
    """
    PERIODIC = "periodic"
    SIZE_BASED = "size_based"
    VERSION_BASED = "version_based"


@dataclass
class EventStoreConfig:
    """
    Configuration cho event store — backbone của event sourcing.

    Event store lưu sequence immutable events. Replay events để tái tạo
    state của aggregate root.

    Attributes:
        backend: Backend lưu trữ events (database, kafka, dynamodb, mongodb)
        connection_string: Connection string cho backend
        snapshot_strategy: Chiến lược snapshot (periodic, size_based, version_based)
        snapshot_interval: Interval giữa snapshots (số events hoặc versions)
        enable_optimistic_locking: Optimistic concurrency control
        enable_outbox: Sử dụng outbox pattern cho reliable delivery
        max_batch_size: Số events tối đa trong 1 batch append
        description: Mô tả event store
    """
    backend: EventStoreBackend = EventStoreBackend.DATABASE
    connection_string: str = ""
    snapshot_strategy: SnapshotStrategy = SnapshotStrategy.PERIODIC
    snapshot_interval: int = 100
    enable_optimistic_locking: bool = True
    enable_outbox: bool = True
    max_batch_size: int = 50
    description: str = ""

    def __post_init__(self) -> None:
        """Validate event store config sau khi khởi tạo."""
        if self.snapshot_interval < 1:
            self.snapshot_interval = 100
        if self.max_batch_size < 1:
            self.max_batch_size = 50

    def to_dict(self) -> dict[str, Any]:
        """Chuyển event store config sang dict format."""
        return {
            "backend": self.backend.value,
            "connection_string": self.connection_string,
            "snapshot_strategy": self.snapshot_strategy.value,
            "snapshot_interval": self.snapshot_interval,
            "enable_optimistic_locking": self.enable_optimistic_locking,
            "enable_outbox": self.enable_outbox,
            "max_batch_size": self.max_batch_size,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventStoreConfig":
        """Tạo EventStoreConfig từ dict."""
        return cls(
            backend=EventStoreBackend(data.get("backend", "database")),
            connection_string=data.get("connection_string", ""),
            snapshot_strategy=SnapshotStrategy(data.get("snapshot_strategy", "periodic")),
            snapshot_interval=data.get("snapshot_interval", 100),
            enable_optimistic_locking=data.get("enable_optimistic_locking", True),
            enable_outbox=data.get("enable_outbox", True),
            max_batch_size=data.get("max_batch_size", 50),
            description=data.get("description", ""),
        )


# ============================================================================
# Retry Policy
# ============================================================================


class RetryStrategy(str, Enum):
    """
    Chiến lược retry.

    - fixed: Fixed delay giữa retries
    - exponential: Exponential backoff
    - exponential_with_jitter: Exponential backoff + random jitter
    - fibonacci: Fibonacci backoff
    """
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"
    FIBONACCI = "fibonacci"


@dataclass
class RetryPolicy:
    """
    Retry policy cho event processing.

    Attributes:
        strategy: Chiến lược retry (fixed, exponential, exponential_with_jitter, fibonacci)
        max_attempts: Số lần retry tối đa
        initial_delay_ms: Delay ban đầu (milliseconds)
        max_delay_ms: Delay tối đa (milliseconds)
        multiplier: Multiplier cho exponential/fibonacci backoff
        retryable_errors: Danh sách error codes có thể retry
        description: Mô tả retry policy
    """
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER
    max_attempts: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    multiplier: float = 2.0
    retryable_errors: list[str] = field(default_factory=lambda: ["timeout", "connection_error", "rate_limit"])
    description: str = ""

    def __post_init__(self) -> None:
        """Validate retry policy sau khi khởi tạo."""
        if self.max_attempts < 0:
            self.max_attempts = 3
        if self.initial_delay_ms < 1:
            self.initial_delay_ms = 1000
        if self.multiplier < 1.0:
            self.multiplier = 2.0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển retry policy sang dict format."""
        return {
            "strategy": self.strategy.value,
            "max_attempts": self.max_attempts,
            "initial_delay_ms": self.initial_delay_ms,
            "max_delay_ms": self.max_delay_ms,
            "multiplier": self.multiplier,
            "retryable_errors": self.retryable_errors,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetryPolicy":
        """Tạo RetryPolicy từ dict."""
        return cls(
            strategy=RetryStrategy(data.get("strategy", "exponential_with_jitter")),
            max_attempts=data.get("max_attempts", 3),
            initial_delay_ms=data.get("initial_delay_ms", 1000),
            max_delay_ms=data.get("max_delay_ms", 30000),
            multiplier=data.get("multiplier", 2.0),
            retryable_errors=data.get("retryable_errors", ["timeout", "connection_error", "rate_limit"]),
            description=data.get("description", ""),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "EventDefinition",
    "OutboxEntry",
    "TransportType",
    "DeliveryGuarantee",
    "TransportConfig",
    "DLQPolicy",
    "DLQConfig",
    "EventStoreBackend",
    "SnapshotStrategy",
    "EventStoreConfig",
    "RetryStrategy",
    "RetryPolicy",
]