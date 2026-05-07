"""
Tests cho CP03 Angular Auth Emitter.

Unit tests cho:
- AngularEmitter emit code
- GeneratedFile output
- emit_angular_auth utility function

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from midicoder.emitters.core.auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    Permission,
)
from midicoder.emitters.core.auth.angular import (
    AngularEmitter,
    GeneratedFile,
    emit_angular_auth,
)


class TestAngularEmitter:
    """Tests cho AngularEmitter."""

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
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_auth_directory(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        emitter.emit(auth_ir, output_dir)
        assert (output_dir / "src" / "app" / "core" / "auth").is_dir()

    def test_emit_auth_service(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        svc = [f for f in files if f.path.name == "auth.service.ts"]
        assert len(svc) == 1
        assert "AuthService" in svc[0].content

    def test_emit_auth_guard(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        guard = [f for f in files if f.path.name == "auth.guard.ts"]
        assert len(guard) == 1
        assert "AuthGuard" in guard[0].content

    def test_emit_jwt_interceptor(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        interceptor = [f for f in files if f.path.name == "jwt.interceptor.ts"]
        assert len(interceptor) == 1
        assert "JwtInterceptor" in interceptor[0].content

    def test_emit_auth_module(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        mod = [f for f in files if f.path.name == "auth.module.ts"]
        assert len(mod) == 1
        assert "AuthModule" in mod[0].content

    def test_emit_has_correct_capability(self, auth_ir, stack_dir, output_dir):
        emitter = AngularEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert all(f.capability == "CP03" for f in files)

    def test_emit_angular_auth_utility(self, auth_ir, stack_dir, output_dir):
        files = emit_angular_auth(auth_ir, stack_dir, output_dir)
        assert len(files) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])