"""
Twilio SMS Gateway.

Concrete implementation của SmsGateway cho Twilio Messages API.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.emitters.core.notification.providers.base import SmsGateway
from midicoder.errors import ErrorCode, MidicoderErrorManager


class TwilioSmsGateway(SmsGateway):
    """
    Twilio SMS Gateway.

    Implementation cua SmsGateway su dung Twilio Messages API.

    Config required:
        account_sid: Twilio Account SID (bat buoc)
        auth_token: Twilio Auth Token (bat buoc)
        from_phone: So dien thoai gui (E.164 format)

    Example:
        >>> gateway = TwilioSmsGateway({
        ...     "account_sid": "ACxxx",
        ...     "auth_token": "token",
        ...     "from_phone": "+1234567890",
        ... })
    """

    API_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Khoi tao TwilioSmsGateway.

        Args:
            config: Configuration dictionary
        """
        self._account_sid = config.get("account_sid", "")
        self._auth_token = config.get("auth_token", "")
        self._from_phone = config.get("from_phone", "")

        if not self._account_sid or not self._auth_token:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="Twilio",
                missing_config=["account_sid", "auth_token"],
            )
        if not self._from_phone:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="Twilio",
                missing_config=["from_phone"],
            )

    def send(
        self,
        recipient: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gui SMS qua Twilio API.

        Args:
            recipient: Phone number nguoi nhan (E.164)
            body: SMS message content
            **kwargs: Additional parameters

        Returns:
            DispatchResult voi status va provider response
        """
        dispatch_id = kwargs.get("dispatch_id", str(uuid.uuid4()))

        data = {
            "From": self._from_phone,
            "To": recipient,
            "Body": body,
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.API_URL.format(sid=self._account_sid),
                    data=data,
                    auth=(self._account_sid, self._auth_token),
                    timeout=30.0,
                )

            if response.status_code == 201:
                result_data = response.json()
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={"sid": result_data.get("sid", "")},
                )
            else:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-005",
                    provider_response={"status_code": response.status_code},
                )

        except httpx.HTTPError as e:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
                provider_response={"error": str(e)},
            )