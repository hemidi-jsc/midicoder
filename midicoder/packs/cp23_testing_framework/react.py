# coding: utf-8
"""
Mô-đun React emitter cho Testing Framework Generator (CP23).

Emit code Jest cho React:
- jest.config.js (config)
- Component test files
- Hook test files
- E2E test files

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.packs.cp23_testing_framework.models import (
    TestCollection,
    TestSuite,
)


class ReactTestEmitter:
    """
    Emitter sinh code Jest cho React.

    Sinh ra:
    - jest.config.js — Jest config
    - src/__tests__/{entity}.test.tsx
    - src/__tests__/hooks/use{Entity}.test.tsx
    - src/e2e/app.test.tsx
    """

    def __init__(self, stack_dir: str | Path) -> None:
        self.emitter = Emitter(stack="react")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: TestCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ test files cho React."""
        results: list[dict[str, str]] = []

        results.extend(self._generate_jest_config(collection))

        for suite in collection.suites:
            results.extend(self._generate_suite(suite, entities or [], commands or [], queries or []))

        return results

    def _generate_jest_config(self, collection: TestCollection) -> list[dict[str, str]]:
        """Sinh jest.config.js."""
        try:
            content = self.emitter.render(
                "cp23_testing_framework/jest.config.js.jinja2",
                {"collection": collection},
            )
            return [{"path": "jest.config.js", "content": content}]
        except Exception:
            return []

    def _generate_suite(
        self,
        suite: TestSuite,
        entities: list[dict[str, Any]],
        commands: list[dict[str, Any]],
        queries: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh test files cho một test suite."""
        results: list[dict[str, str]] = []

        for case in suite.cases:
            template_name = self._get_template_name(suite, case)
            if not template_name:
                continue

            try:
                content = self.emitter.render(
                    f"cp23_testing_framework/{template_name}",
                    {
                        "case": case,
                        "suite": suite,
                        "collection": None,
                        "entity": self._find_entity(case.target, entities),
                        "command": self._find_item(case.target, commands),
                        "query": self._find_item(case.target, queries),
                        "all_entities": entities,
                    },
                )
                file_path = self._get_file_path(suite, case)
                results.append({"path": file_path, "content": content})
            except Exception:
                continue

        return results

    def _get_template_name(self, suite: TestSuite, case: "TestCase") -> str:
        """Xác định template name theo test type."""
        if suite.test_type.value in ("unit", "integration"):
            if case.tags and "hook" in case.tags:
                return "hook.test.tsx.jinja2"
            return "component.test.tsx.jinja2"
        elif suite.test_type.value == "e2e":
            return "e2e_app.test.tsx.jinja2"
        return ""

    def _get_file_path(self, suite: TestSuite, case: "TestCase") -> str:
        """Xác định file path cho test case."""
        entity_snake = case.target.lower().replace(" ", "_")
        if suite.test_type.value == "e2e":
            return f"src/e2e/{entity_snake}.e2e.test.tsx"
        elif case.tags and "hook" in case.tags:
            return f"src/__tests__/hooks/use{case.target}.test.tsx"
        else:
            return f"src/__tests__/{entity_snake}.test.tsx"

    def _find_entity(self, target: str, entities: list[dict[str, Any]]) -> dict[str, Any] | None:
        for e in entities:
            if e.get("id", "").lower() == target.lower():
                return e
        return None

    def _find_item(self, target: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        for item in items:
            if item.get("id", "").lower() == target.lower():
                return item
        return None
