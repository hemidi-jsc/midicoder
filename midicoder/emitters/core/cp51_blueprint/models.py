# coding: utf-8
"""
Mô-đun models cho Blueprint Composition Engine (CP51).

Định nghĩa các data classes để biểu diễn blueprint composition:

- CapabilityGraph: DAG của capabilities từ CPs + DPs
- Resolution: Kết quả resolve dependency graph
- MergeStrategy: Chiến lược merge output từ nhiều packs
- ConflictResolution: Xử lý xung đột khi merge
- BlueprintSchema: Schema versioning + backward compatibility
- VersionConstraint: Ràng buộc version giữa các packs

Obligations:
1. CapabilityGraph PHẢI là DAG — không cho phép cycle (MDC-CP51-001)
2. Resolution PHẢI include tất cả mandatory P0 packs (MDC-CP51-002)
3. VersionConstraint PHẢI enforce semver compatibility (MDC-CP51-003)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


# ===========================================================================
# CapabilityGraph
# ===========================================================================


@dataclass
class CapabilityNode:
    """
    Node trong capability graph — đại diện cho một pack (CP/DP/RX).

    Attributes:
        pack_id: ID của pack (vd: CP01, DP01, RX01)
        pack_type: Loại pack (core, domain, regulatory)
        capabilities: Danh sách capabilities mà pack cung cấp
        depends_on: Danh sách pack IDs mà pack này phụ thuộc
        metadata: Metadata bổ sung (optional)
    """

    pack_id: str
    pack_type: str
    capabilities: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo."""
        if not self.pack_id or not self.pack_id.strip():
            EM.raise_error(
                ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED,
                detail="pack_id không được rỗng",
            )

        if self.pack_type not in ("core", "domain", "regulatory"):
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail=f"pack_type '{self.pack_type}' không hợp lệ, phải là: core, domain, regulatory",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "pack_type": self.pack_type,
            "capabilities": self.capabilities,
            "depends_on": self.depends_on,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityNode:
        """Tạo CapabilityNode từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            pack_type=data["pack_type"],
            capabilities=data.get("capabilities", []),
            depends_on=data.get("depends_on", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CapabilityGraph:
    """
    DAG (Directed Acyclic Graph) của capabilities từ CPs + DPs + RXs.

    CapabilityGraph biểu diễn dependency relationship giữa các packs.
    Graph PHẢI là DAG — không cho phép cycle (Obligation 1, MDC-CP51-001).

    Attributes:
        nodes: Danh sách capability nodes
        edges: Danh sách edges (source → target, nghĩa là source depends on target)

    Raises:
        MidicoderError: Nếu graph chứa cycle (MDC-CP51-001) — Obligation 1
    """

    nodes: list[CapabilityNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo — enforce DAG invariant."""
        # Obligation 1: graph PHẢI là DAG — detect cycle
        if self._has_cycle():
            EM.raise_error(
                ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED,
                detail="CapabilityGraph chứa cycle — không thể resolve dependencies",
            )

    def add_node(self, node: CapabilityNode) -> None:
        """
        Thêm node vào graph và tạo edges từ depends_on.

        Args:
            node: CapabilityNode để thêm
        """
        self.nodes.append(node)
        for dep in node.depends_on:
            self.edges.append((node.pack_id, dep))

        # Re-validate DAG invariant sau khi thêm
        if self._has_cycle():
            EM.raise_error(
                ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED,
                detail=f"Thêm node '{node.pack_id}' tạo cycle trong graph",
            )

    def get_topological_order(self) -> list[str]:
        """
        Trả về topological order của nodes (Kahn's algorithm).

        Returns:
            Danh sách pack IDs theo topological order (dependencies trước)
        """
        # Build adjacency list + in-degree count
        in_degree: dict[str, int] = {}
        adj: dict[str, list[str]] = {}

        all_ids = [n.pack_id for n in self.nodes]
        for nid in all_ids:
            in_degree[nid] = 0
            adj[nid] = []

        for source, target in self.edges:
            if source in adj and target in in_degree:
                adj[target].append(source)
                in_degree[source] = in_degree.get(source, 0) + 1

        # Kahn's algorithm
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            queue.sort()  # deterministic order
            node = queue.pop(0)
            result.append(node)

            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(all_ids):
            # Should not happen since __post_init__ checks for cycles
            raise MidicoderError(
                code=ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED,
                message="Topological sort failed — graph chứa cycle",
            )

        return result

    def get_all_capabilities(self) -> list[str]:
        """
        Trả về tất cả capabilities từ tất cả nodes, theo topological order.

        Returns:
            Danh sách unique capabilities
        """
        order = self.get_topological_order()
        node_map = {n.pack_id: n for n in self.nodes}

        caps = []
        for pack_id in order:
            node = node_map.get(pack_id)
            if node:
                for cap in node.capabilities:
                    if cap not in caps:
                        caps.append(cap)

        return caps

    def _has_cycle(self) -> bool:
        """Detect cycle trong graph dùng DFS."""
        # Build adjacency list
        adj: dict[str, list[str]] = {}
        all_ids = [n.pack_id for n in self.nodes]

        for nid in all_ids:
            adj[nid] = []

        for source, target in self.edges:
            if source in adj:
                adj[source].append(target)

        # DFS with coloring: WHITE=0, GRAY=1, BLACK=2
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in all_ids}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in adj.get(node, []):
                if color.get(neighbor) == GRAY:
                    return True  # back edge = cycle
                if color.get(neighbor) == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for nid in all_ids:
            if color[nid] == WHITE:
                if dfs(nid):
                    return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [{"from": src, "to": tgt} for src, tgt in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityGraph:
        """Tạo CapabilityGraph từ dictionary."""
        nodes = [CapabilityNode.from_dict(n) for n in data.get("nodes", [])]
        edges_data = data.get("edges", [])
        edges = [(e["from"], e["to"]) for e in edges_data]

        graph = cls(nodes=nodes, edges=edges)
        # __post_init__ will validate DAG
        return graph


# ===========================================================================
# Resolution
# ===========================================================================


class ResolutionStatus(str, Enum):
    """Trạng thái của resolution."""

    RESOLVED = "resolved"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class Resolution:
    """
    Kết quả resolve dependency graph.

    Resolution chứa kết quả sau khi resolve tất cả dependencies:
    resolved packs, missing dependencies, conflicts.

    Attributes:
        status: Trạng thái resolution (resolved, partial, failed)
        resolved_packs: Danh sách pack IDs đã resolve thành công
        missing_dependencies: Danh sách pack IDs không tìm thấy
        conflicts: Danh sách conflict descriptions
        topological_order: Topological order của resolved packs
        metadata: Metadata bổ sung (optional)

    Raises:
        MidicoderError: Nếu status là RESOLVED但有 missing_dependencies (MDC-CP51-002)
    """

    status: ResolutionStatus
    resolved_packs: list[str] = field(default_factory=list)
    missing_dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    topological_order: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo."""
        # Nếu status là RESOLVED nhưng có missing dependencies → error
        if self.status == ResolutionStatus.RESOLVED and self.missing_dependencies:
            EM.raise_error(
                ErrorCode.BLUEPRINT_DEPENDENCY_RESOLUTION_FAILED,
                detail=f"Resolution RESOLVED nhưng còn missing dependencies: {self.missing_dependencies}",
            )

        # Nếu status là RESOLVED nhưng có conflicts → downgrade到 PARTIAL
        if self.status == ResolutionStatus.RESOLVED and self.conflicts:
            self.status = ResolutionStatus.PARTIAL

        # Nếu có missing dependencies → status là FAILED
        if self.missing_dependencies and self.status != ResolutionStatus.FAILED:
            self.status = ResolutionStatus.FAILED

    @property
    def is_fully_resolved(self) -> bool:
        """Kiểm tra resolution có hoàn toàn thành công không."""
        return (
            self.status == ResolutionStatus.RESOLVED
            and not self.missing_dependencies
            and not self.conflicts
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "status": self.status.value,
            "resolved_packs": self.resolved_packs,
            "missing_dependencies": self.missing_dependencies,
            "conflicts": self.conflicts,
            "topological_order": self.topological_order,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Resolution:
        """Tạo Resolution từ dictionary."""
        return cls(
            status=ResolutionStatus(data.get("status", "failed")),
            resolved_packs=data.get("resolved_packs", []),
            missing_dependencies=data.get("missing_dependencies", []),
            conflicts=data.get("conflicts", []),
            topological_order=data.get("topological_order", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# MergeStrategy + ConflictResolution
# ===========================================================================


class MergeMode(str, Enum):
    """Chế độ merge output từ nhiều packs."""

    # Merge tất cả, conflict resolution tùy case
    MERGE_ALL = "merge_all"
    # Chỉ merge packs không conflict
    MERGE_NON_CONFLICTING = "merge_non_conflicting"
    # Prioritize pack có priority cao hơn
    PRIORITY_BASED = "priority_based"
    # Chỉ merge theo topological order, skip nếu conflict
    TOPOLOGICAL = "topological"


@dataclass
class MergeStrategy:
    """
    Chiến lược merge output từ nhiều packs.

    MergeStrategy xác định cách merge code artifact từ nhiều packs
    khi chúng có overlapping output (cùng file, cùng function, v.v.).

    Attributes:
        mode: Chế độ merge (merge_all, merge_non_conflicting, priority_based, topological)
        priority_map: Map pack_id → priority (cao hơn = ưu tiên hơn)
        fallback_mode: Fallback mode nếu mode chính không resolve được conflict
        metadata: Metadata bổ sung (optional)
    """

    mode: MergeMode
    priority_map: dict[str, int] = field(default_factory=dict)
    fallback_mode: Optional[MergeMode] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_priority(self, pack_id: str) -> int:
        """
        Lấy priority của pack.

        Args:
            pack_id: ID của pack

        Returns:
            Priority (mặc định: 0)
        """
        return self.priority_map.get(pack_id, 0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "mode": self.mode.value,
            "priority_map": self.priority_map,
            "fallback_mode": self.fallback_mode.value if self.fallback_mode else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MergeStrategy:
        """Tạo MergeStrategy từ dictionary."""
        return cls(
            mode=MergeMode(data.get("mode", "merge_all")),
            priority_map=data.get("priority_map", {}),
            fallback_mode=MergeMode(data["fallback_mode"]) if data.get("fallback_mode") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConflictResolution:
    """
    Xử lý xung đột khi merge output từ nhiều packs.

    ConflictResolution xác định cách handle khi 2+ packs generate
    cùng artifact (file, function, class) với nội dung khác nhau.

    Attributes:
        conflict_type: Loại xung đột (file_overlap, function_overlap, class_overlap, import_overlap)
        conflicting_packs: Danh sách pack IDs conflict
        artifact_path: Path của artifact conflict
        resolution: Cách resolve (keep_first, keep_last, merge, override_with_priority)
        winner_pack: Pack ID được chọn (nếu resolution là keep_first/keep_last/override)
        metadata: Metadata bổ sung (optional)
    """

    conflict_type: str
    conflicting_packs: list[str]
    artifact_path: str
    resolution: str
    winner_pack: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo."""
        if not self.conflict_type or not self.conflict_type.strip():
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail="conflict_type không được rỗng",
            )

        if len(self.conflicting_packs) < 2:
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail="conflicting_packs phải có ít nhất 2 packs",
            )

        valid_resolutions = ("keep_first", "keep_last", "merge", "override_with_priority")
        if self.resolution not in valid_resolutions:
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail=f"resolution '{self.resolution}' không hợp lệ, phải là: {valid_resolutions}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "conflict_type": self.conflict_type,
            "conflicting_packs": self.conflicting_packs,
            "artifact_path": self.artifact_path,
            "resolution": self.resolution,
            "winner_pack": self.winner_pack,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConflictResolution:
        """Tạo ConflictResolution từ dictionary."""
        return cls(
            conflict_type=data["conflict_type"],
            conflicting_packs=data.get("conflicting_packs", []),
            artifact_path=data["artifact_path"],
            resolution=data["resolution"],
            winner_pack=data.get("winner_pack"),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# BlueprintSchema + VersionConstraint
# ===========================================================================


@dataclass
class BlueprintSchema:
    """
    Schema versioning + backward compatibility cho blueprint.

    BlueprintSchema quản lý version của blueprint schema và xác định
    backward compatibility giữa các versions.

    Attributes:
        schema_version: Version của schema (semver, vd: "1.0.0")
        min_compatible_version: Version nhỏ nhất tương thích backward
        max_compatible_version: Version lớn nhất tương thích forward
        deprecation_notice: Thông báo deprecation (nếu schema bị deprecate)
        migration_guide: Link đến migration guide (nếu có breaking change)
        metadata: Metadata bổ sung (optional)
    """

    schema_version: str
    min_compatible_version: str = "1.0.0"
    max_compatible_version: str = "2.0.0"
    deprecation_notice: Optional[str] = None
    migration_guide: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo."""
        if not self.schema_version or not self.schema_version.strip():
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail="schema_version không được rỗng",
            )

        # Validate semver format (basic check)
        if not self._is_valid_semver(self.schema_version):
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail=f"schema_version '{self.schema_version}' không theo semver format",
            )

    def is_compatible(self, other_version: str) -> bool:
        """
        Kiểm tra version khác có tương thích không.

        Args:
            other_version: Version để kiểm tra (semver)

        Returns:
            True nếu version nằm trong compatibility range
        """
        return (
            self._compare_versions(other_version, self.min_compatible_version) >= 0
            and self._compare_versions(other_version, self.max_compatible_version) < 0
        )

    def _is_valid_semver(self, version: str) -> bool:
        """Kiểm tra version có theo semver format không (basic check)."""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        So sánh 2 semver versions.

        Returns:
            -1 nếu v1 < v2, 0 nếu v1 == v2, 1 nếu v1 > v2
        """
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "schema_version": self.schema_version,
            "min_compatible_version": self.min_compatible_version,
            "max_compatible_version": self.max_compatible_version,
            "deprecation_notice": self.deprecation_notice,
            "migration_guide": self.migration_guide,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlueprintSchema:
        """Tạo BlueprintSchema từ dictionary."""
        return cls(
            schema_version=data.get("schema_version", "1.0.0"),
            min_compatible_version=data.get("min_compatible_version", "1.0.0"),
            max_compatible_version=data.get("max_compatible_version", "2.0.0"),
            deprecation_notice=data.get("deprecation_notice"),
            migration_guide=data.get("migration_guide"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VersionConstraint:
    """
    Ràng buộc version giữa các packs.

    VersionConstraint xác định version range mà một pack có thể
    phụ thuộc vào pack khác.

    Attributes:
        pack_id: ID của pack bị ràng buộc
        min_version: Version nhỏ nhất (semver, inclusive)
        max_version: Version lớn nhất (semver, exclusive)
        recommended_version: Version được khuyến nghị
        metadata: Metadata bổ sung (optional)

    Raises:
        MidicoderError: Nếu pack_id rỗng (MDC-CP51-003) — Obligation 3
        MidicoderError: Nếu version không theo semver (MDC-CP51-003)
    """

    pack_id: str
    min_version: str = "1.0.0"
    max_version: str = "2.0.0"
    recommended_version: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sau khi khởi tạo — enforce semver (Obligation 3)."""
        # Obligation 3: pack_id không rỗng + semver
        if not self.pack_id or not self.pack_id.strip():
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail="pack_id không được rỗng",
            )

        # Validate semver format
        for field_name in ("min_version", "max_version"):
            version = getattr(self, field_name)
            if not self._is_valid_semver(version):
                EM.raise_error(
                    ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                    detail=f"{field_name} '{version}' không theo semver format",
                )

        if self.recommended_version and not self._is_valid_semver(self.recommended_version):
            EM.raise_error(
                ErrorCode.BLUEPRINT_SCHEMA_INVALID,
                detail=f"recommended_version '{self.recommended_version}' không theo semver format",
            )

    def satisfies(self, version: str) -> bool:
        """
        Kiểm tra version có满足 constraint không.

        Args:
            version: Version để kiểm tra (semver)

        Returns:
            True nếu version nằm trong [min_version, max_version)
        """
        return (
            self._compare_versions(version, self.min_version) >= 0
            and self._compare_versions(version, self.max_version) < 0
        )

    def _is_valid_semver(self, version: str) -> bool:
        """Kiểm tra version có theo semver format không."""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def _compare_versions(self, v1: str, v2: str) -> int:
        """So sánh 2 semver versions."""
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "min_version": self.min_version,
            "max_version": self.max_version,
            "recommended_version": self.recommended_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionConstraint:
        """Tạo VersionConstraint từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            min_version=data.get("min_version", "1.0.0"),
            max_version=data.get("max_version", "2.0.0"),
            recommended_version=data.get("recommended_version"),
            metadata=data.get("metadata", {}),
        )


__all__ = [
    # CapabilityGraph
    "CapabilityNode",
    "CapabilityGraph",
    # Resolution
    "ResolutionStatus",
    "Resolution",
    # MergeStrategy + ConflictResolution
    "MergeMode",
    "MergeStrategy",
    "ConflictResolution",
    # BlueprintSchema + VersionConstraint
    "BlueprintSchema",
    "VersionConstraint",
    # Composition Plan (từ contracts/composition/ — emit order + template binding)
    "CompositionNode",
    "PackResolution",
    "TemplateBinding",
    "StackBinding",
    "CompositionPlan",
]


# ===========================================================================
# Composition Plan Models
# (từ contracts/composition/ — emit order + template binding + stack binding)
# ===========================================================================


@dataclass
class CompositionNode:
    """
    Node trong emit order của CompositionPlan.

    Mỗi node đại diện cho một pack cần emit, với thông tin
    về thứ tự emit và dependencies.

    Attributes:
        pack_id: ID của pack (CP01, DP01, RX01)
        pack_type: Loại pack (core_pack, domain_pack, regulatory_overlay)
        emit_order: Thứ tự emit (1-based, nhỏ hơn = emit trước)
        phase: Phase của pack (P0, P1, P2, P3, P4)
        dependencies: Danh sách pack IDs phải emit trước pack này
    """

    pack_id: str
    pack_type: str
    emit_order: int
    phase: str
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "pack_type": self.pack_type,
            "emit_order": self.emit_order,
            "phase": self.phase,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompositionNode:
        """Tạo CompositionNode từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            pack_type=data["pack_type"],
            emit_order=data["emit_order"],
            phase=data["phase"],
            dependencies=data.get("dependencies", []),
        )


@dataclass
class PackResolution:
    """
    Kết quả resolve một pack từ TaxonomyRegistry.

    Chứa thông tin chi tiết về pack đã được resolve,
    bao gồm capabilities_provided và templates mapping.

    Attributes:
        pack_id: ID của pack
        pack_type: Loại pack
        internal_id: Internal ID (vd: cp1-domain-model)
        status: Trạng thái pack (stable, developing, planned)
        capabilities_provided: Danh sách capabilities của pack
        templates: Mapping capability → template path
        pack_yml_path: Đường dẫn đến pack.yml
    """

    pack_id: str
    pack_type: str
    internal_id: str
    status: str
    capabilities_provided: list[str] = field(default_factory=list)
    templates: dict[str, str] = field(default_factory=dict)
    pack_yml_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "pack_id": self.pack_id,
            "pack_type": self.pack_type,
            "internal_id": self.internal_id,
            "status": self.status,
            "capabilities_provided": self.capabilities_provided,
            "templates": self.templates,
            "pack_yml_path": self.pack_yml_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PackResolution:
        """Tạo PackResolution từ dictionary."""
        return cls(
            pack_id=data["pack_id"],
            pack_type=data["pack_type"],
            internal_id=data["internal_id"],
            status=data["status"],
            capabilities_provided=data.get("capabilities_provided", []),
            templates=data.get("templates", {}),
            pack_yml_path=data.get("pack_yml_path", ""),
        )


@dataclass
class TemplateBinding:
    """
    Binding giữa MIR operation type và template path.

    Mỗi binding nối một MIR op_type với template cụ thể
    trong stack cụ thể.

    Attributes:
        op_type: MIR operation type (vd: create_record, query_records)
        pack_id: Pack cung cấp template (vd: CP08)
        template_path: Đường dẫn template (vd: fastapi/model.py.jinja2)
        stack: Stack name (fastapi, nestjs, angular, react)
    """

    op_type: str
    pack_id: str
    template_path: str
    stack: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "op_type": self.op_type,
            "pack_id": self.pack_id,
            "template_path": self.template_path,
            "stack": self.stack,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateBinding:
        """Tạo TemplateBinding từ dictionary."""
        return cls(
            op_type=data["op_type"],
            pack_id=data["pack_id"],
            template_path=data["template_path"],
            stack=data["stack"],
        )


@dataclass
class StackBinding:
    """
    Binding giữa stack name và danh sách templates.

    Mỗi stack binding chứa tất cả templates cần render
    cho stack cụ thể.

    Attributes:
        stack_name: Tên stack (fastapi, nestjs, angular, react)
        templates: Danh sách template bindings cho stack này
        stack_dir: Đường dẫn đến stack directory
    """

    stack_name: str
    templates: list[TemplateBinding] = field(default_factory=list)
    stack_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "stack_name": self.stack_name,
            "templates": [t.to_dict() for t in self.templates],
            "stack_dir": self.stack_dir,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StackBinding:
        """Tạo StackBinding từ dictionary."""
        return cls(
            stack_name=data["stack_name"],
            templates=[
                TemplateBinding.from_dict(t) for t in data.get("templates", [])
            ],
            stack_dir=data.get("stack_dir", ""),
        )


@dataclass
class CompositionPlan:
    """
    Kế hoạch composition hoàn chỉnh cho Blueprint.

    CompositionPlan là output của CP51 — chứa đầy đủ thông tin
    cần thiết cho stage 'code gen' để emit source code:
    - Emit order (topological sort của packs)
    - Pack resolution (capabilities, templates)
    - Template mapping (MIR op_type → template)
    - Stack bindings (stack-specific templates)
    - Validation results

    Attributes:
        blueprint_id: ID của CompiledBlueprint reference
        schema_version: Version của composition plan schema
        emit_order: Danh sách nodes theo thứ tự emit (topological)
        pack_resolution: Mapping pack ID → PackResolution
        template_mapping: Mapping MIR op_type → TemplateBinding
        stack_bindings: Mapping stack name → StackBinding
        validation_errors: Danh sách validation errors
        validation_warnings: Danh sách validation warnings
    """

    blueprint_id: str
    schema_version: str = "composition-plan-v1"
    emit_order: list[CompositionNode] = field(default_factory=list)
    pack_resolution: dict[str, PackResolution] = field(default_factory=dict)
    template_mapping: dict[str, TemplateBinding] = field(default_factory=dict)
    stack_bindings: dict[str, StackBinding] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def add_validation_error(self, error: str) -> None:
        """Thêm validation error vào plan."""
        self.validation_errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Thêm warning vào plan."""
        self.validation_warnings.append(warning)

    def is_valid(self) -> bool:
        """Kiểm tra plan có valid không (không có validation errors)."""
        return len(self.validation_errors) == 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dictionary."""
        return {
            "blueprint_id": self.blueprint_id,
            "schema_version": self.schema_version,
            "emit_order": [node.to_dict() for node in self.emit_order],
            "pack_resolution": {
                k: v.to_dict() for k, v in self.pack_resolution.items()
            },
            "template_mapping": {
                k: v.to_dict() for k, v in self.template_mapping.items()
            },
            "stack_bindings": {
                k: v.to_dict() for k, v in self.stack_bindings.items()
            },
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompositionPlan:
        """Tạo CompositionPlan từ dictionary."""
        emit_order = [
            CompositionNode.from_dict(n) for n in data.get("emit_order", [])
        ]
        pack_resolution = {
            k: PackResolution.from_dict(v)
            for k, v in data.get("pack_resolution", {}).items()
        }
        template_mapping = {
            k: TemplateBinding.from_dict(v)
            for k, v in data.get("template_mapping", {}).items()
        }
        stack_bindings = {
            k: StackBinding.from_dict(v)
            for k, v in data.get("stack_bindings", {}).items()
        }

        return cls(
            blueprint_id=data["blueprint_id"],
            schema_version=data.get("schema_version", "composition-plan-v1"),
            emit_order=emit_order,
            pack_resolution=pack_resolution,
            template_mapping=template_mapping,
            stack_bindings=stack_bindings,
            validation_errors=data.get("validation_errors", []),
            validation_warnings=data.get("validation_warnings", []),
        )
