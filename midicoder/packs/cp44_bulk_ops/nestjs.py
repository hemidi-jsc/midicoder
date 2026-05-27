# coding: utf-8
"""
NestJS Emitter cho CP44: Bulk Operations Engine.

Module này render Jinja2 templates để sinh bulk operations code
cho NestJS stack, bao gồm entity, dto, service, controller,
module, scheduler, và WebSocket gateway.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp44_bulk_ops.parser import BulkIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSBulkOpsEmitter",
]


class NestJSBulkOpsEmitter:
    """Emitter cho NestJS stack — CP44 Bulk Operations Engine."""

    _TEMPLATE_MAP: dict[str, str] = {
        "bulk.entity.ts.jinja2": "src/bulk/entities/bulk.entity.ts",
        "bulk.dto.ts.jinja2": "src/bulk/dtos/bulk.dto.ts",
        "bulk.service.ts.jinja2": "src/bulk/services/bulk.service.ts",
        "bulk.controller.ts.jinja2": "src/bulk/controllers/bulk.controller.ts",
        "bulk.module.ts.jinja2": "src/bulk/bulk.module.ts",
        "bulk.scheduler.ts.jinja2": "src/bulk/schedulers/bulk.scheduler.ts",
        "bulk.gateway.ts.jinja2": "src/bulk/gateways/bulk.gateway.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
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

    def emit(self, ir: BulkIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit bulk operations code cho NestJS.

        Sinh 7 files: entity, dto, service, controller, module, scheduler, gateway.
        """
        extra_context = context or {}
        jobs_list = [j.to_dict() for j in ir.jobs]

        template_context: dict[str, Any] = {
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
            **extra_context,
        }

        result: list[dict[str, str]] = []
        for template_name, output_path in self._TEMPLATE_MAP.items():
            if self._template_exists(template_name):
                content = self._render(template_name, template_context)
                result.append({"path": output_path, "content": content})

        return result

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP44_BULK_JOB_NOT_FOUND,
                reason=f"Render thất bại {template_name}: {e}",
            )
