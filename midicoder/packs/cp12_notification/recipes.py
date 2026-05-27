"""
Mô-đun Notification Recipes.

Recipes là pattern macro — cách gán giá trị cụ thể vào pattern vocabulary.
Mỗi recipe trả về dataclass instance đã config sẵn cho use case phổ biến.

Recipe call direct tới pattern, không nested recipe, không domain-specific.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp12_notification.models import (
    NotificationChannel,
    NotificationProvider,
    NotificationTemplate,
    WebhookConfig,
    WebhookAuthType,
    DeliveryTracking,
    DeliveryStatus,
    ABTestConfig,
    ABTestVariant,
)


# ============================================================================
# Email Recipes
# ============================================================================


@dataclass
class SMTPEmailRecipe:
    """
    Recipe: Email qua SMTP native.

    Config sẵn SMTP provider với TLS, authentication.

    Usage:
        recipe = SMTPEmailRecipe(host="smtp.gmail.com", port=587)
        provider = recipe.build_provider()
    """
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_email: str = "noreply@example.com"
    provider_id: str = "smtp_default"

    def build_provider(self) -> NotificationProvider:
        """Trả về NotificationProvider config sẵn cho SMTP."""
        return NotificationProvider(
            provider_id=self.provider_id,
            channel=NotificationChannel.EMAIL,
            config={
                "type": "smtp",
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password,
                "use_tls": self.use_tls,
                "from_email": self.from_email,
            },
            enabled=True,
            priority=1,
        )


@dataclass
class SendGridEmailRecipe:
    """
    Recipe: Email qua SendGrid.

    Usage:
        recipe = SendGridEmailRecipe(api_key="SG.xxx")
        provider = recipe.build_provider()
    """
    api_key: str = ""
    from_email: str = "noreply@example.com"
    from_name: str = "Midicoder"
    provider_id: str = "sendgrid_default"

    def build_provider(self) -> NotificationProvider:
        """Trả về NotificationProvider config sẵn cho SendGrid."""
        return NotificationProvider(
            provider_id=self.provider_id,
            channel=NotificationChannel.EMAIL,
            config={
                "type": "sendgrid",
                "api_key": self.api_key,
                "from_email": self.from_email,
                "from_name": self.from_name,
            },
            enabled=bool(self.api_key),
            priority=1,
        )


@dataclass
class SESEmailRecipe:
    """
    Recipe: Email qua AWS SES.

    Usage:
        recipe = SESEmailRecipe(
            aws_access_key="AKIAXXX",
            aws_secret_key="xxx",
            region="us-east-1",
        )
    """
    aws_access_key: str = ""
    aws_secret_key: str = ""
    region: str = "us-east-1"
    from_email: str = "noreply@example.com"
    provider_id: str = "ses_default"

    def build_provider(self) -> NotificationProvider:
        """Trả về NotificationProvider config sẵn cho AWS SES."""
        return NotificationProvider(
            provider_id=self.provider_id,
            channel=NotificationChannel.EMAIL,
            config={
                "type": "aws_ses",
                "aws_access_key": self.aws_access_key,
                "aws_secret_key": self.aws_secret_key,
                "region": self.region,
                "from_email": self.from_email,
            },
            enabled=bool(self.aws_access_key and self.aws_secret_key),
            priority=1,
        )


# ============================================================================
# SMS Recipes
# ============================================================================


@dataclass
class TwilioSMSRecipe:
    """
    Recipe: SMS qua Twilio.

    Usage:
        recipe = TwilioSMSRecipe(
            account_sid="AC.xxx",
            auth_token="xxx",
            from_phone="+1234567890",
        )
    """
    account_sid: str = ""
    auth_token: str = ""
    from_phone: str = ""
    status_callback: str = ""
    provider_id: str = "twilio_default"

    def build_provider(self) -> NotificationProvider:
        """Trả về NotificationProvider config sẵn cho Twilio SMS."""
        return NotificationProvider(
            provider_id=self.provider_id,
            channel=NotificationChannel.SMS,
            config={
                "type": "twilio",
                "account_sid": self.account_sid,
                "auth_token": self.auth_token,
                "from_phone": self.from_phone,
                "status_callback": self.status_callback,
            },
            enabled=bool(self.account_sid and self.auth_token and self.from_phone),
            priority=1,
        )

    def build_welcome_template(self) -> NotificationTemplate:
        """Trả về welcome SMS template."""
        return NotificationTemplate(
            template_id="sms_welcome",
            channel=NotificationChannel.SMS,
            body_text="Xin chào {{name}}! Cảm ơn bạn đã đăng ký. Mã xác nhận: {{code}}",
            variables=["name", "code"],
        )

    def build_verification_template(self) -> NotificationTemplate:
        """Trả về verification SMS template."""
        return NotificationTemplate(
            template_id="sms_verification",
            channel=NotificationChannel.SMS,
            body_text="Mã xác nhận của bạn là: {{code}}. Không chia sẻ mã này cho bất kỳ ai.",
            variables=["code"],
        )

    def build_password_reset_template(self) -> NotificationTemplate:
        """Trả về password reset SMS template."""
        return NotificationTemplate(
            template_id="sms_password_reset",
            channel=NotificationChannel.SMS,
            body_text="Mã đặt lại mật khẩu: {{code}}. Hết hạn sau {{expiry}} phút.",
            variables=["code", "expiry"],
        )


# ============================================================================
# Push Recipes
# ============================================================================


@dataclass
class FCMRecipe:
    """
    Recipe: Push notification qua Firebase FCM.

    Usage:
        recipe = FCMRecipe(
            project_id="my-project",
            access_token="ya29.xxx",
        )
    """
    project_id: str = ""
    access_token: str = ""
    credentials_path: str = ""
    provider_id: str = "firebase_fcm"

    def build_provider(self) -> NotificationProvider:
        """Trả về NotificationProvider config sẵn cho FCM."""
        return NotificationProvider(
            provider_id=self.provider_id,
            channel=NotificationChannel.PUSH,
            config={
                "type": "firebase_fcm",
                "project_id": self.project_id,
                "access_token": self.access_token,
                "credentials_path": self.credentials_path,
            },
            enabled=bool(self.project_id and (self.access_token or self.credentials_path)),
            priority=1,
        )

    def build_order_update_template(self) -> NotificationTemplate:
        """Trả về order update push template."""
        return NotificationTemplate(
            template_id="push_order_update",
            channel=NotificationChannel.PUSH,
            subject="Đơn hàng {{order_id}} đã cập nhật",
            body_text="Đơn hàng {{order_id}} của bạn đã ở trạng thái: {{status}}",
            variables=["order_id", "status"],
        )


# ============================================================================
# Webhook Recipe
# ============================================================================


@dataclass
class WebhookRecipe:
    """
    Recipe: Webhook notification.

    Usage:
        recipe = WebhookRecipe(url="https://example.com/webhook")
        config = recipe.build_config()
    """
    url: str
    method: str = "POST"
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    auth_header: str = ""
    auth_secret: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: int = 10
    description: str = ""

    def build_config(self) -> WebhookConfig:
        """Trả về WebhookConfig đã config sẵn."""
        return WebhookConfig(
            url=self.url,
            method=self.method,
            auth_type=self.auth_type,
            auth_header=self.auth_header,
            auth_secret=self.auth_secret,
            headers=self.headers,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            retry_backoff_seconds=self.retry_backoff_seconds,
            description=self.description,
        )

    @classmethod
    def with_bearer(cls, url: str, token: str, **kwargs: Any) -> "WebhookRecipe":
        """Tạo recipe với Bearer auth."""
        return cls(
            url=url,
            auth_type=WebhookAuthType.BEARER,
            auth_header=token,
            **kwargs,
        )

    @classmethod
    def with_hmac(cls, url: str, secret: str, **kwargs: Any) -> "WebhookRecipe":
        """Tạo recipe với HMAC-SHA256 auth."""
        return cls(
            url=url,
            auth_type=WebhookAuthType.HMAC,
            auth_secret=secret,
            **kwargs,
        )

    @classmethod
    def with_basic(cls, url: str, credentials: str, **kwargs: Any) -> "WebhookRecipe":
        """Tạo recipe với Basic auth."""
        return cls(
            url=url,
            auth_type=WebhookAuthType.BASIC,
            auth_header=credentials,
            **kwargs,
        )


# ============================================================================
# Delivery Tracking Recipe
# ============================================================================


@dataclass
class DeliveryTrackingRecipe:
    """
    Recipe: Delivery tracking cho notification.

    Tạo tracking record mặc định cho một dispatch.

    Usage:
        recipe = DeliveryTrackingRecipe(dispatch_id="disp_001")
        tracking = recipe.create("user@example.com", NotificationChannel.EMAIL)
    """
    dispatch_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def create(
        self,
        recipient: str,
        channel: NotificationChannel,
    ) -> DeliveryTracking:
        """Tạo delivery tracking record."""
        return DeliveryTracking(
            dispatch_id=self.dispatch_id,
            recipient=recipient,
            channel=channel,
            metadata=self.metadata,
        )


# ============================================================================
# A/B Testing Recipe
# ============================================================================


@dataclass
class ABTestRecipe:
    """
    Recipe: A/B test cho notification.

    Tạo A/B test config với 2+ variants.

    Usage:
        recipe = ABTestRecipe(
            name="Welcome Email Test",
            channel=NotificationChannel.EMAIL,
        )
        recipe.add_variant("A", "welcome_v1", weight=50.0)
        recipe.add_variant("B", "welcome_v2", weight=50.0)
        config = recipe.build()
    """
    name: str
    channel: NotificationChannel
    metric: str = "open_rate"
    description: str = ""
    _variants: list[ABTestVariant] = field(default_factory=list, repr=False)

    def add_variant(
        self,
        variant_id: str,
        template_id: str,
        weight: float = 50.0,
        name: str = "",
        description: str = "",
    ) -> "ABTestRecipe":
        """Thêm variant vào A/B test (chainable)."""
        self._variants.append(ABTestVariant(
            variant_id=variant_id,
            template_id=template_id,
            weight=weight,
            name=name,
            description=description,
        ))
        return self

    def build(self) -> ABTestConfig:
        """
        Build ABTestConfig từ các variants đã thêm.

        Raises:
            ValueError: Nếu少于 2 variants hoặc total weight != 100
        """
        if len(self._variants) < 2:
            raise ValueError("A/B test cần ít nhất 2 variants")

        total_weight = sum(v.weight for v in self._variants)
        if abs(total_weight - 100.0) > 0.01:
            raise ValueError(
                f"Total weight phải bằng 100, nhận được: {total_weight}"
            )

        return ABTestConfig(
            name=self.name,
            channel=self.channel,
            variants=list(self._variants),
            metric=self.metric,
            description=self.description,
        )

    @classmethod
    def simple_email_test(
        cls,
        name: str,
        variant_a_template: str,
        variant_b_template: str,
    ) -> ABTestConfig:
        """Tạo A/B test đơn giản cho email (50/50)."""
        recipe = cls(name=name, channel=NotificationChannel.EMAIL)
        recipe.add_variant("A", variant_a_template, weight=50.0, name="Variant A")
        recipe.add_variant("B", variant_b_template, weight=50.0, name="Variant B")
        return recipe.build()

    @classmethod
    def three_way_test(
        cls,
        name: str,
        channel: NotificationChannel,
        template_a: str,
        template_b: str,
        template_c: str,
    ) -> ABTestConfig:
        """Tạo A/B/C test (33.33% mỗi variant)."""
        recipe = cls(name=name, channel=channel, metric="click_rate")
        recipe.add_variant("A", template_a, weight=33.33, name="Variant A")
        recipe.add_variant("B", template_b, weight=33.33, name="Variant B")
        recipe.add_variant("C", template_c, weight=33.34, name="Variant C")
        return recipe.build()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SMTPEmailRecipe",
    "SendGridEmailRecipe",
    "SESEmailRecipe",
    "TwilioSMSRecipe",
    "FCMRecipe",
    "WebhookRecipe",
    "DeliveryTrackingRecipe",
    "ABTestRecipe",
]
