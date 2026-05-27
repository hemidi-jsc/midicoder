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

# Import stack constants và CP_ID_TO_INTERNAL từ single source
from midicoder.contracts.registry import (
    ALL_STACKS,
    BACKEND_STACKS,
    CP_ID_TO_INTERNAL,
    FRONTEND_STACKS,
    INFRA_STACK,
)
from midicoder.pipeline.config import resolve_render_context


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
class PerCommandFile:
    """A file emitted once per command in MIR metadata."""

    path_pattern: str  # e.g. "app/commands/{command_snake}_handler.py"
    file_type: str
    template: str
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    context_keys: list[str] = field(default_factory=list)


@dataclass
class PerQueryFile:
    """A file emitted once per query in MIR metadata."""

    path_pattern: str  # e.g. "app/queries/{query_snake}_handler.py"
    file_type: str
    template: str
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    context_keys: list[str] = field(default_factory=list)


@dataclass
class PerUIComponentFile:
    """A file emitted once per entity × component_type combo (CP19).

    Iterates over ``entities × component_types`` so that each entity
    gets a set of UI component files (form, table, card list, dialog, …).
    """

    path_pattern: str  # e.g. "src/components/{entity_pascal}/Form{entity_pascal}.tsx"
    file_type: str
    template: str
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    component_types: list[str] = field(default_factory=list)
    context_keys: list[str] = field(default_factory=list)


@dataclass
class PerWidgetFile:
    """A file emitted once per widget type (CP22 realtime).

    Iterates over ``component_types`` (widget types like presence,
    live_feed, live_counter, live_cursor, notification_toast) so that
    each widget type gets its own file (hook/service/component).
    """

    path_pattern: str  # e.g. "{widget_pascal}.tsx" or "{widget_kebab}.component.ts"
    file_type: str = "widget"
    template: str = ""
    stacks: list[str] = field(default_factory=list)
    pack_emitter: str | None = None
    component_types: list[str] = field(default_factory=list)
    context_keys: list[str] = field(default_factory=list)


@dataclass
class FileContributions:
    """All file contributions declared by a single pack."""

    pack_id: str
    pack_internal_id: str
    infrastructure: list[InfrastructureFile] = field(default_factory=list)
    per_entity: list[PerEntityFile] = field(default_factory=list)
    per_command: list[PerCommandFile] = field(default_factory=list)
    per_query: list[PerQueryFile] = field(default_factory=list)
    per_ui_component: list[PerUIComponentFile] = field(default_factory=list)
    per_widget: list[PerWidgetFile] = field(default_factory=list)
    status: str = "stable"

    @property
    def is_empty(self) -> bool:
        return not (
            self.infrastructure
            or self.per_entity
            or self.per_command
            or self.per_query
            or self.per_ui_component
            or self.per_widget
        )


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


def _snake_to_pascal(name: str) -> str:
    """``live_feed`` → ``LiveFeed``, ``order_item`` → ``OrderItem``."""
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts)


# ---------------------------------------------------------------------------
# Stack-aware Loader
# ---------------------------------------------------------------------------

# CP_ID_TO_INTERNAL imported from midicoder.contracts.registry (single source)


