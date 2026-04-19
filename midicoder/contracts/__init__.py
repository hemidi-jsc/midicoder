"""
Module Artifact Contracts cho Midicoder v1.0.0

Module này định nghĩa các contract chuẩn cho artifacts trong pipeline:
- Capability Graph: Source of truth cho system capabilities
- Validation Report: Kết quả validation tại compile time
- Expansion Report: Trace macro expansion thành core instructions
- MIR (Intermediate Representation): Implementation truth typed
- Surface Plan: Map capabilities → runtime surfaces
- Patch Plan: Delivery plan cho code changes

Tất cả artifacts được thiết kế để:
1. Deterministic: Same input → same output (hashable)
2. Verifiable: Machine-readable validation
3. Portable: Vendor-agnostic format
4. Auditable: Clear provenance và metadata

Author: Midicoder Team
Version: 1.0.0
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .artifact import (
    ArtifactMetadata,
    ArtifactVersion,
    write_artifact,
    read_artifact,
)
from .graph import (
    CapabilityGraph,
    CapabilityInstance,
    MacroCapability,
    CoreCapability,
    Obligation,
)
from .mir import (
    MIR,
    MIROperation,
    MIRDataFlow,
    MIREffectFlow,
    MIRBoundary,
)
from .plan import (
    SurfacePlan,
    Surface,
    TargetPlan,
    PatchPlan,
    PatchOperation,
)
from .validation import (
    ValidationReport,
    ValidationError,
    ValidationWarning,
    ValidationStatus,
)
from .expansion import (
    ExpansionReport,
    ExpansionStep,
    ExpansionTrace,
)
from .capability_params import (
    CapabilityParams,
    AuthorizedMutationParams,
    AuthorizedQueryParams,
    CacheStrategyParams,
    DataExportParams,
    DataImportParams,
    ScheduledTaskParams,
    WorkflowDefinitionParams,
    AuditLogParams,
    EventHandlerParams,
    InboundIntegrationParams,
    OutboundIntegrationParams,
    MonitoringParams,
    RateLimitingParams,
    NotificationParams,
    MessageQueueParams,
    BatchJobParams,
    DataRetentionParams,
)
from .capability_validator import (
    CAPABILITY_VALIDATORS,
    validate_capability_params,
    get_known_capability_types,
)
from .core_capabilities import (
    CoreCapabilitiesRegistry,
    AuthorizationCoreCapabilities,
    DataOperationsCoreCapabilities,
    TransactionCoreCapabilities,
    EventIntegrationCoreCapabilities,
    AuditObservabilityCoreCapabilities,
)
from .blueprint_compiler import (
    BlueprintCompiler,
    BlueprintCompilerError,
    CompiledBlueprint,
    BlueprintMetadata,
    IndustryInfo,
    CorePacksConfig,
    DomainPackRef,
    RegulatoryOverlayRef,
    BusinessInvariant,
    ComplianceInvariant,
    FailureModeInvariant,
    InvariantsConfig,
    BlueprintConfig,
    BlueprintReferences,
)

__all__ = [
    # Artifact base
    "ArtifactMetadata",
    "ArtifactVersion",
    "write_artifact",
    "read_artifact",
    
    # Capability Graph
    "CapabilityGraph",
    "CapabilityInstance",
    "MacroCapability",
    "CoreCapability",
    "Obligation",
    
    # MIR
    "MIR",
    "MIROperation",
    "MIRDataFlow",
    "MIREffectFlow",
    "MIRBoundary",
    
    # Plans
    "SurfacePlan",
    "Surface",
    "TargetPlan",
    "PatchPlan",
    "PatchOperation",
    
    # Validation
    "ValidationReport",
    "ValidationError",
    "ValidationWarning",
    "ValidationStatus",
    
    # Expansion
    "ExpansionReport",
    "ExpansionStep",
    "ExpansionTrace",
    
    # Capability Params
    "CapabilityParams",
    "AuthorizedMutationParams",
    "AuthorizedQueryParams",
    "CacheStrategyParams",
    "DataExportParams",
    "DataImportParams",
    "ScheduledTaskParams",
    "WorkflowDefinitionParams",
    "AuditLogParams",
    "EventHandlerParams",
    "InboundIntegrationParams",
    "OutboundIntegrationParams",
    "MonitoringParams",
    "RateLimitingParams",
    "NotificationParams",
    "MessageQueueParams",
    "BatchJobParams",
    "DataRetentionParams",
    
    # Capability Validators
    "CAPABILITY_VALIDATORS",
    "validate_capability_params",
    "get_known_capability_types",
    
    # Core Capabilities Registry
    "CoreCapabilitiesRegistry",
    "AuthorizationCoreCapabilities",
    "DataOperationsCoreCapabilities",
    "TransactionCoreCapabilities",
    "EventIntegrationCoreCapabilities",
    "AuditObservabilityCoreCapabilities",
    
    # Blueprint Compiler
    "BlueprintCompiler",
    "BlueprintCompilerError",
    "CompiledBlueprint",
    "BlueprintMetadata",
    "IndustryInfo",
    "CorePacksConfig",
    "DomainPackRef",
    "RegulatoryOverlayRef",
    "BusinessInvariant",
    "ComplianceInvariant",
    "FailureModeInvariant",
    "InvariantsConfig",
    "BlueprintConfig",
    "BlueprintReferences",
]
