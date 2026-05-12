# coding: utf-8
"""
CP20 — API Client & Integration Generator.

Module này cung cấp typed API client generation từ OpenAPI spec,
realtime WebSocket/SSE bridge, và client↔backend type binding.

Capabilities:
- api_client_generate: Sinh typed API client từ OpenAPI spec
- realtime_bridge: WebSocket/SSE bridge với auto-reconnect
- openapi_bind: Auto-generate TypeScript interfaces từ backend spec

Obligations:
1. Type Safety: Client types match backend
2. Error Mapping: Backend error → Client error via interceptor
3. Auth Injection: Auto-attach auth token per request

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.api_client.models import (
    ApiSpec,
    ClientBinding,
    RealtimeBridgeSpec,
    AuthMode,
    HttpMethod,
    TransportType,
)
from midicoder.emitters.core.api_client.angular import (
    AngularApiEmitter,
)
from midicoder.emitters.core.api_client.react import (
    ReactApiEmitter,
)
from midicoder.emitters.core.api_client.fastapi import (
    FastAPIApiEmitter,
)
from midicoder.emitters.core.api_client.nestjs import (
    NestJSApiEmitter,
)

__all__ = [
    # Models
    "ApiSpec",
    "ClientBinding",
    "RealtimeBridgeSpec",
    "AuthMode",
    "HttpMethod",
    "TransportType",
    # Emitters
    "AngularApiEmitter",
    "ReactApiEmitter",
    "FastAPIApiEmitter",
    "NestJSApiEmitter",
]
