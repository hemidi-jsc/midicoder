"""
Tests cho I01 IAC models.

Kiểm tra:
- InfrastructureConfig: Docker Compose configuration
- AWSInfrastructureConfig: AWS Terraform configuration
- Constants mặc định
"""

import pytest

from midicoder.packs.cp_infra_iac.models import (
    AWSInfrastructureConfig,
    DEFAULT_BACKEND_PORT,
    DEFAULT_ENVIRONMENT,
    DEFAULT_FRONTEND_PORT,
    DEFAULT_NEO4J_USER,
    DEFAULT_POSTGRES_DATABASE,
    InfrastructureConfig,
)


class TestConstants:
    """Tests cho các hằng số mặc định."""

    def test_default_backend_port(self):
        assert DEFAULT_BACKEND_PORT == 8000

    def test_default_frontend_port(self):
        assert DEFAULT_FRONTEND_PORT == 7272

    def test_default_postgres_database(self):
        assert DEFAULT_POSTGRES_DATABASE == "midicoder"

    def test_default_neo4j_user(self):
        assert DEFAULT_NEO4J_USER == "neo4j"

    def test_default_environment(self):
        assert DEFAULT_ENVIRONMENT == "development"


class TestInfrastructureConfig:
    """Tests cho InfrastructureConfig dataclass."""

    def test_default_creation(self):
        config = InfrastructureConfig()
        assert config.has_backend is False
        assert config.has_frontend is False
        assert config.backend_stack == "fastapi"
        assert config.frontend_stack == "angular"
        assert config.backend_port == 8000
        assert config.frontend_port == 7272

    def test_services_initialized_with_defaults(self):
        config = InfrastructureConfig()
        # Với has_backend=False, has_frontend=False -> chỉ còn postgres, redis, neo4j
        assert "postgres" in config.services
        assert "redis" in config.services
        assert "neo4j" in config.services
        assert "backend" not in config.services
        assert "frontend" not in config.services

    def test_with_backend_only(self):
        config = InfrastructureConfig(has_backend=True)
        assert "backend" in config.services
        assert "frontend" not in config.services

    def test_with_frontend_only(self):
        config = InfrastructureConfig(has_frontend=True)
        assert "frontend" in config.services
        assert "backend" not in config.services

    def test_with_both_backend_frontend(self):
        config = InfrastructureConfig(has_backend=True, has_frontend=True)
        assert "backend" in config.services
        assert "frontend" in config.services

    def test_custom_ports(self):
        config = InfrastructureConfig(
            has_backend=True,
            backend_port=9000,
            frontend_port=8080,
        )
        assert config.backend_port == 9000
        assert config.frontend_port == 8080

    def test_custom_stacks(self):
        config = InfrastructureConfig(
            backend_stack="nestjs",
            frontend_stack="react",
        )
        assert config.backend_stack == "nestjs"
        assert config.frontend_stack == "react"

    def test_secrets_auto_generated(self):
        config = InfrastructureConfig()
        assert len(config.postgres_password) == 32  # secrets.token_hex(16)
        assert len(config.neo4j_password) == 32
        assert len(config.jwt_secret) == 64  # secrets.token_hex(32)

    def test_secrets_unique_per_instance(self):
        config1 = InfrastructureConfig()
        config2 = InfrastructureConfig()
        assert config1.postgres_password != config2.postgres_password
        assert config1.jwt_secret != config2.jwt_secret

    def test_custom_postgres_database(self):
        config = InfrastructureConfig(postgres_database="custom_db")
        assert config.postgres_database == "custom_db"

    def test_custom_services_list(self):
        config = InfrastructureConfig(
            has_backend=True,
            services=["custom_service"],
        )
        assert config.services == ["custom_service"]


class TestAWSInfrastructureConfig:
    """Tests cho AWSInfrastructureConfig dataclass."""

    def test_default_creation(self):
        config = AWSInfrastructureConfig()
        assert config.app_name == "midicoder-app"
        assert config.region == "ap-southeast-1"
        assert config.use_ecs is True
        assert config.environment == "development"

    def test_ecs_configuration(self):
        config = AWSInfrastructureConfig(
            ecs_instance_type="t3.large",
            ecs_cpu=512,
            ecs_memory=1024,
        )
        assert config.ecs_instance_type == "t3.large"
        assert config.ecs_cpu == 512
        assert config.ecs_memory == 1024

    def test_database_configuration(self):
        config = AWSInfrastructureConfig(
            db_engine="mysql",
            db_version="8.0",
            db_instance_class="db.t3.small",
            db_allocated_storage=50,
        )
        assert config.db_engine == "mysql"
        assert config.db_version == "8.0"
        assert config.db_allocated_storage == 50

    def test_redis_configuration(self):
        config = AWSInfrastructureConfig(
            use_redis=True,
            redis_node_type="cache.t3.small",
            redis_num_nodes=3,
        )
        assert config.redis_node_type == "cache.t3.small"
        assert config.redis_num_nodes == 3

    def test_neo4j_configuration(self):
        config = AWSInfrastructureConfig(
            use_neo4j=True,
            neo4j_instance_type="t3.large",
        )
        assert config.use_neo4j is True
        assert config.neo4j_instance_type == "t3.large"

    def test_s3_configuration(self):
        config = AWSInfrastructureConfig(
            use_s3=True,
            s3_bucket_prefix="myapp",
        )
        assert config.use_s3 is True
        assert config.s3_bucket_prefix == "myapp"

    def test_secrets_auto_generated(self):
        config = AWSInfrastructureConfig()
        assert len(config.postgres_password) == 32
        assert len(config.neo4j_password) == 32
        assert len(config.jwt_secret) == 64

    def test_secrets_unique_per_instance(self):
        config1 = AWSInfrastructureConfig()
        config2 = AWSInfrastructureConfig()
        assert config1.postgres_password != config2.postgres_password

    def test_custom_app_name_and_region(self):
        config = AWSInfrastructureConfig(
            app_name="my-custom-app",
            region="us-west-2",
        )
        assert config.app_name == "my-custom-app"
        assert config.region == "us-west-2"

    def test_production_environment(self):
        config = AWSInfrastructureConfig(environment="production")
        assert config.environment == "production"

    def test_disable_optional_services(self):
        config = AWSInfrastructureConfig(
            use_ecs=False,
            use_redis=False,
            use_neo4j=False,
            use_s3=False,
        )
        assert config.use_ecs is False
        assert config.use_redis is False
        assert config.use_neo4j is False
        assert config.use_s3 is False
