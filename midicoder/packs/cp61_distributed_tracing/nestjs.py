# coding: utf-8
"""
NestJS Emitter cho CP61: Distributed Tracing & Correlation ID.

Module này render Jinja2 templates để sinh distributed tracing code
cho NestJS stack, bao gồm tracing module, correlation interceptor,
span decorator, và log correlation setup.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp61_distributed_tracing.parser import TracingIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSTracingEmitter",
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


class NestJSTracingEmitter:
    """Emitter cho NestJS stack — CP61 Distributed Tracing & Correlation ID.

    Render templates từ `stacks/nestjs/cp61_distributed_tracing/`
    để sinh distributed tracing code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp61_distributed_tracing"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
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
        ir: TracingIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit distributed tracing code cho NestJS.

        Sinh 5 files:
        - tracing.module.ts
        - correlation.interceptor.ts
        - span.decorator.ts
        - log-correlation.service.ts
        - tracing.config.ts

        Args:
            ir: TracingIR chứa trace configs và correlation settings.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("tracing.module.ts.jinja2", "src/tracing/tracing.module.ts"),
            ("correlation.interceptor.ts.jinja2", "src/tracing/correlation.interceptor.ts"),
            ("span.decorator.ts.jinja2", "src/tracing/span.decorator.ts"),
            ("log-correlation.service.ts.jinja2", "src/tracing/log-correlation.service.ts"),
            ("tracing.config.ts.jinja2", "src/config/tracing.config.ts"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: TracingIR) -> dict[str, Any]:
        """Xây dựng template context từ TracingIR."""
        configs_list = [c.to_dict() for c in ir.configs]
        fields_list = [f.to_dict() for f in ir.correlation_fields]
        spans_list = [s.to_dict() for s in ir.spans]
        exporters_list = [e.to_dict() for e in ir.exporters]
        log_corr_list = [l.to_dict() for l in ir.log_correlation]

        return {
            "configs": configs_list,
            "correlation_fields": fields_list,
            "spans": spans_list,
            "exporters": exporters_list,
            "log_correlation": log_corr_list,
            "config_count": len(ir.configs),
            "field_count": len(ir.correlation_fields),
            "span_count": len(ir.spans),
            "exporter_count": len(ir.exporters),
            "log_corr_count": len(ir.log_correlation),
            "has_log_correlation": len(ir.log_correlation) > 0,
            "has_exporters": len(ir.exporters) > 0,
            "default_service_name": ir.configs[0].service_name if ir.configs else "unknown",
            "default_exporter": ir.exporters[0].type.value if ir.exporters else "otel",
            "default_endpoint": ir.exporters[0].endpoint if ir.exporters else "http://localhost:4318",
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.INVALID_CONFIG,
                reason=f"Render template thất bại {template_name}: {e}",
            )
