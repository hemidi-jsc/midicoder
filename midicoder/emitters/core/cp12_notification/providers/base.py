"""
Provider Base Module.

Module này định nghĩa các abstract gateway interfaces:
- EmailGateway: Interface cho email providers
- SmsGateway: Interface cho SMS providers
- PushGateway: Interface cho push notification providers
- WebhookGateway: Interface cho webhook providers
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from midicoder.emitters.core.cp12_notification.models import (
    DispatchResult,
    WebhookConfig,
)


class EmailGateway(ABC):
    """Abstract gateway cho email providers."""

    @abstractmethod
    def send(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi email notification.

        Args:
            recipient: Email address người nhận
            subject: Subject line
            body_html: HTML body content
            body_text: Plain text body content
            **kwargs: Additional parameters

        Returns:
            DispatchResult với status và provider response
        """
        pass


class SmsGateway(ABC):
    """Abstract gateway cho SMS providers."""

    @abstractmethod
    def send(
        self,
        recipient: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi SMS notification.

        Args:
            recipient: Phone number người nhận (E.164 format)
            body: SMS message content
            **kwargs: Additional parameters

        Returns:
            DispatchResult với status và provider response
        """
        pass


class PushGateway(ABC):
    """Abstract gateway cho push notification providers."""

    @abstractmethod
    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi push notification.

        Args:
            recipient: Device/user ID
            title: Push notification title
            body: Push notification body
            **kwargs: Additional parameters (badge, sound, data)

        Returns:
            DispatchResult với status và provider response
        """
        pass


class WebhookGateway(ABC):
    """Abstract gateway cho webhook providers."""

    @abstractmethod
    def send(
        self,
        config: WebhookConfig,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi webhook notification.

        Args:
            config: WebhookConfig chứa URL, auth, headers
            payload: JSON payload để POST
            **kwargs: Additional parameters

        Returns:
            DispatchResult với status và provider response
        """
        pass
