# coding: utf-8
"""
FastAPI Emitter cho CP38: Data Import/Export/ETL.

Module này render Jinja2 templates để sinh data import/export/ETL code
cho FastAPI stack, bao gồm models, schemas, services, routers,
parsers, và bulk worker.

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
    "FastAPIETLEmitter",
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


class FastAPIETLEmitter:
    """Emitter cho FastAPI stack — CP38 Data Import/Export/ETL.

    Render templates từ `stacks/fastapi/core/cp38_data_etl/`
    để sinh data import/export/ETL code, bao gồm models, schemas,
    services, routers, parsers, và bulk worker.

    Ví dụ:
        >>> emitter = FastAPIETLEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/core/`.

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
        """Emit data import/export/ETL code cho FastAPI.

        Sinh 11 files:
        - __init__.py
        - import_models.py
        - import_schemas.py
        - import_service.py
        - export_service.py
        - etl_service.py
        - import_router.py
        - export_router.py
        - bulk_worker.py
        - csv_parser.py
        - json_parser.py

        Args:
            ir: ETLIR chứa import jobs, export jobs, ETL jobs, bulk config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # __init__.py
        if self._template_exists("__init__.py.jinja2"):
            content = self._render("__init__.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/__init__.py",
                content=content,
            ))

        # import_models.py
        if self._template_exists("import_models.py.jinja2"):
            content = self._render("import_models.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/models/import_models.py",
                content=content,
            ))

        # import_schemas.py
        if self._template_exists("import_schemas.py.jinja2"):
            content = self._render("import_schemas.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/schemas/import_schemas.py",
                content=content,
            ))

        # import_service.py
        if self._template_exists("import_service.py.jinja2"):
            content = self._render("import_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/services/import_service.py",
                content=content,
            ))

        # export_service.py
        if self._template_exists("export_service.py.jinja2"):
            content = self._render("export_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/services/export_service.py",
                content=content,
            ))

        # etl_service.py
        if self._template_exists("etl_service.py.jinja2"):
            content = self._render("etl_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/services/etl_service.py",
                content=content,
            ))

        # import_router.py
        if self._template_exists("import_router.py.jinja2"):
            content = self._render("import_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/routers/import_router.py",
                content=content,
            ))

        # export_router.py
        if self._template_exists("export_router.py.jinja2"):
            content = self._render("export_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/routers/export_router.py",
                content=content,
            ))

        # bulk_worker.py
        if self._template_exists("bulk_worker.py.jinja2"):
            content = self._render("bulk_worker.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/workers/bulk_worker.py",
                content=content,
            ))

        # csv_parser.py
        if self._template_exists("csv_parser.py.jinja2"):
            content = self._render("csv_parser.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/parsers/csv_parser.py",
                content=content,
            ))

        # json_parser.py
        if self._template_exists("json_parser.py.jinja2"):
            content = self._render("json_parser.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/etl/parsers/json_parser.py",
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
