# coding: utf-8
"""
Integration tests cho CP21 Authentication UI Generator.

Test full pipeline: AuthUIConfig → Angular/React emit → verify output.
"""

import pytest
from pathlib import Path
from midicoder.packs.cp21_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
    SessionMonitorConfig,
)
from midicoder.packs.cp21_auth_ui.angular import AngularAuthUIEmitter
from midicoder.packs.cp21_auth_ui.react import ReactAuthUIEmitter


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Output directory cho integration tests."""
    d = tmp_path / "integration-output"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ============================================================================
# Test full pipeline: Config → Emit → Verify (Angular)
# ============================================================================


class TestAngularFullPipeline:
    """Integration tests cho Angular pipeline."""

    def test_full_pipeline_with_all_features(self, output_dir: Path):
        """Test full Angular emit với tất cả features."""
        config = AuthUIConfig(
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

        emitter = AngularAuthUIEmitter(ui_framework=config.ui_framework)
        files = emitter.generate(config, output_dir)

        # Verify structure
        file_names = [f.path.name for f in files]

        # Auth pages
        assert "login.component.ts" in file_names
        assert "register.component.ts" in file_names
        assert "forgot-password.component.ts" in file_names
        assert "reset-password.component.ts" in file_names
        assert "mfa-verify.component.ts" in file_names
        assert "oauth-callback.component.ts" in file_names

        # Guards
        assert "role.guard.ts" in file_names
        assert "permission.guard.ts" in file_names

        # Session
        assert "session-timeout.modal.component.ts" in file_names
        assert "session-monitor.service.ts" in file_names

        # Routes + Module
        assert "auth.routes.ts" in file_names
        assert "auth-ui.module.ts" in file_names

        # Index
        assert "index.ts" in file_names

        # Verify content quality
        for f in files:
            assert len(f.content) > 50  # Không phải placeholder
            assert f.path.name.endswith(".ts")

    def test_angular_output_directory_structure(self, output_dir: Path):
        """Kiểm tra cấu trúc directory output đúng."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=True,
            include_permission_guard=False,
            include_session_timeout=False,
        )

        emitter = AngularAuthUIEmitter()
        emitter.generate(config, output_dir)

        auth_dir = output_dir / "auth-ui"
        assert auth_dir.exists()

        login_file = auth_dir / "login.component.ts"
        assert login_file.exists()
        content = login_file.read_text(encoding="utf-8")
        assert "LoginComponent" in content

    def test_angular_custom_session_config(self, output_dir: Path):
        """Test session monitor với custom config."""
        session_cfg = SessionMonitorConfig(
            timeout_ms=600_000,
            interval_ms=60_000,
            redirect_path="/auth/login",
            renew_endpoint="/api/auth/renew",
        )
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            session_monitor=session_cfg,
            include_session_timeout=True,
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
        )

        emitter = AngularAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        monitor = next(f for f in files if f.path.name == "session-monitor.service.ts")
        # Template variables are replaced at render time, verify the rendered output exists
        assert "SessionMonitorService" in monitor.content
        assert "/auth/login" in monitor.content

    def test_angular_all_ui_frameworks_emit(self, output_dir: Path):
        """Test emit hoạt động với cả 5 UI frameworks."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )

        frameworks = ["material", "tailwind", "bootstrap", "antd", "carbon"]
        for fw in frameworks:
            config.ui_framework = fw
            emitter = AngularAuthUIEmitter(ui_framework=fw)
            files = emitter.generate(config, output_dir)
            assert len(files) > 0

            # Login file phải có content
            login = next(f for f in files if f.path.name == "login.component.ts")
            assert "CP21" in login.content


# ============================================================================
# Test full pipeline: Config → Emit → Verify (React)
# ============================================================================


class TestReactFullPipeline:
    """Integration tests cho React pipeline."""

    def test_full_pipeline_with_all_features(self, output_dir: Path):
        """Test full React emit với tất cả features."""
        config = AuthUIConfig(
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

        emitter = ReactAuthUIEmitter(ui_framework=config.ui_framework)
        files = emitter.generate(config, output_dir)

        file_names = [f.path.name for f in files]

        # Auth pages
        assert "login.tsx" in file_names
        assert "register.tsx" in file_names
        assert "forgot-password.tsx" in file_names
        assert "reset-password.tsx" in file_names
        assert "mfa-verify.tsx" in file_names
        assert "oauth-callback.tsx" in file_names

        # Route guards
        assert "RoleRoute.tsx" in file_names
        assert "PermissionRoute.tsx" in file_names

        # Session
        assert "SessionTimeoutModal.tsx" in file_names
        assert "useSessionMonitor.ts" in file_names

        # Routes
        assert "auth-routes.tsx" in file_names

        # Index
        assert "index.ts" in file_names

        # Verify content quality
        for f in files:
            assert len(f.content) > 50

    def test_react_output_directory_structure(self, output_dir: Path):
        """Kiểm tra cấu trúc directory output đúng."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=True,
            include_permission_guard=False,
            include_session_timeout=False,
        )

        emitter = ReactAuthUIEmitter()
        emitter.generate(config, output_dir)

        auth_dir = output_dir / "auth-ui"
        assert auth_dir.exists()

        login_file = auth_dir / "login.tsx"
        assert login_file.exists()
        content = login_file.read_text(encoding="utf-8")
        assert "CP21" in content

    def test_react_custom_session_config(self, output_dir: Path):
        """Test session monitor với custom config."""
        session_cfg = SessionMonitorConfig(
            timeout_ms=900_000,
            interval_ms=90_000,
            redirect_path="/auth/signin",
            renew_endpoint="/api/session/renew",
        )
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            session_monitor=session_cfg,
            include_session_timeout=True,
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
        )

        emitter = ReactAuthUIEmitter()
        files = emitter.generate(config, output_dir)

        hook = next(f for f in files if f.path.name == "useSessionMonitor.ts")
        assert "useSessionMonitor" in hook.content

    def test_react_all_ui_frameworks_emit(self, output_dir: Path):
        """Test emit hoạt động với cả 5 UI frameworks."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
            include_session_timeout=False,
        )

        frameworks = ["material", "tailwind", "bootstrap", "antd", "carbon"]
        for fw in frameworks:
            config.ui_framework = fw
            emitter = ReactAuthUIEmitter(ui_framework=fw)
            files = emitter.generate(config, output_dir)
            assert len(files) > 0

            login = next(f for f in files if f.path.name == "login.tsx")
            assert "CP21" in login.content


# ============================================================================
# Cross-stack consistency
# ============================================================================


class TestCrossStackConsistency:
    """Tests kiểm tra consistency giữa Angular và React."""

    def test_same_config_same_pages(self, output_dir: Path):
        """Cùng config → cùng số lượng auth pages."""
        config = AuthUIConfig(
            pages=[
                AuthPageType.LOGIN,
                AuthPageType.REGISTER,
                AuthPageType.FORGOT_PASSWORD,
            ],
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=True,
            include_permission_guard=True,
            include_session_timeout=True,
        )

        angular_emitter = AngularAuthUIEmitter()
        angular_files = angular_emitter.generate(config, output_dir / "angular")

        react_emitter = ReactAuthUIEmitter()
        react_files = react_emitter.generate(config, output_dir / "react")

        # Cùng số lượng page components (3 pages)
        angular_pages = [f for f in angular_files if "component.ts" in str(f.path) and f.path.name not in ("auth-ui.module.ts", "auth.routes.ts", "index.ts")]
        react_pages = [f for f in react_files if f.path.name.endswith(".tsx") and f.path.name not in ("auth-routes.tsx", "RoleRoute.tsx", "PermissionRoute.tsx", "SessionTimeoutModal.tsx", "index.ts")]

        # Angular: 3 page components
        # React: 3 page components
        assert len(angular_pages) >= 3
        assert len(react_pages) >= 3

    def test_both_stacks_emit_guards(self, output_dir: Path):
        """Cả Angular và React đều emit guards."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            include_role_guard=True,
            include_permission_guard=True,
            mfa_enabled=False,
            oauth_enabled=False,
            include_session_timeout=False,
        )

        angular_emitter = AngularAuthUIEmitter()
        angular_files = angular_emitter.generate(config, output_dir / "angular")
        angular_names = [f.path.name for f in angular_files]

        react_emitter = ReactAuthUIEmitter()
        react_files = react_emitter.generate(config, output_dir / "react")
        react_names = [f.path.name for f in react_files]

        assert "role.guard.ts" in angular_names
        assert "permission.guard.ts" in angular_names
        assert "RoleRoute.tsx" in react_names
        assert "PermissionRoute.tsx" in react_names

    def test_both_stacks_emit_session_monitor(self, output_dir: Path):
        """Cả Angular và React đều emit session monitoring."""
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN],
            include_session_timeout=True,
            mfa_enabled=False,
            oauth_enabled=False,
            include_role_guard=False,
            include_permission_guard=False,
        )

        angular_emitter = AngularAuthUIEmitter()
        angular_files = angular_emitter.generate(config, output_dir / "angular")
        angular_names = [f.path.name for f in angular_files]

        react_emitter = ReactAuthUIEmitter()
        react_files = react_emitter.generate(config, output_dir / "react")
        react_names = [f.path.name for f in react_files]

        assert "session-timeout.modal.component.ts" in angular_names
        assert "session-monitor.service.ts" in angular_names
        assert "SessionTimeoutModal.tsx" in react_names
        assert "useSessionMonitor.ts" in react_names
