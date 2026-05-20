# coding: utf-8
"""
Mô-đun NestJS emitter cho Documentation Generator (CP26).

Sinh code Swagger + Docusaurus cho NestJS:
- swagger-config.ts — Swagger module config
- docs/docusaurus.config.js — Docusaurus config
- docs/sidebar.js — Sidebar navigation
- docs/index.md — Homepage

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp26_documentation.models import DocCollection


class NestJSDocEmitter:
    """Emitter sinh code Swagger + Docusaurus cho NestJS."""

    def __init__(self, stack_dir: str | Path) -> None:
        self.emitter = Emitter(stack="nestjs")
        self.stack_dir = Path(stack_dir)

    def generate(
        self, collection: DocCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ doc files cho NestJS."""
        results: list[dict[str, str]] = []
        results.extend(self._generate_swagger(collection))
        results.extend(self._generate_docusaurus(collection))
        results.extend(self._generate_sidebar(collection))
        results.extend(self._generate_index(collection))
        return results

    def _generate_swagger(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp26_documentation/swagger_config.ts.jinja2", {"collection": collection})
            return [{"path": "swagger-config.ts", "content": content}]
        except Exception:
            return []

    def _generate_docusaurus(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp26_documentation/docusaurus.config.js.jinja2", {"collection": collection})
            return [{"path": "docs/docusaurus.config.js", "content": content}]
        except Exception:
            return []

    def _generate_sidebar(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp26_documentation/sidebar.js.jinja2", {"collection": collection})
            return [{"path": "docs/sidebar.js", "content": content}]
        except Exception:
            return []

    def _generate_index(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp26_documentation/docs_index.md.jinja2", {"collection": collection})
            return [{"path": "docs/index.md", "content": content}]
        except Exception:
            return []
