"""
CP12: Notification & Communication Emitter.

Module này cung cấp các class để generate notification code:
- Models: NotificationChannel, NotificationTemplate, NotificationDispatch,
           NotificationProvider, DispatchResult, WebhookConfig, WebhookDelivery,
           ChatIntegrationConfig, ChatPlatform, DeliveryStatus, DeliveryAttempt,
           DeliveryTracking, ABTestVariant, ABTestConfig
- Parser: Parse notification definitions từ YAML
- Template Engine: TemplateRenderer, TemplateValidator, RenderedTemplate
- I18n: I18nTemplateRegistry cho multi-language templates
- Rate Limiter: RateLimiter cho rate limiting per recipient
- Retry Policy: RetryPolicy với exponential backoff
- Providers: EmailGateway, SmsGateway, PushGateway, WebhookGateway (ABC)
             + SmtpEmailGateway, SendGridEmailGateway, AwsSesEmailGateway,
               TwilioSmsGateway, FirebasePushGateway, WebhookGatewayImpl
- Recipes: Pattern recipes (SMTPEmailRecipe, SESEmailRecipe, SendGridEmailRecipe,
           TwilioSMSRecipe, FCMRecipe, WebhookRecipe, DeliveryTrackingRecipe)

CP12 depends on CP01 (Domain Model) và CP05 (Event-Driven Architecture).
"""

from midicoder.emitters.core.cp12_notification.models import (
    NotificationChannel,
    NotificationTemplate,
    NotificationDispatch,
    NotificationProvider,
    DispatchResult,
    WebhookConfig,
    WebhookDelivery,
    WebhookAuthType,
    ChatIntegrationConfig,
    ChatPlatform,
    DeliveryStatus,
    DeliveryAttempt,
    DeliveryTracking,
    ABTestVariant,
    ABTestConfig,
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
from midicoder.emitters.core.cp12_notification.providers import (
    EmailGateway,
    SmsGateway,
    PushGateway,
    WebhookGateway,
    SmtpEmailGateway,
    SendGridEmailGateway,
    AwsSesEmailGateway,
    TwilioSmsGateway,
    FirebasePushGateway,
    WebhookGatewayImpl,
)
from midicoder.emitters.core.cp12_notification.recipes import (
    SMTPEmailRecipe,
    SESEmailRecipe,
    SendGridEmailRecipe,
    TwilioSMSRecipe,
    FCMRecipe,
    WebhookRecipe,
    DeliveryTrackingRecipe,
)

__all__ = [
    # Models
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationDispatch",
    "NotificationProvider",
    "DispatchResult",
    "WebhookConfig",
    "WebhookDelivery",
    "WebhookAuthType",
    "ChatIntegrationConfig",
    "ChatPlatform",
    "DeliveryStatus",
    "DeliveryAttempt",
    "DeliveryTracking",
    "ABTestVariant",
    "ABTestConfig",
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
    "WebhookGateway",
    "SmtpEmailGateway",
    "SendGridEmailGateway",
    "AwsSesEmailGateway",
    "TwilioSmsGateway",
    "FirebasePushGateway",
    "WebhookGatewayImpl",
    # Recipes
    "SMTPEmailRecipe",
    "SESEmailRecipe",
    "SendGridEmailRecipe",
    "TwilioSMSRecipe",
    "FCMRecipe",
    "WebhookRecipe",
    "DeliveryTrackingRecipe",
]
