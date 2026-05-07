"""
Tests cho CP07: Infrastructure as Code Generator.

Module này kiểm tra:
- InfrastructureConfig model validation
- AWSInfrastructureConfig model validation
- DockerComposeGenerator functionality
- TerraformGenerator functionality
- MIR op_type integration (emit_iac_docker, emit_iac_aws)
- Error handling (MDC-CP07-001~005)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from dataclasses import asdict


# ============================================================================
# Tests: InfrastructureConfig Model
# ============================================================================

class TestInfrastructureConfig:
    """Tests cho InfrastructureConfig data model."""

    def test_create_default_config(self) -> None:
        """Test: Tạo config mặc định có đầy đủ services."""
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        config = InfrastructureConfig()

        # Mặc định không có backend/frontend
        assert config.has_backend is False
        assert config.has_frontend is False
        # PostgreSQL, Redis, Neo4j luôn có mặt
        assert "postgres" in config.services
        assert "redis" in config.services
        assert "neo4j" in config.services

    def test_create_config_with_backend(self) -> None:
        """Test: Config với backend include service 'backend'."""
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        config = InfrastructureConfig(has_backend=True)

        assert "backend" in config.services
        assert config.backend_stack == "fastapi"

    def test_create_config_with_frontend(self) -> None:
        """Test: Config với frontend include service 'frontend'."""
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        config = InfrastructureConfig(has_frontend=True)

        assert "frontend" in config.services
        assert config.frontend_stack == "angular"

    def test_create_config_full_stack(self) -> None:
        """Test: Config đầy đủ backend + frontend + infra."""
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_stack="nestjs",
            frontend_stack="react"
        )

        assert "backend" in config.services
        assert "frontend" in config.services
        assert "postgres" in config.services
        assert "redis" in config.services
        assert "neo4j" in config.services
        assert config.backend_stack == "nestjs"
        assert config.frontend_stack == "react"


# ============================================================================
# Tests: AWSInfrastructureConfig Model
# ============================================================================

class TestAWSInfrastructureConfig:
    """Tests cho AWSInfrastructureConfig data model."""

    def test_create_default_aws_config(self) -> None:
        """Test: Tạo AWS config mặc định."""
        from midicoder.emitters.core.iac.models import AWSInfrastructureConfig

        config = AWSInfrastructureConfig()

        assert config.app_name == "midicoder-app"
        assert config.region == "ap-southeast-1"
        assert config.use_ecs is True
        assert config.use_redis is True
        assert config.use_neo4j is True
        assert config.use_s3 is True

    def test_create_custom_aws_config(self) -> None:
        """Test: Tạo AWS config với custom values."""
        from midicoder.emitters.core.iac.models import AWSInfrastructureConfig

        config = AWSInfrastructureConfig(
            app_name="my-ecommerce",
            region="us-east-1",
            use_ecs=False,
            use_s3=False
        )

        assert config.app_name == "my-ecommerce"
        assert config.region == "us-east-1"
        assert config.use_ecs is False
        assert config.use_s3 is False

    def test_secrets_auto_generated(self) -> None:
        """Test: Secrets tự động generate khi tạo config."""
        from midicoder.emitters.core.iac.models import AWSInfrastructureConfig

        config = AWSInfrastructureConfig()

        assert len(config.postgres_password) > 0
        assert len(config.neo4j_password) > 0
        assert len(config.jwt_secret) > 0
        # Các secrets là unique
        assert config.postgres_password != config.neo4j_password
        assert config.jwt_secret != config.postgres_password


# ============================================================================
# Tests: DockerComposeGenerator
# ============================================================================

class TestDockerComposeGenerator:
    """Tests cho DockerComposeGenerator."""

    def test_extract_infrastructure_from_mir_with_backend_ops(self) -> None:
        """Test: Extract detect backend khi MIR có API operations."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.docker import DockerComposeGenerator

        # Tạo MIR với backend operations
        mir = MIR()
        mir.operations.append(type('Operation', (), {
            'op_type': 'create_record',
            'params': {'entity': 'Order'},
            'obligation_refs': []
        })())

        generator = DockerComposeGenerator()
        config = generator.extract_infrastructure(mir)

        assert config.has_backend is True

    def test_extract_infrastructure_from_mir_with_frontend_ops(self) -> None:
        """Test: Extract detect frontend khi MIR có UI operations."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.docker import DockerComposeGenerator

        mir = MIR()
        mir.operations.append(type('Operation', (), {
            'op_type': 'render_ui_component',
            'params': {},
            'obligation_refs': []
        })())

        generator = DockerComposeGenerator()
        config = generator.extract_infrastructure(mir)

        assert config.has_frontend is True

    def test_extract_infrastructure_empty_mir(self) -> None:
        """Test: Extract với MIR trống chỉ có infra services."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.docker import DockerComposeGenerator

        mir = MIR()  # Trống
        generator = DockerComposeGenerator()
        config = generator.extract_infrastructure(mir)

        assert config.has_backend is False
        assert config.has_frontend is False
        # Vẫn có postgres, redis, neo4j
        assert "postgres" in config.services

    def test_override_config_priority(self) -> None:
        """Test: Override config có ưu tiên cao nhất."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.docker import DockerComposeGenerator

        mir = MIR(metadata={"backend_stack": "fastapi"})
        generator = DockerComposeGenerator()

        override = {"backend_stack": "nestjs"}
        config = generator.extract_infrastructure(mir, override_config=override)

        assert config.backend_stack == "nestjs"


# ============================================================================
# Tests: TerraformGenerator
# ============================================================================

class TestTerraformGenerator:
    """Tests cho TerraformGenerator."""

    def test_extract_aws_infrastructure_from_mir(self) -> None:
        """Test: Extract AWS infra từ MIR có đầy đủ operations."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.terraform import TerraformGenerator

        mir = MIR()
        # API operation
        mir.operations.append(type('Operation', (), {
            'op_type': 'handle_api_request',
            'params': {},
            'obligation_refs': []
        })())
        # DB operation
        mir.operations.append(type('Operation', (), {
            'op_type': 'query_records',
            'params': {},
            'obligation_refs': []
        })())

        generator = TerraformGenerator()
        config = generator.extract_aws_infrastructure(mir)

        assert config.use_ecs is True
        assert config.app_name == "midicoder-app"

    def test_extract_with_override_config(self) -> None:
        """Test: Extract với override config."""
        from midicoder.pipeline.mir import MIR
        from midicoder.emitters.core.iac.terraform import TerraformGenerator

        mir = MIR()
        generator = TerraformGenerator()

        override = {"region": "us-east-1", "use_ecs": False}
        config = generator.extract_aws_infrastructure(mir, override)

        assert config.region == "us-east-1"
        assert config.use_ecs is False

    def test_aws_config_defaults(self) -> None:
        """Test: AWS config default values đúng."""
        from midicoder.emitters.core.iac.models import AWSInfrastructureConfig

        config = AWSInfrastructureConfig()

        assert config.db_engine == "postgres"
        assert config.db_version == "15"
        assert config.environment == "development"


