# coding: utf-8
"""
API Client Models (CP20).

Module này cung cấp các models cho API Client & Integration Generator:
- ApiSpec: Spec cho API client (base_url, auth, endpoints, realtime bridge)
- ClientBinding: Binding giữa client method và backend route
- RealtimeBridgeSpec: Spec cho realtime bridge (WebSocket/SSE)

Enums:
- TransportType: WEBSOCKET, SSE
- AuthMode: BEARER, COOKIE, NONE
- HttpMethod: GET, POST, PUT, PATCH, DELETE

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode


# ============================================================================
# Enums
# ============================================================================


class TransportType(str, Enum):
    """Loại transport cho realtime bridge."""
    WEBSOCKET = "websocket"
    SSE = "sse"


class AuthMode(str, Enum):
    """Phương thức auth cho API client."""
    BEARER = "bearer"
    COOKIE = "cookie"
    NONE = "none"


class HttpMethod(str, Enum):
    """HTTP method cho API endpoint."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# ============================================================================
# ClientBinding — Binding giữa client method và backend route
# ============================================================================


@dataclass
class ClientBinding:
    """
    Binding giữa client method và backend route.

    Attributes:
        client_method: Tên method trên client (ví dụ: getUsers)
        http_method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        backend_route: Route path trên backend (ví dụ: /api/users)
        request_type: Type của request body (nếu có)
        response_type: Type của response (nếu có)
        headers: Custom headers cho endpoint này
    """
    client_method: str
    http_method: HttpMethod
    backend_route: str
    request_type: Optional[str] = None
    response_type: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ClientBinding sau khi khởi tạo."""
        if not self.client_method or not self.client_method.strip():
            EM.raise_error(
                ErrorCode.CP20_OPENAPI_PARSE_ERROR,
                detail="client_method không được để trống",
            )
        if not self.backend_route or not self.backend_route.strip():
            EM.raise_error(
                ErrorCode.CP20_OPENAPI_PARSE_ERROR,
                detail="backend_route không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        return {
            "client_method": self.client_method,
            "http_method": self.http_method.value,
            "backend_route": self.backend_route,
            "request_type": self.request_type,
            "response_type": self.response_type,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientBinding":
        """Deserialise từ dict."""
        return cls(
            client_method=data["client_method"],
            http_method=HttpMethod(data.get("http_method", "GET")),
            backend_route=data["backend_route"],
            request_type=data.get("request_type"),
            response_type=data.get("response_type"),
            headers=data.get("headers", {}),
        )

    @classmethod
    def from_openapi_path(
        cls,
        path: str,
        method: str,
        operation: dict[str, Any],
    ) -> "ClientBinding":
        """
        Tạo ClientBinding từ OpenAPI path item.

        Args:
            path: Path trong OpenAPI (ví dụ: /api/users)
            method: HTTP method lowercase (get, post, ...)
            operation: Operation dict từ OpenAPI spec

        Returns:
            ClientBinding instance
        """
        op_id = operation.get("operationId", f"{method}_{path.replace('/', '_').strip('_')}")
        http_method = HttpMethod(method.upper())

        return cls(
            client_method=op_id,
            http_method=http_method,
            backend_route=path,
        )


# ============================================================================
# RealtimeBridgeSpec — Spec cho realtime bridge (WebSocket/SSE)
# ============================================================================


@dataclass
class RealtimeBridgeSpec:
    """
    Spec cho realtime bridge (WebSocket/SSE).

    Attributes:
        name: Tên bridge (ví dụ: OrderUpdates)
        transport: Loại transport (websocket, sse)
        url: URL của endpoint realtime
        channels: Danh sách channels để subscribe
        reconnect_attempts: Số lần reconnect tối đa
        reconnect_delay_ms: Delay giữa các lần reconnect (ms)
    """
    name: str
    transport: TransportType
    url: str
    channels: list[str] = field(default_factory=list)
    reconnect_attempts: int = 5
    reconnect_delay_ms: int = 1000

    def __post_init__(self) -> None:
        """Validate RealtimeBridgeSpec sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP20_BRIDGE_CONFIG_INVALID,
                detail="Bridge name không được để trống",
            )
        if not self.url or not self.url.strip():
            EM.raise_error(
                ErrorCode.CP20_BRIDGE_CONFIG_INVALID,
                detail="Bridge URL không được để trống",
            )
        # Validate URL format theo transport type
        if self.transport == TransportType.WEBSOCKET:
            if not self.url.startswith(("ws://", "wss://")):
                EM.raise_error(
                    ErrorCode.CP20_BRIDGE_CONFIG_INVALID,
                    detail=f"WebSocket URL phải bắt đầu bằng ws:// hoặc wss://, nhận được: {self.url}",
                )
        elif self.transport == TransportType.SSE:
            if not self.url.startswith(("http://", "https://")):
                EM.raise_error(
                    ErrorCode.CP20_BRIDGE_CONFIG_INVALID,
                    detail=f"SSE URL phải bắt đầu bằng http:// hoặc https://, nhận được: {self.url}",
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        return {
            "name": self.name,
            "transport": self.transport.value,
            "url": self.url,
            "channels": self.channels,
            "reconnect_attempts": self.reconnect_attempts,
            "reconnect_delay_ms": self.reconnect_delay_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RealtimeBridgeSpec":
        """Deserialise từ dict."""
        return cls(
            name=data["name"],
            transport=TransportType(data["transport"]),
            url=data["url"],
            channels=data.get("channels", []),
            reconnect_attempts=data.get("reconnect_attempts", 5),
            reconnect_delay_ms=data.get("reconnect_delay_ms", 1000),
        )


# ============================================================================
# ApiSpec — Spec cho API client
# ============================================================================


@dataclass
class ApiSpec:
    """
    Spec cho API client typed.

    Attributes:
        name: Tên API (ví dụ: CommerceAPI)
        base_url: Base URL của backend API
        auth_mode: Phương thức auth (bearer, cookie, none)
        timeout: Timeout cho requests (ms)
        retry_count: Số lần retry khi fail
        token_header: Header name cho auth token
        token_prefix: Prefix cho token (ví dụ: "Bearer ")
        bindings: Danh sách ClientBinding
        bridge: RealtimeBridgeSpec (nếu có realtime)
    """
    name: str
    base_url: str
    auth_mode: AuthMode = AuthMode.NONE
    timeout: int = 30000
    retry_count: int = 3
    token_header: str = "Authorization"
    token_prefix: str = "Bearer"
    bindings: list[ClientBinding] = field(default_factory=list)
    bridge: Optional[RealtimeBridgeSpec] = None

    def __post_init__(self) -> None:
        """Validate ApiSpec sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(
                ErrorCode.CP20_OPENAPI_PARSE_ERROR,
                detail="API name không được để trống",
            )
        if not self.base_url or not self.base_url.strip():
            EM.raise_error(
                ErrorCode.CP20_OPENAPI_PARSE_ERROR,
                detail="Base URL không được để trống",
            )
        # Kiểm tra duplicate endpoint (Obligation)
        methods = [b.client_method for b in self.bindings]
        if len(methods) != len(set(methods)):
            duplicates = [m for m in methods if methods.count(m) > 1]
            EM.raise_error(
                ErrorCode.CP20_ENDPOINT_DUPLICATE,
                detail=f"Duplicate client_method: {set(duplicates)}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        result: dict[str, Any] = {
            "name": self.name,
            "base_url": self.base_url,
            "auth_mode": self.auth_mode.value,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "token_header": self.token_header,
            "token_prefix": self.token_prefix,
        }
        if self.bindings:
            result["bindings"] = [b.to_dict() for b in self.bindings]
        if self.bridge:
            result["bridge"] = self.bridge.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiSpec":
        """Deserialise từ dict."""
        result: dict[str, Any] = {
            "name": data["name"],
            "base_url": data["base_url"],
            "auth_mode": AuthMode(data.get("auth_mode", "none")),
            "timeout": data.get("timeout", 30000),
            "retry_count": data.get("retry_count", 3),
            "token_header": data.get("token_header", "Authorization"),
            "token_prefix": data.get("token_prefix", "Bearer"),
        }
        if "bindings" in data:
            result["bindings"] = [ClientBinding.from_dict(b) for b in data["bindings"]]
        if "bridge" in data:
            result["bridge"] = RealtimeBridgeSpec.from_dict(data["bridge"])
        return cls(**result)

    @classmethod
    def from_openapi(cls, openapi_spec: dict[str, Any]) -> "ApiSpec":
        """
        Tạo ApiSpec từ OpenAPI 3.x spec dict.

        Args:
            openapi_spec: OpenAPI 3.x spec dict

        Returns:
            ApiSpec instance với bindings từ paths

        Raises:
            MidicoderError: Nếu OpenAPI spec không hợp lệ
        """
        # Lấy info
        info = openapi_spec.get("info", {})
        api_name = info.get("title", "API")

        # Lấy base URL từ servers
        servers = openapi_spec.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost"

        # Parse paths thành bindings
        bindings: list[ClientBinding] = []
        paths = openapi_spec.get("paths", {})
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method in methods:
                if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    continue
                operation = methods[method]
                binding = ClientBinding.from_openapi_path(path, method, operation)
                bindings.append(binding)

        return cls(
            name=api_name,
            base_url=base_url,
            auth_mode=AuthMode.NONE,
            bindings=bindings,
        )


__all__ = [
    # Enums
    "TransportType",
    "AuthMode",
    "HttpMethod",
    # Models
    "ClientBinding",
    "RealtimeBridgeSpec",
    "ApiSpec",
]
