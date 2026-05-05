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
# Exports
# ============================================================================

__all__ = [
    "EventDefinition",
]