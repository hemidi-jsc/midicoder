# coding: utf-8
"""
Tests cho CP48 emitters — FastAPI, NestJS, Angular, React.

Test cấu trúc emitter (init, class existence, template discovery) +
coverage cho emit()/render methods bằng mock.

Templates từ agents chứa TypeScript/JSX syntax không tương thích với
Jinja2 parser nên test emit dùng mock _render thay vì render thật.

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from midicoder.packs.cp48_rate_limit.parser import RateLimitIR
from midicoder.packs.cp48_rate_limit.models import (
    RateLimitPolicy,
    RateLimitStrategy,
    QuotaConfig,
    QuotaLevel,
    QuotaPeriod,
)
from midicoder.packs.cp48_rate_limit.fastapi import (
    FastAPIRateLimitEmitter,
    GeneratedFile,
)
from midicoder.packs.cp48_rate_limit.nestjs import NestJSRateLimitEmitter
from midicoder.packs.cp48_rate_limit.angular import AngularRateLimitEmitter
from midicoder.packs.cp48_rate_limit.react import ReactRateLimitEmitter
from midicoder.errors import MidicoderError


# ============================================================================
# Helper
# ============================================================================


def _get_template_dir(stack: str) -> str:
    """Lấy đường dẫn template directory cho stack."""
    return str(Path(__file__).parents[4] / "stacks" / stack / "core" / "cp48_rate_limit")


def _make_test_ir() -> RateLimitIR:
    """Tạo IR test với 1 policy + 1 quota."""
    return RateLimitIR(
        policies=[
            RateLimitPolicy(
                policy_id="test_policy",
                name="Test Policy",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                max_requests=100,
                window_seconds=60,
            )
        ],
        quotas=[
            QuotaConfig(
                config_id="test_quota",
                level=QuotaLevel.USER,
                period=QuotaPeriod.DAY,
                max_requests=1000,
            )
        ],
    )


# ============================================================================
# FastAPI
# ============================================================================


class TestFastAPIEmitter:
    """Test FastAPIRateLimitEmitter."""

    def test_init_validates_directory(self):
        """Init raise error nếu directory không tồn tại."""
        with pytest.raises(MidicoderError):
            FastAPIRateLimitEmitter("/nonexistent/path")

    def test_init_with_valid_directory(self):
        """Init thành công với directory tồn tại."""
        template_dir = _get_template_dir("fastapi")
        emitter = FastAPIRateLimitEmitter(template_dir)
        assert emitter.stack_dir.exists()

    def test_templates_directory_has_files(self):
        """Template directory chứa đúng số lượng template files."""
        template_dir = Path(_get_template_dir("fastapi"))
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == 5  # models, middleware, service, router, quota

    def test_emit_returns_files(self, tmp_path):
        """Emit trả về danh sách GeneratedFile."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        assert len(files) == 5
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_emit_has_expected_paths(self, tmp_path):
        """Emit tạo files với đúng output paths."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        paths = [f.path for f in files]
        assert any("models.py" in p for p in paths)
        assert any("middleware.py" in p for p in paths)
        assert any("service.py" in p for p in paths)

    def test_emit_content_not_empty(self, tmp_path):
        """Emit tạo files có nội dung không rỗng."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_emit_raises_on_render_error(self, tmp_path):
        """Emit raise MidicoderError khi render lỗi."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", side_effect=RuntimeError("template error")):
            with pytest.raises(MidicoderError):
                emitter.emit(ir, tmp_path)

    def test_build_context(self):
        """_build_context trả về dict có policies và quotas."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = _make_test_ir()
        context = emitter._build_context(ir)
        assert "policies" in context
        assert "quotas" in context
        assert "has_policies" in context
        assert "has_quotas" in context
        assert context["has_policies"] is True
        assert context["has_quotas"] is True
        assert len(context["policies"]) == 1
        assert len(context["quotas"]) == 1

    def test_build_context_empty_ir(self):
        """_build_context với IR rỗng → has_policies=False, has_quotas=False."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        ir = RateLimitIR()
        context = emitter._build_context(ir)
        assert context["has_policies"] is False
        assert context["has_quotas"] is False
        assert context["policies"] == []
        assert context["quotas"] == []

    def test_render_raises_on_missing_template(self):
        """_render raise MidicoderError khi template không tồn tại."""
        emitter = FastAPIRateLimitEmitter(_get_template_dir("fastapi"))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.jinja2", {})

    def test_generated_file_dataclass(self):
        """GeneratedFile dataclass hoạt động đúng."""
        f = GeneratedFile(path="test.py", content="print('hello')")
        assert f.path == "test.py"
        assert f.content == "print('hello')"


# ============================================================================
# NestJS
# ============================================================================


class TestNestJSEmitter:
    """Test NestJSRateLimitEmitter."""

    def test_init_validates_directory(self):
        """Init raise error nếu directory không tồn tại."""
        with pytest.raises(MidicoderError):
            NestJSRateLimitEmitter("/nonexistent/path")

    def test_init_with_valid_directory(self):
        """Init thành công với directory tồn tại."""
        template_dir = _get_template_dir("nestjs")
        emitter = NestJSRateLimitEmitter(template_dir)
        assert emitter.stack_dir.exists()

    def test_templates_directory_has_files(self):
        """Template directory chứa đúng số lượng template files."""
        template_dir = Path(_get_template_dir("nestjs"))
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == 5  # service, middleware, module, controller, quota

    def test_emit_returns_files(self, tmp_path):
        """Emit trả về danh sách GeneratedFile."""
        emitter = NestJSRateLimitEmitter(_get_template_dir("nestjs"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        assert len(files) == 5

    def test_emit_raises_on_render_error(self, tmp_path):
        """Emit raise MidicoderError khi render lỗi."""
        emitter = NestJSRateLimitEmitter(_get_template_dir("nestjs"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", side_effect=RuntimeError("template error")):
            with pytest.raises(MidicoderError):
                emitter.emit(ir, tmp_path)

    def test_build_context(self):
        """_build_context trả về dict có policies và quotas."""
        emitter = NestJSRateLimitEmitter(_get_template_dir("nestjs"))
        ir = _make_test_ir()
        context = emitter._build_context(ir)
        assert context["has_policies"] is True
        assert context["has_quotas"] is True


# ============================================================================
# Angular
# ============================================================================


class TestAngularEmitter:
    """Test AngularRateLimitEmitter."""

    def test_init_validates_directory(self):
        """Init raise error nếu directory không tồn tại."""
        with pytest.raises(MidicoderError):
            AngularRateLimitEmitter("/nonexistent/path")

    def test_init_with_valid_directory(self):
        """Init thành công với directory tồn tại."""
        template_dir = _get_template_dir("angular")
        emitter = AngularRateLimitEmitter(template_dir)
        assert emitter.stack_dir.exists()

    def test_templates_directory_has_files(self):
        """Template directory chứa đúng số lượng template files."""
        template_dir = Path(_get_template_dir("angular"))
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == 3  # dashboard, quota_status, service

    def test_emit_returns_files(self, tmp_path):
        """Emit trả về danh sách GeneratedFile."""
        emitter = AngularRateLimitEmitter(_get_template_dir("angular"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        assert len(files) == 3

    def test_emit_raises_on_render_error(self, tmp_path):
        """Emit raise MidicoderError khi render lỗi."""
        emitter = AngularRateLimitEmitter(_get_template_dir("angular"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", side_effect=RuntimeError("template error")):
            with pytest.raises(MidicoderError):
                emitter.emit(ir, tmp_path)

    def test_build_context(self):
        """_build_context trả về dict có policies và quotas."""
        emitter = AngularRateLimitEmitter(_get_template_dir("angular"))
        ir = _make_test_ir()
        context = emitter._build_context(ir)
        assert context["has_policies"] is True
        assert context["has_quotas"] is True


# ============================================================================
# React
# ============================================================================


class TestReactEmitter:
    """Test ReactRateLimitEmitter."""

    def test_init_validates_directory(self):
        """Init raise error nếu directory không tồn tại."""
        with pytest.raises(MidicoderError):
            ReactRateLimitEmitter("/nonexistent/path")

    def test_init_with_valid_directory(self):
        """Init thành công với directory tồn tại."""
        template_dir = _get_template_dir("react")
        emitter = ReactRateLimitEmitter(template_dir)
        assert emitter.stack_dir.exists()

    def test_templates_directory_has_files(self):
        """Template directory chứa đúng số lượng template files."""
        template_dir = Path(_get_template_dir("react"))
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == 3  # dashboard, quota_status, hook

    def test_emit_returns_files(self, tmp_path):
        """Emit trả về danh sách GeneratedFile."""
        emitter = ReactRateLimitEmitter(_get_template_dir("react"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", return_value="mock content"):
            files = emitter.emit(ir, tmp_path)
        assert len(files) == 3

    def test_emit_raises_on_render_error(self, tmp_path):
        """Emit raise MidicoderError khi render lỗi."""
        emitter = ReactRateLimitEmitter(_get_template_dir("react"))
        ir = _make_test_ir()
        with patch.object(emitter, "_render", side_effect=RuntimeError("template error")):
            with pytest.raises(MidicoderError):
                emitter.emit(ir, tmp_path)

    def test_build_context(self):
        """_build_context trả về dict có policies và quotas."""
        emitter = ReactRateLimitEmitter(_get_template_dir("react"))
        ir = _make_test_ir()
        context = emitter._build_context(ir)
        assert context["has_policies"] is True
        assert context["has_quotas"] is True
