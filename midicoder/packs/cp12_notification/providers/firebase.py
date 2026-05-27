"""
Firebase FCM Push Gateway Provider.

Firebase Cloud Messaging integration cho push notification delivery.
Hỗ trợ FCM v1 API (HTTP-based).
"""

from __future__ import annotations

import logging
from typing import Any

import urllib.request
import urllib.error
import json

from midicoder.packs.cp12_notification.models import DispatchResult
from midicoder.packs.cp12_notification.providers.base import PushGateway

logger = logging.getLogger(__name__)


class FirebasePushGateway(PushGateway):
    """
    Firebase Cloud Messaging (FCM) push gateway.

    Gửi push notification qua Firebase FCM v1 HTTP API.

    Attributes:
        project_id: Firebase project ID
        access_token: OAuth 2.0 access token (hoặc service account JSON path)
        credentials_path: Path to service account JSON file
    """

    FCM_API_BASE = "https://fcm.googleapis.com/v1"

    def __init__(
        self,
        project_id: str = "",
        access_token: str = "",
        credentials_path: str = "",
    ) -> None:
        """
        Khởi tạo Firebase FCM gateway.

        Args:
            project_id: Firebase project ID
            access_token: OAuth 2.0 access token
            credentials_path: Path to service account JSON (alternative to access_token)
        """
        self._project_id = project_id
        self._access_token = access_token
        self._credentials_path = credentials_path

    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi push notification qua Firebase FCM.

        Args:
            recipient: Device token hoặc user ID
            title: Notification title
            body: Notification body
            **kwargs:
                - dispatch_id: Dispatch ID để track
                - topic: Topic name (cho topic messaging)
                - data: Custom data payload
                - badge: Badge count (iOS)
                - sound: Sound name
                - priority: "normal" hoặc "high"

        Returns:
            DispatchResult với status và provider response
        """
        dispatch_id = kwargs.pop("dispatch_id", "unknown")
        topic = kwargs.pop("topic", "")
        data_payload = kwargs.pop("data", {})
        badge = kwargs.pop("badge", 0)
        sound = kwargs.pop("sound", "default")
        priority = kwargs.pop("priority", "normal")

        if not self._project_id:
            logger.error("Firebase: Project ID not configured")
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        token = self._get_access_token()
        if not token:
            logger.error("Firebase: Access token not available")
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        # Build FCM message
        message = {
            "notification": {
                "title": title,
                "body": body,
            },
            "data": {str(k): str(v) for k, v in data_payload.items()},
            "android": {
                "priority": priority,
                "notification": {
                    "sound": sound,
                },
            },
            "apns": {
                "payload": {
                    "aps": {
                        "sound": sound,
                    }
                }
            },
        }
        if badge:
            message["apns"]["payload"]["aps"]["badge"] = badge

        # Target
        if topic:
            message["topic"] = topic
        else:
            message["token"] = recipient

        body_json = json.dumps({"message": message})

        try:
            url = f"{self.FCM_API_BASE}/projects/{self._project_id}/messages:send"
            req = urllib.request.Request(
                url,
                data=body_json.encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={
                        "name": resp_data.get("name", ""),
                        "to": recipient,
                        "provider": "firebase_fcm",
                    },
                )

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error("Firebase HTTP error: %d - %s", e.code, error_body)
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
                provider_response={"http_code": e.code, "detail": error_body},
            )
        except Exception as e:
            logger.error("Firebase send failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    def _get_access_token(self) -> str:
        """Lấy access token (từ config hoặc refresh)."""
        if self._access_token:
            return self._access_token

        # Nếu có credentials_path, load service account
        # (Trong thực tế dùng google-auth-library, ở đây placeholder)
        if self._credentials_path:
            # TODO: Implement proper OAuth token refresh
            # from google.oauth2 import service_account
            # from google.auth.transport.requests import Request
            pass

        return ""

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi push notification đến topic.

        Args:
            topic: Topic name (vd: "all_users", "premium")
            title: Notification title
            body: Notification body
            **kwargs: Same as send()

        Returns:
            DispatchResult
        """
        return self.send(
            recipient="",
            title=title,
            body=body,
            topic=topic,
            **kwargs,
        )

    def send_condition(
        self,
        condition: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi push notification đến condition (topic expression).

        Args:
            condition: Topic condition (vd: "'A' in topics && 'B' in topics")
            title: Notification title
            body: Notification body
            **kwargs: Same as send()

        Returns:
            DispatchResult
        """
        dispatch_id = kwargs.pop("dispatch_id", "unknown")

        if not self._project_id:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        token = self._get_access_token()
        if not token:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        data_payload = kwargs.pop("data", {})
        sound = kwargs.pop("sound", "default")
        priority = kwargs.pop("priority", "normal")

        message = {
            "notification": {
                "title": title,
                "body": body,
            },
            "data": {str(k): str(v) for k, v in data_payload.items()},
            "condition": condition,
            "android": {"priority": priority},
        }

        body_json = json.dumps({"message": message})

        try:
            url = f"{self.FCM_API_BASE}/projects/{self._project_id}/messages:send"
            req = urllib.request.Request(
                url,
                data=body_json.encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="sent",
                    provider_response={
                        "name": resp_data.get("name", ""),
                        "condition": condition,
                        "provider": "firebase_fcm",
                    },
                )

        except urllib.error.HTTPError as e:
            logger.error("Firebase condition error: %d", e.code)
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )
        except Exception as e:
            logger.error("Firebase condition failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )
