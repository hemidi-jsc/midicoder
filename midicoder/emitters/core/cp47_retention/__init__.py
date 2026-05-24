# coding: utf-8
"""
CP47 — Data Retention & Lifecycle Management.

Re-exports:
- models: RetentionAction, RetentionPolicyType, RetentionPolicyStatus,
          ArchiveStatus, ErasureStatus, RetentionPolicy, ArchivedRecord,
          ErasureRequest, RetentionEngine
- parser: RetentionIR, parse_policies, parse_retention_config, parse_to_ir
- recipes: RecipeOutput, basic_retention_recipe, full_lifecycle_recipe

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp47_retention.models import (
    ArchiveStatus,
    ArchivedRecord,
    ErasureRequest,
    ErasureStatus,
    RetentionAction,
    RetentionEngine,
    RetentionPolicy,
    RetentionPolicyStatus,
    RetentionPolicyType,
)
from midicoder.emitters.core.cp47_retention.parser import (
    RetentionIR,
    parse_policies,
    parse_retention_config,
    parse_to_ir,
)
from midicoder.emitters.core.cp47_retention.recipes import (
    RecipeOutput,
    basic_retention_recipe,
    full_lifecycle_recipe,
)

__all__ = [
    # Enums
    "RetentionAction",
    "RetentionPolicyType",
    "RetentionPolicyStatus",
    "ArchiveStatus",
    "ErasureStatus",
    # Dataclasses
    "RetentionPolicy",
    "ArchivedRecord",
    "ErasureRequest",
    # Engine
    "RetentionEngine",
    # Parser
    "RetentionIR",
    "parse_policies",
    "parse_retention_config",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_retention_recipe",
    "full_lifecycle_recipe",
]
