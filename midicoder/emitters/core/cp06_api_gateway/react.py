# coding: utf-8
"""
React Gateway Emitter (CP06).

Unified emitter để sinh gateway files cho React:
- ApiClient
- RouteGuard component
- Types

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
class ReactGatewayEmitter:
    """
    Unified emitter cho CP06 React.

    Generate gateway files từ RouteCollection:
    - ApiClient
    - RouteGuard component
    - Types

    Attributes:
        stack_dir: Directory chứa Jinja2 templates (stacks/react/core/)
    """

    stack_dir: Path = field(default_factory=lambda: Path(""))

    def generate(self, collection: RouteCollection) -> dict[str, str]:
        """
        Sinh toàn bộ gateway files cho React.

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
            ("cp06_api_gateway/api-client.ts.jinja2", "gateway/api-client.ts"),
            ("cp06_api_gateway/route-guard.tsx.jinja2", "gateway/route-guard.tsx"),
            ("cp06_api_gateway/types.ts.jinja2", "gateway/types.ts"),
        ]

        for template_name, output_path in infra_templates:
            try:
                template = env.get_template(template_name)
                content = template.render(**context)
                files[output_path] = content
            except Exception:
                pass  # Template không tồn tại — skip

        return files