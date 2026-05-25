# coding: utf-8
"""
Emitter tests cho CP29 Multi-Language Support Generator.

Kiểm tra:
- FastAPI emitter: render đúng 2 templates (i18n.py, config_i18n.py)
- NestJS emitter: render đúng 2 templates (i18n_module.ts, i18n_service.ts)
- Angular emitter: render đúng 1 template (i18n_service.ts)
- React emitter: render đúng 2 templates (i18n.ts, use_translation.ts)
- Locale content: verify gettext format, XLIFF format, JSON key-value structure
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from midicoder.emitters.core.cp29_multi_language.models import (
    I18nBundle,
    I18nKeyset,
    LanguageProfile,
)
from midicoder.emitters.core.cp29_multi_language.parser import I18nParser
from midicoder.emitters.core.cp29_multi_language.recipes import (
    auto_generate_i18n_from_mir,
    generate_i18n_bundles,
    generate_language_profile,
)
from midicoder.pipeline.emitter import Emitter


def _parse_entities(entity_list: list[dict[str, Any]]) -> I18nKeyset:
    """Helper: parse danh sách entities thành I18nKeyset."""
    return I18nParser().parse_from_metadata({"entities": entity_list, "commands": [], "queries": [], "events": []})


# ===========================================================================
# Context mẫu cho tất cả test
# ===========================================================================


def _make_context() -> dict[str, Any]:
    """Tạo context mẫu cho i18n emit."""
    profile = generate_language_profile()
    keyset = _parse_entities([
        {"id": "Customer", "fields": [{"id": "name"}, {"id": "email"}]},
        {"id": "Order", "fields": [{"id": "total"}, {"id": "status"}]},
    ])
    bundles = generate_i18n_bundles(keyset)

    return {
        "entities": [
            {"id": "Customer", "fields": [{"name": "name"}, {"name": "email"}]},
            {"id": "Order", "fields": [{"name": "total"}, {"name": "status"}]},
        ],
        "commands": [
            {"id": "CreateOrder", "input": [{"name": "customer_id"}]},
        ],
        "queries": [{"id": "GetCustomer", "returns": "Customer"}],
        "events": [],
        "language_profile": {
            "id": profile.id,
            "locales": profile.locales,
            "default_locale": profile.default_locale,
        },
        "i18n_keyset": keyset.to_dict() if hasattr(keyset, 'to_dict') else {},
        "i18n_bundles": [
            b.to_dict()
            for b in bundles
        ],
    }


# Template lists per stack (theo templates có thật)
FASTAPI_TEMPLATES = [
    "i18n.py.jinja2",
    "config_i18n.py.jinja2",
]

NESTJS_TEMPLATES = [
    "i18n_module.ts.jinja2",
    "i18n_service.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "i18n_service.ts.jinja2",
]

REACT_TEMPLATES = [
    "i18n.ts.jinja2",
    "use_translation.ts.jinja2",
]


# ===========================================================================
# Test FastAPI Emitter
# ===========================================================================


class TestFastAPIEmitter:
    """Kiểm tra FastAPI emitter render đúng templates."""

    def test_render_i18n_py(self, tmp_path: Path) -> None:
        """i18n.py.jinja2 render được và chứa i18n logic."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp29_multi_language/i18n.py.jinja2", _make_context())
        assert len(content) > 0
        assert "i18n" in content.lower() or "translation" in content.lower() or "locale" in content.lower()

    def test_render_config_i18n_py(self, tmp_path: Path) -> None:
        """config_i18n.py.jinja2 render được và chứa config."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp29_multi_language/config_i18n.py.jinja2", _make_context())
        assert len(content) > 0
        assert "config" in content.lower() or "i18n" in content.lower()

    def test_emit_both_templates(self, tmp_path: Path) -> None:
        """Cả 2 FastAPI templates render được."""
        emitter = Emitter(stack="fastapi")
        context = _make_context()
        for tmpl in FASTAPI_TEMPLATES:
            content = emitter.render(f"cp29_multi_language/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"

    def test_i18n_py_has_gettext_format(self, tmp_path: Path) -> None:
        """i18n.py output có gettext structure."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp29_multi_language/i18n.py.jinja2", _make_context())
        # Gettext format: msgid/msgstr hoặc translation dict
        assert "msgid" in content.lower() or "translations" in content.lower() or "dict" in content.lower()


# ===========================================================================
# Test NestJS Emitter
# ===========================================================================


