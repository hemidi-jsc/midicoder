"""Internal models for code-plan build."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SuggestedPath:
    file: str
    anchor: str
    reason: str | None = None
    score: float | None = None
    resolver_source: str | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"file": self.file, "anchor": self.anchor}
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.score is not None:
            payload["score"] = self.score
        if self.resolver_source is not None:
            payload["resolver_source"] = self.resolver_source
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


@dataclass(frozen=True)
class RequiredFile:
    path_pattern: str
    required: bool
    role: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path_pattern": self.path_pattern,
            "required": self.required,
            "role": self.role,
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True)
class PlanMeta:
    generated_at: str
    generator_version: str
    source_ir_checksum: str
    ir_kinds_used: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CodePlanItem:
    schema_version: str
    ir_ref: str
    target: str
    pseudo: str
    pseudo_struct: dict[str, Any] | None
    suggested_paths: list[SuggestedPath]
    meta: PlanMeta
    required_files: list[RequiredFile] = field(default_factory=list)
    integration_contract: dict[str, Any] | None = None
    io_reconciliation: dict[str, Any] | None = None
    security_contract: dict[str, Any] | None = None
    error_contract: dict[str, Any] | None = None
    merge_contract: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "ir_ref": self.ir_ref,
            "target": self.target,
            "pseudo": self.pseudo,
            "pseudo_struct": self.pseudo_struct,
            "suggested_paths": [path.to_dict() for path in self.suggested_paths],
            "required_files": [entry.to_dict() for entry in self.required_files],
            "meta": self.meta.to_dict(),
        }
        if self.integration_contract is not None:
            payload["integration_contract"] = self.integration_contract
        if self.io_reconciliation is not None:
            payload["io_reconciliation"] = self.io_reconciliation
        if self.security_contract is not None:
            payload["security_contract"] = self.security_contract
        if self.error_contract is not None:
            payload["error_contract"] = self.error_contract
        if self.merge_contract is not None:
            payload["merge_contract"] = self.merge_contract
        return payload


@dataclass(frozen=True)
class IRPlanItem:
    raw_id: str
    type_name: str
    id: str
    kind: str
    module: str
    source: dict[str, Any]
    payload: dict[str, Any]
    source_order: int
    io_contract: dict[str, Any] = field(default_factory=dict)
    behavior_contract: dict[str, Any] = field(default_factory=dict)
    api_contract: dict[str, Any] = field(default_factory=dict)
    state_contract: dict[str, Any] = field(default_factory=dict)
    rules_contract: dict[str, Any] = field(default_factory=dict)
    policy_contract: dict[str, Any] = field(default_factory=dict)
    trace_contract: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphNode:
    file: str
    module: str
    kind: str
    symbols: list[str] = field(default_factory=list)
    score_base: float = 0.0
    source_order: int = 0


@dataclass(frozen=True)
class GraphEdge:
    from_file: str
    to_file: str
    type: str
    weight: float


@dataclass(frozen=True)
class GraphCandidate:
    file: str
    module: str
    kind: str
    source_order: int
    score: float
    distance: int


@dataclass
class BuildResult:
    plans: list[CodePlanItem]
    plan_paths: list[str]
    warnings: list[str]
    errors: list[str]
    stack: str


@dataclass(frozen=True)
class IntegrationContext:
    canonical_symbols: dict[str, dict[str, Any]]
    routes_by_command: dict[str, list[dict[str, Any]]]
    routes_by_query: dict[str, list[dict[str, Any]]]
    permissions_by_item: dict[str, list[dict[str, Any]]]
    errors_by_key: dict[str, list[dict[str, Any]]]
    workflow_transitions_by_command: dict[str, list[dict[str, Any]]]
    io_by_ref: dict[str, dict[str, list[dict[str, Any]]]]
    io_by_symbol: dict[str, dict[str, dict[str, list[dict[str, Any]]]]]
    seams: list[dict[str, Any]] = field(default_factory=list)
    virtual_seams: list[dict[str, Any]] = field(default_factory=list)
    profile: dict[str, Any] | None = None
