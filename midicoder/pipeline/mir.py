"""
MIR (Midicoder Intermediate Representation) Module.

MIR là typed IR đại diện cho implementation truth trong Midicoder pipeline.
Đây KHÔNG phải pseudo-code text, mà là structured data với:
- Operations (core capability instructions)
- Data Flows (explicit data movement)
- Effect Flows (events, side effects)
- Boundaries (transaction, auth, tenant)

Theo SoT E05, MIR được build từ Capability Graph (DSL kernel ProjectionTree)
và lưu vào SQLite artifacts table.

Ví dụ sử dụng:
    # Tạo MIR với operations
    mir = MIR()
    mir.operations.append(Operation(
        op_id="auth_001",
        op_type="authorize_permission",
        params={"permission": "order.create"},
        obligation_refs=["perm_oblig_001"]
    ))

    # Serialize to JSON
    json_str = mir.to_json()

    # Save to SQLite
    artifacts_manager.create(
        artifact_id="mir-v1.0.0",
        artifact_type="mir",
        content=json_str
    )

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================================
# Operation - Core Capability Instruction
# ============================================================================


@dataclass
class Operation:
    """
    Operation - Core Capability Instruction.

    Operation đại diện cho một core capability instruction đã được expand
    từ macro capabilities. Đây là atomic operation trong MIR.

    Theo SoT E05, mỗi operation có:
    - op_id: Unique identifier
    - op_type: Loại operation (authorize_permission, create_record, etc.)
    - params: Tham số của operation
    - obligation_refs: References đến obligations cần satisfy
    - input_refs: Input data references từ operations khác
    - output_refs: Output data references cho operations khác

    Attributes:
        op_id: Định danh duy nhất của operation
        op_type: Loại operation (core capability type)
        params: Tham số của operation
        obligation_refs: Danh sách obligation references
        input_refs: Danh sách input data references
        output_refs: Danh sách output data references
        metadata: Metadata bổ sung

    Ví dụ:
        op = Operation(
            op_id="create_order_001",
            op_type="create_record",
            params={"entity": "Order", "fields": ["order_id", "tenant_id"]},
            obligation_refs=["tenant_oblig_001", "perm_oblig_001"],
            input_refs=["tenant_id", "order_data"],
            output_refs=["order_entity"]
        )
    """

    op_id: str
    op_type: str
    params: dict[str, Any]
    obligation_refs: list[str] = field(default_factory=list)
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Backward-compatibility alias (contracts/mir used "op" instead of "op_type")
    @property
    def op(self) -> str:
        """Alias for op_type (compatibility with contracts/mir API)."""
        return self.op_type

    @op.setter
    def op(self, value: str) -> None:
        self.op_type = value

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Operation sang dictionary.

        Returns:
            Dictionary representation (legacy + canonical keys)
        """
        return {
            "op_id": self.op_id,
            "op": self.op_type,  # Legacy key
            "op_type": self.op_type,
            "params": self.params,
            "obligation_refs": self.obligation_refs,
            "input_refs": self.input_refs,
            "output_refs": self.output_refs,
            "effect_refs": [],  # Legacy field on MIR level
            "transaction_boundary": self.metadata.get("transaction_boundary"),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Operation":
        """
        Tạo Operation từ dictionary.

        Args:
            data: Dictionary chứa operation data (supports legacy "op" key)

        Returns:
            Operation instance
        """
        op_type = data.get("op_type", data.get("op", ""))
        op_id = data.get("op_id", op_type)
        return cls(
            op_id=op_id,
            op_type=op_type,
            params=data.get("params", {}),
            obligation_refs=data.get("obligation_refs", []),
            input_refs=data.get("input_refs", []),
            output_refs=data.get("output_refs", []),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# DataFlow - Explicit Data Movement
# ============================================================================


@dataclass
class DataFlow:
    """
    Data Flow - Explicit data movement between operations.

    DataFlow mô tả cách dữ liệu di chuyển giữa các operations trong MIR.
    Đây là explicit data movement, không phải implicit dependencies.

    Theo SoT E05, mỗi data flow có:
    - source_op: Source operation ID
    - source_field: Field name trong source
    - target_op: Target operation ID
    - target_field: Field name trong target
    - transformation: Optional transformation (uppercase, concat, etc.)

    Attributes:
        source_op: Operation ID nguồn
        source_field: Field name nguồn
        target_op: Operation ID đích
        target_field: Field name đích
        transformation: Transformation function (optional)
        metadata: Metadata bổ sung

    Ví dụ:
        df = DataFlow(
            source_op="auth_001",
            source_field="user_id",
            target_op="create_order_001",
            target_field="created_by"
        )
    """

    source_op: str
    source_field: str
    target_op: str
    target_field: str
    transformation: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Backward-compat with contracts/mir API
    id: Optional[str] = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển DataFlow sang dictionary.

        Returns:
            Dictionary representation của DataFlow
        """
        d: dict[str, Any] = {
            "source_op": self.source_op,
            "source_field": self.source_field,
            "target_op": self.target_op,
            "target_field": self.target_field,
            "transformation": self.transformation,
            "metadata": self.metadata,
        }
        if self.id is not None:
            d["id"] = self.id
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataFlow":
        """
        Tạo DataFlow từ dictionary.

        Args:
            data: Dictionary chứa data flow data

        Returns:
            DataFlow instance
        """
        return cls(
            id=data.get("id"),
            source_op=data["source_op"],
            source_field=data["source_field"],
            target_op=data["target_op"],
            target_field=data["target_field"],
            transformation=data.get("transformation"),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# EffectFlow - Events and Side Effects
# ============================================================================


@dataclass
class EffectFlow:
    """
    Effect Flow - Events and side effects.

    EffectFlow mô tả các side effects xảy ra sau khi operations complete.
    Bao gồm event publishing, log writing, metric recording, notifications.

    Theo SoT E05, mỗi effect flow có:
    - source_op: Source operation ID
    - effect_type: Loại effect (event_publish, log_write, metric_record)
    - target: Target (event name, log type, metric name)
    - payload_fields: Danh sách fields trong payload

    Attributes:
        source_op: Operation ID nguồn
        effect_type: Loại effect
        target: Target của effect
        payload_fields: Danh sách payload fields
        metadata: Metadata bổ sung

    Ví dụ:
        ef = EffectFlow(
            source_op="create_order_001",
            effect_type="event_publish",
            target="OrderCreated",
            payload_fields=["order_id", "tenant_id", "total"]
        )
    """

    source_op: str
    effect_type: str
    target: str
    payload_fields: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Backward-compat with contracts/mir API
    id: Optional[str] = field(default=None, repr=False)
    async_: bool = field(default=False, repr=False)
    retry_policy: Optional[dict[str, Any]] = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển EffectFlow sang dictionary.

        Returns:
            Dictionary representation của EffectFlow
        """
        d: dict[str, Any] = {
            "source_op": self.source_op,
            "effect_type": self.effect_type,
            "target": self.target,
            "payload_fields": self.payload_fields,
            "metadata": self.metadata,
        }
        if self.id is not None:
            d["id"] = self.id
        if self.async_:
            d["async"] = self.async_
        if self.retry_policy is not None:
            d["retry_policy"] = self.retry_policy
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EffectFlow":
        """
        Tạo EffectFlow từ dictionary.

        Args:
            data: Dictionary chứa effect flow data

        Returns:
            EffectFlow instance
        """
        return cls(
            id=data.get("id"),
            source_op=data["source_op"],
            effect_type=data["effect_type"],
            target=data["target"],
            payload_fields=data.get("payload_fields", []),
            async_=data.get("async", False),
            retry_policy=data.get("retry_policy"),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# Boundary - Transaction, Auth, Tenant Boundaries
# ============================================================================


@dataclass
class Boundary:
    """
    Boundary - Transaction, Auth, Tenant boundaries.

    Boundary mô tả các transaction, authorization, và tenant scopes
    trong MIR. Đây là important metadata cho code generation.

    Theo SoT E05, mỗi boundary có:
    - boundary_id: Unique identifier
    - boundary_type: Loại boundary (transaction, auth, tenant)
    - enclosing_ops: Danh sách operation IDs được bao bởi boundary
    - config: Configuration cho boundary

    Attributes:
        boundary_id: Định danh duy nhất của boundary
        boundary_type: Loại boundary
        enclosing_ops: Danh sách enclosed operations
        config: Configuration cho boundary
        metadata: Metadata bổ sung

    Ví dụ:
        b = Boundary(
            boundary_id="txn_001",
            boundary_type="transaction",
            enclosing_ops=["create_order_001", "create_items_001"],
            config={"isolation_level": "read_committed"}
        )
    """

    boundary_id: str
    boundary_type: str
    enclosing_ops: list[str]
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Backward-compat with contracts/mir API
    scope: Optional[str] = field(default=None, repr=False)

    @property
    def id(self) -> str:
        """Alias for boundary_id (compatibility with contracts/mir API)."""
        return self.boundary_id

    @id.setter
    def id(self, value: str) -> None:
        self.boundary_id = value

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Boundary sang dictionary.

        Returns:
            Dictionary representation của Boundary (legacy + canonical keys)
        """
        d: dict[str, Any] = {
            "id": self.boundary_id,
            "boundary_type": self.boundary_type,
            "enclosing_ops": self.enclosing_ops,
            "config": self.config,
            "metadata": self.metadata,
        }
        if self.scope is not None:
            d["scope"] = self.scope
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Boundary":
        """
        Tạo Boundary từ dictionary.

        Args:
            data: Dictionary chứa boundary data (supports legacy "id" key)

        Returns:
            Boundary instance
        """
        return cls(
            boundary_id=data.get("id", data.get("boundary_id", "")),
            boundary_type=data["boundary_type"],
            enclosing_ops=data.get("enclosing_ops", []),
            config=data.get("config", {}),
            scope=data.get("scope"),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# MIR - Midicoder Intermediate Representation
# ============================================================================


@dataclass
class MIR:
    """
    Midicoder Intermediate Representation (MIR).

    MIR là typed IR đại diện cho implementation truth. Đây là central data
    structure trong Midicoder pipeline, được build từ Capability Graph (DSL)
    và sử dụng bởi emitters cho code generation.

    Theo SoT E05, MIR bao gồm:
    - Operations (core capability instructions)
    - Data Flows (explicit data movement)
    - Effect Flows (events, side effects)
    - Boundaries (transaction, auth, tenant)
    - Metadata (version, source, etc.)

    Attributes:
        operations: Danh sách operations (core capability instructions)
        data_flows: Danh sách data flows (explicit data movement)
        effect_flows: Danh sách effect flows (events, side effects)
        boundaries: Danh sách boundaries (transaction, auth, tenant)
        metadata: Metadata (version, source, etc.)

    Ví dụ:
        mir = MIR()
        mir.operations.append(Operation(...))
        mir.data_flows.append(DataFlow(...))
        json_str = mir.to_json()
    """

    operations: list[Operation] = field(default_factory=list)
    data_flows: list[DataFlow] = field(default_factory=list)
    effect_flows: list[EffectFlow] = field(default_factory=list)
    boundaries: list[Boundary] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Backward-compat for contracts/mir API (legacy tests)
    _ops_by_index: dict[int, Operation] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Build legacy index cache."""
        self._ops_by_index = {i: op for i, op in enumerate(self.operations)}

    @property
    def ir_ref(self) -> str:
        """Legacy alias for metadata['ir_ref']."""
        return self.metadata.get("ir_ref", "")

    @ir_ref.setter
    def ir_ref(self, value: str) -> None:
        self.metadata["ir_ref"] = value

    @property
    def description(self) -> str | None:
        """Legacy alias for metadata['description']."""
        return self.metadata.get("description")

    @description.setter
    def description(self, value: str | None) -> None:
        if value is not None:
            self.metadata["description"] = value
        else:
            self.metadata.pop("description", None)

    @property
    def ops(self) -> list[Operation]:
        """Legacy alias — same list as ``operations``."""
        return self.operations

    @property
    def effect_refs(self) -> list[str]:
        """Legacy: unused on MIR level (was on MIROperation)."""
        return []

    def get_operation(self, index: int) -> Operation | None:
        """Legacy: get operation by numeric index."""
        return self._ops_by_index.get(index)

    def add_operation_compat(self, op: Operation) -> int:
        """Legacy: add an Operation object (not builder-style kwargs)."""
        index = len(self.operations)
        self.operations.append(op)
        self._ops_by_index[index] = op
        return index

    def add_operation(self, op: Operation) -> None:
        """
        Thêm operation vào MIR.

        Args:
            op: Operation để thêm
        """
        self.operations.append(op)

    def add_data_flow(self, df: DataFlow) -> None:
        """
        Thêm data flow vào MIR.

        Args:
            df: DataFlow để thêm
        """
        self.data_flows.append(df)

    def add_effect_flow(self, ef: EffectFlow) -> None:
        """
        Thêm effect flow vào MIR.

        Args:
            ef: EffectFlow để thêm
        """
        self.effect_flows.append(ef)

    def add_boundary(self, b: Boundary) -> None:
        """
        Thêm boundary vào MIR.

        Args:
            b: Boundary để thêm
        """
        self.boundaries.append(b)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển MIR sang dictionary.

        Returns:
            Dictionary representation của MIR
        """
        return {
            "version": self.metadata.get("version", "1.0.0"),
            "operations": [op.to_dict() for op in self.operations],
            "data_flows": [df.to_dict() for df in self.data_flows],
            "effect_flows": [ef.to_dict() for ef in self.effect_flows],
            "boundaries": [b.to_dict() for b in self.boundaries],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize MIR sang JSON string.

        Args:
            indent: Số khoảng trắng cho indentation

        Returns:
            JSON string representation của MIR
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MIR":
        """
        Tạo MIR từ dictionary.

        Args:
            data: Dictionary chứa MIR data

        Returns:
            MIR instance
        """
        mir = cls(metadata=data.get("metadata", {}))

        for op_data in data.get("operations", []):
            mir.operations.append(Operation.from_dict(op_data))

        for df_data in data.get("data_flows", []):
            mir.data_flows.append(DataFlow.from_dict(df_data))

        for ef_data in data.get("effect_flows", []):
            mir.effect_flows.append(EffectFlow.from_dict(ef_data))

        for b_data in data.get("boundaries", []):
            mir.boundaries.append(Boundary.from_dict(b_data))

        return mir

    @classmethod
    def from_json(cls, json_str: str) -> "MIR":
        """
        Tạo MIR từ JSON string.

        Args:
            json_str: JSON string chứa MIR data

        Returns:
            MIR instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Tính hash deterministic cho MIR.

        Dùng cho verification và caching. Cùng input → Cùng hash.

        Returns:
            SHA256 hash string của MIR
        """
        # Normalize JSON cho determinism (sorted keys)
        normalized = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_operations_by_type(self, op_type: str) -> list[Operation]:
        """
        Lọc operations theo type.

        Args:
            op_type: Loại operation để lọc

        Returns:
            Danh sách operations matching type
        """
        return [op for op in self.operations if op.op_type == op_type]

    def get_operations_with_obligation(self, obligation_ref: str) -> list[Operation]:
        """
        Tìm operations có obligation reference.

        Args:
            obligation_ref: Obligation reference ID

        Returns:
            Danh sách operations có obligation reference
        """
        return [
            op for op in self.operations
            if obligation_ref in op.obligation_refs
        ]

    def get_dependencies(self, op_id: str) -> list[str]:
        """
        Tìm dependencies của một operation.

        Dependencies là các operations mà op này cần output.

        Args:
            op_id: Operation ID để tìm dependencies

        Returns:
            Danh sách dependency operation IDs
        """
        deps = set()
        for df in self.data_flows:
            if df.target_op == op_id:
                deps.add(df.source_op)
        return list(deps)

    def get_dependents(self, op_id: str) -> list[str]:
        """
        Tìm operations phụ thuộc vào một operation.

        Dependents là các operations sử dụng output của op này.

        Args:
            op_id: Operation ID để tìm dependents

        Returns:
            Danh sách dependent operation IDs
        """
        dependents = set()
        for df in self.data_flows:
            if df.source_op == op_id:
                dependents.add(df.target_op)
        return list(dependents)


# ============================================================================
# MIR Builder - Helper cho MIR construction
# ============================================================================


@dataclass
class MIRBuilder:
    """
    MIR Builder - Fluent API cho MIR construction.

    Cung cấp builder pattern để tạo MIR một cách declarative.
    Hữu ích cho MIR generation từ ProjectionTree.

    Attributes:
        mir: MIR đang build
    """

    mir: MIR = field(default_factory=MIR)

    def with_version(self, version: str) -> "MIRBuilder":
        """
        Set MIR version.

        Args:
            version: Version string

        Returns:
            Self cho chaining
        """
        self.mir.metadata["version"] = version
        return self

    def with_source(self, source: str) -> "MIRBuilder":
        """
        Set MIR source.

        Args:
            source: Source identifier

        Returns:
            Self cho chaining
        """
        self.mir.metadata["source"] = source
        return self

    def add_operation(
        self,
        op_id: str,
        op_type: str,
        params: dict[str, Any],
        obligation_refs: list[str] | None = None,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None
    ) -> "MIRBuilder":
        """
        Thêm operation vào MIR.

        Args:
            op_id: Operation ID
            op_type: Operation type
            params: Operation params
            obligation_refs: Obligation references
            input_refs: Input references
            output_refs: Output references

        Returns:
            Self cho chaining
        """
        self.mir.operations.append(Operation(
            op_id=op_id,
            op_type=op_type,
            params=params,
            obligation_refs=obligation_refs or [],
            input_refs=input_refs or [],
            output_refs=output_refs or []
        ))
        return self

    def add_data_flow(
        self,
        source_op: str,
        source_field: str,
        target_op: str,
        target_field: str,
        transformation: str | None = None
    ) -> "MIRBuilder":
        """
        Thêm data flow vào MIR.

        Args:
            source_op: Source operation ID
            source_field: Source field name
            target_op: Target operation ID
            target_field: Target field name
            transformation: Transformation function

        Returns:
            Self cho chaining
        """
        self.mir.data_flows.append(DataFlow(
            source_op=source_op,
            source_field=source_field,
            target_op=target_op,
            target_field=target_field,
            transformation=transformation
        ))
        return self

    def add_effect_flow(
        self,
        source_op: str,
        effect_type: str,
        target: str,
        payload_fields: list[str] | None = None
    ) -> "MIRBuilder":
        """
        Thêm effect flow vào MIR.

        Args:
            source_op: Source operation ID
            effect_type: Effect type
            target: Effect target
            payload_fields: Payload fields

        Returns:
            Self cho chaining
        """
        self.mir.effect_flows.append(EffectFlow(
            source_op=source_op,
            effect_type=effect_type,
            target=target,
            payload_fields=payload_fields or []
        ))
        return self

    def add_boundary(
        self,
        boundary_id: str,
        boundary_type: str,
        enclosing_ops: list[str],
        config: dict[str, Any] | None = None
    ) -> "MIRBuilder":
        """
        Thêm boundary vào MIR.

        Args:
            boundary_id: Boundary ID
            boundary_type: Boundary type
            enclosing_ops: Enclosed operations
            config: Boundary config

        Returns:
            Self cho chaining
        """
        self.mir.boundaries.append(Boundary(
            boundary_id=boundary_id,
            boundary_type=boundary_type,
            enclosing_ops=enclosing_ops,
            config=config or {}
        ))
        return self

    def build(self) -> MIR:
        """
        Build MIR hoàn tất.

        Returns:
            MIR instance
        """
        return self.mir