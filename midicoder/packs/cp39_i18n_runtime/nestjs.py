# coding: utf-8
"""
NestJS Emitter cho CP39: i18n/L10n Runtime.

Module này render Jinja2 templates để sinh i18n runtime code
cho NestJS stack, bao gồm entities, DTOs, services, controllers,
locale formatter, cache, WebSocket gateway, interceptor, và module.

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
    CacheConfig,
    DiscoverSource,
    LocaleConfig,
    PluralRule,
    TranslationEntry,
)
from midicoder.packs.cp39_i18n_runtime.parser import I18nRuntimeIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "NestJSI18nRuntimeEmitter",
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


class NestJSI18nRuntimeEmitter:
    """Emitter cho NestJS stack — CP39 i18n/L10n Runtime.

    Render templates từ `stacks/nestjs/cp39_i18n_runtime/`
    để sinh i18n runtime code, bao gồm entities, DTOs, services,
    controllers, formatter, cache, gateway, interceptor, và module.

    Ví dụ:
        >>> emitter = NestJSI18nRuntimeEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.

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

    def emit(
        self,
        ir: I18nRuntimeIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit i18n runtime code cho NestJS.

        Sinh 10 files:
        - translation.entity.ts
        - locale.entity.ts
        - translation.dto.ts
        - translation.service.ts
        - translation.controller.ts
        - locale-formatter.service.ts
        - i18n-cache.service.ts
        - i18n.gateway.ts
        - i18n.interceptor.ts
        - i18n.module.ts

        Args:
            ir: I18nRuntimeIR chứa locales, translations, cache_config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # translation.entity.ts
        if self._template_exists("translation.entity.ts.jinja2"):
            content = self._render("translation.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/entities/translation.entity.ts",
                content=content,
            ))

        # locale.entity.ts
        if self._template_exists("locale.entity.ts.jinja2"):
            content = self._render("locale.entity.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/entities/locale.entity.ts",
                content=content,
            ))

        # translation.dto.ts
        if self._template_exists("translation.dto.ts.jinja2"):
            content = self._render("translation.dto.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/dtos/translation.dto.ts",
                content=content,
            ))

        # translation.service.ts
        if self._template_exists("translation.service.ts.jinja2"):
            content = self._render("translation.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/services/translation.service.ts",
                content=content,
            ))

        # translation.controller.ts
        if self._template_exists("translation.controller.ts.jinja2"):
            content = self._render("translation.controller.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/controllers/translation.controller.ts",
                content=content,
            ))

        # locale-formatter.service.ts
        if self._template_exists("locale-formatter.service.ts.jinja2"):
            content = self._render("locale-formatter.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/services/locale-formatter.service.ts",
                content=content,
            ))

        # i18n-cache.service.ts
        if self._template_exists("i18n-cache.service.ts.jinja2"):
            content = self._render("i18n-cache.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/services/i18n-cache.service.ts",
                content=content,
            ))

        # i18n.gateway.ts
        if self._template_exists("i18n.gateway.ts.jinja2"):
            content = self._render("i18n.gateway.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/gateways/i18n.gateway.ts",
                content=content,
            ))

        # i18n.interceptor.ts
        if self._template_exists("i18n.interceptor.ts.jinja2"):
            content = self._render("i18n.interceptor.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/interceptors/i18n.interceptor.ts",
                content=content,
            ))

        # i18n.module.ts
        if self._template_exists("i18n.module.ts.jinja2"):
            content = self._render("i18n.module.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/i18n/i18n.module.ts",
                content=content,
            ))

        return files

    def _build_context(self, ir: I18nRuntimeIR) -> dict[str, Any]:
        """Xây dựng template context từ I18nRuntimeIR.

        Args:
            ir: I18nRuntimeIR input.

        Returns:
            Dict context cho Jinja2.
        """
        locales_list = [loc.to_dict() for loc in ir.locales]
        translations_list = [t.to_dict() for t in ir.translations]

        return {
            # Data từ IR
            "locales": locales_list,
            "translations": translations_list,
            "locale_count": len(ir.locales),
            "translation_count": len(ir.translations),
            "cache_config": ir.cache_config.to_dict() if ir.cache_config else None,
            # Enum values để template reference
            "plural_rules": [
                PluralRule.SINGULAR.value,
                PluralRule.PLURAL.value,
            ],
            "cache_backends": [
                CacheBackend.MEMORY.value,
                CacheBackend.REDIS.value,
            ],
            # Namespace list từ translations
            "namespaces": list({t.namespace for t in ir.translations}),
            # Default locale
            "default_locale": next(
                (loc.code for loc in ir.locales if loc.is_default),
                "en",
            ),
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
                ErrorCode.CP39_TEMPLATE_NOT_FOUND,
                template=template_name,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.CP39_RENDER_FAILED,
                template=template_name,
                reason=f"Render template thất bại {template_name}: {e}",
            )
