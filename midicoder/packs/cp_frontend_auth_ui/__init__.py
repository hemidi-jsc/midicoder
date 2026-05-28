# coding: utf-8
"""
Authentication UI Generator (CP21).

Module này cung cấp các models và emitters để sinh auth-specific UI pages
từ AuthUIConfig: Login, Register, ForgotPassword, ResetPassword, MFA, OAuth Callback,
RoleGuard, PermissionGuard, Session Timeout Modal.

Models:
    - AuthPageType: Enum các auth pages
    - UIFrameworkType: Enum các UI framework
    - SessionMonitorConfig: Config cho session monitoring
    - AuthPageConfig: Config cho từng page
    - AuthUIConfig: Config chính

Emitters:
    - AngularAuthUIEmitter: Angular components
    - ReactAuthUIEmitter: React components
"""

from midicoder.packs.cp_frontend_auth_ui.models import (
    AuthPageType,
    UIFrameworkType,
    SUPPORTED_UI_FRAMEWORKS,
    SessionMonitorConfig,
    AuthPageConfig,
    AuthUIConfig,
)

from midicoder.packs.cp_frontend_auth_ui.angular import (
    AngularAuthUIEmitter,
    emit_angular_auth_ui,
)

from midicoder.packs.cp_frontend_auth_ui.react import (
    ReactAuthUIEmitter,
    emit_react_auth_ui,
)

__all__ = [
    # Enums
    "AuthPageType",
    "UIFrameworkType",
    "SUPPORTED_UI_FRAMEWORKS",
    # Models
    "SessionMonitorConfig",
    "AuthPageConfig",
    "AuthUIConfig",
    # Emitters
    "AngularAuthUIEmitter",
    "ReactAuthUIEmitter",
    # Helper functions
    "emit_angular_auth_ui",
    "emit_react_auth_ui",
]
