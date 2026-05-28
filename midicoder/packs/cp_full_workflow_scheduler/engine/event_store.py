"""
Mô-đun Event Store cho Event Sourcing.

Cung cấp:
- EventStore: Lưu trữ và truy xuất workflow events
- WorkflowEvent: Event dataclass

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class WorkflowEvent:
    """
    Event trong event sourcing.
    
    Attributes:
        event_id: Event ID
        event_type: Loại event (instance_created, transition, error)
        instance_id: Workflow instance ID
        workflow_name: Tên workflow
        data: Event data (JSON-serializable)
        timestamp: Thời gian event xảy ra
        tenant_id: Tenant ID (optional)
    """
    event_type: str
    instance_id: UUID
    workflow_name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tenant_id: UUID | None = None


class EventStore:
    """
    Event Store cho workflow event sourcing.
    
    Lưu trữ events và cung cấp API để:
    - Append new events
    - Query events by instance
    - Rebuild state from events
    
    Usage:
        store = EventStore()
        store.append(event)
        events = store.get_by_instance(instance_id)
    """

    def __init__(self):
        """Khởi tạo EventStore với in-memory storage."""
        self._events: list[WorkflowEvent] = []
        self._index: dict[UUID, list[int]] = {}

    def append(self, event: WorkflowEvent) -> None:
        """
        Append event mới vào store.
        
        Args:
            event: Event để lưu
        """
        index = len(self._events)
        self._events.append(event)
        
        # Update index
        if event.instance_id not in self._index:
            self._index[event.instance_id] = []
        self._index[event.instance_id].append(index)

    def get_by_instance(self, instance_id: UUID) -> list[WorkflowEvent]:
        """
        Lấy tất cả events cho một instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Danh sách events theo thứ tự thời gian
        """
        indices = self._index.get(instance_id, [])
        return [self._events[i] for i in sorted(indices)]

    def get_by_workflow(self, workflow_name: str) -> list[WorkflowEvent]:
        """
        Lấy tất cả events cho một workflow.
        
        Args:
            workflow_name: Tên workflow
            
        Returns:
            Danh sách events
        """
        return [e for e in self._events if e.workflow_name == workflow_name]

    def get_by_type(self, event_type: str) -> list[WorkflowEvent]:
        """
        Lấy tất cả events theo loại.
        
        Args:
            event_type: Loại event
            
        Returns:
            Danh sách events
        """
        return [e for e in self._events if e.event_type == event_type]

    def get_count(self) -> int:
        """
        Lấy tổng số events.
        
        Returns:
            Số lượng events
        """
        return len(self._events)

    def clear(self) -> None:
        """Xóa tất cả events."""
        self._events.clear()
        self._index.clear()