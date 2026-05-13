"""
Module Artifact Contracts cho Midicoder v1.0.0

Module này định nghĩa các contract chuẩn cho artifacts trong pipeline:
- Artifact base types: Metadata, versioning, serialization
- MIR (Intermediate Representation): Implementation truth typed
- Surface/Patch Plan: Map capabilities → runtime surfaces → delivery plan

Tất cả artifacts được thiết kế để:
1. Deterministic: Same input → same output (hashable)
2. Verifiable: Machine-readable validation
3. Portable: Vendor-agnostic format
4. Auditable: Clear provenance và metadata

Author: Midicoder Team
Version: 1.0.0
"""

from .artifact import (
    ArtifactBase,
    ArtifactMetadata,
    ArtifactVersion,
    write_artifact,
    read_artifact,
    compute_content_hash,
    compute_file_hash,
)
from midicoder.pipeline.mir import (
    MIR,
    Operation,
    DataFlow,
    EffectFlow,
    Boundary,
)

# Backward-compatibility aliases (deprecated — keep for legacy consumers)
MIROperation = Operation
MIRDataFlow = DataFlow
MIREffectFlow = EffectFlow
MIRBoundary = Boundary
from .plan import (
    Surface,
    SurfaceType,
    # SurfacePlan and PatchPlan are deprecated — dead code, not used in pipeline.
    # Keep imports available for legacy consumers but do NOT re-export in __all__.
    SurfacePlan as _DeprecatedSurfacePlan,  # noqa: F401
    TargetPlan,
    PatchOperation,
    PatchOperationType,
    PatchPlan as _DeprecatedPatchPlan,  # noqa: F401
)
from .composition.models import (
    CompositionNode,
    PackResolution,
    TemplateBinding,
    StackBinding,
    CompositionPlan,
)
from .composition.resolver import PackResolver
from .composition.engine import CompositionEngine

__all__ = [
    # Artifact base
    "ArtifactBase",
    "ArtifactMetadata",
    "ArtifactVersion",
    "write_artifact",
    "read_artifact",
    "compute_content_hash",
    "compute_file_hash",

    # MIR
    "MIR",
    "MIROperation",
    "MIRDataFlow",
    "MIREffectFlow",
    "MIRBoundary",

    # Plans
    "Surface",
    "SurfaceType",
    # "SurfacePlan" — deprecated, removed from public API (dead code)
    # "PatchPlan" — deprecated, removed from public API (dead code)
    "TargetPlan",
    "PatchOperation",
    "PatchOperationType",

    # Composition Engine
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
    "PackResolver",
    "CompositionEngine",
]
