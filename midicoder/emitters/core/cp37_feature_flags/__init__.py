# coding: utf-8
"""
CP37 — Feature Flags & Dynamic Config.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp37_feature_flags.models import (
    ABExperiment,
    ABExperimentAssignment,
    ABExperimentEngine,
    ABVariant,
    ConfigChange,
    ConfigScope,
    ConfigValueType,
    ConditionType,
    DynamicConfig,
    FeatureFlag,
    FeatureFlagEvaluator,
    FlagEvaluation,
    FlagStore,
    FlagVariantType,
    TargetingRule,
)
from midicoder.emitters.core.cp37_feature_flags.parser import (
    FeatureFlagIR,
    parse_configs,
    parse_experiments,
    parse_feature_flags,
    parse_to_ir,
)
from midicoder.emitters.core.cp37_feature_flags.recipes import (
    RecipeOutput,
    ab_testing_recipe,
    dynamic_config_recipe,
    simple_flags_recipe,
)
from midicoder.emitters.core.cp37_feature_flags.fastapi import (
    FastAPIFeatureFlagEmitter,
)
from midicoder.emitters.core.cp37_feature_flags.nestjs import (
    NestJSFeatureFlagEmitter,
)
from midicoder.emitters.core.cp37_feature_flags.angular import (
    AngularFeatureFlagEmitter,
)
from midicoder.emitters.core.cp37_feature_flags.react import (
    ReactFeatureFlagEmitter,
)

__all__ = [
    # Models - Enums
    "FlagVariantType",
    "ConditionType",
    "ConfigScope",
    "ConfigValueType",
    # Models - Feature Flags
    "FeatureFlag",
    "TargetingRule",
    "FlagEvaluation",
    "FeatureFlagEvaluator",
    # Models - A/B Testing
    "ABExperiment",
    "ABVariant",
    "ABExperimentAssignment",
    "ABExperimentEngine",
    # Models - Dynamic Config
    "DynamicConfig",
    "ConfigChange",
    # Models - Storage
    "FlagStore",
    # Parser
    "FeatureFlagIR",
    "parse_feature_flags",
    "parse_experiments",
    "parse_configs",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "simple_flags_recipe",
    "ab_testing_recipe",
    "dynamic_config_recipe",
    # Emitters
    "FastAPIFeatureFlagEmitter",
    "NestJSFeatureFlagEmitter",
    "AngularFeatureFlagEmitter",
    "ReactFeatureFlagEmitter",
]
