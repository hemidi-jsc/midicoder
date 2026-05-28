# coding: utf-8
"""
F35: Service Discovery & Dynamic Config (merged: CP37 + CP60).

Public API barrel export.

Tác giả: Midicoder Team
Version: 2.0.0
"""

from midicoder.packs.cp_full_service_discovery.models import (
    # Feature Flags (CP37)
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
    # Service Discovery (CP60)
    Environment,
    LBStrategy,
    Protocol,
    RegistryProvider,
    ConfigEntry,
    ConfigWatch,
    LoadBalancingConfig,
    ServiceInstance,
    ServiceRegistry,
)
from midicoder.packs.cp_full_service_discovery.parser import (
    FeatureFlagIR,
    parse_configs,
    parse_experiments,
    parse_feature_flags,
    parse_to_ir,
)
from midicoder.packs.cp_full_service_discovery.recipes import (
    RecipeOutput,
    ab_testing_recipe,
    dynamic_config_recipe,
    simple_flags_recipe,
)
from midicoder.packs.cp_full_service_discovery.fastapi import (
    FastAPIFeatureFlagEmitter,
)
from midicoder.packs.cp_full_service_discovery.nestjs import (
    NestJSFeatureFlagEmitter,
)
from midicoder.packs.cp_full_service_discovery.angular import (
    AngularFeatureFlagEmitter,
)
from midicoder.packs.cp_full_service_discovery.react import (
    ReactFeatureFlagEmitter,
)

__all__ = [
    # Models - Feature Flags Enums (CP37)
    "FlagVariantType",
    "ConditionType",
    "ConfigScope",
    "ConfigValueType",
    # Models - Feature Flags (CP37)
    "FeatureFlag",
    "TargetingRule",
    "FlagEvaluation",
    "FeatureFlagEvaluator",
    # Models - A/B Testing (CP37)
    "ABExperiment",
    "ABVariant",
    "ABExperimentAssignment",
    "ABExperimentEngine",
    # Models - Dynamic Config (CP37)
    "DynamicConfig",
    "ConfigChange",
    # Models - Storage (CP37)
    "FlagStore",
    # Models - Service Discovery Enums (CP60)
    "Protocol",
    "RegistryProvider",
    "Environment",
    "LBStrategy",
    # Models - Service Discovery (CP60)
    "ServiceInstance",
    "ServiceRegistry",
    "ConfigEntry",
    "ConfigWatch",
    "LoadBalancingConfig",
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
