# coding: utf-8
"""
Mô-đun models cho CP40 — Webhook & Outbound Integration Hub.

Định nghĩa các dataclass biểu diễn:
- WebhookAuthType: Loại xác thực webhook (none, bearer, basic, hmac)
- WebhookStatus: Trạng thái subscription (ACTIVE, INACTIVE, PAUSED, FAILED)
- WebhookSubscription: Đăng ký webhook endpoint (event_type → URL + auth)
- WebhookDispatch: Bản ghi dispatch (subscription → payload → delivery)
- WebhookDeliveryAttempt: Thử nghiệm dispatch (response_code, error, timestamp)
- RetryPolicy: Chính sách retry (exponential backoff)
- WebhookDispatcher: Engine dispatch webhook (subscribe → render → dispatch → audit)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP40).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class WebhookAuthType(str, Enum):
    """Loại xác thực cho outbound webhook.

    - NONE: Không xác thực
    - BEARER: Bearer token trong Authorization header
    - BASIC: Basic authentication (username:password)
    - HMAC: HMAC-SHA256 signature trong X-Webhook-Signature header
    """
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    HMAC = "hmac"


class WebhookStatus(str, Enum):
    """Trạng thái của webhook subscription.

    - ACTIVE: Subscription đang hoạt động, nhận event và dispatch
    - INACTIVE: Subscription bị vô hiệu hóa, không dispatch
    - PAUSED: Subscription tạm dừng, có thể activate lại
    - FAILED: Subscription bị lỗi (sau max retries), cần can thiệp
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    FAILED = "failed"


class DispatchStatus(str, Enum):
    """Trạng thái của webhook dispatch.

    - PENDING: Chờ dispatch
    - DISPATCHING: Đang dispatch
    - DELIVERED: Đã gửi thành công (HTTP 2xx)
    - FAILED: Thất bại (sau max retries)
    - RETRYING: Đang retry
    """
    PENDING = "pending"
    DISPATCHING = "dispatching"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# ===========================================================================
# WebhookAuthConfig
# ===========================================================================


