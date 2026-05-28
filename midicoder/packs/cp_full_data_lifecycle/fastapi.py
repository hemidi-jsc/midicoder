# coding: utf-8
"""
FastAPI Emitter cho CP47: Data Retention & Lifecycle Management.

Module này render Jinja2 templates để sinh retention lifecycle code
cho FastAPI stack, bao gồm models, schemas, service, router,
webhook handler, và scheduled tasks.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_data_lifecycle.parser import RetentionIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIRetentionEmitter",
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


class FastAPIRetentionEmitter:
    """Emitter cho FastAPI stack — CP47 Data Retention & Lifecycle Management.

    Render templates từ `stacks/fastapi/cp_full_data_lifecycle/`
    để sinh retention lifecycle code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_full_data_lifecycle"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_POLICY_NOT_FOUND,
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
        ir: RetentionIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit retention lifecycle code cho FastAPI.

        Sinh 6 files:
        - retention_models.py
        - retention_schemas.py
        - retention_service.py
        - retention_router.py
        - retention_webhook.py
        - retention_tasks.py

        Args:
            ir: RetentionIR chứa policies và config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("retention_models.py.jinja2", "app/models/retention_models.py"),
            ("retention_schemas.py.jinja2", "app/schemas/retention_schemas.py"),
            ("retention_service.py.jinja2", "app/services/retention_service.py"),
            ("retention_router.py.jinja2", "app/api/retention_router.py"),
            ("retention_webhook.py.jinja2", "app/api/retention_webhook.py"),
            ("retention_tasks.py.jinja2", "app/services/retention_tasks.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: RetentionIR) -> dict[str, Any]:
        """Xây dựng template context từ RetentionIR."""
        return {
            "policies": ir.policies,
            "policy_count": len(ir.policies),
            "enable_archival": ir.enable_archival,
            "enable_purge": ir.enable_purge,
            "enable_erasure": ir.enable_erasure,
            "enable_scheduler": ir.enable_scheduler,
            "default_retention_days": ir.default_retention_days,
            "batch_size": ir.batch_size,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_POLICY_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_SCAN_FAILED,
                reason=f"Render template thất bại {template_name}: {e}",
            )
