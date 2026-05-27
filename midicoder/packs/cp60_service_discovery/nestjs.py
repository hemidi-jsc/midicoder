# coding: utf-8
"""
NestJS Emitter cho CP60: Service Discovery & Config Center.

Module này render Jinja2 templates để sinh service discovery code
cho NestJS stack, bao gồm entities, DTOs, service, controller,
và NestJS module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp60_service_discovery.parser import ServiceDiscoveryIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSServiceDiscoveryEmitter",
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


class NestJSServiceDiscoveryEmitter:
    """Emitter cho NestJS stack — CP60 Service Discovery & Config Center.

    Render templates từ `stacks/nestjs/cp60_service_discovery/`
    để sinh service discovery code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp60_service_discovery"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
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
        ir: ServiceDiscoveryIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit service discovery code cho NestJS.

        Sinh 5 files:
        - discovery.entity.ts
        - discovery.dto.ts
        - discovery.service.ts
        - discovery.controller.ts
        - discovery.module.ts

        Args:
            ir: ServiceDiscoveryIR chứa service instances, registries, configs.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("discovery.entity.ts.jinja2", "src/discovery/entities/discovery.entity.ts"),
            ("discovery.dto.ts.jinja2", "src/discovery/dtos/discovery.dto.ts"),
            ("discovery.service.ts.jinja2", "src/discovery/services/discovery.service.ts"),
            ("discovery.controller.ts.jinja2", "src/discovery/controllers/discovery.controller.ts"),
            ("discovery.module.ts.jinja2", "src/discovery/discovery.module.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: ServiceDiscoveryIR) -> dict[str, Any]:
        """Xây dựng template context từ ServiceDiscoveryIR."""
        instances_list = [i.to_dict() for i in ir.instances]
        registries_list = [r.to_dict() for r in ir.registries]
        return {
            "instances": instances_list,
            "registries": registries_list,
            "configs": [c.to_dict() for c in ir.configs],
            "watches": [w.to_dict() for w in ir.watches],
            "load_balancers": [lb.to_dict() for lb in ir.load_balancers],
            "instance_count": len(ir.instances),
            "registry_count": len(ir.registries),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.DSL_LOAD_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
