# coding: utf-8
"""
FastAPI Emitter cho CP44: Bulk Operations Engine.

Module này render Jinja2 templates để sinh bulk operations code
cho FastAPI stack, bao gồm models, schemas, service, router,
worker, DLQ worker, và SSE endpoint.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp44_bulk_ops.parser import BulkIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIBulkOpsEmitter",
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


class FastAPIBulkOpsEmitter:
    """Emitter cho FastAPI stack — CP44 Bulk Operations Engine.

    Render templates từ `stacks/fastapi/core/cp44_bulk_ops/`
    để sinh bulk operations code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
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
        ir: BulkIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit bulk operations code cho FastAPI.

        Sinh 7 files:
        - bulk_models.py
        - bulk_schemas.py
        - bulk_service.py
        - bulk_router.py
        - bulk_worker.py
        - bulk_dlq_worker.py
        - bulk_sse.py

        Args:
            ir: BulkIR chứa bulk jobs và config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("bulk_models.py.jinja2", "app/models/bulk_models.py"),
            ("bulk_schemas.py.jinja2", "app/schemas/bulk_schemas.py"),
            ("bulk_service.py.jinja2", "app/services/bulk_service.py"),
            ("bulk_router.py.jinja2", "app/api/bulk_router.py"),
            ("bulk_worker.py.jinja2", "app/workers/bulk_worker.py"),
            ("bulk_dlq_worker.py.jinja2", "app/workers/bulk_dlq_worker.py"),
            ("bulk_sse.py.jinja2", "app/api/bulk_sse.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: BulkIR) -> dict[str, Any]:
        """Xây dựng template context từ BulkIR."""
        jobs_list = [j.to_dict() for j in ir.jobs]
        return {
            "bulk_jobs": jobs_list,
            "job_count": len(ir.jobs),
            "default_chunk_size": ir.default_chunk_size,
            "default_concurrency": ir.default_concurrency,
            "default_max_retries": ir.default_max_retries,
            "default_retry_strategy": ir.default_retry_strategy.value,
            "default_timeout": ir.default_timeout,
            "dlq_enabled": ir.dlq_enabled,
            "use_events": ir.use_events,
            "use_audit": ir.use_audit,
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