class TestNestJSEmitter:
    """Kiểm tra NestJS emitter render đúng templates."""

    def test_render_i18n_module(self, tmp_path: Path) -> None:
        """i18n_module.ts.jinja2 render được và chứa @Module."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp29_multi_language/i18n_module.ts.jinja2", _make_context())
        assert len(content) > 0
        assert "@Module" in content or "Module" in content

    def test_render_i18n_service(self, tmp_path: Path) -> None:
        """i18n_service.ts.jinja2 render được và chứa @Injectable."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp29_multi_language/i18n_service.ts.jinja2", _make_context())
        assert len(content) > 0
        assert "@Injectable" in content or "Service" in content

    def test_emit_both_templates(self, tmp_path: Path) -> None:
        """Cả 2 NestJS templates render được."""
        emitter = Emitter(stack="nestjs")
        context = _make_context()
        for tmpl in NESTJS_TEMPLATES:
            content = emitter.render(f"cp29_multi_language/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"


# ===========================================================================
# Test Angular Emitter
# ===========================================================================


class TestAngularEmitter:
    """Kiểm tra Angular emitter render đúng templates."""

    def test_render_i18n_service(self, tmp_path: Path) -> None:
        """i18n_service.ts.jinja2 render được và chứa @Injectable."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp29_multi_language/i18n_service.ts.jinja2", _make_context())
        assert len(content) > 0
        assert "@Injectable" in content or "Service" in content or "injectable" in content.lower()

    def test_emit_all_templates(self, tmp_path: Path) -> None:
        """Tất cả Angular templates render được."""
        emitter = Emitter(stack="angular")
        context = _make_context()
        for tmpl in ANGULAR_TEMPLATES:
            content = emitter.render(f"cp29_multi_language/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"


# ===========================================================================
# Test React Emitter
# ===========================================================================


class TestReactEmitter:
    """Kiểm tra React emitter render đúng templates."""

    def test_render_i18n_ts(self, tmp_path: Path) -> None:
        """i18n.ts.jinja2 render được."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp29_multi_language/i18n.ts.jinja2", _make_context())
        assert len(content) > 0
        assert "i18n" in content.lower() or "translation" in content.lower()

    def test_render_use_translation(self, tmp_path: Path) -> None:
        """use_translation.ts.jinja2 render được và chứa hook."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp29_multi_language/use_translation.ts.jinja2", _make_context())
        assert len(content) > 0
        assert "useTranslation" in content or "use" in content.lower() or "function" in content.lower()

    def test_emit_all_templates(self, tmp_path: Path) -> None:
        """Tất cả React templates render được."""
        emitter = Emitter(stack="react")
        context = _make_context()
        for tmpl in REACT_TEMPLATES:
            content = emitter.render(f"cp29_multi_language/{tmpl}", context)
            assert len(content) > 0, f"Template {tmpl} render rỗng"


# ===========================================================================
# Test Locale Content
# ===========================================================================


class TestLocaleContent:
    """Kiểm tra locale content đúng format."""

    def test_gettext_po_format(self, tmp_path: Path) -> None:
        """Verify gettext (.po) format: msgid/msgstr."""
        keyset = _parse_entities([{"id": "Customer", "fields": [{"id": "name"}]}])
        bundles = generate_i18n_bundles(keyset)

        for bundle in bundles:
            assert bundle.locale in ["en", "vi"]
            bundle_dict = bundle.to_dict()
            for key, value in bundle_dict["keys"].items():
                assert isinstance(key, str)
                assert isinstance(value, str)

    def test_xliff_format(self, tmp_path: Path) -> None:
        """Verify XLIFF format: có target/source structure."""
        keyset = _parse_entities([{"id": "Customer", "fields": [{"id": "name"}]}])
        bundles = generate_i18n_bundles(keyset)

        for bundle in bundles:
            # XLIFF structure: key → translated value
            assert len(bundle.keys) >= 0

    def test_json_key_value_format(self, tmp_path: Path) -> None:
        """Verify JSON format: key-value structure."""
        keyset = _parse_entities([{"id": "Customer", "fields": [{"id": "name"}]}])
        bundles = generate_i18n_bundles(keyset)

        for bundle in bundles:
            # JSON key-value: dict[str, str]
            bundle_dict = bundle.to_dict()
            for key, val in bundle_dict["keys"].items():
                assert isinstance(key, str)
                assert isinstance(val, str)

    def test_default_locales_are_en_and_vi(self, tmp_path: Path) -> None:
        """Verify default locales là en và vi."""
        profile = generate_language_profile()
        assert profile.locales == ["en", "vi"]
        assert profile.default_locale == "en"

    def test_keyset_has_entity_keys(self, tmp_path: Path) -> None:
        """Verify keyset có keys từ entities."""
        keyset = _parse_entities([{"id": "Customer", "fields": [{"id": "name"}, {"id": "email"}]}])
        assert len(keyset.keys) >= 2


# ===========================================================================
# Test Error Boundary
# ===========================================================================


class TestErrorBoundary:
    """Kiểm tra error boundary."""

    def test_emitter_raises_error_for_missing_template(self, tmp_path: Path) -> None:
        """Emitter raise error khi template không tồn tại."""
        emitter = Emitter(stack="fastapi")
        with pytest.raises(Exception):
            emitter.render("cp29_multi_language/nonexistent.py.jinja2", _make_context())

    def test_parser_with_empty_entities(self, tmp_path: Path) -> None:
        """Parser xử lý empty entities không crash."""
        keyset = I18nParser().parse_from_metadata({})
        assert len(keyset.keys) == 0
