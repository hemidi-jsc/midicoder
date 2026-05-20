# coding: utf-8
"""
React Auth UI Emitter (CP21).

Module này cung cấp ReactAuthUIEmitter để emit auth-specific UI pages
cho React frontend:
- 6 auth pages: Login, Register, ForgotPassword, ResetPassword, MFA, OAuth Callback
- 2 route guards: RoleRoute, PermissionRoute
- Session timeout modal + monitor hook
- Auth routes config

Templates: stacks/react/core/cp21_auth_ui/**/*.jinja2

Usage:
    from midicoder.emitters.core.cp21_auth_ui.react import ReactAuthUIEmitter
    emitter = ReactAuthUIEmitter(ui_framework="antd")
    files = emitter.generate(config, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp21_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
    SUPPORTED_UI_FRAMEWORKS,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "cp21_auth_ui"

# Mapping: AuthPageType → (template_file, output_file)
_PAGE_TEMPLATE_MAP: dict[AuthPageType, tuple[str, str]] = {
    AuthPageType.LOGIN: ("login.tsx.jinja2", "login.tsx"),
    AuthPageType.REGISTER: ("register.tsx.jinja2", "register.tsx"),
    AuthPageType.FORGOT_PASSWORD: ("forgot-password.tsx.jinja2", "forgot-password.tsx"),
    AuthPageType.RESET_PASSWORD: ("reset-password.tsx.jinja2", "reset-password.tsx"),
    AuthPageType.MFA_VERIFY: ("mfa-verify.tsx.jinja2", "mfa-verify.tsx"),
    AuthPageType.OAUTH_CALLBACK: ("oauth-callback.tsx.jinja2", "oauth-callback.tsx"),
}


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactAuthUIEmitter:
    """Emitter cho React Auth UI Pages.

    Sinh ra 6 auth pages + 2 route wrappers + session monitor + routes.
    """

    SUPPORTED_UI_FRAMEWORKS = SUPPORTED_UI_FRAMEWORKS

    def __init__(self, ui_framework: str = "antd") -> None:
        """Khởi tạo ReactAuthUIEmitter.

        Args:
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            EM.raise_error(
                ErrorCode.CP21_INVALID_UI_FRAMEWORK,
                message=f"UI framework '{ui_framework}' không được hỗ trợ",
                ui_framework=ui_framework,
                supported=self.SUPPORTED_UI_FRAMEWORKS,
            )
        self.ui_framework = ui_framework

        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            # Custom delimiters để không conflict với JSX {{ }}
            variable_start_string="{[{",
            variable_end_string="}]}",
        )

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render jinja2 template với context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            EM.raise_error(
                ErrorCode.CP21_TEMPLATE_NOT_FOUND,
                message=f"Template không tìm thấy: {template_name}",
                template_name=template_name,
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.CP21_RENDER_FAILED,
                message=f"Lỗi render template '{template_name}': {e}",
                template_name=template_name,
                cause=str(e),
            )

    def generate(
        self,
        config: AuthUIConfig,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh React auth UI components từ AuthUIConfig.

        Args:
            config: AuthUIConfig instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        auth_dir = output_dir / "auth-ui"
        auth_dir.mkdir(parents=True, exist_ok=True)

        # 1. Emit auth pages
        for page_type in config.get_pages_to_emit():
            page_cfg = config.get_page_config(page_type)
            template_name, output_name = _PAGE_TEMPLATE_MAP[page_type]
            ctx = self._build_context(config, page_type, page_cfg)
            files.append(self._write_file(template_name, output_name, ctx, auth_dir, output_dir))

        # 2. Emit RoleRoute
        if config.include_role_guard:
            files.append(self._emit_role_route(auth_dir, output_dir))

        # 3. Emit PermissionRoute
        if config.include_permission_guard:
            files.append(self._emit_permission_route(auth_dir, output_dir))

        # 4. Emit Session Timeout Modal
        if config.include_session_timeout:
            files.append(self._emit_session_timeout_modal(config, auth_dir, output_dir))
            files.append(self._emit_use_session_monitor(config, auth_dir, output_dir))

        # 5. Emit Auth Routes
        files.append(self._emit_auth_routes(config, auth_dir, output_dir))

        # 6. Emit barrel index
        files.append(self._emit_index(auth_dir, output_dir))

        return files

    def _build_context(
        self,
        config: AuthUIConfig,
        page_type: AuthPageType,
        page_cfg: Any,
    ) -> dict[str, Any]:
        """Build template context cho auth page."""
        return {
            "ui_framework": config.ui_framework,
            "page_type": page_type.value,
            "title": page_cfg.title,
            "subtitle": page_cfg.subtitle,
            "logo_url": page_cfg.logo_url,
            "redirect_on_success": page_cfg.redirect_on_success,
            "mfa_enabled": config.mfa_enabled,
            "oauth_enabled": config.oauth_enabled,
        }

    def _write_file(
        self,
        template_name: str,
        filename: str,
        context: dict[str, Any],
        output_dir: Path,
        root_dir: Path,
    ) -> GeneratedFile:
        """Render template, write file, trả về GeneratedFile."""
        content = self._render_template(template_name, context)
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        try:
            rel_path = file_path.relative_to(root_dir)
        except ValueError:
            rel_path = file_path
        return GeneratedFile(
            path=rel_path,
            content=content,
            template=f"react/cp21_auth_ui/{template_name}",
        )

    def _emit_role_route(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit RoleRoute — component wrapper kiểm tra roles."""
        ctx = {"ui_framework": self.ui_framework}
        return self._write_file("RoleRoute.tsx.jinja2", "RoleRoute.tsx", ctx, output_dir, root_dir)

    def _emit_permission_route(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit PermissionRoute — component wrapper kiểm tra permissions."""
        ctx = {"ui_framework": self.ui_framework}
        return self._write_file("PermissionRoute.tsx.jinja2", "PermissionRoute.tsx", ctx, output_dir, root_dir)

    def _emit_session_timeout_modal(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit SessionTimeoutModal — modal cảnh báo session sắp hết hạn."""
        ctx = {
            "ui_framework": self.ui_framework,
            "timeout_ms": config.session_monitor.timeout_ms,
            "redirect_path": config.session_monitor.redirect_path,
        }
        return self._write_file(
            "SessionTimeoutModal.tsx.jinja2",
            "SessionTimeoutModal.tsx",
            ctx, output_dir, root_dir,
        )

    def _emit_use_session_monitor(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit useSessionMonitor — custom hook monitor token expiry."""
        ctx = {
            "ui_framework": self.ui_framework,
            "timeout_ms": config.session_monitor.timeout_ms,
            "interval_ms": config.session_monitor.interval_ms,
            "redirect_path": config.session_monitor.redirect_path,
            "renew_endpoint": config.session_monitor.renew_endpoint or "",
        }
        return self._write_file(
            "useSessionMonitor.ts.jinja2",
            "useSessionMonitor.ts",
            ctx, output_dir, root_dir,
        )

    def _emit_auth_routes(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit auth-routes.tsx — route config cho auth pages."""
        pages = config.get_pages_to_emit()
        ctx = {
            "ui_framework": self.ui_framework,
            "pages": [p.value for p in pages],
            "include_role_guard": config.include_role_guard,
            "include_permission_guard": config.include_permission_guard,
        }
        return self._write_file("auth-routes.tsx.jinja2", "auth-routes.tsx", ctx, output_dir, root_dir)

    def _emit_index(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit barrel index."""
        content = '/** Auth UI Module Exports - CP21.\n */\n'
        content += 'export * from "./login";\n'
        content += 'export * from "./register";\n'
        content += 'export * from "./forgot-password";\n'
        content += 'export * from "./reset-password";\n'
        content += 'export * from "./mfa-verify";\n'
        content += 'export * from "./oauth-callback";\n'
        content += 'export * from "./RoleRoute";\n'
        content += 'export * from "./PermissionRoute";\n'
        content += 'export * from "./SessionTimeoutModal";\n'
        content += 'export * from "./useSessionMonitor";\n'
        content += 'export * from "./auth-routes";\n'
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        try:
            rel_path = file_path.relative_to(root_dir)
        except ValueError:
            rel_path = file_path
        return GeneratedFile(path=rel_path, content=content, template="react/cp21_auth_ui/index.ts")


def emit_react_auth_ui(
    config: AuthUIConfig,
    output_dir: Path,
) -> list[GeneratedFile]:
    """Emit React auth UI code từ AuthUIConfig.

    Args:
        config: AuthUIConfig instance
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = ReactAuthUIEmitter(ui_framework=config.ui_framework)
    return emitter.generate(config, output_dir)


__all__ = ["ReactAuthUIEmitter", "GeneratedFile", "emit_react_auth_ui"]
