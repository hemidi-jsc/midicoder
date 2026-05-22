# coding: utf-8
"""
NestJS Emitter cho CP38: Data Import/Export/ETL.

Module này render Jinja2 templates để sinh data import/export/ETL code
cho NestJS stack, bao gồm entities, DTOs, services, controllers,
bulk processor, và module.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp38_data_etl.models import (
    ExtractSource,
    ImportFormat,
    JobStatus,
    LoadMode,
    TransformType,
)
from midicoder.emitters.core.cp38_data_etl.parser import ETLIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSETLEmitter",
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


class NestJSETLEmitter:
    """Emitter cho NestJS stack — CP38 Data Import/Export/ETL.

    Render templates từ `stacks/nestjs/core/cp38_data_etl/`
    để sinh data import/export/ETL code, bao gồm entities, DTOs,
    services, controllers, bulk processor, và NestJS module.

    Ví dụ:
        >>> emitter = NestJSETLEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/core/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại (CP38_TEMPLATE_NOT_FOUND).
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp38_data_etl"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP38_TEMPLATE_NOT_FOUND,
                template=str(self.template_dir),
                message=f"Template directory không tìm thấy: {self.template_dir}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: ETLIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit data import/export/ETL code cho NestJS.

        Sinh 9 files:
        - import.entity.ts
        - import.dto.ts
        - import.service.ts
        - export.service.ts
        - etl.service.ts
        - import.controller.ts
        - export.controller.ts
        - bulk-processor.service.ts
        - etl.module.ts

        Args:
            ir: ETLIR chứa import jobs, export jobs, ETL jobs, bulk config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # import.entity.ts
        if self._template_exists("import.entity.ts.jinja2"):
            content = self._render("import.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/entities/import.entity.ts",
                content=content,
            ))

        # import.dto.ts
        if self._template_exists("import.dto.ts.jinja2"):
            content = self._render("import.dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/dtos/import.dto.ts",
                content=content,
            ))

        # import.service.ts
        if self._template_exists("import.service.ts.jinja2"):
            content = self._render("import.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/services/import.service.ts",
                content=content,
            ))

        # export.service.ts
        if self._template_exists("export.service.ts.jinja2"):
            content = self._render("export.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/services/export.service.ts",
                content=content,
            ))

        # etl.service.ts
        if self._template_exists("etl.service.ts.jinja2"):
            content = self._render("etl.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/services/etl.service.ts",
                content=content,
            ))

        # import.controller.ts
        if self._template_exists("import.controller.ts.jinja2"):
            content = self._render("import.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/controllers/import.controller.ts",
                content=content,
            ))

        # export.controller.ts
        if self._template_exists("export.controller.ts.jinja2"):
            content = self._render("export.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/controllers/export.controller.ts",
                content=content,
            ))

        # bulk-processor.service.ts
        if self._template_exists("bulk-processor.service.ts.jinja2"):
            content = self._render("bulk-processor.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/services/bulk-processor.service.ts",
                content=content,
            ))

        # etl.module.ts
        if self._template_exists("etl.module.ts.jinja2"):
            content = self._render("etl.module.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/etl/etl.module.ts",
                content=content,
            ))

        return files

    def _build_context(self, ir: ETLIR) -> dict[str, Any]:
        """Xây dựng template context từ ETLIR.

        Args:
            ir: ETLIR input.

        Returns:
            Dict context cho Jinja2.
        """
        return {
            # Data từ IR
            "import_jobs": [j.to_dict() for j in ir.import_jobs],
            "export_jobs": [j.to_dict() for j in ir.export_jobs],
            "etl_jobs": [j.to_dict() for j in ir.etl_jobs],
            "bulk_config": ir.bulk_config.to_dict() if ir.bulk_config else None,
            # Counts
            "import_job_count": len(ir.import_jobs),
            "export_job_count": len(ir.export_jobs),
            "etl_job_count": len(ir.etl_jobs),
            # Enum values để template reference
            "import_formats": [f.value for f in ImportFormat],
            "job_statuses": [s.value for s in JobStatus],
            "transform_types": [t.value for t in TransformType],
            "extract_sources": [s.value for s in ExtractSource],
            "load_modes": [m.value for m in LoadMode],
        }

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một template.

        Args:
            template_name: Tên template file.
            context: Template context.

        Returns:
            Rendered string.

        Raises:
            MidicoderError: Nếu template không tìm thấy hoặc render lỗi.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.CP38_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP38_RENDER_FAILED,
                template=template_name,
                reason=f"Render template thất bại {template_name}: {e}",
            )
