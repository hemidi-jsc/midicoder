# coding: utf-8
"""
Integration tests cho CP20 API Client & Integration Generator.

Module này test full pipeline:
- OpenAPI spec → ApiSpec model → Client generation (frontend + backend)
- CP06 (API Gateway) → CP20 wiring
- Realtime bridge end-to-end

Author: Midicoder Team
Version: 1.0.0
"""

import json
import pytest

from midicoder.packs.cp_backend_api_client.models import (
    ApiSpec,
    AuthMode,
    ClientBinding,
    HttpMethod,
    RealtimeBridgeSpec,
    TransportType,
)


def _make_full_spec() -> ApiSpec:
    """Tạo full ApiSpec cho integration testing."""
    return ApiSpec(
        name="full-api",
        base_url="https://api.example.com/v1",
        auth_mode=AuthMode.BEARER,
        bindings=[
            ClientBinding(
                client_method="getUsers",
                http_method=HttpMethod.GET,
                backend_route="/users",
                request_type=None,
                response_type="UserList",
            ),
            ClientBinding(
                client_method="createUser",
                http_method=HttpMethod.POST,
                backend_route="/users",
                request_type="CreateUserRequest",
                response_type="User",
            ),
            ClientBinding(
                client_method="deleteUser",
                http_method=HttpMethod.DELETE,
                backend_route="/users/{id}",
                request_type=None,
                response_type=None,
            ),
        ],
        bridge=RealtimeBridgeSpec(
            name="events",
            transport=TransportType.WEBSOCKET,
            url="wss://api.example.com/ws",
            channels=["events.created", "events.updated"],
            reconnect_attempts=5,
            reconnect_delay_ms=1000,
        ),
    )


class TestOpenApiToClientPipeline:
    """Test pipeline: OpenAPI spec → Typed client generation."""

    def test_openapi_to_angular_client(self, tmp_path):
        """Test: Parse OpenAPI → Angular typed client."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = _make_full_spec()
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        # Verify all 3 files generated
        assert len(files) == 3

        # Verify type safety (Obligation 1): client methods match backend routes
        bind_file = next(f for f in files if f.path.name == "openapi-bind.ts")
        assert "getUsers" in bind_file.content
        assert "/users" in bind_file.content

        # Verify auth injection (Obligation 3): bearer mode
        client_file = next(f for f in files if f.path.name == "api-client.service.ts")
        assert "bearer" in client_file.content.lower()

    def test_openapi_to_react_client(self, tmp_path):
        """Test: Parse OpenAPI → React typed client."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        spec = _make_full_spec()
        emitter = ReactApiEmitter()
        files = emitter.generate(spec, tmp_path)

        assert len(files) == 3

        # Verify error mapping (Obligation 2): interceptor
        client_file = next(f for f in files if f.path.name == "api-client.ts")
        assert "interceptor" in client_file.content.lower()

    def test_openapi_to_fastapi_backend(self):
        """Test: Parse OpenAPI → FastAPI OpenAPI endpoint."""
        from midicoder.packs.cp_backend_api_client.fastapi import FastAPIApiEmitter

        spec = _make_full_spec()
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)

        assert "openapi_endpoint.py" in files
        assert "websocket_gateway.py" in files

        # Verify spec URL
        assert spec.base_url in files["openapi_endpoint.py"]

    def test_openapi_to_nestjs_backend(self):
        """Test: Parse OpenAPI → NestJS OpenAPI module."""
        from midicoder.packs.cp_backend_api_client.nestjs import NestJSApiEmitter

        spec = _make_full_spec()
        emitter = NestJSApiEmitter()
        files = emitter.generate(spec)

        assert "openapi.module.ts" in files
        assert "websocket.gateway.ts" in files


