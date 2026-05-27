"""
Comprehensive tests for CP05 Event-Driven Architecture models.

Tests cover:
- EventDefinition
- OutboxEntry (with tenant_id)
- TransportConfig
- DLQConfig
- EventStoreConfig
- RetryPolicy
- IdempotentConsumer
- EventSchemaVersion
- EventStream
- CQRSProjection
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp05_event_driven.models import (
    CQRSProjection,
    DeliveryGuarantee,
    DLQConfig,
    DLQDashboardConfig,
    DLQManagementConfig,
    DLQMessage,
    DLQPolicy,
    DLQStatus,
    EventDefinition,
    EventSchemaVersion,
    EventStoreBackend,
    EventStoreConfig,
    EventStream,
    IdempotencyStrategy,
    IdempotentConsumer,
    MaterializationStrategy,
    OutboxEntry,
    RetryPolicy,
    RetryStrategy,
    SchemaEvolutionPolicy,
    SnapshotStrategy,
    TransportConfig,
    TransportType,
)


# ============================================================================
# EventDefinition Tests
# ============================================================================


class TestEventDefinition:
    def test_creation_minimal(self):
        event = EventDefinition(event_name="order.created")
        assert event.event_name == "order.created"
        assert event.payload_fields == []
        assert event.topic == "default"
        assert event.version == "1.0"
        assert event.tenant_id is None
        assert event.schema_fields is None

    def test_creation_full(self):
        event = EventDefinition(
            event_name="payment.completed",
            payload_fields=["payment_id", "amount", "currency"],
            topic="payments",
            version="2.0",
            tenant_id="tenant_123",
            schema_fields={"payment_id": {"type": "string"}},
        )
        assert event.event_name == "payment.completed"
        assert event.topic == "payments"
        assert event.version == "2.0"
        assert event.tenant_id == "tenant_123"
        assert event.schema_fields == {"payment_id": {"type": "string"}}

    def test_empty_event_name_raises(self):
        with pytest.raises(ValueError, match="không được để trống"):
            EventDefinition(event_name="")

    def test_whitespace_event_name_raises(self):
        with pytest.raises(ValueError, match="không được để trống"):
            EventDefinition(event_name="   ")

    def test_to_dict_minimal(self):
        event = EventDefinition(event_name="test.event")
        result = event.to_dict()
        assert result == {
            "event_name": "test.event",
            "payload_fields": [],
            "topic": "default",
            "version": "1.0",
        }

    def test_to_dict_with_tenant_and_schema(self):
        event = EventDefinition(
            event_name="test.event",
            tenant_id="t1",
            schema_fields={"id": {"type": "int"}},
        )
        result = event.to_dict()
        assert result["tenant_id"] == "t1"
        assert result["schema_fields"] == {"id": {"type": "int"}}

    def test_from_dict(self):
        data = {
            "event_name": "order.created",
            "payload_fields": ["order_id"],
            "topic": "orders",
            "version": "1.1",
            "tenant_id": "t1",
            "schema_fields": {"order_id": {"type": "string"}},
        }
        event = EventDefinition.from_dict(data)
        assert event.event_name == "order.created"
        assert event.topic == "orders"
        assert event.version == "1.1"

    def test_from_dict_defaults(self):
        data = {"event_name": "x"}
        event = EventDefinition.from_dict(data)
        assert event.topic == "default"
        assert event.version == "1.0"


# ============================================================================
# OutboxEntry Tests
# ============================================================================


class TestOutboxEntry:
    def test_creation_minimal(self):
        entry = OutboxEntry(event_name="test.event")
        assert entry.event_name == "test.event"
        assert entry.payload == {}
        assert entry.topic == "default"
        assert entry.status == "pending"
        assert entry.tenant_id is None

    def test_creation_full(self):
        entry = OutboxEntry(
            event_name="order.created",
            payload={"order_id": "123"},
            topic="orders",
            transaction_id="txn_456",
            visibility_delay=30,
            tenant_id="tenant_1",
        )
        assert entry.tenant_id == "tenant_1"
        assert entry.transaction_id == "txn_456"
        assert entry.visibility_delay == 30

    def test_to_dict_minimal(self):
        entry = OutboxEntry(event_name="x")
        result = entry.to_dict()
        assert "tenant_id" not in result
        assert "transaction_id" not in result

    def test_to_dict_with_tenant_id(self):
        entry = OutboxEntry(event_name="x", tenant_id="t1")
        result = entry.to_dict()
        assert result["tenant_id"] == "t1"

    def test_to_dict_with_all_fields(self):
        entry = OutboxEntry(
            event_name="x",
            transaction_id="txn",
            visibility_delay=10,
            created_at="2024-01-01",
            published_at="2024-01-02",
            tenant_id="t1",
        )
        result = entry.to_dict()
        assert result["transaction_id"] == "txn"
        assert result["visibility_delay"] == 10
        assert result["tenant_id"] == "t1"

    def test_to_dict_zero_delay_excluded(self):
        entry = OutboxEntry(event_name="x", visibility_delay=0)
        result = entry.to_dict()
        assert "visibility_delay" not in result

    def test_from_dict(self):
        data = {
            "event_name": "x",
            "payload": {"k": "v"},
            "tenant_id": "t1",
            "status": "published",
        }
        entry = OutboxEntry.from_dict(data)
        assert entry.tenant_id == "t1"
        assert entry.status == "published"


# ============================================================================
# TransportConfig Tests
# ============================================================================


class TestTransportConfig:
    def test_defaults(self):
        config = TransportConfig()
        assert config.transport_type == TransportType.KAFKA
        assert config.delivery_guarantee == DeliveryGuarantee.AT_LEAST_ONCE

    def test_negative_retries_fixed(self):
        config = TransportConfig(max_retries=-1)
        assert config.max_retries == 0

    def test_zero_backoff_fixed(self):
        config = TransportConfig(retry_backoff_ms=0)
        assert config.retry_backoff_ms == 1000

    def test_zero_batch_size_fixed(self):
        config = TransportConfig(batch_size=0)
        assert config.batch_size == 100

    def test_to_dict(self):
        config = TransportConfig()
        result = config.to_dict()
        assert result["transport_type"] == "kafka"
        assert result["delivery_guarantee"] == "at_least_once"

    def test_from_dict(self):
        data = {"transport_type": "rabbitmq", "max_retries": 10}
        config = TransportConfig.from_dict(data)
        assert config.transport_type == TransportType.RABBITMQ
        assert config.max_retries == 10


# ============================================================================
# DLQConfig Tests
# ============================================================================


class TestDLQConfig:
    def test_defaults(self):
        config = DLQConfig()
        assert config.enabled is True
        assert config.policy == DLQPolicy.MOVE_AFTER_RETRIES

    def test_zero_retries_fixed(self):
        config = DLQConfig(max_retries_before_dlq=0)
        assert config.max_retries_before_dlq == 5

    def test_zero_retention_fixed(self):
        config = DLQConfig(retention_hours=0)
        assert config.retention_hours == 168

    def test_empty_alert_channels_fixed(self):
        config = DLQConfig(alert_channels=[])
        assert config.alert_channels == ["slack"]

    def test_to_dict(self):
        config = DLQConfig(queue_name="dlq")
        result = config.to_dict()
        assert result["queue_name"] == "dlq"

    def test_from_dict(self):
        data = {"enabled": False, "policy": "alert_only"}
        config = DLQConfig.from_dict(data)
        assert config.enabled is False
        assert config.policy == DLQPolicy.ALERT_ONLY


# ============================================================================
# EventStoreConfig Tests
# ============================================================================


class TestEventStoreConfig:
    def test_defaults(self):
        config = EventStoreConfig()
        assert config.backend == EventStoreBackend.DATABASE
        assert config.snapshot_strategy == SnapshotStrategy.PERIODIC

    def test_zero_snapshot_interval_fixed(self):
        config = EventStoreConfig(snapshot_interval=0)
        assert config.snapshot_interval == 100

    def test_zero_batch_size_fixed(self):
        config = EventStoreConfig(max_batch_size=0)
        assert config.max_batch_size == 50

    def test_to_dict(self):
        config = EventStoreConfig()
        result = config.to_dict()
        assert result["backend"] == "database"

    def test_from_dict(self):
        data = {"backend": "kafka", "snapshot_interval": 50}
        config = EventStoreConfig.from_dict(data)
        assert config.backend == EventStoreBackend.KAFKA
        assert config.snapshot_interval == 50


# ============================================================================
# RetryPolicy Tests
# ============================================================================


class TestRetryPolicy:
    def test_defaults(self):
        policy = RetryPolicy()
        assert policy.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER
        assert policy.max_attempts == 3

    def test_negative_attempts_fixed(self):
        policy = RetryPolicy(max_attempts=-1)
        assert policy.max_attempts == 3

    def test_zero_delay_fixed(self):
        policy = RetryPolicy(initial_delay_ms=0)
        assert policy.initial_delay_ms == 1000

    def test_low_multiplier_fixed(self):
        policy = RetryPolicy(multiplier=0.5)
        assert policy.multiplier == 2.0

    def test_to_dict(self):
        policy = RetryPolicy()
        result = policy.to_dict()
        assert result["strategy"] == "exponential_with_jitter"

    def test_from_dict(self):
        data = {"strategy": "fixed", "max_attempts": 10}
        policy = RetryPolicy.from_dict(data)
        assert policy.strategy == RetryStrategy.FIXED
        assert policy.max_attempts == 10


# ============================================================================
# IdempotentConsumer Tests
# ============================================================================


class TestIdempotentConsumer:
    def test_defaults(self):
        consumer = IdempotentConsumer()
        assert consumer.strategy == IdempotencyStrategy.DEDUP_BY_EVENT_ID
        assert consumer.dedup_window_seconds == 3600

    def test_low_window_fixed(self):
        consumer = IdempotentConsumer(dedup_window_seconds=10)
        assert consumer.dedup_window_seconds == 3600

    def test_zero_checkpoint_interval_fixed(self):
        consumer = IdempotentConsumer(checkpoint_interval=0)
        assert consumer.checkpoint_interval == 100

    def test_to_dict(self):
        consumer = IdempotentConsumer()
        result = consumer.to_dict()
        assert result["strategy"] == "dedup_by_event_id"

    def test_from_dict(self):
        data = {"strategy": "dedup_by_business_key", "business_key_fields": ["order_id"]}
        consumer = IdempotentConsumer.from_dict(data)
        assert consumer.strategy == IdempotencyStrategy.DEDUP_BY_BUSINESS_KEY
        assert consumer.business_key_fields == ["order_id"]


# ============================================================================
# EventSchemaVersion Tests
# ============================================================================


class TestEventSchemaVersion:
    def test_creation_minimal(self):
        v = EventSchemaVersion(event_name="order.created")
        assert v.version == "1.0"
        assert v.evolution_policy == SchemaEvolutionPolicy.ADDITIVE_ONLY
        assert v.is_deprecated is False

    def test_empty_event_name_raises(self):
        with pytest.raises(ValueError):
            EventSchemaVersion(event_name="")

    def test_empty_version_fixed(self):
        v = EventSchemaVersion(event_name="x", version="")
        assert v.version == "1.0"

    def test_to_dict_with_deprecated(self):
        v = EventSchemaVersion(
            event_name="x",
            is_deprecated=True,
            deprecated_since="2024-01-01",
            migration_target="2.0",
        )
        result = v.to_dict()
        assert result["deprecated_since"] == "2024-01-01"
        assert result["migration_target"] == "2.0"

    def test_to_dict_without_optional(self):
        v = EventSchemaVersion(event_name="x")
        result = v.to_dict()
        assert "deprecated_since" not in result

    def test_from_dict(self):
        data = {"event_name": "x", "version": "3.0", "is_deprecated": True}
        v = EventSchemaVersion.from_dict(data)
        assert v.version == "3.0"
        assert v.is_deprecated is True


# ============================================================================
# EventStream Tests
# ============================================================================


class TestEventStream:
    def test_creation_minimal(self):
        s = EventStream(stream_id="stream_1")
        assert s.current_version == 0
        assert s.events == []

    def test_empty_stream_id_raises(self):
        with pytest.raises(ValueError):
            EventStream(stream_id="")

    def test_whitespace_stream_id_raises(self):
        with pytest.raises(ValueError):
            EventStream(stream_id="  ")

    def test_to_dict(self):
        s = EventStream(stream_id="s1", aggregate_type="Order", current_version=5)
        result = s.to_dict()
        assert result["stream_id"] == "s1"
        assert result["aggregate_type"] == "Order"
        assert result["current_version"] == 5

    def test_from_dict(self):
        data = {"stream_id": "s1", "events": [{"type": "created"}]}
        s = EventStream.from_dict(data)
        assert len(s.events) == 1


# ============================================================================
# CQRSProjection Tests
# ============================================================================


class TestCQRSProjection:
    def test_creation_minimal(self):
        p = CQRSProjection(
            projection_id="p1",
            source_events=["order.created"],
            target_entity="OrderView",
        )
        assert p.materialization == MaterializationStrategy.INCREMENTAL
        assert p.refresh_interval_seconds == 300

    def test_empty_projection_id_raises(self):
        with pytest.raises(ValueError):
            CQRSProjection(projection_id="", source_events=["x"], target_entity="y")

    def test_no_source_events_raises(self):
        with pytest.raises(ValueError, match="source event"):
            CQRSProjection(projection_id="p1", source_events=[], target_entity="y")

    def test_empty_target_entity_raises(self):
        with pytest.raises(ValueError):
            CQRSProjection(projection_id="p1", source_events=["x"], target_entity="")

    def test_to_dict(self):
        p = CQRSProjection(
            projection_id="p1",
            source_events=["e1", "e2"],
            target_entity="View",
            enable_cdc=True,
        )
        result = p.to_dict()
        assert result["materialization"] == "incremental"
        assert result["enable_cdc"] is True

    def test_from_dict(self):
        data = {
            "projection_id": "p1",
            "source_events": ["e1"],
            "target_entity": "v",
            "materialization": "batch",
        }
        p = CQRSProjection.from_dict(data)
        assert p.materialization == MaterializationStrategy.BATCH


# ============================================================================
# DLQStatus Enum Tests
# ============================================================================


class TestDLQStatus:
    def test_status_values(self):
        assert DLQStatus.ACTIVE.value == "active"
        assert DLQStatus.ARCHIVED.value == "archived"
        assert DLQStatus.RETRYING.value == "retrying"
        assert DLQStatus.PURGED.value == "purged"


# ============================================================================
# DLQManagementConfig Tests
# ============================================================================


class TestDLQManagementConfig:
    def test_creation_minimal(self):
        config = DLQManagementConfig(
            id="dlq.1",
            name="Test DLQ",
            source_topic="orders.failed",
        )
        assert config.id == "dlq.1"
        assert config.name == "Test DLQ"
        assert config.source_topic == "orders.failed"
        assert config.max_retries == 3
        assert config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.initial_delay_seconds == 10
        assert config.max_delay_seconds == 3600
        assert config.visibility_timeout_seconds == 300
        assert config.retention_days == 7
        assert config.auto_purge is False
        assert config.alert_on_threshold == 100

    def test_creation_full(self):
        config = DLQManagementConfig(
            id="dlq.2",
            name="Full DLQ",
            source_topic="events.failed",
            max_retries=5,
            retry_strategy=RetryStrategy.ADAPTIVE,
            initial_delay_seconds=5,
            max_delay_seconds=7200,
            retention_days=30,
            auto_purge=True,
            alert_on_threshold=50,
        )
        assert config.max_retries == 5
        assert config.retry_strategy == RetryStrategy.ADAPTIVE
        assert config.auto_purge is True
        assert config.alert_on_threshold == 50

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="DLQ id không được để trống"):
            DLQManagementConfig(id="", name="x", source_topic="y")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="DLQ name không được để trống"):
            DLQManagementConfig(id="x", name="", source_topic="y")

    def test_empty_source_topic_raises(self):
        with pytest.raises(ValueError, match="source_topic không được để trống"):
            DLQManagementConfig(id="x", name="y", source_topic="")

    def test_negative_retries_fixed(self):
        config = DLQManagementConfig(id="x", name="y", source_topic="z", max_retries=-1)
        assert config.max_retries == 3

    def test_zero_delay_fixed(self):
        config = DLQManagementConfig(id="x", name="y", source_topic="z", initial_delay_seconds=0)
        assert config.initial_delay_seconds == 10

    def test_max_delay_less_than_initial_fixed(self):
        config = DLQManagementConfig(id="x", name="y", source_topic="z", initial_delay_seconds=50, max_delay_seconds=10)
        assert config.max_delay_seconds == 100

    def test_zero_retention_fixed(self):
        config = DLQManagementConfig(id="x", name="y", source_topic="z", retention_days=0)
        assert config.retention_days == 7

    def test_zero_alert_threshold_fixed(self):
        config = DLQManagementConfig(id="x", name="y", source_topic="z", alert_on_threshold=0)
        assert config.alert_on_threshold == 100

    def test_to_dict(self):
        config = DLQManagementConfig(
            id="dlq.1",
            name="Test",
            source_topic="topic",
            max_retries=5,
            auto_purge=True,
        )
        result = config.to_dict()
        assert result["id"] == "dlq.1"
        assert result["retry_strategy"] == "exponential_backoff"
        assert result["auto_purge"] is True

    def test_from_dict(self):
        data = {
            "id": "dlq.from",
            "name": "From Dict",
            "source_topic": "from.topic",
            "retry_strategy": "adaptive",
            "auto_purge": True,
        }
        config = DLQManagementConfig.from_dict(data)
        assert config.id == "dlq.from"
        assert config.retry_strategy == RetryStrategy.ADAPTIVE
        assert config.auto_purge is True


# ============================================================================
# DLQMessage Tests
# ============================================================================


class TestDLQMessage:
    def test_creation_minimal(self):
        msg = DLQMessage(
            id="msg.1",
            original_message={"order_id": "123"},
            error_reason="Schema validation failed",
        )
        assert msg.id == "msg.1"
        assert msg.retry_count == 0
        assert msg.max_retries == 3
        assert msg.headers == {}

    def test_creation_full(self):
        msg = DLQMessage(
            id="msg.2",
            original_message={"data": "test"},
            error_reason="Timeout",
            retry_count=2,
            max_retries=5,
            first_failure_at="2024-01-01T00:00:00Z",
            last_retry_at="2024-01-01T01:00:00Z",
            source_topic="orders",
            headers={"content-type": "application/json"},
        )
        assert msg.retry_count == 2
        assert msg.first_failure_at == "2024-01-01T00:00:00Z"
        assert msg.source_topic == "orders"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="DLQ message id không được để trống"):
            DLQMessage(id="", original_message="x", error_reason="y")

    def test_empty_error_reason_raises(self):
        with pytest.raises(ValueError, match="error_reason không được để trống"):
            DLQMessage(id="x", original_message="x", error_reason="")

    def test_negative_retry_count_fixed(self):
        msg = DLQMessage(id="x", original_message="x", error_reason="y", retry_count=-5)
        assert msg.retry_count == 0

    def test_to_dict_minimal(self):
        msg = DLQMessage(id="m1", original_message="body", error_reason="err")
        result = msg.to_dict()
        assert result["id"] == "m1"
        assert "first_failure_at" not in result
        assert "headers" not in result

    def test_to_dict_full(self):
        msg = DLQMessage(
            id="m1",
            original_message="body",
            error_reason="err",
            first_failure_at="2024-01-01",
            last_retry_at="2024-01-02",
            source_topic="t1",
            headers={"k": "v"},
        )
        result = msg.to_dict()
        assert result["first_failure_at"] == "2024-01-01"
        assert result["headers"] == {"k": "v"}

    def test_from_dict(self):
        data = {
            "id": "m.from",
            "original_message": {"payload": "data"},
            "error_reason": "parse error",
            "retry_count": 2,
            "headers": {"x-correlation-id": "abc"},
        }
        msg = DLQMessage.from_dict(data)
        assert msg.id == "m.from"
        assert msg.retry_count == 2
        assert msg.headers == {"x-correlation-id": "abc"}


# ============================================================================
# DLQDashboardConfig Tests
# ============================================================================


class TestDLQDashboardConfig:
    def test_creation_minimal(self):
        config = DLQDashboardConfig(
            id="dash.1",
            name="DLQ Dashboard",
        )
        assert config.enabled is True
        assert config.auto_retry is False
        assert config.retry_batch_size == 10
        assert config.purge_after_days == 7
        assert config.notification_on_new_message is True
        assert config.slack_webhook == ""
        assert config.email_recipients == []

    def test_creation_full(self):
        config = DLQDashboardConfig(
            id="dash.2",
            name="Full Dashboard",
            enabled=False,
            auto_retry=True,
            retry_batch_size=50,
            purge_after_days=14,
            notification_on_new_message=False,
            slack_webhook="https://hooks.slack.com/test",
            email_recipients=["ops@example.com"],
        )
        assert config.enabled is False
        assert config.auto_retry is True
        assert config.retry_batch_size == 50
        assert config.email_recipients == ["ops@example.com"]

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="DLQ dashboard id không được để trống"):
            DLQDashboardConfig(id="", name="x")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="DLQ dashboard name không được để trống"):
            DLQDashboardConfig(id="x", name="")

    def test_zero_batch_size_fixed(self):
        config = DLQDashboardConfig(id="x", name="y", retry_batch_size=0)
        assert config.retry_batch_size == 10

    def test_zero_purge_days_fixed(self):
        config = DLQDashboardConfig(id="x", name="y", purge_after_days=0)
        assert config.purge_after_days == 7

    def test_to_dict(self):
        config = DLQDashboardConfig(
            id="d1",
            name="Test",
            auto_retry=True,
            slack_webhook="https://hooks.slack.com/test",
            email_recipients=["a@b.com"],
        )
        result = config.to_dict()
        assert result["id"] == "d1"
        assert result["auto_retry"] is True
        assert result["slack_webhook"] == "https://hooks.slack.com/test"
        assert result["email_recipients"] == ["a@b.com"]

    def test_from_dict(self):
        data = {
            "id": "d.from",
            "name": "From Dict",
            "enabled": False,
            "auto_retry": True,
            "retry_batch_size": 20,
            "email_recipients": ["ops@test.com"],
        }
        config = DLQDashboardConfig.from_dict(data)
        assert config.id == "d.from"
        assert config.enabled is False
        assert config.retry_batch_size == 20


# ============================================================================
# Enum Coverage Tests
# ============================================================================


class TestEnumValues:
    def test_transport_type_values(self):
        assert TransportType.KAFKA.value == "kafka"
        assert TransportType.RABBITMQ.value == "rabbitmq"
        assert TransportType.SQS.value == "sqs"
        assert TransportType.SNS.value == "sns"
        assert TransportType.REDIS.value == "redis"
        assert TransportType.IN_MEMORY.value == "in_memory"

    def test_delivery_guarantee_values(self):
        assert DeliveryGuarantee.AT_MOST_ONCE.value == "at_most_once"
        assert DeliveryGuarantee.AT_LEAST_ONCE.value == "at_least_once"
        assert DeliveryGuarantee.EXACTLY_ONCE.value == "exactly_once"

    def test_dlq_policy_values(self):
        assert DLQPolicy.MOVE_AFTER_RETRIES.value == "move_after_retries"
        assert DLQPolicy.MOVE_ON_PERMANENT_ERROR.value == "move_on_permanent_error"
        assert DLQPolicy.HOLD_FOR_REVIEW.value == "hold_for_review"
        assert DLQPolicy.ALERT_ONLY.value == "alert_only"

    def test_event_store_backend_values(self):
        assert EventStoreBackend.DATABASE.value == "database"
        assert EventStoreBackend.KAFKA.value == "kafka"
        assert EventStoreBackend.DYNAMODB.value == "dynamodb"
        assert EventStoreBackend.MONGODB.value == "mongodb"

    def test_snapshot_strategy_values(self):
        assert SnapshotStrategy.PERIODIC.value == "periodic"
        assert SnapshotStrategy.SIZE_BASED.value == "size_based"
        assert SnapshotStrategy.VERSION_BASED.value == "version_based"

    def test_retry_strategy_values(self):
        assert RetryStrategy.FIXED.value == "fixed"
        assert RetryStrategy.EXPONENTIAL.value == "exponential"
        assert RetryStrategy.EXPONENTIAL_WITH_JITTER.value == "exponential_with_jitter"
        assert RetryStrategy.FIBONACCI.value == "fibonacci"
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"
        assert RetryStrategy.ADAPTIVE.value == "adaptive"

    def test_idempotency_strategy_values(self):
        assert IdempotencyStrategy.DEDUP_BY_EVENT_ID.value == "dedup_by_event_id"
        assert IdempotencyStrategy.DEDUP_BY_BUSINESS_KEY.value == "dedup_by_business_key"
        assert IdempotencyStrategy.EXACTLY_ONCE_SEMANTIC.value == "exactly_once_semantic"
        assert IdempotencyStrategy.NONE.value == "none"

    def test_schema_evolution_policy_values(self):
        assert SchemaEvolutionPolicy.ADDITIVE_ONLY.value == "additive_only"
        assert SchemaEvolutionPolicy.ADDITIVE_WITH_DEFAULTS.value == "additive_with_defaults"
        assert SchemaEvolutionPolicy.ADDITIVE_AND_RENAME.value == "additive_and_rename"
        assert SchemaEvolutionPolicy.FREE_FORM.value == "free_form"

    def test_materialization_strategy_values(self):
        assert MaterializationStrategy.INCREMENTAL.value == "incremental"
        assert MaterializationStrategy.BATCH.value == "batch"
        assert MaterializationStrategy.HYBRID.value == "hybrid"
