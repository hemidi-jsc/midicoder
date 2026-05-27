"""
Taxonomy Registry — Programmatic access to industry/taxonomy.yml.

Cung cấp:
- Load taxonomy từ YAML file
- Query packs theo type, status, phase, category
- Resolve dependencies (DAG)
- Validate blueprints against taxonomy
- Detect dependency cycles

Sử dụng:
    registry = TaxonomyRegistry.load("industry/taxonomy.yml")
    stable_p0 = registry.find_packs(type="core_pack", status="stable", phase="P0")
    dependents = registry.find_dependents("CP01")
    report = registry.validate_blueprint(blueprint_data)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class Pack:
    """Representation of a single pack (CP, DP, or RX)."""

    id: str
    name: str
    pack_type: str  # "core_pack" | "domain_pack" | "regulatory_overlay"
    version: str = "1.0.0"
    description: str = ""
    category: str = ""
    status: str = "planned"
    phase: Optional[str] = None
    internal_id: Optional[str] = None
    definitions_count: int = 0
    obligations_count: int = 0
    depends_on: list[str] = field(default_factory=list)
    industries_using: list[str] = field(default_factory=list)
    industries_requiring: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.pack_type,
            "version": self.version,
            "status": self.status,
            "phase": self.phase,
            "category": self.category,
            "depends_on": self.depends_on,
        }


@dataclass
class ValidationIssue:
    """Single validation issue found during blueprint validation."""

    rule: str
    severity: str
    message: str
    pack_id: Optional[str] = None


class TaxonomyRegistry:
    """
    Programmatic registry for Midicoder taxonomy.

    Loads taxonomy.yml and provides query, dependency resolution,
    and blueprint validation capabilities.
    """

    def __init__(self, raw_data: dict[str, Any]):
        self._raw = raw_data
        self._packs: dict[str, Pack] = {}
        self._validation_rules: list[dict[str, str]] = []
        self._status_transitions: dict[str, list[str]] = {}
        self._build_index()

    @classmethod
    def load(cls, taxonomy_path: str | Path) -> TaxonomyRegistry:
        """Load taxonomy from YAML file."""
        path = Path(taxonomy_path)
        if not path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    def _build_index(self):
        """Build pack index from raw taxonomy data."""
        # Core Packs
        for cp_raw in self._raw.get("core_packs", []):
            pack = Pack(
                id=cp_raw["id"],
                name=cp_raw["name"],
                pack_type="core_pack",
                version=cp_raw.get("version", "1.0.0"),
                description=cp_raw.get("description", ""),
                category=cp_raw.get("category", ""),
                status=cp_raw.get("status", "planned"),
                phase=cp_raw.get("phase"),
                internal_id=cp_raw.get("internal_id"),
                definitions_count=cp_raw.get("definitions_count", 0),
                obligations_count=cp_raw.get("obligations_count", 0),
                depends_on=cp_raw.get("depends_on", []),
                raw=cp_raw,
            )
            self._packs[pack.id] = pack

        # Domain Packs
        for dp_raw in self._raw.get("domain_packs", []):
            pack = Pack(
                id=dp_raw["id"],
                name=dp_raw["name"],
                pack_type="domain_pack",
                version=dp_raw.get("version", "1.0.0"),
                description=dp_raw.get("description", ""),
                category=dp_raw.get("category", ""),
                status=dp_raw.get("status", "planned"),
                phase=dp_raw.get("phase"),
                depends_on=dp_raw.get("depends_on", []),
                industries_using=dp_raw.get("industries_using", []),
                raw=dp_raw,
            )
            self._packs[pack.id] = pack

        # Regulatory Overlays
        for rx_raw in self._raw.get("regulatory_overlays", []):
            pack = Pack(
                id=rx_raw["id"],
                name=rx_raw["name"],
                pack_type="regulatory_overlay",
                version=rx_raw.get("version", "1.0.0"),
                description=rx_raw.get("description", ""),
                category=rx_raw.get("category", ""),
                status=rx_raw.get("status", "planned"),
                phase=rx_raw.get("phase"),
                depends_on=rx_raw.get("depends_on", []),
                industries_requiring=rx_raw.get("industries_requiring", []),
                obligations=rx_raw.get("obligations", []),
                raw=rx_raw,
            )
            self._packs[pack.id] = pack

        # Validation rules
        self._validation_rules = self._raw.get("validation_rules", [])

        # Status transitions
        self._status_transitions = self._raw.get("status_transitions", {})

    # ========================================================================
    # Query API
    # ========================================================================

    def find_packs(
        self,
        pack_type: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[Pack]:
        """Query packs by filters."""
        results = []
        for pack in self._packs.values():
            if pack_type and pack.pack_type != pack_type:
                continue
            if status and pack.status != status:
                continue
            if phase and pack.phase != phase:
                continue
            if category and pack.category != category:
                continue
            results.append(pack)
        return results

    def get_pack(self, pack_id: str) -> Optional[Pack]:
        """Get a single pack by ID."""
        return self._packs.get(pack_id)

    def get_all_packs(self) -> list[Pack]:
        """Get all packs."""
        return list(self._packs.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get taxonomy statistics."""
        return self._raw.get("statistics", {})

    # ========================================================================
    # Dependency Resolution
    # ========================================================================

    def find_dependents(self, pack_id: str) -> list[Pack]:
        """Find all packs that depend on a given pack."""
        if pack_id not in self._packs:
            raise KeyError(f"Pack not found: {pack_id}")
        return [p for p in self._packs.values() if pack_id in p.depends_on]

    def resolve_dependencies(self, pack_id: str) -> list[str]:
        """Resolve full dependency chain for a pack (BFS)."""
        if pack_id not in self._packs:
            raise KeyError(f"Pack not found: {pack_id}")
        visited: set[str] = set()
        queue = [pack_id]
        result = []
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if current != pack_id:
                result.append(current)
            pack = self._packs.get(current)
            if pack:
                for dep in pack.depends_on:
                    if dep not in visited:
                        queue.append(dep)
        return result

    def detect_cycles(self) -> list[list[str]]:
        """Detect dependency cycles in the taxonomy."""
        cycles = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            pack = self._packs.get(node)
            if pack:
                for dep in pack.depends_on:
                    if dep not in visited:
                        dfs(dep)
                    elif dep in rec_stack:
                        cycle_start = path.index(dep)
                        cycles.append(path[cycle_start:] + [dep])
            path.pop()
            rec_stack.discard(node)

        for pid in self._packs:
            if pid not in visited:
                dfs(pid)
        return cycles

    # ========================================================================
    # Status Validation
    # ========================================================================

    def is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        return to_status in self._status_transitions.get(from_status, [])

    def validate_pack_status(self, pack_id: str, new_status: str) -> list[ValidationIssue]:
        """Validate a status change for a pack."""
        issues = []
        pack = self._packs.get(pack_id)
        if not pack:
            issues.append(ValidationIssue("pack_exists", "error", f"Pack not found: {pack_id}", pack_id))
            return issues
        if not self.is_valid_transition(pack.status, new_status):
            allowed = self._status_transitions.get(pack.status, [])
            issues.append(ValidationIssue(
                "status_transition", "error",
                f"Cannot transition from '{pack.status}' to '{new_status}'. Allowed: {allowed}",
                pack_id))
        if new_status == "stable":
            for dep_id in pack.depends_on:
                dep_pack = self._packs.get(dep_id)
                if dep_pack and dep_pack.status == "planned":
                    issues.append(ValidationIssue(
                        "stable_cannot_depend_on_planned", "error",
                        f"Pack {pack_id} (stable) depends on {dep_id} (planned)",
                        pack_id))
        return issues

    # ========================================================================
    # Pack Resolution (DSL → MIR → Template wiring)
    # ========================================================================

    def resolve_packs_for_operations(self, operation_types: list[str]) -> list[Pack]:
        """
        Resolve packs needed for a set of MIR operation types.

        This is the LINK between MIR operations and Pack emitters.
        MIR op_type 'create_record' → query packs for capabilities_provided → get pack.

        Args:
            operation_types: List of MIR op_type strings (e.g., ['create_record', 'query_records'])

        Returns:
            List of Pack objects that provide the requested operations
        """
        required_packs: dict[str, Pack] = {}

        for pack in self._packs.values():
            caps_provided = pack.raw.get("capabilities_provided", [])
            for op_type in operation_types:
                if op_type in caps_provided and pack.id not in required_packs:
                    required_packs[pack.id] = pack

        return list(required_packs.values())

    # ========================================================================
    # Blueprint / Pack Combination Validation
    # ========================================================================

    def validate_pack_combination(self, pack_ids: dict[str, Any]) -> list[ValidationIssue]:
        """
        Validate a pack combination against taxonomy rules.

        Replaces old validate_blueprint(). Now validates CP/DP/RX combinations
        for the 3-layer pipeline (DSL → MIR → Template).
        """
        issues: list[ValidationIssue] = []
        cp_ids = {p.get("id") for p in pack_ids.get("core_packs", [])}
        dp_ids = {p.get("id") for p in pack_ids.get("domain_packs", [])}
        rx_ids = {p.get("id") for p in pack_ids.get("regulatory_overlays", [])}
        all_bp_ids = cp_ids | dp_ids | rx_ids

        # all_referenced_packs_exist
        for pid in all_bp_ids:
            if pid and pid not in self._packs:
                issues.append(ValidationIssue("all_referenced_packs_exist", "error",
                    f"Referenced pack '{pid}' does not exist in taxonomy", pid))

        # blueprint_must_include_p0_core_packs
        p0_ids = {p.id for p in self.find_packs(pack_type="core_pack", phase="P0")}
        missing_p0 = p0_ids - cp_ids
        if missing_p0:
            issues.append(ValidationIssue("blueprint_must_include_p0_core_packs", "error",
                f"Missing P0 core packs: {missing_p0}"))

        # universal_regulatory_overlays_included
        missing_rx = {"RX01", "RX11"} - rx_ids
        if missing_rx:
            issues.append(ValidationIssue("universal_regulatory_overlays_included", "error",
                f"Missing universal regulatory overlays: {missing_rx}"))

        # no_dependency_cycles
        for cycle in self.detect_cycles():
            issues.append(ValidationIssue("no_dependency_cycles", "error",
                f"Dependency cycle detected: {' -> '.join(cycle)}"))

        # stable_cannot_depend_on_planned
        for pack in self._packs.values():
            if pack.status == "stable":
                for dep_id in pack.depends_on:
                    dep_pack = self._packs.get(dep_id)
                    if dep_pack and dep_pack.status == "planned":
                        issues.append(ValidationIssue("stable_cannot_depend_on_planned", "error",
                            f"Stable pack {pack.id} depends on planned pack {dep_id}", pack.id))

        # dependency_order_preserved
        phase_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        for pack in self._packs.values():
            if pack.phase and pack.pack_type == "core_pack":
                pack_num = phase_order.get(pack.phase, -1)
                for dep_id in pack.depends_on:
                    dep_pack = self._packs.get(dep_id)
                    if dep_pack and dep_pack.phase:
                        dep_num = phase_order.get(dep_pack.phase, -1)
                        if pack_num < dep_num:
                            issues.append(ValidationIssue("dependency_order_preserved", "error",
                                f"{pack.id} (phase {pack.phase}) depends on {dep_id} (phase {dep_pack.phase})",
                                pack.id))
        return issues

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_json(self, indent: int = 2) -> str:
        """Export taxonomy as JSON string."""
        return json.dumps(self._raw, indent=indent, ensure_ascii=False)

    def __len__(self) -> int:
        return len(self._packs)

    def __contains__(self, pack_id: str) -> bool:
        return pack_id in self._packs

    def __repr__(self) -> str:
        return f"TaxonomyRegistry(packs={len(self._packs)})"