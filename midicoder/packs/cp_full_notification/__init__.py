"""
CP12: Notification & Communication Emitter (merged with CP62 Mobile Backend).

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

=== Mobile Backend (CP62) ===
- Models: PushPlatform, DeepLinkAuth, MobileAuthType, OTAPlatform, DevicePlatform
           PushNotificationConfig, DeepLinkRoute, MobileAuthProvider,
           OTAUpdateConfig, DeviceRegistration
- Parser: MobileIR, parse_push_configs, parse_deep_links, parse_auth_providers,
           parse_ota_configs, parse_mobile_to_ir
- Recipes: RecipeOutput, fcm_push_notification_recipe, apns_push_notification_recipe,
           deep_linking_recipe, mobile_auth_recipe, ota_update_recipe,
           full_mobile_backend_recipe

CP12+CP62 depends on CP01 (Domain Model) và CP05 (Event-Driven Architecture).
"""

from midicoder.packs.cp_full_notification.models import (
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
    # Mobile Backend (CP62)
    PushPlatform,
    DeepLinkAuth,
    MobileAuthType,
    OTAPlatform,
    DevicePlatform,
    PushNotificationConfig,
    DeepLinkRoute,
    MobileAuthProvider,
    OTAUpdateConfig,
    DeviceRegistration,
)
from midicoder.packs.cp_full_notification.parser import (
    parse_notifications,
    parse_channels,
    parse_providers,
    # Mobile Backend (CP62)
    MobileIR,
    parse_push_configs,
    parse_deep_links,
    parse_auth_providers,
    parse_ota_configs,
    parse_mobile_to_ir,
)
from midicoder.packs.cp_full_notification.template_engine import (
    TemplateRenderer,
    TemplateValidator,
    RenderedTemplate,
)
from midicoder.packs.cp_full_notification.i18n import I18nTemplateRegistry
from midicoder.packs.cp_full_notification.rate_limiter import RateLimiter
from midicoder.packs.cp_full_notification.retry_policy import RetryPolicy
from midicoder.packs.cp_full_notification.providers import (
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
from midicoder.packs.cp_full_notification.recipes import (
    SMTPEmailRecipe,
    SESEmailRecipe,
    SendGridEmailRecipe,
    TwilioSMSRecipe,
    FCMRecipe,
    WebhookRecipe,
    DeliveryTrackingRecipe,
    ABTestRecipe,
    # Mobile Backend (CP62)
    RecipeOutput,
    fcm_push_notification_recipe,
    apns_push_notification_recipe,
    deep_linking_recipe,
    mobile_auth_recipe,
    ota_update_recipe,
    full_mobile_backend_recipe,
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
    # Mobile Backend Models (CP62)
    "PushPlatform",
    "DeepLinkAuth",
    "MobileAuthType",
    "OTAPlatform",
    "DevicePlatform",
    "PushNotificationConfig",
    "DeepLinkRoute",
    "MobileAuthProvider",
    "OTAUpdateConfig",
    "DeviceRegistration",
    # Parser
    "parse_notifications",
    "parse_channels",
    "parse_providers",
    # Mobile Backend Parser (CP62)
    "MobileIR",
    "parse_push_configs",
    "parse_deep_links",
    "parse_auth_providers",
    "parse_ota_configs",
    "parse_mobile_to_ir",
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
    "ABTestRecipe",
    # Mobile Backend Recipes (CP62)
    "RecipeOutput",
    "fcm_push_notification_recipe",
    "apns_push_notification_recipe",
    "deep_linking_recipe",
    "mobile_auth_recipe",
    "ota_update_recipe",
    "full_mobile_backend_recipe",
]
