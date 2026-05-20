# coding: utf-8
"""
Mô-đun FastAPI emitter cho Documentation Generator (CP26).

Sinh code MkDocs + OpenAPI cho FastAPI:
- mkdocs.yml — MkDocs config
- docs/index.md — Documentation homepage
- docs/api/openapi.json — OpenAPI spec
- docs/nav.md — Navigation sidebar

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp26_documentation.models import DocCollection


class FastAPIDocEmitter:
    """Emitter sinh code MkDocs + OpenAPI cho FastAPI."""

    def __init__(self, stack_dir: str | Path) -> None:
        self.emitter = Emitter(stack="fastapi")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: DocCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ doc files cho FastAPI."""
        results: list[dict[str, str]] = []
        results.extend(self._generate_mkdocs(collection))
        results.extend(self._generate_index(collection))
        results.extend(self._generate_openapi(collection, entities or [], commands or [], queries or []))
        results.extend(self._generate_nav(collection))
        return results

    def _generate_mkdocs(self, collection: DocCollection) -> list[dict[str, str]]:
        """Sinh mkdocs.yml config."""
        try:
            content = self.emitter.render("cp26_documentation/mkdocs.yml.jinja2", {"collection": collection})
            return [{"path": "mkdocs.yml", "content": content}]
        except Exception:
            return []

    def _generate_index(self, collection: DocCollection) -> list[dict[str, str]]:
        """Sinh docs/index.md."""
        try:
            content = self.emitter.render("cp26_documentation/docs_index.md.jinja2", {"collection": collection})
            return [{"path": "docs/index.md", "content": content}]
        except Exception:
            return []

    def _generate_openapi(
        self, collection: DocCollection,
        entities: list[dict[str, Any]], commands: list[dict[str, Any]],
        queries: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh OpenAPI spec."""
        try:
            content = self.emitter.render("cp26_documentation/openapi.json.jinja2", {
                "collection": collection, "entities": entities,
                "commands": commands, "queries": queries,
            })
            return [{"path": "docs/api/openapi.json", "content": content}]
        except Exception:
            return []

    def _generate_nav(self, collection: DocCollection) -> list[dict[str, str]]:
        """Sinh nav.md."""
        try:
            content = self.emitter.render("cp26_documentation/nav.md.jinja2", {"collection": collection})
            return [{"path": "docs/nav.md", "content": content}]
        except Exception:
            return []
