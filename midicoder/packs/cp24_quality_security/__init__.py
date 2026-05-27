# coding: utf-8
"""
CP24: Code Quality & Security Scanner Generator.

Cung cấp:
- models: SeverityLevel, StackType, LinterType, FormatterType, SecurityTool,
          QualityProfile, SecurityScanRule, SecurityScanConfig, QualityGateConfig,
          QualityViolation, QualityReport, QualityCollection
- parser: QualityProfileParser
- recipes: auto_generate_quality_collection, generate_default_profiles, ...
- fastapi: FastAPIQualityEmitter
- nestjs: NestJSQualityEmitter
- angular: AngularQualityEmitter
- react: ReactQualityEmitter

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp24_quality_security.angular import AngularQualityEmitter
from midicoder.packs.cp24_quality_security.fastapi import FastAPIQualityEmitter
from midicoder.packs.cp24_quality_security.models import (
    AlertSeverity,
    DataQualityProfile,
    DataQualityRule,
    FormatterType,
    LinterType,
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
from midicoder.packs.cp24_quality_security.nestjs import NestJSQualityEmitter
from midicoder.packs.cp24_quality_security.parser import QualityProfileParser
from midicoder.packs.cp24_quality_security.recipes import (
    RecipeOutput,
    auto_generate_quality_collection,
    data_quality_recipe,
    generate_default_profiles,
    generate_security_config,
    generate_strict_profiles,
)
from midicoder.packs.cp24_quality_security.react import ReactQualityEmitter

__all__ = [
    "AlertSeverity",
    "AngularQualityEmitter",
    "auto_generate_quality_collection",
    "DataQualityProfile",
    "DataQualityRule",
    "data_quality_recipe",
    "FastAPIQualityEmitter",
    "FormatterType",
    "generate_default_profiles",
    "generate_security_config",
    "generate_strict_profiles",
    "LinterType",
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
    "SecurityTool",
    "SeverityLevel",
    "StackType",
]
