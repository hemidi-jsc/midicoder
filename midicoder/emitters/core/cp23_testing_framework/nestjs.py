# coding: utf-8
"""
Mô-đun NestJS emitter cho Testing Framework Generator (CP23).

Emit code Jest cho NestJS:
- jest.config.ts (config)
- Entity spec files
- Command handler spec files
- Query handler spec files
- Integration spec files
- E2E flow spec files

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp23_testing_framework.models import (
    TestCollection,
    TestSuite,
)


class NestJSTestEmitter:
    """
    Emitter sinh code Jest cho NestJS.

    Sinh ra:
    - jest.config.ts — Jest config
    - src/**/entities/{entity}.entity.spec.ts
    - src/**/commands/{command}.handler.spec.ts
    - src/**/queries/{query}.handler.spec.ts
    - src/integration/{entity}.integration.spec.ts
    - src/e2e/flows.spec.ts
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Init emitter.

        Args:
            stack_dir: Đường dẫn đến template directory
        """
        self.emitter = Emitter(stack="nestjs")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: TestCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ test files cho NestJS.

        Args:
            collection: TestCollection từ parser
            entities: Danh sách entities từ MIR metadata
            commands: Danh sách commands từ MIR metadata
            queries: Danh sách queries từ MIR metadata

        Returns:
            Danh sách {path, content} cho mỗi file sinh ra
        """
        results: list[dict[str, str]] = []

        # Infrastructure files
        results.extend(self._generate_jest_config(collection))

        # Per-suite test files
        for suite in collection.suites:
            results.extend(self._generate_suite(suite, entities or [], commands or [], queries or []))

        return results

    def _generate_jest_config(self, collection: TestCollection) -> list[dict[str, str]]:
        """Sinh jest.config.ts."""
        try:
            content = self.emitter.render(
                "cp23_testing_framework/jest.config.ts.jinja2",
                {"collection": collection},
            )
            return [{"path": "jest.config.ts", "content": content}]
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
        if suite.test_type.value == "unit":
            if case.tags and "command" in case.tags:
                return "command_handler.spec.ts.jinja2"
            elif case.tags and "query" in case.tags:
                return "query_handler.spec.ts.jinja2"
            else:
                return "entity.spec.ts.jinja2"
        elif suite.test_type.value == "integration":
            return "integration.spec.ts.jinja2"
        elif suite.test_type.value == "e2e":
            return "e2e_flows.spec.ts.jinja2"
        return ""

    def _get_file_path(self, suite: TestSuite, case: "TestCase") -> str:
        """Xác định file path cho test case."""
        entity_snake = case.target.lower().replace(" ", "_")
        if suite.test_type.value == "unit":
            if case.tags and "command" in case.tags:
                return f"src/commands/{entity_snake}.handler.spec.ts"
            elif case.tags and "query" in case.tags:
                return f"src/queries/{entity_snake}.handler.spec.ts"
            else:
                return f"src/entities/{entity_snake}.entity.spec.ts"
        elif suite.test_type.value == "integration":
            return f"src/integration/{entity_snake}.integration.spec.ts"
        elif suite.test_type.value == "e2e":
            return f"src/e2e/{entity_snake}.e2e.spec.ts"
        return f"src/__tests__/{entity_snake}.spec.ts"

    def _find_entity(self, target: str, entities: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Tìm entity theo target ID."""
        for e in entities:
            if e.get("id", "").lower() == target.lower():
                return e
        return None

    def _find_item(self, target: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Tìm item theo target ID."""
        for item in items:
            if item.get("id", "").lower() == target.lower():
                return item
        return None
