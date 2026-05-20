# coding: utf-8
"""
CP25: Performance Testing Generator.

Cung cấp:
- models: PerfScenarioType, PerfScenario, PerfThreshold, PerfBaseline, PerfReport, PerfSuite, PerfCollection
- parser: PerfParser
- recipes: auto_generate_perf_scenarios_from_mir, generate_load_scenarios, generate_web_vitals_tests, save_baseline, compare_baseline
- baseline: BaselineManager
- fastapi: FastAPIPerfEmitter (Locust)
- nestjs: NestJSPerfEmitter (Artillery)
- angular: AngularPerfEmitter (Lighthouse CI + Playwright)
- react: ReactPerfEmitter (Lighthouse CI + Playwright)

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp25_performance_testing.models import (
    PerfBaseline,
    PerfCollection,
    PerfReport,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
    PerfThreshold,
)
from midicoder.emitters.core.cp25_performance_testing.parser import PerfParser
from midicoder.emitters.core.cp25_performance_testing.baseline import BaselineManager
from midicoder.emitters.core.cp25_performance_testing.fastapi import FastAPIPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.nestjs import NestJSPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.angular import AngularPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.react import ReactPerfEmitter
from midicoder.emitters.core.cp25_performance_testing.recipes import (
    auto_generate_perf_scenarios_from_mir,
    compare_baseline,
    generate_load_scenarios,
    generate_web_vitals_tests,
    save_baseline,
)

__all__ = [
    "AngularPerfEmitter",
    "auto_generate_perf_scenarios_from_mir",
    "BaselineManager",
    "compare_baseline",
    "FastAPIPerfEmitter",
    "generate_load_scenarios",
    "generate_web_vitals_tests",
    "NestJSPerfEmitter",
    "PerfBaseline",
    "PerfCollection",
    "PerfParser",
    "PerfReport",
    "PerfScenario",
    "PerfScenarioType",
    "PerfSuite",
    "PerfThreshold",
    "ReactPerfEmitter",
    "save_baseline",
]
