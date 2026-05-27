# coding: utf-8
"""
FastAPI Emitter cho CP39: i18n/L10n Runtime.

Module này render Jinja2 templates để sinh i18n runtime code
cho FastAPI stack, bao gồm models, schemas, services, routers,
cache layer, auto-discover scanner, WebSocket handler, và middleware.

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
    "FastAPII18nRuntimeEmitter",
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


class FastAPII18nRuntimeEmitter:
    """Emitter cho FastAPI stack — CP39 i18n/L10n Runtime.

    Render templates từ `stacks/fastapi/cp39_i18n_runtime/`
    để sinh i18n runtime code, bao gồm models, schemas, services,
    routers, cache, auto-discover, WebSocket, và middleware.

    Ví dụ:
        >>> emitter = FastAPII18nRuntimeEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(ir, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

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
        """Emit i18n runtime code cho FastAPI.

        Sinh 9 files:
        - models.py
        - schemas.py
        - translation_service.py
        - locale_formatter.py
        - i18n_router.py
        - cache.py
        - discover.py
        - ws.py
        - middleware.py

        Args:
            ir: I18nRuntimeIR chứa locales, translations, cache_config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)

        context = self._build_context(ir)

        files: list[GeneratedFile] = []

        # i18n_models.py
        if self._template_exists("i18n_models.py.jinja2"):
            content = self._render("i18n_models.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/models.py",
                content=content,
            ))

        # i18n_schemas.py
        if self._template_exists("i18n_schemas.py.jinja2"):
            content = self._render("i18n_schemas.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/schemas.py",
                content=content,
            ))

        # i18n_service.py
        if self._template_exists("i18n_service.py.jinja2"):
            content = self._render("i18n_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/services/translation_service.py",
                content=content,
            ))

        # i18n_formatter.py
        if self._template_exists("i18n_formatter.py.jinja2"):
            content = self._render("i18n_formatter.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/services/locale_formatter.py",
                content=content,
            ))

        # i18n_router.py
        if self._template_exists("i18n_router.py.jinja2"):
            content = self._render("i18n_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/routers/i18n_router.py",
                content=content,
            ))

        # i18n_cache.py
        if self._template_exists("i18n_cache.py.jinja2"):
            content = self._render("i18n_cache.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/services/cache.py",
                content=content,
            ))

        # i18n_discover.py
        if self._template_exists("i18n_discover.py.jinja2"):
            content = self._render("i18n_discover.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/services/discover.py",
                content=content,
            ))

        # i18n_ws.py
        if self._template_exists("i18n_ws.py.jinja2"):
            content = self._render("i18n_ws.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/ws.py",
                content=content,
            ))

        # i18n_middleware.py
        if self._template_exists("i18n_middleware.py.jinja2"):
            content = self._render("i18n_middleware.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/i18n/middleware.py",
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
            "discover_sources": [
                DiscoverSource.TEMPLATE.value,
                DiscoverSource.HTML.value,
                DiscoverSource.TSX.value,
                DiscoverSource.CODE.value,
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
