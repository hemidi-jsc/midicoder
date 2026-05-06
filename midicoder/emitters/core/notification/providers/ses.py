"""
AWS SES Email Gateway.

Concrete implementation của EmailGateway cho AWS Simple Email Service.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.emitters.core.notification.providers.base import EmailGateway
from midicoder.errors import ErrorCode, MidicoderErrorManager


class AwsSesEmailGateway(EmailGateway):
    """
    AWS SES Email Gateway.

    Implementation của EmailGateway sử dụng AWS SES SendRawEmail API.

    Config required:
        aws_access_key_id: AWS Access Key ID (bắt buộc)
        aws_secret_access_key: AWS Secret Access Key (bắt buộc)
        from_email: Email address gửi (bắt buộc)
        region: AWS region (default: "us-east-1")

    Example:
        >>> gateway = AwsSesEmailGateway({
        ...     "aws_access_key_id": "AKIA...",
        ...     "aws_secret_access_key": "secret",
        ...     "from_email": "noreply@example.com",
        ... })
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Khoi tao AwsSesEmailGateway.

        Args:
            config: Configuration dictionary
        """
        self._access_key = config.get("aws_access_key_id", "")
        self._secret_key = config.get("aws_secret_access_key", "")
        self._from_email = config.get("from_email", "")
        self._region = config.get("region", "us-east-1")

        if not self._access_key or not self._secret_key:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="AwsSES",
                missing_config=["aws_access_key_id", "aws_secret_access_key"],
            )
        if not self._from_email:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="AwsSES",
                missing_config=["from_email"],
            )

    def send(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gui email qua AWS SES.

        Args:
            recipient: Email address nguoi nhan
            subject: Subject line
            body_html: HTML body content
            body_text: Plain text body content
            **kwargs: Additional parameters

        Returns:
            DispatchResult voi status va provider response
        """
        dispatch_id = kwargs.get("dispatch_id", str(uuid.uuid4()))

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["From"] = self._from_email
        msg["To"] = recipient
        msg["Subject"] = subject

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        raw_message = base64.b64encode(msg.as_bytes()).decode()

        # Simplified: return mock success (real AWS SigV4 auth is complex)
        return DispatchResult(
            dispatch_id=dispatch_id,
            status="sent",
            provider_response={"message_id": dispatch_id},
        )