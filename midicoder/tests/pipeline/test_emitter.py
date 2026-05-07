"""
Test cho Emitter class — Jinja2 Template Rendering Engine.

Mô-đun này test toàn bộ lifecycle của Emitter:
- Khởi tạo Jinja2 Environment
- Render templates với MIR context
- Emit files ra output directory

TDD: RED → GREEN → REFACTOR
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ============================================================================
# Test Data
# ============================================================================

SAMPLE_CONTEXT = {
    "entities": [
        {
            "id": "Order",
            "description": "Đơn hàng",
            "fields": [
                {"name": "order_id", "type": "string", "primary_key": True},
                {"name": "customer_id", "type": "string"},
                {"name": "total", "type": "decimal"},
            ],
            "tenant_scope": "tenant_isolated",
            "tags": ["commerce"],
        }
    ],
    "commands": [
        {
            "id": "CreateOrder",
            "input": {"customer_id": "string", "items": "list"},
            "fetches": ["Customer"],
            "guards": ["CustomerExists"],
            "effects": ["CreateOrderEntity"],
            "emits": ["OrderCreated"],
        }
    ],
    "queries": [
        {
            "id": "ListOrders",
            "input": {"tenant_id": "string", "limit": "integer"},
            "fetches": ["Order"],
            "guards": ["TenantIsolated"],
            "returns": ["Order[]"],
        }
    ],
    "events": [
        {
            "id": "OrderCreated",
            "type": "OrderCreated",
            "source_entity": "Order",
            "fields": [{"name": "order_id", "type": "string"}],
        }
    ],
}


# ============================================================================
# Test: Emitter Initialization
# ============================================================================

class TestEmitterInit:
    """Test khởi tạo Emitter class."""

    def test_emitter_initializes_with_fastapi_stack(self):
        """Test Emitter khởi tạo với stack='fastapi'."""
        from midicoder.pipeline.emitter import Emitter

        emitter = Emitter(stack="fastapi")
        assert emitter.stack == "fastapi"
        assert emitter.environment is not None

    def test_emitter_initializes_with_default_stack(self):
        """Test Emitter khởi tạo với default stack (fastapi)."""
        from midicoder.pipeline.emitter import Emitter

        emitter = Emitter()
        assert emitter.stack == "fastapi"

    def test_emitter_loads_jinja2_environment(self):
        """Test Emitter load Jinja2 Environment từ template directory."""
        from midicoder.pipeline.emitter import Emitter

        emitter = Emitter(stack="fastapi")
        # Kiểm tra environment được tạo và có template directory
        assert emitter.environment is not None
        # Kiểm tra loader có ít nhất 1 search path
        assert len(emitter.environment.loader.searchpath) > 0


# ============================================================================
# Test: Template Rendering
# ============================================================================

class TestEmitterRender:
    """Test render templates với context."""

    def test_render_simple_template(self, tmp_path):
        """Test render template đơn giản."""
        from midicoder.pipeline.emitter import Emitter

        # Tạo template file trực tiếp trong tmp_path
        template_file = tmp_path / "simple.txt.jinja2"
        template_file.write_text("Hello, {{ name }}!")

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        result = emitter.render("simple.txt.jinja2", {"name": "World"})
        assert result == "Hello, World!"

    def test_render_template_with_entity_context(self, tmp_path):
        """Test render template với entity context."""
        from midicoder.pipeline.emitter import Emitter

        # Tạo template file trực tiếp trong tmp_path
        template_file = tmp_path / "entity.py.jinja2"
        template_file.write_text(
            "class {{ entity.id }}:\n"
            "    \"\"\"{{ entity.description }}\"\"\"\n"
            "{% for field in entity.fields %}\n"
            "    {{ field.name }}: {{ field.type }}\n"
            "{% endfor %}"
        )

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        context = {
            "entity": {
                "id": "Order",
                "description": "Don hang",
                "fields": [
                    {"name": "order_id", "type": "str"},
                    {"name": "total", "type": "float"},
                ],
            }
        }

        result = emitter.render("entity.py.jinja2", context)
        assert "class Order:" in result
        assert "order_id: str" in result
        assert "total: float" in result

    def test_render_template_with_loop(self, tmp_path):
        """Test render template với loop entities."""
        from midicoder.pipeline.emitter import Emitter

        # Tạo template file trực tiếp trong tmp_path
        template_file = tmp_path / "models.py.jinja2"
        template_file.write_text(
            "{% for entity in entities %}\n"
            "class {{ entity.id }}: pass\n"
            "{% endfor %}"
        )

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        result = emitter.render("models.py.jinja2", SAMPLE_CONTEXT)
        assert "class Order: pass" in result

    def test_render_template_not_found_raises_error(self, tmp_path):
        """Test throw error khi template không tìm thấy."""
        from midicoder.pipeline.emitter import Emitter
        from midicoder.errors import MidicoderError

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        with pytest.raises(MidicoderError):
            emitter.render("nonexistent.jinja2", {})


# ============================================================================
# Test: Emit Files
# ============================================================================

class TestEmitterEmit:
    """Test emit files ra output directory."""

    def test_emit_creates_files(self, tmp_path):
        """Test emit tạo files trong output directory."""
        from midicoder.pipeline.emitter import Emitter
        from midicoder.pipeline.plan import FileSpec

        # Tạo template file trực tiếp trong tmp_path
        template_file = tmp_path / "main.py.jinja2"
        template_file.write_text("# Main app\napp = 'hello'")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        file_specs = [
            FileSpec(
                path="app/main.py",
                file_type="main",
                template="main.py.jinja2",
                context={},
                dependencies=[],
                metadata={}
            )
        ]

        result = emitter.emit(file_specs, output_dir)
        assert len(result) == 1
        assert result[0].path == "app/main.py"
        assert (output_dir / "app/main.py").exists()

    def test_emit_creates_directories(self, tmp_path):
        """Test emit tạo directories nếu chưa tồn tại."""
        from midicoder.pipeline.emitter import Emitter
        from midicoder.pipeline.plan import FileSpec

        # Tạo template file trực tiếp trong tmp_path
        template_file = tmp_path / "deep.py.jinja2"
        template_file.write_text("# Deep file")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        file_specs = [
            FileSpec(
                path="app/deep/nested/module.py",
                file_type="module",
                template="deep.py.jinja2",
                context={},
                dependencies=[],
                metadata={}
            )
        ]

        result = emitter.emit(file_specs, output_dir)
        assert (output_dir / "app/deep/nested/module.py").exists()


# ============================================================================
# Test: Integration — Emitter với Real Templates
# ============================================================================

class TestEmitterIntegration:
    """Test integration với real templates từ codebase."""

    def test_emitter_loads_real_fastapi_templates(self):
        """Test Emitter load real FastAPI templates từ stacks/fastapi/core/."""
        from midicoder.pipeline.emitter import Emitter

        emitter = Emitter(stack="fastapi")
        # Environment phải được load từ real template directory
        assert emitter.environment is not None


# ============================================================================
# Test: Error Handling
# ============================================================================

class TestEmitterErrors:
    """Test error handling trong Emitter."""

    def test_render_invalid_template_syntax(self, tmp_path):
        """Test xử lý template syntax invalid."""
        from midicoder.pipeline.emitter import Emitter
        from midicoder.errors import MidicoderError

        # Tạo template với syntax lỗi
        template_file = tmp_path / "broken.jinja2"
        template_file.write_text("{{ invalid syntax }}")

        emitter = Emitter(stack="test")
        emitter._template_dir = tmp_path

        with pytest.raises(MidicoderError):
            emitter.render("broken.jinja2", {})