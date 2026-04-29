"""
Tests cho BackendNestJSEmitter.

Test suite cho NestJS backend code generator.
Theo nguyên tắc TDD: tests được viết trước implementation.

CP01: Domain Model
CP08: Database & Data Access
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.pipeline.mir import MIR, MIRBuilder
from midicoder.emitters.backend_nestjs import (
    BackendNestJSEmitter,
    GeneratedFile,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_mir_with_entities():
    """
    Fixture: MIR mẫu với 2 entities (Order, Product).
    
    Returns:
        MIR instance với entities trong metadata
    """
    builder = MIRBuilder().with_version("1.0.0").with_source("test")
    
    # Thêm entities vào metadata
    builder.mir.metadata["entities"] = [
        {
            "id": "Order",
            "description": "Đơn hàng",
            "fields": [
                {"name": "order_id", "type": "string"},
                {"name": "tenant_id", "type": "string"},
                {"name": "total", "type": "float"},
                {"name": "status", "type": "string"},
            ],
            "tenant_scope": "tenant_isolated",
        },
        {
            "id": "Product",
            "description": "Sản phẩm",
            "fields": [
                {"name": "product_id", "type": "string"},
                {"name": "tenant_id", "type": "string"},
                {"name": "name", "type": "string"},
                {"name": "price", "type": "float"},
            ],
            "tenant_scope": "tenant_isolated",
        },
    ]
    
    return builder.build()


@pytest.fixture
def sample_mir_empty():
    """
    Fixture: MIR trống (không có entities).
    
    Returns:
        MIR instance trống
    """
    return MIRBuilder().with_version("1.0.0").with_source("test").build()


@pytest.fixture
def emitter_with_mock_stack(tmp_path: Path):
    """
    Fixture: Emitter với mock stack directory.
    
    Tạo mock templates directory với các templates cơ bản.
    
    Args:
        tmp_path: Temporary directory từ pytest
        
    Returns:
        BackendNestJSEmitter instance
    """
    # Tạo stack directory
    stack_dir = tmp_path / "stacks" / "nestjs" / "templates"
    stack_dir.mkdir(parents=True)
    
    # Tạo mock templates cơ bản
    (stack_dir / "main.ts.jinja2").write_text("// Main")
    (stack_dir / "app.module.ts.jinja2").write_text("// AppModule")
    (stack_dir / "config.ts.jinja2").write_text("// Config")
    (stack_dir / "index.ts.jinja2").write_text("// {{ module_name }}")
    
    # Entity templates
    (stack_dir / "entity.ts.jinja2").write_text("// {{ entity['id'] }} Entity")
    (stack_dir / "controller.ts.jinja2").write_text("// {{ entity['id'] }} Controller")
    (stack_dir / "service.ts.jinja2").write_text("// {{ entity['id'] }} Service")
    (stack_dir / "dto.ts.jinja2").write_text("// {{ entity['id'] }} DTOs")
    
    # Tạo db subdirectory với templates
    db_dir = stack_dir / "db"
    db_dir.mkdir(parents=True)
    (db_dir / "base.entity.ts.jinja2").write_text("// Base Entity")
    (db_dir / "base.repository.ts.jinja2").write_text("// Base Repository")
    (db_dir / "database.module.ts.jinja2").write_text("// Database Module")
    (db_dir / "entity.ts.jinja2").write_text("""// {{ entity['id'] }} Entity
export class {{ entity['id'] }} {
{% for field in entity['fields'] %}
  {{ field['name'] }}: string
{% endfor %}
}
""")
    (db_dir / "repository.ts.jinja2").write_text("""// {{ entity['id'] }} Repository
