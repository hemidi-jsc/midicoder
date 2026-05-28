# coding: utf-8
"""
Tests cho CP20 API Client Emitters.

Module này test 4 emitter classes:
- AngularApiEmitter: FileSystemLoader pattern, emit 3 Angular templates
- ReactApiEmitter: FileSystemLoader pattern, emit 3 React templates
- FastAPIApiEmitter: @dataclass inline, emit 2 FastAPI files
- NestJSApiEmitter: @dataclass inline, emit 2 NestJS files

Author: Midicoder Team
Version: 1.0.0
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


def _make_sample_spec() -> ApiSpec:
    """Tạo sample ApiSpec cho testing."""
    return ApiSpec(
        name="test-api",
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
        ],
        bridge=RealtimeBridgeSpec(
            name="notifications",
            transport=TransportType.WEBSOCKET,
            url="wss://api.example.com/ws",
            channels=["notifications", "orders.updated"],
            reconnect_attempts=5,
            reconnect_delay_ms=1000,
        ),
    )


def _make_spec_no_bridge() -> ApiSpec:
    """Tạo ApiSpec không có realtime bridge."""
    return ApiSpec(
        name="test-no-bridge",
        base_url="https://api.example.com/v1",
        auth_mode=AuthMode.COOKIE,
        bindings=[
            ClientBinding(
                client_method="getHealth",
                http_method=HttpMethod.GET,
                backend_route="/health",
                request_type=None,
                response_type="HealthStatus",
            ),
        ],
        bridge=None,
    )


class TestAngularApiEmitter:
    """Tests cho AngularApiEmitter."""

    def test_emit_basic_spec(self, tmp_path):
        """Test emit Angular client từ spec cơ bản."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        emitter = AngularApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        assert len(files) == 3  # api-client, realtime-bridge, openapi-bind
        paths = [f.path.name for f in files]
        assert "api-client.service.ts" in paths
        assert "realtime-bridge.service.ts" in paths
        assert "openapi-bind.ts" in paths

    def test_emit_no_bridge(self, tmp_path):
        """Test emit Angular client không có bridge."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        emitter = AngularApiEmitter()
        spec = _make_spec_no_bridge()
        files = emitter.generate(spec, tmp_path)

        # Chỉ có api-client + openapi-bind (không có realtime-bridge)
        assert len(files) == 2
        paths = [f.path.name for f in files]
        assert "api-client.service.ts" in paths
        assert "realtime-bridge.service.ts" not in paths
        assert "openapi-bind.ts" in paths

    def test_emit_content_has_auth_mode(self, tmp_path):
        """Test content có chứa auth mode đúng."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        emitter = AngularApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.service.ts")
        assert "bearer" in client_file.content.lower()

    def test_emit_openapi_bind_has_endpoints(self, tmp_path):
        """Test openapi-bind.ts có chứa endpoint mappings."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        emitter = AngularApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        bind_file = next(f for f in files if f.path.name == "openapi-bind.ts")
        assert "getUsers" in bind_file.content
        assert "createUser" in bind_file.content

    def test_emit_files_written_to_disk(self, tmp_path):
        """Test files được write ra disk."""
        from midicoder.packs.cp_backend_api_client.angular import AngularApiEmitter

        emitter = AngularApiEmitter()
        spec = _make_sample_spec()
        emitter.generate(spec, tmp_path)

        assert (tmp_path / "api-client.service.ts").exists()
        assert (tmp_path / "openapi-bind.ts").exists()


class TestReactApiEmitter:
    """Tests cho ReactApiEmitter."""

    def test_emit_basic_spec(self, tmp_path):
        """Test emit React client từ spec cơ bản."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        emitter = ReactApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        assert len(files) == 3  # api-client, realtime-hooks, openapi-bind
        paths = [f.path.name for f in files]
        assert "api-client.ts" in paths
        assert "realtime-hooks.ts" in paths
        assert "openapi-bind.ts" in paths

    def test_emit_no_bridge(self, tmp_path):
        """Test emit React client không có bridge."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        emitter = ReactApiEmitter()
        spec = _make_spec_no_bridge()
        files = emitter.generate(spec, tmp_path)

        assert len(files) == 2
        paths = [f.path.name for f in files]
        assert "api-client.ts" in paths
        assert "realtime-hooks.ts" not in paths

    def test_emit_content_has_axios(self, tmp_path):
        """Test content có chứa axios import."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        emitter = ReactApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        client_file = next(f for f in files if f.path.name == "api-client.ts")
        assert "axios" in client_file.content.lower()

    def test_emit_hooks_has_websocket(self, tmp_path):
        """Test realtime-hooks.ts có chứa WebSocket hook."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        emitter = ReactApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec, tmp_path)

        hooks_file = next(f for f in files if f.path.name == "realtime-hooks.ts")
        assert "useWebSocket" in hooks_file.content or "useSSE" in hooks_file.content

    def test_emit_files_written_to_disk(self, tmp_path):
        """Test files được write ra disk."""
        from midicoder.packs.cp_backend_api_client.react import ReactApiEmitter

        emitter = ReactApiEmitter()
        spec = _make_sample_spec()
        emitter.generate(spec, tmp_path)

        assert (tmp_path / "api-client.ts").exists()
        assert (tmp_path / "openapi-bind.ts").exists()


class TestFastAPIApiEmitter:
    """Tests cho FastAPIApiEmitter."""

    def test_emit_basic_spec(self):
        """Test emit FastAPI files từ spec cơ bản."""
        from midicoder.packs.cp_backend_api_client.fastapi import FastAPIApiEmitter

        emitter = FastAPIApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        assert "openapi_endpoint.py" in files
        assert "websocket_gateway.py" in files

    def test_emit_openapi_has_base_url(self):
        """Test openapi_endpoint.py có chứa base_url."""
        from midicoder.packs.cp_backend_api_client.fastapi import FastAPIApiEmitter

        emitter = FastAPIApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        content = files["openapi_endpoint.py"]
        assert "https://api.example.com/v1" in content

    def test_emit_websocket_has_manager(self):
        """Test websocket_gateway.py có chứa ConnectionManager."""
        from midicoder.packs.cp_backend_api_client.fastapi import FastAPIApiEmitter

        emitter = FastAPIApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        content = files["websocket_gateway.py"]
        assert "ConnectionManager" in content
        assert "subscribe" in content

    def test_emit_empty_spec(self):
        """Test emit với spec tối thiểu."""
        from midicoder.packs.cp_backend_api_client.fastapi import FastAPIApiEmitter

        emitter = FastAPIApiEmitter()
        spec = ApiSpec(
            name="minimal",
            base_url="http://localhost:8000",
            auth_mode=AuthMode.NONE,
            bindings=[],
            bridge=None,
        )
        files = emitter.generate(spec)

        assert len(files) == 2
        assert "openapi_endpoint.py" in files


class TestNestJSApiEmitter:
    """Tests cho NestJSApiEmitter."""

    def test_emit_basic_spec(self):
        """Test emit NestJS files từ spec cơ bản."""
        from midicoder.packs.cp_backend_api_client.nestjs import NestJSApiEmitter

        emitter = NestJSApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        assert "openapi.module.ts" in files
        assert "websocket.gateway.ts" in files

    def test_emit_openapi_has_module(self):
        """Test openapi.module.ts có chứa NestJS module."""
        from midicoder.packs.cp_backend_api_client.nestjs import NestJSApiEmitter

        emitter = NestJSApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        content = files["openapi.module.ts"]
        assert "@Module" in content
        assert "OpenApiModule" in content

    def test_emit_websocket_has_gateway(self):
        """Test websocket.gateway.ts có chứa WebSocketGateway."""
        from midicoder.packs.cp_backend_api_client.nestjs import NestJSApiEmitter

        emitter = NestJSApiEmitter()
        spec = _make_sample_spec()
        files = emitter.generate(spec)

        content = files["websocket.gateway.ts"]
        assert "@WebSocketGateway" in content
        assert "SubscribeMessage" in content

    def test_emit_empty_spec(self):
        """Test emit với spec tối thiểu."""
        from midicoder.packs.cp_backend_api_client.nestjs import NestJSApiEmitter

        emitter = NestJSApiEmitter()
        spec = ApiSpec(
            name="minimal",
            base_url="http://localhost:3000",
            auth_mode=AuthMode.NONE,
            bindings=[],
            bridge=None,
        )
        files = emitter.generate(spec)

        assert len(files) == 2
        assert "openapi.module.ts" in files
