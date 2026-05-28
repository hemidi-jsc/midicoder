"""
Tests cho CP03 NestJS Auth Emitter.

Unit tests cho:
- NestJSEmitter emit code
- GeneratedFile output
- emit_nestjs_auth utility function

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from midicoder.packs.cp_full_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    Permission,
)
from midicoder.packs.cp_full_auth.nestjs import (
    NestJSEmitter,
    GeneratedFile,
    emit_nestjs_auth,
)


class TestNestJSEmitter:
    """Tests cho NestJSEmitter."""

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
            permissions=[
                Permission(id="user:create"),
                Permission(id="order:*"),
            ],
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

    def test_emitter_requires_stack_dir(self):
        with pytest.raises(FileNotFoundError):
            NestJSEmitter(Path("/nonexistent/path"))

    def test_emit_generates_files(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert len(files) >= 4
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_auth_directory(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        emitter.emit(auth_ir, output_dir)
        assert (output_dir / "src" / "auth").is_dir()

    def test_emit_auth_module(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        module_files = [f for f in files if f.path.name == "auth.module.ts"]
        assert len(module_files) == 1
        assert "AuthModule" in module_files[0].content

    def test_emit_jwt_guard(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        guard_files = [f for f in files if f.path.name == "jwt-auth.guard.ts"]
        assert len(guard_files) == 1
        assert "JwtAuthGuard" in guard_files[0].content
        assert "canActivate" in guard_files[0].content

    def test_emit_auth_service(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        service_files = [f for f in files if f.path.name == "auth.service.ts"]
        assert len(service_files) == 1
        assert "AuthService" in service_files[0].content
        assert "createAccessToken" in service_files[0].content

    def test_emit_permissions_decorator(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        perm_files = [f for f in files if f.path.name == "permissions.decorator.ts"]
        assert len(perm_files) == 1
        assert "Permissions" in perm_files[0].content
        assert "permissionMatches" in perm_files[0].content

    def test_emit_index_file(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        index_files = [f for f in files if f.path.name == "index.ts"]
        assert len(index_files) == 1

    def test_emit_has_correct_capability(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        emitter = NestJSEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert all(f.capability == "CP03" for f in files)

    def test_emit_nestjs_auth_utility(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        files = emit_nestjs_auth(auth_ir, stack_dir, output_dir)
        assert len(files) >= 4
        assert all(isinstance(f, GeneratedFile) for f in files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])