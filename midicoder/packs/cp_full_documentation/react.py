# coding: utf-8
"""
Mô-đun React emitter cho Documentation Generator (CP26).

Sinh code Storybook + TypeDoc cho React:
- .storybook/main.ts — Storybook config
- .storybook/preview.ts — Storybook preview
- typedoc.json — TypeDoc config
- docs/components.md — Component reference

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.packs.cp_full_documentation.models import DocCollection


class ReactDocEmitter:
    """Emitter sinh code Storybook + TypeDoc cho React."""

    def __init__(self, stack_dir: str | Path) -> None:
        self.emitter = Emitter(stack="react")
        self.stack_dir = Path(stack_dir)

    def generate(
        self, collection: DocCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ doc files cho React."""
        results: list[dict[str, str]] = []
        results.extend(self._generate_storybook_main(collection))
        results.extend(self._generate_storybook_preview(collection))
        results.extend(self._generate_typedoc(collection))
        results.extend(self._generate_components(collection))
        return results

    def _generate_storybook_main(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp_full_documentation/storybook_main.ts.jinja2", {"collection": collection})
            return [{"path": ".storybook/main.ts", "content": content}]
        except Exception:
            return []

    def _generate_storybook_preview(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp_full_documentation/storybook_preview.ts.jinja2", {"collection": collection})
            return [{"path": ".storybook/preview.ts", "content": content}]
        except Exception:
            return []

    def _generate_typedoc(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp_full_documentation/typedoc.json.jinja2", {"collection": collection})
            return [{"path": "typedoc.json", "content": content}]
        except Exception:
            return []

    def _generate_components(self, collection: DocCollection) -> list[dict[str, str]]:
        try:
            content = self.emitter.render("cp_full_documentation/components.md.jinja2", {"collection": collection})
            return [{"path": "docs/components.md", "content": content}]
        except Exception:
            return []
