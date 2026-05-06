"""
CP12: Notification & Communication Emitter.

Module này cung cấp các class để generate notification code:
- Models: NotificationChannel, NotificationTemplate, NotificationDispatch, NotificationProvider, DispatchResult
- Parser: Parse notification definitions từ YAML
- Template Engine: TemplateRenderer, TemplateValidator, RenderedTemplate
- I18n: I18nTemplateRegistry cho multi-language templates
- Rate Limiter: RateLimiter cho rate limiting per recipient
- Retry Policy: RetryPolicy với exponential backoff
- Providers: SendGrid, AWS SES, Twilio, Firebase FCM
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
from midicoder.emitters.core.notification.template_engine import (
    TemplateRenderer,
    TemplateValidator,
    RenderedTemplate,
)
from midicoder.emitters.core.notification.i18n import I18nTemplateRegistry
from midicoder.emitters.core.notification.rate_limiter import RateLimiter
from midicoder.emitters.core.notification.retry_policy import RetryPolicy
from midicoder.emitters.core.notification.fastapi import (
    FastAPINotificationEmitter,
)
from midicoder.emitters.core.notification.nestjs import (
    NestJSNotificationEmitter,
)
from midicoder.emitters.core.notification.providers import (
    EmailGateway,
    SmsGateway,
    PushGateway,
    SendGridEmailGateway,
    AwsSesEmailGateway,
    TwilioSmsGateway,
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
    "SendGridEmailGateway",
    "AwsSesEmailGateway",
    "TwilioSmsGateway",
    "FirebasePushGateway",
    # Emitters
    "FastAPINotificationEmitter",
    "NestJSNotificationEmitter",
]