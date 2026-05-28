# coding: utf-8
"""
Tests cho CP49 Consent emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- __init__ succeeds với template dir có thật
- __init__ sets template_dir đúng
- emit() returns correct number of files
- emit() returns correct paths
- emit() files have non-empty content
- _build_context() returns correct keys
- _template_exists() returns True/False
- _render() raises MidicoderError khi template không tồn tại
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError
from midicoder.packs.cp_full_consent.parser import ConsentIR
from midicoder.packs.cp_full_consent.recipes import basic_consent_recipe

# Project root = 6 parents up from tests/ → d:\hemidi-labs\midicoder-ce
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

FASTAPI_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp_full_consent"
NESTJS_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp_full_consent"
ANGULAR_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp_full_consent"
REACT_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp_full_consent"


def _make_ir():
    """Tạo ConsentIR sample cho testing từ basic_consent_recipe."""
    return basic_consent_recipe().ir


# ============================================================================
# Test FastAPIConsentEmitter (9 tests)
# ============================================================================


class TestFastAPIConsentEmitter:
    """Tests cho FastAPIConsentEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        with pytest.raises(MidicoderError):
            FastAPIConsentEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter.template_dir == FASTAPI_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/models/consent_models.py" in paths
        assert "app/schemas/consent_schemas.py" in paths
        assert "app/services/consent_service.py" in paths
        assert "app/api/consent_router.py" in paths
        assert "app/services/cookie_banner_service.py" in paths
        assert "app/middleware/consent_middleware.py" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "consent_policies" in ctx
        assert "consent_records" in ctx
        assert "cookie_categories" in ctx
        assert "comm_channels" in ctx
        assert "use_audit" in ctx
        assert "use_retention" in ctx

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("consent_models.py.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_consent.fastapi import (
            FastAPIConsentEmitter,
        )
        emitter = FastAPIConsentEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ============================================================================
# Test NestJSConsentEmitter (9 tests)
# ============================================================================


class TestNestJSConsentEmitter:
    """Tests cho NestJSConsentEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        with pytest.raises(MidicoderError):
            NestJSConsentEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter.template_dir == NESTJS_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho NestJS."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/consent/consent.entity.ts" in paths
        assert "src/consent/consent.dto.ts" in paths
        assert "src/consent/consent.service.ts" in paths
        assert "src/consent/consent.controller.ts" in paths
        assert "src/consent/consent.module.ts" in paths
        assert "src/consent/consent.guard.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "consent_policies" in ctx
        assert "consent_records" in ctx
        assert "cookie_categories" in ctx
        assert "comm_channels" in ctx
        assert "use_audit" in ctx
        assert "use_retention" in ctx

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("consent.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_consent.nestjs import (
            NestJSConsentEmitter,
        )
        emitter = NestJSConsentEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularConsentEmitter (10 tests)
# ============================================================================


class TestAngularConsentEmitter:
    """Tests cho AngularConsentEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        with pytest.raises(MidicoderError):
            AngularConsentEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter.template_dir == ANGULAR_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 5 files."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 5

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho Angular."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/consent/privacy-center.component.ts" in paths
        assert "src/consent/cookie-banner.component.ts" in paths
        assert "src/consent/consent-manager.component.ts" in paths
        assert "src/consent/consent.service.ts" in paths
        assert "src/consent/consent.store.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "consent_policies" in ctx
        assert "consent_records" in ctx
        assert "cookie_categories" in ctx
        assert "comm_channels" in ctx
        assert "use_audit" in ctx
        assert "use_retention" in ctx

    def test_template_map_has_5_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 5 entries."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        assert len(AngularConsentEmitter._TEMPLATE_MAP) == 5

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("privacy-center.component.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_consent.angular import (
            AngularConsentEmitter,
        )
        emitter = AngularConsentEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactConsentEmitter (10 tests)
# ============================================================================


class TestReactConsentEmitter:
    """Tests cho ReactConsentEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        with pytest.raises(MidicoderError):
            ReactConsentEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter.template_dir == REACT_STACK_DIR

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 5 files."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 5

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho React."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/consent/PrivacyCenter.tsx" in paths
        assert "src/consent/CookieBanner.tsx" in paths
        assert "src/consent/ConsentManager.tsx" in paths
        assert "src/consent/CommunicationPreferences.tsx" in paths
        assert "src/consent/hooks/useConsent.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_emit_files_are_dicts(self):
        """Kiểm tra các file trả về là dict với key path và content."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert isinstance(f, dict)
            assert "path" in f
            assert "content" in f

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("PrivacyCenter.tsx.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_consent.react import (
            ReactConsentEmitter,
        )
        emitter = ReactConsentEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})
