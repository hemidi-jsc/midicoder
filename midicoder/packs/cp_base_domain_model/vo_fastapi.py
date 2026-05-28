"""
FastAPI Value Object Emitter

FastAPI-specific implementation của ValueObjectEmitter.
Generate Python code với dataclass, validation, và type hints.

Author: Midicoder Team
Version: 2.0.0
"""

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .vo_emitter import ValueObjectEmitter, EmittedValueObject, EmittedField
from .vo_types import TypeResolver
from .vo_inheritance import InheritanceResolver
from .vo_computed import ComputedFieldEvaluator


class FastAPIValueObjectEmitter(ValueObjectEmitter):
    """
    FastAPI Value Object Emitter.

    Generate Python Value Object code từ extended DSL với support cho:
    - Complex fields (object, array, map, ref)
    - Inheritance (extends)
    - Computed fields
    - Methods
    - Validation rules

    Usage:
        emitter = FastAPIValueObjectEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        emitted_vo = emitter.emit(vo_params, parent_vo_map)
        code = emitter.render_value_object(emitted_vo)
    """

    def __init__(
        self,
        stack_dir: Path,
        target_language: str = "python"
    ) -> None:
        """
        Khởi tạo FastAPIValueObjectEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
            target_language: Target language (default: python)
        """
        super().__init__()

        self.stack_dir = stack_dir
        self.target_language = target_language

        # Initialize type resolver
        self.type_resolver = TypeResolver(target_language=target_language)

        # Initialize computed field evaluator
        self.computed_evaluator = ComputedFieldEvaluator()

        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True,
        )

        # Cache cho nested classes
        self._nested_classes: dict[str, str] = {}

    def map_type(self, field: dict[str, Any]) -> str:
        """
        Map DSL type sang Python type annotation.

        Args:
            field: Field definition

        Returns:
            Type annotation string
        """
        mapping = self.type_resolver.resolve(field)
        return mapping.annotation

    def render_value_object(self, vo: EmittedValueObject) -> str:
        """
        Render Value Object thành Python code.

        Args:
            vo: Emitted Value Object

        Returns:
            Generated Python code
        """
        # Build template context
        context = self._build_template_context(vo)

        try:
            template = self.template_env.get_template("value_object.py.jinja2")
            return template.render(**context)
        except Exception as e:
            # Fallback: Generate code manually
            return self._generate_code_fallback(vo)

    def _build_template_context(self, vo: EmittedValueObject) -> dict[str, Any]:
        """
        Build template context cho Jinja2 rendering.

        Args:
            vo: Emitted Value Object

        Returns:
            Template context dictionary
        """
        # Build imports
        imports = self._collect_imports(vo)

        # Build nested classes (cho complex fields)
        nested_classes = self._generate_nested_classes(vo)

        # Build computed field properties
        computed_properties = self._generate_computed_properties(vo)

        # Build methods
        methods = self._generate_methods(vo)

        return {
            "vo": {
                "id": vo.id,
                "description": vo.description,
                "extends": vo.inherits_from,
                "tags": vo.tags,
                "is_frozen": vo.is_frozen,
                "comparable": vo.comparable,
            },
            "fields": vo.fields,
            "methods": methods,
            "computed_properties": computed_properties,
            "validation_rules": vo.validation_rules,
            "imports": imports,
            "nested_classes": nested_classes,
        }

    def _collect_imports(self, vo: EmittedValueObject) -> dict[str, list[str]]:
        """
        Collect tất cả required imports.

        Args:
            vo: Emitted Value Object

        Returns:
            Dict of import categories → import statements
        """
        imports = {
            "standard": [],
            "typing": [],
            "domain": [],
        }

        # Always include base imports
        imports["standard"].append("from dataclasses import dataclass, field")
        imports["typing"].append("from typing import Optional, List, Dict, Any")

        # Check fields for specific imports
        has_decimal = False
        has_datetime = False
        has_uuid = False
        has_enum = False

        for field_def in vo.fields:
            original = field_def.original

            if original.get("type") == "decimal":
                has_decimal = True
            elif original.get("type") == "datetime":
                has_datetime = True
            elif original.get("type") == "uuid":
                has_uuid = True
            elif original.get("type") == "enum":
                has_enum = True
            elif original.get("type") == "ref" and original.get("ref_type") == "value_object":
                ref_to = original.get("ref_to", "")
                imports["domain"].append(f"from . import {ref_to}")

        if has_decimal:
            imports["standard"].append("from decimal import Decimal")
        if has_datetime:
            imports["standard"].append("from datetime import datetime")
        if has_uuid:
            imports["standard"].append("from uuid import UUID")
        if has_enum:
            imports["standard"].append("from enum import Enum")

        # Check for Literal (computed fields)
        has_computed = any(f.is_computed for f in vo.fields)
        if has_computed:
            imports["typing"].append("from typing import Literal")

        return imports

    def _generate_nested_classes(self, vo: EmittedValueObject) -> list[str]:
        """
        Generate nested class code cho complex fields.

        Args:
            vo: Emitted Value Object

        Returns:
            List of nested class code strings
        """
        nested_classes = []

        for field_def in vo.fields:
            original = field_def.original
            field_type = original.get("type", "")

            if field_type == "object" and "fields" in original:
                nested_code = self._generate_nested_object_class(
                    field_name=field_def.name,
                    fields=original["fields"],
                )
                nested_classes.append(nested_code)

            elif field_type == "array" and "item_fields" in original:
                nested_code = self._generate_nested_object_class(
                    field_name=f"{field_def.name}Item",
                    fields=original["item_fields"],
                )
                nested_classes.append(nested_code)

        return nested_classes

    def _generate_nested_object_class(
        self,
        field_name: str,
        fields: list[dict[str, Any]]
    ) -> str:
        """
        Generate nested object class code.

        Args:
            field_name: Field name (used as class name)
            fields: Nested fields

        Returns:
            Nested class code string
        """
        class_name = f"{field_name.capitalize()}Item"
        lines = [
            f"@dataclass(frozen=True)",
            f"class {class_name}:",
            '    """Nested class for {field_name}."""',
            "",
        ]

        for nested_field in fields:
            nested_type = self.type_resolver.resolve(nested_field).annotation
            default = ""
            if not nested_field.get("required"):
                default = " = None"
            lines.append(f"    {nested_field['name']}: {nested_type}{default}")

        lines.append("")
        lines.append("    def to_dict(self) -> dict:")
        lines.append('        """Convert to dictionary."""')
        lines.append("        return {")
        for nested_field in fields:
            lines.append(f"            '{nested_field['name']}': self.{nested_field['name']},")
        lines.append("        }")
        lines.append("")

        return "\n".join(lines)

    def _generate_computed_properties(self, vo: EmittedValueObject) -> list[str]:
        """
        Generate computed field properties.

        Args:
            vo: Emitted Value Object

        Returns:
            List of property code strings
        """
        properties = []

        for field_def in vo.fields:
            if not field_def.is_computed:
                continue

            original = field_def.original
            field_type = original.get("type", "decimal")
            formula = original.get("formula", "")
            depends_on = original.get("depends_on", [])

            code = self.computed_evaluator.generate_python_code(
                field_name=field_def.name,
                field_type=field_type,
                formula=formula,
                depends_on=depends_on,
            )
            properties.append(code)

        return properties

    def _generate_methods(self, vo: EmittedValueObject) -> list[str]:
        """
        Generate method code.

        Args:
            vo: Emitted Value Object

        Returns:
            List of method code strings
        """
        methods = []

        for method_def in vo.methods:
            # Generate method stub
            code = f"""
    def {method_def.name}({method_def.signature}):
        \"\"\"{method_def.original.get('description', '')}\"\"\"
        {method_def.implementation}"""
            methods.append(code)

        return methods

    def _generate_code_fallback(self, vo: EmittedValueObject) -> str:
        """
        Fallback code generation khi template không sẵn.

        Args:
            vo: Emitted Value Object

        Returns:
            Generated Python code
        """
        lines = [
            '"""',
            f"{vo.id} Value Object.",
            f"{vo.description or vo.id}",
            "Generated by Midicoder - FastAPIValueObjectEmitter",
            "CP01: Domain Model - Value Objects",
            '"""',
            "",
            "from dataclasses import dataclass, field",
            "from decimal import Decimal",
            "from datetime import datetime",
            "from uuid import UUID",
            "from typing import Optional, List, Dict, Any",
            "",
            "",
        ]

        # Add frozen decorator
        frozen = "frozen=True" if vo.is_frozen else ""
        inherits = f"(BaseValueObject)" if vo.inherits_from else ""

        lines.append(f"@dataclass({frozen})")
        lines.append(f"class {vo.name}{inherits}:")
        lines.append(f'    """')
        lines.append(f"    {vo.description or vo.id}")
        lines.append("    ")
        lines.append("    Attributes:")
        for field_def in vo.fields:
            lines.append(f"        {field_def.name}: {field_def.original.get('description', field_def.name)}")
        lines.append("    ")
        lines.append("    Raises:")
        lines.append("        ValueError: Nếu validation thất bại")
        lines.append('    """')
        lines.append("")

        # Generate fields
        for field_def in vo.fields:
            default = ""
            if not field_def.is_required and not field_def.is_computed:
                default = " = None"
            lines.append(f"    {field_def.name}: {field_def.type_annotation}{default}")

        lines.append("")

        # Add __post_init__
        lines.append("    def __post_init__(self) -> None:")
        lines.append('        """Validate fields sau khi init."""')

        for field_def in vo.fields:
            original = field_def.original
            if original.get("required") and not field_def.is_computed:
                lines.append(f'        if self.{field_def.name} is None:')
                lines.append('            raise ValueError(f"{field_def.name} là trường bắt buộc")')
                lines.append("")

        lines.append("")

        # Add computed properties
        for field_def in vo.fields:
            if field_def.is_computed:
                original = field_def.original
                formula = original.get("formula", "")
                field_type = original.get("type", "decimal")

                lines.append("    @property")
                lines.append(f"    def {field_def.name}(self) -> {field_def.type_annotation}:")
                lines.append(f'        """Computed field: {field_def.name}"""')
                if field_type == "decimal":
                    lines.append(f"        return Decimal(str({formula}))")
                else:
                    lines.append(f"        return {formula}")
                lines.append("")

        # Add methods
        for method_def in vo.methods:
            lines.append(method_def.signature)
            lines.append(f"        # {method_def.original.get('logic', '')}")
            lines.append("")

        # Add to_dict
        lines.append("    def to_dict(self) -> dict:")
        lines.append('        """Chuyển thành dictionary."""')
        lines.append("        return {")
        for field_def in vo.fields:
            lines.append(f"        '{field_def.name}': self.{field_def.name},")
        lines.append("        }")
        lines.append("")

        # Add from_dict
        lines.append("    @classmethod")
        lines.append(f"    def from_dict(cls, data: dict) -> '{vo.name}':")
        lines.append(f'        """Tạo {vo.name} từ dictionary."""')
        lines.append("        return cls(")
        for field_def in vo.fields:
            original = field_def.original
            field_type = original.get("type", "string")
            field_name = field_def.name

            if field_type == "decimal":
                lines.append(f"            {field_name}=Decimal(str(data['{field_name}'])),")
            elif field_type == "uuid":
                lines.append(f"            {field_name}=UUID(data['{field_name}'])),")
            elif field_type == "datetime":
                lines.append(f"            {field_name}=datetime.fromisoformat(data['{field_name}'])),")
            else:
                lines.append(f"            {field_name}=data['{field_name}'],")
        lines.append("        )")
        lines.append("")

        # Add __str__
        lines.append("    def __str__(self) -> str:")
        lines.append('        """String representation."""')
        lines.append("        return str(self.to_dict())")
        lines.append("")

        # Add __repr__
        lines.append("    def __repr__(self) -> str:")
        lines.append('        """Debug representation."""')
        lines.append(f"        return f'{vo.name}(**self.to_dict())'")

        return "\n".join(lines)

    def emit_all(
        self,
        vo_map: dict[str, dict[str, Any]],
        output_dir: Path
    ) -> list[tuple[Path, str]]:
        """
        Emit tất cả Value Objects vào output directory.

        Args:
            vo_map: Map của VO IDs → params
            output_dir: Output directory

        Returns:
            List of (path, content) tuples
        """
        # Initialize inheritance resolver
        inheritance_resolver = InheritanceResolver(vo_map)

        # Check for circular inheritance
        cycles = inheritance_resolver.detect_all_cycles()
        if cycles:
            EM.raise_error(
                ErrorCode.MDC-B01_VALUE_OBJECT_NOT_FOUND,
                cycles=cycles,
            )

        emitted_files: list[tuple[Path, str]] = []

        # Emit each VO
        for vo_id, vo_params in vo_map.items():
            # Merge với inheritance
            merged_params = inheritance_resolver.merge_vo(vo_id)

            # Emit
            emitted_vo = self.emit(merged_params, parent_vo_map=vo_map)

            # Write file
            vo_lower = vo_id.lower()
            file_path = output_dir / f"{vo_lower}.py"
            file_path.write_text(emitted_vo.full_content, encoding="utf-8")

            emitted_files.append((file_path, emitted_vo.full_content))

        return emitted_files