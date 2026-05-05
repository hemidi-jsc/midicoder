"""
NestJS Value Object Emitter

NestJS-specific implementation của ValueObjectEmitter.
Generate TypeScript code với decorators, class-validator, và type hints.

Author: Midicoder Team
Version: 2.0.0
"""

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .base import ValueObjectEmitter, EmittedValueObject, EmittedField
from .type_resolver import TypeResolver
from .inheritance import InheritanceResolver
from .computed import ComputedFieldEvaluator


class NestJSValueObjectEmitter(ValueObjectEmitter):
    """
    NestJS Value Object Emitter.

    Generate TypeScript Value Object code từ extended DSL với support cho:
    - Complex fields (object, array, map, ref)
    - Inheritance (extends)
    - Computed fields
    - Methods
    - Validation rules (class-validator decorators)

    Usage:
        emitter = NestJSValueObjectEmitter(stack_dir=Path("midicoder/stacks/nestjs/templates"))
        emitted_vo = emitter.emit(vo_params, parent_vo_map)
        code = emitter.render_value_object(emitted_vo)
    """

    def __init__(
        self,
        stack_dir: Path,
        target_language: str = "typescript"
    ) -> None:
        """
        Khởi tạo NestJSValueObjectEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
            target_language: Target language (default: typescript)
        """
        super().__init__()

        self.stack_dir = stack_dir
        self.target_language = target_language

        # Initialize type resolver
        self.type_resolver = TypeResolver(target_language=target_language)

        # Initialize computed field evaluator
        self.computed_evaluator = ComputedFieldEvaluator()

        # Initialize Jinja2 environment
        templates_dir = stack_dir / "value_objects"
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

        # Cache cho nested classes
        self._nested_classes: dict[str, str] = {}

    def map_type(self, field: dict[str, Any]) -> str:
        """
        Map DSL type sang TypeScript type annotation.

        Args:
            field: Field definition

        Returns:
            Type annotation string
        """
        mapping = self.type_resolver.resolve(field)
        return mapping.annotation

    def render_value_object(self, vo: EmittedValueObject) -> str:
        """
        Render Value Object thành TypeScript code.

        Args:
            vo: Emitted Value Object

        Returns:
            Generated TypeScript code
        """
        # Build template context
        context = self._build_template_context(vo)

        try:
            template = self.template_env.get_template("value_object.ts.jinja2")
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

        # Build computed field getters
        computed_getters = self._generate_computed_getters(vo)

        # Build methods
        methods = self._generate_methods(vo)

        return {
            "vo": {
                "id": vo.id,
                "description": vo.description,
                "extends": vo.inherits_from,
                "tags": vo.tags,
                "is_frozen": vo.is_frozen,
            },
            "fields": vo.fields,
            "methods": methods,
            "computed_getters": computed_getters,
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
            "validator": [],
            "standard": [],
            "domain": [],
        }

        # Always include base imports
        imports["standard"].append('import { IsOptional, IsString, IsNumber, IsBoolean, IsDate } from "class-validator";')
        imports["standard"].append('import { Type } from "class-transformer";')

        # Check fields for specific validators
        has_is_string = False
        has_is_number = False
        has_is_boolean = False
        has_is_date = False
        has_min = False
        has_max = False
        has_min_length = False
        has_max_length = False
        has_is_enum = False

        for field_def in vo.fields:
            original = field_def.original
            field_type = original.get("type", "string")

            if field_type == "string":
                has_is_string = True
                if original.get("min_length"):
                    has_min_length = True
                if original.get("max_length"):
                    has_max_length = True
            elif field_type in ["integer", "decimal", "float"]:
                has_is_number = True
                if original.get("min"):
                    has_min = True
                if original.get("max"):
                    has_max = True
            elif field_type == "boolean":
                has_is_boolean = True
            elif field_type == "datetime":
                has_is_date = True
            elif field_type == "enum":
                has_is_enum = True
            elif field_type == "ref" and original.get("ref_type") == "value_object":
                ref_to = original.get("ref_to", "")
                imports["domain"].append(f'import {{{ref_to}}} from "./{ref_to.lower()}";')

        # Build validator import
        validators = ['IsOptional']
        if has_is_string:
            validators.append('IsString')
        if has_is_number:
            validators.append('IsNumber')
        if has_is_boolean:
            validators.append('IsBoolean')
        if has_is_date:
            validators.append('IsDate')
        if has_min:
            validators.append('Min')
        if has_max:
            validators.append('Max')
        if has_min_length:
            validators.append('MinLength')
        if has_max_length:
            validators.append('MaxLength')
        if has_is_enum:
            validators.append('IsEnum')

        imports["validator"] = [f'import {{{", ".join(validators)}}} from "class-validator";']

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
                    field_name=f"{field_def.name.capitalize()}Item",
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
            "export class " + class_name + " {",
            '  /** Nested class for ' + field_name + ' */',
            "",
        ]

        for nested_field in fields:
            nested_type = self.type_resolver.resolve(nested_field).annotation
            required = nested_field.get("required", True)

            lines.append(f"  @IsOptional()")
            lines.append(f"  {nested_field['name']}: {nested_type};")
            lines.append("")

        lines.append("  toDict(): Record<string, any> {")
        lines.append("    return {")
        for nested_field in fields:
            lines.append(f"      {nested_field['name']}: this.{nested_field['name']},")
        lines.append("    };")
        lines.append("  }")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _generate_computed_getters(self, vo: EmittedValueObject) -> list[str]:
        """
        Generate computed field getters.

        Args:
            vo: Emitted Value Object

        Returns:
            List of getter code strings
        """
        getters = []

        for field_def in vo.fields:
            if not field_def.is_computed:
                continue

            original = field_def.original
            field_type = original.get("type", "decimal")
            formula = original.get("formula", "")
            depends_on = original.get("depends_on", [])

            code = self.computed_evaluator.generate_typescript_code(
                field_name=field_def.name,
                field_type=field_type,
                formula=formula,
                depends_on=depends_on,
            )
            getters.append(code)

        return getters

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
            # Generate method stub - use return_type attribute (not 'returns')
            code = f"""
  /** {method_def.original.get('description', '')} */
  {method_def.name}{method_def.signature}: {method_def.return_type} {{
    // {method_def.original.get('logic', '')}
    throw new Error("Not implemented");
  }}"""
            methods.append(code)

        return methods

    def _generate_code_fallback(self, vo: EmittedValueObject) -> str:
        """
        Fallback code generation khi template không sẵn.

        Args:
            vo: Emitted Value Object

        Returns:
            Generated TypeScript code
        """
        # Check if we need Decimal import
        needs_decimal = any(
            f.original.get("type") == "decimal"
            for f in vo.fields
        )

        lines = [
            '"""',
            f"{vo.id} Value Object.",
            f"{vo.description or vo.id}",
            "Generated by Midicoder - NestJSValueObjectEmitter",
            "CP01: Domain Model - Value Objects",
            '"""',
            "",
            'import { IsOptional, IsString, IsNumber, IsBoolean, IsDate } from "class-validator";',
            'import { Type } from "class-transformer";',
        ]

        if needs_decimal:
            lines.append('import { Decimal } from "decimal.js";')

        lines.append("")
        lines.append("")
        lines.append("export class " + vo.name + "{")
        lines.append('  /**')
        lines.append(f'   * {vo.description or vo.id}')
        lines.append('   */')
        lines.append("")

        # Generate fields with validators
        for field_def in vo.fields:
            original = field_def.original
            field_type = original.get("type", "string")
            required = original.get("required", True)
            is_computed = field_def.is_computed
            is_frozen = vo.is_frozen

            if is_computed:
                # Computed field as getter
                formula = original.get("formula", "")
                lines.append("  get " + field_def.name + "(): " + field_def.type_annotation + " {")
                lines.append(f"    return {formula};")
                lines.append("  }")
                lines.append("")
                continue

            # Add decorators
            lines.append("  @IsOptional()")
            if field_type == "string":
                lines.append("  @IsString()")
                if original.get("min_length"):
                    lines.append(f"  @MinLength({original.get('min_length')})")
                if original.get("max_length"):
                    lines.append(f"  @MaxLength({original.get('max_length')})")
            elif field_type in ["integer", "decimal", "float"]:
                lines.append("  @IsNumber()")
                if original.get("min"):
                    lines.append(f"  @Min({original.get('min')})")
                if original.get("max"):
                    lines.append(f"  @Max({original.get('max')})")
            elif field_type == "boolean":
                lines.append("  @IsBoolean()")
            elif field_type == "datetime":
                lines.append("  @IsDate()")

            # Add readonly modifier for frozen/immutable VO
            readonly_prefix = "readonly " if is_frozen else ""
            lines.append(f"  {readonly_prefix}{field_def.name}: {field_def.type_annotation};")
            lines.append("")

        # Add toDict method
        lines.append("  toDict(): Record<string, any> {")
        lines.append("    return {")
        for field_def in vo.fields:
            lines.append(f"      {field_def.name}: this.{field_def.name},")
        lines.append("    };")
        lines.append("  }")

        # Build field assignments for static methods
        field_assignments = []
        for field_def in vo.fields:
            if not field_def.is_computed:
                original = field_def.original
                field_type = original.get("type", "string")
                if field_type == "decimal":
                    field_assignments.append(f"instance.{field_def.name} = parseFloat(data['{field_def.name}']);")
                elif field_type == "datetime":
                    field_assignments.append(f"instance.{field_def.name} = new Date(data['{field_def.name}']);")
                else:
                    field_assignments.append(f"instance.{field_def.name} = data['{field_def.name}'];")

        # Add fromDict static method
        lines.append("")
        lines.append("  static fromDict(data: Record<string, any>): " + vo.name + " {")
        lines.append("    const instance = new this();")
        for assignment in field_assignments:
            lines.append(f"    {assignment}")
        lines.append("    return instance;")
        lines.append("  }")

        # Add create static method (alias for fromDict)
        lines.append("")
        lines.append(f"  /** Tạo instance mới từ data */")
        lines.append("  static create(data: Record<string, any>): " + vo.name + " {")
        lines.append("    return this.fromDict(data);")
        lines.append("  }")

        lines.append("")
        lines.append("  toString(): string {")
        lines.append("    return JSON.stringify(this.toDict());")
        lines.append("  }")

        lines.append("}")

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
                ErrorCode.CP01_VALUE_OBJECT_NOT_FOUND,
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
            file_path = output_dir / f"{vo_lower}.ts"
            file_path.write_text(emitted_vo.full_content, encoding="utf-8")

            emitted_files.append((file_path, emitted_vo.full_content))

        return emitted_files