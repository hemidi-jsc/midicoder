"""
SendGrid Email Gateway Provider (Stub).

SendGrid integration placeholder cho production email delivery.
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp_full_notification.models import DispatchResult
from midicoder.packs.cp_full_notification.providers.base import EmailGateway
from midicoder.errors import ErrorCode


class SendGridEmailGateway(EmailGateway):
    """SendGrid email gateway (stub implementation)."""

    def __init__(
        self,
        api_key: str = "",
        from_email: str = "noreply@midicoder.dev",
    ) -> None:
        self._api_key = api_key
        self._from_email = from_email

    def send(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        **kwargs: Any,
    ) -> DispatchResult:
        """Gửi email qua SendGrid (stub)."""
        dispatch_id = kwargs.pop("dispatch_id", "unknown")

        if not self._api_key:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        # Stub: trả về sent giả định
        return DispatchResult(
            dispatch_id=dispatch_id,
            status="sent",
            provider_response={"to": recipient, "provider": "sendgrid"},
        )
