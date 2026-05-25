# coding: utf-8
"""
Public API Surface cho Midicoder CE pipeline.

Module này là điểm import ổn định cho internal consumers (emitters, templates,
pipeline). Không chứa implementation logic — chỉ re-export types từ source
of truth.

**Không phải cho generated code dùng.** Generated code phải standalone —
không import từ `midicoder.*`.

Nguồn re-export:
- MIR types ← `pipeline/mir.py` (source of truth)
- Plan types ← `pipeline/plan.py` (source of truth)
- Artifact types ← `contracts/artifact.py` (own code)
- CP51 Composition ← `emitters/core/cp51_blueprint/` (own code)
- Registry ← `contracts/registry.py` (single source mapping)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

# ============================================================================
# MIR types (source: pipeline/mir.py)
# ============================================================================

from midicoder.pipeline.mir import (
    MIR,
    Boundary,
    DataFlow,
    EffectFlow,
    Operation,
)

# Backward-compatibility aliases (deprecated — giữ để không break existing import)
MIROperation = Operation
MIRDataFlow = DataFlow
MIREffectFlow = EffectFlow
MIRBoundary = Boundary

# ============================================================================
# Plan types (source: pipeline/plan.py)
# ============================================================================

from midicoder.pipeline.plan import (
    FileSpec,
    ImplementationPlan,
    ModuleSpec,
    PlanBuilder,
)

# ============================================================================
# Artifact types (source: contracts/artifact.py — own code)
# ============================================================================

from .artifact import (
    ArtifactBase,
    ArtifactMetadata,
    ArtifactVersion,
    compute_content_hash,
    compute_file_hash,
    read_artifact,
    write_artifact,
)

# ============================================================================
# CP51 Composition (source: emitters/core/cp51_blueprint/)
# ============================================================================

from midicoder.emitters.core.cp51_blueprint.models import (
    CapabilityGraph,
    CompositionNode,
    CompositionPlan,
    PackResolution,
    StackBinding,
    TemplateBinding,
)
from midicoder.emitters.core.cp51_blueprint.resolver import PackResolver
from midicoder.emitters.core.cp51_blueprint.engine import CompositionEngine

# ============================================================================
# Registry (source: contracts/registry.py — single source mapping)
# ============================================================================

from .registry import (
    ALL_STACKS,
    BACKEND_STACKS,
    CP_ID_TO_INTERNAL,
    FRONTEND_STACKS,
    INFRA_STACK,
)

__all__ = [
    # MIR
    "MIR",
    "Operation",
    "DataFlow",
    "EffectFlow",
    "Boundary",
    # Backward-compat aliases
    "MIROperation",
    "MIRDataFlow",
    "MIREffectFlow",
    "MIRBoundary",
    # Plan
    "FileSpec",
    "ModuleSpec",
    "ImplementationPlan",
    "PlanBuilder",
    # Artifact
    "ArtifactBase",
    "ArtifactMetadata",
    "ArtifactVersion",
    "write_artifact",
    "read_artifact",
    "compute_content_hash",
    "compute_file_hash",
    # Composition (CP51)
    "CapabilityGraph",
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
    "PackResolver",
    "CompositionEngine",
    # Registry
    "CP_ID_TO_INTERNAL",
    "BACKEND_STACKS",
    "FRONTEND_STACKS",
    "INFRA_STACK",
    "ALL_STACKS",
]
