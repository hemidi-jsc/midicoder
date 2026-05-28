"""
Tests cho I01 IAC FastAPI emitter.

Kiểm tra:
- FastAPIIacEmitter: Generate Docker Compose cho FastAPI stack
- Minimal compose fallback
"""

import pytest

from midicoder.packs.cp_infra_iac.fastapi import FastAPIIacEmitter
from midicoder.packs.cp_infra_iac.models import InfrastructureConfig


class TestFastAPIIacEmitter:
    """Tests cho FastAPIIacEmitter."""

    def test_emitter_initialization(self):
        emitter = FastAPIIacEmitter()
        assert emitter is not None
        assert emitter.generator is not None

    def test_generate_with_backend_only(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(
            has_backend=True,
            backend_stack="fastapi",
            backend_port=8000,
        )
        result = emitter.generate(config)
        assert "docker-compose.yml" in result
        content = result["docker-compose.yml"]
        assert "backend:" in content
        assert "postgres:" in content
        assert "redis:" in content

    def test_generate_with_frontend_only(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(
            has_frontend=True,
            frontend_port=3000,
        )
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "frontend:" in content

    def test_generate_with_both(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(
            has_backend=True,
            has_frontend=True,
            backend_port=8000,
            frontend_port=3000,
        )
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "backend:" in content
        assert "frontend:" in content
        assert "postgres:" in content
        assert "redis:" in content
        assert "neo4j:" in content

    def test_generate_includes_volumes(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(has_backend=True)
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "volumes:" in content
        assert "postgres_data:" in content

    def test_generate_includes_custom_port(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig(
            has_backend=True,
            backend_port=9000,
        )
        result = emitter.generate(config)
        content = result["docker-compose.yml"]
        assert "9000:9000" in content

    def test_generate_returns_dict(self):
        emitter = FastAPIIacEmitter()
        config = InfrastructureConfig()
        result = emitter.generate(config)
        assert isinstance(result, dict)
