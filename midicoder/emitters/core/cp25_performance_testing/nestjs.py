# coding: utf-8
"""
Mô-đun NestJS emitter cho Performance Testing Generator (CP25).

Sinh code Artillery cho NestJS:
- artillery.yml — Artillery scenario config
- tests/perf/baseline.spec.ts — Baseline runner

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.pipeline.emitter import Emitter

from midicoder.emitters.core.cp25_performance_testing.models import (
    PerfCollection,
)


class NestJSPerfEmitter:
    """
    Emitter sinh code Artillery cho NestJS.

    Sinh ra:
    - artillery.yml — Artillery scenario config
    - tests/perf/baseline.spec.ts — Baseline runner
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Init emitter."""
        self.emitter = Emitter(stack="nestjs")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: PerfCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ perf test files cho NestJS."""
        results: list[dict[str, str]] = []

        results.extend(self._generate_artillery(collection, commands or [], queries or []))
        results.extend(self._generate_baseline(collection))

        return results

    def _generate_artillery(
        self,
        collection: PerfCollection,
        commands: list[dict[str, Any]],
        queries: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Sinh artillery.yml scenarios."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/artillery.yml.jinja2",
                {
                    "collection": collection,
                    "commands": commands,
                    "queries": queries,
                    "scenarios": collection.get_all_scenarios(),
                },
            )
            return [{"path": "artillery.yml", "content": content}]
        except Exception:
            return []

    def _generate_baseline(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh baseline runner."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/perf_baseline.spec.ts.jinja2",
                {"collection": collection},
            )
            return [{"path": "tests/perf/baseline.spec.ts", "content": content}]
        except Exception:
            return []
