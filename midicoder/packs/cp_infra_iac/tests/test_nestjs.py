"""
Tests cho I01 IAC NestJS emitter.

Kiểm tra:
- NestJSIacEmitter: Generate Docker Compose cho NestJS stack
- Minimal compose fallback
"""

import pytest

from midicoder.packs.cp_infra_iac.nestjs import NestJSIacEmitter
from midicoder.packs.cp_infra_iac.models import InfrastructureConfig


class TestNestJSIacEmitter:
    """Tests cho NestJSIacEmitter."""

    def test_emitter_initialization(self):
        emitter = NestJSIacEmitter()
        assert emitter is not None
        assert emitter.generator is not None

    def test_generate_with_backend_only(self):
        emitter = NestJSIacEmitter()
        config = InfrastructureConfig(
            has_backend=True,
            backend_stack="nestjs",
            backend_port=3000,
        )
        result = emitter.generate(config)
        assert "docker-compose.yml" in result
        content = result["docker-compose.yml"]
        assert "backend:" in content
        assert "postgres:" in content
        assert "redis:" in content

    def test_generate_with_frontend(self):
        emitter = NestJSIacEmitter()
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_port=3000,
            frontend_port=80,
        )
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "frontend:" in content

    def test_generate_includes_neo4j(self):
        emitter = NestJSIacEmitter()
        config = InfrastructureConfig(has_backend=True)
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "neo4j:" in content

    def test_generate_returns_dict(self):
        emitter = NestJSIacEmitter()
        config = InfrastructureConfig()
        result = emitter.generate(config)
        assert isinstance(result, dict)