# ============================================================================
# Tests: MIR Integration (IAC op_types)
# ============================================================================

class TestMIRIacIntegration:
    """Tests cho IAC op_type integration với MIR."""

    def test_mir_has_iac_docker_op_type(self) -> None:
        """Test: MIR support op_type 'emit_iac_docker'."""
        from midicoder.pipeline.mir import MIR, MIRBuilder

        builder = MIRBuilder()
        builder.add_operation(
            op_id="iac_docker_001",
            op_type="emit_iac_docker",
            params={"target": "docker-compose.yml"}
        )
        mir = builder.build()

        docker_ops = mir.get_operations_by_type("emit_iac_docker")
        assert len(docker_ops) == 1
        assert docker_ops[0].op_id == "iac_docker_001"

    def test_mir_has_iac_aws_op_type(self) -> None:
        """Test: MIR support op_type 'emit_iac_aws'."""
        from midicoder.pipeline.mir import MIR, MIRBuilder

        builder = MIRBuilder()
        builder.add_operation(
            op_id="iac_aws_001",
            op_type="emit_iac_aws",
            params={"target": "terraform/"}
        )
        mir = builder.build()

        aws_ops = mir.get_operations_by_type("emit_iac_aws")
        assert len(aws_ops) == 1
        assert aws_ops[0].op_id == "iac_aws_001"


# ============================================================================
# Tests: Pack Resolution
# ============================================================================

