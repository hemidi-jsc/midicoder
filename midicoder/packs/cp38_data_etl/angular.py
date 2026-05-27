# coding: utf-8
"""
Angular Emitter cho CP38: Data Import/Export/ETL (Frontend).

Module này render Jinja2 templates để sinh data import/export/ETL UI
cho Angular stack, bao gồm:
- import-wizard.component.ts: Component hướng dẫn import dữ liệu
- export-dialog.component.ts: Dialog export dữ liệu
- import.service.ts: Injectable service cho import
- export.service.ts: Injectable service cho export
- job-status.component.ts: Component hiển thị trạng thái job

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp38_data_etl.parser import ETLIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularETLEmitter",
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


class AngularETLEmitter:
    """Emitter cho Angular stack — CP38 Data Import/Export/ETL.

    Render templates từ `stacks/angular/cp38_data_etl/`
    để sinh data import/export/ETL UI components cho Angular.

    Ví dụ:
        >>> emitter = AngularETLEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = ETLIR(import_jobs=[...], export_jobs=[...], etl_jobs=[...])
        >>> files = emitter.emit(ir)
    """

    # Mapping template name -> output path
    _TEMPLATE_MAP: dict[str, str] = {
        "import-wizard.component.ts.jinja2": "src/app/etl/components/import-wizard.component.ts",
        "export-dialog.component.ts.jinja2": "src/app/etl/components/export-dialog.component.ts",
        "import.service.ts.jinja2": "src/app/etl/services/import.service.ts",
        "export.service.ts.jinja2": "src/app/etl/services/export.service.ts",
        "job-status.component.ts.jinja2": "src/app/etl/components/job-status.component.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

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

    def emit(self, ir: ETLIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit data import/export/ETL UI cho Angular.

        Sinh 5 files:
        - import-wizard.component.ts
        - export-dialog.component.ts
        - import.service.ts
        - export.service.ts
        - job-status.component.ts

        Args:
            ir: ETLIR chứa import jobs, export jobs, ETL jobs.
            context: Context bổ sung (optional), vd: ui_framework.

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        # Xây dựng context từ ETLIR
        import_jobs_list = [j.to_dict() for j in ir.import_jobs]
        export_jobs_list = [j.to_dict() for j in ir.export_jobs]
        etl_jobs_list = [j.to_dict() for j in ir.etl_jobs]

        # Import job keys flat list
        import_job_keys = [j.job_key for j in ir.import_jobs]

        # Export job keys flat list
        export_job_keys = [j.job_key for j in ir.export_jobs]

        # ETL job keys flat list
        etl_job_keys = [j.job_key for j in ir.etl_jobs]

        # Target entities cho import
        target_entities = list({j.target_entity for j in ir.import_jobs})

        # Source entities cho export
        source_entities = list({j.entity for j in ir.export_jobs})

        # Có bulk config không
        has_bulk_config = ir.bulk_config is not None

        template_context: dict[str, Any] = {
            # Jobs
            "import_jobs": import_jobs_list,
            "export_jobs": export_jobs_list,
            "etl_jobs": etl_jobs_list,
            # Counts
            "import_job_count": len(ir.import_jobs),
            "export_job_count": len(ir.export_jobs),
            "etl_job_count": len(ir.etl_jobs),
            # Flat key lists
            "import_job_keys": import_job_keys,
            "export_job_keys": export_job_keys,
            "etl_job_keys": etl_job_keys,
            # Entities
            "target_entities": target_entities,
            "source_entities": source_entities,
            # Bulk
            "has_bulk_config": has_bulk_config,
            "bulk_config": ir.bulk_config.to_dict() if ir.bulk_config else None,
            # Extra context
            **extra_context,
        }

        result: list[dict[str, str]] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
            if self._template_exists(template_name):
                content = self._render(template_name, template_context)
                result.append({"path": output_path, "content": content})

        return result

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
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP38_RENDER_FAILED,
                template=template_name,
                reason=f"Render thất bại {template_name}: {e}",
            )
