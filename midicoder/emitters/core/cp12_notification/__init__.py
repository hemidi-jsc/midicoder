"""
CP12: Notification & Communication Emitter.

Module này cung cấp các class để generate notification code:
- Models: NotificationChannel, NotificationTemplate, NotificationDispatch, NotificationProvider, DispatchResult
- Parser: Parse notification definitions từ YAML
- Template Engine: TemplateRenderer, TemplateValidator, RenderedTemplate
- I18n: I18nTemplateRegistry cho multi-language templates
- Rate Limiter: RateLimiter cho rate limiting per recipient
- Retry Policy: RetryPolicy với exponential backoff
- Providers: EmailGateway, SmsGateway, PushGateway (ABC) + SmtpEmailGateway
- FastAPI Emitter: Generate notification service, router, models, tasks
- NestJS Emitter: Generate NotificationModule, Service, Controller, DTOs

CP12 depends on CP01 (Domain Model) và CP05 (Event-Driven Architecture).
"""

from midicoder.emitters.core.cp12_notification.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationDispatch,
    NotificationProvider,
    DispatchResult,
)
from midicoder.emitters.core.cp12_notification.parser import (
    parse_notifications,
    parse_channels,
    parse_providers,
)
from midicoder.emitters.core.cp12_notification.template_engine import (
    TemplateRenderer,
    TemplateValidator,
    RenderedTemplate,
)
from midicoder.emitters.core.cp12_notification.i18n import I18nTemplateRegistry
from midicoder.emitters.core.cp12_notification.rate_limiter import RateLimiter
from midicoder.emitters.core.cp12_notification.retry_policy import RetryPolicy
from midicoder.emitters.core.cp12_notification.fastapi import FastAPINotificationEmitter
from midicoder.emitters.core.cp12_notification.nestjs import NestJSNotificationEmitter
from midicoder.emitters.core.cp12_notification.providers import (
    EmailGateway,
    SmsGateway,
    PushGateway,
    SmtpEmailGateway,
    SendGridEmailGateway,
    AwsSesEmailGateway,
    FirebasePushGateway,
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
    # Template Engine
    "TemplateRenderer",
    "TemplateValidator",
    "RenderedTemplate",
    # I18n
    "I18nTemplateRegistry",
    # Rate Limiter
    "RateLimiter",
    # Retry Policy
    "RetryPolicy",
    # Providers
    "EmailGateway",
    "SmsGateway",
    "PushGateway",
    "SmtpEmailGateway",
    "SendGridEmailGateway",
    "AwsSesEmailGateway",
    "FirebasePushGateway",
    # Emitters
    "FastAPINotificationEmitter",
    "NestJSNotificationEmitter",
]
