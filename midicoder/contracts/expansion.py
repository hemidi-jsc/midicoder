"""
Expansion Report Contract cho Midicoder v1.0.0

Module này định nghĩa Expansion Report - trace macro expansion thành core instructions.

Theo Rule 2 trong MIDICODER_STRATEGY.md:
- Macro Expansion là deterministic, không LLM
- Macro capabilities expand thành core capabilities
- Expansion trace phải visible cho debugging

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifact import ArtifactBase, ArtifactMetadata


# ============================================================================
# Expansion Trace
# ============================================================================


@dataclass
class ExpansionTrace:
    """
    Expansion Trace ghi lại chi tiết của một bước expansion.
    
    Trace giúp debug và verify rằng expansion đúng như mong đợi.
    
    Attributes:
        source_id: ID của macro instance được expand
        source_type: Type của macro
        target_ids: Danh sách core capability IDs sau khi expand
        params_mapping: Mapping từ macro params → core params
        obligations_added: Obligations được thêm từ expansion
        config_applied: Config đã apply cho expansion
        
    Example:
        ExpansionTrace(
            source_id="create_order",
            source_type="authorized_mutation",
            target_ids=[
                "auth_perm_001",
                "tenant_scope_001",
                "begin_txn_001",
                "create_order_rec_001",
                "emit_order_created_001",
                "commit_txn_001",
            ],
            obligations_added=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
            ],
        )
    """
    source_id: str
    source_type: str
    target_ids: list[str] = field(default_factory=list)
    params_mapping: dict[str, Any] = field(default_factory=dict)
    obligations_added: list[str] = field(default_factory=list)
    config_applied: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "target_ids": self.target_ids,
            "params_mapping": self.params_mapping,
            "obligations_added": self.obligations_added,
            "config_applied": self.config_applied,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpansionTrace":
        """Create from dictionary."""
        return cls(
            source_id=data["source_id"],
            source_type=data["source_type"],
            target_ids=data.get("target_ids", []),
            params_mapping=data.get("params_mapping", {}),
            obligations_added=data.get("obligations_added", []),
            config_applied=data.get("config_applied", {}),
        )


# ============================================================================
# Expansion Step
# ============================================================================


@dataclass
class ExpansionStep:
    """
    Expansion Step đại diện cho một bước trong expansion pipeline.
    
    Expansion có thể có nhiều steps:
    1. Resolve macro definition
    2. Apply default obligations
    3. Generate core capability instances
    4. Resolve parameters
    5. Generate MIR operations
    
    Attributes:
        step_name: Tên bước
        step_number: Số thứ tự bước
        input_refs: References vào inputs của step
        output_refs: References vào outputs của step
        status: Status của bước (success/failed/skipped)
        trace: Expansion trace cho bước này
        error: Error message nếu fail
        
    Example:
        ExpansionStep(
            step_name="resolve_macro",
            step_number=1,
            input_refs=["instance:create_order"],
            output_refs=["macro:authorized_mutation"],
            status="success",
            trace=ExpansionTrace(...),
        )
    """
    step_name: str
    step_number: int
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    status: str = "success"  # success, failed, skipped
    trace: ExpansionTrace | None = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "step_name": self.step_name,
            "step_number": self.step_number,
            "input_refs": self.input_refs,
            "output_refs": self.output_refs,
            "status": self.status,
        }
        
        if self.trace:
            result["trace"] = self.trace.to_dict()
        
        if self.error:
            result["error"] = self.error
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpansionStep":
        """Create from dictionary."""
        trace_data = data.get("trace")
        trace = ExpansionTrace.from_dict(trace_data) if trace_data else None
        
        return cls(
            step_name=data["step_name"],
            step_number=data["step_number"],
            input_refs=data.get("input_refs", []),
            output_refs=data.get("output_refs", []),
            status=data.get("status", "success"),
            trace=trace,
            error=data.get("error"),
        )
    
    @property
    def is_success(self) -> bool:
        """Kiểm tra step thành công không."""
        return self.status == "success"
    
    @property
    def is_failed(self) -> bool:
        """Kiểm tra step thất bại không."""
        return self.status == "failed"


# ============================================================================
# Expansion Report
# ============================================================================


@dataclass
class ExpansionReport(ArtifactBase):
    """
    Expansion Report - Trace toàn bộ quá trình macro expansion.
    
    Theo Rule 2: Macro expansion deterministic và debuggable.
    Report này cung cấp:
    - Full trace của expansion
    - Mapping từ macros → cores
    - Obligations được generate
    - Errors trong quá trình expansion
    
    Attributes:
        source_instance_id: ID của capability instance được expand
        source_macro_type: Type của macro
        steps: Danh sách expansion steps
        final_core_instances: Danh sách core instances sau khi expand
        total_obligations: Total obligations sau expansion
        expansion_time_ms: Thời gian expansion (milliseconds)
        metadata: Artifact metadata
        
    Example:
        report = ExpansionReport(
            source_instance_id="create_order",
            source_macro_type="authorized_mutation",
            steps=[
                ExpansionStep(step_name="resolve_macro", ...),
                ExpansionStep(step_name="generate_cores", ...),
            ],
            final_core_instances=[
                "auth_perm_001",
                "tenant_scope_001",
                "begin_txn_001",
                ...
            ],
            total_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
            ],
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    source_instance_id: str = ""
    source_macro_type: str = ""
    steps: list[ExpansionStep] = field(default_factory=list)
    final_core_instances: list[str] = field(default_factory=list)
    total_obligations: list[str] = field(default_factory=list)
    expansion_time_ms: int | None = None
    
    # Cache mappings
    _steps_by_name: dict[str, ExpansionStep] = field(default_factory=dict, repr=False)
    
    @property
    def artifact_type(self) -> str:
        """Return artifact type."""
        return "expansion_report"
    
    def __post_init__(self) -> None:
        """Build cache mappings."""
        self._build_cache()
    
    def _build_cache(self) -> None:
        """Build cache mappings cho fast lookups."""
        self._steps_by_name = {s.step_name: s for s in self.steps}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "source_instance_id": self.source_instance_id,
            "source_macro_type": self.source_macro_type,
            "steps": [s.to_dict() for s in self.steps],
            "final_core_instances": self.final_core_instances,
            "total_obligations": self.total_obligations,
            "expansion_time_ms": self.expansion_time_ms,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpansionReport":
        """Tạo ExpansionReport từ dictionary."""
        # Tạo instance với các fields cơ bản (metadata được set sau do init=False)
        report = cls(
            source_instance_id=data.get("source_instance_id", ""),
            source_macro_type=data.get("source_macro_type", ""),
            steps=[ExpansionStep.from_dict(s) for s in data.get("steps", [])],
            final_core_instances=data.get("final_core_instances", []),
            total_obligations=data.get("total_obligations", []),
            expansion_time_ms=data.get("expansion_time_ms"),
        )
        # Set metadata sau khi tạo instance (do init=False)
        object.__setattr__(report, 'metadata', ArtifactMetadata.from_dict(data.get("metadata", {})))
        return report
    
    # =========================================================================
    # Step Management
    # =========================================================================
    
    def add_step(
        self,
        step_name: str,
        step_number: int,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        status: str = "success",
        trace: ExpansionTrace | None = None,
        error: str | None = None,
    ) -> ExpansionStep:
        """
        Thêm expansion step.
        
        Args:
            step_name: Tên bước
            step_number: Số thứ tự bước
            input_refs: References vào inputs
            output_refs: References vào outputs
            status: Status của bước
            trace: Expansion trace
            error: Error message nếu fail
            
        Returns:
            ExpansionStep được tạo
        """
        step = ExpansionStep(
            step_name=step_name,
            step_number=step_number,
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            status=status,
            trace=trace,
            error=error,
        )
        self.steps.append(step)
        self._steps_by_name[step_name] = step
        return step
    
    def get_step(self, step_name: str) -> ExpansionStep | None:
        """Lấy step theo name."""
        return self._steps_by_name.get(step_name)
    
    def get_step_by_number(self, step_number: int) -> ExpansionStep | None:
        """Lấy step theo số thứ tự."""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def is_successful(self) -> bool:
        """Kiểm tra expansion thành công không."""
        return all(step.is_success for step in self.steps)
    
    def get_failed_steps(self) -> list[ExpansionStep]:
        """Lấy danh sách failed steps."""
        return [s for s in self.steps if s.is_failed]
    
    def get_all_trace(self) -> list[ExpansionTrace]:
        """Lấy tất cả traces từ các steps."""
        traces: list[ExpansionTrace] = []
        for step in self.steps:
            if step.trace:
                traces.append(step.trace)
        return traces
    
    def get_obligation_summary(self) -> dict[str, Any]:
        """
        Lấy summary của obligations.
        
        Returns:
            Dictionary với obligation statistics
        """
        return {
            "total_obligations": len(self.total_obligations),
            "obligations": self.total_obligations,
            "by_step": {
                step.step_name: (step.trace.obligations_added if step.trace else [])
                for step in self.steps
            },
        }
    
    def get_core_instance_summary(self) -> dict[str, Any]:
        """
        Lấy summary của core instances.
        
        Returns:
            Dictionary với core instance statistics
        """
        return {
            "total_cores": len(self.final_core_instances),
            "core_instances": self.final_core_instances,
            "generated_in_steps": {
                step.step_name: (step.trace.target_ids if step.trace else [])
                for step in self.steps
            },
        }
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate expansion report.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check required fields
        if not self.source_instance_id:
            errors.append("ExpansionReport.source_instance_id is required")
        
        if not self.source_macro_type:
            errors.append("ExpansionReport.source_macro_type is required")
        
        # Check steps are ordered
        for i, step in enumerate(self.steps):
            if step.step_number != i + 1:
                errors.append(
                    f"Step order mismatch: expected {i + 1}, got "
                    f"{step.step_number} for '{step.step_name}'"
                )
        
        # Check failed steps have error message
        for step in self.steps:
            if step.is_failed and not step.error:
                errors.append(
                    f"Failed step '{step.step_name}' has no error message"
                )
        
        return errors