@dataclass
class WebhookAuthConfig:
    """Cấu hình xác thực cho outbound webhook.

    Lưu trữ thông tin xác thực để gửi cùng với webhook payload.

    Attributes:
        auth_type: Loại xác thực (none, bearer, basic, hmac)
        header_name: Tên header (cho bearer/hmac)
        secret: Secret key (token, password, hoặc HMAC secret)
        algorithm: Algorithm cho HMAC (mặc định sha256)
    """
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    header_name: str = "Authorization"
    secret: str = ""
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        """Validate auth config sau khi khởi tạo."""
        if self.auth_type == WebhookAuthType.NONE:
            return

        if not self.secret or not self.secret.strip():
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_AUTH_CONFIG_INVALID,
                reason=f"secret bắt buộc khi auth_type={self.auth_type.value}",
            )

        if self.auth_type in (WebhookAuthType.BEARER, WebhookAuthType.HMAC):
            if not self.header_name or not self.header_name.strip():
                EM.raise_error(
                    ErrorCode.CP40_WEBHOOK_AUTH_CONFIG_INVALID,
                    reason="header_name bắt buộc cho bearer/hmac auth",
                )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WebhookAuthConfig sang dict."""
        return {
            "auth_type": self.auth_type.value,
            "header_name": self.header_name,
            "secret": self.secret,
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookAuthConfig":
        """Tạo WebhookAuthConfig từ dict."""
        return cls(
            auth_type=WebhookAuthType(data.get("auth_type", "none")),
            header_name=data.get("header_name", "Authorization"),
            secret=data.get("secret", ""),
            algorithm=data.get("algorithm", "sha256"),
        )


# ===========================================================================
# WebhookSubscription
# ===========================================================================


@dataclass
class WebhookSubscription:
    """Đăng ký webhook endpoint.

    Liên kết một event_type với một hoặc nhiều target URLs.
    Mỗi subscription có auth config, retry policy, và rate limit riêng.

    Attributes:
        subscription_id: ID duy nhất của subscription
        event_type: Tên event trigger dispatch (ví dụ: 'order.created')
        url: URL target endpoint
        http_method: HTTP method (POST, PUT, PATCH)
        auth_config: Cấu hình xác thực
        payload_template: Template JSON cho payload (support variable interpolation)
        retry_policy: Chính sách retry (max_retries, base_delay, max_delay)
        rate_limit_rpm: Rate limit (requests per minute)
        status: Trạng thái subscription
        tenant_id: Tenant ID (nullable — None = global)
        tags: Danh sách tags để phân loại
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    subscription_id: str
    event_type: str
    url: str
    http_method: str = "POST"
    auth_config: WebhookAuthConfig = field(default_factory=WebhookAuthConfig)
    payload_template: dict[str, Any] = field(default_factory=dict)
    retry_policy: dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "base_delay": 1.0, "max_delay": 60.0})
    rate_limit_rpm: int = 60
    status: WebhookStatus = WebhookStatus.ACTIVE
    tenant_id: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate subscription sau khi khởi tạo."""
        if not self.subscription_id or not self.subscription_id.strip():
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_SUBSCRIPTION_NOT_FOUND,
                subscription_id=self.subscription_id,
            )

        if not self.event_type or not self.event_type.strip():
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_SUBSCRIPTION_NOT_FOUND,
                subscription_id=self.subscription_id,
            )

        # Kiểm tra URL hợp lệ
        if not self._is_valid_url(self.url):
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_INVALID_URL,
                url=self.url,
            )

        if self.http_method not in ("POST", "PUT", "PATCH"):
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_INVALID_URL,
                url=f"HTTP method không hợp lệ: {self.http_method}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Kiểm tra URL có hợp lệ không.

        Args:
            url: URL cần kiểm tra

        Returns:
            True nếu URL hợp lệ
        """
        pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*(:\d{1,5})?(/[^\s]*)?$'
        return bool(re.match(pattern, url))

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WebhookSubscription sang dict."""
        return {
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "url": self.url,
            "http_method": self.http_method,
            "auth_config": self.auth_config.to_dict(),
            "payload_template": self.payload_template,
            "retry_policy": self.retry_policy,
            "rate_limit_rpm": self.rate_limit_rpm,
            "status": self.status.value,
            "tenant_id": self.tenant_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookSubscription":
        """Tạo WebhookSubscription từ dict."""
        auth_data = data.get("auth_config", {})
        auth_config = WebhookAuthConfig.from_dict(auth_data) if auth_data else WebhookAuthConfig()

        return cls(
            subscription_id=data.get("subscription_id", ""),
            event_type=data.get("event_type", ""),
            url=data.get("url", ""),
            http_method=data.get("http_method", "POST"),
            auth_config=auth_config,
            payload_template=data.get("payload_template", {}),
            retry_policy=data.get("retry_policy", {"max_retries": 3, "base_delay": 1.0, "max_delay": 60.0}),
            rate_limit_rpm=data.get("rate_limit_rpm", 60),
            status=WebhookStatus(data.get("status", "active")),
            tenant_id=data.get("tenant_id"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# WebhookDispatch
# ===========================================================================


@dataclass
class WebhookDispatch:
    """Bản ghi dispatch webhook.

    Theo dõi một lần dispatch từ subscription đến target endpoint.

    Attributes:
        dispatch_id: ID duy nhất của dispatch
        subscription_id: ID của subscription
        event_type: Event type trigger
        payload: Payload đã render (JSON dict)
        status: Trạng thái dispatch
        attempts: Số lần thử đã thực hiện
        created_at: Thời điểm tạo dispatch
        delivered_at: Thời điểm deliver thành công
    """
    dispatch_id: str
    subscription_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: DispatchStatus = DispatchStatus.PENDING
    attempts: int = 0
    created_at: datetime | None = None
    delivered_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate dispatch sau khi khởi tạo."""
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WebhookDispatch sang dict."""
        return {
            "dispatch_id": self.dispatch_id,
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status.value,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookDispatch":
        """Tạo WebhookDispatch từ dict."""
        return cls(
            dispatch_id=data.get("dispatch_id", ""),
            subscription_id=data.get("subscription_id", ""),
            event_type=data.get("event_type", ""),
            payload=data.get("payload", {}),
            status=DispatchStatus(data.get("status", "pending")),
            attempts=data.get("attempts", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            delivered_at=datetime.fromisoformat(data["delivered_at"]) if data.get("delivered_at") else None,
        )


# ===========================================================================
# WebhookDeliveryAttempt
# ===========================================================================


@dataclass
class WebhookDeliveryAttempt:
    """Thử nghiệm delivery webhook.

    Lưu trữ chi tiết mỗi lần thử dispatch.

    Attributes:
        attempt_id: ID duy nhất của attempt
        dispatch_id: ID của dispatch parent
        response_code: HTTP response code (None nếu chưa gửi)
        response_body: Response body (truncated)
        error: Error message (nếu có)
        timestamp: Thời điểm attempt
    """
    attempt_id: str
    dispatch_id: str
    response_code: int | None = None
    response_body: str = ""
    error: str = ""
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Validate attempt sau khi khởi tạo."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển WebhookDeliveryAttempt sang dict."""
        return {
            "attempt_id": self.attempt_id,
            "dispatch_id": self.dispatch_id,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookDeliveryAttempt":
        """Tạo WebhookDeliveryAttempt từ dict."""
        return cls(
            attempt_id=data.get("attempt_id", ""),
            dispatch_id=data.get("dispatch_id", ""),
            response_code=data.get("response_code"),
            response_body=data.get("response_body", ""),
            error=data.get("error", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
        )


# ===========================================================================
# RetryPolicy
# ===========================================================================


@dataclass
class RetryPolicy:
    """Chính sách retry cho webhook dispatch.

    Exponential backoff với configurable max_retries, base_delay, max_delay.

    Attributes:
        max_retries: Số lần retry tối đa
        base_delay: Delay ban đầu (giây)
        max_delay: Delay tối đa (giây)
        backoff_multiplier: Nhân tử exponential backoff
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Tính delay cho attempt cụ thể.

        Args:
            attempt: Số lần attempt hiện tại (0-based)

        Returns:
            Delay (giây) cho attempt này
        """
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, response_code: int | None = None) -> bool:
        """Kiểm tra có nên retry không.

        4xx non-retryable (trừ 429), 5xx/network errors retried.

        Args:
            attempt: Số lần attempt hiện tại
            response_code: HTTP response code (None = network error)

        Returns:
            True nếu nên retry
        """
        if attempt >= self.max_retries:
            return False

        # Network error (no response) — always retry
        if response_code is None:
            return True

        # 5xx — retry
        if 500 <= response_code < 600:
            return True

        # 429 Too Many Requests — retry
        if response_code == 429:
            return True

        # 4xx — don't retry
        if 400 <= response_code < 500:
            return False

        return True


# ===========================================================================
# WebhookDispatcher
# ===========================================================================


class WebhookDispatcher:
    """Engine dispatch webhook.

    Subscribe to domain events, render payload, dispatch via HTTP,
    và ghi audit log cho mỗi dispatch.

    Workflow:
    1. Nhận event (event_type, event_data)
    2. Tìm tất cả subscriptions matching event_type
    3. Render payload template với event_data
    4. Tạo dispatch record
    5. HTTP POST/PUT/PATCH đến target URL
    6. Theo dõi delivery attempt
    7. Retry theo policy nếu thất bại
    8. Ghi audit trail

    Attributes:
        subscriptions: Dict subscription_id -> WebhookSubscription
        dispatches: Dict dispatch_id -> WebhookDispatch
        delivery_attempts: List WebhookDeliveryAttempt
    """

    def __init__(self) -> None:
        self.subscriptions: dict[str, WebhookSubscription] = {}
        self.dispatches: dict[str, WebhookDispatch] = {}
        self.delivery_attempts: list[WebhookDeliveryAttempt] = []
        self._attempt_counter = 0

    def add_subscription(self, subscription: WebhookSubscription) -> None:
        """Thêm webhook subscription.

        Args:
            subscription: WebhookSubscription để thêm
        """
        self.subscriptions[subscription.subscription_id] = subscription

    def remove_subscription(self, subscription_id: str) -> bool:
        """Xóa webhook subscription.

        Args:
            subscription_id: ID của subscription

        Returns:
            True nếu xóa thành công
        """
        return self.subscriptions.pop(subscription_id, None) is not None

    def get_subscriptions_by_event(self, event_type: str) -> list[WebhookSubscription]:
        """Lấy tất cả subscriptions cho một event type.

        Args:
            event_type: Tên event type

        Returns:
            Danh sách WebhookSubscription matching
        """
        return [
            sub for sub in self.subscriptions.values()
            if sub.event_type == event_type and sub.status == WebhookStatus.ACTIVE
        ]

    def dispatch_event(self, event_type: str, event_data: dict[str, Any]) -> list[str]:
        """Dispatch event đến tất cả matching subscriptions.

        Args:
            event_type: Tên event type
            event_data: Dữ liệu event để render vào payload

        Returns:
            Danh sách dispatch_ids đã tạo
        """
        subscriptions = self.get_subscriptions_by_event(event_type)
        dispatch_ids: list[str] = []

        for sub in subscriptions:
            dispatch_id = self._generate_dispatch_id()

            # Render payload
            payload = self._render_payload(sub.payload_template, event_data)

            # Tạo dispatch record
            dispatch = WebhookDispatch(
                dispatch_id=dispatch_id,
                subscription_id=sub.subscription_id,
                event_type=event_type,
                payload=payload,
                status=DispatchStatus.PENDING,
            )
            self.dispatches[dispatch_id] = dispatch
            dispatch_ids.append(dispatch_id)

        return dispatch_ids

    def compute_hmac_signature(self, payload: dict[str, Any], secret: str, algorithm: str = "sha256") -> str:
        """Tính HMAC signature cho payload.

        Args:
            payload: Payload dict cần ký
            secret: Secret key
            algorithm: Algorithm HMAC (mặc định sha256)

        Returns:
            HMAC signature hex string
        """
        import json
        payload_str = json.dumps(payload, sort_keys=True, default=str)

        try:
            signature = hmac.new(
                secret.encode("utf-8"),
                payload_str.encode("utf-8"),
                algorithm,
            ).hexdigest()
            return signature
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_SIGNATURE_GENERATION_FAILED,
                reason=str(e),
            )

    def get_build_headers(self, subscription: WebhookSubscription, dispatch: WebhookDispatch) -> dict[str, str]:
        """Build HTTP headers cho dispatch.

        Args:
            subscription: Webhook subscription
            dispatch: Webhook dispatch

        Returns:
            Dict headers
        """
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Dispatch-ID": dispatch.dispatch_id,
            "X-Webhook-Timestamp": datetime.now(timezone.utc).isoformat(),
        }

        auth = subscription.auth_config
        if auth.auth_type == WebhookAuthType.BEARER:
            headers[auth.header_name] = f"Bearer {auth.secret}"
        elif auth.auth_type == WebhookAuthType.HMAC:
            signature = self.compute_hmac_signature(dispatch.payload, auth.secret, auth.algorithm)
            headers[auth.header_name] = signature

        return headers

    def _render_payload(self, template: dict[str, Any], event_data: dict[str, Any]) -> dict[str, Any]:
        """Render payload template với event data.

        Interpolate variables trong template bằng event data.
        Template syntax: {{variable_name}}

        Args:
            template: Payload template dict
            event_data: Event data để interpolate

        Returns:
            Rendered payload dict
        """
        if not template:
            return {"event_type": "", "data": event_data, "timestamp": datetime.now(timezone.utc).isoformat()}

        try:
            import json
            # Convert to string, interpolate, then back to dict
            template_str = json.dumps(template)
            for key, value in event_data.items():
                template_str = template_str.replace(f"{{{key}}}", str(value))
            return json.loads(template_str)
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP40_WEBHOOK_PAYLOAD_RENDER_FAILED,
                reason=str(e),
            )

    def _generate_dispatch_id(self) -> str:
        """Generate unique dispatch ID.

        Returns:
            Unique dispatch ID string
        """
        timestamp = time.time()
        return f"dispatch_{int(timestamp * 1000)}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"

    def _generate_attempt_id(self) -> str:
        """Generate unique attempt ID.

        Returns:
            Unique attempt ID string
        """
        self._attempt_counter += 1
        return f"attempt_{self._attempt_counter}"
