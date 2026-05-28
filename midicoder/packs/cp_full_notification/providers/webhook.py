"""
Webhook Gateway Provider.

Gửi HTTP webhook notification với:
- Multiple auth types (None, Basic, Bearer, HMAC-SHA256)
- Retry với exponential backoff
- Response tracking
"""

from __future__ import annotations

import logging
import time
from typing import Any

import urllib.parse
import urllib.request
import urllib.error

from midicoder.packs.cp_full_notification.models import (
    DispatchResult,
    WebhookConfig,
    WebhookAuthType,
)
from midicoder.packs.cp_full_notification.providers.base import WebhookGateway

logger = logging.getLogger(__name__)


class WebhookGatewayImpl(WebhookGateway):
    """
    HTTP webhook gateway.

    Gửi webhook qua HTTP POST/PUT/PATCH với:
    - Auth: None, Basic, Bearer token, HMAC-SHA256 signature
    - Retry với exponential backoff
    - Timeout configurable
    - Response tracking (status code, body)
    """

    def __init__(
        self,
        default_timeout: int = 30,
        default_max_retries: int = 3,
        default_backoff: int = 10,
    ) -> None:
        """
        Khởi tạo WebhookGateway.

        Args:
            default_timeout: Default timeout (giây)
            default_max_retries: Default số lần retry
            default_backoff: Default backoff giữa retries (giây)
        """
        self._default_timeout = default_timeout
        self._default_max_retries = default_max_retries
        self._default_backoff = default_backoff

    def send(
        self,
        config: WebhookConfig,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi webhook notification.

        Args:
            config: WebhookConfig (URL, auth, headers, timeout, retries)
            payload: JSON body
            **kwargs:
                - dispatch_id: Dispatch ID để track
                - max_retries: Override số lần retry
                - backoff: Override backoff seconds

        Returns:
            DispatchResult với status và provider response
        """
        dispatch_id = kwargs.pop("dispatch_id", "unknown")
        max_retries = kwargs.pop("max_retries", config.max_retries)
        backoff = kwargs.pop("backoff", config.retry_backoff_seconds)
        timeout = config.timeout_seconds or self._default_timeout

        if not config.url or not config.url.strip():
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
                provider_response={"error": "Webhook URL is empty"},
            )

        # Build JSON body
        import json
        body = json.dumps(payload)

        # Build headers
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "Midicoder-Webhook/1.0",
        }
        headers.update(config.headers)

        # Add auth headers
        self._apply_auth(headers, config)

        max_attempts = max_retries + 1

        for attempt in range(max_attempts):
            try:
                req = urllib.request.Request(
                    config.url,
                    data=body.encode("utf-8"),
                    headers=headers,
                    method=config.method.upper(),
                )

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    response_body = resp.read().decode("utf-8", errors="replace")
                    response_code = resp.getcode()

                    return DispatchResult(
                        dispatch_id=dispatch_id,
                        status="sent",
                        provider_response={
                            "status_code": response_code,
                            "response_body": response_body,
                            "url": config.url,
                            "method": config.method,
                            "provider": "webhook",
                            "attempts": attempt + 1,
                        },
                    )

            except urllib.error.HTTPError as e:
                response_code = e.code
                logger.warning(
                    "Webhook HTTP error (attempt %d/%d): %d - %s",
                    attempt + 1, max_attempts, response_code, config.url,
                )

                # 4xx errors are not retried (except 429)
                if 400 <= response_code < 500 and response_code != 429:
                    return DispatchResult(
                        dispatch_id=dispatch_id,
                        status="failed",
                        error_code="MDC-CP12-005",
                        provider_response={
                            "status_code": response_code,
                            "url": config.url,
                            "provider": "webhook",
                        },
                    )

                if attempt < max_retries:
                    time.sleep(min(backoff * (2 ** attempt), 60))

            except (urllib.error.URLError, OSError, TimeoutError) as e:
                logger.warning(
                    "Webhook connection error (attempt %d/%d): %s",
                    attempt + 1, max_attempts, str(e),
                )
                if attempt < max_retries:
                    time.sleep(min(backoff * (2 ** attempt), 60))

        # All attempts exhausted
        return DispatchResult(
            dispatch_id=dispatch_id,
            status="failed",
            error_code="MDC-CP12-005",
            provider_response={
                "url": config.url,
                "max_attempts": max_attempts,
                "provider": "webhook",
                "error": "All retry attempts exhausted",
            },
        )

    def _apply_auth(
        self,
        headers: dict[str, str],
        config: WebhookConfig,
    ) -> None:
        """Apply authentication headers based on auth type."""
        if config.auth_type == WebhookAuthType.BASIC and config.auth_header:
            headers["Authorization"] = f"Basic {config.auth_header}"

        elif config.auth_type == WebhookAuthType.BEARER and config.auth_header:
            headers["Authorization"] = f"Bearer {config.auth_header}"

        elif config.auth_type == WebhookAuthType.HMAC and config.auth_secret:
            headers["X-Webhook-Signature"] = config.auth_secret


def verify_webhook_signature(
    body: str,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 webhook signature.

    Bảo vệ webhook receiver endpoint khỏi request giả mạo.

    Args:
        body: Raw request body
        signature: Received signature (X-Webhook-Signature header)
        secret: Shared HMAC secret

    Returns:
        True nếu signature hợp lệ
    """
    import hmac as hmac_mod
    import hashlib

    computed = hmac_mod.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac_mod.compare_digest(computed, signature)
