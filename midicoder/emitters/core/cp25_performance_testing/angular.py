# coding: utf-8
"""
Mô-đun Angular emitter cho Performance Testing Generator (CP25).

Sinh code Lighthouse CI + Playwright cho Angular:
- lighthouserc.js — Lighthouse config
- tests/perf/web-vitals.spec.ts — Playwright Web Vitals
- tests/perf/lighthouse-ci.js — Lighthouse CI runner

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


class AngularPerfEmitter:
    """
    Emitter sinh code Lighthouse CI + Playwright cho Angular.

    Sinh ra:
    - lighthouserc.js — Lighthouse config
    - tests/perf/web-vitals.spec.ts — Playwright Web Vitals
    - tests/perf/lighthouse-ci.js — Lighthouse CI runner
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Init emitter."""
        self.emitter = Emitter(stack="angular")
        self.stack_dir = Path(stack_dir)

    def generate(
        self,
        collection: PerfCollection,
        entities: list[dict[str, Any]] | None = None,
        commands: list[dict[str, Any]] | None = None,
        queries: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        """Generate toàn bộ perf test files cho Angular."""
        results: list[dict[str, str]] = []

        results.extend(self._generate_lighthouserc(collection))
        results.extend(self._generate_web_vitals(collection))
        results.extend(self._generate_lighthouse_ci(collection))

        return results

    def _generate_lighthouserc(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh lighthouserc.js config."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/lighthouserc.js.jinja2",
                {"collection": collection},
            )
            return [{"path": "lighthouserc.js", "content": content}]
        except Exception:
            return []

    def _generate_web_vitals(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh Playwright Web Vitals test."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/web_vitals.spec.ts.jinja2",
                {"collection": collection},
            )
            return [{"path": "tests/perf/web-vitals.spec.ts", "content": content}]
        except Exception:
            return []

    def _generate_lighthouse_ci(self, collection: PerfCollection) -> list[dict[str, str]]:
        """Sinh Lighthouse CI runner."""
        try:
            content = self.emitter.render(
                "cp25_performance_testing/lighthouse_ci.js.jinja2",
                {"collection": collection},
            )
            return [{"path": "tests/perf/lighthouse-ci.js", "content": content}]
        except Exception:
            return []
