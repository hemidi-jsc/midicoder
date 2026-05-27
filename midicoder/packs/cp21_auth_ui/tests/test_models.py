# coding: utf-8
"""
TDD RED: Tests cho CP21 Auth UI Models.

Unit tests cho:
- AuthPageType enum
- UIFrameworkType enum
- SessionMonitorConfig validation
- AuthPageConfig defaults
- AuthUIConfig validation + utility methods
"""

import pytest
from midicoder.packs.cp21_auth_ui.models import (
    AuthPageConfig,
    AuthPageType,
    AuthUIConfig,
    SessionMonitorConfig,
    SUPPORTED_UI_FRAMEWORKS,
    UIFrameworkType,
)
from midicoder.errors import MidicoderError


# ============================================================================
# Test AuthPageType
# ============================================================================


class TestAuthPageType:
    """Tests cho AuthPageType enum."""

    def test_login_value(self):
        assert AuthPageType.LOGIN.value == "login"

    def test_register_value(self):
        assert AuthPageType.REGISTER.value == "register"

    def test_forgot_password_value(self):
        assert AuthPageType.FORGOT_PASSWORD.value == "forgot_password"

    def test_reset_password_value(self):
        assert AuthPageType.RESET_PASSWORD.value == "reset_password"

    def test_mfa_verify_value(self):
        assert AuthPageType.MFA_VERIFY.value == "mfa_verify"

    def test_oauth_callback_value(self):
        assert AuthPageType.OAUTH_CALLBACK.value == "oauth_callback"

    def test_all_six_pages(self):
        assert len(AuthPageType) == 6


# ============================================================================
# Test UIFrameworkType
# ============================================================================


class TestUIFrameworkType:
    """Tests cho UIFrameworkType enum."""

    def test_material_value(self):
        assert UIFrameworkType.MATERIAL.value == "material"

    def test_tailwind_value(self):
        assert UIFrameworkType.TAILWIND.value == "tailwind"

    def test_bootstrap_value(self):
        assert UIFrameworkType.BOOTSTRAP.value == "bootstrap"

    def test_ant_d_value(self):
        assert UIFrameworkType.ANT_D.value == "antd"

    def test_carbon_value(self):
        assert UIFrameworkType.CARBON.value == "carbon"

    def test_five_frameworks(self):
        assert len(UIFrameworkType) == 5

    def test_supported_list(self):
        assert SUPPORTED_UI_FRAMEWORKS == ["material", "tailwind", "bootstrap", "antd", "carbon"]


# ============================================================================
# Test SessionMonitorConfig
# ============================================================================


class TestSessionMonitorConfig:
    """Tests cho SessionMonitorConfig."""

    def test_default_values(self):
        cfg = SessionMonitorConfig()
        assert cfg.timeout_ms == 300_000
        assert cfg.interval_ms == 30_000
        assert cfg.redirect_path == "/login"
        assert cfg.renew_endpoint is None

    def test_custom_values(self):
        cfg = SessionMonitorConfig(
            timeout_ms=600_000,
            interval_ms=60_000,
            redirect_path="/auth/login",
            renew_endpoint="/api/auth/renew",
        )
        assert cfg.timeout_ms == 600_000
        assert cfg.interval_ms == 60_000
        assert cfg.redirect_path == "/auth/login"
        assert cfg.renew_endpoint == "/api/auth/renew"

    def test_negative_timeout_raises(self):
        with pytest.raises(MidicoderError):
            SessionMonitorConfig(timeout_ms=-1)

    def test_zero_timeout_raises(self):
        with pytest.raises(MidicoderError):
            SessionMonitorConfig(timeout_ms=0)

    def test_negative_interval_raises(self):
        with pytest.raises(MidicoderError):
            SessionMonitorConfig(interval_ms=-1)

    def test_interval_ge_timeout_raises(self):
        with pytest.raises(MidicoderError):
            SessionMonitorConfig(timeout_ms=30_000, interval_ms=30_000)

    def test_interval_equal_timeout_raises(self):
        with pytest.raises(MidicoderError):
            SessionMonitorConfig(timeout_ms=50_000, interval_ms=50_000)


# ============================================================================
# Test AuthPageConfig
# ============================================================================


