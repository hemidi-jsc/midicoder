"""Entity relationship diagram generator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import (
    DiagramGenerator,
    DiagramOutput,
    MermaidRenderer,
    create_source_metadata,
)

if TYPE_CHECKING:
    from ...schema.ir_schema import DomainIR, EntityIR, FieldIR, ValueObjectIR


class EntityDiagramGenerator(DiagramGenerator):
    """Generator for entity relationship diagrams (ERD) using Mermaid."""

    def generate(self, domain: DomainIR) -> list[DiagramOutput]:
        """Generate entity relationship diagram.

        Args:
            domain: Domain IR object

        Returns:
            List of generated diagram outputs
        """
        if not domain.entities and not domain.value_objects:
            return []

        mermaid_source = self._build_mermaid_source(domain)

        output_path = self.output_dir / "domain_model.mmd"

        assets = MermaidRenderer.render_to_file(mermaid_source, output_path, "mmd")

        # Build sources with full metadata
        sources = []
        for e in domain.entities:
            sources.append(
                create_source_metadata(
                    id=e.id,
                    type="Entity",
                    source=e.source if hasattr(e, "source") else None,
                )
            )

        for vo in domain.value_objects:
            sources.append(
                create_source_metadata(
                    id=vo.id,
                    type="ValueObject",
                    source=vo.source if hasattr(vo, "source") else None,
                )
            )

        return [
            DiagramOutput(
                diagram_id="entity_domain_model",
                diagram_type="entity",
                format="mmd",
                path=output_path,
                sources=sources,
                template="domain_model.er",
                assets=assets,
            )
        ]

    def _build_mermaid_source(self, domain: DomainIR) -> str:
        """Build Mermaid erDiagram source for ERD.

        Args:
            domain: Domain IR object

        Returns:
            Mermaid source code
        """
        lines = [
            "---",
            "title: Domain Model",
            "---",
            "erDiagram",
            "",
        ]

        # Map entity/VO IDs to sanitized names
        entity_nodes = {}
        for entity in domain.entities:
            node_id = MermaidRenderer.sanitize_mermaid_id(entity.id)
            entity_nodes[entity.id] = node_id

        for vo in domain.value_objects:
            node_id = MermaidRenderer.sanitize_mermaid_id(vo.id)
            entity_nodes[vo.id] = node_id

        entity_ids = {entity.id for entity in domain.entities}
        value_object_ids = {vo.id for vo in domain.value_objects}

        # Define entities with attributes
        for entity in domain.entities:
            node_id = entity_nodes[entity.id]
            lines.append(f"    {node_id} {{")
            optional_fields = []

            # Add primary key
            if entity.primary_key:
                pk_type = self._get_field_type_for_pk(entity, entity.primary_key)
                pk_name = self._sanitize_attribute_name(entity.primary_key)
                lines.append(f"        {pk_type} {pk_name} PK")

            # Add fields (limit to prevent overflow)
            for field in entity.fields[:15]:
                if field.name == entity.primary_key:
                    continue
                if not field.required:
                    optional_fields.append(field.name)

                field_type = self._simplify_type_mermaid(field.type)
                field_name = self._sanitize_attribute_name(field.name)
                lines.append(f"        {field_type} {field_name}")

            if len(entity.fields) > 15:
                lines.append("    }")
                lines.append(f"    %% ... {len(entity.fields) - 15} more fields")
                if optional_fields:
                    opt_list = ", ".join(optional_fields)
                    lines.append(f"    %% optional: {opt_list}")
                lines.append("")
                continue

            lines.append("    }")
            if optional_fields:
                opt_list = ", ".join(optional_fields)
                lines.append(f"    %% optional: {opt_list}")
            lines.append("")

        # Define value objects with attributes
        for vo in domain.value_objects:
            node_id = entity_nodes[vo.id]
            lines.append(f"    {node_id} {{")
            optional_fields = []

            for field in vo.fields[:12]:
                field_type = self._simplify_type_mermaid(field.type)
                if not field.required:
                    optional_fields.append(field.name)
                field_name = self._sanitize_attribute_name(field.name)
                lines.append(f"        {field_type} {field_name}")

            if len(vo.fields) > 12:
                lines.append("    }")
                lines.append(f"    %% ... {len(vo.fields) - 12} more fields")
                if optional_fields:
                    opt_list = ", ".join(optional_fields)
                    lines.append(f"    %% optional: {opt_list}")
                lines.append("")
                continue

            lines.append("    }")
            if optional_fields:
                opt_list = ", ".join(optional_fields)
                lines.append(f"    %% optional: {opt_list}")
            lines.append("")

        # Extract and define relationships
        relationships = []
        for entity in domain.entities:
            entity_relationships = self._extract_relationships(
                entity.id,
                entity.fields,
                entity_ids,
                value_object_ids,
            )
            relationships.extend(entity_relationships)

        for vo in domain.value_objects:
            vo_relationships = self._extract_relationships(
                vo.id,
                vo.fields,
                entity_ids,
                value_object_ids,
            )
            relationships.extend(vo_relationships)

        # Add relationships
        seen_edges = set()
        for (
            source_id,
            target_id,
            field_name,
            is_array,
            is_optional,
            target_kind,
        ) in relationships:
            edge_key = (
                source_id,
                target_id,
                field_name,
                is_array,
                is_optional,
                target_kind,
            )
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            source_node = entity_nodes.get(source_id)
            target_node = entity_nodes.get(target_id)

            if not source_node or not target_node:
                continue

            # Determine cardinality and direction
            if target_kind == "Entity":
                if is_array:
                    left_node = source_node
                    right_node = target_node
                    left_card = "||"
                    right_card = "o{"
                else:
                    left_node = target_node
                    right_node = source_node
                    left_card = "o|" if is_optional else "||"
                    right_card = "o{"
            else:  # ValueObject
                left_node = source_node
                right_node = target_node
                left_card = "||"
                if is_array:
                    right_card = "o{"
                else:
                    right_card = "o|" if is_optional else "||"

            cardinality = f"{left_card}--{right_card}"
            label = MermaidRenderer.escape_mermaid_text(
                self._sanitize_attribute_name(field_name)
            )
            lines.append(f"    {left_node} {cardinality} {right_node} : {label}")

        return "\n".join(lines)

    def _get_field_type_for_pk(self, entity: EntityIR, pk_name: str) -> str:
        """Get field type for primary key.

        Args:
            entity: Entity IR object
            pk_name: Primary key field name

        Returns:
            Field type
        """
        for field in entity.fields:
            if field.name == pk_name:
                return self._simplify_type_mermaid(field.type)
        return "string"

    def _simplify_type_mermaid(self, type_str: str) -> str:
        """Simplify type string for Mermaid ERD display.

        Args:
            type_str: Original type string

        Returns:
            Simplified type for Mermaid
        """
        # Handle arrays
        if type_str.startswith("Array["):
            inner = type_str[6:-1]
            return self._simplify_type_mermaid(inner)

        # Handle optional
        if type_str.startswith("Optional["):
            inner = type_str[9:-1]
            return self._simplify_type_mermaid(inner)

        # Map to Mermaid-friendly types
        type_mapping = {
            "String": "string",
            "Integer": "int",
            "Boolean": "bool",
            "Decimal": "decimal",
            "Float": "float",
            "DateTime": "datetime",
            "Date": "date",
            "Time": "time",
            "UUID": "uuid",
            "JSON": "json",
            "Binary": "binary",
        }

        return type_mapping.get(type_str, "string")

    def _extract_relationships(
        self,
        source_id: str,
        fields: list[FieldIR],
        entity_ids: set[str],
        value_object_ids: set[str],
    ) -> list[tuple[str, str, str, bool, bool, str]]:
        """Extract relationships from entity fields.

        Args:
            source_id: Source entity/value object ID
            fields: List of fields

        Returns:
            List of (source_id, target_id, field_name, is_array, is_optional, target_kind) tuples
        """
        relationships = []

        for field in fields:
            field_type, is_array, is_optional = self._unwrap_type(field.type)
            is_optional = is_optional or (not field.required)

            target_kind = None
            target_id = None

            if ":" in field_type:
                ref_type, ref_id = field_type.split(":", 1)
                if ref_type == "Entity" and ref_id in entity_ids:
                    target_kind = "Entity"
                    target_id = ref_id
                elif ref_type == "ValueObject" and ref_id in value_object_ids:
                    target_kind = "ValueObject"
                    target_id = ref_id
            else:
                if field_type in entity_ids:
                    target_kind = "Entity"
                    target_id = field_type
                elif field_type in value_object_ids:
                    target_kind = "ValueObject"
                    target_id = field_type

            if target_kind and target_id:
                relationships.append(
                    (
                        source_id,
                        target_id,
                        field.name,
                        is_array,
                        is_optional,
                        target_kind,
                    )
                )

        return relationships

    def _unwrap_type(self, type_str: str) -> tuple[str, bool, bool]:
        """Unwrap Optional/Array wrappers from a type string.

        Returns:
            (base_type, is_array, is_optional)
        """
        is_array = False
        is_optional = False
        current = type_str

        while True:
            if current.startswith("Array[") and current.endswith("]"):
                current = current[6:-1]
                is_array = True
                continue
            if current.startswith("Optional[") and current.endswith("]"):
                current = current[9:-1]
                is_optional = True
                continue
            break

        return current, is_array, is_optional

    def _sanitize_attribute_name(self, name: str) -> str:
        """Sanitize attribute name for Mermaid ERD."""
        return MermaidRenderer.sanitize_mermaid_id(name)
