"""
Mô-đun Notification Models.

Module này định nghĩa các data models cho CP12 Notification Emitter:
- NotificationChannel: Enum các kênh notification
- NotificationTemplate: Template cho notification với variable interpolation
- NotificationDispatch: Dispatch request cho notification
- NotificationProvider: Provider config
- DispatchResult: Kết quả sau khi dispatch
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ============================================================================
# NotificationChannel Enum
# ============================================================================


class NotificationChannel(str, Enum):
    """
    Enum các kênh notification được hỗ trợ.

    Values:
        EMAIL: Email notification
        SMS: SMS notification
        PUSH: Push notification (Firebase/APNs)
        WEBHOOK: Webhook HTTP POST notification
        IN_APP: In-application notification
    """

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


# ============================================================================
# NotificationTemplate Model
# ============================================================================


@dataclass
class NotificationTemplate:
    """
    Notification template với variable interpolation support.

    Template định nghĩa cấu trúc của notification bao gồm subject, body_html,
    body_text và các variables có thể interpolate.

    Attributes:
        template_id: Định danh duy nhất của template
        channel: Channel enum (EMAIL, SMS, PUSH, WEBHOOK, IN_APP)
        subject: Subject line (cho EMAIL/PUSH), support {{variable}}
        body_html: HTML body content, support {{variable}}
        body_text: Plain text body content, support {{variable}}
        variables: Danh sách variable names trong template
        locale: Locale code (default: "en")
    """

    template_id: str
    channel: NotificationChannel
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    variables: list[str] = field(default_factory=list)
    locale: str = "en"

    def __post_init__(self) -> None:
        """Kiểm tra template_id không được rỗng."""
        if not self.template_id or not self.template_id.strip():
            raise ValueError("template_id không được để rỗng")

    def render(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Render template với variable values.

        Thay thế các {{variable}} trong subject, body_html, body_text
        bằng values từ data dict. Các variable không có trong data
        sẽ được giữ nguyên (không replace).

        Args:
            data: Dictionary chứa variable values

        Returns:
            Dictionary với keys: subject, body_html, body_text đã render
        """
        result: dict[str, Any] = {
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
        }

        pattern = re.compile(r"\{\{(\w+)\}\}")

        for key in ["subject", "body_html", "body_text"]:
            text = result[key]

            def _replacer(match: re.Match) -> str:
                var_name = match.group(1)
                if var_name in data:
                    return str(data[var_name])
                return match.group(0)

            result[key] = pattern.sub(_replacer, text)

        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển NotificationTemplate sang dictionary.

        Returns:
            Dictionary representation của NotificationTemplate
        """
        return {
            "template_id": self.template_id,
            "channel": self.channel.value,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "variables": self.variables,
            "locale": self.locale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationTemplate":
        """
        Tạo NotificationTemplate từ dictionary.

        Args:
            data: Dictionary chứa template data

        Returns:
            NotificationTemplate instance
        """
        channel_value = data.get("channel", "email")
        channel = NotificationChannel(channel_value)

        return cls(
            template_id=data.get("template_id", ""),
            channel=channel,
            subject=data.get("subject", ""),
            body_html=data.get("body_html", ""),
            body_text=data.get("body_text", ""),
            variables=data.get("variables", []),
            locale=data.get("locale", "en"),
        )


# ============================================================================
# NotificationDispatch Model
# ============================================================================


@dataclass
class NotificationDispatch:
    """
    Dispatch request cho notification.

    Dispatch đại diện cho một yêu cầu gửi notification cụ thể
    đến một recipient qua một channel.

    Attributes:
        dispatch_id: Định danh duy nhất của dispatch
        template_ref: Reference đến template_id
        recipient: Người nhận (email, phone number, user_id)
        channel: Channel để gửi notification
        payload: Variable values cho template rendering
        status: Status hiện tại (pending, sent, failed, bounced)
        scheduled_at: Thời gian scheduled (optional)
        sent_at: Thời gian đã gửi (nullable)
        error_message: Error message nếu failed (nullable)
    """

    dispatch_id: str
    template_ref: str
    recipient: str
    channel: NotificationChannel
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Kiểm tra dispatch_id và recipient không được rỗng."""
        if not self.dispatch_id or not self.dispatch_id.strip():
            raise ValueError("dispatch_id không được để rỗng")
        if not self.recipient or not self.recipient.strip():
            raise ValueError("recipient không được để rỗng")

    def mark_sent(self) -> None:
        """Mark dispatch đã được gửi thành công."""
        self.status = "sent"
        self.sent_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark dispatch thất bại với error message."""
        self.status = "failed"
        self.error_message = error

    def mark_bounced(self, reason: str) -> None:
        """Mark dispatch bounced (email returned)."""
        self.status = "bounced"
        self.error_message = reason

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển NotificationDispatch sang dictionary.

        Returns:
            Dictionary representation của NotificationDispatch
        """
        result: dict[str, Any] = {
            "dispatch_id": self.dispatch_id,
            "template_ref": self.template_ref,
            "recipient": self.recipient,
            "channel": self.channel.value,
            "payload": self.payload,
            "status": self.status,
        }
        if self.scheduled_at:
            result["scheduled_at"] = self.scheduled_at.isoformat()
        if self.sent_at:
            result["sent_at"] = self.sent_at.isoformat()
        if self.error_message:
            result["error_message"] = self.error_message
        return result


