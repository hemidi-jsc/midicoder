# coding: utf-8
"""
NestJS Emitter cho CP58: Data Encryption at Rest.

Module này render Jinja2 templates để sinh encryption code
cho NestJS stack, bao gồm entities, DTOs, service, controller,
key rotation scheduler, và NestJS module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp58_encryption.parser import EncryptionIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSEncryptionEmitter",
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


class NestJSEncryptionEmitter:
    """Emitter cho NestJS stack — CP58 Data Encryption at Rest.

    Render templates từ `stacks/nestjs/core/cp58_encryption/`
    để sinh encryption code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp58_encryption"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTION_CONFIG_NOT_FOUND,
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
        ir: EncryptionIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit encryption code cho NestJS.

        Sinh 6 files:
        - encryption.entity.ts
        - encryption.dto.ts
        - encryption.service.ts
        - encryption.controller.ts
        - key-rotation.scheduler.ts
        - encryption.module.ts

        Args:
            ir: EncryptionIR chứa encryption configs và policies.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("encryption.entity.ts.jinja2", "src/encryption/entities/encryption.entity.ts"),
            ("encryption.dto.ts.jinja2", "src/encryption/dtos/encryption.dto.ts"),
            ("encryption.service.ts.jinja2", "src/encryption/services/encryption.service.ts"),
            ("encryption.controller.ts.jinja2", "src/encryption/controllers/encryption.controller.ts"),
            ("key-rotation.scheduler.ts.jinja2", "src/encryption/schedulers/key-rotation.scheduler.ts"),
            ("encryption.module.ts.jinja2", "src/encryption/encryption.module.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: EncryptionIR) -> dict[str, Any]:
        """Xây dựng template context từ EncryptionIR."""
        configs_list = [c.to_dict() for c in ir.configs]
        keys_list = [k.to_dict() for k in ir.keys]
        return {
            "configs": configs_list,
            "fields": [f.to_dict() for f in ir.fields],
            "keys": keys_list,
            "policies": [p.to_dict() for p in ir.policies],
            "config_count": len(ir.configs),
            "field_count": len(ir.fields),
            "key_count": len(ir.keys),
            "policy_count": len(ir.policies),
            "default_algorithm": ir.default_algorithm.value,
            "default_key_management": ir.default_key_management.value,
            "enable_auto_encrypt": ir.enable_auto_encrypt,
            "enable_auto_decrypt": ir.enable_auto_decrypt,
            "enable_key_rotation": ir.enable_key_rotation,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP58_ENCRYPTION_CONFIG_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP58_INVALID_ENCRYPTION_CONFIG,
                reason=f"Render template thất bại {template_name}: {e}",
            )