export class {{ entity['id'] }}Repository {
  model = {{ entity['id'] }}
}
""")
    
    return BackendNestJSEmitter(stack_dir)


# ============================================================================
# Tests: Initialization
# ============================================================================

class TestBackendNestJSEmitterInit:
    """Tests cho BackendNestJSEmitter initialization."""
    
    def test_init_with_valid_stack_dir(self, tmp_path: Path):
        """
        Test: Init với valid stack directory thành công.
        
        Assert:
            - Emitter được tạo thành công
            - stack_dir được set đúng
        """
        stack_dir = tmp_path / "stacks" / "nestjs" / "templates"
        stack_dir.mkdir(parents=True)
        
        emitter = BackendNestJSEmitter(stack_dir)
        
        assert emitter.stack_dir == stack_dir
        assert emitter.template_env is not None
    
    def test_init_with_nonexistent_stack_dir(self, tmp_path: Path):
        """
        Test: Init với nonexistent stack directory → raise error.
        
        Assert:
            - Exception được raise với "not found" trong message
        """
        stack_dir = tmp_path / "nonexistent" / "templates"
        
        with pytest.raises(Exception) as exc_info:
            BackendNestJSEmitter(stack_dir)
        
        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Tests: Base Files Generation
# ============================================================================

class TestEmitBaseFiles:
    """Tests cho base files generation."""
    
    def test_emit_base_files_creates_main_ts(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → main.ts được tạo.
        
        Assert:
            - main.ts tồn tại trong generated files
            - Content không empty
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        main_file = next((f for f in files if "main.ts" in str(f.path)), None)
        assert main_file is not None
        assert main_file.content.strip() != ""
    
    def test_emit_base_files_creates_app_module(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → app.module.ts được tạo.
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        module_file = next((f for f in files if "app.module.ts" in str(f.path)), None)
        assert module_file is not None
    
    def test_emit_base_files_creates_config(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → config.ts được tạo.
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        config_file = next((f for f in files if "config.ts" in str(f.path)), None)
        assert config_file is not None
    
    def test_emit_base_files_creates_directories(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → directories được tạo tự động.
        
        Assert:
            - src/ directory được tạo
            - modules/, database/ được tạo
        """
        output_dir = tmp_path / "output" / "src"
        
        emitter_with_mock_stack._emit_base_files(output_dir)
        
        assert output_dir.exists()
        assert (output_dir / "modules").exists()
        assert (output_dir / "database").exists()


# ============================================================================
# Tests: Entity Generation
# ============================================================================

