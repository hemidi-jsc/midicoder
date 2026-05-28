# coding: utf-8
"""
FastAPI Gateway Emitter (CP06).

Unified emitter để sinh toàn bộ gateway files cho FastAPI:
- HTTP REST routes (per tag)
- GraphQL resolvers & schema
- Webhook handlers
- Infrastructure: circuit_breaker, rate_limiter, gateway_app, gateway_router, gateway_service

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from midicoder.packs.cp_full_api_gateway.models import RouteCollection
from midicoder.packs.cp_full_api_gateway.route_fastapi import (
    FastAPIRouteEmitter,
    FastAPIGraphQLResolverEmitter,
    FastAPIWebhookEmitter,
)


@dataclass
class FastAPIGatewayEmitter:
    """
    Unified emitter cho CP06 FastAPI.

    Generate toàn bộ gateway files từ RouteCollection:
    - Routes grouped by tag
    - GraphQL resolvers
    - Webhook handlers
    - Infrastructure files (circuit breaker, rate limiter, gateway app/service/router)

    Attributes:
        stack_dir: Directory chứa Jinja2 templates (stacks/fastapi/)
    """

    stack_dir: Path = field(default_factory=lambda: Path(""))

    def generate(self, collection: RouteCollection) -> dict[str, str]:
        """
        Sinh toàn bộ gateway files cho FastAPI.

        Args:
            collection: RouteCollection chứa routes, resolvers, webhooks

        Returns:
            Dictionary {file_path: content}
        """
        files: dict[str, str] = {}

        if not collection.total_count:
            return files

        # 1. Emit infrastructure files (raw Jinja2)
        files.update(self._emit_infrastructure())

        # 2. Emit HTTP routes (structured)
        if collection.routes:
            route_emitter = FastAPIRouteEmitter()
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                route_files = route_emitter.emit(collection, Path(tmp))
                for k, v in route_files.items():
                    files[f"routes/{k}" if not k.startswith("routes/") else k] = v

        # 3. Emit GraphQL resolvers (structured)
        if collection.resolvers:
            graphql_emitter = FastAPIGraphQLResolverEmitter()
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                graphql_files = graphql_emitter.emit(collection, Path(tmp))
                for k, v in graphql_files.items():
                    files[k] = v

        # 4. Emit Webhook handlers (structured)
        if collection.webhooks:
            webhook_emitter = FastAPIWebhookEmitter()
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                webhook_files = webhook_emitter.emit(collection, Path(tmp))
                for k, v in webhook_files.items():
                    files[k] = v

        return files

    def _emit_infrastructure(self) -> dict[str, str]:
        """Emit infrastructure files từ Jinja2 templates."""
        files: dict[str, str] = {}

        if not self.stack_dir.exists():
            return files

        env = Environment(
            loader=FileSystemLoader(str(self.stack_dir)),
            keep_trailing_newline=True,
        )

        infra_templates = [
            ("cp_full_api_gateway/__init__.py.jinja2", "gateway/__init__.py"),
            ("cp_full_api_gateway/circuit_breaker.py.jinja2", "gateway/circuit_breaker.py"),
            ("cp_full_api_gateway/gateway_app.py.jinja2", "gateway/gateway_app.py"),
            ("cp_full_api_gateway/gateway_router.py.jinja2", "gateway/gateway_router.py"),
            ("cp_full_api_gateway/gateway_service.py.jinja2", "gateway/gateway_service.py"),
            ("cp_full_api_gateway/rate_limiter.py.jinja2", "gateway/rate_limiter.py"),
            ("cp_full_api_gateway/route_config.py.jinja2", "gateway/route_config.py"),
        ]

        for template_name, output_path in infra_templates:
            try:
                template = env.get_template(template_name)
                content = template.render()
                files[output_path] = content
            except Exception:
                pass  # Template không tồn tại — skip

        return files