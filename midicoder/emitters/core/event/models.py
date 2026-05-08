"""
Event Models Module.

Module này định nghĩa các models cho Event DSL:
- EventDefinition: Định nghĩa event với event_name, payload_fields, topic, version, tenant_id

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
# Exports
# ============================================================================

__all__ = [
    "EventDefinition",
    "OutboxEntry",
]