"""
DSL Parser Module.

Module này cung cấp DSLParser để parse YAML contract files → ProjectionTree:
- Load YAML files từ directory paths
- Parse entities, commands, queries, events, workflows, value_objects, guards
- Convert parsed models → ProjectionNode (DSL kernel)
- Build ProjectionTree với tất cả nodes

Sử dụng:
    from midicoder.pipeline.dsl_parser import DSLParser
    
    parser = DSLParser()
    tree = parser.parse_directory("contracts/")
    # tree: ProjectionTree

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from midicoder.dsl.projection import ProjectionNode, ProjectionTree, NodeKind
from midicoder.emitters.core.`entity.parser import EntityParser
from midicoder.emitters.core.`command.parser import CommandParser
from midicoder.emitters.core.`query.parser import parse_filters, parse_pagination
from midicoder.emitters.core.`workflow.parser import WorkflowParser
from midicoder.emitters.core.`value_object.parser import ValueObjectParser


class DSLParser:
    """
    Unified DSL Parser cho Midicoder contracts.

    Parse YAML contract files thành ProjectionTree (DSL kernel).
    Sử dụng existing parsers cho từng contract type.

    Supported files:
        - entities.yml
        - commands.yml
        - queries.yml
        - events.yml
        - workflows.yml
        - value_objects.yml
        - guards.yml
    """

    def __init__(self) -> None:
        """Khởi tạo DSLParser với các sub-parsers."""
        self.entity_parser = EntityParser()
        self.command_parser = CommandParser()
        self.workflow_parser = WorkflowParser()
        self.vo_parser = ValueObjectParser()

    def parse_directory(self, contracts_dir: str) -> ProjectionTree:
        """
        Parse tất cả YAML files trong contracts directory.

        Args:
            contracts_dir: Path đến contracts directory

        Returns:
            ProjectionTree với tất cả nodes

        Example:
            parser = DSLParser()
            tree = parser.parse_directory("contracts/")
        """
        tree = ProjectionTree()
        dir_path = Path(contracts_dir)

        if not dir_path.exists():
            raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")

        # Parse each supported file type
        file_mappings = {
            "entities.yml": self._parse_entities_file,
            "commands.yml": self._parse_commands_file,
            "queries.yml": self._parse_queries_file,
            "events.yml": self._parse_events_file,
            "workflows.yml": self._parse_workflows_file,
            "value_objects.yml": self._parse_value_objects_file,
            "guards.yml": self._parse_guards_file,
        }

        for filename, parser_func in file_mappings.items():
            file_path = dir_path / filename
            if file_path.exists():
                nodes = parser_func(file_path)
                for node in nodes:
                    tree.add_node(node)

        return tree

    def parse_file(self, file_path: str, contract_type: str) -> list[ProjectionNode]:
        """
        Parse single YAML file theo contract type.

        Args:
            file_path: Path đến YAML file
            contract_type: Loại contract (entities, commands, queries, etc.)

        Returns:
            List của ProjectionNode
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        parser_map = {
            "entities": self._parse_entities_file,
            "commands": self._parse_commands_file,
            "queries": self._parse_queries_file,
            "events": self._parse_events_file,
            "workflows": self._parse_workflows_file,
            "value_objects": self._parse_value_objects_file,
            "guards": self._parse_guards_file,
        }

        if contract_type not in parser_map:
            raise ValueError(f"Unknown contract type: {contract_type}")

        return parser_map[contract_type](file_path)

    # ========================================================================
    # Entity Parsing
    # ========================================================================

    def _parse_entities_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse entities.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        entities = self.entity_parser.parse(yaml_content)

        nodes = []
        for entity in entities:
            params = {
                "id": entity.id,
                "description": entity.description,
                "fields": [f.to_dict() for f in entity.fields],
                "primary_key": entity.primary_key,
                "indexes": [i.to_dict() for i in entity.indexes] if hasattr(entity, 'indexes') else [],
                "constraints": [c.to_dict() for c in entity.constraints] if hasattr(entity, 'constraints') else [],
                "tenant_scope": getattr(entity, 'tenant_scope', 'global'),
                "source": str(file_path),
            }

            # Add relationships if exists
            if hasattr(entity, 'relationships') and entity.relationships:
                params["relationships"] = [
                    {
                        "type": r.rel_type.value,
                        "target": r.target,
                        "local_field": r.local_field,
                        "foreign_field": r.foreign_field,
                    }
                    for r in entity.relationships
                ]

            node = ProjectionNode(
                id=entity.id,
                kind=NodeKind.ENTITY,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Command Parsing
    # ========================================================================

    def _parse_commands_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse commands.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        commands = self.command_parser.parse(yaml_content)

        nodes = []
        for cmd in commands:
            params = {
                "id": cmd.id,
                "description": cmd.description,
                "input": [f.to_dict() for f in cmd.input],
                "fetches": cmd.fetches,
                "guards": cmd.guards,
                "effects": cmd.effects,
                "errors": cmd.errors,
                "returns": [r.to_dict() for r in cmd.returns],
                "category": cmd.category,
                "emits": cmd.emits,
                "required_roles": cmd.required_roles,
                "required_permissions": cmd.required_permissions,
                "writes_to": cmd.writes_to,
                "transaction": cmd.transaction,
                "tenant_scope": cmd.tenant_scope,
                "source": str(file_path),
            }

            node = ProjectionNode(
                id=cmd.id,
                kind=NodeKind.COMMAND,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Query Parsing
    # ========================================================================

    def _parse_queries_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse queries.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(yaml_content)

        nodes = []
        for query_def in data.get("queries", []):
            if not query_def.get("id"):
                continue

            query_id = query_def["id"]

            # Parse input fields (similar to command input)
            input_fields = []
            if "input" in query_def:
                for f in query_def["input"]:
                    input_fields.append({
                        "name": f.get("name"),
                        "type": f.get("type", "string"),
                        "required": bool(f.get("required", False)),
                    })

            params = {
                "id": query_id,
                "description": query_def.get("description", ""),
                "input": input_fields,
                "fetches": query_def.get("fetches", []),
                "guards": query_def.get("guards", []),
                "returns": query_def.get("returns", []),
                "category": query_def.get("category", "list"),
                "reads_from": query_def.get("reads_from", []),
                "required_roles": query_def.get("required_roles", []),
                "required_permissions": query_def.get("required_permissions", []),
                "tenant_scope": query_def.get("tenant_scope", "global"),
                "source": str(file_path),
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

    def _parse_events_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse events.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(yaml_content)

        nodes = []
        for event_def in data.get("events", []):
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
                "source": str(file_path),
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

    def _parse_workflows_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse workflows.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        workflows = self.workflow_parser.parse(yaml_content)

        nodes = []
        for workflow in workflows:
            params = {
                "id": workflow.id,
                "description": workflow.description,
                "states": [s.to_dict() for s in workflow.states] if hasattr(workflow, 'states') else [],
                "transitions": [t.to_dict() for t in workflow.transitions] if hasattr(workflow, 'transitions') else [],
                "guards": workflow.guards if hasattr(workflow, 'guards') else [],
                "effects": workflow.effects if hasattr(workflow, 'effects') else [],
                "tenant_scope": getattr(workflow, 'tenant_scope', 'global'),
                "source": str(file_path),
            }

            node = ProjectionNode(
                id=workflow.id,
                kind=NodeKind.WORKFLOW,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Value Object Parsing
    # ========================================================================

    def _parse_value_objects_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse value_objects.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        vos = self.vo_parser.parse(yaml_content)

        nodes = []
        for vo in vos:
            params = {
                "id": vo.id,
                "description": vo.description,
                "fields": [f.to_dict() for f in vo.fields],
                "immutable": vo.immutable,
                "comparable": vo.comparable,
                "extends": vo.extends,
                "source": str(file_path),
            }

            node = ProjectionNode(
                id=vo.id,
                kind=NodeKind.VALUE_OBJECT,
                params=params,
            )
            nodes.append(node)

        return nodes

    # ========================================================================
    # Guard Parsing
    # ========================================================================

    def _parse_guards_file(self, file_path: Path) -> list[ProjectionNode]:
        """Parse guards.yml → ProjectionNodes."""
        yaml_content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(yaml_content)

        nodes = []
        for guard_def in data.get("guards", []):
            if not guard_def.get("id"):
                continue

            guard_id = guard_def["id"]

            params = {
                "id": guard_id,
                "description": guard_def.get("description", ""),
                "type": guard_def.get("type", "validation"),
                "condition": guard_def.get("condition", {}),
                "error": guard_def.get("error"),
                "source": str(file_path),
            }

            node = ProjectionNode(
                id=guard_id,
                kind=NodeKind.GUARD,
                params=params,
            )
            nodes.append(node)

        return nodes


# ============================================================================
# Exports
# ============================================================================

__all__ = ["DSLParser"]