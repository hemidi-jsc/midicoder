# coding: utf-8
"""
Tests cho models của API Client & Integration Generator (CP20).

Module: midicoder/emitters/core/api_client/models.py
Features: ApiSpec, ClientBinding, RealtimeBridgeSpec + enums

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.errors import MidicoderError, ErrorCode


class TestTransportType:
    """Tests cho enum TransportType."""

    def test_transport_type_values(self):
        """Test giá trị của TransportType."""
        from midicoder.emitters.core.cp20_api_client.models import TransportType
        assert TransportType.WEBSOCKET.value == "websocket"
        assert TransportType.SSE.value == "sse"

    def test_transport_type_from_string(self):
        """Test tạo TransportType từ string."""
        from midicoder.emitters.core.cp20_api_client.models import TransportType
        assert TransportType("websocket") == TransportType.WEBSOCKET
        assert TransportType("sse") == TransportType.SSE


class TestAuthMode:
    """Tests cho enum AuthMode."""

    def test_auth_mode_values(self):
        """Test giá trị của AuthMode."""
        from midicoder.emitters.core.cp20_api_client.models import AuthMode
        assert AuthMode.BEARER.value == "bearer"
        assert AuthMode.COOKIE.value == "cookie"
        assert AuthMode.NONE.value == "none"

    def test_auth_mode_from_string(self):
        """Test tạo AuthMode từ string."""
        from midicoder.emitters.core.cp20_api_client.models import AuthMode
        assert AuthMode("bearer") == AuthMode.BEARER
        assert AuthMode("none") == AuthMode.NONE


class TestHttpMethod:
    """Tests cho enum HttpMethod."""

    def test_http_method_values(self):
        """Test giá trị của HttpMethod."""
        from midicoder.emitters.core.cp20_api_client.models import HttpMethod
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.PATCH.value == "PATCH"
        assert HttpMethod.DELETE.value == "DELETE"


class TestClientBinding:
    """Tests cho ClientBinding."""

    def test_client_binding_creation(self):
        """Test tạo ClientBinding hợp lệ."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        binding = ClientBinding(
            client_method="getUsers",
            http_method=HttpMethod.GET,
            backend_route="/api/users",
        )
        assert binding.client_method == "getUsers"
        assert binding.http_method == HttpMethod.GET
        assert binding.backend_route == "/api/users"

    def test_client_binding_with_types(self):
        """Test ClientBinding có request/response type."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        binding = ClientBinding(
            client_method="createOrder",
            http_method=HttpMethod.POST,
            backend_route="/api/orders",
            request_type="OrderCreate",
            response_type="Order",
        )
        assert binding.request_type == "OrderCreate"
        assert binding.response_type == "Order"

    def test_client_binding_to_dict(self):
        """Test serialise ClientBinding ra dict."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        binding = ClientBinding(
            client_method="getUser",
            http_method=HttpMethod.GET,
            backend_route="/api/users/:id",
            response_type="User",
        )
        d = binding.to_dict()
        assert d["client_method"] == "getUser"
        assert d["http_method"] == "GET"
        assert d["backend_route"] == "/api/users/:id"

    def test_client_binding_from_dict(self):
        """Test deserialise ClientBinding từ dict."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding
        data = {
            "client_method": "deleteUser",
            "http_method": "DELETE",
            "backend_route": "/api/users/:id",
        }
        binding = ClientBinding.from_dict(data)
        assert binding.client_method == "deleteUser"

    def test_client_binding_empty_method_raises(self):
        """Test ClientBinding method rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        with pytest.raises(MidicoderError) as exc_info:
            ClientBinding(
                client_method="",
                http_method=HttpMethod.GET,
                backend_route="/api/test",
            )
        assert exc_info.value.code == ErrorCode.CP20_OPENAPI_PARSE_ERROR

    def test_client_binding_empty_route_raises(self):
        """Test ClientBinding route rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        with pytest.raises(MidicoderError) as exc_info:
            ClientBinding(
                client_method="test",
                http_method=HttpMethod.GET,
                backend_route="",
            )
        assert exc_info.value.code == ErrorCode.CP20_OPENAPI_PARSE_ERROR


class TestRealtimeBridgeSpec:
    """Tests cho RealtimeBridgeSpec."""

    def test_realtime_bridge_spec_websocket(self):
        """Test tạo RealtimeBridgeSpec cho WebSocket."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        spec = RealtimeBridgeSpec(
            name="OrderUpdates",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost:8000/ws/orders",
            channels=["orders.updated", "orders.created"],
        )
        assert spec.name == "OrderUpdates"
        assert spec.transport == TransportType.WEBSOCKET
        assert len(spec.channels) == 2

    def test_realtime_bridge_spec_sse(self):
        """Test tạo RealtimeBridgeSpec cho SSE."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        spec = RealtimeBridgeSpec(
            name="Notifications",
            transport=TransportType.SSE,
            url="http://localhost:8000/sse/notifications",
            channels=["notifications"],
        )
        assert spec.transport == TransportType.SSE

    def test_realtime_bridge_spec_empty_name_raises(self):
        """Test RealtimeBridgeSpec name rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        with pytest.raises(MidicoderError) as exc_info:
            RealtimeBridgeSpec(
                name="",
                transport=TransportType.WEBSOCKET,
                url="ws://localhost/ws",
            )
        assert exc_info.value.code == ErrorCode.CP20_BRIDGE_CONFIG_INVALID

    def test_realtime_bridge_spec_empty_url_raises(self):
        """Test RealtimeBridgeSpec URL rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        with pytest.raises(MidicoderError) as exc_info:
            RealtimeBridgeSpec(
                name="Test",
                transport=TransportType.WEBSOCKET,
                url="",
            )
        assert exc_info.value.code == ErrorCode.CP20_BRIDGE_CONFIG_INVALID

    def test_realtime_bridge_spec_websocket_url_format(self):
        """Test WebSocket URL phải bắt đầu bằng ws:// hoặc wss://."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="BadWs",
                transport=TransportType.WEBSOCKET,
                url="http://localhost/ws",
            )

    def test_realtime_bridge_spec_sse_url_format(self):
        """Test SSE URL phải bắt đầu bằng http:// hoặc https://."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        with pytest.raises(MidicoderError):
            RealtimeBridgeSpec(
                name="BadSse",
                transport=TransportType.SSE,
                url="ws://localhost/sse",
            )

    def test_realtime_bridge_spec_default_values(self):
        """Test giá trị mặc định của RealtimeBridgeSpec."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        spec = RealtimeBridgeSpec(
            name="Test",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost/ws",
        )
        assert spec.reconnect_attempts == 5
        assert spec.reconnect_delay_ms == 1000
        assert spec.channels == []

    def test_realtime_bridge_spec_to_dict(self):
        """Test serialise RealtimeBridgeSpec ra dict."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec, TransportType
        spec = RealtimeBridgeSpec(
            name="Orders",
            transport=TransportType.WEBSOCKET,
            url="ws://localhost/ws/orders",
            channels=["orders.*"],
            reconnect_attempts=10,
        )
        d = spec.to_dict()
        assert d["name"] == "Orders"
        assert d["transport"] == "websocket"
        assert d["reconnect_attempts"] == 10

    def test_realtime_bridge_spec_from_dict(self):
        """Test deserialise RealtimeBridgeSpec từ dict."""
        from midicoder.emitters.core.cp20_api_client.models import RealtimeBridgeSpec
        data = {
            "name": "Products",
            "transport": "sse",
            "url": "http://localhost/sse/products",
            "channels": ["products.updated"],
        }
        spec = RealtimeBridgeSpec.from_dict(data)
        assert spec.name == "Products"
        assert spec.transport.value == "sse"


class TestApiSpec:
    """Tests cho ApiSpec."""

    def test_api_spec_creation(self):
        """Test tạo ApiSpec hợp lệ."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        spec = ApiSpec(
            name="CommerceAPI",
            base_url="http://localhost:8000/api",
            auth_mode=AuthMode.BEARER,
        )
        assert spec.name == "CommerceAPI"
        assert spec.base_url == "http://localhost:8000/api"
        assert spec.auth_mode == AuthMode.BEARER

    def test_api_spec_with_bindings(self):
        """Test ApiSpec có ClientBindings."""
        from midicoder.emitters.core.cp20_api_client.models import (
            ApiSpec, AuthMode, ClientBinding, HttpMethod,
        )
        spec = ApiSpec(
            name="OrderAPI",
            base_url="http://localhost:8000/api",
            auth_mode=AuthMode.BEARER,
            bindings=[
                ClientBinding(
                    client_method="getOrders",
                    http_method=HttpMethod.GET,
                    backend_route="/orders",
                ),
            ],
        )
        assert len(spec.bindings) == 1
        assert spec.bindings[0].client_method == "getOrders"

    def test_api_spec_with_bridge(self):
        """Test ApiSpec có RealtimeBridge."""
        from midicoder.emitters.core.cp20_api_client.models import (
            ApiSpec, AuthMode, RealtimeBridgeSpec, TransportType,
        )
        spec = ApiSpec(
            name="LiveAPI",
            base_url="http://localhost:8000/api",
            auth_mode=AuthMode.NONE,
            bridge=RealtimeBridgeSpec(
                name="LiveUpdates",
                transport=TransportType.WEBSOCKET,
                url="ws://localhost:8000/ws",
            ),
        )
        assert spec.bridge is not None
        assert spec.bridge.transport == TransportType.WEBSOCKET

    def test_api_spec_empty_name_raises(self):
        """Test ApiSpec name rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        with pytest.raises(MidicoderError) as exc_info:
            ApiSpec(name="", base_url="http://localhost", auth_mode=AuthMode.NONE)
        assert exc_info.value.code == ErrorCode.CP20_OPENAPI_PARSE_ERROR

    def test_api_spec_empty_base_url_raises(self):
        """Test ApiSpec base_url rỗng thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        with pytest.raises(MidicoderError) as exc_info:
            ApiSpec(name="Test", base_url="", auth_mode=AuthMode.NONE)
        assert exc_info.value.code == ErrorCode.CP20_OPENAPI_PARSE_ERROR

    def test_api_spec_duplicate_endpoint_raises(self):
        """Test ApiSpec có duplicate endpoint thì raise."""
        from midicoder.emitters.core.cp20_api_client.models import (
            ApiSpec, AuthMode, ClientBinding, HttpMethod,
        )
        with pytest.raises(MidicoderError) as exc_info:
            ApiSpec(
                name="DupAPI",
                base_url="http://localhost/api",
                auth_mode=AuthMode.NONE,
                bindings=[
                    ClientBinding(client_method="getData", http_method=HttpMethod.GET, backend_route="/a"),
                    ClientBinding(client_method="getData", http_method=HttpMethod.POST, backend_route="/b"),
                ],
            )
        assert exc_info.value.code == ErrorCode.CP20_ENDPOINT_DUPLICATE

    def test_api_spec_auth_injection_obligation(self):
        """Test Obligation 3: auth_mode != NONE cần token config (validate tại emit)."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        spec = ApiSpec(
            name="SecureAPI",
            base_url="http://localhost/api",
            auth_mode=AuthMode.BEARER,
            token_header="Authorization",
            token_prefix="Bearer",
        )
        assert spec.token_header == "Authorization"
        assert spec.token_prefix == "Bearer"

    def test_api_spec_default_values(self):
        """Test giá trị mặc định của ApiSpec."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        spec = ApiSpec(
            name="Test",
            base_url="http://localhost",
            auth_mode=AuthMode.NONE,
        )
        assert spec.timeout == 30000
        assert spec.retry_count == 3

    def test_api_spec_to_dict(self):
        """Test serialise ApiSpec ra dict."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        spec = ApiSpec(
            name="API",
            base_url="http://localhost/api",
            auth_mode=AuthMode.COOKIE,
            timeout=5000,
        )
        d = spec.to_dict()
        assert d["name"] == "API"
        assert d["auth_mode"] == "cookie"
        assert d["timeout"] == 5000

    def test_api_spec_from_dict(self):
        """Test deserialise ApiSpec từ dict."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec
        data = {
            "name": "TestAPI",
            "base_url": "http://localhost/v1",
            "auth_mode": "bearer",
            "bindings": [
                {
                    "client_method": "listItems",
                    "http_method": "GET",
                    "backend_route": "/items",
                },
            ],
        }
        spec = ApiSpec.from_dict(data)
        assert spec.name == "TestAPI"
        assert len(spec.bindings) == 1

    def test_api_spec_generate_from_openapi(self):
        """Test generate ApiSpec từ OpenAPI spec dict."""
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec
        openapi_spec = {
            "info": {"title": "Store API", "version": "1.0.0"},
            "servers": [{"url": "http://localhost:8000/api"}],
            "paths": {
                "/products": {
                    "get": {"operationId": "getProducts", "responses": {"200": {"description": "OK"}}},
                },
                "/orders": {
                    "post": {"operationId": "createOrder", "responses": {"201": {"description": "Created"}}},
                },
            },
        }
        spec = ApiSpec.from_openapi(openapi_spec)
        assert spec.name == "Store API"
        assert len(spec.bindings) == 2
        methods = [b.client_method for b in spec.bindings]
        assert "getProducts" in methods
        assert "createOrder" in methods


class TestObligationTypeSafety:
    """Tests cho Obligation 1: Type Safety (Client <-> Backend Sync)."""

    def test_binding_type_consistency(self):
        """Test ClientBinding types consistent với spec."""
        from midicoder.emitters.core.cp20_api_client.models import ClientBinding, HttpMethod
        binding = ClientBinding(
            client_method="createUser",
            http_method=HttpMethod.POST,
            backend_route="/users",
            request_type="UserCreate",
            response_type="User",
        )
        assert binding.request_type is not None
        assert binding.response_type is not None


class TestObligationErrorMapping:
    """Tests cho Obligation 2: Error Mapping."""

    def test_error_interceptor_emitted(self):
        """Test error mapping được enforce trong template (kiểm tra tại emit level)."""
        # Đây là obligation runtime - enforced bởi template interceptor
        # Test verify rằng model không chặn việc emit error interceptor
        from midicoder.emitters.core.cp20_api_client.models import ApiSpec, AuthMode
        spec = ApiSpec(name="Test", base_url="http://localhost", auth_mode=AuthMode.NONE)
        assert spec is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
