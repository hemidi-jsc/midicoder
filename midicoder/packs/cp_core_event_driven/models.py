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
    tenant_id: str | None = None
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
        if self.tenant_id is not None:
            result["tenant_id"] = self.tenant_id
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
            tenant_id=data.get("tenant_id"),
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
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE = "adaptive"


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
# Idempotent Consumer
# ============================================================================


class IdempotencyStrategy(str, Enum):
    """
    Chiến lược đảm bảo idempotent consumer.

    - dedup_by_event_id: Lọc trùng dựa trên event_id (correlation_id)
    - dedup_by_business_key: Lọc trùng dựa trên business key (vd: order_id)
    - exactly_once_semantic: Dùng transactional receive (Kafka EOS, SQS FIFO)
    - none: Không đảm bảo idempotent (at-most-once)
    """
    DEDUP_BY_EVENT_ID = "dedup_by_event_id"
    DEDUP_BY_BUSINESS_KEY = "dedup_by_business_key"
    EXACTLY_ONCE_SEMANTIC = "exactly_once_semantic"
    NONE = "none"


@dataclass
class IdempotentConsumer:
    """
    Configuration cho idempotent event consumer.

    Attributes:
        strategy: Chiến lược idempotency
        dedup_window_seconds: Cửa sổ thời gian giữ dedup keys
        business_key_fields: Các fields dùng làm business key (vd: ["order_id"])
        enable_checkpoint: Có checkpoint progress không (cho restart safety)
        checkpoint_interval: Interval giữa các checkpoint (số events processed)
        description: Mô tả idempotent consumer config
    """
    strategy: IdempotencyStrategy = IdempotencyStrategy.DEDUP_BY_EVENT_ID
    dedup_window_seconds: int = 3600
    business_key_fields: list[str] = field(default_factory=list)
    enable_checkpoint: bool = True
    checkpoint_interval: int = 100
    description: str = ""

    def __post_init__(self) -> None:
        """Validate idempotent consumer config sau khi khởi tạo."""
        if self.dedup_window_seconds < 60:
            self.dedup_window_seconds = 3600
        if self.checkpoint_interval < 1:
            self.checkpoint_interval = 100

    def to_dict(self) -> dict[str, Any]:
        """Chuyển idempotent consumer config sang dict format."""
        return {
            "strategy": self.strategy.value,
            "dedup_window_seconds": self.dedup_window_seconds,
            "business_key_fields": self.business_key_fields,
            "enable_checkpoint": self.enable_checkpoint,
            "checkpoint_interval": self.checkpoint_interval,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IdempotentConsumer":
        """Tạo IdempotentConsumer từ dict."""
        return cls(
            strategy=IdempotencyStrategy(data.get("strategy", "dedup_by_event_id")),
            dedup_window_seconds=data.get("dedup_window_seconds", 3600),
            business_key_fields=data.get("business_key_fields", []),
            enable_checkpoint=data.get("enable_checkpoint", True),
            checkpoint_interval=data.get("checkpoint_interval", 100),
            description=data.get("description", ""),
        )


# ============================================================================
# Event Schema Versioning & Evolution
# ============================================================================


class SchemaEvolutionPolicy(str, Enum):
    """Chính sách evolution cho event schema."""
    ADDITIVE_ONLY = "additive_only"
    ADDITIVE_WITH_DEFAULTS = "additive_with_defaults"
    ADDITIVE_AND_RENAME = "additive_and_rename"
    FREE_FORM = "free_form"


@dataclass
class EventSchemaVersion:
    """
    Version tracking cho event schema — backward compatibility enforcement.

    Attributes:
        event_name: Tên event type
        version: Version string (vd: "1.0", "2.0")
        schema: JSON Schema definition cho event payload
        evolution_policy: Chính sách evolution cho version này
        is_deprecated: Có deprecated không
        deprecated_since: Từ khi nào deprecated (ISO date string)
        migration_target: Version target để migrate (nếu deprecated)
        description: Mô tả schema version
    """
    event_name: str
    version: str = "1.0"
    schema: dict[str, Any] = field(default_factory=dict)
    evolution_policy: SchemaEvolutionPolicy = SchemaEvolutionPolicy.ADDITIVE_ONLY
    is_deprecated: bool = False
    deprecated_since: str | None = None
    migration_target: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        """Validate event schema version sau khi khởi tạo."""
        if not self.event_name or not self.event_name.strip():
            raise ValueError("event_name không được để trống")
        if not self.version or not self.version.strip():
            self.version = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển event schema version sang dict format."""
        result: dict[str, Any] = {
            "event_name": self.event_name,
            "version": self.version,
            "schema": self.schema,
            "evolution_policy": self.evolution_policy.value,
            "is_deprecated": self.is_deprecated,
            "description": self.description,
        }
        if self.deprecated_since is not None:
            result["deprecated_since"] = self.deprecated_since
        if self.migration_target is not None:
            result["migration_target"] = self.migration_target
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventSchemaVersion":
        """Tạo EventSchemaVersion từ dict."""
        return cls(
            event_name=data.get("event_name", ""),
            version=data.get("version", "1.0"),
            schema=data.get("schema", {}),
            evolution_policy=SchemaEvolutionPolicy(data.get("evolution_policy", "additive_only")),
            is_deprecated=data.get("is_deprecated", False),
            deprecated_since=data.get("deprecated_since"),
            migration_target=data.get("migration_target"),
            description=data.get("description", ""),
        )


# ============================================================================
# Event Stream (Event Sourcing backbone)
# ============================================================================


@dataclass
class EventStream:
    """
    Event stream cho event-sourced aggregate.

    Attributes:
        stream_id: Unique ID cho stream (thường là aggregate_id)
        aggregate_type: Loại aggregate root (vd: "Order", "Customer")
        aggregate_id: ID của aggregate root
        events: Sequence của events trong stream
        current_version: Version hiện tại của stream (số events)
        max_version: Max version cho optimistic locking
        description: Mô tả event stream
    """
    stream_id: str
    aggregate_type: str = ""
    aggregate_id: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    current_version: int = 0
    max_version: int = 0
    description: str = ""

    def __post_init__(self) -> None:
        """Validate event stream sau khi khởi tạo."""
        if not self.stream_id or not self.stream_id.strip():
            raise ValueError("stream_id không được để trống")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển event stream sang dict format."""
        return {
            "stream_id": self.stream_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "events": self.events,
            "current_version": self.current_version,
            "max_version": self.max_version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventStream":
        """Tạo EventStream từ dict."""
        return cls(
            stream_id=data.get("stream_id", ""),
            aggregate_type=data.get("aggregate_type", ""),
            aggregate_id=data.get("aggregate_id", ""),
            events=data.get("events", []),
            current_version=data.get("current_version", 0),
            max_version=data.get("max_version", 0),
            description=data.get("description", ""),
        )


# ============================================================================
# CQRS Projection
# ============================================================================


class MaterializationStrategy(str, Enum):
    """Chiến lược materialization cho read model."""
    INCREMENTAL = "incremental"
    BATCH = "batch"
    HYBRID = "hybrid"


@dataclass
class CQRSProjection:
    """
    CQRS projection — transform write model events vào read model.

    Attributes:
        projection_id: Unique ID cho projection
        name: Tên projection (vd: "OrderDashboardView")
        source_events: List của event names để subscribe
        target_entity: Entity/table để materialize read model
        transformation: Transformation rules (JSON)
        materialization: Chiến lược materialization
        refresh_interval_seconds: Interval cho batch/hybrid materialization
        enable_cdc: Enable change data capture
        description: Mô tả projection
    """
    projection_id: str
    name: str = ""
    source_events: list[str] = field(default_factory=list)
    target_entity: str = ""
    transformation: dict[str, Any] = field(default_factory=dict)
    materialization: MaterializationStrategy = MaterializationStrategy.INCREMENTAL
    refresh_interval_seconds: int = 300
    enable_cdc: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate CQRS projection sau khi khởi tạo."""
        if not self.projection_id or not self.projection_id.strip():
            raise ValueError("projection_id không được để trống")
        if not self.source_events:
            raise ValueError("CQRS projection phải có ít nhất một source event")
        if not self.target_entity or not self.target_entity.strip():
            raise ValueError("target_entity không được để trống")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CQRS projection sang dict format."""
        return {
            "projection_id": self.projection_id,
            "name": self.name,
            "source_events": self.source_events,
            "target_entity": self.target_entity,
            "transformation": self.transformation,
            "materialization": self.materialization.value,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "enable_cdc": self.enable_cdc,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CQRSProjection":
        """Tạo CQRSProjection từ dict."""
        return cls(
            projection_id=data.get("projection_id", ""),
            name=data.get("name", ""),
            source_events=data.get("source_events", []),
            target_entity=data.get("target_entity", ""),
            transformation=data.get("transformation", {}),
            materialization=MaterializationStrategy(data.get("materialization", "incremental")),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 300),
            enable_cdc=data.get("enable_cdc", False),
            description=data.get("description", ""),
        )


# ============================================================================
# Centralized DLQ Management
# ============================================================================


class DLQStatus(str, Enum):
    """
    Trạng thái của Dead Letter Queue.

    - active: DLQ đang hoạt động, thu thập messages
    - archived: DLQ đã được lưu trữ (historical)
    - retrying: DLQ đang trong quá trình retry batch messages
    - purged: DLQ đã được purge (messages đã bị xóa)
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    RETRYING = "retrying"
    PURGED = "purged"


@dataclass
class DLQManagementConfig:
    """
    Cấu hình Dead Letter Queue cho centralized management.

    Mở rộng DLQConfig truyền thống với các tính năng management:
    exponential backoff, auto-purge, và dashboard integration.

    Attributes:
        id: Unique ID cho DLQ management config
        name: Tên hiển thị của DLQ
        source_topic: Topic/source mà DLQ nhận messages
        max_retries: Số lần retry tối đa trước khi message vào DLQ vĩnh viễn
        retry_strategy: Chiến lược retry (fixed_delay, exponential_backoff, linear_backoff, adaptive)
        initial_delay_seconds: Delay ban đầu giữa retries (giây)
        max_delay_seconds: Delay tối đa giữa retries (giây)
        visibility_timeout_seconds: Thời gian message bị ẩn trong queue khi đang processing
        retention_days: Số ngày giữ messages trong DLQ trước khi auto-purge
        auto_purge: Có tự động purge messages sau retention_days không
        alert_on_threshold: Alert khi DLQ vượt quá số messages này
        description: Mô tả DLQ config
    """
    id: str
    name: str
    source_topic: str
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay_seconds: int = 10
    max_delay_seconds: int = 3600
    visibility_timeout_seconds: int = 300
    retention_days: int = 7
    auto_purge: bool = False
    alert_on_threshold: int = 100
    description: str = ""

    def __post_init__(self) -> None:
        """Validate DLQ management config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise ValueError("DLQ id không được để trống")
        if not self.name or not self.name.strip():
            raise ValueError("DLQ name không được để trống")
        if not self.source_topic or not self.source_topic.strip():
            raise ValueError("DLQ source_topic không được để trống")
        if self.max_retries < 0:
            self.max_retries = 3
        if self.initial_delay_seconds < 1:
            self.initial_delay_seconds = 10
        if self.max_delay_seconds < self.initial_delay_seconds:
            self.max_delay_seconds = self.initial_delay_seconds * 2
        if self.visibility_timeout_seconds < 1:
            self.visibility_timeout_seconds = 300
        if self.retention_days < 1:
            self.retention_days = 7
        if self.alert_on_threshold < 1:
            self.alert_on_threshold = 100

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DLQ management config sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "source_topic": self.source_topic,
            "max_retries": self.max_retries,
            "retry_strategy": self.retry_strategy.value,
            "initial_delay_seconds": self.initial_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "visibility_timeout_seconds": self.visibility_timeout_seconds,
            "retention_days": self.retention_days,
            "auto_purge": self.auto_purge,
            "alert_on_threshold": self.alert_on_threshold,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DLQManagementConfig":
        """Tạo DLQManagementConfig từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            source_topic=data.get("source_topic", ""),
            max_retries=data.get("max_retries", 3),
            retry_strategy=RetryStrategy(data.get("retry_strategy", "exponential_backoff")),
            initial_delay_seconds=data.get("initial_delay_seconds", 10),
            max_delay_seconds=data.get("max_delay_seconds", 3600),
            visibility_timeout_seconds=data.get("visibility_timeout_seconds", 300),
            retention_days=data.get("retention_days", 7),
            auto_purge=data.get("auto_purge", False),
            alert_on_threshold=data.get("alert_on_threshold", 100),
            description=data.get("description", ""),
        )


@dataclass
class DLQMessage:
    """
    Message trong Dead Letter Queue.

    Đại diện cho một message không thể process được — được lưu trong DLQ
    để debug, retry manual, hoặc alert team.

    Attributes:
        id: Unique ID của message
        original_message: Raw message body gốc
        error_reason: Lý do message bị fail
        retry_count: Số lần đã retry (bắt đầu từ 0)
        max_retries: Số lần retry tối đa
        first_failure_at: Thời điểm fail đầu tiên (ISO timestamp)
        last_retry_at: Thời điểm retry cuối cùng (ISO timestamp)
        source_topic: Topic gốc của message
        headers: Headers/raw metadata của message
    """
    id: str
    original_message: Any
    error_reason: str
    retry_count: int = 0
    max_retries: int = 3
    first_failure_at: str = ""
    last_retry_at: str = ""
    source_topic: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate DLQ message sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise ValueError("DLQ message id không được để trống")
        if not self.error_reason or not self.error_reason.strip():
            raise ValueError("DLQ message error_reason không được để trống")
        if self.retry_count < 0:
            self.retry_count = 0
        if self.max_retries < 0:
            self.max_retries = 3

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DLQ message sang dict format."""
        result: dict[str, Any] = {
            "id": self.id,
            "original_message": self.original_message,
            "error_reason": self.error_reason,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
        if self.first_failure_at:
            result["first_failure_at"] = self.first_failure_at
        if self.last_retry_at:
            result["last_retry_at"] = self.last_retry_at
        if self.source_topic:
            result["source_topic"] = self.source_topic
        if self.headers:
            result["headers"] = self.headers
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DLQMessage":
        """Tạo DLQMessage từ dict."""
        return cls(
            id=data.get("id", ""),
            original_message=data.get("original_message"),
            error_reason=data.get("error_reason", ""),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            first_failure_at=data.get("first_failure_at", ""),
            last_retry_at=data.get("last_retry_at", ""),
            source_topic=data.get("source_topic", ""),
            headers=data.get("headers", {}),
        )


@dataclass
class DLQDashboardConfig:
    """
    Cấu hình DLQ management dashboard — UI centralized.

    Dashboard cho phép quan sát, retry manual, và purge messages từ DLQ.
    Integration với Slack/email cho notification khi có messages mới.

    Attributes:
        id: Unique ID cho dashboard config
        name: Tên hiển thị của dashboard
        enabled: Có enable dashboard không
        auto_retry: Có tự động retry messages trong DLQ không
        retry_batch_size: Số messages retry cùng lúc (khi auto_retry enabled)
        purge_after_days: Tự động purge messages sau bao nhiêu ngày
        notification_on_new_message: Có notify khi có message mới vào DLQ không
        slack_webhook: Webhook URL cho Slack notification
        email_recipients: Danh sách email để nhận notification
        description: Mô tả dashboard config
    """
    id: str
    name: str
    enabled: bool = True
    auto_retry: bool = False
    retry_batch_size: int = 10
    purge_after_days: int = 7
    notification_on_new_message: bool = True
    slack_webhook: str = ""
    email_recipients: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate DLQ dashboard config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise ValueError("DLQ dashboard id không được để trống")
        if not self.name or not self.name.strip():
            raise ValueError("DLQ dashboard name không được để trống")
        if self.retry_batch_size < 1:
            self.retry_batch_size = 10
        if self.purge_after_days < 1:
            self.purge_after_days = 7

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DLQ dashboard config sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "auto_retry": self.auto_retry,
            "retry_batch_size": self.retry_batch_size,
            "purge_after_days": self.purge_after_days,
            "notification_on_new_message": self.notification_on_new_message,
            "slack_webhook": self.slack_webhook,
            "email_recipients": self.email_recipients,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DLQDashboardConfig":
        """Tạo DLQDashboardConfig từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            auto_retry=data.get("auto_retry", False),
            retry_batch_size=data.get("retry_batch_size", 10),
            purge_after_days=data.get("purge_after_days", 7),
            notification_on_new_message=data.get("notification_on_new_message", True),
            slack_webhook=data.get("slack_webhook", ""),
            email_recipients=data.get("email_recipients", []),
            description=data.get("description", ""),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core models
    "EventDefinition",
    "OutboxEntry",
    # Transport abstraction
    "TransportType",
    "DeliveryGuarantee",
    "TransportConfig",
    # Dead Letter Queue
    "DLQPolicy",
    "DLQConfig",
    # Event Sourcing
    "EventStoreBackend",
    "SnapshotStrategy",
    "EventStoreConfig",
    # Retry
    "RetryStrategy",
    "RetryPolicy",
    # Idempotent Consumer
    "IdempotencyStrategy",
    "IdempotentConsumer",
    # Schema Versioning
    "SchemaEvolutionPolicy",
    "EventSchemaVersion",
    # Event Stream
    "EventStream",
    # CQRS Projection
    "MaterializationStrategy",
    "CQRSProjection",
    # Centralized DLQ Management
    "DLQStatus",
    "DLQManagementConfig",
    "DLQMessage",
    "DLQDashboardConfig",
]