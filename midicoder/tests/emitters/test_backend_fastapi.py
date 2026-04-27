"""
Tests cho BackendFastAPIEmitter.

Test suite cho FastAPI backend code generator.
Theo nguyên tắc TDD: tests được viết trước implementation.

CP01: Domain Model
CP08: Database & Data Access
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from midicoder.pipeline.mir import MIR, MIRBuilder
from midicoder.emitters.backend_fastapi import (
    BackendFastAPIEmitter,
    GeneratedFile,
)
from midicoder.errors import MidicoderErrorManager as EM, ErrorCode


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
                {"name": "order_id", "type": "str", "primary_key": True},
                {"name": "tenant_id", "type": "str"},
                {"name": "total", "type": "float"},
                {"name": "status", "type": "str"},
            ],
            "tenant_scope": "tenant_isolated",
        },
        {
            "id": "Product",
            "description": "Sản phẩm",
            "fields": [
                {"name": "product_id", "type": "str", "primary_key": True},
                {"name": "tenant_id", "type": "str"},
                {"name": "name", "type": "str"},
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
        BackendFastAPIEmitter instance
    """
    # Tạo stack directory
    stack_dir = tmp_path / "stacks" / "fastapi" / "templates"
    stack_dir.mkdir(parents=True)
    
    # Tạo mock templates cơ bản
    (stack_dir / "__init__.py.jinja2").write_text("# {{ module_name }} package\n")
    
    (stack_dir / "main.py.jinja2").write_text("""# FastAPI Main
from fastapi import FastAPI

app = FastAPI(title="Midicoder API")
""")
    
    (stack_dir / "config.py.jinja2").write_text("""# Configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Midicoder"
""")
    
    (stack_dir / "database.py.jinja2").write_text("""# Database
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://localhost/app"
engine = create_async_engine(DATABASE_URL)
""")
    
    (stack_dir / "model.py.jinja2").write_text("""# {{ entity['id'] }} Model
from sqlalchemy import Column, String, Float
from .base import Base

class {{ entity['id'] }}(Base):
    __tablename__ = '{{ entity['id'] | lower }}s'
    
{% for field in entity['fields'] %}
    {{ field['name'] }} = Column(String)
{% endfor %}
""")
    
    (stack_dir / "repository.py.jinja2").write_text("""# {{ entity['id'] }} Repository
from .base_repository import BaseRepository
from .models.{{ entity['id'] | lower }} import {{ entity['id'] }}

class {{ entity['id'] }}Repository(BaseRepository[{{ entity['id'] }}]):
    model = {{ entity['id'] }}
""")
    
    # Tạo db subdirectory với templates
    db_dir = stack_dir / "db"
    db_dir.mkdir(parents=True)
    (db_dir / "database.py.jinja2").write_text("""# Database
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://localhost/app"
engine = create_async_engine(DATABASE_URL)
""")
    (db_dir / "base_model.py.jinja2").write_text("""# Base Model
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""")
    (db_dir / "base_repository.py.jinja2").write_text("""# Base Repository
from abc import ABC

class BaseRepository(ABC):
    pass
""")
    
    return BackendFastAPIEmitter(stack_dir)


# ============================================================================
# Tests: Initialization
# ============================================================================

class TestBackendFastAPIEmitterInit:
    """Tests cho BackendFastAPIEmitter initialization."""
    
    def test_init_with_valid_stack_dir(self, tmp_path: Path):
        """
        Test: Init với valid stack directory thành công.
        
        Assert:
            - Emitter được tạo thành công
            - stack_dir được set đúng
        """
        stack_dir = tmp_path / "stacks" / "fastapi" / "templates"
        stack_dir.mkdir(parents=True)
        
        emitter = BackendFastAPIEmitter(stack_dir)
        
        assert emitter.stack_dir == stack_dir
        assert emitter.template_env is not None
    
    def test_init_with_nonexistent_stack_dir(self, tmp_path: Path):
        """
        Test: Init với nonexistent stack directory → raise error.
        
        Assert:
            - EM.raise_error được gọi với EMITTER_TEMPLATE_NOT_FOUND
        """
        stack_dir = tmp_path / "nonexistent" / "templates"
        
        with pytest.raises(Exception) as exc_info:
            BackendFastAPIEmitter(stack_dir)
        
        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Tests: Base Files Generation
# ============================================================================