# ============================================================================
# NotificationProvider Model
# ============================================================================


@dataclass
class NotificationProvider:
    """
    Provider configuration cho notification channel.

    Provider đại diện cho một service cung cấp notification
    (ví dụ: SendGrid cho email, Twilio cho SMS).

    Attributes:
        provider_id: Định danh duy nhất của provider
        channel: Channel mà provider support
        config: Configuration dictionary cho provider
        enabled: Provider có được enabled không
        priority: Priority order (nhỏ hơn = ưu tiên hơn)
    """

    provider_id: str
    channel: NotificationChannel
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 99

    def __post_init__(self) -> None:
        """Kiểm tra provider_id không được rỗng."""
        if not self.provider_id or not self.provider_id.strip():
            raise ValueError("provider_id không được để rỗng")

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển NotificationProvider sang dictionary.

        Returns:
            Dictionary representation của NotificationProvider
        """
        return {
            "provider_id": self.provider_id,
            "channel": self.channel.value,
            "config": self.config,
            "enabled": self.enabled,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationProvider":
        """
        Tạo NotificationProvider từ dictionary.

        Args:
            data: Dictionary chứa provider data

        Returns:
            NotificationProvider instance
        """
        channel_value = data.get("channel", "email")
        channel = NotificationChannel(channel_value)

        return cls(
            provider_id=data.get("provider_id", ""),
            channel=channel,
            config=data.get("config", {}),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 99),
        )


# ============================================================================
# DispatchResult Model
# ============================================================================


@dataclass
class DispatchResult:
    """
    Kết quả sau khi dispatch notification.

    Result chứa thông tin về kết quả dispatch bao gồm status,
    provider response và error code nếu có.

    Attributes:
        dispatch_id: Dispatch ID liên quan
        status: Status kết quả (sent, failed, bounced)
        provider_response: Response từ provider (optional)
        error_code: Error code nếu failed (optional)
    """

    dispatch_id: str
    status: str
    provider_response: dict[str, Any] | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển DispatchResult sang dictionary.

        Returns:
            Dictionary representation của DispatchResult
        """
        result: dict[str, Any] = {
            "dispatch_id": self.dispatch_id,
            "status": self.status,
        }
        if self.provider_response:
            result["provider_response"] = self.provider_response
        if self.error_code:
            result["error_code"] = self.error_code
        return result


# ============================================================================
# Webhook Channel
# ============================================================================


class WebhookAuthType(str, Enum):
    """Authentication cho webhook delivery."""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC = "hmac"


