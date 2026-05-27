"""
Tests cho CP20 API Client FastAPI emitter.
"""

import pytest

from midicoder.packs.cp20_api_client.fastapi import FastAPIApiEmitter
from midicoder.packs.cp20_api_client.models import (
    ApiSpec,
    AuthMode,
    ClientBinding,
    HttpMethod,
    RealtimeBridgeSpec,
    TransportType,
)


class TestFastAPIApiEmitter:
    """Tests cho FastAPIApiEmitter."""

    def test_generate_returns_files(self):
        spec = ApiSpec(name="Test", base_url="https://api.example.com")
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)
        assert "openapi_endpoint.py" in files
        assert "websocket_gateway.py" in files

    def test_openapi_endpoint_contains_base_url(self):
        spec = ApiSpec(name="Test", base_url="https://api.example.com")
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)
        content = files["openapi_endpoint.py"]
        assert "https://api.example.com" in content

    def test_openapi_endpoint_has_router(self):
        spec = ApiSpec(name="Test", base_url="http://localhost")
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)
        content = files["openapi_endpoint.py"]
        assert "APIRouter" in content
        assert "get_openapi_spec" in content

    def test_websocket_gateway_has_manager(self):
        spec = ApiSpec(name="Test", base_url="http://localhost")
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)
        content = files["websocket_gateway.py"]
        assert "ConnectionManager" in content
        assert "broadcast" in content

    def test_generate_with_complex_spec(self):
        spec = ApiSpec(
            name="SecureAPI",
            base_url="https://api.example.com",
            auth_mode=AuthMode.BEARER,
            bindings=[
                ClientBinding(
                    client_method="getUsers",
                    http_method=HttpMethod.GET,
                    backend_route="/api/users",
                )
            ],
            bridge=RealtimeBridgeSpec(
                name="WS",
                transport=TransportType.WEBSOCKET,
                url="ws://localhost/ws",
            ),
        )
        emitter = FastAPIApiEmitter()
        files = emitter.generate(spec)
        assert len(files) == 2
