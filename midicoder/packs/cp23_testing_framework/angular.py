# coding: utf-8
"""
Mô-đun Angular emitter cho Testing Framework Generator (CP23).

Emit code Karma/Jest cho Angular:
- karma.conf.js (config)
- Component spec files
- Service spec files
- E2E spec files

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


class AngularTestEmitter:
    """
    Emitter sinh code Karma/Jest cho Angular.

    Sinh ra:
    - karma.conf.js — Karma config
    - src/app/**/components/{entity}-list.component.spec.ts
    - src/app/**/services/{entity}-service.spec.ts
    - e2e/src/app.e2e-spec.ts
    """

    def __init__(self, stack_dir: str | Path) -> None:
        self.emitter = Emitter(stack="angular")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: TestCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ test files cho Angular."""
        results: list[dict[str, str]] = []

        results.extend(self._generate_karma_config(collection))

        for suite in collection.suites:
            results.extend(self._generate_suite(suite, entities or [], commands or [], queries or []))

        return results

    def _generate_karma_config(self, collection: TestCollection) -> list[dict[str, str]]:
        """Sinh karma.conf.js."""
        try:
            content = self.emitter.render(
                "cp23_testing_framework/karma.conf.js.jinja2",
                {"collection": collection},
            )
            return [{"path": "karma.conf.js", "content": content}]
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
            if case.tags and "service" in case.tags:
                return "service.spec.ts.jinja2"
            return "component.spec.ts.jinja2"
        elif suite.test_type.value == "e2e":
            return "e2e_app.spec.ts.jinja2"
        return ""

    def _get_file_path(self, suite: TestSuite, case: "TestCase") -> str:
        """Xác định file path cho test case."""
        entity_snake = case.target.lower().replace(" ", "_")
        if suite.test_type.value == "e2e":
            return f"e2e/src/{entity_snake}.e2e-spec.ts"
        elif case.tags and "service" in case.tags:
            return f"src/app/services/{entity_snake}-service.spec.ts"
        else:
            return f"src/app/components/{entity_snake}-component.spec.ts"

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
