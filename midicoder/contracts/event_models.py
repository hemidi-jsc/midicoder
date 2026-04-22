"""
CP05: Event-Driven Architecture Models.

Module này cung cấp các lớp để xử lý event-driven patterns:
- EventMessage: Message đơn lẻ trong event bus
- DomainEvent: Định nghĩa domain events
- EventPublisher: Publish events đến event bus
- EventSubscriber: Subscribe và xử lý events
- EventBus: In-memory event bus cho publish/subscribe pattern

Tuân thủ SoT (requirement.md - E12 CP05):
- Event definitions
- Event publishers/subscribers
- Event schemas
- Message queue integration

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


# ============================================================================
# EventMessage - Basic Event Message
# ============================================================================


@dataclass
class EventMessage:
    """
    Đại diện cho một event message trong hệ thống.

    EventMessage là đơn vị cơ bản được truyền qua event bus.
    Mỗi message có event_id, payload, và metadata.

    Attributes:
        event_id: Định danh duy nhất của event type (ví dụ: "order.created")
        payload: Dữ liệu chính của event
        version: Version của event schema
        timestamp: Thời điểm event được tạo
        correlation_id: ID để trace event qua nhiều services
        metadata: Metadata bổ sung (tenant_id, source, etc.)
    """

    event_id: str
    payload: dict[str, Any]
    version: str = "1.0"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    topic: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển EventMessage thành dict.

        Returns:
            Dict representation của EventMessage
        """
        return {
            "event_id": self.event_id,
            "payload": self.payload,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "topic": self.topic,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventMessage":
        """
        Tạo EventMessage từ dict.

        Args:
            data: Dict chứa dữ liệu EventMessage

        Returns:
            EventMessage instance
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            event_id=data["event_id"],
            payload=data["payload"],
            version=data.get("version", "1.0"),
            timestamp=timestamp or datetime.now(timezone.utc),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata"),
            topic=data.get("topic"),
        )

    def __str__(self) -> str:
        """Trả về string representation của EventMessage."""
        return f"EventMessage(event_id={self.event_id}, version={self.version})"


# ============================================================================
# DomainEvent - Domain Event Definition
# ============================================================================


@dataclass
class DomainEvent:
    """
    Định nghĩa một domain event.

    DomainEvent mô tả cấu trúc của một event trong domain.
    Được sử dụng để register event schemas.

    Attributes:
        name: Tên event (ví dụ: "OrderCreated")
        aggregate_type: Loại aggregate phát ra event (ví dụ: "Order")
        version: Version của event schema
        description: Mô tả event (tiếng Việt)
    """

    name: str
    aggregate_type: str
    version: str = "1.0"
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển DomainEvent thành dict.

        Returns:
            Dict representation của DomainEvent
        """
        return {
            "name": self.name,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        """
        Tạo DomainEvent từ dict.

        Args:
            data: Dict chứa dữ liệu DomainEvent

        Returns:
            DomainEvent instance
        """
        return cls(
            name=data["name"],
            aggregate_type=data["aggregate_type"],
            version=data.get("version", "1.0"),
            description=data.get("description"),
        )

    def __str__(self) -> str:
        """Trả về string representation của DomainEvent."""
        return f"DomainEvent(name={self.name}, aggregate={self.aggregate_type})"


# ============================================================================
# EventPublisher - Publish Events
# ============================================================================


@dataclass
class EventPublisher:
    """
    Publisher để publish events đến event bus.

    EventPublisher cung cấp interface để publish events.
    Có thể tích hợp với Kafka, RabbitMQ, SQS, etc.

    Attributes:
        bus_name: Tên của event bus
        topic: Topic để publish events
    """

    bus_name: str
    topic: str

    def publish(self, message: EventMessage) -> EventMessage:
        """
        Publish event message đến event bus.

        Args:
            message: EventMessage cần publish

        Returns:
            EventMessage đã được publish (có thể có topic được set)
        """
        # Set topic cho message
        message.topic = self.topic

        # Trong implementation thực tế, đây là nơi gửi message đến message queue
        # Ví dụ: kafka_producer.send(self.topic, message.to_dict())
        # Hiện tại chỉ return message để tests có thể verify

        return message

    def publish_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> EventMessage:
        """
        Publish event với event_id và payload.

        Args:
            event_id: ID của event type
            payload: Dữ liệu event
            correlation_id: ID để trace event

        Returns:
            EventMessage đã được publish
        """
        message = EventMessage(
            event_id=event_id,
            payload=payload,
            correlation_id=correlation_id,
            topic=self.topic,
        )
        return self.publish(message)


# ============================================================================
# EventSubscriber - Subscribe và Handle Events
# ============================================================================


@dataclass
class EventSubscriber:
    """
    Subscriber để subscribe và handle events.

    EventSubscriber đăng ký handler để xử lý events.
    Có thể có filter và retry policies.

    Attributes:
        bus_name: Tên của event bus
        topic: Topic để subscribe
        handler: Function để handle events
        filter: Optional filter để filter events
        retry_policy: Retry configuration
    """

    bus_name: str
    topic: str
    handler: Callable[[EventMessage], Any]
    filter: Optional[Callable[[EventMessage], bool]] = None
    retry_policy: Optional[dict[str, Any]] = None

    def should_handle(self, message: EventMessage) -> bool:
        """
        Kiểm tra xem subscriber có nên handle message không.

        Args:
            message: EventMessage cần kiểm tra

        Returns:
            True nếu nên handle, False nếu không
        """
        if self.filter is None:
            return True
        return self.filter(message)

    def handle(self, message: EventMessage) -> Any:
        """
        Handle event message.

        Args:
            message: EventMessage cần handle

        Returns:
            Kết quả từ handler
        """
        if not self.should_handle(message):
            return None

        return self.handler(message)


# ============================================================================
# EventBus - In-Memory Event Bus
# ============================================================================


class EventBus:
    """
    In-memory event bus cho publish/subscribe pattern.

    EventBus quản lý subscribers và route events đến handlers.
    Trong production, có thể tích hợp với Kafka, RabbitMQ, SQS, etc.

    Attributes:
        name: Tên của event bus
        subscribers: Danh sách subscribers theo topic
    """

    def __init__(self, name: str):
        """
        Tạo EventBus mới.

        Args:
            name: Tên của event bus
        """
        self.name = name
        self._subscribers: dict[str, list[Callable[[EventMessage], Any]]] = {}

    @property
    def subscribers(self) -> dict[str, list[Callable]]:
        """
        Lấy danh sách subscribers.

        Returns:
            Dict mapping topic → list of handlers
        """
        return self._subscribers

    def subscribe(
        self,
        topic: str,
        handler: Callable[[EventMessage], Any],
    ) -> None:
        """
        Subscribe handler đến topic.

        Args:
            topic: Topic để subscribe
            handler: Function để handle events
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def unsubscribe(
        self,
        topic: str,
        handler: Callable[[EventMessage], Any],
    ) -> None:
        """
        Unsubscribe handler từ topic.

        Args:
            topic: Topic để unsubscribe
            handler: Handler cần remove
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
            except ValueError:
                pass  # Handler not found, ignore

    def publish(self, message: EventMessage) -> None:
        """
        Publish event message đến tất cả subscribers.

        Args:
            message: EventMessage cần publish
        """
        topic = message.topic or "default"

        if topic not in self._subscribers:
            return

        # Call all handlers cho topic này
        for handler in self._subscribers[topic]:
            try:
                handler(message)
            except Exception:
                # Trong production, cần có error handling và retry logic
                pass

    def publish_to_topic(
        self,
        topic: str,
        event_id: str,
        payload: dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish event đến specific topic.

        Args:
            topic: Topic để publish
            event_id: ID của event type
            payload: Dữ liệu event
            correlation_id: ID để trace event
        """
        message = EventMessage(
            event_id=event_id,
            payload=payload,
            correlation_id=correlation_id,
            topic=topic,
        )
        self.publish(message)