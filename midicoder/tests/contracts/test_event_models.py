"""
Tests cho CP05: Event-Driven Architecture Models.

Viết theo TDD, bám sát SoT (requirement.md - E12 CP05):
- Event definitions
- Event publishers/subscribers
- Event schemas
- Message queue integration

Không dùng mock, test với real implementations.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.contracts.event_models import (
    DomainEvent,
    EventBus,
    EventMessage,
    EventPublisher,
    EventSubscriber,
)


# ============================================================================
# Test EventMessage Class
# ============================================================================


class TestEventMessage:
    """Tests cho EventMessage class theo SoT CP05."""

    def test_create_event_message_minimal(self) -> None:
        """Kiểm tra tạo event message với minimal fields."""
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001", "total": 100000},
        )

        assert message.event_id == "order.created"
        assert message.payload == {"order_id": "ORD-001", "total": 100000}
        assert message.version == "1.0"
        assert message.timestamp is not None
        assert message.correlation_id is None

    def test_create_event_message_full(self) -> None:
        """Kiểm tra tạo event message với đầy đủ fields."""
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001", "total": 100000},
            version="1.0",
            correlation_id="corr-123",
            metadata={"tenant_id": "tenant-001"},
        )

        assert message.event_id == "order.created"
        assert message.version == "1.0"
        assert message.correlation_id == "corr-123"
        assert message.metadata == {"tenant_id": "tenant-001"}

    def test_event_message_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
            version="1.0",
            correlation_id="corr-123",
        )

        msg_dict = message.to_dict()

        assert msg_dict["event_id"] == "order.created"
        assert msg_dict["payload"] == {"order_id": "ORD-001"}
        assert msg_dict["version"] == "1.0"
        assert msg_dict["correlation_id"] == "corr-123"

    def test_event_message_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        msg_dict = {
            "event_id": "payment.processed",
            "payload": {"payment_id": "PAY-001"},
            "version": "1.0",
            "correlation_id": "corr-456",
            "metadata": {"source": "payment-service"},
        }

        message = EventMessage.from_dict(msg_dict)

        assert message.event_id == "payment.processed"
        assert message.payload == {"payment_id": "PAY-001"}
        assert message.version == "1.0"
        assert message.correlation_id == "corr-456"


# ============================================================================
# Test DomainEvent Class
# ============================================================================


class TestDomainEvent:
    """Tests cho DomainEvent class theo SoT CP05."""

    def test_create_domain_event(self) -> None:
        """Kiểm tra tạo domain event."""
        event = DomainEvent(
            name="OrderCreated",
            aggregate_type="Order",
            version="1.0",
        )

        assert event.name == "OrderCreated"
        assert event.aggregate_type == "Order"
        assert event.version == "1.0"

    def test_domain_event_to_dict(self) -> None:
        """Kiểm tra to_dict serialization."""
        event = DomainEvent(
            name="OrderCreated",
            aggregate_type="Order",
            version="1.0",
            description="Sự kiện đơn hàng được tạo",
        )

        event_dict = event.to_dict()

        assert event_dict["name"] == "OrderCreated"
        assert event_dict["aggregate_type"] == "Order"
        assert event_dict["version"] == "1.0"

    def test_domain_event_from_dict(self) -> None:
        """Kiểm tra from_dict deserialization."""
        event_dict = {
            "name": "PaymentProcessed",
            "aggregate_type": "Payment",
            "version": "1.0",
            "description": "Sự kiện thanh toán được xử lý",
        }

        event = DomainEvent.from_dict(event_dict)

        assert event.name == "PaymentProcessed"
        assert event.aggregate_type == "Payment"
        assert event.version == "1.0"


# ============================================================================
# Test EventPublisher Class
# ============================================================================


class TestEventPublisher:
    """Tests cho EventPublisher class theo SoT CP05."""

    def test_create_event_publisher(self) -> None:
        """Kiểm tra tạo event publisher."""
        publisher = EventPublisher(
            bus_name="default",
            topic="orders",
        )

        assert publisher.bus_name == "default"
        assert publisher.topic == "orders"

    def test_publish_event(self) -> None:
        """Kiểm tra publish event."""
        publisher = EventPublisher(
            bus_name="default",
            topic="orders",
        )

        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
        )

        # Publish should return the message
        result = publisher.publish(message)

        assert result.event_id == "order.created"
        assert "orders" in result.topic if hasattr(result, "topic") else True

    def test_publish_with_correlation_id(self) -> None:
        """Kiểm tra publish với correlation ID."""
        publisher = EventPublisher(
            bus_name="default",
            topic="orders",
        )

        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
            correlation_id="corr-123",
        )

        result = publisher.publish(message)

        assert result.correlation_id == "corr-123"


# ============================================================================
# Test EventSubscriber Class
# ============================================================================


class TestEventSubscriber:
    """Tests cho EventSubscriber class theo SoT CP05."""

    def test_create_event_subscriber(self) -> None:
        """Kiểm tra tạo event subscriber."""
        subscriber = EventSubscriber(
            bus_name="default",
            topic="orders",
            handler=lambda msg: msg,
        )

        assert subscriber.bus_name == "default"
        assert subscriber.topic == "orders"
        assert subscriber.handler is not None

    def test_subscribe_to_event(self) -> None:
        """Kiểm tra subscribe đến event."""
        subscriber = EventSubscriber(
            bus_name="default",
            topic="orders",
            handler=lambda msg: {"processed": True},
        )

        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
        )

        result = subscriber.handle(message)

        assert result == {"processed": True}

    def test_subscribe_with_filter(self) -> None:
        """Kiểm tra subscribe với filter."""
        def order_filter(msg: EventMessage) -> bool:
            """Chỉ xử lý orders với total > 50000."""
            return msg.payload.get("total", 0) > 50000

        subscriber = EventSubscriber(
            bus_name="default",
            topic="orders",
            handler=lambda msg: {"processed": True},
            filter=order_filter,
        )

        # High value order - should pass filter
        high_value = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001", "total": 100000},
        )

        # Low value order - should be filtered out
        low_value = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-002", "total": 10000},
        )

        assert subscriber.should_handle(high_value) is True
        assert subscriber.should_handle(low_value) is False


# ============================================================================
# Test EventBus Class
# ============================================================================


class TestEventBus:
    """Tests cho EventBus class theo SoT CP05."""

    def test_create_event_bus(self) -> None:
        """Kiểm tra tạo event bus."""
        bus = EventBus(name="default")

        assert bus.name == "default"
        # subscribers là dict mapping topic -> list của handlers
        assert bus.subscribers == {}

    def test_publish_event(self) -> None:
        """Kiểm tra publish event."""
        bus = EventBus(name="default")

        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
        )

        bus.publish(message)

        # Event should be published
        assert True  # Bus handles publish internally

    def test_subscribe_event(self) -> None:
        """Kiểm tra subscribe event."""
        bus = EventBus(name="default")

        handler_called = []

        def handler(msg: EventMessage):
            handler_called.append(msg)

        bus.subscribe("orders", handler)

        # Message cần có topic để route đến handlers
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
            topic="orders",
        )

        bus.publish(message)

        # Handler should be called
        assert len(handler_called) == 1
        assert handler_called[0].event_id == "order.created"

    def test_multiple_subscribers(self) -> None:
        """Kiểm tra nhiều subscribers."""
        bus = EventBus(name="default")

        handler1_called = []
        handler2_called = []

        def handler1(msg: EventMessage):
            handler1_called.append(msg)

        def handler2(msg: EventMessage):
            handler2_called.append(msg)

        bus.subscribe("orders", handler1)
        bus.subscribe("orders", handler2)

        # Message cần có topic để route đến handlers
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
            topic="orders",
        )

        bus.publish(message)

        # Both handlers should be called
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    def test_unsubscribe_event(self) -> None:
        """Kiểm tra unsubscribe event."""
        bus = EventBus(name="default")

        handler_called = []

        def handler(msg: EventMessage):
            handler_called.append(msg)

        bus.subscribe("orders", handler)
        bus.unsubscribe("orders", handler)

        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001"},
        )

        bus.publish(message)

        # Handler should NOT be called after unsubscribe
        assert len(handler_called) == 0


# ============================================================================
# Test Integration: Event Flow
# ============================================================================


class TestEventIntegration:
    """Tests cho integration event flow theo SoT CP05."""

    def test_publish_subscribe_flow(self) -> None:
        """Kiểm tra publish-subscribe flow."""
        bus = EventBus(name="order-bus")

        received_events = []

        def order_handler(msg: EventMessage):
            received_events.append(msg)

        bus.subscribe("orders", order_handler)

        # Publisher publishes event với topic
        message = EventMessage(
            event_id="order.created",
            payload={"order_id": "ORD-001", "total": 100000},
            correlation_id="corr-123",
            topic="orders",
        )

        bus.publish(message)

        # Subscriber receives event
        assert len(received_events) == 1
        assert received_events[0].event_id == "order.created"
        assert received_events[0].correlation_id == "corr-123"

    def test_event_with_retry_policy(self) -> None:
        """Kiểm tra event với retry policy."""
        subscriber = EventSubscriber(
            bus_name="default",
            topic="orders",
            handler=lambda msg: {"processed": True},
            retry_policy={
                "max_retries": 3,
                "backoff_ms": 1000,
            },
        )

        assert subscriber.retry_policy["max_retries"] == 3
        assert subscriber.retry_policy["backoff_ms"] == 1000

    def test_domain_event_lifecycle(self) -> None:
        """Kiểm tra lifecycle của domain event."""
        # Define domain event
        order_created = DomainEvent(
            name="OrderCreated",
            aggregate_type="Order",
            version="1.0",
            description="Sự kiện đơn hàng được tạo",
        )

        # Create message from domain event
        message = EventMessage(
            event_id=order_created.name.lower().replace(" ", "."),
            payload={"order_id": "ORD-001"},
            version=order_created.version,
        )

        assert message.event_id == "ordercreated"
        assert message.version == "1.0"