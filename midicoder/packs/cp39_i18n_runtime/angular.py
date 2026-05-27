# coding: utf-8
"""
Angular Emitter cho CP39: i18n/L10n Runtime (Frontend).

Module này render Jinja2 templates để sinh i18n runtime infrastructure
cho Angular stack, bao gồm:
- i18n-runtime.service.ts: Injectable service quản lý translation và locale switch
- locale-directive.ts: Attribute directive format date/number/currency inline
- translation-sync.service.ts: WebSocket client nhận real-time translation update
- locale-formatter.pipe.ts: Pipe format giá trị theo locale

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp39_i18n_runtime.models import (
    CacheBackend,
    PluralRule,
)
from midicoder.packs.cp39_i18n_runtime.parser import I18nRuntimeIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "AngularI18nRuntimeEmitter",
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


class AngularI18nRuntimeEmitter:
    """Emitter cho Angular stack — CP39 i18n/L10n Runtime.

    Render templates từ `stacks/angular/cp39_i18n_runtime/`
    để sinh i18n runtime infrastructure cho Angular.

    Ví dụ:
        >>> emitter = AngularI18nRuntimeEmitter(stack_dir="/path/to/stacks/angular/core")
        >>> ir = I18nRuntimeIR(locales=[...], translations=[...])
        >>> files = emitter.emit(ir)
    """

    # Mapping template name -> output path
    _TEMPLATE_MAP: dict[str, str] = {
        "i18n-runtime.service.ts.jinja2": "src/app/core/i18n/i18n-runtime.service.ts",
        "locale-directive.ts.jinja2": "src/app/core/i18n/locale-directive.ts",
        "translation-sync.service.ts.jinja2": "src/app/core/i18n/translation-sync.service.ts",
        "locale-formatter.pipe.ts.jinja2": "src/app/core/i18n/locale-formatter.pipe.ts",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/angular/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại (CP39_TEMPLATE_NOT_FOUND).
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp39_i18n_runtime"

        if not self.template_dir.exists():
            EM.raise_error(
                ErrorCode.CP39_TEMPLATE_NOT_FOUND,
                template=str(self.template_dir),
                message=f"Template directory không tìm thấy: {self.template_dir}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, ir: I18nRuntimeIR, context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Emit i18n runtime infrastructure cho Angular.

        Sinh 4 files:
        - i18n-runtime.service.ts
        - locale-directive.ts
        - translation-sync.service.ts
        - locale-formatter.pipe.ts

        Args:
            ir: I18nRuntimeIR chứa locales, translations, cache_config.
            context: Context bổ sung (optional), vd: ui_framework.

        Returns:
            List của {path, content} cho mỗi file.
        """
        extra_context = context or {}

        locales_list = [loc.to_dict() for loc in ir.locales]
        translations_list = [t.to_dict() for t in ir.translations]

        # Locale codes flat list cho TypeScript union type
        locale_codes = [loc.code for loc in ir.locales]

        # Namespace list
        namespaces = list({t.namespace for t in ir.translations})

        # Default locale
        default_locale = next(
            (loc.code for loc in ir.locales if loc.is_default),
            "en",
        )

        template_context: dict[str, Any] = {
            # Data
            "locales": locales_list,
            "translations": translations_list,
            "locale_count": len(ir.locales),
            "translation_count": len(ir.translations),
            "locale_codes": locale_codes,
            "namespaces": namespaces,
            "default_locale": default_locale,
            # Enum values
            "plural_rules": [
                PluralRule.SINGULAR.value,
                PluralRule.PLURAL.value,
            ],
            "cache_backends": [
                CacheBackend.MEMORY.value,
                CacheBackend.REDIS.value,
            ],
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
                ErrorCode.CP39_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP39_RENDER_FAILED,
                template=template_name,
                reason=f"Render thất bại {template_name}: {e}",
            )
