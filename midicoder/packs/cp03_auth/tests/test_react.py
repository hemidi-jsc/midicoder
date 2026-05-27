"""
Tests cho CP03 React Auth Emitter.

Unit tests cho:
- ReactEmitter emit code
- GeneratedFile output
- emit_react_auth utility function

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from midicoder.packs.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    Permission,
)
from midicoder.packs.cp03_auth.react import (
    ReactEmitter,
    GeneratedFile,
    emit_react_auth,
)


class TestReactEmitter:
    """Tests cho ReactEmitter."""

    @pytest.fixture
    def auth_ir(self) -> AuthIR:
        return AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(expire_minutes=30, algorithm="HS256"),
                ),
            ],
            permissions=[Permission(id="user:create")],
        )

    @pytest.fixture
    def stack_dir(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "auth").mkdir()
        return tmp

    @pytest.fixture
    def output_dir(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_emit_generates_files(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_auth_directory(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        emitter.emit(auth_ir, output_dir)
        assert (output_dir / "src" / "auth").is_dir()

    def test_emit_auth_context(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        ctx = [f for f in files if f.path.name == "AuthContext.tsx"]
        assert len(ctx) == 1
        assert "AuthProvider" in ctx[0].content
        assert "useAuthContext" in ctx[0].content

    def test_emit_use_auth_hook(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        hook = [f for f in files if f.path.name == "useAuth.ts"]
        assert len(hook) == 1

    def test_emit_protected_route(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        route = [f for f in files if f.path.name == "ProtectedRoute.tsx"]
        assert len(route) == 1
        assert "ProtectedRoute" in route[0].content

    def test_emit_api_client(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        client = [f for f in files if f.path.name == "api-client.ts"]
        assert len(client) == 1

    def test_emit_has_correct_capability(self, auth_ir, stack_dir, output_dir):
        emitter = ReactEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert all(f.capability == "CP03" for f in files)

    def test_emit_react_auth_utility(self, auth_ir, stack_dir, output_dir):
        files = emit_react_auth(auth_ir, stack_dir, output_dir)
        assert len(files) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])