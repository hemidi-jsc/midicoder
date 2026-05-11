"""
Firebase FCM Push Gateway Provider (Stub).

Firebase Cloud Messaging integration placeholder for push notifications.
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.notification.models import DispatchResult
from midicoder.emitters.core.notification.providers.base import PushGateway


class FirebasePushGateway(PushGateway):
    """Firebase FCM push gateway (stub implementation)."""

    def __init__(
        self,
        credentials_path: str = "",
        project_id: str = "",
    ) -> None:
        self._credentials_path = credentials_path
        self._project_id = project_id

    def send(
        self,
        recipient: str,
        title: str,
        body: str,
        **kwargs: Any,
    ) -> DispatchResult:
        """Gửi push notification qua Firebase FCM (stub)."""
        dispatch_id = kwargs.pop("dispatch_id", "unknown")

        if not self._credentials_path:
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )

        # Stub: trả về sent giả định
        return DispatchResult(
            dispatch_id=dispatch_id,
            status="sent",
            provider_response={"to": recipient, "provider": "firebase_fcm"},
        )
