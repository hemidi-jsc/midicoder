"""
Tests cho CP20 API Client models.

Kiểm tra:
- TransportType enum
- AuthMode enum
- HttpMethod enum
- ClientBinding dataclass
- RealtimeBridgeSpec dataclass
- ApiSpec dataclass
"""

import pytest

from midicoder.packs.cp_backend_api_client.models import (
    ApiSpec,
    AuthMode,
    ClientBinding,
    HttpMethod,
    RealtimeBridgeSpec,
    TransportType,
)
from midicoder.errors import MidicoderError


class TestTransportType:
    """Tests cho TransportType enum."""

    def test_transport_types_exist(self):
        assert TransportType.WEBSOCKET.value == "websocket"
        assert TransportType.SSE.value == "sse"

    def test_transport_type_from_string(self):
        assert TransportType("websocket") == TransportType.WEBSOCKET
        assert TransportType("sse") == TransportType.SSE


class TestAuthMode:
    """Tests cho AuthMode enum."""

    def test_auth_modes_exist(self):
        assert AuthMode.BEARER.value == "bearer"
        assert AuthMode.COOKIE.value == "cookie"
        assert AuthMode.NONE.value == "none"

    def test_auth_mode_from_string(self):
        assert AuthMode("bearer") == AuthMode.BEARER
        assert AuthMode("cookie") == AuthMode.COOKIE


class TestHttpMethod:
    """Tests cho HttpMethod enum."""

    def test_http_methods_exist(self):
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.PATCH.value == "PATCH"
        assert HttpMethod.DELETE.value == "DELETE"

    def test_http_method_from_string(self):
        assert HttpMethod("GET") == HttpMethod.GET
        assert HttpMethod("POST") == HttpMethod.POST


class TestClientBinding:
    """Tests cho ClientBinding dataclass."""

    def test_creation(self):
        binding = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.GET,
            backend_route="/api/users",
        )
        assert binding.client_method == "getUsers"
        assert binding.http_method == HttpMethod.GET
        assert binding.backend_route == "/api/users"
        assert binding.request_type is None
        assert binding.response_type is None
        assert binding.headers == {}

    def test_creation_with_all_fields(self):
        binding = ClientBinding(
            client_method="createOrder",
            http_method=HttpMethod.POST,
            backend_route="/api/orders",
            request_type="OrderCreate",
            response_type="Order",
            headers={"X-Custom": "value"},
        )
        assert binding.request_type == "OrderCreate"
        assert binding.response_type == "Order"
        assert binding.headers == {"X-Custom": "value"}

    def test_empty_client_method_raises(self):
        with pytest.raises(MidicoderError):
            ClientBinding(
                client_method="",
                http_method=HttpMethod.GET,
                backend_route="/api/users",
            )

    def test_empty_backend_route_raises(self):
        with pytest.raises(MidicoderError):
            ClientBinding(
                client_method="getUsers",
                http_method=HttpMethod.GET,
                backend_route="",
            )

    def test_whitespace_client_method_raises(self):
        with pytest.raises(MidicoderError):
            ClientBinding(
                client_method="   ",
                http_method=HttpMethod.GET,
                backend_route="/api/users",
            )

    def test_to_dict(self):
        binding = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.GET,
            backend_route="/api/users",
            headers={"X-Custom": "value"},
        )
        d = binding.to_dict()
        assert d["client_method"] == "getUsers"
        assert d["http_method"] == "GET"
        assert d["backend_route"] == "/api/users"
        assert d["headers"] == {"X-Custom": "value"}

    def test_from_dict(self):
        d = {
            "client_method": "getUsers",
            "http_method": "GET",
            "backend_route": "/api/users",
            "request_type": "UserCreate",
            "response_type": "User",
            "headers": {"X-Test": "val"},
        }
        binding = ClientBinding.from_dict(d)
        assert binding.client_method == "getUsers"
        assert binding.http_method == HttpMethod.GET
        assert binding.request_type == "UserCreate"

    def test_from_openapi_path(self):
        op = {"operationId": "listUsers"}
        binding = ClientBinding.from_openapi_path("/api/users", "get", op)
        assert binding.client_method == "listUsers"
        assert binding.http_method == HttpMethod.GET
        assert binding.backend_route == "/api/users"

    def test_from_openapi_path_without_operation_id(self):
        op = {}
        binding = ClientBinding.from_openapi_path("/api/users", "post", op)
        assert binding.http_method == HttpMethod.POST
        assert binding.backend_route == "/api/users"


