"""
Value Object Base Emitter

Abstract base class cho Value Object code generation.
Cung cấp infrastructure cho FastAPI/NestJS implementations.

Author: Midicoder Team
Version: 2.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from midicoder.dsl.projection import (
    FieldDefinition,
    MethodDefinition,
    ValidationRule,
    ExtendedValueObjectParams,
)


@dataclass
class EmittedField:
    """
    Field đã được emit với type mapping và metadata.

    Attributes:
        name: Tên field
        original: Original FieldDefinition từ DSL
        type_annotation: Type annotation cho target language (Python/TypeScript)
        is_required: Có phải required field không
        is_computed: Có phải computed field không
        default_value: Giá trị mặc định (nếu có)
        validation_rules: Danh sách validation rules
        nested_class: Nested class name nếu là complex type
    """

    name: str
    original: FieldDefinition
    type_annotation: str
    is_required: bool
    is_computed: bool
    default_value: Optional[Any] = None
    validation_rules: list[str] = field(default_factory=list)
    nested_class: Optional[str] = None


@dataclass
class EmittedMethod:
    """
    Method đã được emit với signature và implementation.

    Attributes:
        name: Tên method
        original: Original MethodDefinition từ DSL
        signature: Method signature (target language)
        implementation: Method implementation (target language)
        is_async: Có phải async method không
        return_type: Return type annotation
    """

    name: str
    original: MethodDefinition
    signature: str
    implementation: str
    is_async: bool = False
    return_type: str = ""


@dataclass
class EmittedValidationRule:
    """
    Validation rule đã được emit.

    Attributes:
        name: Tên rule
        original: Original ValidationRule từ DSL
        condition: Condition expression
        error_code: Error code
        error_message: Error message (tiếng Việt)
        implementation: Implementation code
    """

    name: str
    original: ValidationRule
    condition: str
    error_code: str
    error_message: str
    implementation: str


@dataclass
class EmittedValueObject:
    """
    Value Object đã được emit hoàn chỉnh.

    Attributes:
        id: VO ID từ DSL
        name: Class name (PascalCase)
        description: Mô tả VO
        fields: Danh sách emitted fields
        methods: Danh sách emitted methods
        validation_rules: Danh sách emitted validation rules
        inherits_from: Parent VO name (nếu có inheritance)
        tags: Danh sách tags
        is_frozen: Có phải immutable VO không
        full_content: Full generated code
    """

    id: str
    name: str
    description: str
    fields: list[EmittedField]
    methods: list[EmittedMethod]
    validation_rules: list[EmittedValidationRule]
    inherits_from: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    is_frozen: bool = True
    full_content: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "fields": [
                {
                    "name": f.name,
                    "type_annotation": f.type_annotation,
                    "is_required": f.is_required,
                    "is_computed": f.is_computed,
                    "default_value": f.default_value,
                    "validation_rules": f.validation_rules,
                    "nested_class": f.nested_class,
                }
                for f in self.fields
            ],
            "methods": [
                {
                    "name": m.name,
                    "signature": m.signature,
                    "implementation": m.implementation,
                    "is_async": m.is_async,
                    "return_type": m.return_type,
                }
                for m in self.methods
            ],
            "validation_rules": [
                {
                    "name": r.name,
                    "condition": r.condition,
                    "error_code": r.error_code,
                    "error_message": r.error_message,
                    "implementation": r.implementation,
                }
                for r in self.validation_rules
            ],
            "inherits_from": self.inherits_from,
            "tags": self.tags,
            "is_frozen": self.is_frozen,
            "full_content": self.full_content,
        }


class ValueObjectEmitter(ABC):
    """
    Abstract base class cho Value Object emitters.

    Cung cấp common functionality cho FastAPI/NestJS implementations.
    Subclasses cần implement template rendering cho target language.

    Usage:
        class FastAPIValueObjectEmitter(ValueObjectEmitter):
            def render_value_object(self, vo: EmittedValueObject) -> str:
                # Jinja2 template rendering
                return self._template.render(vo.to_dict())
    """

    def __init__(self) -> None:
        """Initialize emitter."""
        self._nested_classes: dict[str, EmittedValueObject] = {}

    @abstractmethod
    def render_value_object(self, vo: EmittedValueObject) -> str:
        """
        Render Value Object thành target language code.

        Args:
            vo: Emitted Value Object

        Returns:
            Generated code string
        """
        pass

    @abstractmethod
    def map_type(self, field: FieldDefinition) -> str:
        """
        Map DSL type sang target language type.

        Args:
            field: Field definition

        Returns:
            Type annotation string
        """
        pass

    def emit(
        self,
        vo_params: ExtendedValueObjectParams,
        parent_vo_map: Optional[dict[str, ExtendedValueObjectParams]] = None
    ) -> EmittedValueObject:
        """
        Emit Value Object từ DSL params.

        Process:
        1. Resolve inheritance chain (nếu có extends)
        2. Merge fields từ parent VO
        3. Resolve types cho mỗi field
        4. Emit methods
        5. Emit validation rules
        6. Render final code

        Args:
            vo_params: Value Object params từ DSL
            parent_vo_map: Map của parent VOs cho inheritance resolution

        Returns:
            Emitted Value Object
        """
        # Step 1: Resolve inheritance
        inherits_from = vo_params.get("extends")
        parent_fields: list[FieldDefinition] = []

        if inherits_from and parent_vo_map:
            parent_params = parent_vo_map.get(inherits_from)
            if parent_params:
                parent_fields = parent_params.get("fields", [])
            else:
                raise ValueError(
                    f"Parent Value Object '{inherits_from}' không tìm thấy"
                )

        # Step 2: Merge fields (child fields override parent)
        child_fields = vo_params.get("fields", [])
        merged_fields = self._merge_fields(parent_fields, child_fields)

        # Step 3: Resolve types và emit fields
        emitted_fields = []
        for field_def in merged_fields:
            emitted_field = self._emit_field(field_def)
            emitted_fields.append(emitted_field)

        # Step 4: Emit methods
        methods = vo_params.get("methods", [])
        emitted_methods = [self._emit_method(m) for m in methods]

        # Step 5: Emit validation rules
        validation_rules = vo_params.get("validation_rules", [])
        emitted_rules = [self._emit_validation_rule(r) for r in validation_rules]

        # Step 6: Create EmittedValueObject
        vo_name = self._to_pascal_case(vo_params["id"])
        emitted_vo = EmittedValueObject(
            id=vo_params["id"],
            name=vo_name,
            description=vo_params.get("description", ""),
            fields=emitted_fields,
            methods=emitted_methods,
            validation_rules=emitted_rules,
            inherits_from=inherits_from,
            tags=vo_params.get("tags", []),
            is_frozen=vo_params.get("immutable", True),
        )

        # Step 7: Render final code
        emitted_vo.full_content = self.render_value_object(emitted_vo)

        return emitted_vo

    def _emit_field(self, field_def: FieldDefinition) -> EmittedField:
        """
        Emit một field.

        Args:
            field_def: Field definition từ DSL

        Returns:
            Emitted field
        """
        type_annotation = self.map_type(field_def)

        return EmittedField(
            name=field_def["name"],
            original=field_def,
            type_annotation=type_annotation,
            is_required=field_def.get("required", False),
            is_computed=field_def.get("computed", False),
            default_value=field_def.get("default"),
            nested_class=self._emit_nested_class(field_def),
        )

    def _emit_method(self, method_def: MethodDefinition) -> EmittedMethod:
        """
        Emit một method.

        Args:
            method_def: Method definition từ DSL

        Returns:
            Emitted method
        """
        # Build signature
        params_str = self._build_method_params(method_def.get("params", []))
        return_type = method_def.get("returns", "void")
        return_annotation = self.map_type_from_name(return_type)

        signature = (
            f"def {method_def['name']}({params_str}) -> {return_annotation}:"
        )

        # Implementation sẽ được template render
        implementation = f"# {method_def.get('logic', '')}"

        return EmittedMethod(
            name=method_def["name"],
            original=method_def,
            signature=signature,
            implementation=implementation,
            is_async=method_def.get("async_", False),
            return_type=return_annotation,
        )

    def _emit_validation_rule(self, rule: ValidationRule) -> EmittedValidationRule:
        """
        Emit một validation rule.

        Args:
            rule: Validation rule từ DSL

        Returns:
            Emitted validation rule
        """
        # Implementation sẽ được template render
        implementation = f"raise ValueError('{rule['error_message']}')"

        return EmittedValidationRule(
            name=rule["name"],
            original=rule,
            condition=rule["condition"],
            error_code=rule["error_code"],
            error_message=rule["error_message"],
            implementation=implementation,
        )

    def _merge_fields(
        self,
        parent_fields: list[FieldDefinition],
        child_fields: list[FieldDefinition]
    ) -> list[FieldDefinition]:
        """
        Merge fields từ parent và child.

        Child fields override parent fields với cùng name.

        Args:
            parent_fields: Fields từ parent VO
            child_fields: Fields từ child VO

        Returns:
            Merged field list
        """
        merged = {}

        # Add parent fields
        for field in parent_fields:
            merged[field["name"]] = field

        # Override với child fields
        for field in child_fields:
            merged[field["name"]] = field

        return list(merged.values())

    def _emit_nested_class(
        self, field_def: FieldDefinition
    ) -> Optional[str]:
        """
        Emit nested class cho complex types.

        Args:
            field_def: Field definition

        Returns:
            Nested class name nếu là complex type
        """
        field_type = field_def.get("type", "")

        if field_type in ("object", "array"):
            # Tạo nested class name
            nested_name = f"{field_def['name'].capitalize()}Item"
            return nested_name

        return None

    def _build_method_params(
        self, params: list[FieldDefinition]
    ) -> str:
        """
        Build method parameter string.

        Args:
            params: List of parameter definitions

        Returns:
            Parameter string
        """
        if not params:
            return "self"

        param_strings = ["self"]
        for param in params:
            type_ann = self.map_type(param)
            param_strings.append(f"{param['name']}: {type_ann}")

        return ", ".join(param_strings)

    def map_type_from_name(self, type_name: str) -> str:
        """
        Map type name (string) sang type annotation.

        Args:
            type_name: Type name string

        Returns:
            Type annotation
        """
        # Default mapping cho primitive types
        type_map = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "decimal": "Decimal",
            "datetime": "datetime",
            "void": "None",
        }
        return type_map.get(type_name, type_name)

    def _to_pascal_case(self, name: str) -> str:
        """
        Convert name sang PascalCase.

        Args:
            name: Input name

        Returns:
            PascalCase name
        """
        # Handle kebab-case và snake_case
        parts = name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts)

    def get_nested_classes(self) -> dict[str, EmittedValueObject]:
        """
        Get all emitted nested classes.

        Returns:
            Map của nested class names → EmittedValueObject
        """
        return self._nested_classes.copy()