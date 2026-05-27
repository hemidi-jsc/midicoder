# coding: utf-8
"""
CP21: Authentication UI Models.

Module này cung cấp data models cho CP21 Authentication UI Generator:
- AuthPageType: Enum các auth pages có thể emit
- AuthUIConfig: Config chính cho auth UI generation
- SessionMonitorConfig: Config cho session timeout monitoring

Usage:
    from midicoder.packs.cp21_auth_ui.models import AuthUIConfig
    config = AuthUIConfig(pages=[AuthPageType.LOGIN, AuthPageType.REGISTER])

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =========================================================================
# Enums
# =========================================================================


class AuthPageType(str, Enum):
    """Enum các auth pages có thể emit."""

    LOGIN = "login"
    REGISTER = "register"
    FORGOT_PASSWORD = "forgot_password"
    RESET_PASSWORD = "reset_password"
    MFA_VERIFY = "mfa_verify"
    OAUTH_CALLBACK = "oauth_callback"


class UIFrameworkType(str, Enum):
    """Enum các UI framework được hỗ trợ."""

    MATERIAL = "material"
    TAILWIND = "tailwind"
    BOOTSTRAP = "bootstrap"
    ANT_D = "antd"
    CARBON = "carbon"


# Supported frameworks list (single source)
SUPPORTED_UI_FRAMEWORKS = [f.value for f in UIFrameworkType]


# =========================================================================
# Session Monitor Config
# =========================================================================


@dataclass
class SessionMonitorConfig:
    """
    Config cho session timeout monitoring.

    Attributes:
        timeout_ms: Thời gian (ms) trước khi token expire để show modal
        interval_ms: Interval (ms) để check token expiry
        redirect_path: Path redirect sau khi session timeout
        renew_endpoint: API endpoint để renew token (optional)
    """

    timeout_ms: int = 300_000  # 5 phút mặc định
    interval_ms: int = 30_000  # check mỗi 30 giây
    redirect_path: str = "/login"
    renew_endpoint: str | None = None

    def __post_init__(self) -> None:
        """Validate session timeout config."""
        if self.timeout_ms <= 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.CP21_INVALID_SESSION_TIMEOUT,
                message=f"timeout_ms phải > 0, nhận được: {self.timeout_ms}",
                timeout_ms=self.timeout_ms,
            )
        if self.interval_ms <= 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.CP21_INVALID_SESSION_TIMEOUT,
                message=f"interval_ms phải > 0, nhận được: {self.interval_ms}",
                interval_ms=self.interval_ms,
            )
        # Interval phải nhỏ hơn timeout để kịp cảnh báo
        if self.interval_ms >= self.timeout_ms:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.CP21_INVALID_SESSION_TIMEOUT,
                message="interval_ms phải nhỏ hơn timeout_ms",
                interval_ms=self.interval_ms,
                timeout_ms=self.timeout_ms,
            )


# =========================================================================
# Auth Page Config
# =========================================================================


@dataclass
class AuthPageConfig:
    """
    Config cho từng auth page riêng lẻ.

    Attributes:
        page_type: Loại page
        title: Title hiển thị trên page
        subtitle: Subtitle/mô tả ngắn
        logo_url: URL logo hiển thị (optional)
        redirect_on_success: Path redirect sau khi thành công
    """

    page_type: AuthPageType
    title: str = ""
    subtitle: str = ""
    logo_url: str | None = None
    redirect_on_success: str = "/"

    def __post_init__(self) -> None:
        """Set default title nếu chưa có."""
        default_titles = {
            AuthPageType.LOGIN: "Đăng nhập",
            AuthPageType.REGISTER: "Đăng ký tài khoản",
            AuthPageType.FORGOT_PASSWORD: "Quên mật khẩu",
            AuthPageType.RESET_PASSWORD: "Đặt lại mật khẩu",
            AuthPageType.MFA_VERIFY: "Xác thực hai yếu tố",
            AuthPageType.OAUTH_CALLBACK: "Xác thực OAuth",
        }
        if not self.title:
            self.title = default_titles.get(self.page_type, "Authentication")


# =========================================================================
# AuthUIConfig (main config)
# =========================================================================


@dataclass
class AuthUIConfig:
    """
    Config chính cho CP21 Authentication UI Generator.

    Attributes:
        pages: Danh sách các auth pages cần emit
        ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        mfa_enabled: Có enable MFA verification page không
        oauth_enabled: Có enable OAuth callback page không
        session_monitor: Config cho session timeout monitoring
        page_configs: Config chi tiết cho từng page (optional)
        include_role_guard: Có emit RoleGuard không
        include_permission_guard: Có emit PermissionGuard không
        include_session_timeout: Có emit session timeout modal không

    Example:
        config = AuthUIConfig(
            pages=[AuthPageType.LOGIN, AuthPageType.REGISTER],
            ui_framework="material",
            mfa_enabled=True,
        )
    """

    pages: list[AuthPageType] = field(default_factory=list)
    ui_framework: str = "material"
    mfa_enabled: bool = True
    oauth_enabled: bool = True
    session_monitor: SessionMonitorConfig = field(default_factory=SessionMonitorConfig)
    page_configs: dict[str, AuthPageConfig] = field(default_factory=dict)
    include_role_guard: bool = True
    include_permission_guard: bool = True
    include_session_timeout: bool = True

    def __post_init__(self) -> None:
        """Validate UI framework và pages config."""
        # Validate UI framework
        if self.ui_framework not in SUPPORTED_UI_FRAMEWORKS:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.CP21_INVALID_UI_FRAMEWORK,
                message=f"UI framework '{self.ui_framework}' không được hỗ trợ",
                ui_framework=self.ui_framework,
                supported=SUPPORTED_UI_FRAMEWORKS,
            )

        # Auto-include pages based on flags
        if self.mfa_enabled and AuthPageType.MFA_VERIFY not in self.pages:
            self.pages.append(AuthPageType.MFA_VERIFY)
        if self.oauth_enabled and AuthPageType.OAUTH_CALLBACK not in self.pages:
            self.pages.append(AuthPageType.OAUTH_CALLBACK)

        # Đảm bảo login luôn có (là page bắt buộc)
        if AuthPageType.LOGIN not in self.pages:
            self.pages.insert(0, AuthPageType.LOGIN)

        # Validate page_configs reference valid pages
        for key, pg_cfg in self.page_configs.items():
            if not pg_cfg.page_type.value:
                from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
                EM.raise_error(
                    ErrorCode.CP21_MISSING_PAGE_CONFIG,
                    message=f"Page config '{key}' thiếu page_type",
                    page_key=key,
                )

    def get_pages_to_emit(self) -> list[AuthPageType]:
        """Trả về danh sách pages cần emit (sorted theo thứ tự hợp lý)."""
        order = [
            AuthPageType.LOGIN,
            AuthPageType.REGISTER,
            AuthPageType.FORGOT_PASSWORD,
            AuthPageType.RESET_PASSWORD,
            AuthPageType.MFA_VERIFY,
            AuthPageType.OAUTH_CALLBACK,
        ]
        return [p for p in order if p in self.pages]

    def has_page(self, page_type: AuthPageType) -> bool:
        """Kiểm tra page type có trong config không."""
        return page_type in self.pages

    def get_page_config(self, page_type: AuthPageType) -> AuthPageConfig:
        """Lấy config cho page type (tạo default nếu chưa có)."""
        key = page_type.value
        if key not in self.page_configs:
            self.page_configs[key] = AuthPageConfig(page_type=page_type)
        return self.page_configs[key]

    def to_dict(self) -> dict[str, Any]:
        """Serialize config thành dict."""
        return {
            "pages": [p.value for p in self.pages],
            "ui_framework": self.ui_framework,
            "mfa_enabled": self.mfa_enabled,
            "oauth_enabled": self.oauth_enabled,
            "session_monitor": {
                "timeout_ms": self.session_monitor.timeout_ms,
                "interval_ms": self.session_monitor.interval_ms,
                "redirect_path": self.session_monitor.redirect_path,
                "renew_endpoint": self.session_monitor.renew_endpoint,
            },
            "include_role_guard": self.include_role_guard,
            "include_permission_guard": self.include_permission_guard,
            "include_session_timeout": self.include_session_timeout,
        }


__all__ = [
    "AuthPageType",
    "UIFrameworkType",
    "SUPPORTED_UI_FRAMEWORKS",
    "SessionMonitorConfig",
    "AuthPageConfig",
    "AuthUIConfig",
]
