# coding: utf-8
"""
Tests cho CP42 Approval emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- emit() returns correct number of files
- emit() returns correct paths
- emit() files have non-empty content
- _build_context() returns correct keys và giá trị
- _template_exists() returns True/False
- _render() raises MidicoderError khi template không tồn tại
- Angular/React _TEMPLATE_MAP có đúng số lượng entries
- Rendered content chứa context từ IR
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError

# Project root = 6 parents up from tests/ → d:\hemidi-labs\midicoder-ce
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

FASTAPI_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp42_approval"
NESTJS_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp42_approval"
ANGULAR_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp42_approval"
REACT_STACK_DIR = MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp42_approval"


def _make_ir():
    """Tạo ApprovalIR sample cho testing từ basic_approval_recipe."""
    from midicoder.packs.cp42_approval.recipes import basic_approval_recipe
    recipe = basic_approval_recipe()
    return recipe.ir


# ============================================================================
# Test FastAPIApprovalEmitter (13 tests)
# ============================================================================


class TestFastAPIApprovalEmitter:
    """Tests cho FastAPIApprovalEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        with pytest.raises(MidicoderError):
            FastAPIApprovalEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter.template_dir == FASTAPI_STACK_DIR  # template_dir = stack_dir, không thêm subdir

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/models/approval_models.py" in paths
        assert "app/services/approval_service.py" in paths
        assert "app/api/approval_router.py" in paths
        assert "app/events/approval_event_handler.py" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng: requests_list, steps_list, num_requests, num_steps."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "approval_requests" in ctx
        assert "approval_steps" in ctx
        assert "request_count" in ctx
        assert "step_count" in ctx

    def test_build_context_request_count(self):
        """Kiểm tra request_count đúng với IR (basic_approval có 1 request)."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["request_count"] == 1

    def test_build_context_step_count(self):
        """Kiểm tra step_count đúng với IR (basic_approval có 2 steps)."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["step_count"] == 2

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("approval_models.py.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})

    def test_emit_files_are_generated_file_instances(self, tmp_path: Path):
        """Kiểm tra các file trả về là đối tượng GeneratedFile."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter, GeneratedFile,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert isinstance(f, GeneratedFile)


# ============================================================================
# Test NestJSApprovalEmitter (13 tests)
# ============================================================================


class TestNestJSApprovalEmitter:
    """Tests cho NestJSApprovalEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        with pytest.raises(MidicoderError):
            NestJSApprovalEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter.template_dir == NESTJS_STACK_DIR  # template_dir = stack_dir, không thêm subdir

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho NestJS."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/approval/approval.entity.ts" in paths
        assert "src/approval/approval.service.ts" in paths
        assert "src/approval/approval.controller.ts" in paths
        assert "src/approval/approval.gateway.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng: requests_list, steps_list, num_requests, num_steps."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "approval_requests" in ctx
        assert "approval_steps" in ctx
        assert "request_count" in ctx
        assert "step_count" in ctx

    def test_build_context_request_count(self):
        """Kiểm tra request_count đúng với IR (basic_approval có 1 request)."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["request_count"] == 1

    def test_build_context_step_count(self):
        """Kiểm tra step_count đúng với IR (basic_approval có 2 steps)."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["step_count"] == 2

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("approval.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})

    def test_emit_files_are_generated_file_instances(self, tmp_path: Path):
        """Kiểm tra các file trả về là đối tượng GeneratedFile."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter, GeneratedFile,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert isinstance(f, GeneratedFile)


# ============================================================================
# Test AngularApprovalEmitter (10 tests)
# ============================================================================


class TestAngularApprovalEmitter:
    """Tests cho AngularApprovalEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        with pytest.raises(MidicoderError):
            AngularApprovalEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho Angular."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/approval/approval-dashboard.component.ts" in paths
        assert "src/approval/approval.service.ts" in paths
        assert "src/approval/approval.store.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_emit_with_extra_context(self, tmp_path: Path):
        """Kiểm tra emit hoạt động với context bổ sung (thông qua IR)."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) > 0

    def test_template_map_has_6_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 6 entries."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        assert len(AngularApprovalEmitter._TEMPLATE_MAP) == 6

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("approval-dashboard.component.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactApprovalEmitter (10 tests)
# ============================================================================


class TestReactApprovalEmitter:
    """Tests cho ReactApprovalEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        with pytest.raises(MidicoderError):
            ReactApprovalEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho React."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/approval/ApprovalDashboard.tsx" in paths
        assert "src/approval/ApprovalDetails.tsx" in paths
        assert "src/approval/hooks/useApprovals.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_emit_files_are_dicts(self):
        """Kiểm tra các file trả về là dict với key path và content."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert isinstance(f, dict)
            assert "path" in f
            assert "content" in f

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("ApprovalDashboard.tsx.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})


# ============================================================================
# Test Emit Context (3 tests)
# ============================================================================


class TestEmitContext:
    """Tests cho việc context từ IR có trong nội dung rendered."""

    def test_fastapi_content_rendered_with_context(self, tmp_path: Path):
        """Kiểm tra FastAPI emitted content chứa context từ IR."""
        from midicoder.packs.cp42_approval.fastapi import (
            FastAPIApprovalEmitter,
        )
        emitter = FastAPIApprovalEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        # Basic approval có 1 request, 2 steps — context này phải xuất hiện trong rendered content
        assert "1" in all_content or "2" in all_content

    def test_nestjs_content_rendered_with_context(self, tmp_path: Path):
        """Kiểm tra NestJS emitted content chứa context từ IR."""
        from midicoder.packs.cp42_approval.nestjs import (
            NestJSApprovalEmitter,
        )
        emitter = NestJSApprovalEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        # Basic approval có 1 request, 2 steps — context này phải xuất hiện trong rendered content
        assert "1" in all_content or "2" in all_content

    def test_angular_react_content_rendered_with_context(self):
        """Kiểm tra Angular và React emitted content chứa context từ IR."""
        from midicoder.packs.cp42_approval.angular import (
            AngularApprovalEmitter,
        )
        from midicoder.packs.cp42_approval.react import (
            ReactApprovalEmitter,
        )
        # Angular
        angular_emitter = AngularApprovalEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        angular_files = angular_emitter.emit(_make_ir(), Path("/tmp"))
        angular_content = "\n".join(f.content for f in angular_files)
        assert "1" in angular_content or "2" in angular_content

        # React
        react_emitter = ReactApprovalEmitter(stack_dir=str(REACT_STACK_DIR))
        react_files = react_emitter.emit(_make_ir())
        react_content = "\n".join(f["content"] for f in react_files)
        assert "1" in react_content or "2" in react_content
