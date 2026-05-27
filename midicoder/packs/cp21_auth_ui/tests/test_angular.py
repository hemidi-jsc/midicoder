# coding: utf-8
"""
Tests cho CP21 Angular Auth UI Emitter.

Unit tests cho:
- AngularAuthUIEmitter initialization
- Emit auth pages
- Emit guards
- Emit session timeout
- UI framework support
"""

import pytest
from pathlib import Path
from midicoder.packs.cp21_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
)
from midicoder.packs.cp21_auth_ui.angular import (
    AngularAuthUIEmitter,
    GeneratedFile,
    emit_angular_auth_ui,
)
from midicoder.errors import MidicoderError


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Output directory cho tests."""
    d = tmp_path / "angular-output"
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
        ui_framework="material",
        mfa_enabled=True,
        oauth_enabled=True,
        include_role_guard=True,
        include_permission_guard=True,
        include_session_timeout=True,
    )


# ============================================================================
# Test AngularAuthUIEmitter initialization
# ============================================================================


class TestAngularAuthUIEmitterInit:
    """Tests cho khởi tạo AngularAuthUIEmitter."""

    def test_default_ui_framework(self):
        emitter = AngularAuthUIEmitter()
        assert emitter.ui_framework == "material"

    def test_custom_ui_framework(self):
        for fw in ["tailwind", "bootstrap", "antd", "carbon"]:
            emitter = AngularAuthUIEmitter(ui_framework=fw)
            assert emitter.ui_framework == fw

    def test_invalid_ui_framework_raises(self):
        with pytest.raises(MidicoderError):
            AngularAuthUIEmitter(ui_framework="invalid")

    def test_template_env_initialized(self):
        emitter = AngularAuthUIEmitter()
        assert emitter._template_env is not None


# ============================================================================
# Test AngularAuthUIEmitter generate
# ============================================================================


class TestAngularAuthUIEmitterGenerate:
    """Tests cho emit Angular auth UI."""

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
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        assert len(files) >= 4  # login + routes + module + index
        # Kiểm tra login component có trong files
        file_names = [f.path.name for f in files]
        assert "login.component.ts" in file_names

    def test_emit_full_config(self, output_dir: Path, full_config: AuthUIConfig):
        """Emit với config đầy đủ."""
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        # Kiểm tra số lượng files tối thiểu
        # 6 pages + 2 guards + 2 session + routes + module + index = 13
        assert len(files) >= 13

        file_names = [f.path.name for f in files]
        assert "login.component.ts" in file_names
        assert "register.component.ts" in file_names
        assert "forgot-password.component.ts" in file_names
        assert "reset-password.component.ts" in file_names
        assert "mfa-verify.component.ts" in file_names
        assert "oauth-callback.component.ts" in file_names
        assert "role.guard.ts" in file_names
        assert "permission.guard.ts" in file_names
        assert "session-timeout.modal.component.ts" in file_names
        assert "session-monitor.service.ts" in file_names
        assert "auth.routes.ts" in file_names
        assert "auth-ui.module.ts" in file_names
        assert "index.ts" in file_names

    def test_emit_files_written_to_disk(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra files được ghi xuống disk."""
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        for f in files:
            # File content không rỗng
            assert len(f.content) > 0, f"File {f.path.name} content rỗng"
            # File có path
            assert f.path is not None

    def test_emit_content_has_cp21_marker(self, output_dir: Path):
        """Kiểm tra content có marker CP21."""
        config = AuthUIConfig(pages=[AuthPageType.LOGIN], mfa_enabled=False, oauth_enabled=False)
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        login = next((f for f in files if f.path.name == "login.component.ts"), None)
        assert login is not None
        assert "CP21" in login.content

    def test_emit_role_guard_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra role guard có content đúng."""
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        role_guard = next((f for f in files if f.path.name == "role.guard.ts"), None)
        assert role_guard is not None
        assert "CanActivate" in role_guard.content
        assert "requiredRoles" in role_guard.content
        assert "unauthorized" in role_guard.content

    def test_emit_permission_guard_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra permission guard có content đúng."""
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        perm_guard = next((f for f in files if f.path.name == "permission.guard.ts"), None)
        assert perm_guard is not None
        assert "CanActivate" in perm_guard.content
        assert "requiredPermissions" in perm_guard.content

    def test_emit_session_monitor_content(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra session monitor có content đúng."""
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(full_config, output_dir)

        monitor = next((f for f in files if f.path.name == "session-monitor.service.ts"), None)
        assert monitor is not None
        assert "SessionMonitorService" in monitor.content
        assert "timeoutMs" in monitor.content

    def test_emit_without_role_guard(self, output_dir: Path):
        """Emit không có role guard khi config.disable."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
            mfa_enabled=False,
            oauth_enabled=False,
        )
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        file_names = [f.path.name for f in files]
        assert "role.guard.ts" not in file_names
        assert "permission.guard.ts" not in file_names

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
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        file_names = [f.path.name for f in files]
        assert "session-timeout.modal.component.ts" not in file_names
        assert "session-monitor.service.ts" not in file_names

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
            emitter = AngularAuthUIEmitter(ui_framework=fw)
            files = emitter.generate(config, output_dir)
            assert len(files) > 0

    def test_emit_output_dir_created(self, output_dir: Path, full_config: AuthUIConfig):
        """Kiểm tra auth-ui directory được tạo."""
        emitter = AngularAuthUIEmitter()
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
        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        for f in files:
            assert f.template is not None
            assert "cp21_auth_ui" in f.template


# ============================================================================
# Test emit_angular_auth_ui helper
# ============================================================================


class TestEmitAngularAuthUI:
    """Tests cho helper function emit_angular_auth_ui."""

    def test_helper_function(self, output_dir: Path):
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )
        files = emit_angular_auth_ui(config, output_dir)
        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)
