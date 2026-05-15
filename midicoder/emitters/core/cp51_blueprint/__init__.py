# coding: utf-8
"""
Blueprint Composition Engine (CP51)

Hệ thống composition engine để compose multiple packs (CPs + DPs + RXs)
thành unified blueprint. Cung cấp:
- CapabilityGraph: DAG của capabilities từ tất cả packs
- Resolution: Resolve dependencies và trả về topological order
- MergeStrategy: Chiến lược merge output từ nhiều packs
- BlueprintSchema: Schema versioning + backward compatibility
- Recipes: Pre-mixed concrete blueprints (FullStack, BackendOnly, v.v.)
- CompositionPlan: Kế hoạch composition hoàn chỉnh (emit order, template mapping)
- PackResolver: Resolve packs từ TaxonomyRegistry
- CompositionEngine: Orchestrate full composition flow

Sử dụng:
    from midicoder.emitters.core.cp51_blueprint import (
        CapabilityGraph,
        CapabilityNode,
        Resolution,
        MergeStrategy,
        BlueprintSchema,
        VersionConstraint,
        FullStackBlueprintRecipe,
        BackendOnlyRecipe,
        CompositionPlan,
        PackResolver,
        CompositionEngine,
    )

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.cp51_blueprint.models import (
    CapabilityNode,
    CapabilityGraph,
    ResolutionStatus,
    Resolution,
    MergeMode,
    MergeStrategy,
    ConflictResolution,
    BlueprintSchema,
    VersionConstraint,
    # Composition plan models (từ contracts/composition/)
    CompositionNode,
    PackResolution,
    TemplateBinding,
    StackBinding,
    CompositionPlan,
)

from midicoder.emitters.core.cp51_blueprint.recipes import (
    FullStackBlueprintRecipe,
    BackendOnlyRecipe,
    FrontendOnlyRecipe,
    MicroserviceBlueprintRecipe,
    MonolithRecipe,
)

from midicoder.emitters.core.cp51_blueprint.resolver import PackResolver

from midicoder.emitters.core.cp51_blueprint.engine import CompositionEngine

__all__ = [
    # Models — CapabilityGraph
    "CapabilityNode",
    "CapabilityGraph",
    # Models — Resolution
    "ResolutionStatus",
    "Resolution",
    # Models — MergeStrategy + ConflictResolution
    "MergeMode",
    "MergeStrategy",
    "ConflictResolution",
    # Models — BlueprintSchema + VersionConstraint
    "BlueprintSchema",
    "VersionConstraint",
    # Models — Composition Plan
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
    # Recipes
    "FullStackBlueprintRecipe",
    "BackendOnlyRecipe",
    "FrontendOnlyRecipe",
    "MicroserviceBlueprintRecipe",
    "MonolithRecipe",
    # Resolver + Engine
    "PackResolver",
    "CompositionEngine",
]
