"""Tests for CP05 recipes."""

from __future__ import annotations

from midicoder.packs.cp_core_event_driven.models import (
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
    TransportConfig,
    TransportType,
)
from midicoder.packs.cp_core_event_driven.recipes import (
    dlq_management_recipe,
    dlq_recipe,
    event_sourcing_recipe,
    idempotent_consumer_recipe,
    in_memory_transport,
    kafka_transport,
    outbox_recipe,
    rabbitmq_transport,
    redis_pubsub,
    retry_policy_recipe,
    sns_transport,
    sqs_transport,
)


# ============================================================================
# Transport Recipe Tests
# ============================================================================


class TestKafkaTransport:
    def test_defaults(self):
        config = kafka_transport()
        assert config.transport_type == TransportType.KAFKA
        assert config.delivery_guarantee == DeliveryGuarantee.EXACTLY_ONCE
        assert config.batch_size == 500

    def test_custom_brokers(self):
        config = kafka_transport(brokers="k1:9092,k2:9092")
        assert config.connection_string == "k1:9092,k2:9092"

    def test_custom_batch(self):
        config = kafka_transport(batch_size=1000)
        assert config.batch_size == 1000


class TestRabbitMQTransport:
    def test_defaults(self):
        config = rabbitmq_transport()
        assert config.transport_type == TransportType.RABBITMQ
        assert config.delivery_guarantee == DeliveryGuarantee.AT_LEAST_ONCE

    def test_custom_host(self):
        config = rabbitmq_transport(host="mq.example.com", port=5673)
        assert config.transport_type == TransportType.RABBITMQ


class TestRedisPubSub:
    def test_defaults(self):
        config = redis_pubsub()
        assert config.transport_type == TransportType.REDIS
        assert config.delivery_guarantee == DeliveryGuarantee.AT_MOST_ONCE

    def test_custom_port(self):
        config = redis_pubsub(port=6380, db=5)
        assert config.transport_type == TransportType.REDIS


class TestInMemoryTransport:
    def test_defaults(self):
        config = in_memory_transport()
        assert config.transport_type == TransportType.IN_MEMORY
        assert config.max_retries == 0
        assert config.connection_string == ""


class TestSQSTransport:
    def test_defaults(self):
        config = sqs_transport()
        assert config.transport_type == TransportType.SQS
        assert config.batch_size == 10
        assert config.enable_tls is True


class TestSNSTransport:
    def test_defaults(self):
        config = sns_transport()
        assert config.transport_type == TransportType.SNS
        assert config.batch_size == 10


# ============================================================================
# Event Sourcing Recipe Tests
# ============================================================================


class TestEventSourcingRecipe:
    def test_defaults(self):
        config = event_sourcing_recipe()
        assert isinstance(config, EventStoreConfig)
        assert config.backend == EventStoreBackend.DATABASE
        assert config.enable_optimistic_locking is True

    def test_kafka_backend(self):
        config = event_sourcing_recipe(backend=EventStoreBackend.KAFKA, snapshot_interval=50)
        assert config.backend == EventStoreBackend.KAFKA
        assert config.snapshot_interval == 50


# ============================================================================
# Outbox Recipe Tests
# ============================================================================


class TestOutboxRecipe:
    def test_defaults(self):
        result = outbox_recipe()
        assert result["visibility_delay"] == 0
        assert result["max_retries"] == 5
        assert result["transport"] is None

    def test_with_transport(self):
        transport = in_memory_transport()
        result = outbox_recipe(transport=transport)
        assert result["transport"]["transport_type"] == "in_memory"


# ============================================================================
# DLQ Recipe Tests
# ============================================================================


class TestDLQRecipe:
    def test_defaults(self):
        config = dlq_recipe()
        assert isinstance(config, DLQConfig)
        assert config.queue_name == "events.dlq"
        assert config.alert_channels == ["slack"]

    def test_custom_channels(self):
        config = dlq_recipe(alert_channels=["pagerduty", "slack"])
        assert config.alert_channels == ["pagerduty", "slack"]


# ============================================================================
# Idempotent Consumer Recipe Tests
# ============================================================================


class TestIdempotentConsumerRecipe:
    def test_defaults(self):
        consumer = idempotent_consumer_recipe()
        assert isinstance(consumer, IdempotentConsumer)
        assert consumer.strategy == IdempotencyStrategy.DEDUP_BY_EVENT_ID

    def test_business_key(self):
        consumer = idempotent_consumer_recipe(
            strategy=IdempotencyStrategy.DEDUP_BY_BUSINESS_KEY,
            business_key_fields=["order_id"],
        )
        assert consumer.strategy == IdempotencyStrategy.DEDUP_BY_BUSINESS_KEY
        assert consumer.business_key_fields == ["order_id"]


# ============================================================================
# Retry Policy Recipe Tests
# ============================================================================


class TestRetryPolicyRecipe:
    def test_defaults(self):
        policy = retry_policy_recipe()
        assert isinstance(policy, RetryPolicy)
        assert policy.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER

    def test_fixed_strategy(self):
        policy = retry_policy_recipe(strategy=RetryStrategy.FIXED, max_attempts=10)
        assert policy.strategy == RetryStrategy.FIXED
        assert policy.max_attempts == 10


# ============================================================================
# DLQ Management Recipe Tests
# ============================================================================


class TestDLQManagementRecipe:
    def test_defaults(self):
        result = dlq_management_recipe()
        assert isinstance(result, dict)
        assert "dlq_config" in result
        assert "dashboard_config" in result
        assert "status" in result

    def test_dlq_config_defaults(self):
        result = dlq_management_recipe()
        dlq = result["dlq_config"]
        assert isinstance(dlq, DLQManagementConfig)
        assert dlq.id == "dlq.central"
        assert dlq.name == "Central DLQ"
        assert dlq.source_topic == "events.failed"
        assert dlq.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert dlq.max_retries == 3
        assert dlq.auto_purge is False

    def test_dashboard_config_defaults(self):
        result = dlq_management_recipe()
        dash = result["dashboard_config"]
        assert isinstance(dash, DLQDashboardConfig)
        assert dash.id == "dlq.dashboard"
        assert dash.name == "DLQ Management Dashboard"
        assert dash.enabled is True
        assert dash.auto_retry is False
        assert dash.notification_on_new_message is True

    def test_status_is_active(self):
        result = dlq_management_recipe()
        assert result["status"] == DLQStatus.ACTIVE.value

    def test_custom_params(self):
        result = dlq_management_recipe(
            dlq_id="custom.dlq",
            dlq_name="Custom DLQ",
            source_topic="payments.failed",
            max_retries=5,
            retry_strategy=RetryStrategy.ADAPTIVE,
            auto_purge=True,
            alert_on_threshold=50,
            dashboard_id="custom.dash",
            dashboard_name="Custom Dashboard",
            auto_retry=True,
            retry_batch_size=25,
            slack_webhook="https://hooks.slack.com/test",
            email_recipients=["ops@test.com"],
        )
        dlq = result["dlq_config"]
        assert dlq.id == "custom.dlq"
        assert dlq.retry_strategy == RetryStrategy.ADAPTIVE
        assert dlq.auto_purge is True
        dash = result["dashboard_config"]
        assert dash.id == "custom.dash"
        assert dash.auto_retry is True
        assert dash.retry_batch_size == 25
        assert dash.slack_webhook == "https://hooks.slack.com/test"
        assert dash.email_recipients == ["ops@test.com"]
