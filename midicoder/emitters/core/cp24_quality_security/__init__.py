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

from midicoder.emitters.core.cp24_quality_security.angular import AngularQualityEmitter
from midicoder.emitters.core.cp24_quality_security.fastapi import FastAPIQualityEmitter
from midicoder.emitters.core.cp24_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    QualityReport,
    QualityViolation,
    SecurityScanConfig,
    SecurityScanRule,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.emitters.core.cp24_quality_security.nestjs import NestJSQualityEmitter
from midicoder.emitters.core.cp24_quality_security.parser import QualityProfileParser
from midicoder.emitters.core.cp24_quality_security.recipes import (
    auto_generate_quality_collection,
    generate_default_profiles,
    generate_security_config,
    generate_strict_profiles,
)
from midicoder.emitters.core.cp24_quality_security.react import ReactQualityEmitter

__all__ = [
    "AngularQualityEmitter",
    "auto_generate_quality_collection",
    "FastAPIQualityEmitter",
    "FormatterType",
    "generate_default_profiles",
    "generate_security_config",
    "generate_strict_profiles",
    "LinterType",
    "NestJSQualityEmitter",
    "QualityCollection",
    "QualityGateConfig",
    "QualityProfile",
    "QualityProfileParser",
    "QualityReport",
    "QualityViolation",
    "ReactQualityEmitter",
    "SecurityScanConfig",
    "SecurityScanRule",
    "SecurityTool",
    "SeverityLevel",
    "StackType",
]
