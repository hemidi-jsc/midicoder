"""
Mô-đun data models cho CP07: Infrastructure as Code Generator.

Cung cấp:
- InfrastructureConfig: Configuration cho Docker Compose generation
- AWSInfrastructureConfig: Configuration cho AWS Terraform generation

Sử dụng:
    from midicoder.emitters.core.iac.models import InfrastructureConfig
    config = InfrastructureConfig(has_backend=True, has_frontend=True)
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field


# ============================================================================
# Constants
# ============================================================================

DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 7272
DEFAULT_POSTGRES_DATABASE = "midicoder"
DEFAULT_NEO4J_USER = "neo4j"

DEFAULT_AWS_REGION = "ap-southeast-1"  # Singapore
DEFAULT_DB_ENGINE = "postgres"
DEFAULT_DB_VERSION = "15"
DEFAULT_ENVIRONMENT = "development"


# ============================================================================
# InfrastructureConfig
# ============================================================================


@dataclass
class InfrastructureConfig:
    """
    Infrastructure Configuration từ MIR cho Docker Compose.

    Lưu trữ configuration extracted từ MIR cho Docker Compose generation.
    Các services chỉ được include nếu được detect trong MIR.

    Attributes:
        has_backend: Có backend service không
        has_frontend: Có frontend service không
        backend_stack: Backend stack (fastapi, nestjs)
        frontend_stack: Frontend stack (angular, react)
        backend_port: Backend port
        frontend_port: Frontend port
        postgres_password: PostgreSQL password (tự generate)
        postgres_database: PostgreSQL database name
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password (tự generate)
        jwt_secret: JWT secret cho backend (tự generate)
        services: List services được include

    Ví dụ:
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_stack="fastapi",
            frontend_stack="angular"
        )
    """

    has_backend: bool = False
    has_frontend: bool = False
    backend_stack: str = "fastapi"
    frontend_stack: str = "angular"
    backend_port: int = DEFAULT_BACKEND_PORT
    frontend_port: int = DEFAULT_FRONTEND_PORT
    postgres_password: str = field(default_factory=lambda: secrets.token_hex(16))
    postgres_database: str = DEFAULT_POSTGRES_DATABASE
    neo4j_user: str = DEFAULT_NEO4J_USER
    neo4j_password: str = field(default_factory=lambda: secrets.token_hex(16))
    jwt_secret: str = field(default_factory=lambda: secrets.token_hex(32))
    services: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Initialize services list sau khi create object.

        Build services list từ has_backend và has_frontend.
        PostgreSQL, Redis, Neo4j luôn có mặt cho local development.
        """
        if not self.services:
            self.services = []
            if self.has_backend:
                self.services.append("backend")
            if self.has_frontend:
                self.services.append("frontend")
            self.services.extend(["postgres", "redis", "neo4j"])


# ============================================================================
# AWSInfrastructureConfig
# ============================================================================


@dataclass
class AWSInfrastructureConfig:
    """
    AWS Infrastructure Configuration từ MIR cho Terraform.

    Lưu trữ configuration extracted từ MIR cho Terraform generation.
    Mỗi service chỉ được enable nếu detect trong MIR operations.

    Attributes:
        app_name: Tên ứng dụng
        region: AWS region
        use_ecs: Có dùng ECS không
        ecs_instance_type: ECS instance type
        ecs_cpu: ECS CPU units
        ecs_memory: ECS memory (MB)
        db_engine: Database engine
        db_version: Database version
        db_instance_class: RDS instance class
        db_allocated_storage: RDS allocated storage (GB)
        use_redis: Có dùng Redis không
        redis_node_type: ElastiCache node type
        redis_num_nodes: Số lượng Redis nodes
        use_neo4j: Có dùng Neo4j không
        neo4j_instance_type: Neo4j instance type
        use_s3: Có dùng S3 không
        s3_bucket_prefix: S3 bucket prefix
        environment: Environment (development/staging/production)
        postgres_password: PostgreSQL password (tự generate)
        neo4j_password: Neo4j password (tự generate)
        jwt_secret: JWT secret cho backend (tự generate)

    Ví dụ:
        config = AWSInfrastructureConfig(
            app_name="my-app",
            region="us-west-2",
            use_ecs=True
        )
    """

    app_name: str = "midicoder-app"
    region: str = DEFAULT_AWS_REGION

    # ECS Configuration
    use_ecs: bool = True
    ecs_instance_type: str = "t3.medium"
    ecs_cpu: int = 256
    ecs_memory: int = 512

    # Database Configuration
    db_engine: str = DEFAULT_DB_ENGINE
    db_version: str = DEFAULT_DB_VERSION
    db_instance_class: str = "db.t3.micro"
    db_allocated_storage: int = 20

    # Cache Configuration
    use_redis: bool = True
    redis_node_type: str = "cache.t3.micro"
    redis_num_nodes: int = 1

    # Neo4j Configuration
    use_neo4j: bool = True
    neo4j_instance_type: str = "t3.medium"

    # S3 Configuration
    use_s3: bool = True
    s3_bucket_prefix: str = "midicoder"

    # Environment
    environment: str = DEFAULT_ENVIRONMENT

    # Secrets (sẽ lưu trong AWS Secrets Manager)
    postgres_password: str = field(default_factory=lambda: secrets.token_hex(16))
    neo4j_password: str = field(default_factory=lambda: secrets.token_hex(16))
    jwt_secret: str = field(default_factory=lambda: secrets.token_hex(32))