# coding: utf-8
"""
Angular Gateway Emitter (CP06).

Unified emitter để sinh gateway files cho Angular:
- GatewayModule
- ApiClientService
- RouteGuardService

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from midicoder.emitters.core.cp06_api_gateway.models import RouteCollection


@dataclass
class AngularGatewayEmitter:
    """
    Unified emitter cho CP06 Angular.

    Generate gateway files từ RouteCollection:
    - GatewayModule
    - ApiClientService
    - RouteGuardService

    Attributes:
        stack_dir: Directory chứa Jinja2 templates (stacks/angular/core/)
    """

    stack_dir: Path = field(default_factory=lambda: Path(""))

    def generate(self, collection: RouteCollection) -> dict[str, str]:
        """
        Sinh toàn bộ gateway files cho Angular.

        Args:
            collection: RouteCollection

        Returns:
            Dictionary {file_path: content}
        """
        files: dict[str, str] = {}

        if not collection.total_count:
            return files

        files.update(self._emit_infrastructure(collection))

        return files

    def _emit_infrastructure(self, collection: RouteCollection) -> dict[str, str]:
        """Emit infrastructure files từ Jinja2 templates."""
        files: dict[str, str] = {}

        if not self.stack_dir.exists():
            return files

        env = Environment(
            loader=FileSystemLoader(str(self.stack_dir)),
            keep_trailing_newline=True,
        )

        # Build context from collection
        context = {
            "total_routes": len(collection.routes),
            "route_tags": list(set(tag for r in collection.routes for tag in r.tags)),
            "has_auth": any(r.requires_auth() for r in collection.routes),
        }

        infra_templates = [
            ("cp06_api_gateway/gateway.module.ts.jinja2", "app/core/gateway/gateway.module.ts"),
            ("cp06_api_gateway/api-client.service.ts.jinja2", "app/core/gateway/api-client.service.ts"),
            ("cp06_api_gateway/route-guard.service.ts.jinja2", "app/core/gateway/route-guard.service.ts"),
        ]

        for template_name, output_path in infra_templates:
            try:
                template = env.get_template(template_name)
                content = template.render(**context)
                files[output_path] = content
            except Exception:
                pass  # Template không tồn tại — skip

        return files