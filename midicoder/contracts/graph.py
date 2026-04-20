"""
Capability Graph Contract cho Midicoder v1.0.0

Module này định nghĩa Capability Graph - source of truth cho system capabilities.

Theo Rule 1 trong MIDICODER_STRATEGY.md:
- Capability Graph là source of truth duy nhất
- Không dùng prompt tự do hay contract do LLM author
- Có schema chặt, validator bắt buộc
- Explicit reads, writes, effects, obligations

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifact import ArtifactBase, ArtifactMetadata
from .capability_params import (
    AuthorizedMutationParams,
    AuthorizedQueryParams,
    AuditLogParams,
    BaseCapabilityParams,
    BatchJobParams,
    CacheStrategyParams,
    CapabilityParams,
    DataExportParams,
    DataImportParams,
    DataRetentionParams,
    EventHandlerParams,
    InboundIntegrationParams,
    MessageQueueParams,
    MonitoringParams,
    NotificationParams,
    OutboundIntegrationParams,
    RateLimitingParams,
    ScheduledTaskParams,
    WorkflowDefinitionParams,
)


# ============================================================================
# Obligation
# ============================================================================


@dataclass
class Obligation:
    """
    Obligation đại diện cho một yêu cầu bắt buộc phải được satisfy.
    
    Obligations là compile-time checks, không phải runtime checks.
    Verifier sẽ validate rằng mọi obligation đều được materialize.
    
    Attributes:
        id: Định danh duy nhất của obligation
        type: Loại obligation (permission_check, tenant_filter, transaction, etc.)
        description: Mô tả obligation
        source: Nguồn origin (capability ID yêu cầu obligation này)
        satisfied: Có được satisfy chưa (do verifier set)
        satisfaction_evidence: Evidence của satisfaction (file/line)
    
    Example:
        Obligation(
            id="perm_check_001",
            type="permission_check_required",
            description="Yêu cầu permission check cho order.create",
            source="capability:CreateOrder",
        )
    """
    id: str
    type: str
    description: str
    source: str
    satisfied: bool = False
    satisfaction_evidence: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "source": self.source,
            "satisfied": self.satisfied,
            "satisfaction_evidence": self.satisfaction_evidence,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Obligation":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            description=data.get("description", ""),
            source=data.get("source", ""),
            satisfied=data.get("satisfied", False),
            satisfaction_evidence=data.get("satisfaction_evidence"),
        )


# ============================================================================
# Capability Instance
# ============================================================================


@dataclass
class CapabilityInstance:
    """
    Capability Instance đại diện cho một instance của capability trong hệ thống.
    
    Theo Rule 2: Core capability language phải nhỏ, đóng, có semantics chặt.
    Mỗi instance có:
    - Type (macro hoặc core capability)
    - Params (typed parameters)
    - Obligations (các yêu cầu phải satisfy)
    - Confidence (độ tin cậy từ LLM proposal)
    
    Attributes:
        id: Định danh duy nhất của instance
        type: Loại capability (authorized_mutation, query, event_handler, etc.)
        description: Mô tả capability
        confidence: Confidence score (0.0-1.0) từ LLM proposal
        params: Typed parameters cho capability (sử dụng CapabilityParams union)
        reads: Danh sách entities/resources cần read
        writes: Danh sách entities/resources sẽ write
        emits: Danh sách events sẽ emit
        obligations: Danh sách obligations phải satisfy
        tags: Danh sách tags
        
    Typed Params Support:
        - authorized_mutation: AuthorizedMutationParams
        - authorized_query: AuthorizedQueryParams
        - event_handler: EventHandlerParams
        - scheduled_task: ScheduledTaskParams
        - workflow_definition: WorkflowDefinitionParams
        - See capability_params.py for full list
        
    Example:
        CapabilityInstance(
            id="create_order",
            type="authorized_mutation",
            confidence=0.95,
            params={
                "actor_role": "staff",
                "permission": "order.create",
                "writes": ["Order", "OrderItem"],
                "transaction": "required",
                "tenant_scope": "tenant_isolated",
            },
            obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
            ],
        )
    """
    id: str
    type: str
    description: str | None = None
    confidence: float = 1.0
    params: CapabilityParams = field(default_factory=dict)  # type: ignore
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    emits: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "confidence": self.confidence,
            "params": self.params,
            "reads": self.reads,
            "writes": self.writes,
            "emits": self.emits,
            "obligations": self.obligations,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityInstance":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            description=data.get("description"),
            confidence=data.get("confidence", 1.0),
            params=data.get("params", {}),
            reads=data.get("reads", []),
            writes=data.get("writes", []),
            emits=data.get("emits", []),
            obligations=data.get("obligations", []),
            tags=data.get("tags", []),
        )
    
    def add_obligation(self, obligation_id: str) -> None:
        """Thêm obligation nếu chưa tồn tại."""
        if obligation_id not in self.obligations:
            self.obligations.append(obligation_id)
    
    def is_high_confidence(self) -> bool:
        """Kiểm tra confidence có cao không (> 0.8)."""
        return self.confidence >= 0.8


# ============================================================================
# Macro Capability
# ============================================================================


@dataclass
class MacroCapability:
    """
    Macro Capability định nghĩa một capability level cao.
    
    Macro capabilities expand thành core capabilities.
    Theo Rule 2: Macro chỉ là "sugar", phải expand về instruction set lõi.
    
    Attributes:
        id: Định danh macro
        name: Tên hiển thị
        description: Mô tả macro
        expands_to: Danh sách core capability IDs
        params_schema: Schema cho params
        default_obligations: Obligations mặc định cho instances
        
    Example:
        MacroCapability(
            id="authorized_mutation",
            name="Authorized Mutation",
            description="Mutation với permission check, tenant scope, và transaction",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
            ],
        )
    """
    id: str
    name: str
    description: str | None = None
    expands_to: list[str] = field(default_factory=list)
    params_schema: dict[str, Any] = field(default_factory=dict)
    default_obligations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "expands_to": self.expands_to,
            "params_schema": self.params_schema,
            "default_obligations": self.default_obligations,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroCapability":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            expands_to=data.get("expands_to", []),
            params_schema=data.get("params_schema", {}),
            default_obligations=data.get("default_obligations", []),
        )


# ============================================================================
# Core Capability
# ============================================================================


@dataclass
class CoreCapability:
    """
    Core Capability định nghĩa một primitive instruction.
    
    Theo Rule 2: Core capability language phải nhỏ, đóng, có semantics chặt.
    Core capabilities là instruction set hữu hạn mà mọi macro expand về.
    
    Attributes:
        id: Định danh core capability
        name: Tên hiển thị
        description: Mô tả capability
        params_schema: Schema cho params
        default_obligations: Obligations mặc định
        read_access: Danh sách resources cần read
        write_access: Danh sách resources có thể write
        effects: Danh sách side effects
        
    Example:
        CoreCapability(
            id="authorize_permission",
            name="Authorize Permission",
            description="Check user có permission không",
            params_schema={
                "permission": {"type": "string", "required": True},
            },
        )
    """
    id: str
    name: str
    description: str | None = None
    params_schema: dict[str, Any] = field(default_factory=dict)
    default_obligations: list[str] = field(default_factory=list)
    read_access: list[str] = field(default_factory=list)
    write_access: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "params_schema": self.params_schema,
            "default_obligations": self.default_obligations,
            "read_access": self.read_access,
            "write_access": self.write_access,
            "effects": self.effects,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoreCapability":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            params_schema=data.get("params_schema", {}),
            default_obligations=data.get("default_obligations", []),
            read_access=data.get("read_access", []),
            write_access=data.get("write_access", []),
            effects=data.get("effects", []),
        )


# ============================================================================
# Capability Graph
# ============================================================================


@dataclass
class CapabilityGraph(ArtifactBase):
    """
    Capability Graph - Source of Truth cho system capabilities.
    
    Theo Rule 1: Capability Graph là source of truth duy nhất.
    
    Graph chứa:
    - Core capabilities: Instruction set lõi
    - Macro capabilities: High-level patterns
    - Instances: Capability instances trong hệ thống
    - Obligations: Tất cả obligations cần satisfy
    
    Attributes:
        core_capabilities: Danh sách core capabilities
        macro_capabilities: Danh sách macro capabilities
        instances: Danh sách capability instances
        obligations: Danh sách tất cả obligations
        metadata: Artifact metadata
        
    Example:
        graph = CapabilityGraph(
            core_capabilities=[
                CoreCapability(id="authorize_permission", ...),
            ],
            macro_capabilities=[
                MacroCapability(id="authorized_mutation", ...),
            ],
            instances=[
                CapabilityInstance(id="create_order", ...),
            ],
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    core_capabilities: list[CoreCapability] = field(default_factory=list)
    macro_capabilities: list[MacroCapability] = field(default_factory=list)
    instances: list[CapabilityInstance] = field(default_factory=list)
    obligations: list[Obligation] = field(default_factory=list)
    
    # Cache mappings
    _core_by_id: dict[str, CoreCapability] = field(default_factory=dict, repr=False)
    _macro_by_id: dict[str, MacroCapability] = field(default_factory=dict, repr=False)
    _instance_by_id: dict[str, CapabilityInstance] = field(default_factory=dict, repr=False)
    _obligation_by_id: dict[str, Obligation] = field(default_factory=dict, repr=False)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "capability_graph"
    
    def __post_init__(self) -> None:
        """Build cache mappings."""
        self._build_cache()
    
    def _build_cache(self) -> None:
        """Build cache mappings cho fast lookups."""
        self._core_by_id = {c.id: c for c in self.core_capabilities}
        self._macro_by_id = {m.id: m for m in self.macro_capabilities}
        self._instance_by_id = {i.id: i for i in self.instances}
        self._obligation_by_id = {o.id: o for o in self.obligations}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "core_capabilities": [c.to_dict() for c in self.core_capabilities],
            "macro_capabilities": [m.to_dict() for m in self.macro_capabilities],
            "instances": [i.to_dict() for i in self.instances],
            "obligations": [o.to_dict() for o in self.obligations],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityGraph":
        """Tạo CapabilityGraph từ dictionary."""
        # Tạo instance với các fields cơ bản (metadata được set sau do init=False)
        graph = cls(
            core_capabilities=[
                CoreCapability.from_dict(c)
                for c in data.get("core_capabilities", [])
            ],
            macro_capabilities=[
                MacroCapability.from_dict(m)
                for m in data.get("macro_capabilities", [])
            ],
            instances=[
                CapabilityInstance.from_dict(i)
                for i in data.get("instances", [])
            ],
            obligations=[
                Obligation.from_dict(o)
                for o in data.get("obligations", [])
            ],
        )
        # Set metadata sau khi tạo instance (do init=False)
        object.__setattr__(graph, 'metadata', ArtifactMetadata.from_dict(data.get("metadata", {})))
        return graph
    
    # =========================================================================
    # Instance Management
    # =========================================================================
    
    def add_instance(self, instance: CapabilityInstance) -> None:
        """
        Thêm capability instance vào graph.
        
        Args:
            instance: Instance để thêm
        """
        self.instances.append(instance)
        self._instance_by_id[instance.id] = instance
    
    def get_instance(self, instance_id: str) -> CapabilityInstance | None:
        """Lấy instance theo ID."""
        return self._instance_by_id.get(instance_id)
    
    def get_instances_by_type(self, capability_type: str) -> list[CapabilityInstance]:
        """Lấy instances theo capability type."""
        return [i for i in self.instances if i.type == capability_type]
    
    # =========================================================================
    # Macro/Core Lookup
    # =========================================================================
    
    def get_macro(self, macro_id: str) -> MacroCapability | None:
        """Lấy macro capability theo ID."""
        return self._macro_by_id.get(macro_id)
    
    def get_core(self, core_id: str) -> CoreCapability | None:
        """Lấy core capability theo ID."""
        return self._core_by_id.get(core_id)
    
    # =========================================================================
    # Obligation Management
    # =========================================================================
    
    def add_obligation(self, obligation: Obligation) -> None:
        """Thêm obligation vào graph."""
        self.obligations.append(obligation)
        self._obligation_by_id[obligation.id] = obligation
    
    def get_obligation(self, obligation_id: str) -> Obligation | None:
        """Lấy obligation theo ID."""
        return self._obligation_by_id.get(obligation_id)
    
    def get_unsatisfied_obligations(self) -> list[Obligation]:
        """Lấy danh sách obligations chưa được satisfy."""
        return [o for o in self.obligations if not o.satisfied]
    
    def mark_obligation_satisfied(self, obligation_id: str, evidence: str) -> bool:
        """
        Đánh dấu obligation đã được satisfy.
        
        Args:
            obligation_id: ID của obligation
            evidence: Evidence của satisfaction
            
        Returns:
            True nếu thành công, False nếu không tìm thấy
        """
        obligation = self._obligation_by_id.get(obligation_id)
        if obligation:
            obligation.satisfied = True
            obligation.satisfaction_evidence = evidence
            return True
        return False
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate capability graph.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check instance IDs are unique
        seen_ids: set[str] = set()
        for instance in self.instances:
            if instance.id in seen_ids:
                errors.append(f"Duplicate instance ID: {instance.id}")
            seen_ids.add(instance.id)
        
        # Check instance types reference valid macros/cores
        all_capability_ids = set(self._macro_by_id.keys()) | set(self._core_by_id.keys())
        for instance in self.instances:
            if instance.type not in all_capability_ids:
                errors.append(
                    f"Instance '{instance.id}' references unknown capability type: "
                    f"{instance.type}"
                )
        
        # Check obligations reference valid sources
        for obligation in self.obligations:
            if obligation.source.startswith("capability:"):
                ref_id = obligation.source.split(":", 1)[1]
                if ref_id not in self._instance_by_id:
                    errors.append(
                        f"Obligation '{obligation.id}' references unknown capability: "
                        f"{ref_id}"
                    )
        
        return errors
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Lấy thống kê cho graph.
        
        Returns:
            Dictionary với statistics
        """
        return {
            "total_instances": len(self.instances),
            "total_core_capabilities": len(self.core_capabilities),
            "total_macro_capabilities": len(self.macro_capabilities),
            "total_obligations": len(self.obligations),
            "satisfied_obligations": sum(
                1 for o in self.obligations if o.satisfied
            ),
            "unsatisfied_obligations": sum(
                1 for o in self.obligations if not o.satisfied
            ),
            "instance_types": {
                t: sum(1 for i in self.instances if i.type == t)
                for t in set(i.type for i in self.instances)
            },
        }