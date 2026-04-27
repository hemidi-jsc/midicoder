"""
Unit Tests cho Docker Compose Generator.

Tests cho:
- InfrastructureConfig dataclass
- DockerComposeGenerator.extract_infrastructure()
- DockerComposeGenerator.render_template()
- DockerComposeGenerator.write_compose()
- DockerComposeGenerator.generate() (full pipeline)

Sử dụng pytest và unittest.mock.

Cách chạy:
    pytest midicoder/tests/infra/test_docker.py -v
    pytest midicoder/tests/infra/test_docker.py -v --tb=short

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from midicoder.infra.docker import (
    DockerComposeGenerator,
    InfrastructureConfig,
    DEFAULT_BACKEND_PORT,
    DEFAULT_FRONTEND_PORT
)
from midicoder.pipeline.mir import MIR, Operation, DataFlow, Boundary
from midicoder.errors import MidicoderError, ErrorCode


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_mir_with_backend():
    """MIR với backend operations."""
    mir = MIR()
    mir.operations.append(Operation(
        op_id="create_order_001",
        op_type="create_order_api",
        params={"entity": "Order", "fields": ["order_id", "tenant_id"]},
        obligation_refs=["tenant_oblig_001"]
    ))
    mir.operations.append(Operation(
        op_id="list_orders_001",
        op_type="list_orders_api",
        params={"entity": "Order"},
        obligation_refs=[]
    ))
    mir.metadata = {"backend_stack": "fastapi", "frontend_stack": "angular"}
    return mir


@pytest.fixture
def sample_mir_with_frontend():
    """MIR với frontend operations."""
    mir = MIR()
    mir.operations.append(Operation(
        op_id="order_list_page_001",
        op_type="order_list_page",
        params={"page": "OrderList"},
        obligation_refs=[]
    ))
    mir.operations.append(Operation(
        op_id="order_form_component_001",
        op_type="order_form_component",
        params={"component": "OrderForm"},
        obligation_refs=[]
    ))
    mir.metadata = {"backend_stack": "fastapi", "frontend_stack": "angular"}
    return mir


@pytest.fixture
def sample_mir_fullstack():
    """MIR với cả backend và frontend operations."""
    mir = MIR()
    # Backend operations
    mir.operations.append(Operation(
        op_id="create_order_001",
        op_type="create_order_api",
        params={"entity": "Order"},
        obligation_refs=["tenant_oblig_001"]
    ))
    mir.operations.append(Operation(
        op_id="get_order_001",
        op_type="get_order_service",
        params={"entity": "Order"},
        obligation_refs=[]
    ))
    # Frontend operations
    mir.operations.append(Operation(
        op_id="order_list_view_001",
        op_type="order_list_view",
        params={"view": "OrderList"},
        obligation_refs=[]
    ))
    mir.operations.append(Operation(
        op_id="order_detail_page_001",
        op_type="order_detail_page",
        params={"page": "OrderDetail"},
        obligation_refs=[]
    ))
    mir.metadata = {"backend_stack": "nestjs", "frontend_stack": "react"}
    return mir


@pytest.fixture
def sample_mir_empty():
    """MIR không có operations."""
    mir = MIR()
    mir.metadata = {"backend_stack": "fastapi"}
    return mir


@pytest.fixture
def generator():
    """DockerComposeGenerator instance."""
    return DockerComposeGenerator()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    output_dir = tmp_path / ".midicoder" / "versions" / "v1.0.0" / "src"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# ============================================================================
# Tests cho InfrastructureConfig
# ============================================================================

class TestInfrastructureConfig:
    """Tests cho InfrastructureConfig dataclass."""

    def test_default_config(self):
        """Test default values của InfrastructureConfig."""
        config = InfrastructureConfig()
        
        assert config.has_backend is False
        assert config.has_frontend is False
        assert config.backend_stack == "fastapi"
        assert config.frontend_stack == "angular"
        assert config.backend_port == DEFAULT_BACKEND_PORT
        assert config.frontend_port == DEFAULT_FRONTEND_PORT
        assert config.postgres_database == "midicoder"
        assert config.neo4j_user == "neo4j"
        # Random values generated
        assert len(config.postgres_password) > 0
        assert len(config.neo4j_password) > 0
        assert len(config.jwt_secret) > 0

    def test_services_list_initialized(self):
        """Test services list được initialize đúng trong __post_init__."""
        config = InfrastructureConfig(has_backend=True, has_frontend=True)
        
        assert "backend" in config.services
        assert "frontend" in config.services
        assert "postgres" in config.services
        assert "redis" in config.services
        assert "neo4j" in config.services

    def test_services_list_backend_only(self):
        """Test services list với chỉ backend."""
        config = InfrastructureConfig(has_backend=True, has_frontend=False)
        
        assert "backend" in config.services
        assert "frontend" not in config.services
        assert "postgres" in config.services

    def test_services_list_frontend_only(self):
        """Test services list với chỉ frontend."""
        config = InfrastructureConfig(has_backend=False, has_frontend=True)
        
        assert "backend" not in config.services
        assert "frontend" in config.services
        assert "postgres" in config.services

    def test_custom_ports(self):
        """Test custom ports."""
        config = InfrastructureConfig(backend_port=3000, frontend_port=8080)
        
        assert config.backend_port == 3000
        assert config.frontend_port == 8080


# ============================================================================
# Tests cho DockerComposeGenerator.extract_infrastructure
# ============================================================================

class TestExtractInfrastructure:
    """Tests cho extract_infrastructure method."""

    def test_detect_backend_from_api_operations(self, generator, sample_mir_with_backend):
        """Test detect backend từ API operations."""
        config = generator.extract_infrastructure(sample_mir_with_backend)
        
        assert config.has_backend is True
        assert config.backend_stack == "fastapi"

    def test_detect_backend_from_service_operations(self, generator):
        """Test detect backend từ service operations."""
        mir = MIR()
        mir.operations.append(Operation(
            op_id="user_service_001",
            op_type="user_service",
            params={"entity": "User"}
        ))
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_backend is True

    def test_detect_frontend_from_page_operations(self, generator, sample_mir_with_frontend):
        """Test detect frontend từ page operations."""
        config = generator.extract_infrastructure(sample_mir_with_frontend)
        
        assert config.has_frontend is True
        assert config.frontend_stack == "angular"

    def test_detect_frontend_from_component_operations(self, generator):
        """Test detect frontend từ component operations."""
        mir = MIR()
        mir.operations.append(Operation(
            op_id="nav_component_001",
            op_type="nav_component",
            params={"component": "Navbar"}
        ))
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_frontend is True

    def test_detect_fullstack(self, generator, sample_mir_fullstack):
        """Test detect cả backend và frontend."""
        config = generator.extract_infrastructure(sample_mir_fullstack)
        
        assert config.has_backend is True
        assert config.has_frontend is True
        assert config.backend_stack == "nestjs"
        assert config.frontend_stack == "react"

    def test_empty_mir_returns_no_services(self, generator, sample_mir_empty):
        """Test empty MIR trả về không có services."""
        config = generator.extract_infrastructure(sample_mir_empty)
        
        assert config.has_backend is False
        assert config.has_frontend is False

    def test_override_backend_stack(self, generator, sample_mir_with_backend):
        """Test override backend stack từ override_config."""
        config = generator.extract_infrastructure(
            sample_mir_with_backend,
            override_config={"backend_stack": "nestjs", "frontend_stack": "react"}
        )
        
        assert config.backend_stack == "nestjs"
        assert config.frontend_stack == "react"

    def test_metadata_stack_override(self, generator):
        """Test stack từ MIR metadata override detection."""
        mir = MIR()
        mir.operations.append(Operation(
            op_id="api_001",
            op_type="user_api",
            params={}
        ))
        mir.metadata = {"backend_stack": "nestjs", "frontend_stack": "react"}
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_backend is True
        assert config.backend_stack == "nestjs"


# ============================================================================
# Tests cho DockerComposeGenerator.render_template
# ============================================================================

class TestRenderTemplate:
    """Tests cho render_template method."""

    def test_render_fullstack_compose(self, generator):
        """Test render Docker Compose với fullstack config."""
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_stack="fastapi",
            frontend_stack="angular"
        )
        
        compose_content = generator.render_template(config)
        
        assert "version: \"3.8\"" in compose_content
        assert "backend:" in compose_content
        assert "frontend:" in compose_content
        assert "postgres:" in compose_content
        assert "redis:" in compose_content
        assert "neo4j:" in compose_content

    def test_render_backend_only_compose(self, generator):
        """Test render Docker Compose với chỉ backend."""
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=False
        )
        
        compose_content = generator.render_template(config)
        
        assert "backend:" in compose_content
        assert "frontend:" not in compose_content
        assert "postgres:" in compose_content

    def test_render_backend_only_no_frontend_service(self, generator):
        """Test render khi frontend service không tồn tại."""
        config = InfrastructureConfig(
            has_backend=False,
            has_frontend=False
        )
        
        compose_content = generator.render_template(config)
        
        assert "backend:" not in compose_content
        assert "frontend:" not in compose_content
        # Infrastructure services vẫn tồn tại
        assert "postgres:" in compose_content

    def test_render_custom_ports(self, generator):
        """Test render với custom ports."""
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_port=3000,
            frontend_port=8080
        )
        
        compose_content = generator.render_template(config)
        
        assert "3000:8000" in compose_content
        assert "8080:4200" in compose_content

    def test_template_not_found_raises_error(self):
        """Test template không tìm thấy throw error."""
        generator = DockerComposeGenerator(template_path="/nonexistent/path/template.j2")
        config = InfrastructureConfig()
        
        with pytest.raises(MidicoderError) as exc_info:
            generator.render_template(config)
        
        assert exc_info.value.code == ErrorCode.INFRA_TEMPLATE_NOT_FOUND


# ============================================================================
# Tests cho DockerComposeGenerator.write_compose
# ============================================================================

class TestWriteCompose:
    """Tests cho write_compose method."""

    def test_write_compose_creates_file(self, generator, temp_output_dir):
        """Test write_compose tạo file thành công."""
        compose_content = "version: \"3.8\"\nservices:\n  test:\n    image: test"
        output_path = temp_output_dir / "docker-compose.yml"
        
        generator.write_compose(compose_content, output_path)
        
        assert output_path.exists()
        assert output_path.read_text() == compose_content

    def test_write_compose_creates_directory(self, generator, tmp_path):
        """Test write_compose tạo directory nếu không tồn tại."""
        compose_content = "version: \"3.8\""
        output_path = tmp_path / "new" / "dir" / "docker-compose.yml"
        
        generator.write_compose(compose_content, output_path)
        
        assert output_path.exists()
        assert output_path.parent.exists()


# ============================================================================
# Tests cho DockerComposeGenerator.generate (full pipeline)
# ============================================================================

class TestGenerate:
    """Tests cho generate method (full pipeline)."""

    def test_generate_full_pipeline(self, generator, sample_mir_fullstack, temp_output_dir):
        """Test full generate pipeline."""
        output_path = temp_output_dir / "docker-compose.yml"
        
        config = generator.generate(sample_mir_fullstack, output_path)
        
        assert output_path.exists()
        assert config.has_backend is True
        assert config.has_frontend is True
        
        compose_content = output_path.read_text()
        assert "backend:" in compose_content
        assert "frontend:" in compose_content

    def test_generate_with_override_config(self, generator, sample_mir_with_backend, temp_output_dir):
        """Test generate với override config."""
        output_path = temp_output_dir / "docker-compose.yml"
        
        config = generator.generate(
            sample_mir_with_backend,
            output_path,
            override_config={"backend_stack": "nestjs"}
        )
        
        assert config.backend_stack == "nestjs"

    def test_generate_backend_only(self, generator, sample_mir_with_backend, temp_output_dir):
        """Test generate với chỉ backend MIR."""
        output_path = temp_output_dir / "docker-compose.yml"
        
        config = generator.generate(sample_mir_with_backend, output_path)
        
        assert config.has_backend is True
        assert config.has_frontend is False
        
        compose_content = output_path.read_text()
        assert "backend:" in compose_content
        assert "frontend:" not in compose_content


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests cho Docker Compose generation."""

    def test_generated_compose_is_valid_yaml(self, generator, sample_mir_fullstack, temp_output_dir):
        """Test generated compose là valid YAML."""
        import yaml
        
        output_path = temp_output_dir / "docker-compose.yml"
        generator.generate(sample_mir_fullstack, output_path)
        
        # Parse YAML
        compose_data = yaml.safe_load(output_path.read_text())
        
        assert "version" in compose_data
        assert "services" in compose_data
        assert "backend" in compose_data["services"]
        assert "frontend" in compose_data["services"]
        assert "postgres" in compose_data["services"]

    def test_generated_compose_has_required_services(self, generator, sample_mir_fullstack, temp_output_dir):
        """Test generated compose có required services."""
        import yaml
        
        output_path = temp_output_dir / "docker-compose.yml"
        generator.generate(sample_mir_fullstack, output_path)
        
        compose_data = yaml.safe_load(output_path.read_text())
        services = compose_data["services"]
        
        # Backend service
        assert "build" in services["backend"]
        assert "ports" in services["backend"]
        assert "environment" in services["backend"]
        
        # Frontend service
        assert "build" in services["frontend"]
        assert "ports" in services["frontend"]
        
        # Database services
        assert "image" in services["postgres"]
        assert "image" in services["redis"]
        assert "image" in services["neo4j"]


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests cho edge cases."""

    def test_mir_with_no_operations(self, generator):
        """Test MIR không có operations."""
        mir = MIR()
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_backend is False
        assert config.has_frontend is False

    def test_mir_with_many_operations(self, generator):
        """Test MIR với nhiều operations."""
        mir = MIR()
        # Thêm nhiều operations
        for i in range(100):
            mir.operations.append(Operation(
                op_id=f"op_{i}",
                op_type=f"api_operation_{i}",
                params={}
            ))
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_backend is True

    def test_case_insensitive_detection(self, generator):
        """Test detection không phân biệt case."""
        mir = MIR()
        mir.operations.append(Operation(
            op_id="OP_001",
            op_type="API_OPERATION",  # Uppercase
            params={}
        ))
        
        config = generator.extract_infrastructure(mir)
        
        assert config.has_backend is True