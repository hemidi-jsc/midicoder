"""
MIR (Midicoder Intermediate Representation) Contract cho v1.0.0

Module này định nghĩa MIR - Implementation Truth typed cho code generation.

Theo Rule 4 trong MIDICODER_STRATEGY.md:
- MIR là implementation truth, không phải pseudo text
- MIR phải chứa: ops, data flow, effect flow, transaction boundaries
- MIR target-agnostic, file-agnostic, patch-agnostic
- MIR là input bắt buộc cho emitter

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifact import ArtifactBase, ArtifactMetadata


# ============================================================================
# MIR Operation
# ============================================================================


@dataclass
class MIROperation:
    """
    MIR Operation đại diện cho một primitive operation.
    
    Theo Rule 2: Core capability language nhỏ, đóng, có semantics chặt.
    Mỗi operation map về một core capability instruction.
    
    Attributes:
        op: Operation name (authorize_permission, create_record, etc.)
        params: Typed parameters cho operation
        input_refs: References vào data flow inputs
        output_refs: References vào data flow outputs
        effect_refs: References vào effect outputs
        transaction_boundary: Transaction boundary cho operation
        obligation_refs: Obligations phải satisfy
        
    Example:
        MIROperation(
            op="authorize_permission",
            params={"permission": "order.create"},
            obligation_refs=["perm_check_001"],
        )
    """
    op: str
    params: dict[str, Any] = field(default_factory=dict)
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    effect_refs: list[str] = field(default_factory=list)
    transaction_boundary: str | None = None
    obligation_refs: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "op": self.op,
            "params": self.params,
            "input_refs": self.input_refs,
            "output_refs": self.output_refs,
            "effect_refs": self.effect_refs,
            "transaction_boundary": self.transaction_boundary,
            "obligation_refs": self.obligation_refs,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIROperation":
        """Create from dictionary."""
        return cls(
            op=data["op"],
            params=data.get("params", {}),
            input_refs=data.get("input_refs", []),
            output_refs=data.get("output_refs", []),
            effect_refs=data.get("effect_refs", []),
            transaction_boundary=data.get("transaction_boundary"),
            obligation_refs=data.get("obligation_refs", []),
        )


# ============================================================================
# MIR Data Flow
# ============================================================================


@dataclass
class MIRDataFlow:
    """
    MIR Data Flow định nghĩa data flow giữa operations.
    
    Theo Rule 4: MIR phải capture data flow explicit.
    
    Attributes:
        id: Định danh data flow
        source_op: Operation source
        source_field: Field name từ source
        target_op: Operation target
        target_field: Field name ở target
        transformation: Transformation function (nếu có)
        
    Example:
        MIRDataFlow(
            id="flow_001",
            source_op="authorize_permission",
            source_field="principal.user_id",
            target_op="create_record",
            target_field="created_by",
        )
    """
    id: str
    source_op: str
    source_field: str
    target_op: str
    target_field: str
    transformation: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_op": self.source_op,
            "source_field": self.source_field,
            "target_op": self.target_op,
            "target_field": self.target_field,
            "transformation": self.transformation,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIRDataFlow":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source_op=data["source_op"],
            source_field=data["source_field"],
            target_op=data["target_op"],
            target_field=data["target_field"],
            transformation=data.get("transformation"),
        )


# ============================================================================
# MIR Effect Flow
# ============================================================================


@dataclass
class MIREffectFlow:
    """
    MIR Effect Flow định nghĩa effect flow (events, side effects).
    
    Theo Rule 4: MIR phải capture effect flow explicit.
    
    Attributes:
        id: Định danh effect
        source_op: Operation phát sinh effect
        effect_type: Loại effect (event_publish, notification, etc.)
        target: Target của effect
        payload_fields: Payload fields cho effect
        async_: Có execute async không
        retry_policy: Retry policy (nếu có)
        
    Example:
        MIREffectFlow(
            id="effect_001",
            source_op="create_record",
            effect_type="event_publish",
            target="OrderCreated",
            payload_fields=["order_id", "customer_id", "total"],
        )
    """
    id: str
    source_op: str
    effect_type: str
    target: str
    payload_fields: list[str] = field(default_factory=list)
    async_: bool = False
    retry_policy: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_op": self.source_op,
            "effect_type": self.effect_type,
            "target": self.target,
            "payload_fields": self.payload_fields,
            "async": self.async_,
            "retry_policy": self.retry_policy,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIREffectFlow":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source_op=data["source_op"],
            effect_type=data["effect_type"],
            target=data["target"],
            payload_fields=data.get("payload_fields", []),
            async_=data.get("async", False),
            retry_policy=data.get("retry_policy"),
        )


# ============================================================================
# MIR Boundary
# ============================================================================


@dataclass
class MIRBoundary:
    """
    MIR Boundary định nghĩa boundaries (transaction, auth, tenant).
    
    Theo Rule 4: MIR phải capture transaction boundaries, auth boundaries.
    
    Attributes:
        id: Định danh boundary
        boundary_type: Loại boundary (transaction, auth, tenant, etc.)
        enclosing_ops: Danh sách operations trong boundary
        config: Configuration cho boundary
        scope: Scope của boundary
        
    Example:
        MIRBoundary(
            id="txn_001",
            boundary_type="transaction",
            enclosing_ops=["create_order", "create_items"],
            config={"isolation": "read_committed"},
        )
    """
    id: str
    boundary_type: str
    enclosing_ops: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    scope: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "boundary_type": self.boundary_type,
            "enclosing_ops": self.enclosing_ops,
            "config": self.config,
            "scope": self.scope,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIRBoundary":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            boundary_type=data["boundary_type"],
            enclosing_ops=data.get("enclosing_ops", []),
            config=data.get("config", {}),
            scope=data.get("scope"),
        )


# ============================================================================
# MIR (Intermediate Representation)
# ============================================================================


@dataclass
class MIR(ArtifactBase):
    """
    MIR (Midicoder Intermediate Representation) - Implementation Truth.
    
    Theo Rule 4: MIR là implementation truth, không phải pseudo text.
    MIR phải typed, có thể verify, target-agnostic.
    
    Attributes:
        ir_ref: Reference vào source (capability/command ID)
        description: Mô tả MIR
        ops: Danh sách operations
        data_flows: Danh sách data flows
        effect_flows: Danh sách effect flows
        boundaries: Danh sách boundaries
        response_shape: Response shaping specification
        metadata: Artifact metadata
        
    Example:
        mir = MIR(
            ir_ref="Command.CreateOrder",
            ops=[
                MIROperation(op="authorize_permission", ...),
                MIROperation(op="enforce_tenant_scope", ...),
                MIROperation(op="begin_transaction", ...),
                MIROperation(op="create_record", ...),
            ],
            data_flows=[...],
            effect_flows=[...],
            boundaries=[...],
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    # Required field (must come before fields with defaults when inheriting)
    ir_ref: str = ""
    description: str | None = None
    ops: list[MIROperation] = field(default_factory=list)
    data_flows: list[MIRDataFlow] = field(default_factory=list)
    effect_flows: list[MIREffectFlow] = field(default_factory=list)
    boundaries: list[MIRBoundary] = field(default_factory=list)
    response_shape: dict[str, Any] | None = None
    # metadata inherited from ArtifactBase
    
    # Cache mappings
    _ops_by_index: dict[int, MIROperation] = field(default_factory=dict, repr=False)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "mir"
    
    def __post_init__(self) -> None:
        """Build cache mappings."""
        self._build_cache()
    
    def _build_cache(self) -> None:
        """Build cache mappings cho fast lookups."""
        self._ops_by_index = {i: op for i, op in enumerate(self.ops)}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "ir_ref": self.ir_ref,
            "description": self.description,
            "ops": [op.to_dict() for op in self.ops],
            "data_flows": [df.to_dict() for df in self.data_flows],
            "effect_flows": [ef.to_dict() for ef in self.effect_flows],
            "boundaries": [b.to_dict() for b in self.boundaries],
            "response_shape": self.response_shape,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIR":
        """Tạo MIR từ dictionary."""
        # Tạo instance với các fields cơ bản (metadata được set sau do init=False)
        mir = cls(
            ir_ref=data.get("ir_ref", ""),
            description=data.get("description"),
            ops=[MIROperation.from_dict(op) for op in data.get("ops", [])],
            data_flows=[MIRDataFlow.from_dict(df) for df in data.get("data_flows", [])],
            effect_flows=[MIREffectFlow.from_dict(ef) for ef in data.get("effect_flows", [])],
            boundaries=[MIRBoundary.from_dict(b) for b in data.get("boundaries", [])],
            response_shape=data.get("response_shape"),
        )
        # Set metadata sau khi tạo instance (do init=False)
        object.__setattr__(mir, 'metadata', ArtifactMetadata.from_dict(data.get("metadata", {})))
        return mir
    
    # =========================================================================
    # Operation Management
    # =========================================================================
    
    def add_operation(self, op: MIROperation) -> int:
        """
        Thêm operation vào MIR.
        
        Args:
            op: Operation để thêm
            
        Returns:
            Index của operation trong list
        """
        index = len(self.ops)
        self.ops.append(op)
        self._ops_by_index[index] = op
        return index
    
    def get_operation(self, index: int) -> MIROperation | None:
        """Lấy operation theo index."""
        return self._ops_by_index.get(index)
    
    def get_operations_by_type(self, op_type: str) -> list[MIROperation]:
        """Lấy operations theo operation type."""
        return [op for op in self.ops if op.op == op_type]
    
    # =========================================================================
    # Flow Management
    # =========================================================================
    
    def add_data_flow(self, flow: MIRDataFlow) -> None:
        """Thêm data flow vào MIR."""
        self.data_flows.append(flow)
    
    def add_effect_flow(self, flow: MIREffectFlow) -> None:
        """Thêm effect flow vào MIR."""
        self.effect_flows.append(flow)
    
    # =========================================================================
    # Boundary Management
    # =========================================================================
    
    def add_boundary(self, boundary: MIRBoundary) -> None:
        """Thêm boundary vào MIR."""
        self.boundaries.append(boundary)
    
    def get_boundaries_by_type(self, boundary_type: str) -> list[MIRBoundary]:
        """Lấy boundaries theo type."""
        return [b for b in self.boundaries if b.boundary_type == boundary_type]
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate MIR.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check ir_ref is set
        if not self.ir_ref:
            errors.append("MIR.ir_ref is required")
        
        # Check operations are not empty
        if not self.ops:
            errors.append("MIR must have at least one operation")
        
        # Check data flow references are valid
        op_indices = set(self._ops_by_index.keys())
        for flow in self.data_flows:
            if flow.source_op not in op_indices:
                errors.append(
                    f"DataFlow '{flow.id}' references unknown source op: "
                    f"{flow.source_op}"
                )
            if flow.target_op not in op_indices:
                errors.append(
                    f"DataFlow '{flow.id}' references unknown target op: "
                    f"{flow.target_op}"
                )
        
        # Check effect flow references are valid
        for flow in self.effect_flows:
            if flow.source_op not in op_indices:
                errors.append(
                    f"EffectFlow '{flow.id}' references unknown source op: "
                    f"{flow.source_op}"
                )
        
        return errors
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Lấy thống kê cho MIR.
        
        Returns:
            Dictionary với statistics
        """
        return {
            "total_operations": len(self.ops),
            "total_data_flows": len(self.data_flows),
            "total_effect_flows": len(self.effect_flows),
            "total_boundaries": len(self.boundaries),
            "operation_types": {
                op.op: sum(1 for o in self.ops if o.op == op.op)
                for op in self.ops
            },
            "boundary_types": {
                b.boundary_type: sum(1 for x in self.boundaries if x.boundary_type == b.boundary_type)
                for b in self.boundaries
            },
        }