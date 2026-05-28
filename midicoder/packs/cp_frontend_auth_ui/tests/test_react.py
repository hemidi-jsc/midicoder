# coding: utf-8
"""
Tests cho CP21 React Auth UI Emitter.

Unit tests cho:
- ReactAuthUIEmitter initialization
- Emit auth pages
- Emit route guards
- Emit session monitor
- UI framework support
"""

import pytest
from pathlib import Path
from midicoder.packs.cp_frontend_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
)
from midicoder.packs.cp_frontend_auth_ui.react import (
    ReactAuthUIEmitter,
    GeneratedFile,
    emit_react_auth_ui,
)
from midicoder.errors import MidicoderError


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Output directory cho tests."""
    d = tmp_path / "react-output"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def full_config() -> AuthUIConfig:
    """AuthUIConfig với tất cả pages bật."""
    return AuthUIConfig(
        pages=[
            AuthPageType.LOGIN,
            AuthPageType.REGISTER,
            AuthPageType.FORGOT_PASSWORD,
            AuthPageType.RESET_PASSWORD,
        ],
        ui_framework="antd",
        mfa_enabled=True,
        oauth_enabled=True,
        include_role_guard=True,
        include_permission_guard=True,
        include_session_timeout=True,
    )


# ============================================================================
# Test ReactAuthUIEmitter initialization
# ============================================================================


class TestReactAuthUIEmitterInit:
    """Tests cho khởi tạo ReactAuthUIEmitter."""

    def test_default_ui_framework(self):
        emitter = ReactAuthUIEmitter()
        assert emitter.ui_framework == "antd"

    def test_custom_ui_framework(self):
        for fw in ["material", "tailwind", "bootstrap", "carbon"]:
            emitter = ReactAuthUIEmitter(ui_framework=fw)
            assert emitter.ui_framework == fw

    def test_invalid_ui_framework_raises(self):
        with pytest.raises(MidicoderError):
            ReactAuthUIEmitter(ui_framework="invalid")

    def test_template_env_initialized(self):
        emitter = ReactAuthUIEmitter()
        assert emitter._template_env is not None


# ============================================================================
# Test ReactAuthUIEmitter generate
# ============================================================================


class TestReactAuthUIEmitterGenerate:
    """Tests cho emit React auth UI."""

    def test_emit_minimal_config(self, output_dir: Path):
        """Emit với config tối thiểu (chỉ login)."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        assert len(files) >= 3  # login + routes + index
        file_names = [f.path.name for f in files]
        assert "login.tsx" in file_names

    def test_emit_full_config(self, output_dir: Path, full_config: AuthUIConfig):
        """Emit với config đầy đủ."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        # 6 pages + 2 route wrappers + 2 session + routes + index = 12
        assert len(files) >= 12

        file_names = [f.path.name for f in files]
        assert "login.tsx" in file_names
        assert "register.tsx" in file_names
        assert "forgot-password.tsx" in file_names
        assert "reset-password.tsx" in file_names
        assert "mfa-verify.tsx" in file_names
        assert "oauth-callback.tsx" in file_names
        assert "RoleRoute.tsx" in file_names
        assert "PermissionRoute.tsx" in file_names
        assert "SessionTimeoutModal.tsx" in file_names
        assert "useSessionMonitor.ts" in file_names
        assert "auth-routes.tsx" in file_names
        assert "index.ts" in file_names

    def test_emit_files_written_to_disk(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra files được ghi xuống disk."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        for f in files:
            assert len(f.content) > 0, f"File {f.path.name} content rỗng"
            assert f.path is not None

    def test_emit_content_has_cp21_marker(self, output_dir: Path):
        """Kiểm tra content có marker CP21."""
        config = AuthUIConfig(pages=[AuthPageType.LOGIN], mfa_enabled=False, oauth_enabled=False)
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        login = next((f for f in files if f.path.name == "login.tsx"), None)
        assert login is not None
        assert "CP21" in login.content

    def test_emit_role_route_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra RoleRoute có content đúng."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        role_route = next((f for f in files if f.path.name == "RoleRoute.tsx"), None)
        assert role_route is not None
        assert "requiredRoles" in role_route.content
        assert "Navigate" in role_route.content

    def test_emit_permission_route_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra PermissionRoute có content đúng."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        perm_route = next((f for f in files if f.path.name == "PermissionRoute.tsx"), None)
        assert perm_route is not None
        assert "requiredPermissions" in perm_route.content

    def test_emit_session_timeout_modal_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra SessionTimeoutModal có content đúng."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        modal = next((f for f in files if f.path.name == "SessionTimeoutModal.tsx"), None)
        assert modal is not None
        assert "countdown" in modal.content
        assert "onStayLoggedIn" in modal.content

    def test_emit_use_session_monitor_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra useSessionMonitor có content đúng."""
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        hook = next((f for f in files if f.path.name == "useSessionMonitor.ts"), None)
        assert hook is not None
        assert "useSessionMonitor" in hook.content
        assert "timeoutMs" in hook.content

    def test_emit_without_role_guard(self, output_dir: Path):
        """Emit không có RoleRoute khi config.disable."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
            mfa_enabled=False,
            oauth_enabled=False,
        )
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        file_names = [f.path.name for f in files]
        assert "RoleRoute.tsx" not in file_names
        assert "PermissionRoute.tsx" not in file_names

    def test_emit_without_session_timeout(self, output_dir: Path):
        """Emit không có session timeout khi config.disable."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            include_session_timeout=False,
            include_role_guard=False,
            include_permission_guard=False,
            mfa_enabled=False,
            oauth_enabled=False,
        )
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        file_names = [f.path.name for f in files]
        assert "SessionTimeoutModal.tsx" not in file_names
        assert "useSessionMonitor.ts" not in file_names

    def test_emit_all_ui_frameworks(self, output_dir: Path):
        """Kiểm tra emit hoạt động với tất cả UI frameworks."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )
        for fw in ["material", "tailwind", "bootstrap", "antd", "carbon"]:
            config.ui_framework = fw
            emitter = ReactAuthUIEmitter(ui_framework=fw)
            files = emitter.generate(config, output_dir)
            assert len(files) > 0

    def test_emit_output_dir_created(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra auth-ui directory được tạo."""
        emitter = ReactAuthUIEmitter()
        emitter.generate(full_config, output_dir)

        auth_dir = output_dir / "auth-ui"
        assert auth_dir.exists()
        assert auth_dir.is_dir()

    def test_generated_file_has_correct_template_path(self, output_dir: Path):
        """Kiểm tra GeneratedFile có template path đúng."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )
        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        for f in files:
            assert f.template is not None
            assert "cp_frontend_auth_ui" in f.template


# ============================================================================
# Test emit_react_auth_ui helper
# ============================================================================


class TestEmitReactAuthUI:
    """Tests cho helper function emit_react_auth_ui."""

    def test_helper_function(self, output_dir: Path):
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )
        files = emit_react_auth_ui(config, output_dir)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)
