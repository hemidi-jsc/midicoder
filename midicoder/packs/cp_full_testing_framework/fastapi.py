# coding: utf-8
"""
Mô-đun FastAPI emitter cho Testing Framework Generator (CP23).

Emit code pytest cho FastAPI:
- conftest.py (fixtures)
- pytest.ini (config)
- Unit tests (entity, command, query)
- Integration tests (API)
- E2E tests (flow)
- Coverage config

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.packs.cp_full_testing_framework.models import (
    TestCollection,
    TestSuite,
)


class FastAPITestEmitter:
    """
    Emitter sinh code pytest cho FastAPI.

    Sinh ra:
    - tests/conftest.py — pytest fixtures
    - pytest.ini — config
    - tests/unit/test_{entity}.py — unit tests
    - tests/integration/test_{entity}_api.py — integration tests
    - tests/e2e/test_flows.py — E2E tests
    - .coveragerc — coverage config
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Init emitter.

        Args:
            stack_dir: Đường dẫn đến template directory
        """
        self.emitter = Emitter(stack="fastapi")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: TestCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ test files cho FastAPI.

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
        results.extend(self._generate_conftest(collection, entities or []))
        results.extend(self._generate_pytest_ini(collection))
        results.extend(self._generate_coverage_config(collection))

        # Per-suite test files
        for suite in collection.suites:
            results.extend(self._generate_suite(suite, entities or [], commands or [], queries or []))

        return results

    def _generate_conftest(
        self,
        collection: TestCollection,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh conftest.py với pytest fixtures."""
        try:
            content = self.emitter.render(
                "cp_full_testing_framework/conftest.py.jinja2",
                {
                    "collection": collection,
                    "entities": entities,
                    "suite_names": [s.name for s in collection.suites],
                },
            )
            return [{"path": "tests/conftest.py", "content": content}]
        except Exception:
            return []

    def _generate_pytest_ini(self, collection: TestCollection) -> list[dict[str, str]]:
        """Sinh pytest.ini config."""
        try:
            content = self.emitter.render(
                "cp_full_testing_framework/pytest.ini.jinja2",
                {"collection": collection},
            )
            return [{"path": "pytest.ini", "content": content}]
        except Exception:
            return []

    def _generate_coverage_config(self, collection: TestCollection) -> list[dict[str, str]]:
        """Sinh .coveragerc config."""
        try:
            content = self.emitter.render(
                "cp_full_testing_framework/coverage_config.py.jinja2",
                {"collection": collection},
            )
            return [{"path": ".coveragerc", "content": content}]
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
                    f"cp_full_testing_framework/{template_name}",
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
            if "command" in case.target.lower() or case.tags and "command" in case.tags:
                return "unit_test_command.py.jinja2"
            elif "query" in case.target.lower() or case.tags and "query" in case.tags:
                return "unit_test_query.py.jinja2"
            else:
                return "unit_test_entity.py.jinja2"
        elif suite.test_type.value == "integration":
            return "integration_test_api.py.jinja2"
        elif suite.test_type.value == "e2e":
            return "e2e_test_flow.py.jinja2"
        return ""

    def _get_file_path(self, suite: TestSuite, case: "TestCase") -> str:
        """Xác định file path cho test case."""
        if suite.test_type.value == "unit":
            return f"tests/unit/test_{case.target.lower()}.py"
        elif suite.test_type.value == "integration":
            return f"tests/integration/test_{case.target.lower()}_api.py"
        elif suite.test_type.value == "e2e":
            return f"tests/e2e/test_{case.scenario.lower().replace(' ', '_')}.py"
        return f"tests/test_{case.id}.py"

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
