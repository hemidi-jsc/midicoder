"""
Event Parser Module.

Module này cung cấp EventParser class để parse YAML/dict data thành EventDefinition objects.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from .models import EventDefinition


# ============================================================================
# Event Parser
# ============================================================================


class EventParser:
    """
    Parser cho Event definitions.

    Convert YAML dict data thành EventDefinition objects.

    Usage:
        parser = EventParser()
        events = parser.parse([
            {"event_name": "order.created", "payload_fields": ["order_id"]},
            {"event_name": "order.cancelled", "payload_fields": ["order_id", "reason"]},
        ])
    """

    def parse(self, data: list[dict[str, Any]]) -> list[EventDefinition]:
        """
        Parse list of YAML dicts thành EventDefinition objects.

        Args:
            data: List of dictionaries chứa event data

        Returns:
            List of EventDefinition instances

        Raises:
            ValueError: Nếu event_name missing hoặc empty
        """
        events: list[EventDefinition] = []

        for item in data:
            event_name = item.get("event_name", "")
            if not event_name or not str(event_name).strip():
                raise ValueError(
                    "event_name bắt buộc và không được để trống"
                )

            event = EventDefinition(
                event_name=str(event_name),
                payload_fields=item.get("payload_fields", []),
                topic=item.get("topic", "default"),
                version=item.get("version", "1.0"),
                tenant_id=item.get("tenant_id"),
                schema_fields=item.get("schema_fields"),
            )
            events.append(event)

        return events


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "EventParser",
]