"""
SendGrid Email Gateway.

Concrete implementation của EmailGateway cho SendGrid API.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.emitters.core.notification.providers.base import EmailGateway
from midicoder.errors import ErrorCode, MidicoderErrorManager


class SendGridEmailGateway(EmailGateway):
    """
    SendGrid Email Gateway.

    Implementation của EmailGateway sử dụng SendGrid API v3.

    Config required:
        api_key: SendGrid API key (bắt buộc)
        from_email: Email address gửi (bắt buộc)
        from_name: Tên người gửi (optional)

    Example:
        >>> gateway = SendGridEmailGateway({
        ...     "api_key": "SG.xxx",
        ...     "from_email": "noreply@example.com",
        ... })
        >>> result = gateway.send("user@test.com", "Chào", "<h1>Xin chào</h1>")
    """

    API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Khởi tạo SendGridEmailGateway.

        Args:
            config: Configuration dictionary với api_key, from_email
        """
        self._api_key = config.get("api_key", "")
        self._from_email = config.get("from_email", "")
        self._from_name = config.get("from_name", "Midicoder")

        # Validate config
        if not self._api_key:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="SendGrid",
                missing_config=["api_key"],
            )
        if not self._from_email:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="SendGrid",
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
        Gửi email qua SendGrid API.

        Args:
            recipient: Email address người nhận
            subject: Subject line
            body_html: HTML body content
            body_text: Plain text body content
            **kwargs: Additional parameters

        Returns:
            DispatchResult với status và provider response

        Raises:
            MidicoderError: Nếu dispatch fail
        """
        dispatch_id = kwargs.get("dispatch_id", str(uuid.uuid4()))

        # Build SendGrid payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": recipient}],
                    "subject": subject,
                }
            ],
            "from": {"email": self._from_email, "name": self._from_name},
            "content": [
                {"type": "text/html", "value": body_html},
            ],
        }

        # Thêm plain text content nếu có
        if body_text:
            payload["content"].append({"type": "text/plain", "value": body_text})

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

            if response.status_code in (202, 200):
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={
                        "message_id": response.headers.get("x-message-id", ""),
                        "status_code": response.status_code,
                    },
                )
            else:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-005",
                    provider_response={
                        "status_code": response.status_code,
                        "error": response.text,
                    },
                )

        except httpx.HTTPError as e:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
                provider_response={"error": str(e)},
            )