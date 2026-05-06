"""
Notification Models Module.

Module này định nghĩa các data models cho CP12 Notification Emitter:
- NotificationChannel: Enum các kênh notification (EMAIL, SMS, PUSH, WEBHOOK, IN_APP)
- NotificationTemplate: Template cho notification với variable interpolation
- NotificationDispatch: Dispatch request cho notification
- NotificationProvider: Provider config (SendGrid, Twilio, Firebase, etc.)
- DispatchResult: Kết quả sau khi dispatch notification

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
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

    Example:
        >>> template = NotificationTemplate(
        ...     template_id="welcome_email",
        ...     channel=NotificationChannel.EMAIL,
        ...     subject="Chào mừng {{name}}",
        ...     body_html="<h1>Xin chào {{name}}</h1>",
        ...     variables=["name"],
        ... )
    """

    template_id: str
    channel: NotificationChannel
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    variables: list[str] = field(default_factory=list)
    locale: str = "en"

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

        # Tìm tất cả {{variable}} patterns trong template
        pattern = re.compile(r"\{\{(\w+)\}\}")

        for key in ["subject", "body_html", "body_text"]:
            text = result[key]

            def _replacer(match: re.Match) -> str:
                var_name = match.group(1)
                if var_name in data:
                    return str(data[var_name])
                # Giữ nguyên variable nếu không có value
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
        # Resolve channel từ string value
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
        recipient: Người nhận (email, phone number, user_id, webhook_url)
        channel: Channel để gửi notification
        payload: Variable values cho template rendering
        status: Status hiện tại (pending, sent, failed, bounced)
        scheduled_at: Thời gian scheduled (optional)
        sent_at: Thời gian đã gửi (nullable)
        error_message: Error message nếu failed (nullable)

    Example:
        >>> dispatch = NotificationDispatch(
        ...     dispatch_id="disp_001",
        ...     template_ref="welcome_email",
        ...     recipient="user@example.com",
        ...     channel=NotificationChannel.EMAIL,
        ...     payload={"name": "Minh"},
        ... )
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

    Example:
        >>> provider = NotificationProvider(
        ...     provider_id="sendgrid_prod",
        ...     channel=NotificationChannel.EMAIL,
        ...     config={"api_key": "SG.xxx", "from_email": "noreply@test.com"},
        ...     priority=1,
        ... )
    """

    provider_id: str
    channel: NotificationChannel
    config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 99

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

    Example:
        >>> result = DispatchResult(
        ...     dispatch_id="disp_001",
        ...     status="sent",
        ...     provider_response={"message_id": "msg_123"},
        ... )
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
# Exports
# ============================================================================

__all__ = [
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationDispatch",
    "NotificationProvider",
    "DispatchResult",
]