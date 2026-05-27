# coding: utf-8
"""
FastAPI Emitter cho CP49: Consent & Preference Management.

Module này render Jinja2 templates để sinh consent management code
cho FastAPI stack, bao gồm models, schemas, service, router,
cookie banner service, và consent middleware.

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp49_consent.parser import ConsentIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIConsentEmitter",
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


class FastAPIConsentEmitter:
    """Emitter cho FastAPI stack — CP49 Consent & Preference Management.

    Render templates từ `stacks/fastapi/cp49_consent/`
    để sinh consent management code.

    Ví dụ:
        >>> emitter = FastAPIConsentEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir  # stack_dir đã là .../cp49_consent

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
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
        ir: ConsentIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit consent management code cho FastAPI.

        Sinh 6 files:
        - consent_models.py
        - consent_schemas.py
        - consent_service.py
        - consent_router.py
        - cookie_banner_service.py
        - consent_middleware.py

        Args:
            ir: ConsentIR chứa consent policies, records, config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        templates = [
            ("consent_models.py.jinja2", "app/models/consent_models.py"),
            ("consent_schemas.py.jinja2", "app/schemas/consent_schemas.py"),
            ("consent_service.py.jinja2", "app/services/consent_service.py"),
            ("consent_router.py.jinja2", "app/api/consent_router.py"),
            ("cookie_banner_service.py.jinja2", "app/services/cookie_banner_service.py"),
            ("consent_middleware.py.jinja2", "app/middleware/consent_middleware.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: ConsentIR) -> dict[str, Any]:
        """Xây dựng template context từ ConsentIR.

        Args:
            ir: ConsentIR input.

        Returns:
            Dict context cho Jinja2.
        """
        policies_list = [p.to_dict() for p in ir.policies]
        consents_list = [c.to_dict() for c in ir.consents]

        return {
            "consent_policies": policies_list,
            "consent_policies_list": policies_list,
            "consent_records": consents_list,
            "consent_records_list": consents_list,
            "cookie_categories": ir.cookie_categories,
            "cookie_categories_list": ir.cookie_categories,
            "comm_channels": ir.comm_channels,
            "comm_channels_list": ir.comm_channels,
            "policy_count": len(ir.policies),
            "consent_count": len(ir.consents),
            "use_audit": ir.use_audit,
            "use_retention": ir.use_retention,
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
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
