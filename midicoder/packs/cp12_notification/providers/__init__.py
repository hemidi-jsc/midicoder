"""Provider exports."""

from midicoder.packs.cp12_notification.providers.base import (
    EmailGateway,
    SmsGateway,
    PushGateway,
    WebhookGateway,
)
from midicoder.packs.cp12_notification.providers.smtp import SmtpEmailGateway
from midicoder.packs.cp12_notification.providers.sendgrid import (
    SendGridEmailGateway,
)
from midicoder.packs.cp12_notification.providers.ses import AwsSesEmailGateway
from midicoder.packs.cp12_notification.providers.twilio import TwilioSmsGateway
from midicoder.packs.cp12_notification.providers.firebase import FirebasePushGateway
from midicoder.packs.cp12_notification.providers.webhook import (
    WebhookGatewayImpl,
    verify_webhook_signature,
)

__all__ = [
    # ABC
    "EmailGateway",
    "SmsGateway",
    "PushGateway",
    "WebhookGateway",
    # Email
    "SmtpEmailGateway",
    "SendGridEmailGateway",
    "AwsSesEmailGateway",
    # SMS
    "TwilioSmsGateway",
    # Push
    "FirebasePushGateway",
    # Webhook
    "WebhookGatewayImpl",
    "verify_webhook_signature",
]
