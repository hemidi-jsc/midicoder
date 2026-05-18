"""
Mô-đun Notification Models.

Module này định nghĩa các data models cho CP12 Notification Emitter:
- NotificationChannel: Enum các kênh notification
- NotificationTemplate: Template cho notification với variable interpolation
- NotificationDispatch: Dispatch request cho notification
- NotificationProvider: Provider config
- DispatchResult: Kết quả sau khi dispatch
- WebhookConfig, WebhookDelivery: Webhook channel
- ChatIntegrationConfig, ChatPlatform: Chat integration
- DeliveryStatus, DeliveryAttempt, DeliveryTracking: Delivery tracking
- ABTestVariant, ABTestConfig: A/B Testing
"""

from __future__ import annotations

import hashlib
import hmac
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
        """Chuyển NotificationTemplate sang dictionary."""
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
        """Tạo NotificationTemplate từ dictionary."""
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
        """Chuyển NotificationDispatch sang dictionary."""
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
        """Chuyển NotificationProvider sang dictionary."""
        return {
            "provider_id": self.provider_id,
            "channel": self.channel.value,
            "config": self.config,
            "enabled": self.enabled,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationProvider":
        """Tạo NotificationProvider từ dictionary."""
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
        """Chuyển DispatchResult sang dictionary."""
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
        auth_secret: HMAC secret key
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
    auth_secret: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: int = 10
    payload_template: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate webhook config."""
        if not self.url or not self.url.strip():
            raise ValueError("url không được để rỗng")
        if self.method.upper() not in ("POST", "PUT", "PATCH"):
            raise ValueError(
                f"method không hợp lệ: {self.method}. "
                "Phải là POST, PUT, hoặc PATCH"
            )
        if self.timeout_seconds < 1:
            self.timeout_seconds = 30

    def to_dict(self) -> dict[str, Any]:
        """Chuyển webhook config sang dict."""
        return {
            "url": self.url,
            "method": self.method,
            "auth_type": self.auth_type.value,
            "auth_header": self.auth_header,
            "auth_secret": self.auth_secret,
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
            auth_secret=data.get("auth_secret", ""),
            headers=data.get("headers", {}),
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            retry_backoff_seconds=data.get("retry_backoff_seconds", 10),
            payload_template=data.get("payload_template", ""),
            description=data.get("description", ""),
        )

    def compute_hmac_signature(self, body: str) -> str:
        """
        Tính HMAC signature cho webhook payload.

        Args:
            body: Body string cần sign

        Returns:
            HMAC-SHA256 signature (hex)
        """
        if not self.auth_secret:
            return ""
        return hmac.new(
            self.auth_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


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
    delivery_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def mark_attempted(self, response_code: int, response_body: str) -> None:
        """Ghi nhận một lần thử delivery."""
        self.attempts += 1
        self.last_response_code = response_code
        self.last_response_body = response_body
        if 200 <= response_code < 300:
            self.status = "delivered"
            self.delivered_at = datetime.now().isoformat()
        elif response_code >= 500 or response_code == 429:
            self.status = "retried"
        else:
            self.status = "failed"

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
# Delivery Tracking
# ============================================================================


class DeliveryStatus(str, Enum):
    """Trạng thái delivery của notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


@dataclass
class DeliveryAttempt:
    """Record của một lần thử delivery.

    Attributes:
        attempt_id: UUID định danh duy nhất
        attempt_number: Số thứ tự của attempt
        timestamp: Thời điểm attempt
        status: Status của attempt
        response_code: HTTP response code (nếu có)
        response_body: Response body (nếu có)
        error_message: Error message (nếu có)
    """
    attempt_number: int
    timestamp: str
    status: str
    response_code: int = 0
    response_body: str = ""
    error_message: str = ""
    attempt_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DeliveryAttempt sang dict."""
        return {
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp,
            "status": self.status,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "error_message": self.error_message,
        }


@dataclass
class DeliveryTracking:
    """Tracking record cho notification delivery (end-to-end).

    Theo dõi lifecycle đầy đủ của một notification từ lúc pending
    đến khi delivered/opened/clicked.

    Attributes:
        tracking_id: UUID định danh duy nhất
        dispatch_id: Reference đến dispatch ID
        recipient: Người nhận
        channel: Channel đã sử dụng
        status: Delivery status hiện tại
        attempts: Danh sách attempts
        created_at: Thời điểm tạo tracking record
        updated_at: Thời điểm cập nhật cuối
        delivered_at: Thời điểm delivered thành công
        opened_at: Thời điểm opened (nếu có)
        clicked_at: Thời điểm clicked (nếu có)
        metadata: Metadata bổ sung
    """
    dispatch_id: str
    recipient: str
    channel: NotificationChannel
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: list[DeliveryAttempt] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    delivered_at: str | None = None
    opened_at: str | None = None
    clicked_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tracking_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_attempt(
        self,
        status: str,
        response_code: int = 0,
        response_body: str = "",
        error_message: str = "",
    ) -> DeliveryAttempt:
        """Ghi nhận một lần thử delivery."""
        attempt = DeliveryAttempt(
            attempt_number=len(self.attempts) + 1,
            timestamp=datetime.now().isoformat(),
            status=status,
            response_code=response_code,
            response_body=response_body,
            error_message=error_message,
        )
        self.attempts.append(attempt)
        self.updated_at = attempt.timestamp

        if status == "sent":
            self.status = DeliveryStatus.SENT
        elif status == "delivered":
            self.status = DeliveryStatus.DELIVERED
            self.delivered_at = attempt.timestamp
        elif status == "failed":
            self.status = DeliveryStatus.FAILED
        elif status == "bounced":
            self.status = DeliveryStatus.BOUNCED

        return attempt

    def mark_opened(self) -> None:
        """Mark notification đã được mở."""
        self.opened_at = datetime.now().isoformat()
        self.status = DeliveryStatus.OPENED
        self.updated_at = self.opened_at

    def mark_clicked(self) -> None:
        """Mark notification đã được click."""
        self.clicked_at = datetime.now().isoformat()
        self.status = DeliveryStatus.CLICKED
        self.updated_at = self.clicked_at

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DeliveryTracking sang dict."""
        return {
            "tracking_id": self.tracking_id,
            "dispatch_id": self.dispatch_id,
            "recipient": self.recipient,
            "channel": self.channel.value,
            "status": self.status.value,
            "attempts": [a.to_dict() for a in self.attempts],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "delivered_at": self.delivered_at,
            "opened_at": self.opened_at,
            "clicked_at": self.clicked_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeliveryTracking":
        """Tạo DeliveryTracking từ dict."""
        channel_value = data.get("channel", "email")
        channel = NotificationChannel(channel_value)

        status_value = data.get("status", "pending")
        status = DeliveryStatus(status_value)

        attempts_data = data.get("attempts", [])
        attempts = [
            DeliveryAttempt(
                attempt_id=a.get("attempt_id", ""),
                attempt_number=a.get("attempt_number", 0),
                timestamp=a.get("timestamp", ""),
                status=a.get("status", ""),
                response_code=a.get("response_code", 0),
                response_body=a.get("response_body", ""),
                error_message=a.get("error_message", ""),
            )
            for a in attempts_data
        ]

        return cls(
            tracking_id=data.get("tracking_id", ""),
            dispatch_id=data.get("dispatch_id", ""),
            recipient=data.get("recipient", ""),
            channel=channel,
            status=status,
            attempts=attempts,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            delivered_at=data.get("delivered_at"),
            opened_at=data.get("opened_at"),
            clicked_at=data.get("clicked_at"),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# A/B Testing
# ============================================================================


@dataclass
class ABTestVariant:
    """Variant trong A/B test cho notification.

    Mỗi variant đại diện cho một phiên bản khác nhau của notification
    (subject khác, content khác, gửi giờ khác, ...)

    Attributes:
        variant_id: ID của variant (vd: "A", "B", "control")
        template_id: Template ID cho variant này
        weight: Trọng số (tỷ lệ % người nhận được variant này)
        name: Tên hiển thị của variant
        description: Mô tả variant
    """
    variant_id: str
    template_id: str
    weight: float = 50.0
    name: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate variant."""
        if not self.variant_id or not self.variant_id.strip():
            raise ValueError("variant_id không được để rỗng")
        if self.weight < 0 or self.weight > 100:
            raise ValueError(
                f"weight phải trong khoảng 0-100, nhận được: {self.weight}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABTestVariant sang dict."""
        return {
            "variant_id": self.variant_id,
            "template_id": self.template_id,
            "weight": self.weight,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABTestVariant":
        """Tạo ABTestVariant từ dict."""
        return cls(
            variant_id=data.get("variant_id", ""),
            template_id=data.get("template_id", ""),
            weight=data.get("weight", 50.0),
            name=data.get("name", ""),
            description=data.get("description", ""),
        )


@dataclass
class ABTestConfig:
    """Configuration cho A/B test notification.

    Cho phép test nhiều variant của notification để tìm ra
    phiên bản có engagement cao nhất.

    Attributes:
        test_id: UUID định danh duy nhất của A/B test
        name: Tên của test
        channel: Channel để test (email, push, ...)
        variants: Danh sách variants
        start_at: Thời điểm bắt đầu test
        end_at: Thời điểm kết thúc test (nullable)
        is_active: Test có đang active không
        metric: Metric để đánh giá (open_rate, click_rate, conversion_rate)
        description: Mô tả test
    """
    name: str
    channel: NotificationChannel
    variants: list[ABTestVariant] = field(default_factory=list)
    start_at: str = field(default_factory=lambda: datetime.now().isoformat())
    end_at: str | None = None
    is_active: bool = True
    metric: str = "open_rate"
    description: str = ""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate A/B test config."""
        if not self.name or not self.name.strip():
            raise ValueError("name không được để rỗng")
        if len(self.variants) < 2:
            raise ValueError(
                "A/B test cần ít nhất 2 variants"
            )
        total_weight = sum(v.weight for v in self.variants)
        if abs(total_weight - 100.0) > 0.01:
            raise ValueError(
                f"Total weight của variants phải bằng 100, nhận được: {total_weight}"
            )

    def select_variant(self, recipient_hash: int) -> ABTestVariant:
        """
        Chọn variant dựa trên hash của recipient (deterministic).

        Args:
            recipient_hash: Hash value của recipient

        Returns:
            ABTestVariant được chọn
        """
        bucket = recipient_hash % 100
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight
            if bucket < cumulative:
                return variant
        return self.variants[-1]

    @staticmethod
    def hash_recipient(recipient: str) -> int:
        """Tính hash của recipient để chọn variant deterministic."""
        return int(hashlib.sha256(recipient.encode()).hexdigest(), 16)

    def get_variant_for_recipient(self, recipient: str) -> ABTestVariant:
        """Lấy variant cho recipient cụ thể (deterministic)."""
        h = self.hash_recipient(recipient)
        return self.select_variant(h)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABTestConfig sang dict."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "channel": self.channel.value,
            "variants": [v.to_dict() for v in self.variants],
            "start_at": self.start_at,
            "end_at": self.end_at,
            "is_active": self.is_active,
            "metric": self.metric,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABTestConfig":
        """Tạo ABTestConfig từ dict."""
        channel_value = data.get("channel", "email")
        channel = NotificationChannel(channel_value)

        variants_data = data.get("variants", [])
        variants = [ABTestVariant.from_dict(v) for v in variants_data]

        return cls(
            test_id=data.get("test_id", ""),
            name=data.get("name", ""),
            channel=channel,
            variants=variants,
            start_at=data.get("start_at", ""),
            end_at=data.get("end_at"),
            is_active=data.get("is_active", True),
            metric=data.get("metric", "open_rate"),
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
    "WebhookAuthType",
    "ChatIntegrationConfig",
    "ChatPlatform",
    "DeliveryStatus",
    "DeliveryAttempt",
    "DeliveryTracking",
    "ABTestVariant",
    "ABTestConfig",
]
