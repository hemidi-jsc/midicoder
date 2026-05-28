# coding: utf-8
"""
Angular Emitter cho CP49: Consent & Preference Management (Frontend).

Module này render Jinja2 templates để sinh consent management infrastructure
cho Angular stack, bao gồm:
- privacy-center.component.ts: Component chính hiển thị trung tâm quyền riêng tư
- cookie-banner.component.ts: Banner thông báo và thu thập đồng ý cookie
- consent-manager.component.ts: Quản lý các bản ghi đồng ý của user
- consent.service.ts: Injectable service gọi API consent
- consent.store.ts: Store quản lý trạng thái consent

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_consent.parser import ConsentIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularConsentEmitter",
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


class AngularConsentEmitter:
    """Emitter cho Angular stack — CP49 Consent & Preference Management.

    Render templates từ `stacks/angular/cp_full_consent/`
    để sinh consent management infrastructure cho Angular.

    Ví dụ:
        >>> emitter = AngularConsentEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = ConsentIR(policies=[...], consents=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "privacy-center.component.ts.jinja2": "src/consent/privacy-center.component.ts",
        "cookie-banner.component.ts.jinja2": "src/consent/cookie-banner.component.ts",
        "consent-manager.component.ts.jinja2": "src/consent/consent-manager.component.ts",
        "consent.service.ts.jinja2": "src/consent/consent.service.ts",
        "consent.store.ts.jinja2": "src/consent/consent.store.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir  # stack_dir đã là .../cp_full_consent

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.MDC-F31_CONSENT_RECORD_NOT_FOUND,
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
        """Emit consent management infrastructure cho Angular.

        Sinh 5 files:
        - privacy-center.component.ts
        - cookie-banner.component.ts
        - consent-manager.component.ts
        - consent.service.ts
        - consent.store.ts

        Args:
            ir: ConsentIR chứa consent policies, records, config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        for template_name, output_path in self._TEMPLATE_MAP.items():
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
                ErrorCode.MDC-F31_CONSENT_RECORD_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-F31_CONSENT_RECORD_NOT_FOUND,
                reason=f"Render template thất bại {template_name}: {e}",
            )
