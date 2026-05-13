"""
DSL Parser Module.

Module này cung cấp DSLParser để parse YAML contract strings → ProjectionTree:
- Parse YAML content string (từ SQLite artifacts) thành ProjectionNodes
- Hỗ trợ 7 categories: entities, commands, queries, events, workflows, value_objects, guards
- Build ProjectionTree từ dictionary của YAML strings

Sử dụng:
    from midicoder.pipeline.dsl_parser import DSLParser
    
    parser = DSLParser()
    nodes = parser.parse_yaml_string(yaml_content, "entities")
    # Hoặc build tree từ nhiều categories:
    tree = parser.build_projection_tree({"entities": yaml1, "commands": yaml2, ...})

Author: Midicoder Team
Version: 2.0.0 (Refactored: string-based parsing, no filesystem)
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.dsl.projection import ProjectionNode, ProjectionTree, NodeKind


# ============================================================================
# Category → NodeKind mapping
# ============================================================================

_CATEGORY_TO_NODE_KIND = {
    "entities": NodeKind.ENTITY,
    "commands": NodeKind.COMMAND,
    "queries": NodeKind.QUERY,
    "events": NodeKind.EVENT,
    "workflows": NodeKind.WORKFLOW,
    "value_objects": NodeKind.VALUE_OBJECT,
    "guards": NodeKind.GUARD,
    "roles": NodeKind.ROLE,
}

# Key trong YAML dict tương ứng mỗi category
_CATEGORY_YAML_KEY = {
    "entities": "entities",
    "commands": "commands",
    "queries": "queries",
    "events": "events",
    "workflows": "workflows",
    "value_objects": "value_objects",
    "guards": "guards",
    "roles": "roles",
}


class DSLParser:
    """
    Unified DSL Parser cho Midicoder contracts.

    Parse YAML content strings (từ SQLite artifacts) thành ProjectionTree.
    Không sử dụng filesystem — chỉ parse YAML strings.

    Supported categories:
        - entities
        - commands
        - queries
        - events
        - workflows
        - value_objects
        - guards
        - roles
    """

    def __init__(self) -> None:
        """Khởi tạo DSLParser."""
        pass

    def parse_yaml_string(self, yaml_content: str, category: str) -> list[ProjectionNode]:
        """
        Parse YAML content string thành list ProjectionNodes.

        Args:
            yaml_content: YAML content string
            category: Loại contract (entities, commands, queries, events, workflows, value_objects, guards)

        Returns:
            List của ProjectionNode

        Raises:
            ValueError: Nếu category không hợp lệ
        """
        if category not in _CATEGORY_TO_NODE_KIND:
            raise ValueError(f"Unknown contract type: {category}. "
                           f"Supported: {list(_CATEGORY_TO_NODE_KIND.keys())}")

        # Map category → parser function
        parser_map = {
            "entities": self._parse_entities_string,
            "commands": self._parse_commands_string,
            "queries": self._parse_queries_string,
            "events": self._parse_events_string,
            "workflows": self._parse_workflows_string,
            "value_objects": self._parse_value_objects_string,
            "guards": self._parse_guards_string,
            "roles": self._parse_roles_string,
        }

        return parser_map[category](yaml_content)

    def build_projection_tree(self, yaml_dict: dict[str, str]) -> ProjectionTree:
        """
        Build ProjectionTree từ dictionary của YAML strings.

        Args:
            yaml_dict: Dictionary mapping category → YAML content string
                      Ví dụ: {"entities": "...", "commands": "...", ...}

        Returns:
            ProjectionTree với tất cả nodes
        """
        tree = ProjectionTree()

        for category, yaml_content in yaml_dict.items():
            nodes = self.parse_yaml_string(yaml_content, category)
            for node in nodes:
                tree.add_node(node)

        return tree

    # ========================================================================
    # Entity Parsing
    # ========================================================================

    def _parse_entities_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse entities YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or not data.get("entities"):
            return []

        nodes = []
        for entity_def in data["entities"]:
            if not entity_def.get("id"):
                continue

            entity_id = entity_def["id"]
            params = {
                "id": entity_id,
                "description": entity_def.get("description", ""),
                "fields": entity_def.get("fields", []),
                "primary_key": entity_def.get("primary_key", "id"),
                "indexes": entity_def.get("indexes", []),
                "constraints": entity_def.get("constraints", []),
                "tenant_scope": entity_def.get("tenant_scope", "global"),
            }

            # Thêm relationships nếu có
            if entity_def.get("relationships"):
                params["relationships"] = entity_def["relationships"]

            node = ProjectionNode(
                id=entity_id,
                kind=NodeKind.ENTITY,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Command Parsing
    # ========================================================================

    def _parse_commands_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse commands YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "commands" not in data:
            return []

        nodes = []
        for cmd_def in data["commands"]:
            if not cmd_def.get("id"):
                continue

            cmd_id = cmd_def["id"]
            params = {
                "id": cmd_id,
                "description": cmd_def.get("description", ""),
                "input": cmd_def.get("input", []),
                "fetches": cmd_def.get("fetches", []),
                "guards": cmd_def.get("guards", []),
                "effects": cmd_def.get("effects", []),
                "errors": cmd_def.get("errors", []),
                "returns": cmd_def.get("returns", []),
                "category": cmd_def.get("category", "custom"),
                "emits": cmd_def.get("emits", []),
                "required_roles": cmd_def.get("required_roles", []),
                "required_permissions": cmd_def.get("required_permissions", []),
                "writes_to": cmd_def.get("writes_to", []),
                "transaction": cmd_def.get("transaction", False),
                "tenant_scope": cmd_def.get("tenant_scope", "global"),
            }

            node = ProjectionNode(
                id=cmd_id,
                kind=NodeKind.COMMAND,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Query Parsing
    # ========================================================================

    def _parse_queries_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse queries YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "queries" not in data:
            return []

        nodes = []
        for query_def in data["queries"]:
            if not query_def.get("id"):
                continue

            query_id = query_def["id"]
            params = {
                "id": query_id,
                "description": query_def.get("description", ""),
                "input": query_def.get("input", []),
                "fetches": query_def.get("fetches", []),
                "guards": query_def.get("guards", []),
                "returns": query_def.get("returns", []),
                "category": query_def.get("category", "list"),
                "reads_from": query_def.get("reads_from", []),
                "required_roles": query_def.get("required_roles", []),
                "required_permissions": query_def.get("required_permissions", []),
                "tenant_scope": query_def.get("tenant_scope", "global"),
            }

            node = ProjectionNode(
                id=query_id,
                kind=NodeKind.QUERY,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Event Parsing
    # ========================================================================

    def _parse_events_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse events YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "events" not in data:
            return []

        nodes = []
        for event_def in data["events"]:
            if not event_def.get("id"):
                continue

            event_id = event_def["id"]
            params = {
                "id": event_id,
                "description": event_def.get("description", ""),
                "type": event_def.get("type", "domain_event"),
                "source_entity": event_def.get("source_entity"),
                "fields": event_def.get("fields", []),
                "version": event_def.get("version", "1.0.0"),
                "tenant_scope": event_def.get("tenant_scope", "global"),
            }

            node = ProjectionNode(
                id=event_id,
                kind=NodeKind.EVENT,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Workflow Parsing
    # ========================================================================

    def _parse_workflows_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse workflows YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "workflows" not in data:
            return []

        nodes = []
        for wf_def in data["workflows"]:
            if not wf_def.get("id"):
                continue

            wf_id = wf_def["id"]
            params = {
                "id": wf_id,
                "description": wf_def.get("description", ""),
                "states": wf_def.get("states", []),
                "transitions": wf_def.get("transitions", []),
                "guards": wf_def.get("guards", []),
                "effects": wf_def.get("effects", []),
                "tenant_scope": wf_def.get("tenant_scope", "global"),
            }

            node = ProjectionNode(
                id=wf_id,
                kind=NodeKind.WORKFLOW,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Value Object Parsing
    # ========================================================================

    def _parse_value_objects_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse value_objects YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "value_objects" not in data:
            return []

        nodes = []
        for vo_def in data["value_objects"]:
            if not vo_def.get("id"):
                continue

            vo_id = vo_def["id"]
            params = {
                "id": vo_id,
                "description": vo_def.get("description", ""),
                "fields": vo_def.get("fields", []),
                "immutable": vo_def.get("immutable", True),
                "comparable": vo_def.get("comparable", False),
                "extends": vo_def.get("extends"),
            }

            node = ProjectionNode(
                id=vo_id,
                kind=NodeKind.VALUE_OBJECT,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Guard Parsing
    # ========================================================================

    def _parse_guards_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse guards YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "guards" not in data:
            return []

        nodes = []
        for guard_def in data["guards"]:
            if not guard_def.get("id"):
                continue

            guard_id = guard_def["id"]
            params = {
                "id": guard_id,
                "description": guard_def.get("description", ""),
                "type": guard_def.get("type", "validation"),
                "condition": guard_def.get("condition", {}),
                "error": guard_def.get("error"),
            }

            node = ProjectionNode(
                id=guard_id,
                kind=NodeKind.GUARD,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Role Parsing
    # ========================================================================

    def _parse_roles_string(self, yaml_content: str) -> list[ProjectionNode]:
        """Parse roles YAML string → ProjectionNodes."""
        data = yaml.safe_load(yaml_content)
        if not data or "roles" not in data:
            return []

        nodes = []
        for role_def in data["roles"]:
            if not role_def.get("id"):
                continue

            role_id = role_def["id"]
            params = {
                "id": role_id,
                "description": role_def.get("description", ""),
                "permissions": role_def.get("permissions", []),
                "tenant_scope": role_def.get("tenant_scope", "global"),
            }

            node = ProjectionNode(
                id=role_id,
                kind=NodeKind.ROLE,
                params=params,
            )
            nodes.append(node)

        return nodes


# ============================================================================
# Exports
# ============================================================================

__all__ = ["DSLParser"]