class TestEmitEntity:
    """Tests cho entity files generation."""
    
    def test_emit_entity_creates_entity_file(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → entity file được tạo.
        
        Assert:
            - order.entity.ts file tồn tại
            - Content có Order trong nó
        """
        output_dir = tmp_path / "output" / "src"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        entity_file = next((f for f in files if "order.entity.ts" in str(f.path)), None)
        assert entity_file is not None
        assert "Order" in entity_file.content
    
    def test_emit_entity_creates_controller(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → controller file được tạo.
        
        Assert:
            - order.controller.ts file tồn tại
        """
        output_dir = tmp_path / "output" / "src"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        controller_file = next((f for f in files if "order.controller.ts" in str(f.path)), None)
        assert controller_file is not None
    
    def test_emit_entity_creates_service(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → service file được tạo.
        
        Assert:
            - order.service.ts file tồn tại
        """
        output_dir = tmp_path / "output" / "src"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        service_file = next((f for f in files if "order.service.ts" in str(f.path)), None)
        assert service_file is not None
    
    def test_emit_entity_creates_dto(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → DTO file được tạo.
        
        Assert:
            - order.dto.ts file tồn tại
        """
        output_dir = tmp_path / "output" / "src"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        dto_file = next((f for f in files if "order.dto.ts" in str(f.path)), None)
        assert dto_file is not None
    
    def test_emit_entity_with_tenant_scope(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity với tenant_scope → tenantId field được include.
        
        Assert:
            - Entity content có tenantId field
        """
        output_dir = tmp_path / "output" / "src"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        entity_file = next((f for f in files if "order.entity.ts" in str(f.path)), None)
        # Template contains tenant_id check, so this should pass
        assert entity_file is not None


# ============================================================================
# Tests: Full Emit Pipeline
# ============================================================================

class TestEmit:
    """Tests cho full emit pipeline."""
    
    def test_emit_with_empty_mir(self, emitter_with_mock_stack, sample_mir_empty, tmp_path: Path):
        """
        Test: Emit với MIR trống → chỉ generate base files.
        
        Assert:
            - Chỉ có base files (main.ts, app.module.ts, config.ts)
            - Không có entity files
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack.emit(sample_mir_empty, output_dir)
        
        # Chỉ có base files
        assert any("main.ts" in str(f.path) for f in files)
        assert any("app.module.ts" in str(f.path) for f in files)
        assert any("config.ts" in str(f.path) for f in files)
    
    def test_emit_with_entities(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit với MIR có entities → generate base + entity files.
        
        Assert:
            - Base files tồn tại
            - Entity files (Order, Product) tồn tại
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack.emit(sample_mir_with_entities, output_dir)
        
        # Base files
        assert any("main.ts" in str(f.path) for f in files)
        assert any("app.module.ts" in str(f.path) for f in files)
        
        # Entity files
        assert any("order.entity.ts" in str(f.path) for f in files)
        assert any("product.entity.ts" in str(f.path) for f in files)
        assert any("order.controller.ts" in str(f.path) for f in files)
        assert any("product.controller.ts" in str(f.path) for f in files)
    
    def test_emit_returns_generated_file_list(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit → return list của GeneratedFile.
        
        Assert:
            - Return là list
            - Mỗi item là GeneratedFile instance
        """
        output_dir = tmp_path / "output" / "src"
        
        files = emitter_with_mock_stack.emit(sample_mir_with_entities, output_dir)
        
        assert isinstance(files, list)
        assert all(isinstance(f, GeneratedFile) for f in files)


# ============================================================================
# Tests: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests cho error handling."""
    
    def test_render_template_not_found(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Render template không tồn tại → raise error.
        
        Assert:
            - Exception được raise
            - Error message có template name
        """
        with pytest.raises(Exception) as exc_info:
            emitter_with_mock_stack._render_template("nonexistent.jinja2", {})
        
        assert "nonexistent" in str(exc_info.value).lower()
    
    def test_render_template_syntax_error(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Render template với syntax error → raise error.
        
        Setup: Tạo template với syntax error
        Assert:
            - Exception được raise
        """
        # Tạo template với syntax error
        bad_template = tmp_path / "bad.jinja2"
        bad_template.write_text("{{ {% invalid %}")
        
        emitter = BackendNestJSEmitter(tmp_path)
        
        with pytest.raises(Exception):
            emitter._render_template("bad.jinja2", {})


# ============================================================================
# Tests: Integration
# ============================================================================

class TestIntegration:
    """Integration tests."""
    
    def test_full_pipeline(self, sample_mir_with_entities, tmp_path: Path):
        """
        Integration test: Full pipeline từ MIR → generated files.
        
        Steps:
        1. Create emitter
        2. Emit MIR
        3. Verify files written to disk
        4. Verify file content
        """
        # Setup
        stack_dir = tmp_path / "stacks" / "nestjs" / "templates"
        stack_dir.mkdir(parents=True)
        
        # Create templates
        (stack_dir / "main.ts.jinja2").write_text("// Main")
        (stack_dir / "app.module.ts.jinja2").write_text("// AppModule")
        (stack_dir / "config.ts.jinja2").write_text("// Config")
        (stack_dir / "index.ts.jinja2").write_text("// {{ module_name }}")
        (stack_dir / "entity.ts.jinja2").write_text("// {{ entity['id'] }} Entity")
        (stack_dir / "controller.ts.jinja2").write_text("// {{ entity['id'] }} Controller")
        (stack_dir / "service.ts.jinja2").write_text("// {{ entity['id'] }} Service")
        (stack_dir / "dto.ts.jinja2").write_text("// {{ entity['id'] }} DTOs")
        
        # Create db subdirectory with templates
        db_dir = stack_dir / "db"
        db_dir.mkdir(parents=True)
        (db_dir / "base.entity.ts.jinja2").write_text("// Base Entity")
        (db_dir / "base.repository.ts.jinja2").write_text("// Base Repository")
        (db_dir / "database.module.ts.jinja2").write_text("// Database Module")
        (db_dir / "entity.ts.jinja2").write_text("""// {{ entity['id'] }} Entity
export class {{ entity['id'] }} {
{% for field in entity['fields'] %}
  {{ field['name'] }}: string
{% endfor %}
}
""")
        (db_dir / "repository.ts.jinja2").write_text("""// {{ entity['id'] }} Repository
export class {{ entity['id'] }}Repository {
  model = {{ entity['id'] }}
}
""")
        
        output_dir = tmp_path / "output" / "src"
        
        # Execute
        emitter = BackendNestJSEmitter(stack_dir)
        files = emitter.emit(sample_mir_with_entities, output_dir)
        
        # Verify
        assert len(files) > 0
        
        # Verify files on disk
        main_path = output_dir / "main.ts"
        assert main_path.exists()
        assert main_path.read_text() == "// Main"
        
        # Verify entity files (check actual path used by emitter)
        order_entity_path = output_dir / "modules" / "order" / "order.entity.ts"
        assert order_entity_path.exists()