class TestPackResolution:
    """Tests cho pack resolution của CP07."""

    def test_pack_yml_exists(self) -> None:
        """Test: pack.yml tồn tại trong emitters/core/iac/."""
        pack_path = Path("midicoder/emitters/core/iac/pack.yml")
        assert pack_path.exists(), "pack.yml phải tồn tại trong emitters/core/iac/"

    def test_pack_yml_capabilities_provided(self) -> None:
        """Test: pack.yml declare đúng capabilities_provided."""
        import yaml

        pack_path = Path("midicoder/emitters/core/iac/pack.yml")
        with open(pack_path, "r") as f:
            pack_data = yaml.safe_load(f)

        caps = pack_data["pack"]["capabilities_provided"]
        assert "emit_iac_docker" in caps
        assert "emit_iac_aws" in caps

    def test_taxonomy_resolves_iac_ops(self) -> None:
        """Test: Registry resolve duoc IAC op_types den CP07."""
        from industry.registry import TaxonomyRegistry

        registry = TaxonomyRegistry.load("industry/taxonomy.yml")

        # Resolve emit_iac_docker
        docker_packs = registry.resolve_packs_for_operations(["emit_iac_docker"])
        assert len(docker_packs) >= 1
        docker_pack_ids = [p.id for p in docker_packs]
        assert "CP07" in docker_pack_ids

        # Resolve emit_iac_aws
        aws_packs = registry.resolve_packs_for_operations(["emit_iac_aws"])
        assert len(aws_packs) >= 1
        aws_pack_ids = [p.id for p in aws_packs]
        assert "CP07" in aws_pack_ids


# ============================================================================
# Tests: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests cho error codes CP07."""

    def test_cp07_error_codes_exist(self) -> None:
        """Test: Error codes MDC-CP07-001~005 tồn tại trong ErrorCode enum."""
        from midicoder.errors import ErrorCode

        # Kiểm tra các error codes tồn tại
        assert hasattr(ErrorCode, "CP07_MIR_NOT_FOUND")
        assert hasattr(ErrorCode, "CP07_TEMPLATE_NOT_FOUND")
        assert hasattr(ErrorCode, "CP07_RENDER_FAILED")
        assert hasattr(ErrorCode, "CP07_WRITE_FAILED")
        assert hasattr(ErrorCode, "CP07_INVALID_CONFIG")

    def test_cp07_error_messages_vietnamese(self) -> None:
        """Test: Error messages bằng tiếng Việt."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        error = EM.create(ErrorCode.CP07_MIR_NOT_FOUND)
        assert len(error.message) > 0
        # Message nên có nội dung mô tả lỗi

    def test_cp07_error_context(self) -> None:
        """Test: Error có context thông tin."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        error = EM.create(
            ErrorCode.CP07_TEMPLATE_NOT_FOUND,
            template_path="docker-compose.j2"
        )
        assert error.context.get("template_path") == "docker-compose.j2"


# ============================================================================
# Tests: Emitters (FastAPI + NestJS)
# ============================================================================

class TestIacEmitters:
    """Tests cho FastAPI và NestJS IAC Emitters."""

    def test_fastapi_emitter_exists(self) -> None:
        """Test: FastAPI IAC Emitter importable."""
        from midicoder.emitters.core.iac.fastapi import FastAPIIacEmitter
        assert FastAPIIacEmitter is not None

    def test_nestjs_emitter_exists(self) -> None:
        """Test: NestJS IAC Emitter importable."""
        from midicoder.emitters.core.iac.nestjs import NestJSIacEmitter
        assert NestJSIacEmitter is not None

    def test_fastapi_emitter_generate(self) -> None:
        """Test: FastAPI emitter generate docker-compose."""
        from midicoder.emitters.core.iac.fastapi import FastAPIIacEmitter
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(has_backend=True, backend_stack="fastapi")

        result = emitter.generate(config)

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_nestjs_emitter_generate(self) -> None:
        """Test: NestJS emitter generate docker-compose."""
        from midicoder.emitters.core.iac.nestjs import NestJSIacEmitter
        from midicoder.emitters.core.iac.models import InfrastructureConfig

        emitter = NestJSIacEmitter()
        config = InfrastructureConfig(has_backend=True, backend_stack="nestjs")

        result = emitter.generate(config)

        assert isinstance(result, dict)
        assert len(result) > 0


# ============================================================================
# Tests: Module Exports
# ============================================================================

class TestModuleExports:
    """Tests cho module exports."""

    def test_iac_init_exports(self) -> None:
        """Test: __init__.py export đúng classes."""
        from midicoder.emitters.core.iac import (
            InfrastructureConfig,
            AWSInfrastructureConfig,
            DockerComposeGenerator,
            TerraformGenerator,
        )

        assert InfrastructureConfig is not None
        assert AWSInfrastructureConfig is not None
        assert DockerComposeGenerator is not None
        assert TerraformGenerator is not None