class TestAuthPageConfig:
    """Tests cho AuthPageConfig."""

    def test_default_title_set(self):
        cfg = AuthPageConfig(page_type=AuthPageType.LOGIN)
        assert cfg.title == "Đăng nhập"

    def test_custom_title_kept(self):
        cfg = AuthPageConfig(page_type=AuthPageType.LOGIN, title="Sign In")
        assert cfg.title == "Sign In"

    def test_all_default_titles(self):
        expected = {
            AuthPageType.LOGIN: "Đăng nhập",
            AuthPageType.REGISTER: "Đăng ký tài khoản",
            AuthPageType.FORGOT_PASSWORD: "Quên mật khẩu",
            AuthPageType.RESET_PASSWORD: "Đặt lại mật khẩu",
            AuthPageType.MFA_VERIFY: "Xác thực hai yếu tố",
            AuthPageType.OAUTH_CALLBACK: "Xác thực OAuth",
        }
        for page_type, title in expected.items():
            cfg = AuthPageConfig(page_type=page_type)
            assert cfg.title == title

    def test_default_redirect(self):
        cfg = AuthPageConfig(page_type=AuthPageType.LOGIN)
        assert cfg.redirect_on_success == "/"

    def test_custom_redirect(self):
        cfg = AuthPageConfig(
            page_type=AuthPageType.LOGIN,
            redirect_on_success="/dashboard",
        )
        assert cfg.redirect_on_success == "/dashboard"


# ============================================================================
# Test AuthUIConfig
# ============================================================================


class TestAuthUIConfig:
    """Tests cho AuthUIConfig — model chính của CP21."""

    def test_default_config(self):
        cfg = AuthUIConfig()
        assert cfg.ui_framework == "material"
        assert cfg.mfa_enabled is True
        assert cfg.oauth_enabled is True
        assert cfg.include_role_guard is True
        assert cfg.include_permission_guard is True
        assert cfg.include_session_timeout is True

    def test_login_always_included(self):
        """Login page luôn được include, kể cả khi pages rỗng."""
        cfg = AuthUIConfig(pages=[])
        assert AuthPageType.LOGIN in cfg.pages

    def test_mfa_auto_included(self):
        """MFA page auto-included khi mfa_enabled=True."""
        cfg = AuthUIConfig(pages=[AuthPageType.LOGIN], mfa_enabled=True)
        assert AuthPageType.MFA_VERIFY in cfg.pages

    def test_oauth_auto_included(self):
        """OAuth page auto-included khi oauth_enabled=True."""
        cfg = AuthUIConfig(pages=[AuthPageType.LOGIN], oauth_enabled=True)
        assert AuthPageType.OAUTH_CALLBACK in cfg.pages

    def test_mfa_not_included_when_disabled(self):
        cfg = AuthUIConfig(pages=[AuthPageType.LOGIN], mfa_enabled=False, oauth_enabled=False)
        assert AuthPageType.MFA_VERIFY not in cfg.pages

    def test_oauth_not_included_when_disabled(self):
        cfg = AuthUIConfig(pages=[AuthPageType.LOGIN], mfa_enabled=False, oauth_enabled=False)
        assert AuthPageType.OAUTH_CALLBACK not in cfg.pages

    def test_invalid_ui_framework_raises(self):
        with pytest.raises(MidicoderError):
            AuthUIConfig(ui_framework="invalid_framework")

    def test_all_frameworks_valid(self):
        for fw in SUPPORTED_UI_FRAMEWORKS:
            cfg = AuthUIConfig(ui_framework=fw)
            assert cfg.ui_framework == fw

    def test_get_pages_to_emit_ordered(self):
        cfg = AuthUIConfig(
            pages=[AuthPageType.REGISTER, AuthPageType.LOGIN, AuthPageType.FORGOT_PASSWORD],
            mfa_enabled=False,
            oauth_enabled=False,
        )
        pages = cfg.get_pages_to_emit()
        assert pages[0] == AuthPageType.LOGIN
        assert pages[1] == AuthPageType.REGISTER
        assert pages[2] == AuthPageType.FORGOT_PASSWORD

    def test_has_page(self):
        cfg = AuthUIConfig(pages=[AuthPageType.LOGIN, AuthPageType.REGISTER])
        assert cfg.has_page(AuthPageType.LOGIN) is True
        assert cfg.has_page(AuthPageType.FORGOT_PASSWORD) is False

    def test_get_page_config_creates_default(self):
        cfg = AuthUIConfig()
        pg = cfg.get_page_config(AuthPageType.REGISTER)
        assert pg.page_type == AuthPageType.REGISTER
        assert pg.title == "Đăng ký tài khoản"

    def test_to_dict(self):
        cfg = AuthUIConfig(ui_framework="tailwind")
        d = cfg.to_dict()
        assert d["ui_framework"] == "tailwind"
        assert "material" not in d["ui_framework"]
        assert d["include_role_guard"] is True
        assert "pages" in d
        assert "session_monitor" in d

    def test_full_config(self):
        """Test config với tất cả pages và custom settings."""
        cfg = AuthUIConfig(
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
        pages = cfg.get_pages_to_emit()
        assert len(pages) == 6  # 4 + MFA + OAuth
        assert cfg.ui_framework == "antd"