class TestEmitBaseFiles:
    """Tests cho base files generation."""
    
    def test_emit_base_files_creates_main_py(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → main.py được tạo.
        
        Assert:
            - main.py tồn tại trong generated files
            - Content không empty
        """
        output_dir = tmp_path / "output" / "api"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        main_file = next((f for f in files if "main.py" in str(f.path)), None)
        assert main_file is not None
        assert main_file.content.strip() != ""
    
    def test_emit_base_files_creates_config_py(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → config.py được tạo.
        """
        output_dir = tmp_path / "output" / "api"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        config_file = next((f for f in files if "config.py" in str(f.path)), None)
        assert config_file is not None
    
    def test_emit_base_files_creates_database_py(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → database.py được tạo.
        """
        output_dir = tmp_path / "output" / "api"
        
        files = emitter_with_mock_stack._emit_base_files(output_dir)
        
        db_file = next((f for f in files if "database.py" in str(f.path)), None)
        assert db_file is not None
    
    def test_emit_base_files_creates_directories(self, emitter_with_mock_stack, tmp_path: Path):
        """
        Test: Emit base files → directories được tạo tự động.
        
        Assert:
            - app/ directory được tạo
            - models/, schemas/, repositories/, routes/ được tạo
        """
        output_dir = tmp_path / "output" / "api"
        
        emitter_with_mock_stack._emit_base_files(output_dir)
        
        assert (output_dir / "app").exists()
        assert (output_dir / "app" / "models").exists()
        assert (output_dir / "app" / "schemas").exists()
        assert (output_dir / "app" / "repositories").exists()
        assert (output_dir / "app" / "routes").exists()


# ============================================================================
# Tests: Entity Generation
# ============================================================================

class TestEmitEntity:
    """Tests cho entity files generation."""
    
    def test_emit_entity_creates_model(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → model file được tạo.
        
        Assert:
            - order.py model file tồn tại
            - Content có class Order
        """
        output_dir = tmp_path / "output" / "api"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        model_file = next((f for f in files if "order.py" in str(f.path)), None)
        assert model_file is not None
        assert "Order" in model_file.content
    
    def test_emit_entity_creates_repository(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity → repository file được tạo.
        
        Assert:
            - order_repo.py repository file tồn tại
        """
        output_dir = tmp_path / "output" / "api"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        repo_file = next((f for f in files if "order_repo.py" in str(f.path)), None)
        assert repo_file is not None
    
    def test_emit_entity_with_tenant_scope(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit entity với tenant_scope → tenant_id field được include.
        
        Assert:
            - Model content có tenant_id field
        """
        output_dir = tmp_path / "output" / "api"
        
        entity = sample_mir_with_entities.metadata["entities"][0]
        files = emitter_with_mock_stack._emit_entity(entity, output_dir)
        
        model_file = next((f for f in files if "order.py" in str(f.path)), None)
        assert "tenant_id" in model_file.content


# ============================================================================
# Tests: Full Emit Pipeline
# ============================================================================

class TestEmit:
    """Tests cho full emit pipeline."""
    
    def test_emit_with_empty_mir(self, emitter_with_mock_stack, sample_mir_empty, tmp_path: Path):
        """
        Test: Emit với MIR trống → chỉ generate base files.
        
        Assert:
            - Chỉ có base files (main.py, config.py, database.py)
            - Không có entity files
        """
        output_dir = tmp_path / "output" / "api"
        
        files = emitter_with_mock_stack.emit(sample_mir_empty, output_dir)
        
        # Chỉ có base files
        assert any("main.py" in str(f.path) for f in files)
        assert any("config.py" in str(f.path) for f in files)
        assert any("database.py" in str(f.path) for f in files)
    
    def test_emit_with_entities(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit với MIR có entities → generate base + entity files.
        
        Assert:
            - Base files tồn tại
            - Entity files (Order, Product) tồn tại
        """
        output_dir = tmp_path / "output" / "api"
        
        files = emitter_with_mock_stack.emit(sample_mir_with_entities, output_dir)
        
        # Base files
        assert any("main.py" in str(f.path) for f in files)
        assert any("config.py" in str(f.path) for f in files)
        
        # Entity files
        assert any("order.py" in str(f.path) for f in files)
        assert any("product.py" in str(f.path) for f in files)
        assert any("order_repo.py" in str(f.path) for f in files)
        assert any("product_repo.py" in str(f.path) for f in files)
    
    def test_emit_returns_generated_file_list(self, emitter_with_mock_stack, sample_mir_with_entities, tmp_path: Path):
        """
        Test: Emit → return list của GeneratedFile.
        
        Assert:
            - Return là list
            - Mỗi item là GeneratedFile instance
        """
        output_dir = tmp_path / "output" / "api"
        
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
        
        emitter = BackendFastAPIEmitter(tmp_path)
        
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
        stack_dir = tmp_path / "stacks" / "fastapi" / "templates"
        stack_dir.mkdir(parents=True)
        
        # Create templates
        (stack_dir / "__init__.py.jinja2").write_text("# {{ module_name }}")
        (stack_dir / "main.py.jinja2").write_text("# Main")
        (stack_dir / "config.py.jinja2").write_text("# Config")
        (stack_dir / "model.py.jinja2").write_text("# {{ entity['id'] }} Model")
        (stack_dir / "repository.py.jinja2").write_text("# {{ entity['id'] }} Repository")
        
        # Create db subdirectory with templates
        db_dir = stack_dir / "db"
        db_dir.mkdir(parents=True)
        (db_dir / "database.py.jinja2").write_text("# Database")
        (db_dir / "base_model.py.jinja2").write_text("# Base Model")
        (db_dir / "base_repository.py.jinja2").write_text("# Base Repository")
        
        output_dir = tmp_path / "output" / "api"
        
        # Execute
        emitter = BackendFastAPIEmitter(stack_dir)
        files = emitter.emit(sample_mir_with_entities, output_dir)
        
        # Verify
        assert len(files) > 0
        
        # Verify files on disk
        main_path = output_dir / "app" / "main.py"
        assert main_path.exists()
        assert main_path.read_text() == "# Main"
        
        # Verify entity model
        order_model_path = output_dir / "app" / "models" / "order.py"
        assert order_model_path.exists()