"""
Twilio SMS Gateway Provider.

Twilio integration cho SMS notification delivery.
"""

from __future__ import annotations

import hashlib
import hmac as hmac_mod
import logging
import time
from typing import Any

from midicoder.packs.cp12_notification.models import DispatchResult
from midicoder.packs.cp12_notification.providers.base import SmsGateway

logger = logging.getLogger(__name__)


class TwilioSmsGateway(SmsGateway):
    """
    Twilio SMS gateway.

    Gửi SMS qua Twilio API, hỗ trợ:
    - Single recipient
    - Multiple recipients
    - Media URL (MMS)
    - Status callback
    - Signature verification

    Attributes:
        account_sid: Twilio Account SID
        auth_token: Twilio Auth Token
        from_phone: From phone number (E.164 format)
        status_callback: URL callback cho SMS status
    """

    TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"

    def __init__(
        self,
        account_sid: str = "",
        auth_token: str = "",
        from_phone: str = "",
        status_callback: str = "",
    ) -> None:
        """
        Khởi tạo Twilio SMS gateway.

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_phone: From phone number (E.164 format, vd: +1234567890)
            status_callback: URL callback cho SMS delivery status
        """
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_phone = from_phone
        self._status_callback = status_callback

    def send(
        self,
        recipient: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi SMS qua Twilio.

        Args:
            recipient: Phone number (E.164 format)
            body: SMS message content (max 160 chars cho 1 segment)
            **kwargs: Additional parameters:
                - media_url: URL của media attachment (MMS)
                - status_callback: Override callback URL
                - dispatch_id: Dispatch ID để track

        Returns:
            DispatchResult với status và provider response
        """
        dispatch_id = kwargs.pop("dispatch_id", "unknown")
        media_url = kwargs.pop("media_url", "")
        callback = kwargs.pop("status_callback", self._status_callback)

        if not self._account_sid or not self._auth_token:
            logger.error("Twilio: Account SID or Auth Token not configured")
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        if not self._from_phone:
            logger.error("Twilio: From phone number not configured")
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        if not recipient or not recipient.strip():
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-007",
            )

        try:
            # Build request body
            import urllib.parse
            import urllib.request

            form_data = {
                "From": self._from_phone,
                "To": recipient,
                "Body": body,
            }
            if media_url:
                form_data["MediaUrl"] = media_url
            if callback:
                form_data["StatusCallback"] = callback

            data = urllib.parse.urlencode(form_data).encode("utf-8")
            auth = urllib.parse.quote(
                f"{self._account_sid}:{self._auth_token}", safe=""
            )

            url = f"{self.TWILIO_API_BASE}/Accounts/{self._account_sid}/Messages.json"
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read().decode("utf-8")

                # Parse JSON response (không phụ thuộc external library)
                import json
                result = json.loads(resp_data)

                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={
                        "sid": result.get("sid", ""),
                        "status": result.get("status", "queued"),
                        "num_segments": result.get("num_segments", 1),
                        "from": self._from_phone,
                        "to": recipient,
                        "provider": "twilio",
                    },
                )

        except urllib.error.HTTPError as e:
            logger.error("Twilio HTTP error: %d - %s", e.code, str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
                provider_response={"http_code": e.code},
            )
        except Exception as e:
            logger.error("Twilio send failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    def verify_signature(
        self,
        url: str,
        params: dict[str, str],
        signature: str,
    ) -> bool:
        """
        Verify Twilio webhook signature.

        Bảo vệ callback endpoint khỏi request giả mạo.

        Args:
            url: Full URL nhận request (bao gồm query string)
            params: Request body parameters
            signature: X-Twilio-Signature header

        Returns:
            True nếu signature hợp lệ
        """
        if not self._auth_token:
            return False

        # Build body theo Twilio spec
        body = url
        for key in sorted(params.keys()):
            body += params[key]

        computed = hmac_mod.new(
            self._auth_token.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest()

        return hmac_mod.compare_digest(computed, signature)

    def get_message_status(
        self,
        message_sid: str,
    ) -> dict[str, Any]:
        """
        Lấy status của SMS đã gửi.

        Args:
            message_sid: Twilio Message SID

        Returns:
            Dict chứa status info
        """
        if not self._account_sid or not self._auth_token:
            return {"error": "Not configured"}

        try:
            import urllib.request
            import json

            auth = f"{self._account_sid}:{self._auth_token}"
            import base64
            auth_encoded = base64.b64encode(auth.encode()).decode()

            url = (
                f"{self.TWILIO_API_BASE}/Accounts/"
                f"{self._account_sid}/Messages/{message_sid}.json"
            )
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Basic {auth_encoded}"},
                method="GET",
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

        except Exception as e:
            logger.error("Twilio get status failed: %s", str(e))
            return {"error": str(e)}
