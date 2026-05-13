"""
Pack File Contributions Loader — stack-aware.

Reads ``file_contributions`` from pack.yml and turns them into
``FileContributions`` — typed dataclasses that the code plan phase can
consume to build the file list without any hardcoded paths in ``code.py``.

Schema (in pack.yml)::

   file_contributions:
     # Emitted once per project
     infrastructure:
       - path: "app/database.py"
         file_type: "database"
         template: "cp08_database/database.py.jinja2"
         stacks: ["fastapi", "nestjs"]
         pack_emitter: null
     # Emitted once per entity in MIR metadata
     per_entity:
       - path_pattern: "app/repositories/{entity_snake}_repo.py"
         file_type: "repository"
         template: "cp08_database/repository.py.jinja2"
         stacks: ["fastapi", "nestjs"]
         pack_emitter: null  # null = raw Jinja2; string = pack_emitter key
         context_keys: ["entity"]  # which MIR metadata keys to inject

All stacks:
  - Backend:  fastapi, nestjs
  - Frontend: angular, react
  - Infra:    infrastructure  (special — uses stacks/infrastructure/ dir)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Canonical set of known stacks, grouped by role.
BACKEND_STACKS = {"fastapi", "nestjs"}
FRONTEND_STACKS = {"angular", "react"}
INFRA_STACK = "infrastructure"
ALL_STACKS = BACKEND_STACKS | FRONTEND_STACKS | {INFRA_STACK}


# ---------------------------------------------------------------------------
# Typed dataclasses
# ---------------------------------------------------------------------------


@dataclass
class InfrastructureFile:
    """A file emitted once per project (not per-entity)."""

    path: str
    file_type: str
    template: str
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    context_keys: list[str] = field(default_factory=list)


@dataclass
class PerEntityFile:
    """A file emitted once per entity in MIR metadata."""

    path_pattern: str  # e.g. "app/repositories/{entity_snake}_repo.py"
    file_type: str
    template: str
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    context_keys: list[str] = field(default_factory=list)


@dataclass
class FileContributions:
    """All file contributions declared by a single pack."""

    pack_id: str
    pack_internal_id: str
    infrastructure: list[InfrastructureFile] = field(default_factory=list)
    per_entity: list[PerEntityFile] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.infrastructure and not self.per_entity


# ---------------------------------------------------------------------------
# Placeholders
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _expand_path_pattern(pattern: str, entity: dict[str, Any]) -> str:
    """Replace placeholders in a path pattern with entity attributes.

    Supported placeholders (resolved from the raw entity dict):

    - ``entity_snake``  — snake_case (``Customer`` → ``customer``)
    - ``entity_pascal`` — as-is (``Customer``)
    - ``entity_camel``  — camelCase (``Customer`` → ``customer``)
    - ``entity_title``  — human-readable (``Customer``)
    """
    entity_id: str = entity.get("id", "Entity")

    snake = _pascal_to_snake(entity_id)
    camel = _snake_to_camel(snake)

    values = {
        "entity_snake": snake,
        "entity_pascal": entity_id,
        "entity_camel": camel,
        "entity_title": entity_id,
    }

    def _replacer(m: re.Match) -> str:
        key = m.group(1)
        if key in values:
            return str(values[key])
        return m.group(0)

    return _PLACEHOLDER_RE.sub(_replacer, pattern)


def _pascal_to_snake(name: str) -> str:
    """``Customer`` → ``customer``, ``OrderItem`` → ``order_item``."""
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _snake_to_camel(name: str) -> str:
    """``order_item`` → ``orderItem``."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


# ---------------------------------------------------------------------------
# Stack-aware Loader
# ---------------------------------------------------------------------------

# Canonical mapping of CP pack ID → folder name (matches resolver.py)
CP_ID_TO_INTERNAL: dict[str, str] = {
    "CP01": "cp01_domain_model",
    "CP02": "cp02_multi_tenant",
    "CP03": "cp03_auth",
    "CP04": "cp04_rbac",
    "CP05": "cp05_event_driven",
    "CP06": "cp06_api_gateway",
    "CP07": "cp07_iac",
    "CP08": "cp08_database",
    "CP09": "cp09_cache",
    "CP10": "cp10_search",
    "CP11": "cp11_file_media",
    "CP12": "cp12_notification",
    "CP13": "cp13_workflow_runtime",
    "CP14": "cp14_audit_compliance",
    "CP15": "cp15_observability",
    "CP16": "cp16_monitoring",
    "CP17": "cp17_bi_analytics",
    "CP18": "cp18_frontend_framework",
    "CP19": "cp19_ui_components",
    "CP20": "cp20_api_client",
    "CP51": "cp51_blueprint",
    "CP52": "cp52_invariant",
    "CP53": "cp53_domain_bridge",
}


