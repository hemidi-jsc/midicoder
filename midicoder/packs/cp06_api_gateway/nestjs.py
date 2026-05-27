# coding: utf-8
"""
NestJS Gateway Emitter (CP06).

Unified emitter để sinh toàn bộ gateway files cho NestJS:
- HTTP REST controllers (per tag)
- GraphQL resolvers
- Webhook handlers
- Infrastructure: gateway.module, gateway.service, circuit-breaker, rate-limiter, route-config

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from midicoder.packs.cp06_api_gateway.models import RouteCollection
from midicoder.packs.cp06_api_gateway.route_nestjs import (
    NestJSRouteEmitter,
    NestJSGraphQLResolverEmitter,
    NestJSWebhookEmitter,
)


@dataclass
class NestJSGatewayEmitter:
    """
    Unified emitter cho CP06 NestJS.

    Generate toàn bộ gateway files từ RouteCollection:
    - Controllers grouped by tag
    - GraphQL resolvers
    - Webhook handlers
    - Infrastructure files

    Attributes:
        stack_dir: Directory chứa Jinja2 templates (stacks/nestjs/)
    """

    stack_dir: Path = field(default_factory=lambda: Path(""))

    def generate(self, collection: RouteCollection) -> dict[str, str]:
        """
        Sinh toàn bộ gateway files cho NestJS.

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

        # 2. Emit HTTP controllers (structured)
        if collection.routes:
            route_emitter = NestJSRouteEmitter()
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                route_files = route_emitter.emit(collection, Path(tmp))
                for k, v in route_files.items():
                    rel = str(Path(k).relative_to(tmp)) if tmp in k else k
                    files[f"routes/{rel}" if not rel.startswith("routes/") else rel] = v

        # 3. Emit GraphQL resolvers (structured)
        if collection.resolvers:
            graphql_emitter = NestJSGraphQLResolverEmitter()
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                graphql_files = graphql_emitter.emit(collection, Path(tmp))
                for k, v in graphql_files.items():
                    files[k] = v

        # 4. Emit Webhook handlers (structured)
        if collection.webhooks:
            webhook_emitter = NestJSWebhookEmitter()
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
            ("cp06_api_gateway/gateway.module.ts.jinja2", "gateway/gateway.module.ts"),
            ("cp06_api_gateway/gateway.service.ts.jinja2", "gateway/gateway.service.ts"),
            ("cp06_api_gateway/gateway.controller.ts.jinja2", "gateway/gateway.controller.ts"),
            ("cp06_api_gateway/circuit-breaker.providers.ts.jinja2", "gateway/circuit-breaker.providers.ts"),
            ("cp06_api_gateway/rate-limiter.providers.ts.jinja2", "gateway/rate-limiter.providers.ts"),
            ("cp06_api_gateway/route-config.service.ts.jinja2", "gateway/route-config.service.ts"),
        ]

        for template_name, output_path in infra_templates:
            try:
                template = env.get_template(template_name)
                content = template.render()
                files[output_path] = content
            except Exception:
                pass  # Template không tồn tại — skip

        return files