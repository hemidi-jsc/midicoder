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

Sử dụng:
    from midicoder.emitters.core.blueprint import (
        CapabilityGraph,
        CapabilityNode,
        Resolution,
        MergeStrategy,
        BlueprintSchema,
        VersionConstraint,
        FullStackBlueprintRecipe,
        BackendOnlyRecipe,
    )

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.blueprint.models import (
    CapabilityNode,
    CapabilityGraph,
    ResolutionStatus,
    Resolution,
    MergeMode,
    MergeStrategy,
    ConflictResolution,
    BlueprintSchema,
    VersionConstraint,
)

from midicoder.emitters.core.blueprint.recipes import (
    FullStackBlueprintRecipe,
    BackendOnlyRecipe,
    FrontendOnlyRecipe,
    MicroserviceBlueprintRecipe,
    MonolithRecipe,
)

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
    # Recipes
    "FullStackBlueprintRecipe",
    "BackendOnlyRecipe",
    "FrontendOnlyRecipe",
    "MicroserviceBlueprintRecipe",
    "MonolithRecipe",
]