@dataclass
class WebhookConfig:
    """Configuration cho webhook notification channel.

    Attributes:
        url: Webhook endpoint URL
        method: HTTP method (POST, PUT, PATCH)
        auth_type: Auth type (none, basic, bearer, hmac)
        auth_header: Auth header (Bearer token, Basic credentials)
        headers: Custom headers
        timeout_seconds: HTTP timeout
        max_retries: Số lần retry delivery
        retry_backoff_seconds: Backoff giữa retries
        payload_template: Template cho webhook payload
        description: Mô tả webhook
    """
    url: str
    method: str = "POST"
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    auth_header: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: int = 10
    payload_template: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate webhook config."""
        if not self.url or not self.url.strip():
            EM.raise_error(ErrorCode.CP12_EMPTY_REQUIRED_FIELD, field="url")
        if self.method.upper() not in ("POST", "PUT", "PATCH"):
            EM.raise_error(ErrorCode.CP12_CHANNEL_CONFIG_INVALID, channel="webhook", field="method")
        if self.timeout_seconds < 1:
            self.timeout_seconds = 30

    def to_dict(self) -> dict[str, Any]:
        """Chuyển webhook config sang dict."""
        return {
            "url": self.url,
            "method": self.method,
            "auth_type": self.auth_type.value,
            "auth_header": self.auth_header,
            "headers": self.headers,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "payload_template": self.payload_template,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookConfig":
        """Tạo WebhookConfig từ dict."""
        return cls(
            url=data.get("url", ""),
            method=data.get("method", "POST"),
            auth_type=WebhookAuthType(data.get("auth_type", "none")),
            auth_header=data.get("auth_header", ""),
            headers=data.get("headers", {}),
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            retry_backoff_seconds=data.get("retry_backoff_seconds", 10),
            payload_template=data.get("payload_template", ""),
            description=data.get("description", ""),
        )


@dataclass
class WebhookDelivery:
    """Record cho webhook delivery (giống OutboxEntry nhưng cho webhooks).

    Attributes:
        delivery_id: UUID định danh duy nhất
        webhook_url: URL được deliver
        status: Trạng thái (pending, delivered, failed, retried)
        attempts: Số lần thử delivery
        last_response_code: HTTP response code cuối cùng
        last_response_body: Response body cuối cùng
        scheduled_at: Thời điểm scheduled delivery
        delivered_at: Thời điểm delivered thành công
    """
    webhook_url: str
    status: str = "pending"
    attempts: int = 0
    last_response_code: int = 0
    last_response_body: str = ""
    scheduled_at: str | None = None
    delivered_at: str | None = None
    delivery_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Chuyển webhook delivery sang dict."""
        return {
            "delivery_id": self.delivery_id,
            "webhook_url": self.webhook_url,
            "status": self.status,
            "attempts": self.attempts,
            "last_response_code": self.last_response_code,
            "last_response_body": self.last_response_body,
            "scheduled_at": self.scheduled_at,
            "delivered_at": self.delivered_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookDelivery":
        """Tạo WebhookDelivery từ dict."""
        return cls(
            delivery_id=data.get("delivery_id", ""),
            webhook_url=data.get("webhook_url", ""),
            status=data.get("status", "pending"),
            attempts=data.get("attempts", 0),
            last_response_code=data.get("last_response_code", 0),
            last_response_body=data.get("last_response_body", ""),
            scheduled_at=data.get("scheduled_at"),
            delivered_at=data.get("delivered_at"),
        )


# ============================================================================
# Chat Integration (Slack/Teams/Discord)
# ============================================================================


class ChatPlatform(str, Enum):
    """Platform chat integration."""
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    MSTEAMS = "msteams"
    WEBEX = "webex"


@dataclass
class ChatIntegrationConfig:
    """Configuration cho chat integration (Slack, Teams, Discord, ...).

    Attributes:
        platform: Chat platform (slack, teams, discord, msteams, webex)
        bot_token: Bot token/API key
        webhook_url: Incoming webhook URL
        channel_id: Channel/room ID để send messages
        team_id: Team/organization ID
        username: Bot username
        icon_emoji: Icon emoji cho bot messages
        enable_threading: Có reply trong threads không
        mention_users: Danh sách users mention trong alert messages
        description: Mô tả integration
    """
    platform: ChatPlatform
    bot_token: str = ""
    webhook_url: str = ""
    channel_id: str = ""
    team_id: str = ""
    username: str = "Midicoder Bot"
    icon_emoji: str = "🤖"
    enable_threading: bool = False
    mention_users: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển chat config sang dict."""
        return {
            "platform": self.platform.value,
            "webhook_url": self.webhook_url,
            "channel_id": self.channel_id,
            "team_id": self.team_id,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "enable_threading": self.enable_threading,
            "mention_users": self.mention_users,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatIntegrationConfig":
        """Tạo ChatIntegrationConfig từ dict."""
        return cls(
            platform=ChatPlatform(data.get("platform", "slack")),
            bot_token=data.get("bot_token", ""),
            webhook_url=data.get("webhook_url", ""),
            channel_id=data.get("channel_id", ""),
            team_id=data.get("team_id", ""),
            username=data.get("username", "Midicoder Bot"),
            icon_emoji=data.get("icon_emoji", "🤖"),
            enable_threading=data.get("enable_threading", False),
            mention_users=data.get("mention_users", []),
            description=data.get("description", ""),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationDispatch",
    "NotificationProvider",
    "DispatchResult",
    "WebhookConfig",
    "WebhookDelivery",
    "ChatIntegrationConfig",
    "ChatPlatform",
]
