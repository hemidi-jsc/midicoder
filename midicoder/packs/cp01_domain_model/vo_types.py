"""
Value Object Type Resolver

Resolver cho type mapping từ DSL types → Python/TypeScript types.
Support complex types: object, array, map, ref.

Author: Midicoder Team
Version: 2.0.0
"""

from dataclasses import dataclass, replace
from typing import Any, Optional

from midicoder.dsl.projection import FieldDefinition


@dataclass
class TypeMapping:
    """
    Type mapping kết quả.

    Attributes:
        annotation: Type annotation string
        imports: Danh sách required imports
        is_complex: Có phải complex type không
        nested_type: Nested type name nếu là complex
    """

    annotation: str
    imports: list[str] = None
    is_complex: bool = False
    nested_type: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.imports is None:
            self.imports = []


class TypeResolver:
    """
    Resolver cho type mapping.

    Map DSL types sang target language types với support cho:
    - Primitive types: string, integer, decimal, boolean, datetime, uuid, enum
    - Complex types: object, array, map, ref
    - Custom types: Named type references

    Usage:
        resolver = TypeResolver(target_language="python")
        mapping = resolver.resolve(field_def)
        print(mapping.annotation)  # "Decimal"
        print(mapping.imports)     # ["from decimal import Decimal"]
    """

    def __init__(self, target_language: str = "python") -> None:
        """
        Initialize resolver.

        Args:
            target_language: Target language ("python" or "typescript")
        """
        self.target_language = target_language
        self._type_map = self._build_type_map()

    def _build_type_map(self) -> dict[str, TypeMapping]:
        """
        Build type mapping cho primitive types.

        Returns:
            Map của type names → TypeMapping
        """
        if self.target_language == "python":
            return {
                "string": TypeMapping(
                    annotation="str",
                    imports=[],
                ),
                "str": TypeMapping(
                    annotation="str",
                    imports=[],
                ),
                "integer": TypeMapping(
                    annotation="int",
                    imports=[],
                ),
                "int": TypeMapping(
                    annotation="int",
                    imports=[],
                ),
                "decimal": TypeMapping(
                    annotation="Decimal",
                    imports=["from decimal import Decimal"],
                ),
                "float": TypeMapping(
                    annotation="float",
                    imports=[],
                ),
                "boolean": TypeMapping(
                    annotation="bool",
                    imports=[],
                ),
                "bool": TypeMapping(
                    annotation="bool",
                    imports=[],
                ),
                "datetime": TypeMapping(
                    annotation="datetime",
                    imports=["from datetime import datetime"],
                ),
                "uuid": TypeMapping(
                    annotation="UUID",
                    imports=["from uuid import UUID"],
                ),
                "enum": TypeMapping(
                    annotation="str",  # Default to str, can be customized
                    imports=[],
                ),
            }
        else:  # TypeScript
            return {
                "string": TypeMapping(
                    annotation="string",
                    imports=[],
                ),
                "str": TypeMapping(
                    annotation="string",
                    imports=[],
                ),
                "integer": TypeMapping(
                    annotation="number",
                    imports=[],
                ),
                "int": TypeMapping(
                    annotation="number",
                    imports=[],
                ),
                "decimal": TypeMapping(
                    annotation="number",
                    imports=[],
                ),
                "float": TypeMapping(
                    annotation="number",
                    imports=[],
                ),
                "boolean": TypeMapping(
                    annotation="boolean",
                    imports=[],
                ),
                "bool": TypeMapping(
                    annotation="boolean",
                    imports=[],
                ),
                "datetime": TypeMapping(
                    annotation="Date",
                    imports=[],
                ),
                "uuid": TypeMapping(
                    annotation="string",
                    imports=[],
                ),
                "enum": TypeMapping(
                    annotation="string",
                    imports=[],
                ),
            }

    def resolve(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve type cho field definition.

        Args:
            field_def: Field definition từ DSL

        Returns:
            TypeMapping với annotation và imports
        """
        field_type = field_def.get("type", "string")

        # Handle primitive types
        if field_type in self._type_map:
            base_mapping = replace(self._type_map[field_type])

            # Special handling cho enum
            if field_type == "enum":
                if "enum_class" in field_def:
                    # Reference đến enum class
                    enum_class = field_def["enum_class"]
                    base_mapping.annotation = enum_class
                    if self.target_language == "python":
                        base_mapping.imports.append(f"from .enums import {enum_class}")
                elif "enum_values" in field_def:
                    # Inline enum values
                    if self.target_language == "python":
                        values = field_def["enum_values"]
                        base_mapping.annotation = f"Literal[{', '.join(repr(v) for v in values)}]"
                        base_mapping.imports.append("from typing import Literal")
                    else:  # TypeScript
                        values = field_def["enum_values"]
                        base_mapping.annotation = f"{' | '.join(repr(v) for v in values)}"

            return base_mapping

        # Handle complex types
        elif field_type == "object":
            return self._resolve_object_type(field_def)

        elif field_type == "array":
            return self._resolve_array_type(field_def)

        elif field_type == "map":
            return self._resolve_map_type(field_def)

        elif field_type == "ref":
            return self._resolve_ref_type(field_def)

        # Default to string
        return TypeMapping(annotation="str" if self.target_language == "python" else "string")

    def _resolve_object_type(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve object type (nested object).

        Args:
            field_def: Field definition với type="object"

        Returns:
            TypeMapping cho nested object
        """
        fields = field_def.get("fields", [])
        nested_name = f"{field_def['name'].capitalize()}Item"

        if self.target_language == "python":
            # Python: Use nested dataclass
            return TypeMapping(
                annotation=nested_name,
                imports=[],
                is_complex=True,
                nested_type=nested_name,
            )
        else:  # TypeScript
            # TypeScript: Use inline interface
            return TypeMapping(
                annotation=nested_name,
                imports=[],
                is_complex=True,
                nested_type=nested_name,
            )

    def _resolve_array_type(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve array type.

        Args:
            field_def: Field definition với type="array"

        Returns:
            TypeMapping cho array
        """
        item_type = field_def.get("item_type")
        item_fields = field_def.get("item_fields")

        if item_fields:
            # Array of objects
            nested_name = f"{field_def['name'].capitalize()}Item"
            if self.target_language == "python":
                return TypeMapping(
                    annotation=f"list[{nested_name}]",
                    imports=[],
                    is_complex=True,
                    nested_type=nested_name,
                )
            else:  # TypeScript
                return TypeMapping(
                    annotation=f"{nested_name}[]",
                    imports=[],
                    is_complex=True,
                    nested_type=nested_name,
                )
        elif item_type:
            # Array of primitive/reference type
            item_mapping = self._type_map.get(item_type, TypeMapping(annotation=item_type))
            if self.target_language == "python":
                return TypeMapping(
                    annotation=f"list[{item_mapping.annotation}]",
                    imports=item_mapping.imports,
                )
            else:  # TypeScript
                return TypeMapping(
                    annotation=f"{item_mapping.annotation}[]",
                    imports=item_mapping.imports,
                )
        else:
            # Default array
            if self.target_language == "python":
                return TypeMapping(annotation="list[Any]", imports=["from typing import Any"])
            else:
                return TypeMapping(annotation="any[]")

    def _resolve_map_type(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve map type (dictionary).

        Args:
            field_def: Field definition với type="map"

        Returns:
            TypeMapping cho map
        """
        key_type = field_def.get("key_type", "string")
        value_type = field_def.get("value_type", "string")

        key_mapping = self._type_map.get(key_type, TypeMapping(annotation=key_type))
        value_mapping = self._type_map.get(value_type, TypeMapping(annotation=value_type))

        if self.target_language == "python":
            return TypeMapping(
                annotation=f"dict[{key_mapping.annotation}, {value_mapping.annotation}]",
                imports=[],
            )
        else:  # TypeScript
            return TypeMapping(
                annotation=f"Record<{key_mapping.annotation}, {value_mapping.annotation}>",
                imports=[],
            )

    def _resolve_ref_type(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve reference type.

        Args:
            field_def: Field definition với type="ref"

        Returns:
            TypeMapping cho reference
        """
        ref_type = field_def.get("ref_type", "entity")
        ref_to = field_def.get("ref_to", "")

        if self.target_language == "python":
            if ref_type == "entity":
                # Entity reference - use string ID
                return TypeMapping(
                    annotation="str",
                    imports=[],
                )
            elif ref_type == "value_object":
                # VO reference - use the VO class
                return TypeMapping(
                    annotation=ref_to,
                    imports=[f"from . import {ref_to}"],
                )
        else:  # TypeScript
            if ref_type == "entity":
                return TypeMapping(
                    annotation="string",
                    imports=[],
                )
            elif ref_type == "value_object":
                # Python string method is lower(), not toLowerCase()
                return TypeMapping(
                    annotation=ref_to,
                    imports=[f"import {{ {ref_to} }} from './{ref_to.lower()}'"],
                )

        return TypeMapping(annotation="str" if self.target_language == "python" else "string")

    def get_all_imports(self, fields: list[FieldDefinition]) -> list[str]:
        """
        Get tất cả required imports cho list of fields.

        Args:
            fields: List of field definitions

        Returns:
            De-duplicated list of import statements
        """
        all_imports = set()

        for field in fields:
            mapping = self.resolve(field)
            all_imports.update(mapping.imports)

        return sorted(all_imports)

    def resolve_computed_field(self, field_def: FieldDefinition) -> TypeMapping:
        """
        Resolve computed field type.

        Computed fields infer type from formula.

        Args:
            field_def: Field definition với computed=True

        Returns:
            TypeMapping cho computed field
        """
        # Computed fields should have explicit type or infer from formula
        explicit_type = field_def.get("type")

        if explicit_type:
            return self.resolve(field_def)

        # Default to decimal for computed fields
        return self._type_map.get("decimal", TypeMapping(annotation="Decimal"))