# coding: utf-8
"""
React API Client Emitter (CP20).

Module này chứa ReactApiEmitter để emit typed API clients
cho React từ ApiSpec.

Templates:
  - api-client.ts.jinja2
  - realtime-hooks.ts.jinja2
  - openapi-bind.ts.jinja2

Usage:
    from midicoder.packs.api_client.react import ReactApiEmitter
    emitter = ReactApiEmitter()
    files = emitter.generate(api_spec, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_backend_api_client.models import ApiSpec

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "cp_backend_api_client"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactApiEmitter:
    """Emitter cho React API Clients (CP20).

    Sinh ra:
    - api-client.ts — Axios-based typed HTTP client
    - realtime-hooks.ts — Custom React hooks cho WebSocket/SSE
    - openapi-bind.ts — TypeScript interfaces từ OpenAPI spec
    """

    def __init__(self) -> None:
        """Khởi tạo ReactApiEmitter."""
        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render jinja2 template với context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return f"// {template_name} - template not found\n"

    def generate(
        self,
        spec: ApiSpec,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh React API client từ ApiSpec.

        Templates:
          - api-client.ts.jinja2
          - realtime-hooks.ts.jinja2
          - openapi-bind.ts.jinja2

        Args:
            spec: ApiSpec chứa config, bindings, bridge
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Base context
        ctx: dict[str, Any] = {
            "base_url": spec.base_url,
            "auth_mode": spec.auth_mode.value,
        }

        # Always emit api-client.ts
        files.append(self._write_file(
            "api-client.ts.jinja2",
            "api-client.ts",
            ctx, output_dir,
        ))

        # Emit realtime-hooks.ts nếu có bridge spec
        if spec.bridge:
            ctx["bridge"] = {
                "name": spec.bridge.name,
                "transport": spec.bridge.transport.value,
                "url": spec.bridge.url,
                "channels": spec.bridge.channels,
            }
            files.append(self._write_file(
                "realtime-hooks.ts.jinja2",
                "realtime-hooks.ts",
                ctx, output_dir,
            ))

        # Emit openapi-bind.ts (type binding)
        ctx["bindings"] = [
            {
                "client_method": b.client_method,
                "request_type": b.request_type,
                "response_type": b.response_type,
            }
            for b in spec.bindings
        ]
        ctx["endpoints"] = {
            b.client_method: b.backend_route
            for b in spec.bindings
        }
        ctx["methods"] = {
            b.client_method: b.http_method.value
            for b in spec.bindings
        }
        if spec.bridge:
            ctx["bridge"] = {
                "name": spec.bridge.name,
                "transport": spec.bridge.transport.value,
                "url": spec.bridge.url,
            }
            ctx["channels"] = spec.bridge.channels or []
        else:
            ctx["bridge"] = None
            ctx["channels"] = []

        files.append(self._write_file(
            "openapi-bind.ts.jinja2",
            "openapi-bind.ts",
            ctx, output_dir,
        ))

        return files

    def _write_file(
        self,
        template_name: str,
        filename: str,
        context: dict[str, Any],
        output_dir: Path,
    ) -> GeneratedFile:
        """Render template, write file, trả về GeneratedFile."""
        content = self._render_template(template_name, context)
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=Path(filename),
            content=content,
            template=f"react/api_client/{template_name}",
        )


__all__ = ["ReactApiEmitter", "GeneratedFile"]
