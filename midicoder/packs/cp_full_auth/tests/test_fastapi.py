"""
Tests cho CP03 FastAPI Auth Emitter.

Unit tests cho:
- FastAPIAuthEmitter emit code
- GeneratedFile output
- emit_fastapi_auth utility function

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
    OAuth2AuthConfig,
    Permission,
    SessionConfig,
)
from midicoder.packs.cp_full_auth.fastapi import (
    FastAPIAuthEmitter,
    GeneratedFile,
    emit_fastapi_auth,
)


# ============================================================================
# Test FastAPIAuthEmitter
# ============================================================================


class TestFastAPIAuthEmitter:
    """Tests cho FastAPIAuthEmitter."""

    @pytest.fixture
    def auth_ir(self) -> AuthIR:
        """AuthIR fixture với JWT provider."""
        return AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(expire_minutes=30, algorithm="HS256"),
                ),
            ],
            session=SessionConfig(cookie_name="session_id", max_age_minutes=480),
            permissions=[
                Permission(id="user:create"),
                Permission(id="user:read"),
                Permission(id="order:*"),
            ],
        )

    @pytest.fixture
    def stack_dir(self) -> Path:
        """Tạo template directory."""
        tmp = Path(tempfile.mkdtemp())
        (tmp / "auth").mkdir()
        return tmp

    @pytest.fixture
    def output_dir(self) -> Path:
        """Tạo output directory."""
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_emitter_requires_stack_dir(self):
        """Test emitter raise khi stack_dir không tồn tại."""
        with pytest.raises(FileNotFoundError):
            FastAPIAuthEmitter(Path("/nonexistent/path"))

    def test_emit_generates_files(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit generate files."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        # Kiểm tra có files được generate
        assert len(files) >= 3  # __init__.py, jwt_auth.py, session.py, permissions.py
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_creates_security_directory(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo core/security directory."""
        emitter = FastAPIAuthEmitter(stack_dir)
        emitter.emit(auth_ir, output_dir)
        assert (output_dir / "core" / "security").is_dir()

    def test_emit_init_file(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo __init__.py."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        init_files = [f for f in files if f.path.name == "__init__.py"]
        assert len(init_files) == 1
        assert "jwt_auth" in init_files[0].content
        assert "session" in init_files[0].content
        assert "permissions" in init_files[0].content

    def test_emit_jwt_auth_file(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo jwt_auth.py."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        jwt_files = [f for f in files if f.path.name == "jwt_auth.py"]
        assert len(jwt_files) == 1
        assert "create_access_token" in jwt_files[0].content
        assert "verify_token" in jwt_files[0].content
        assert "get_current_user" in jwt_files[0].content

    def test_emit_session_file(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo session.py."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        session_files = [f for f in files if f.path.name == "session.py"]
        assert len(session_files) == 1
        assert "SessionManager" in session_files[0].content
        assert "create_session" in session_files[0].content

    def test_emit_permissions_file(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test emit tạo permissions.py."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        perm_files = [f for f in files if f.path.name == "permissions.py"]
        assert len(perm_files) == 1
        assert "require_permission" in perm_files[0].content
        assert "check_permission" in perm_files[0].content

    def test_emit_with_oauth2_only(self, stack_dir: Path, output_dir: Path):
        """Test emit với chỉ OAuth2 provider (không có JWT)."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="google",
                    provider_type=AuthProviderType.OAUTH2,
                    config=OAuth2AuthConfig(
                        authorization_url="https://accounts.google.com/o/oauth2/auth",
                        token_url="https://oauth2.googleapis.com/token",
                    ),
                ),
            ],
        )
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)

        # Vẫn có session.py và permissions.py
        session_files = [f for f in files if f.path.name == "session.py"]
        perm_files = [f for f in files if f.path.name == "permissions.py"]
        assert len(session_files) == 1
        assert len(perm_files) == 1

    def test_emit_has_correct_capability(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test generated files có capability='CP03'."""
        emitter = FastAPIAuthEmitter(stack_dir)
        files = emitter.emit(auth_ir, output_dir)
        assert all(f.capability == "CP03" for f in files)

    def test_emit_fastapi_auth_utility(self, auth_ir: AuthIR, stack_dir: Path, output_dir: Path):
        """Test utility function emit_fastapi_auth."""
        files = emit_fastapi_auth(auth_ir, stack_dir, output_dir)
        assert len(files) >= 3
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_generated_file_dataclass(self, output_dir: Path):
        """Test GeneratedFile dataclass."""
        gf = GeneratedFile(
            path=output_dir / "test.py",
            content="print('hello')",
            template="test.py.jinja2",
            capability="CP03",
        )
        assert gf.path == output_dir / "test.py"
        assert gf.content == "print('hello')"
        assert gf.template == "test.py.jinja2"
        assert gf.capability == "CP03"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])