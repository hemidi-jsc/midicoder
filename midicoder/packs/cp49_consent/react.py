# coding: utf-8
"""
React Emitter cho CP49: Consent & Preference Management (Frontend).

Module này render Jinja2 templates để sinh consent management infrastructure
cho React stack, bao gồm:
- PrivacyCenter.tsx: Component chính hiển thị trung tâm quyền riêng tư
- CookieBanner.tsx: Banner thông báo và thu thập đồng ý cookie
- ConsentManager.tsx: Quản lý các bản ghi đồng ý của user
- CommunicationPreferences.tsx: Cài đặt sở thích truyền thông
- useConsent.ts: Custom hook để quản lý trạng thái consent

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp49_consent.parser import ConsentIR
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


__all__ = [
    "ReactConsentEmitter",
]


class ReactConsentEmitter:
    """Emitter cho React stack — CP49 Consent & Preference Management.

    Render templates từ `stacks/react/cp49_consent/`
    để sinh consent management frontend components.

    Ví dụ:
        >>> emitter = ReactConsentEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = ConsentIR(policies=[...], consents=[...])
        >>> files = emitter.emit(ir)
    """

    _TEMPLATE_MAP: dict[str, str] = {
        "PrivacyCenter.tsx.jinja2": "src/consent/PrivacyCenter.tsx",
        "CookieBanner.tsx.jinja2": "src/consent/CookieBanner.tsx",
        "ConsentManager.tsx.jinja2": "src/consent/ConsentManager.tsx",
        "CommunicationPreferences.tsx.jinja2": "src/consent/CommunicationPreferences.tsx",
        "useConsent.ts.jinja2": "src/consent/hooks/useConsent.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/`.

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

    def emit(self, ir: ConsentIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit consent management infrastructure cho React.

        Sinh 5 files:
        - PrivacyCenter.tsx
        - CookieBanner.tsx
        - ConsentManager.tsx
        - CommunicationPreferences.tsx
        - useConsent.ts

        Args:
            ir: ConsentIR chứa consent policies, records, config.
            context: Context bổ sung (optional).

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        policies_list = [p.to_dict() for p in ir.policies]
        consents_list = [c.to_dict() for c in ir.consents]

        template_context: dict[str, Any] = {
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
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason=f"Render thất bại {template_name}: {e}",
            )