class FileContributionsLoader:
    """Read ``file_contributions`` from pack.yml files on disk.

    Stack-aware: filters contributions by the target stack so that a
    ``code plan`` only includes files relevant to the selected backend,
    frontend, or infra stack.
    """

    def __init__(self, packs_dir: Path | None = None):
        if packs_dir is None:
            # midicoder/pipeline/ → midicoder/ → packs/
            self._base_dir = Path(__file__).resolve().parent.parent / "packs"
        else:
            self._base_dir = packs_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(
        self,
        pack_internal_id: str,
        pack_id: str = "",
        stack: str | None = None,
        status_filter: str | None = None,
    ) -> FileContributions:
        """Load contributions for a single pack, optionally filtered by stack.

        Args:
            pack_internal_id: Folder name (e.g. ``cp08_database``).
            pack_id: Pack id (e.g. ``CP08``).
            stack: If set, only keep entries whose ``stacks`` list contains
                   the given value.
            status_filter: If set, skip packs whose ``status`` in pack.yml
                           does not match (e.g. ``"stable"`` excludes
                           ``"experimental"`` and ``"deprecated"`` packs).

        Returns:
            ``FileContributions`` — may be empty.
        """
        pack_yml = self._base_dir / pack_internal_id / "pack.yml"
        if not pack_yml.exists():
            return FileContributions(pack_id=pack_id, pack_internal_id=pack_internal_id)

        data = _load_yaml(pack_yml)
        pack_status = data.get("status", "stable")

        # Filter by status if requested
        if status_filter and pack_status != status_filter:
            return FileContributions(pack_id=pack_id, pack_internal_id=pack_internal_id)

        raw = data.get("file_contributions", {})
        if not raw:
            return FileContributions(
                pack_id=pack_id,
                pack_internal_id=pack_internal_id,
                status=pack_status,
            )

        infra = [_parse_infrastructure(f) for f in raw.get("infrastructure", [])]
        per_entity = [_parse_per_entity(f) for f in raw.get("per_entity", [])]
        per_command = [_parse_per_command(f) for f in raw.get("per_command", [])]
        per_query = [_parse_per_query(f) for f in raw.get("per_query", [])]
        per_ui_component = [_parse_per_ui_component(f) for f in raw.get("per_ui_component", [])]
        per_widget = [_parse_per_widget(f) for f in raw.get("per_widget", [])]

        # Filter by stack if requested
        if stack:
            infra = [e for e in infra if stack in e.stacks]
            per_entity = [e for e in per_entity if stack in e.stacks]
            per_command = [e for e in per_command if stack in e.stacks]
            per_query = [e for e in per_query if stack in e.stacks]
            per_ui_component = [e for e in per_ui_component if stack in e.stacks]
            per_widget = [e for e in per_widget if stack in e.stacks]

        return FileContributions(
            pack_id=pack_id,
            pack_internal_id=pack_internal_id,
            infrastructure=infra,
            per_entity=per_entity,
            per_command=per_command,
            per_query=per_query,
            per_ui_component=per_ui_component,
            per_widget=per_widget,
            status=pack_status,
        )

    def load_all(
        self,
        pack_map: dict[str, str] | None = None,
        stack: str | None = None,
        status_filter: str | None = None,
    ) -> list[FileContributions]:
        """Load contributions for all Core Packs (CP).

        Args:
            pack_map: ``{pack_id: internal_id}``.  If ``None``, loads ALL
                      known CP packs.
            stack: Optional stack filter.
            status_filter: If set, skip packs whose ``status`` does not match.

        Returns:
            List of non-empty ``FileContributions``.
        """
        if pack_map is None:
            pack_map = dict(CP_ID_TO_INTERNAL)

        contributions = []
        for pack_id, internal_id in pack_map.items():
            fc = self.load(
                pack_internal_id=internal_id,
                pack_id=pack_id,
                stack=stack,
                status_filter=status_filter,
            )
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
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand infrastructure entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            mir_metadata: Optional MIR metadata dict for ``context_keys``
                          resolution.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        meta = mir_metadata or {}

        for entry in contributions.infrastructure:
            ctx = {}
            # EU-0.1: inject render_context (infrastructure → default {})
            # EU-0.2: merge với user config infrastructure overrides
            if user_config:
                ctx["render_context"] = user_config.get("render", {}).get("infrastructure", {})
            else:
                ctx["render_context"] = {}
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
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand ``per_entity`` entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            entities: Raw entity dicts from ``MIR.metadata.entities``.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_entity:
            for entity in entities:
                path = _expand_path_pattern(entry.path_pattern, entity)

                ctx = {"entity": entity, "all_entities": entities}
                # EU-0.1: inject render_context từ entity vào context
                # EU-0.2: merge với user config (priority: DSL > per_entity > defaults)
                entity_rc = entity.get("render_context", {})
                if user_config:
                    entity_id = entity.get("id", "")
                    ctx["render_context"] = resolve_render_context(entity_id, entity_rc, user_config)
                else:
                    ctx["render_context"] = entity_rc
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

    @staticmethod
    def expand_per_command(
        contributions: FileContributions,
        commands: list[dict[str, Any]],
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand ``per_command`` entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            commands: Raw command dicts from ``MIR.metadata.commands``.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_command:
            for command in commands:
                cmd_id: str = command.get("id", "Command")
                snake = _pascal_to_snake(cmd_id)
                path = entry.path_pattern.replace("{command_snake}", snake)
                path = path.replace("{command_pascal}", cmd_id)

                ctx = {"command": command, "all_commands": commands}
                # EU-0.1: inject render_context từ command vào context
                # EU-0.2: merge với user config
                cmd_rc = command.get("render_context", {})
                if user_config:
                    ctx["render_context"] = resolve_render_context(cmd_id, cmd_rc, user_config)
                else:
                    ctx["render_context"] = cmd_rc
                for key in entry.context_keys:
                    if key in command:
                        ctx[key] = command[key]

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

    @staticmethod
    def expand_per_query(
        contributions: FileContributions,
        queries: list[dict[str, Any]],
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand ``per_query`` entries into concrete file plans.

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            queries: Raw query dicts from ``MIR.metadata.queries``.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_query:
            for query in queries:
                query_id: str = query.get("id", "Query")
                snake = _pascal_to_snake(query_id)
                path = entry.path_pattern.replace("{query_snake}", snake)
                path = path.replace("{query_pascal}", query_id)

                ctx = {"query": query, "all_queries": queries}
                # EU-0.1: inject render_context từ query vào context
                # EU-0.2: merge với user config
                query_rc = query.get("render_context", {})
                if user_config:
                    ctx["render_context"] = resolve_render_context(query_id, query_rc, user_config)
                else:
                    ctx["render_context"] = query_rc
                for key in entry.context_keys:
                    if key in query:
                        ctx[key] = query[key]

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

    @staticmethod
    def expand_per_ui_component(
        contributions: FileContributions,
        entities: list[dict[str, Any]],
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand ``per_ui_component`` entries into concrete file plans.

        Iterates over ``entities × component_types`` so that each entity
        gets a set of UI component files (form, table, card list, dialog, …).

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            entities: Raw entity dicts from ``MIR.metadata.entities``.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_ui_component:
            for entity in entities:
                # Resolve path with entity placeholders (entity_pascal, entity_snake, etc.)
                path = _expand_path_pattern(entry.path_pattern, entity)

                # Build component list from entity — one spec per declared component_type
                comp_types = entry.component_types or ["form_field", "data_table", "card_list", "dialog"]
                ctx = {
                    "entity": entity,
                    "all_entities": entities,
                    "components": comp_types,
                }
                # EU-0.1: inject render_context từ entity vào context
                # EU-0.2: merge với user config
                entity_rc = entity.get("render_context", {})
                if user_config:
                    entity_id = entity.get("id", "")
                    ctx["render_context"] = resolve_render_context(entity_id, entity_rc, user_config)
                else:
                    ctx["render_context"] = entity_rc
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

    @staticmethod
    def expand_per_widget(
        contributions: FileContributions,
        channels: list[dict[str, Any]] | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Expand ``per_widget`` entries into concrete file plans.

        Iterates over ``component_types`` (widget types) so that each
        widget type gets one file spec. Unlike per_ui_component which
        iterates entities × component_types, per_widget iterates only
        component_types (widgets are global, not per-entity).

        Args:
            contributions: Loaded ``FileContributions`` for a pack.
            channels: Optional channel specs from CP22 parser output.
            user_config: Optional user config from ``midicoder.config.yml``.

        Returns:
            List of file plan dicts.
        """
        files: list[dict[str, Any]] = []
        for entry in contributions.per_widget:
            comp_types = entry.component_types or []
            for comp_type in comp_types:
                # Resolve widget path pattern
                # Support {widget_pascal}, {widget_kebab}, {widget_snake}
                widget_pascal = _snake_to_pascal(comp_type)
                widget_kebab = comp_type.replace("_", "-")
                widget_snake = comp_type

                path = entry.path_pattern
                path = path.replace("{widget_pascal}", widget_pascal)
                path = path.replace("{widget_kebab}", widget_kebab)
                path = path.replace("{widget_snake}", widget_snake)

                ctx: dict[str, Any] = {
                    "widget_type": comp_type,
                    "widget_pascal": widget_pascal,
                    "widget_kebab": widget_kebab,
                }
                # EU-0.1: inject render_context (widget không có entity source → default {})
                # EU-0.2: widget dùng infrastructure overrides nếu có
                if user_config:
                    ctx["render_context"] = user_config.get("render", {}).get("infrastructure", {})
                else:
                    ctx["render_context"] = {}
                if channels:
                    ctx["channels"] = channels
                    ctx["channel_topics"] = [ch.get("event_topic", ch.get("channel_id", "")) for ch in channels]

                # Inject additional context keys
                for key in entry.context_keys:
                    if key in ctx:
                        ctx[key] = ctx[key]

                metadata: dict[str, Any] = {}
                if entry.pack_emitter:
                    metadata["pack_emitter"] = entry.pack_emitter
                    metadata["stack"] = entry.stacks[0] if entry.stacks else "react"

                files.append({
                    "path": path,
                    "type": entry.file_type,
                    "template": entry.template,
                    "context": ctx,
                    "metadata": metadata,
                })
        return files

    # ------------------------------------------------------------------

    def resolve_all_infrastructure(
        self,
        stack: str,
        mir_metadata: dict | None = None,
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load infrastructure files from ALL packs for the given stack.

        Returns deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_infrastructure(fc, mir_metadata, user_config=user_config):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_entity(
        self,
        stack: str,
        entities: list[dict[str, Any]],
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load per-entity files from ALL packs for the given stack.

        Returns deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_per_entity(fc, entities, user_config=user_config):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_command(
        self,
        stack: str,
        commands: list[dict[str, Any]],
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load per-command files from ALL packs for the given stack."""
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_per_command(fc, commands, user_config=user_config):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_query(
        self,
        stack: str,
        queries: list[dict[str, Any]],
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load per-query files from ALL packs for the given stack."""
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_per_query(fc, queries, user_config=user_config):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_ui_component(
        self,
        stack: str,
        entities: list[dict[str, Any]],
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load per-ui-component files from ALL packs for the given stack.

        Iterates over entities × component_types per pack declaration.

        Args:
            stack: Target stack (e.g. ``"react"``, ``"angular"``).
            entities: Raw entity dicts from ``MIR.metadata.entities``.
            status_filter: If set, skip packs whose ``status`` does not match.

        Returns:
            Deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_per_ui_component(fc, entities, user_config=user_config):
                if f["path"] not in seen:
                    seen.add(f["path"])
                    result.append(f)
        return result

    def resolve_all_per_widget(
        self,
        stack: str,
        channels: list[dict[str, Any]] | None = None,
        status_filter: str | None = None,
        user_config: dict | None = None,  # EU-0.2
    ) -> list[dict[str, Any]]:
        """Load per-widget files from ALL packs for the given stack.

        Iterates over component_types (widget types) per pack declaration.

        Args:
            stack: Target stack (e.g. ``"react"``, ``"angular"``).
            channels: Optional channel specs from CP22.
            status_filter: If set, skip packs whose ``status`` does not match.

        Returns:
            Deduplicated list of file plan dicts.
        """
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for fc in self.load_all(stack=stack, status_filter=status_filter):
            for f in self.expand_per_widget(fc, channels, user_config=user_config):
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
        file_type=raw.get("file_type", "infrastructure"),
        template=raw.get("template", ""),
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


def _parse_per_command(raw: dict[str, Any]) -> PerCommandFile:
    return PerCommandFile(
        path_pattern=raw["path_pattern"],
        file_type=raw["file_type"],
        template=raw["template"],
        stacks=raw.get("stacks", ["fastapi"]),
        pack_emitter=raw.get("pack_emitter"),
        context_keys=raw.get("context_keys", []),
    )


def _parse_per_query(raw: dict[str, Any]) -> PerQueryFile:
    return PerQueryFile(
        path_pattern=raw["path_pattern"],
        file_type=raw["file_type"],
        template=raw["template"],
        stacks=raw.get("stacks", ["fastapi"]),
        pack_emitter=raw.get("pack_emitter"),
        context_keys=raw.get("context_keys", []),
    )


def _parse_per_ui_component(raw: dict[str, Any]) -> PerUIComponentFile:
    return PerUIComponentFile(
        path_pattern=raw["path_pattern"],
        file_type=raw["file_type"],
        template=raw["template"],
        stacks=raw.get("stacks", ["fastapi"]),
        pack_emitter=raw.get("pack_emitter"),
        component_types=raw.get("component_types", ["form_field", "data_table", "card_list", "dialog"]),
        context_keys=raw.get("context_keys", []),
    )


def _parse_per_widget(raw: dict[str, Any]) -> PerWidgetFile:
    return PerWidgetFile(
        path_pattern=raw["path_pattern"],
        file_type=raw.get("file_type", "widget"),
        template=raw.get("template", ""),
        stacks=raw.get("stacks", []),
        pack_emitter=raw.get("pack_emitter"),
        component_types=raw.get("component_types", []),
        context_keys=raw.get("context_keys", []),
    )


__all__ = [
    "FileContributionsLoader",
    "FileContributions",
    "InfrastructureFile",
    "PerEntityFile",
    "PerCommandFile",
    "PerQueryFile",
    "PerUIComponentFile",
    "PerWidgetFile",
    "_expand_path_pattern",
    "_snake_to_pascal",
    "BACKEND_STACKS",
    "FRONTEND_STACKS",
    "INFRA_STACK",
    "ALL_STACKS",
    "CP_ID_TO_INTERNAL",
]
