# coding: utf-8
"""
Mô-đun FastAPI emitter cho Performance Testing Generator (CP25).

Sinh code Locust cho FastAPI:
- locustfile.py — HTTPUser classes cho load testing
- locust.conf — Locust config
- tests/perf/test_{entity}.py — Perf test files
- tests/perf/baseline.py — Baseline runner

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp25_performance_testing.models import (
    PerfCollection,
    PerfSuite,
)


class FastAPIPerfEmitter:
    """
    Emitter sinh code Locust cho FastAPI.

    Sinh ra:
    - locustfile.py — Locust HTTPUser classes
    - locust.conf — Locust config
    - tests/perf/test_{entity}.py — Perf test files per entity
    - tests/perf/baseline.py — Baseline runner
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
        collection: PerfCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ perf test files cho FastAPI.

        Args:
            collection: PerfCollection từ parser
            entities: Danh sách entities từ MIR metadata
            commands: Danh sách commands từ MIR metadata
            queries: Danh sách queries từ MIR metadata

        Returns:
            Danh sách {path, content} cho mỗi file sinh ra
        """
        results: list[dict[str, str]] = []

        # Infrastructure files
        results.extend(self._generate_locustfile(collection, entities or [], commands or [], queries or []))
        results.extend(self._generate_locust_conf(collection))
        results.extend(self._generate_baseline(collection))

        # Per-scenario test files
        for suite in collection.suites:
            for scenario in suite.scenarios:
                results.extend(self._generate_perf_test(suite, scenario, entities or []))

        return results

    def _generate_locustfile(
        self,
        collection: PerfCollection,
        entities: list[dict[str, Any]],
        commands: list[dict[str, Any]],
        queries: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh locustfile.py với HTTPUser classes."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/locustfile.py.jinja2",
                {
                    "collection": collection,
                    "entities": entities,
                    "commands": commands,
                    "queries": queries,
                    "scenarios": collection.get_all_scenarios(),
                },
            )
            return [{"path": "locustfile.py", "content": content}]
        except Exception:
            return []

    def _generate_locust_conf(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh locust.conf config."""
        try:
            all_scenarios = collection.get_all_scenarios()
            total_users = sum(s.concurrent_users for s in all_scenarios) if all_scenarios else 100
            total_spawn = sum(s.spawn_rate for s in all_scenarios) if all_scenarios else 10

            content = self.emitter.render(
                "cp25_performance_testing/locust.conf.jinja2",
                {
                    "collection": collection,
                    "total_users": total_users,
                    "total_spawn_rate": total_spawn,
                    "scenarios": all_scenarios,
                },
            )
            return [{"path": "locust.conf", "content": content}]
        except Exception:
            return []

    def _generate_baseline(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh baseline runner."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/perf_baseline.py.jinja2",
                {"collection": collection},
            )
            return [{"path": "tests/perf/baseline.py", "content": content}]
        except Exception:
            return []

    def _generate_perf_test(
        self,
        suite: PerfSuite,
        scenario: "PerfScenario",
        entities: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh perf test file cho 1 scenario."""
        try:
            entity = self._find_entity(scenario.target, entities)
            content = self.emitter.render(
                "cp25_performance_testing/perf_test_entity.py.jinja2",
                {
                    "scenario": scenario,
                    "suite": suite,
                    "entity": entity,
                    "all_entities": entities,
                },
            )
            file_path = f"tests/perf/test_{scenario.target.lower()}.py"
            return [{"path": file_path, "content": content}]
        except Exception:
            return []

    def _find_entity(self, target: str, entities: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Tìm entity theo target ID."""
        for e in entities:
            if e.get("id", "").lower() == target.lower():
                return e
        return None


# Import cho template context
from midicoder.emitters.core.cp25_performance_testing.models import PerfScenario  # noqa: E402
