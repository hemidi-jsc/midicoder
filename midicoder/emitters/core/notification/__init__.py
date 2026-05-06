"""
CP12: Notification & Communication Emitter.

Module này cung cấp các class để generate notification code:
- Models: NotificationChannel, NotificationTemplate, NotificationDispatch, NotificationProvider, DispatchResult
- Parser: Parse notification definitions từ YAML
- FastAPI Emitter: Generate notification service, controller, celery tasks
- NestJS Emitter: Generate NotificationModule, Service, Controller

CP12 depends on CP05 (Event-Driven Architecture).
"""

from midicoder.emitters.core.notification.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationDispatch,
    NotificationProvider,
    DispatchResult,
)
from midicoder.emitters.core.notification.parser import (
    parse_notifications,
    parse_channels,
    parse_providers,
)
from midicoder.emitters.core.notification.fastapi import (
    FastAPINotificationEmitter,
)
from midicoder.emitters.core.notification.nestjs import (
    NestJSNotificationEmitter,
)

__all__ = [
    # Models
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationDispatch",
    "NotificationProvider",
    "DispatchResult",
    # Parser
    "parse_notifications",
    "parse_channels",
    "parse_providers",
    # Emitters
    "FastAPINotificationEmitter",
    "NestJSNotificationEmitter",
]