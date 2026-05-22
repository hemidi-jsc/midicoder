# coding: utf-8
"""
Tests cho CP39 emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- emit() returns correct number of files
- emit() returns correct paths
- _build_context() returns correct keys
- _template_exists() returns True/False
- Angular _TEMPLATE_MAP has 4 entries
- React _TEMPLATE_MAP has 5 entries
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError

# Midicoder root = 5 parents up from tests/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_TEMPLATE_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core" / "cp39_i18n_runtime"
NESTJS_TEMPLATE_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core" / "cp39_i18n_runtime"
ANGULAR_TEMPLATE_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core" / "cp39_i18n_runtime"
REACT_TEMPLATE_DIR = MIDICODER_ROOT / "stacks" / "react" / "core" / "cp39_i18n_runtime"

# stack_dir = parent of template_dir (i.e. stacks/{stack}/core)
FASTAPI_STACK_DIR = FASTAPI_TEMPLATE_DIR.parent
NESTJS_STACK_DIR = NESTJS_TEMPLATE_DIR.parent
ANGULAR_STACK_DIR = ANGULAR_TEMPLATE_DIR.parent
REACT_STACK_DIR = REACT_TEMPLATE_DIR.parent


def _make_ir():
    """Tạo I18nRuntimeIR sample cho testing."""
    from midicoder.emitters.core.cp39_i18n_runtime.models import (
        CacheConfig,
        LocaleConfig,
        TranslationEntry,
    )
    from midicoder.emitters.core.cp39_i18n_runtime.parser import I18nRuntimeIR

    locales = [
        LocaleConfig(code="en", name="English", is_default=True, currency_code="USD"),
        LocaleConfig(code="vi", name="Tiếng Việt", currency_code="VND", fallback_locale="en"),
    ]
    translations = [
        TranslationEntry(key="welcome", namespace="common", locale="en", value="Welcome!"),
        TranslationEntry(key="welcome", namespace="common", locale="vi", value="Chào mừng!"),
        TranslationEntry(key="save", namespace="common", locale="en", value="Save"),
        TranslationEntry(key="save", namespace="common", locale="vi", value="Lưu"),
    ]
    cache_config = CacheConfig(ttl_seconds=300, max_size=5000)
    return I18nRuntimeIR(locales=locales, translations=translations, cache_config=cache_config)


# ============================================================================
# Test FastAPII18nRuntimeEmitter
# ============================================================================


class TestFastAPII18nRuntimeEmitter:
    """Tests cho FastAPII18nRuntimeEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        with pytest.raises(MidicoderError):
            FastAPII18nRuntimeEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_files(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) > 0

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/i18n/models.py" in paths
        assert "app/i18n/schemas.py" in paths
        assert "app/i18n/services/translation_service.py" in paths
        assert "app/i18n/services/locale_formatter.py" in paths
        assert "app/i18n/routers/i18n_router.py" in paths
        assert "app/i18n/services/cache.py" in paths
        assert "app/i18n/services/discover.py" in paths
        assert "app/i18n/ws.py" in paths
        assert "app/i18n/middleware.py" in paths

    def test_emit_files_have_content(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_build_context_returns_correct_keys(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "locales" in ctx
        assert "translations" in ctx
        assert "locale_count" in ctx
        assert "translation_count" in ctx
        assert "cache_config" in ctx
        assert "plural_rules" in ctx
        assert "cache_backends" in ctx
        assert "namespaces" in ctx
        assert "default_locale" in ctx

    def test_build_context_counts(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["locale_count"] == 2
        assert ctx["translation_count"] == 4

    def test_template_exists_true(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("i18n_models.py.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.emitters.core.cp39_i18n_runtime.fastapi import (
            FastAPII18nRuntimeEmitter,
        )

        emitter = FastAPII18nRuntimeEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ============================================================================
# Test NestJSI18nRuntimeEmitter
# ============================================================================


class TestNestJSI18nRuntimeEmitter:
    """Tests cho NestJSI18nRuntimeEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        with pytest.raises(MidicoderError):
            NestJSI18nRuntimeEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_files(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) > 0

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/i18n/entities/translation.entity.ts" in paths
        assert "src/i18n/entities/locale.entity.ts" in paths
        assert "src/i18n/dtos/translation.dto.ts" in paths
        assert "src/i18n/services/translation.service.ts" in paths
        assert "src/i18n/controllers/translation.controller.ts" in paths
        assert "src/i18n/services/locale-formatter.service.ts" in paths
        assert "src/i18n/services/i18n-cache.service.ts" in paths
        assert "src/i18n/gateways/i18n.gateway.ts" in paths
        assert "src/i18n/interceptors/i18n.interceptor.ts" in paths
        assert "src/i18n/i18n.module.ts" in paths

    def test_emit_files_have_content(self, tmp_path: Path):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_build_context_returns_correct_keys(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "locales" in ctx
        assert "translations" in ctx
        assert "locale_count" in ctx
        assert "namespaces" in ctx
        assert "default_locale" in ctx

    def test_template_exists_true(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("translation.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.emitters.core.cp39_i18n_runtime.nestjs import (
            NestJSI18nRuntimeEmitter,
        )

        emitter = NestJSI18nRuntimeEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularI18nRuntimeEmitter
# ============================================================================


class TestAngularI18nRuntimeEmitter:
    """Tests cho AngularI18nRuntimeEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        with pytest.raises(MidicoderError):
            AngularI18nRuntimeEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_files(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) > 0

    def test_emit_returns_correct_paths(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/app/core/i18n/i18n-runtime.service.ts" in paths
        assert "src/app/core/i18n/locale-directive.ts" in paths
        assert "src/app/core/i18n/translation-sync.service.ts" in paths
        assert "src/app/core/i18n/locale-formatter.pipe.ts" in paths

    def test_emit_files_have_content(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0

    def test_emit_with_extra_context(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "angular"})
        assert len(files) > 0

    def test_template_map_has_4_entries(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        assert len(AngularI18nRuntimeEmitter._TEMPLATE_MAP) == 4

    def test_template_exists_true(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("i18n-runtime.service.ts.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.emitters.core.cp39_i18n_runtime.angular import (
            AngularI18nRuntimeEmitter,
        )

        emitter = AngularI18nRuntimeEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactI18nRuntimeEmitter
# ============================================================================


class TestReactI18nRuntimeEmitter:
    """Tests cho ReactI18nRuntimeEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        with pytest.raises(MidicoderError):
            ReactI18nRuntimeEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        emitter = ReactI18nRuntimeEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_correct_paths_template_map(self):
        """Verify the _TEMPLATE_MAP output paths are correct."""
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        expected_paths = {
            "src/i18n/hooks/useTranslation.ts",
            "src/i18n/hooks/useLocale.ts",
            "src/i18n/hooks/useFormattedValue.ts",
            "src/i18n/workers/TranslationSyncWorker.ts",
            "src/i18n/components/I18nRuntimeProvider.tsx",
        }
        actual_paths = set(ReactI18nRuntimeEmitter._TEMPLATE_MAP.values())
        assert actual_paths == expected_paths

    def test_template_map_has_5_entries(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        assert len(ReactI18nRuntimeEmitter._TEMPLATE_MAP) == 5

    def test_emit_with_extra_context(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        emitter = ReactI18nRuntimeEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_template_exists_true(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        emitter = ReactI18nRuntimeEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("useTranslation.ts.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        emitter = ReactI18nRuntimeEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.emitters.core.cp39_i18n_runtime.react import (
            ReactI18nRuntimeEmitter,
        )

        emitter = ReactI18nRuntimeEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})