class FileContributionsLoader:
    """Read ``file_contributions`` from pack.yml files on disk.

    Stack-aware: filters contributions by the target stack so that a
    ``code plan`` only includes files relevant to the selected backend,
    frontend, or infra stack.
    """

    def __init__(self, emitters_core_dir: Path | None = None):
        if emitters_core_dir is None:
            # midicoder/pipeline/ → midicoder/ → emitters/core/
            self._base_dir = Path(__file__).resolve().parent.parent / "emitters" / "core"
        else:
            self._base_dir = emitters_core_dir

        # TODO[G5]: DP + RX pack loading (SoT §6.1 emit order: CPs → DPs → RXs)
        # Currently only emitters/core/ (CP packs) is loaded.
        # Future: add emitters/domain/ (DP) and emitters/regulatory/ (RX) dirs.
        # DP packs: domain-specific entities, commands, queries, workflows, invariants
        # RX packs: obligations, guards, gates that inject into CP/DP modules
        self._domain_dir: Path | None = None
        self._regulatory_dir: Path | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(
        self,
        pack_internal_id: str,
        pack_id: str = "",
        stack: str | None = None,
    ) -> FileContributions:
        """Load contributions for a single pack, optionally filtered by stack.

        Args:
            pack_internal_id: Folder name (e.g. ``cp08_database``).
            pack_id: Pack id (e.g. ``CP08``).
            stack: If set, only keep entries whose ``stacks`` list contains
                   the given value.

        Returns:
            ``FileContributions`` — may be empty.
        """
        pack_yml = self._base_dir / pack_internal_id / "pack.yml"
        if not pack_yml.exists():
            return FileContributions(pack_id=pack_id, pack_internal_id=pack_internal_id)

        data = _load_yaml(pack_yml)
        raw = data.get("file_contributions", {})
        if not raw:
            return FileContributions(pack_id=pack_id, pack_internal_id=pack_internal_id)

        infra = [_parse_infrastructure(f) for f in raw.get("infrastructure", [])]
        per_entity = [_parse_per_entity(f) for f in raw.get("per_entity", [])]

        # Filter by stack if requested
        if stack:
            infra = [e for e in infra if stack in e.stacks]
            per_entity = [e for e in per_entity if stack in e.stacks]

        return FileContributions(
            pack_id=pack_id,
            pack_internal_id=pack_internal_id,
            infrastructure=infra,
            per_entity=per_entity,
        )

    def load_all(
        self,
        pack_map: dict[str, str] | None = None,
        stack: str | None = None,
    ) -> list[FileContributions]:
        """Load contributions for multiple packs.

        Args:
            pack_map: ``{pack_id: internal_id}``.  If ``None``, loads ALL
                      known CP packs.
            stack: Optional stack filter.

        Returns:
            List of non-empty ``FileContributions``.
        """
        if pack_map is None:
            pack_map = dict(CP_ID_TO_INTERNAL)

        contributions = []
        for pack_id, internal_id in pack_map.items():
            fc = self.load(pack_internal_id=internal_id, pack_id=pack_id, stack=stack)
            if not fc.is_empty:
                contributions.append(fc)
        return contributions

    # ------------------------------------------------------------------
    # Expansion helpers — produce file plan dicts for code.py
    # ------------------------------------------------------------------

    @staticmethod
    def expand_infrastructure(
        contributions: FileContributions,
        mir_metadata: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Expand infrastructure entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            mir_metadata: Optional MIR metadata dict for ``context_keys``
                          resolution.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        meta = mir_metadata or {}
        for entry in contributions.infrastructure:
            ctx = {}
            for key in entry.context_keys:
                if key in meta:
                    ctx[key] = meta[key]

            metadata: dict[str, Any] = {}
            if entry.pack_emitter:
                metadata["pack_emitter"] = entry.pack_emitter
                metadata["stack"] = entry.stacks[0] if entry.stacks else "fastapi"

            files.append({
                "path": entry.path,
                "type": entry.file_type,
                "template": entry.template,
                "context": ctx,
                "metadata": metadata,
            })
        return files

    @staticmethod
    def expand_per_entity(
        contributions: FileContributions,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Expand ``per_entity`` entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            entities: Raw entity dicts from ``MIR.metadata.entities``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_entity:
            for entity in entities:
                path = _expand_path_pattern(entry.path_pattern, entity)

                ctx = {"entity": entity, "all_entities": entities}
                # Inject additional context keys if declared
                for key in entry.context_keys:
                    if key in entity:
                        ctx[key] = entity[key]

                metadata: dict[str, Any] = {}
                if entry.pack_emitter:
                    metadata["pack_emitter"] = entry.pack_emitter
                    metadata["stack"] = entry.stacks[0] if entry.stacks else "fastapi"

                files.append({
                    "path": path,
                    "type": entry.file_type,
                    "template": entry.template,
                    "context": ctx,
                    "metadata": metadata,
                })
        return files

    # ------------------------------------------------------------------
    # Aggregate helper — used by code.py
    # ------------------------------------------------------------------

    def resolve_all_infrastructure(
        self,
        stack: str,
        mir_metadata: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Load infrastructure files from ALL packs for the given stack.

        Returns deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack):
            for f in self.expand_infrastructure(fc, mir_metadata):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_entity(
        self,
        stack: str,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Load per-entity files from ALL packs for the given stack.

        Returns deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack):
            for f in self.expand_per_entity(fc, entities):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result


# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # pack.yml wraps everything under a "pack:" key
    if "pack" in data and isinstance(data["pack"], dict):
        return data["pack"]
    return data


def _parse_infrastructure(raw: dict[str, Any]) -> InfrastructureFile:
    return InfrastructureFile(
        path=raw["path"],
        file_type=raw["file_type"],
        template=raw["template"],
        stacks=raw.get("stacks", ["fastapi"]),
        pack_emitter=raw.get("pack_emitter"),
        context_keys=raw.get("context_keys", []),
    )


def _parse_per_entity(raw: dict[str, Any]) -> PerEntityFile:
    return PerEntityFile(
        path_pattern=raw["path_pattern"],
        file_type=raw["file_type"],
        template=raw["template"],
        stacks=raw.get("stacks", ["fastapi"]),
        pack_emitter=raw.get("pack_emitter"),
        context_keys=raw.get("context_keys", []),
    )


__all__ = [
    "FileContributionsLoader",
    "FileContributions",
    "InfrastructureFile",
    "PerEntityFile",
    "_expand_path_pattern",
    "BACKEND_STACKS",
    "FRONTEND_STACKS",
    "INFRA_STACK",
    "ALL_STACKS",
    "CP_ID_TO_INTERNAL",
]
