# coding: utf-8
"""
FastAPI Emitter cho CP62: Mobile Backend (FCM/APNs Push, Deep Linking, Mobile Auth, OTA).

Module này render Jinja2 templates để sinh mobile backend code
cho FastAPI stack, bao gồm push notification service, deep link resolver,
mobile auth routes, và OTA check endpoint.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp62_mobile_backend.parser import MobileIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIMobileBackendEmitter",
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


class FastAPIMobileBackendEmitter:
    """Emitter cho FastAPI stack — CP62 Mobile Backend.

    Render templates từ `stacks/fastapi/core/cp62_mobile_backend/`
    để sinh mobile backend code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/core/`.

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
        """Emit mobile backend code cho FastAPI.

        Sinh các files:
        - push_service.py: FCM/APNs push notification service
        - push_router.py: Push notification API routes
        - deep_link_resolver.py: Deep link pattern matching và resolution
        - mobile_auth_router.py: OAuth2 mobile auth routes
        - ota_router.py: OTA update check endpoint
        - device_service.py: Device registration service

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
            ("push_service.py.jinja2", "app/services/push_service.py"),
            ("push_router.py.jinja2", "app/api/push_router.py"),
            ("deep_link_resolver.py.jinja2", "app/services/deep_link_resolver.py"),
            ("mobile_auth_router.py.jinja2", "app/api/mobile_auth_router.py"),
            ("ota_router.py.jinja2", "app/api/ota_router.py"),
            ("device_service.py.jinja2", "app/services/device_service.py"),
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
