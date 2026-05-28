# coding: utf-8
"""
F10: Code Quality & Security Scanner Generator (merged with CP25 Performance Testing).

Cung cấp:
- Quality models: SeverityLevel, StackType, LinterType, FormatterType, SecurityTool,
          QualityProfile, SecurityScanRule, SecurityScanConfig, QualityGateConfig,
          QualityViolation, QualityReport, QualityCollection
- Quality parser: QualityProfileParser
- Quality recipes: auto_generate_quality_collection, generate_default_profiles, ...
- Quality emitters: FastAPIQualityEmitter, NestJSQualityEmitter, AngularQualityEmitter, ReactQualityEmitter
- Data Quality models: DataQualityProfile, DataQualityRule, QualityCheck, QualityResult,
          QualityThreshold, AlertSeverity
- Perf models: PerfScenarioType, PerfScenario, PerfThreshold, PerfBaseline, PerfReport,
          PerfSuite, PerfCollection
- Perf parser: PerfParser
- Perf baseline: BaselineManager
- Perf recipes: auto_generate_perf_scenarios_from_mir, generate_load_scenarios,
          generate_web_vitals_tests, save_baseline, compare_baseline
- Perf emitters: FastAPIPerfEmitter, NestJSPerfEmitter, AngularPerfEmitter, ReactPerfEmitter

Author: Midicoder Team
Version: 2.0.0
"""

from midicoder.packs.cp_full_quality_security.angular import AngularQualityEmitter
from midicoder.packs.cp_full_quality_security.fastapi import FastAPIQualityEmitter
from midicoder.packs.cp_full_quality_security.models import (
    AlertSeverity,
    DataQualityProfile,
    DataQualityRule,
    FormatterType,
    LinterType,
    PerfBaseline,
    PerfCollection,
    PerfReport,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
    PerfThreshold,
    QualityCheck,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    QualityReport,
    QualityResult,
    QualityThreshold,
    QualityViolation,
    SecurityScanConfig,
    SecurityScanRule,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.packs.cp_full_quality_security.nestjs import NestJSQualityEmitter
from midicoder.packs.cp_full_quality_security.parser import QualityProfileParser, PerfParser
from midicoder.packs.cp_full_quality_security.recipes import (
    RecipeOutput,
    auto_generate_quality_collection,
    data_quality_recipe,
    generate_default_profiles,
    generate_security_config,
    generate_strict_profiles,
)
from midicoder.packs.cp_full_quality_security.react import ReactQualityEmitter
from midicoder.packs.cp_full_quality_security.baseline import BaselineManager
from midicoder.packs.cp_full_quality_security.recipes import (
    auto_generate_perf_scenarios_from_mir,
    compare_baseline,
    generate_load_scenarios,
    generate_web_vitals_tests,
    save_baseline,
)

__all__ = [
    # Quality Models - Enums
    "AlertSeverity",
    "DataQualityRule",
    "FormatterType",
    "LinterType",
    "SecurityTool",
    "SeverityLevel",
    "StackType",
    # Quality Models - Dataclasses
    "AngularQualityEmitter",
    "DataQualityProfile",
    "FastAPIQualityEmitter",
    "NestJSQualityEmitter",
    "QualityCheck",
    "QualityCollection",
    "QualityGateConfig",
    "QualityProfile",
    "QualityProfileParser",
    "QualityReport",
    "QualityResult",
    "QualityThreshold",
    "QualityViolation",
    "ReactQualityEmitter",
    "RecipeOutput",
    "SecurityScanConfig",
    "SecurityScanRule",
    # Quality Recipes
    "auto_generate_quality_collection",
    "data_quality_recipe",
    "generate_default_profiles",
    "generate_security_config",
    "generate_strict_profiles",
    # Perf Models - Enum
    "PerfScenarioType",
    # Perf Models - Dataclasses
    "PerfBaseline",
    "PerfCollection",
    "PerfReport",
    "PerfScenario",
    "PerfSuite",
    "PerfThreshold",
    # Perf Baseline Manager
    "BaselineManager",
    # Perf Recipes
    "auto_generate_perf_scenarios_from_mir",
    "compare_baseline",
    "generate_load_scenarios",
    "generate_web_vitals_tests",
    "save_baseline",
]
