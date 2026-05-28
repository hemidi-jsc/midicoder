# coding: utf-8
"""
Angular Emitter cho CP46: MFA & Advanced Authentication.

Module này render Jinja2 templates để sinh MFA code
cho Angular stack, bao gồm components, service, types, và form.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_mfa.parser import MFAIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularMFAEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class AngularMFAEmitter:
    """Emitter cho Angular stack — CP46 MFA & Advanced Authentication.

    Render templates từ `stacks/angular/cp_full_mfa/`
    để sinh MFA code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-F27_MFA_FACTOR_NOT_FOUND,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: MFAIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit MFA code cho Angular.

        Sinh 6 files:
        - mfa-setup.component.ts
        - mfa-verify.component.ts
        - mfa-methods.component.ts
        - mfa.service.ts
        - mfa-types.ts
        - mfa-forms.ts

        Args:
            ir: MFAIR chứa MFA rules và config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("mfa-setup.component.ts.jinja2", "src/app/mfa/mfa-setup.component.ts"),
            ("mfa-verify.component.ts.jinja2", "src/app/mfa/mfa-verify.component.ts"),
            ("mfa-methods.component.ts.jinja2", "src/app/mfa/mfa-methods.component.ts"),
            ("mfa.service.ts.jinja2", "src/app/mfa/mfa.service.ts"),
            ("mfa-types.ts.jinja2", "src/app/mfa/mfa-types.ts"),
            ("mfa-forms.ts.jinja2", "src/app/mfa/mfa-forms.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: MFAIR) -> dict[str, Any]:
        """Xây dựng template context từ MFAIR."""
        rules_list = [r.to_dict() for r in ir.rules]
        return {
            "mfa_rules": rules_list,
            "rule_count": len(ir.rules),
            "enabled_methods": [m.value for m in ir.enabled_methods],
            "default_method": ir.default_method.value,
            "default_priority": ir.default_priority.value,
            "require_mfa": ir.require_mfa,
            "allow_backup": ir.allow_backup,
            "challenge_timeout": ir.challenge_timeout,
            "max_attempts": ir.max_attempts,
            "session_duration": ir.session_duration,
            "use_webauthn": ir.use_webauthn,
            "use_biometric": ir.use_biometric,
            "use_sms_otp": ir.use_sms_otp,
            "use_totp": ir.use_totp,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F27_MFA_FACTOR_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F27_MFA_FACTOR_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
