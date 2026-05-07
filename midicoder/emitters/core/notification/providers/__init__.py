"""
Notification Providers Package.

Package này chứa các concrete provider gateways:
- SendGridEmailGateway: SendGrid email provider
- AwsSesEmailGateway: AWS SES email provider
- TwilioSmsGateway: Twilio SMS provider
- FirebasePushGateway: Firebase FCM push provider

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.notification.providers.base import (
    EmailGateway,
    PushGateway,
    SmsGateway,
)
from midicoder.emitters.core.notification.providers.sendgrid import (
    SendGridEmailGateway,
)
from midicoder.emitters.core.notification.providers.ses import AwsSesEmailGateway
from midicoder.emitters.core.notification.providers.twilio import TwilioSmsGateway
from midicoder.emitters.core.notification.providers.firebase import (
    FirebasePushGateway,
)

__all__ = [
    "EmailGateway",
    "SmsGateway",
    "PushGateway",
    "SendGridEmailGateway",
    "AwsSesEmailGateway",
    "TwilioSmsGateway",
    "FirebasePushGateway",
]