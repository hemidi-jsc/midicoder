"""
NestJS IAC Emitter — Sinh Docker Compose cho NestJS stack.

Module này cung cấp NestJSIacEmitter class để generate
Docker Compose files cho NestJS backend.

Sử dụng:
    from midicoder.packs.cp07_iac.nestjs import NestJSIacEmitter

    emitter = NestJSIacEmitter()
    result = emitter.generate(config)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp07_iac.docker import DockerComposeGenerator
from midicoder.packs.cp07_iac.models import InfrastructureConfig


class NestJSIacEmitter:
    """
    NestJS Infrastructure as Code Emitter.

    Emitter này wrapper quanh DockerComposeGenerator để
    generate docker-compose.yml cho NestJS stack.

    Attributes:
        generator: DockerComposeGenerator instance

    Ví dụ:
        emitter = NestJSIacEmitter()
        config = InfrastructureConfig(has_backend=True, backend_stack="nestjs")
        result = emitter.generate(config)
    """

    def __init__(self) -> None:
        """Initialize NestJSIacEmitter."""
        self.generator = DockerComposeGenerator()

    def generate(self, config: InfrastructureConfig) -> dict[str, str]:
        """
        Generate Docker Compose files cho NestJS stack.

        Args:
            config: InfrastructureConfig với backend_stack="nestjs"

        Returns:
            Dictionary mapping file paths to content
        """
        # Render docker-compose content
        try:
            compose_content = self.generator.render_template(config)
        except Exception:
            # Nếu template không có, trả về minimal compose
            compose_content = self._generate_minimal_compose(config)

        return {"docker-compose.yml": compose_content}

    def _generate_minimal_compose(self, config: InfrastructureConfig) -> str:
        """
        Generate minimal docker-compose.yml khi template không có.

        Args:
            config: InfrastructureConfig

        Returns:
            Docker Compose YAML string
        """
        lines = [
            "version: '3.8'",
            "",
            "services:",
        ]

        if config.has_backend:
            lines.extend([
                "  backend:",
                "    build: ./backend",
                "    ports:",
                f"      - \"{config.backend_port}:{config.backend_port}\"",
                "    environment:",
                f"      - DATABASE_URL=postgresql://postgres:{config.postgres_password}@postgres:5432/{config.postgres_database}",
                f"      - JWT_SECRET={config.jwt_secret}",
                "    depends_on:",
                "      - postgres",
                "      - redis",
            ])

        if config.has_frontend:
            lines.extend([
                "  frontend:",
                "    build: ./frontend",
                "    ports:",
                f"      - \"{config.frontend_port}:80\"",
                "    depends_on:",
                "      - backend",
            ])

        # PostgreSQL
        lines.extend([
            "  postgres:",
            "    image: postgres:15",
            "    environment:",
            f"      - POSTGRES_PASSWORD={config.postgres_password}",
            f"      - POSTGRES_DB={config.postgres_database}",
            "    volumes:",
            "      - postgres_data:/var/lib/postgresql/data",
        ])

        # Redis
        lines.extend([
            "  redis:",
            "    image: redis:7-alpine",
        ])

        # Neo4j
        lines.extend([
            "  neo4j:",
            "    image: neo4j:5",
            "    environment:",
            f"      - NEO4J_AUTH={config.neo4j_user}/{config.neo4j_password}",
        ])

        # Volumes
        lines.extend([
            "",
            "volumes:",
            "  postgres_data:",
        ])

        return "\n".join(lines)