# coding: utf-8
"""
Angular Auth UI Emitter (CP21).

Module này cung cấp AngularAuthUIEmitter để emit auth-specific UI pages
cho Angular frontend:
- 6 auth pages: Login, Register, ForgotPassword, ResetPassword, MFA, OAuth Callback
- 2 route guards: RoleGuard, PermissionGuard
- Session timeout modal + monitor service
- Auth routes config + module

Templates: stacks/angular/cp21_auth_ui/**/*.jinja2

Usage:
    from midicoder.packs.cp21_auth_ui.angular import AngularAuthUIEmitter
    emitter = AngularAuthUIEmitter(ui_framework="material")
    files = emitter.generate(config, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp21_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
    SUPPORTED_UI_FRAMEWORKS,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "angular" / "core" / "cp21_auth_ui"

# Mapping: AuthPageType → (template_file, output_file)
_PAGE_TEMPLATE_MAP: dict[AuthPageType, tuple[str, str]] = {
    AuthPageType.LOGIN: ("login.component.ts.jinja2", "login.component.ts"),
    AuthPageType.REGISTER: ("register.component.ts.jinja2", "register.component.ts"),
    AuthPageType.FORGOT_PASSWORD: ("forgot-password.component.ts.jinja2", "forgot-password.component.ts"),
    AuthPageType.RESET_PASSWORD: ("reset-password.component.ts.jinja2", "reset-password.component.ts"),
    AuthPageType.MFA_VERIFY: ("mfa-verify.component.ts.jinja2", "mfa-verify.component.ts"),
    AuthPageType.OAUTH_CALLBACK: ("oauth-callback.component.ts.jinja2", "oauth-callback.component.ts"),
}


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class AngularAuthUIEmitter:
    """Emitter cho Angular Auth UI Pages.

    Sinh ra 6 auth pages + 2 guards + session monitor + routes.
    """

    SUPPORTED_UI_FRAMEWORKS = SUPPORTED_UI_FRAMEWORKS

    def __init__(self, ui_framework: str = "material") -> None:
        """Khởi tạo AngularAuthUIEmitter.

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
            # Custom delimiters để không conflict với Angular {{ }}
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
        """Sinh Angular auth UI components từ AuthUIConfig.

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

        # 2. Emit RoleGuard
        if config.include_role_guard:
            files.append(self._emit_role_guard(auth_dir, output_dir))

        # 3. Emit PermissionGuard
        if config.include_permission_guard:
            files.append(self._emit_permission_guard(auth_dir, output_dir))

        # 4. Emit Session Timeout Modal
        if config.include_session_timeout:
            files.append(self._emit_session_timeout_modal(config, auth_dir, output_dir))
            files.append(self._emit_session_monitor_service(config, auth_dir, output_dir))

        # 5. Emit Auth Routes
        files.append(self._emit_auth_routes(config, auth_dir, output_dir))

        # 6. Emit Auth UI Module
        files.append(self._emit_auth_ui_module(config, auth_dir, output_dir))

        # 7. Emit barrel index
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
            template=f"angular/cp21_auth_ui/{template_name}",
        )

    def _emit_role_guard(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit RoleGuard — guard kiểm tra roles của user."""
        ctx = {"ui_framework": self.ui_framework}
        return self._write_file("role.guard.ts.jinja2", "role.guard.ts", ctx, output_dir, root_dir)

    def _emit_permission_guard(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit PermissionGuard — guard kiểm tra permissions của user."""
        ctx = {"ui_framework": self.ui_framework}
        return self._write_file("permission.guard.ts.jinja2", "permission.guard.ts", ctx, output_dir, root_dir)

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
            "session-timeout.modal.component.ts.jinja2",
            "session-timeout.modal.component.ts",
            ctx, output_dir, root_dir,
        )

    def _emit_session_monitor_service(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit SessionMonitorService — service monitor token expiry."""
        ctx = {
            "ui_framework": self.ui_framework,
            "timeout_ms": config.session_monitor.timeout_ms,
            "interval_ms": config.session_monitor.interval_ms,
            "redirect_path": config.session_monitor.redirect_path,
            "renew_endpoint": config.session_monitor.renew_endpoint or "",
        }
        return self._write_file(
            "session-monitor.service.ts.jinja2",
            "session-monitor.service.ts",
            ctx, output_dir, root_dir,
        )

    def _emit_auth_routes(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit auth.routes.ts — route config cho auth pages."""
        pages = config.get_pages_to_emit()
        ctx = {
            "ui_framework": self.ui_framework,
            "pages": [p.value for p in pages],
            "include_role_guard": config.include_role_guard,
            "include_permission_guard": config.include_permission_guard,
        }
        return self._write_file("auth.routes.ts.jinja2", "auth.routes.ts", ctx, output_dir, root_dir)

    def _emit_auth_ui_module(
        self, config: AuthUIConfig, output_dir: Path, root_dir: Path
    ) -> GeneratedFile:
        """Emit auth-ui.module.ts — Angular module gom tất cả auth UI components."""
        pages = config.get_pages_to_emit()
        ctx = {
            "ui_framework": self.ui_framework,
            "pages": [p.value for p in pages],
            "include_role_guard": config.include_role_guard,
            "include_permission_guard": config.include_permission_guard,
            "include_session_timeout": config.include_session_timeout,
        }
        return self._write_file("auth-ui.module.ts.jinja2", "auth-ui.module.ts", ctx, output_dir, root_dir)

    def _emit_index(self, output_dir: Path, root_dir: Path) -> GeneratedFile:
        """Emit barrel index."""
        content = '/** Auth UI Module Exports - CP21.\n */\n'
        content += 'export * from "./login.component";\n'
        content += 'export * from "./register.component";\n'
        content += 'export * from "./forgot-password.component";\n'
        content += 'export * from "./reset-password.component";\n'
        content += 'export * from "./mfa-verify.component";\n'
        content += 'export * from "./oauth-callback.component";\n'
        content += 'export * from "./role.guard";\n'
        content += 'export * from "./permission.guard";\n'
        content += 'export * from "./session-timeout.modal.component";\n'
        content += 'export * from "./session-monitor.service";\n'
        content += 'export * from "./auth.routes";\n'
        content += 'export * from "./auth-ui.module";\n'
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        try:
            rel_path = file_path.relative_to(root_dir)
        except ValueError:
            rel_path = file_path
        return GeneratedFile(path=rel_path, content=content, template="angular/cp21_auth_ui/index.ts")


def emit_angular_auth_ui(
    config: AuthUIConfig,
    output_dir: Path,
) -> list[GeneratedFile]:
    """Emit Angular auth UI code từ AuthUIConfig.

    Args:
        config: AuthUIConfig instance
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = AngularAuthUIEmitter(ui_framework=config.ui_framework)
    return emitter.generate(config, output_dir)


__all__ = ["AngularAuthUIEmitter", "GeneratedFile", "emit_angular_auth_ui"]
