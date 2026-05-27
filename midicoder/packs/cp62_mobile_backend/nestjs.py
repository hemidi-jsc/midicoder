# coding: utf-8
"""
NestJS Emitter cho CP62: Mobile Backend (FCM/APNs Push, Deep Linking, Mobile Auth, OTA).

Module này render Jinja2 templates để sinh mobile backend code
cho NestJS stack, bao gồm push notification module, deep link service,
mobile auth controller, OTA controller, và device module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp62_mobile_backend.parser import MobileIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSMobileBackendEmitter",
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


class NestJSMobileBackendEmitter:
    """Emitter cho NestJS stack — CP62 Mobile Backend.

    Render templates từ `stacks/nestjs/cp62_mobile_backend/`
    để sinh mobile backend code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp62_mobile_backend"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
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
        ir: MobileIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit mobile backend code cho NestJS.

        Sinh các files:
        - push.service.ts: FCM/APNs push notification service với queue
        - push.controller.ts: Push notification API controller
        - deep-link.service.ts: Deep link resolution service
        - mobile-auth.controller.ts: OAuth2 mobile auth controller
        - ota.controller.ts: OTA update check controller
        - mobile-backend.module.ts: NestJS module tổng hợp

        Args:
            ir: MobileIR chứa mobile backend configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("push.service.ts.jinja2", "src/mobile/push/push.service.ts"),
            ("push.controller.ts.jinja2", "src/mobile/push/push.controller.ts"),
            ("deep-link.service.ts.jinja2", "src/mobile/deep-link/deep-link.service.ts"),
            ("mobile-auth.controller.ts.jinja2", "src/mobile/auth/mobile-auth.controller.ts"),
            ("ota.controller.ts.jinja2", "src/mobile/ota/ota.controller.ts"),
            ("mobile-backend.module.ts.jinja2", "src/mobile/mobile-backend.module.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: MobileIR) -> dict[str, Any]:
        """Xây dựng template context từ MobileIR."""
        push_list = [p.to_dict() for p in ir.push_configs]
        deep_link_list = [d.to_dict() for d in ir.deep_links]
        auth_list = [a.to_dict() for a in ir.auth_providers]
        ota_list = [o.to_dict() for o in ir.ota_configs]
        return {
            "push_configs": push_list,
            "deep_links": deep_link_list,
            "auth_providers": auth_list,
            "ota_configs": ota_list,
            "push_count": len(ir.push_configs),
            "deep_link_count": len(ir.deep_links),
            "auth_provider_count": len(ir.auth_providers),
            "ota_count": len(ir.ota_configs),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.INVALID_PARAMETER,
                reason=f"Render template thất bại {template_name}: {e}",
            )
