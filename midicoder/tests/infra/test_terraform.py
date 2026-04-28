"""
Unit tests cho AWS Terraform Generator module.

Tests này follow TDD approach:
- Test data class AWSInfrastructureConfig
- Test TerraformGenerator class methods
- Test template rendering
- Test file writing
- Integration tests cho full pipeline

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_mir():
    """Fixture cho sample MIR object."""
    from midicoder.pipeline.mir import MIR, MIRBuilder

    builder = MIRBuilder()
    builder.add_operation(
        op_id="api_create_order",
        op_type="api.handler",
        params={"entity": "Order", "method": "POST"},
    )
    builder.add_operation(
        op_id="db_persist_order",
        op_type="db.repository",
        params={"entity": "Order", "action": "persist"},
    )
    builder.add_operation(
        op_id="cache_order",
        op_type="cache.set",
        params={"key": "order:{id}"},
        obligation_refs=["cache"],
    )
    builder.add_operation(
        op_id="graph_relationship",
        op_type="graph.knowledge",
        params={"node": "Order", "relationship": "BELONGS_TO"},
    )
    builder.add_operation(
        op_id="storage_upload",
        op_type="storage.upload",
        params={"bucket": "orders", "key": "order_{id}.pdf"},
    )

    mir = builder.build()
    return mir


@pytest.fixture
def default_config():
    """Fixture cho default AWSInfrastructureConfig."""
    from midicoder.infra.aws.terraform import AWSInfrastructureConfig

    return AWSInfrastructureConfig()


# ============================================================================
# Tests: AWSInfrastructureConfig Data Class
# ============================================================================


class TestAWSInfrastructureConfig:
    """Tests cho AWSInfrastructureConfig data class."""

    def test_default_values(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test giá trị mặc định của config."""
        assert default_config.app_name == "midicoder-app"
        assert default_config.region == "ap-southeast-1"
        assert default_config.use_ecs is True
        assert default_config.ecs_instance_type == "t3.medium"
        assert default_config.ecs_cpu == 256
        assert default_config.ecs_memory == 512

    def test_database_defaults(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test database defaults."""
        assert default_config.db_engine == "postgres"
        assert default_config.db_version == "15"
        assert default_config.db_instance_class == "db.t3.micro"
        assert default_config.db_allocated_storage == 20

    def test_cache_defaults(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test cache (Redis) defaults."""
        assert default_config.use_redis is True
        assert default_config.redis_node_type == "cache.t3.micro"
        assert default_config.redis_num_nodes == 1

    def test_neo4j_defaults(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test Neo4j defaults."""
        assert default_config.use_neo4j is True
        assert default_config.neo4j_instance_type == "t3.medium"

    def test_s3_defaults(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test S3 defaults."""
        assert default_config.use_s3 is True
        assert default_config.s3_bucket_prefix == "midicoder"

    def test_custom_values(self) -> None:
        """Test tạo config với custom values."""
        from midicoder.infra.aws.terraform import AWSInfrastructureConfig

        config = AWSInfrastructureConfig(
            app_name="custom-app",
            region="us-west-2",
            use_ecs=False,
            db_engine="mysql",
        )
        assert config.app_name == "custom-app"
        assert config.region == "us-west-2"
        assert config.use_ecs is False
        assert config.db_engine == "mysql"


# ============================================================================
# Tests: TerraformGenerator.extract_aws_infrastructure
# ============================================================================


class TestTerraformGeneratorExtract:
    """Tests cho TerraformGenerator.extract_aws_infrastructure method."""

    def test_extract_from_mir(self, sample_mir: "MIR") -> None:
        """Test extract infrastructure từ MIR có đầy đủ operations."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        config = generator.extract_aws_infrastructure(sample_mir)

        assert config.use_ecs is True  # Có api.handler operation
        assert config.use_redis is True  # Có cache operation
        assert config.use_neo4j is True  # Có graph operation
        assert config.use_s3 is True  # Có storage operation

    def test_extract_with_override_config(self, sample_mir: "MIR") -> None:
        """Test extract với override config."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        override = {"region": "us-east-1", "use_ecs": False}
        config = generator.extract_aws_infrastructure(sample_mir, override)

        assert config.region == "us-east-1"
        assert config.use_ecs is False

    def test_extract_empty_mir(self) -> None:
        """Test extract từ MIR rỗng."""
        from midicoder.pipeline.mir import MIR, MIRBuilder
        from midicoder.infra.aws.terraform import TerraformGenerator

        builder = MIRBuilder()
        empty_mir = builder.build()

        generator = TerraformGenerator()
        config = generator.extract_aws_infrastructure(empty_mir)

        # MIR rỗng không detect được service nào
        # (cần override config để enable services)
        assert config.use_ecs is False
        assert config.use_redis is False
        assert config.use_neo4j is False
        assert config.use_s3 is False


# ============================================================================
# Tests: TerraformGenerator.render_terraform
# ============================================================================


class TestTerraformGeneratorRender:
    """Tests cho TerraformGenerator.render_terraform method."""

    def test_render_main_file(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test render main.tf file."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = generator.render_terraform(default_config)

        assert "main.tf" in files
        assert "terraform" in files["main.tf"]
        assert "provider" in files["main.tf"]

    def test_render_variables_file(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test render variables.tf file."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = generator.render_terraform(default_config)

        assert "variables.tf" in files
        assert "variable" in files["variables.tf"]

    def test_render_outputs_file(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test render outputs.tf file."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = generator.render_terraform(default_config)

        assert "outputs.tf" in files
        assert "output" in files["outputs.tf"]

    def test_render_module_files(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test render module files."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = generator.render_terraform(default_config)

        # Kiểm tra các module files
        assert any("api" in f for f in files.keys())
        assert any("rds" in f or "database" in f for f in files.keys())

    def test_render_with_custom_config(self) -> None:
        """Test render với custom config."""
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        config = AWSInfrastructureConfig(app_name="custom-app", region="eu-west-1")
        generator = TerraformGenerator()
        files = generator.render_terraform(config)

        main_content = files.get("main.tf", "")
        # Region được render vào variables.tf default value
        assert "custom-app" in main_content
        variables_content = files.get("variables.tf", "")
        assert "eu-west-1" in variables_content


# ============================================================================
# Tests: TerraformGenerator.write_terraform
# ============================================================================


class TestTerraformGeneratorWrite:
    """Tests cho TerraformGenerator.write_terraform method."""

    def test_write_to_directory(self, default_config: "AWSInfrastructureConfig") -> None:
        """Test write terraform files vào directory."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = generator.render_terraform(default_config)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            generator.write_terraform(files, output_dir)

            # Kiểm tra files được tạo
            assert output_dir.exists()
            assert (output_dir / "main.tf").exists()
            assert (output_dir / "variables.tf").exists()

    def test_write_creates_nested_directories(
        self, default_config: "AWSInfrastructureConfig"
    ) -> None:
        """Test write tạo nested directories tự động."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = {
            "modules/api/main.tf": "resource...",
            "modules/rds/main.tf": "resource...",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            generator.write_terraform(files, output_dir)

            # Kiểm tra nested directories
            assert (output_dir / "modules" / "api" / "main.tf").exists()
            assert (output_dir / "modules" / "rds" / "main.tf").exists()


# ============================================================================
# Tests: TerraformGenerator.generate (Full Pipeline)
# ============================================================================


class TestTerraformGeneratorFullPipeline:
    """Integration tests cho TerraformGenerator.generate method."""

    def test_full_pipeline(self, sample_mir: "MIR") -> None:
        """Test full pipeline: extract → render → write."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            config = generator.generate(sample_mir, output_dir)

            # Verify output
            assert output_dir.exists()
            assert (output_dir / "main.tf").exists()
            assert config.app_name == "midicoder-app"

    def test_full_pipeline_with_override(self, sample_mir: "MIR") -> None:
        """Test full pipeline với override config."""
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        override = {"app_name": "my-aws-app", "region": "us-west-2"}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "terraform"
            config = generator.generate(sample_mir, output_dir, override)

            assert config.app_name == "my-aws-app"
            assert config.region == "us-west-2"


# ============================================================================
# Tests: Error Handling
# ============================================================================


class TestTerraformGeneratorErrors:
    """Tests cho error handling."""

    def test_template_not_found(self) -> None:
        """Test error khi template không tìm thấy."""
        from midicoder.errors import ErrorCode, MidicoderError
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        generator = TerraformGenerator(template_path="/nonexistent/path/template.j2")
        config = AWSInfrastructureConfig()

        with pytest.raises(MidicoderError) as exc_info:
            generator.render_terraform(config)

        assert exc_info.value.code == ErrorCode.INFRA_TEMPLATE_NOT_FOUND

    def test_write_permission_denied(self) -> None:
        """Test error khi không có quyền ghi.
        
        Note: Test này chỉ làm việc trên Unix. Trên Windows, chmod không hoạt động.
        """
        import os
        from midicoder.errors import MidicoderError
        from midicoder.infra.aws.terraform import TerraformGenerator

        generator = TerraformGenerator()
        files = {"main.tf": "content"}

        # Thử write vào readonly directory (chỉ làm việc trên Unix)
        with tempfile.TemporaryDirectory() as tmpdir:
            readonly_dir = Path(tmpdir) / "readonly"
            readonly_dir.mkdir()
            
            # Chỉ áp dụng chmod trên Unix
            if os.name != "nt":
                readonly_dir.chmod(0o444)  # Read-only
                with pytest.raises((MidicoderError, PermissionError)):
                    generator.write_terraform(files, readonly_dir)
            else:
                # Trên Windows, test này pass (không thể test permission)
                pass


# ============================================================================
# Tests: Template Content Validation
# ============================================================================


class TestTerraformTemplateContent:
    """Tests để validate template content."""

    def test_main_tf_contains_terraform_block(self) -> None:
        """Test main.tf chứa terraform block."""
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        generator = TerraformGenerator()
        config = AWSInfrastructureConfig()
        files = generator.render_terraform(config)

        main_tf = files.get("main.tf", "")
        assert "terraform {" in main_tf
        assert "required_providers" in main_tf

    def test_main_tf_contains_aws_provider(self) -> None:
        """Test main.tf chứa AWS provider."""
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        generator = TerraformGenerator()
        config = AWSInfrastructureConfig()
        files = generator.render_terraform(config)

        main_tf = files.get("main.tf", "")
        assert "provider" in main_tf
        assert "aws" in main_tf

    def test_variables_tf_contains_variables(self) -> None:
        """Test variables.tf chứa variable definitions."""
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        generator = TerraformGenerator()
        config = AWSInfrastructureConfig()
        files = generator.render_terraform(config)

        variables_tf = files.get("variables.tf", "")
        assert "variable" in variables_tf
        assert "app_name" in variables_tf

    def test_outputs_tf_contains_outputs(self) -> None:
        """Test outputs.tf chứa output definitions."""
        from midicoder.infra.aws.terraform import (
            AWSInfrastructureConfig,
            TerraformGenerator,
        )

        generator = TerraformGenerator()
        config = AWSInfrastructureConfig()
        files = generator.render_terraform(config)

        outputs_tf = files.get("outputs.tf", "")
        assert "output" in outputs_tf


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])