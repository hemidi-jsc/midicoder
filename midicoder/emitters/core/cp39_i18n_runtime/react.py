# coding: utf-8
"""
React Emitter cho CP39: i18n/L10n Runtime (Frontend).

Module này render Jinja2 templates để sinh i18n runtime infrastructure
cho React stack, bao gồm:
- useTranslation.ts: Custom hook để translate key
- useLocale.ts: Custom hook để switch locale
- useFormattedValue.ts: Custom hook để format date/number/currency
- TranslationSyncWorker.ts: Service worker cho real-time sync translations
- I18nRuntimeProvider.tsx: React Context Provider cho i18n runtime

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp39_i18n_runtime.models import (
    CacheBackend,
    PluralRule,
)
from midicoder.emitters.core.cp39_i18n_runtime.parser import I18nRuntimeIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "ReactI18nRuntimeEmitter",
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


class ReactI18nRuntimeEmitter:
    """Emitter cho React stack — CP39 i18n/L10n Runtime.

    Render templates từ `stacks/react/core/cp39_i18n_runtime/`
    để sinh i18n runtime infrastructure components.

    Ví dụ:
        >>> emitter = ReactI18nRuntimeEmitter(stack_dir="/path/to/stacks/react/core")
        >>> ir = I18nRuntimeIR(locales=[...], translations=[...])
        >>> files = emitter.emit(ir)
    """

    # Mapping template name -> output path
    _TEMPLATE_MAP: dict[str, str] = {
        "useTranslation.ts.jinja2": "src/i18n/hooks/useTranslation.ts",
        "useLocale.ts.jinja2": "src/i18n/hooks/useLocale.ts",
        "useFormattedValue.ts.jinja2": "src/i18n/hooks/useFormattedValue.ts",
        "TranslationSyncWorker.ts.jinja2": "src/i18n/workers/TranslationSyncWorker.ts",
        "I18nRuntimeProvider.tsx.jinja2": "src/i18n/components/I18nRuntimeProvider.tsx",
    }

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/react/core/`.

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
        """Emit i18n runtime infrastructure cho React.

        Sinh 5 files:
        - useTranslation.ts
        - useLocale.ts
        - useFormattedValue.ts
        - TranslationSyncWorker.ts
        - I18nRuntimeProvider.tsx

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

        # Translation keys flat list
        translation_keys = list({t.key for t in ir.translations})

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
            "translation_keys": translation_keys,
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
