# coding: utf-8
"""
Unit tests cho 4 stack emitters của CP25.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp25_performance_testing.angular import AngularPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.fastapi import FastAPIPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.models import (
    PerfCollection,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
)
from midicoder.emitters.core.cp25_performance_testing.nestjs import NestJSPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.react import ReactPerfEmitter


class TestFastAPIPerfEmitter:
    """Test FastAPIPerfEmitter."""

    def test_generate_locustfile(self) -> None:
        """FastAPI emitter sinh locustfile.py."""
        collection = PerfCollection()
        suite = PerfSuite(name="fastapi_perf", stack="fastapi")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = FastAPIPerfEmitter("stacks/fastapi/core")
        results = emitter.generate(collection, entities=[{"id": "CreateOrder"}])

        paths = [r["path"] for r in results]
        assert "locustfile.py" in paths

    def test_generate_locust_conf(self) -> None:
        """FastAPI emitter sinh locust.conf."""
        collection = PerfCollection()
        suite = PerfSuite(name="fastapi_perf", stack="fastapi")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = FastAPIPerfEmitter("stacks/fastapi/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "locust.conf" in paths

    def test_generate_baseline(self) -> None:
        """FastAPI emitter sinh baseline runner."""
        collection = PerfCollection()
        suite = PerfSuite(name="fastapi_perf", stack="fastapi")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = FastAPIPerfEmitter("stacks/fastapi/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "tests/perf/baseline.py" in paths


class TestNestJSPerfEmitter:
    """Test NestJSPerfEmitter."""

    def test_generate_artillery(self) -> None:
        """NestJS emitter sinh artillery.yml."""
        collection = PerfCollection()
        suite = PerfSuite(name="nestjs_perf", stack="nestjs")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = NestJSPerfEmitter("stacks/nestjs/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "artillery.yml" in paths

    def test_generate_baseline(self) -> None:
        """NestJS emitter sinh baseline runner."""
        collection = PerfCollection()
        suite = PerfSuite(name="nestjs_perf", stack="nestjs")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = NestJSPerfEmitter("stacks/nestjs/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "tests/perf/baseline.spec.ts" in paths


class TestAngularPerfEmitter:
    """Test AngularPerfEmitter."""

    def test_generate_lighthouserc(self) -> None:
        """Angular emitter sinh lighthouserc.js."""
        collection = PerfCollection()
        suite = PerfSuite(name="angular_perf", stack="angular")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = AngularPerfEmitter("stacks/angular/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "lighthouserc.js" in paths

    def test_generate_web_vitals(self) -> None:
        """Angular emitter sinh web-vitals.spec.ts."""
        collection = PerfCollection()
        suite = PerfSuite(name="angular_perf", stack="angular")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = AngularPerfEmitter("stacks/angular/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "tests/perf/web-vitals.spec.ts" in paths

    def test_generate_lighthouse_ci(self) -> None:
        """Angular emitter sinh lighthouse-ci.js."""
        collection = PerfCollection()
        suite = PerfSuite(name="angular_perf", stack="angular")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = AngularPerfEmitter("stacks/angular/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "tests/perf/lighthouse-ci.js" in paths


class TestReactPerfEmitter:
    """Test ReactPerfEmitter."""

    def test_generate_lighthouserc(self) -> None:
        """React emitter sinh lighthouserc.js."""
        collection = PerfCollection()
        suite = PerfSuite(name="react_perf", stack="react")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = ReactPerfEmitter("stacks/react/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "lighthouserc.js" in paths

    def test_generate_web_vitals(self) -> None:
        """React emitter sinh web-vitals.test.tsx."""
        collection = PerfCollection()
        suite = PerfSuite(name="react_perf", stack="react")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = ReactPerfEmitter("stacks/react/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "src/__tests__/perf/web-vitals.test.tsx" in paths

    def test_generate_lighthouse_ci(self) -> None:
        """React emitter sinh lighthouse-ci.js."""
        collection = PerfCollection()
        suite = PerfSuite(name="react_perf", stack="react")
        suite.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="CreateOrder"))
        collection.add_suite(suite)

        emitter = ReactPerfEmitter("stacks/react/core")
        results = emitter.generate(collection)

        paths = [r["path"] for r in results]
        assert "tests/perf/lighthouse-ci.js" in paths