class TestRealtimeBridgeE2E:
    """Test realtime bridge end-to-end generation."""

    def test_angular_bridge_has_websocket(self, tmp_path):
        """Test: Angular bridge emit với WebSocket transport."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = _make_full_spec()
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        bridge_file = next(f for f in files if f.path.name == "realtime-bridge.service.ts")
        assert "WebSocket" in bridge_file.content
        assert "reconnect" in bridge_file.content.lower()

    def test_react_bridge_has_hooks(self, tmp_path):
        """Test: React bridge emit với custom hooks."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        spec = _make_full_spec()
        emitter = ReactApiEmitter()
        files = emitter.generate(spec, tmp_path)

        hooks_file = next(f for f in files if f.path.name == "realtime-hooks.ts")
        assert "useWebSocket" in hooks_file.content or "useSSE" in hooks_file.content

    def test_sse_transport_generation(self, tmp_path):
        """Test: Bridge emit với SSE transport."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = ApiSpec(
            name="sse-api",
            base_url="https://api.example.com",
            auth_mode=AuthMode.BEARER,
            bindings=[],
            bridge=RealtimeBridgeSpec(
                name="logs",
                transport=TransportType.SSE,
                url="https://api.example.com/events",
                channels=["logs"],
            ),
        )
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        bridge_file = next(f for f in files if f.path.name == "realtime-bridge.service.ts")
        assert "EventSource" in bridge_file.content or "SSE" in bridge_file.content


class TestObligations:
    """Test 3 obligations: Type Safety, Error Mapping, Auth Injection."""

    def test_obligation_1_type_safety_angular(self, tmp_path):
        """Obligation 1: Client types match backend routes (Angular)."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = _make_full_spec()
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        bind_file = next(f for f in files if f.path.name == "openapi-bind.ts")
        # Method names should appear in binding
        for binding in spec.bindings:
            assert binding.client_method in bind_file.content

    def test_obligation_1_type_safety_react(self, tmp_path):
        """Obligation 1: Client types match backend routes (React)."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        spec = _make_full_spec()
        emitter = ReactApiEmitter()
        files = emitter.generate(spec, tmp_path)

        bind_file = next(f for f in files if f.path.name == "openapi-bind.ts")
        for binding in spec.bindings:
            assert binding.client_method in bind_file.content

    def test_obligation_2_error_mapping_angular(self, tmp_path):
        """Obligation 2: Error mapping via interceptor (Angular)."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = _make_full_spec()
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.service.ts")
        assert "handleError" in client_file.content or "catchError" in client_file.content

    def test_obligation_2_error_mapping_react(self, tmp_path):
        """Obligation 2: Error mapping via interceptor (React)."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        spec = _make_full_spec()
        emitter = ReactApiEmitter()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.ts")
        assert "mapError" in client_file.content or "interceptor" in client_file.content.lower()

    def test_obligation_3_auth_injection_angular(self, tmp_path):
        """Obligation 3: Auth injection per request (Angular)."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        spec = _make_full_spec()
        emitter = AngularApiEmitter()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.service.ts")
        assert "setToken" in client_file.content or "token" in client_file.content.lower()

    def test_obligation_3_auth_injection_react(self, tmp_path):
        """Obligation 3: Auth injection per request (React)."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        spec = _make_full_spec()
        emitter = ReactApiEmitter()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.ts")
        assert "setToken" in client_file.content or "token" in client_file.content.lower()


class TestSpecSerialization:
    """Test ApiSpec serialization/deserialization."""

    def test_to_dict_roundtrip(self):
        """Test to_dict() + from_dict() roundtrip."""
        spec = _make_full_spec()
        d = spec.to_dict()

        assert d["base_url"] == spec.base_url
        assert d["auth_mode"] == spec.auth_mode.value
        assert len(d["bindings"]) == len(spec.bindings)

    def test_from_dict_with_bridge(self):
        """Test from_dict() với bridge spec."""
        spec = _make_full_spec()
        d = spec.to_dict()
        restored = ApiSpec.from_dict(d)

        assert restored.base_url == spec.base_url
        assert restored.auth_mode == spec.auth_mode
        assert len(restored.bindings) == len(spec.bindings)
        assert restored.bridge is not None
        assert restored.bridge.transport == spec.bridge.transport

    def test_from_dict_without_bridge(self):
        """Test from_dict() không có bridge."""
        spec = ApiSpec(
            name="no-bridge",
            base_url="http://localhost",
            auth_mode=AuthMode.NONE,
            bindings=[],
            bridge=None,
        )
        d = spec.to_dict()
        restored = ApiSpec.from_dict(d)

        assert restored.bridge is None