class TestRealtimeBridgeSpec:
    """Tests cho RealtimeBridgeSpec dataclass."""

    def test_creation(self):
        bridge = RealtimeBridgeSpec(
            name="OrderUpdates",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost:8000/ws",
        )
        assert bridge.name == "OrderUpdates"
        assert bridge.transport == TransportType.WEBSOCKET
        assert bridge.reconnect_attempts == 5
        assert bridge.reconnect_delay_ms == 1000

    def test_creation_with_channels(self):
        bridge = RealtimeBridgeSpec(
            name="Chat",
            transport=TransportType.SSE,
            url="https://api.example.com/sse",
            channels=["general", "support"],
        )
        assert bridge.channels == ["general", "support"]

    def test_empty_name_raises(self):
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="",
                transport=TransportType.WEBSOCKET,
                url="ws://localhost/ws",
            )

    def test_empty_url_raises(self):
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="Test",
                transport=TransportType.WEBSOCKET,
                url="",
            )

    def test_websocket_url_format(self):
        bridge = RealtimeBridgeSpec(
            name="Test",
            transport=TransportType.WEBSOCKET,
            url="wss://secure.example.com/ws",
        )
        assert bridge.url == "wss://secure.example.com/ws"

    def test_websocket_invalid_url_raises(self):
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="Test",
                transport=TransportType.WEBSOCKET,
                url="http://localhost/ws",
            )

    def test_sse_url_format(self):
        bridge = RealtimeBridgeSpec(
            name="Test",
            transport=TransportType.SSE,
            url="https://api.example.com/events",
        )
        assert bridge.url == "https://api.example.com/events"

    def test_sse_invalid_url_raises(self):
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="Test",
                transport=TransportType.SSE,
                url="ws://localhost/events",
            )

    def test_to_dict(self):
        bridge = RealtimeBridgeSpec(
            name="Test",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost/ws",
            channels=["ch1"],
            reconnect_attempts=10,
            reconnect_delay_ms=500,
        )
        d = bridge.to_dict()
        assert d["name"] == "Test"
        assert d["transport"] == "websocket"
        assert d["channels"] == ["ch1"]
        assert d["reconnect_attempts"] == 10

    def test_from_dict(self):
        d = {
            "name": "Test",
            "transport": "sse",
            "url": "https://localhost/events",
            "channels": ["a", "b"],
            "reconnect_attempts": 3,
            "reconnect_delay_ms": 2000,
        }
        bridge = RealtimeBridgeSpec.from_dict(d)
        assert bridge.name == "Test"
        assert bridge.transport == TransportType.SSE
        assert bridge.reconnect_delay_ms == 2000


class TestApiSpec:
    """Tests cho ApiSpec dataclass."""

    def test_creation(self):
        spec = ApiSpec(
            name="CommerceAPI",
            base_url="https://api.example.com",
        )
        assert spec.name == "CommerceAPI"
        assert spec.base_url == "https://api.example.com"
        assert spec.auth_mode == AuthMode.NONE
        assert spec.timeout == 30000
        assert spec.retry_count == 3

    def test_creation_with_auth(self):
        spec = ApiSpec(
            name="SecureAPI",
            base_url="https://api.example.com",
            auth_mode=AuthMode.BEARER,
            token_header="Authorization",
            token_prefix="Bearer",
        )
        assert spec.auth_mode == AuthMode.BEARER
        assert spec.token_header == "Authorization"

    def test_empty_name_raises(self):
        with pytest.raises(MidicoderError):
            ApiSpec(name="", base_url="https://api.example.com")

    def test_empty_base_url_raises(self):
        with pytest.raises(MidicoderError):
            ApiSpec(name="Test", base_url="")

    def test_duplicate_bindings_raises(self):
        b1 = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.GET,
            backend_route="/api/users",
        )
        b2 = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.POST,
            backend_route="/api/users/create",
        )
        with pytest.raises(MidicoderError):
            ApiSpec(
                name="Test",
                base_url="https://api.example.com",
                bindings=[b1, b2],
            )

    def test_with_bindings_and_bridge(self):
        binding = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.GET,
            backend_route="/api/users",
        )
        bridge = RealtimeBridgeSpec(
            name="Updates",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost/ws",
        )
        spec = ApiSpec(
            name="Test",
            base_url="https://api.example.com",
            bindings=[binding],
            bridge=bridge,
        )
        assert len(spec.bindings) == 1
        assert spec.bridge is not None

    def test_to_dict(self):
        spec = ApiSpec(
            name="Test",
            base_url="https://api.example.com",
            auth_mode=AuthMode.BEARER,
            timeout=15000,
        )
        d = spec.to_dict()
        assert d["name"] == "Test"
        assert d["base_url"] == "https://api.example.com"
        assert d["auth_mode"] == "bearer"
        assert d["timeout"] == 15000

    def test_from_dict(self):
        d = {
            "name": "Test",
            "base_url": "https://api.example.com",
            "auth_mode": "bearer",
            "timeout": 10000,
            "retry_count": 5,
        }
        spec = ApiSpec.from_dict(d)
        assert spec.name == "Test"
        assert spec.auth_mode == AuthMode.BEARER
        assert spec.retry_count == 5

    def test_from_dict_with_bindings(self):
        d = {
            "name": "Test",
            "base_url": "https://api.example.com",
            "bindings": [
                {
                    "client_method": "getUsers",
                    "http_method": "GET",
                    "backend_route": "/api/users",
                }
            ],
        }
        spec = ApiSpec.from_dict(d)
        assert len(spec.bindings) == 1
        assert spec.bindings[0].client_method == "getUsers"

    def test_from_openapi(self):
        openapi = {
            "info": {"title": "MyAPI"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {"operationId": "listUsers"},
                    "post": {"operationId": "createUser"},
                }
            },
        }
        spec = ApiSpec.from_openapi(openapi)
        assert spec.name == "MyAPI"
        assert spec.base_url == "https://api.example.com"
        assert len(spec.bindings) == 2

    def test_from_openapi_default_server(self):
        openapi = {
            "info": {"title": "LocalAPI"},
            "paths": {},
        }
        spec = ApiSpec.from_openapi(openapi)
        assert spec.base_url == "http://localhost"
        assert len(spec.bindings) == 0
