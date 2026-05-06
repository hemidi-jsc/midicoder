"""
Firebase FCM Push Gateway.

Concrete implementation cua PushGateway cho Firebase Cloud Messaging v1 API.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.emitters.core.notification.providers.base import PushGateway
from midicoder.errors import ErrorCode, MidicoderErrorManager


class FirebasePushGateway(PushGateway):
    """
    Firebase FCM Push Gateway.

    Implementation cua PushGateway su dung Firebase Cloud Messaging v1 API.

    Config required:
        project_id: Firebase project ID (bat buoc)
        access_token: OAuth2 access token (bat buoc)

    Example:
        >>> gateway = FirebasePushGateway({
        ...     "project_id": "my-project",
        ...     "access_token": "ya29.xxx",
        ... })
    """

    API_URL = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Khoi tao FirebasePushGateway.

        Args:
            config: Configuration dictionary
        """
        self._project_id = config.get("project_id", "")
        self._access_token = config.get("access_token", "")

        if not self._project_id:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="FirebaseFCM",
                missing_config=["project_id"],
            )
        if not self._access_token:
            raise MidicoderErrorManager.raise_error(
                ErrorCode.CP12_NOTIFICATION_PROVIDER_NOT_CONFIGURED,
                provider="FirebaseFCM",
                missing_config=["access_token"],
            )

    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gui push notification qua Firebase FCM.

        Args:
            recipient: Device token
            title: Push notification title
            body: Push notification body
            **kwargs: Additional parameters (badge, sound, data)

        Returns:
            DispatchResult voi status va provider response
        """
        dispatch_id = kwargs.get("dispatch_id", str(uuid.uuid4()))

        payload = {
            "message": {
                "token": recipient,
                "notification": {
                    "title": title,
                    "body": body,
                },
            }
        }

        # Add data payload if provided
        if "data" in kwargs and kwargs["data"]:
            payload["message"]["data"] = kwargs["data"]

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.API_URL.format(project_id=self._project_id),
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

            if response.status_code == 200:
                result_data = response.json()
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={"name": result_data.get("name", "")},
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