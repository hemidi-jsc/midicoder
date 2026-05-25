# coding: utf-8
"""
Tests cho CP50 Catalog & Taxonomy Engine emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- __init__ succeeds với template dir có thật
- __init__ sets template_dir đúng
- emit() returns correct number of files
- emit() returns correct paths
- emit() files have non-empty content
- _build_context() returns correct keys (FastAPI, NestJS, Angular)
- _template_exists() returns True/False
- _render() raises MidicoderError khi template không tồn tại
- _TEMPLATE_MAP has correct entries (Angular, React)
- emit() returns dicts (React)
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError
from midicoder.emitters.core.cp50_catalog.parser import CatalogIR
from midicoder.emitters.core.cp50_catalog.recipes import basic_catalog_recipe

# Project root = 6 parents up from tests/ → d:\hemidi-labs\midicoder-ce
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

FASTAPI_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp50_catalog"
NESTJS_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp50_catalog"
ANGULAR_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp50_catalog"
REACT_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp50_catalog"


def _make_ir():
    """Tạo CatalogIR sample cho testing từ basic_catalog_recipe."""
    return basic_catalog_recipe().ir


# ============================================================================
# Test FastAPICatalogEmitter (10 tests)
# ============================================================================


class TestFastAPICatalogEmitter:
    """Tests cho FastAPICatalogEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        with pytest.raises(MidicoderError):
            FastAPICatalogEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter.template_dir == FASTAPI_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho FastAPI."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/models/catalog_models.py" in paths
        assert "app/schemas/catalog_schemas.py" in paths
        assert "app/services/product_service.py" in paths
        assert "app/services/category_service.py" in paths
        assert "app/services/attribute_service.py" in paths
        assert "app/services/faceted_search_service.py" in paths
        assert "app/api/catalog_router.py" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "products" in ctx
        assert "categories" in ctx
        assert "variants" in ctx
        assert "attributes" in ctx
        assert "attribute_values" in ctx
        assert "use_search" in ctx
        assert "use_audit" in ctx

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("catalog_models.py.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.fastapi import (
            FastAPICatalogEmitter,
        )
        emitter = FastAPICatalogEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ============================================================================
# Test NestJSCatalogEmitter (10 tests)
# ============================================================================


class TestNestJSCatalogEmitter:
    """Tests cho NestJSCatalogEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        with pytest.raises(MidicoderError):
            NestJSCatalogEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter.template_dir == NESTJS_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho NestJS."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/catalog/catalog.entity.ts" in paths
        assert "src/catalog/catalog.dto.ts" in paths
        assert "src/catalog/product.service.ts" in paths
        assert "src/catalog/category.service.ts" in paths
        assert "src/catalog/attribute.service.ts" in paths
        assert "src/catalog/catalog.controller.ts" in paths
        assert "src/catalog/catalog.module.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "products" in ctx
        assert "categories" in ctx
        assert "variants" in ctx
        assert "attributes" in ctx
        assert "attribute_values" in ctx
        assert "use_search" in ctx
        assert "use_audit" in ctx

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("catalog.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.nestjs import (
            NestJSCatalogEmitter,
        )
        emitter = NestJSCatalogEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularCatalogEmitter (11 tests)
# ============================================================================


class TestAngularCatalogEmitter:
    """Tests cho AngularCatalogEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        with pytest.raises(MidicoderError):
            AngularCatalogEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter.template_dir == ANGULAR_STACK_DIR

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho Angular."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/catalog/product-list.component.ts" in paths
        assert "src/catalog/product-detail.component.ts" in paths
        assert "src/catalog/category-tree.component.ts" in paths
        assert "src/catalog/facet-filter.component.ts" in paths
        assert "src/catalog/catalog.service.ts" in paths
        assert "src/catalog/catalog.store.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "products" in ctx
        assert "categories" in ctx
        assert "variants" in ctx
        assert "attributes" in ctx
        assert "attribute_values" in ctx
        assert "use_search" in ctx
        assert "use_audit" in ctx

    def test_template_map_has_6_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 6 entries."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        assert len(AngularCatalogEmitter._TEMPLATE_MAP) == 6

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("product-list.component.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.angular import (
            AngularCatalogEmitter,
        )
        emitter = AngularCatalogEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactCatalogEmitter (11 tests)
# ============================================================================


class TestReactCatalogEmitter:
    """Tests cho ReactCatalogEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        with pytest.raises(MidicoderError):
            ReactCatalogEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter.template_dir == REACT_STACK_DIR

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho React."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/catalog/ProductList.tsx" in paths
        assert "src/catalog/ProductDetail.tsx" in paths
        assert "src/catalog/CategoryTree.tsx" in paths
        assert "src/catalog/FacetFilter.tsx" in paths
        assert "src/catalog/hooks/useCatalog.ts" in paths
        assert "src/catalog/hooks/useFacetedSearch.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_emit_files_are_dicts(self):
        """Kiểm tra các file trả về là dict với key path và content."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert isinstance(f, dict)
            assert "path" in f
            assert "content" in f

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("ProductList.tsx.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp50_catalog.react import (
            ReactCatalogEmitter,
        )
        emitter = ReactCatalogEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})
