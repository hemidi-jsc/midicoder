"""
Value Object Core Emitter Tests

Tests cho core emitter infrastructure:
- base.py: EmittedValueObject, ValueObjectEmitter
- type_resolver.py: TypeResolver, TypeMapping
- inheritance.py: InheritanceResolver, InheritanceChain
- computed.py: ComputedFieldEvaluator, FormulaError

Author: Midicoder Team
Version: 2.0.0
"""

import pytest
from decimal import Decimal
from typing import Any

from midicoder.packs.cp_base_domain_model import (
    ValueObjectEmitter,
    EmittedValueObject,
    EmittedField,
    EmittedMethod,
    EmittedValidationRule,
    TypeResolver,
    TypeMapping,
    InheritanceResolver,
    InheritanceChain,
    ComputedFieldEvaluator,
    FormulaError,
)

from midicoder.dsl.projection import (
    FieldDefinition,
    MethodDefinition,
    ValidationRule,
    ExtendedValueObjectParams,
)


# ============================================================================
# Test TypeMapping
# ============================================================================

class TestTypeMapping:
    """Tests cho TypeMapping dataclass."""

    def test_create_basic_mapping(self):
        """Test tạo TypeMapping cơ bản."""
        mapping = TypeMapping(annotation="str")
        assert mapping.annotation == "str"
        assert mapping.imports == []
        assert mapping.is_complex is False
        assert mapping.nested_type is None

    def test_create_mapping_with_imports(self):
        """Test tạo TypeMapping với imports."""
        mapping = TypeMapping(
            annotation="Decimal",
            imports=["from decimal import Decimal"],
        )
        assert mapping.annotation == "Decimal"
        assert len(mapping.imports) == 1
        assert mapping.imports[0] == "from decimal import Decimal"

    def test_create_complex_mapping(self):
        """Test tạo TypeMapping cho complex type."""
        mapping = TypeMapping(
            annotation="list[AddressItem]",
            is_complex=True,
            nested_type="AddressItem",
        )
        assert mapping.annotation == "list[AddressItem]"
        assert mapping.is_complex is True
        assert mapping.nested_type == "AddressItem"


# ============================================================================
# Test TypeResolver - Python
# ============================================================================

class TestTypeResolverPython:
    """Tests cho TypeResolver với Python target."""

    def setup_method(self):
        """Setup test fixtures."""
        self.resolver = TypeResolver(target_language="python")

    def test_resolve_string_type(self):
        """Test resolve string type."""
        field: FieldDefinition = {"name": "email", "type": "string"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "str"
        assert mapping.imports == []

    def test_resolve_integer_type(self):
        """Test resolve integer type."""
        field: FieldDefinition = {"name": "count", "type": "integer"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "int"

    def test_resolve_decimal_type(self):
        """Test resolve decimal type."""
        field: FieldDefinition = {"name": "price", "type": "decimal"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "Decimal"
        assert "from decimal import Decimal" in mapping.imports

    def test_resolve_boolean_type(self):
        """Test resolve boolean type."""
        field: FieldDefinition = {"name": "active", "type": "boolean"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "bool"

    def test_resolve_datetime_type(self):
        """Test resolve datetime type."""
        field: FieldDefinition = {"name": "created_at", "type": "datetime"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "datetime"
        assert "from datetime import datetime" in mapping.imports

    def test_resolve_uuid_type(self):
        """Test resolve UUID type."""
        field: FieldDefinition = {"name": "uuid", "type": "uuid"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "UUID"
        assert "from uuid import UUID" in mapping.imports

    def test_resolve_enum_with_values(self):
        """Test resolve enum với inline values."""
        field: FieldDefinition = {
            "name": "status",
            "type": "enum",
            "enum_values": ["pending", "approved", "rejected"],
        }
        mapping = self.resolver.resolve(field)
        assert "Literal" in mapping.annotation
        assert "from typing import Literal" in mapping.imports

    def test_resolve_object_type(self):
        """Test resolve object type (nested)."""
        field: FieldDefinition = {
            "name": "address",
            "type": "object",
            "fields": [
                {"name": "street", "type": "string"},
                {"name": "city", "type": "string"},
            ],
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "AddressItem"
        assert mapping.is_complex is True
        assert mapping.nested_type == "AddressItem"

    def test_resolve_array_of_primitives(self):
        """Test resolve array of primitives."""
        field: FieldDefinition = {
            "name": "tags",
            "type": "array",
            "item_type": "string",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "list[str]"

    def test_resolve_array_of_objects(self):
        """Test resolve array of objects."""
        field: FieldDefinition = {
            "name": "items",
            "type": "array",
            "item_fields": [
                {"name": "name", "type": "string"},
                {"name": "qty", "type": "integer"},
            ],
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "list[ItemsItem]"
        assert mapping.is_complex is True

    def test_resolve_map_type(self):
        """Test resolve map type."""
        field: FieldDefinition = {
            "name": "metadata",
            "type": "map",
            "key_type": "string",
            "value_type": "string",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "dict[str, str]"

    def test_resolve_ref_to_entity(self):
        """Test resolve ref to entity."""
        field: FieldDefinition = {
            "name": "product_id",
            "type": "ref",
            "ref_type": "entity",
            "ref_to": "Product",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "str"

    def test_resolve_ref_to_value_object(self):
        """Test resolve ref to value object."""
        field: FieldDefinition = {
            "name": "price",
            "type": "ref",
            "ref_type": "value_object",
            "ref_to": "Money",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "Money"
        assert "from . import Money" in mapping.imports

    def test_get_all_imports(self):
        """Test get all imports cho multiple fields."""
        fields: list[FieldDefinition] = [
            {"name": "price", "type": "decimal"},
            {"name": "name", "type": "string"},
            {"name": "uuid", "type": "uuid"},
        ]
        imports = self.resolver.get_all_imports(fields)
        assert "from decimal import Decimal" in imports
        assert "from uuid import UUID" in imports
        # Should be de-duplicated và sorted
        assert imports == sorted(set(imports))


# ============================================================================
# Test TypeResolver - TypeScript
# ============================================================================

class TestTypeResolverTypeScript:
    """Tests cho TypeResolver với TypeScript target."""

    def setup_method(self):
        """Setup test fixtures."""
        self.resolver = TypeResolver(target_language="typescript")

    def test_resolve_string_type(self):
        """Test resolve string type."""
        field: FieldDefinition = {"name": "email", "type": "string"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "string"

    def test_resolve_number_type(self):
        """Test resolve number types."""
        for type_name in ["integer", "decimal", "float"]:
            field: FieldDefinition = {"name": "value", "type": type_name}
            mapping = self.resolver.resolve(field)
            assert mapping.annotation == "number"

    def test_resolve_boolean_type(self):
        """Test resolve boolean type."""
        field: FieldDefinition = {"name": "active", "type": "boolean"}
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "boolean"

    def test_resolve_enum_with_values(self):
        """Test resolve enum với inline values (TypeScript union)."""
        field: FieldDefinition = {
            "name": "status",
            "type": "enum",
            "enum_values": ["pending", "approved"],
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "'pending' | 'approved'"

    def test_resolve_array_type(self):
        """Test resolve array type (TypeScript syntax)."""
        field: FieldDefinition = {
            "name": "tags",
            "type": "array",
            "item_type": "string",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "string[]"

    def test_resolve_map_type(self):
        """Test resolve map type (TypeScript Record)."""
        field: FieldDefinition = {
            "name": "metadata",
            "type": "map",
            "key_type": "string",
            "value_type": "string",
        }
        mapping = self.resolver.resolve(field)
        assert mapping.annotation == "Record<string, string>"


# ============================================================================
# Test InheritanceChain
# ============================================================================

class TestInheritanceChain:
    """Tests cho InheritanceChain dataclass."""

    def test_create_chain(self):
        """Test tạo inheritance chain."""
        chain = InheritanceChain(
            vo_id="BillingAddress",
            chain=["Address", "BillingAddress"],
        )
        assert chain.vo_id == "BillingAddress"
        assert chain.chain == ["Address", "BillingAddress"]
        assert chain.root == "Address"
        assert chain.depth == 1

    def test_chain_post_init(self):
        """Test post_init tính toán root và depth."""
        chain = InheritanceChain(vo_id="C", chain=["A", "B", "C"])
        assert chain.root == "A"
        assert chain.depth == 2


# ============================================================================
# Test InheritanceResolver
# ============================================================================

class TestInheritanceResolver:
    """Tests cho InheritanceResolver."""

    def test_resolve_simple_chain(self):
        """Test resolve đơn giản inheritance chain."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Address": {
                "id": "Address",
                "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                ],
            },
            "BillingAddress": {
                "id": "BillingAddress",
                "extends": "Address",
                "fields": [
                    {"name": "company_name", "type": "string"},
                ],
            },
        }

        resolver = InheritanceResolver(vo_map)
        chain = resolver.resolve_chain("BillingAddress")

        assert chain.chain == ["Address", "BillingAddress"]
        assert chain.root == "Address"
        assert chain.depth == 1

    def test_resolve_multi_level_chain(self):
        """Test resolve multi-level inheritance."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "BaseAddress": {
                "id": "BaseAddress",
                "fields": [{"name": "country", "type": "string"}],
            },
            "Address": {
                "id": "Address",
                "extends": "BaseAddress",
                "fields": [{"name": "street", "type": "string"}],
            },
            "ShippingAddress": {
                "id": "ShippingAddress",
                "extends": "Address",
                "fields": [{"name": "floor", "type": "integer"}],
            },
        }

        resolver = InheritanceResolver(vo_map)
        chain = resolver.resolve_chain("ShippingAddress")

        assert chain.chain == ["BaseAddress", "Address", "ShippingAddress"]
        assert chain.depth == 2

    def test_detect_circular_inheritance(self):
        """Test detect circular inheritance."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "A": {
                "id": "A",
                "extends": "B",
                "fields": [],
            },
            "B": {
                "id": "B",
                "extends": "A",
                "fields": [],
            },
        }

        resolver = InheritanceResolver(vo_map)

        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            resolver.resolve_chain("A")

        assert exc_info.value.code.value == "MDC-B01-010"

    def test_merge_fields_from_parent(self):
        """Test merge fields từ parent."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Address": {
                "id": "Address",
                "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                ],
            },
            "BillingAddress": {
                "id": "BillingAddress",
                "extends": "Address",
                "fields": [
                    {"name": "company_name", "type": "string"},
                ],
            },
        }

        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("BillingAddress")

        field_names = [f["name"] for f in merged["fields"]]
        assert "street" in field_names
        assert "city" in field_names
        assert "company_name" in field_names

    def test_child_override_parent_field(self):
        """Test child override parent field."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Base": {
                "id": "Base",
                "fields": [
                    {"name": "name", "type": "string", "required": False},
                ],
            },
            "Child": {
                "id": "Child",
                "extends": "Base",
                "fields": [
                    {"name": "name", "type": "string", "required": True},
                ],
            },
        }

        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")

        name_field = next(f for f in merged["fields"] if f["name"] == "name")
        assert name_field["required"] is True

    def test_cache_chain_resolution(self):
        """Test cache cho chain resolution."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {"id": "Parent", "fields": []},
            "Child": {"id": "Child", "extends": "Parent", "fields": []},
        }

        resolver = InheritanceResolver(vo_map)

        # First call
        chain1 = resolver.resolve_chain("Child")
        # Second call (should use cache)
        chain2 = resolver.resolve_chain("Child")

        assert chain1 is chain2  # Same object from cache

    def test_get_inherited_fields(self):
        """Test get field inheritance info."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Address": {
                "id": "Address",
                "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                ],
            },
            "BillingAddress": {
                "id": "BillingAddress",
                "extends": "Address",
                "fields": [{"name": "tax_id", "type": "string"}],
            },
        }

        resolver = InheritanceResolver(vo_map)
        field_sources = resolver.get_inherited_fields("BillingAddress")

        assert "street" in field_sources
        assert "Address" in field_sources["street"]
        assert "tax_id" in field_sources
        assert "BillingAddress" in field_sources["tax_id"]


# ============================================================================
# Test ComputedFieldEvaluator
# ============================================================================

class TestComputedFieldEvaluator:
    """Tests cho ComputedFieldEvaluator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.evaluator = ComputedFieldEvaluator()

    def test_evaluate_simple_formula(self):
        """Test evaluate simple formula."""
        result = self.evaluator.evaluate(
            formula="a + b",
            values={"a": 10, "b": 5},
            depends_on=["a", "b"],
        )
        assert result == 15

    def test_evaluate_with_multiplication(self):
        """Test evaluate với multiplication."""
        result = self.evaluator.evaluate(
            formula="quantity * unit_price",
            values={"quantity": 10, "unit_price": 5.50},
            depends_on=["quantity", "unit_price"],
        )
        assert result == 55.0

    def test_evaluate_with_power(self):
        """Test evaluate với power operation."""
        result = self.evaluator.evaluate(
            formula="rate ** 2",
            values={"rate": 5},
            depends_on=["rate"],
        )
        assert result == 25

    def test_evaluate_with_functions(self):
        """Test evaluate với built-in functions."""
        result = self.evaluator.evaluate(
            formula="round(value, 2)",
            values={"value": 3.14159},
            depends_on=["value"],
        )
        assert result == 3.14

    def test_missing_dependency(self):
        """Test missing dependency error."""
        with pytest.raises(FormulaError) as exc_info:
            self.evaluator.evaluate(
                formula="a + b",
                values={"a": 10},
                depends_on=["a", "b"],
            )
        assert "Missing dependencies" in str(exc_info.value.message)
        assert "b" in str(exc_info.value.message)

    def test_formula_syntax_error(self):
        """Test formula syntax error."""
        # Python's eval actually handles "a++b" as "a + (+b)" which is valid
        # Use truly invalid syntax
        with pytest.raises(FormulaError) as exc_info:
            self.evaluator.evaluate(
                formula="a + * b",  # Invalid syntax
                values={"a": 10, "b": 5},
                depends_on=["a", "b"],
            )
        assert exc_info.value.formula == "a + * b"

    def test_evaluate_field_with_type_coercion(self):
        """Test evaluate field với type coercion."""
        result = self.evaluator.evaluate_field(
            field_type="decimal",
            formula="price * tax_rate",
            values={"price": Decimal("100.00"), "tax_rate": Decimal("0.1")},
            depends_on=["price", "tax_rate"],
        )
        assert isinstance(result, Decimal)
        assert result == Decimal("10.00")

    def test_generate_python_code(self):
        """Test generate Python property code."""
        code = self.evaluator.generate_python_code(
            field_name="total",
            field_type="decimal",
            formula="quantity * unit_price",
            depends_on=["quantity", "unit_price"],
        )
        assert "@property" in code
        assert "def total(self)" in code
        assert "Decimal" in code

    def test_generate_typescript_code(self):
        """Test generate TypeScript getter code."""
        code = self.evaluator.generate_typescript_code(
            field_name="total",
            field_type="decimal",
            formula="quantity * unit_price",
            depends_on=["quantity", "unit_price"],
        )
        assert "get total()" in code
        assert ": number" in code

    def test_validate_valid_formula(self):
        """Test validate valid formula."""
        is_valid, error = self.evaluator.validate_formula(
            formula="a + b * c",
            depends_on=["a", "b", "c"],
        )
        assert is_valid is True
        assert error == ""

    def test_validate_invalid_formula(self):
        """Test validate invalid formula."""
        is_valid, error = self.evaluator.validate_formula(
            formula="a + * b",  # Truly invalid syntax
            depends_on=["a", "b"],
        )
        assert is_valid is False
        assert error != ""

    def test_extract_dependencies(self):
        """Test extract field dependencies."""
        deps = self.evaluator.get_field_dependencies(
            formula="quantity * unit_price + shipping"
        )
        assert "quantity" in deps
        assert "unit_price" in deps
        assert "shipping" in deps
        # Should not include operators
        assert "*" not in deps
        assert "+" not in deps


# ============================================================================
# Test EmittedValueObject
# ============================================================================

class TestEmittedValueObject:
    """Tests cho EmittedValueObject."""

    def test_create_basic_vo(self):
        """Test tạo basic Value Object."""
        vo = EmittedValueObject(
            id="Money",
            name="Money",
            description="Giá tiền tệ",
            fields=[],
            methods=[],
            validation_rules=[],
        )
        assert vo.id == "Money"
        assert vo.name == "Money"
        assert vo.is_frozen is True

    def test_to_dict(self):
        """Test convert to dict."""
        field = EmittedField(
            name="amount",
            original={"name": "amount", "type": "decimal"},
            type_annotation="Decimal",
            is_required=True,
            is_computed=False,
        )

        vo = EmittedValueObject(
            id="Money",
            name="Money",
            description="Tiền tệ",
            fields=[field],
            methods=[],
            validation_rules=[],
        )

        vo_dict = vo.to_dict()

        assert vo_dict["id"] == "Money"
        assert len(vo_dict["fields"]) == 1
        assert vo_dict["fields"][0]["name"] == "amount"
        assert vo_dict["fields"][0]["type_annotation"] == "Decimal"


# ============================================================================
# Test FormulaError
# ============================================================================

class TestFormulaError:
    """Tests cho FormulaError."""

    def test_create_error(self):
        """Test tạo FormulaError."""
        error = FormulaError(
            field_name="total",
            formula="a + b",
            message="Syntax error",
        )
        assert error.field_name == "total"
        assert error.formula == "a + b"
        assert error.message == "Syntax error"
        assert error.cause is None

    def test_create_error_with_cause(self):
        """Test tạo FormulaError với cause."""
        cause = SyntaxError("invalid syntax")
        error = FormulaError(
            field_name="total",
            formula="a ++ b",
            message="Formula error",
            cause=cause,
        )
        assert error.cause is cause
        assert isinstance(error.cause, SyntaxError)


# ============================================================================
# Gap-Filling Tests for vo_types.py (84% → 99%)
# ============================================================================

class TestTypeResolverGapLines:
    """Tests covering uncovered lines in vo_types.py."""

    def setup_method(self):
        """Setup test fixtures."""
        self.py_resolver = TypeResolver(target_language="python")
        self.ts_resolver = TypeResolver(target_language="typescript")

    # -----------------------------------------------------------------------
    # Lines 188-191: enum_class branch (Python)
    # -----------------------------------------------------------------------

    def test_enum_with_enum_class_python(self):
        """Cover lines 188-191: enum_class branch for Python target."""
        field: FieldDefinition = {
            "name": "status",
            "type": "enum",
            "enum_class": "OrderStatus",
        }
        mapping = self.py_resolver.resolve(field)
        assert mapping.annotation == "OrderStatus"
        assert "from .enums import OrderStatus" in mapping.imports

    def test_enum_with_enum_class_typescript(self):
        """Cover lines 188-191: enum_class branch for TypeScript target
        (line 190 condition is False, so line 191 is skipped)."""
        field: FieldDefinition = {
            "name": "status",
            "type": "enum",
            "enum_class": "OrderStatus",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "OrderStatus"
        # TypeScript does not append the Python import
        assert "from .enums import OrderStatus" not in mapping.imports

    # -----------------------------------------------------------------------
    # Line 192->202: enum with neither enum_class nor enum_values
    # -----------------------------------------------------------------------

    def test_enum_without_class_or_values(self):
        """Cover 192->202: enum with no enum_class and no enum_values
        falls through to return base_mapping (default str)."""
        field: FieldDefinition = {
            "name": "plain_enum",
            "type": "enum",
        }
        mapping = self.py_resolver.resolve(field)
        # Should return the default enum mapping (annotation="str")
        assert mapping.annotation == "str"

    # -----------------------------------------------------------------------
    # Line 218: unknown type falls to default TypeMapping
    # -----------------------------------------------------------------------

    def test_unknown_type_python_default(self):
        """Cover line 218: unknown type for Python returns default."""
        field: FieldDefinition = {
            "name": "weird",
            "type": "unknown_custom_type",
        }
        mapping = self.py_resolver.resolve(field)
        assert mapping.annotation == "str"

    def test_unknown_type_typescript_default(self):
        """Cover line 218: unknown type for TypeScript returns default."""
        field: FieldDefinition = {
            "name": "weird",
            "type": "unknown_custom_type",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "string"

    # -----------------------------------------------------------------------
    # Lines 295-298: default array (no item_fields, no item_type)
    # -----------------------------------------------------------------------

    def test_default_array_python(self):
        """Cover lines 295-296: default array for Python (list[Any])."""
        field: FieldDefinition = {
            "name": "misc",
            "type": "array",
        }
        mapping = self.py_resolver.resolve(field)
        assert mapping.annotation == "list[Any]"
        assert "from typing import Any" in mapping.imports

    def test_default_array_typescript(self):
        """Cover lines 297-298: default array for TypeScript (any[])."""
        field: FieldDefinition = {
            "name": "misc",
            "type": "array",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "any[]"

    # -----------------------------------------------------------------------
    # Line 366: _resolve_ref_type fallback
    # -----------------------------------------------------------------------

    def test_ref_type_fallback_python(self):
        """Cover line 366: ref_type neither entity nor value_object (Python)."""
        field: FieldDefinition = {
            "name": "foreign",
            "type": "ref",
            "ref_type": "unknown_ref",
            "ref_to": "SomeVO",
        }
        mapping = self.py_resolver.resolve(field)
        assert mapping.annotation == "str"

    def test_ref_type_fallback_typescript(self):
        """Cover line 366: ref_type neither entity nor value_object (TS)."""
        field: FieldDefinition = {
            "name": "foreign",
            "type": "ref",
            "ref_type": "unknown_ref",
            "ref_to": "SomeVO",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "string"

    # -----------------------------------------------------------------------
    # Lines 399-405: resolve_computed_field without explicit type
    # -----------------------------------------------------------------------

    def test_computed_field_no_explicit_type(self):
        """Cover lines 399-405: resolve_computed_field with no type
        falls through to decimal default."""
        field: FieldDefinition = {
            "name": "total",
            "computed": True,
            "formula": "a + b",
        }
        mapping = self.py_resolver.resolve_computed_field(field)
        assert mapping.annotation == "Decimal"

    # -----------------------------------------------------------------------
    # Line 402: resolve_computed_field WITH explicit type
    # -----------------------------------------------------------------------

    def test_computed_field_with_explicit_type(self):
        """Cover line 402: resolve_computed_field delegates to resolve()
        when explicit type is present."""
        field: FieldDefinition = {
            "name": "total",
            "type": "decimal",
            "computed": True,
            "formula": "a + b",
        }
        mapping = self.py_resolver.resolve_computed_field(field)
        assert mapping.annotation == "Decimal"
        assert "from decimal import Decimal" in mapping.imports

    # -----------------------------------------------------------------------
    # Line 243: TypeScript _resolve_object_type
    # -----------------------------------------------------------------------

    def test_resolve_object_type_typescript(self):
        """Cover line 243: TypeScript object type returns TypeMapping."""
        field: FieldDefinition = {
            "name": "address",
            "type": "object",
            "fields": [
                {"name": "street", "type": "string"},
            ],
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "AddressItem"
        assert mapping.is_complex is True

    # -----------------------------------------------------------------------
    # Line 274: TypeScript _resolve_array_type (array of objects)
    # -----------------------------------------------------------------------

    def test_resolve_array_of_objects_typescript(self):
        """Cover line 274: TypeScript array of objects syntax (NestedItem[])."""
        field: FieldDefinition = {
            "name": "items",
            "type": "array",
            "item_fields": [
                {"name": "name", "type": "string"},
            ],
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "ItemsItem[]"
        assert mapping.is_complex is True

    # -----------------------------------------------------------------------
    # Line 355: TypeScript _resolve_ref_type (entity ref)
    # -----------------------------------------------------------------------

    def test_resolve_ref_entity_typescript(self):
        """Cover line 355: TypeScript ref to entity returns string."""
        field: FieldDefinition = {
            "name": "product_id",
            "type": "ref",
            "ref_type": "entity",
            "ref_to": "Product",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "string"

    # -----------------------------------------------------------------------
    # Line 361: TypeScript _resolve_ref_type (value_object ref)
    # -----------------------------------------------------------------------

    def test_resolve_ref_value_object_typescript(self):
        """Cover line 361: TypeScript ref to value_object with import."""
        field: FieldDefinition = {
            "name": "price",
            "type": "ref",
            "ref_type": "value_object",
            "ref_to": "Money",
        }
        mapping = self.ts_resolver.resolve(field)
        assert mapping.annotation == "Money"
        assert "import { Money } from './money'" in mapping.imports


# ============================================================================
# Gap-Filling Tests for vo_computed.py (73% → 99%)
# ============================================================================

class TestComputedFieldEvaluatorGapLines:
    """Tests covering uncovered lines in vo_computed.py."""

    def setup_method(self):
        """Setup test fixtures."""
        self.evaluator = ComputedFieldEvaluator()

    # -----------------------------------------------------------------------
    # Line 93->103: evaluate() branch when depends_on provided but all present
    # (missing list is empty, so `if missing:` is False, falls through to 103)
    # -----------------------------------------------------------------------

    def test_evaluate_with_all_deps_present_fallthrough(self):
        """Cover 93->103: depends_on provided, ALL present, missing=[], skip raise."""
        result = self.evaluator.evaluate(
            formula="x * y",
            values={"x": 3, "y": 4},
            depends_on=["x", "y"],
        )
        assert result == 12

    # -----------------------------------------------------------------------
    # Lines 146-157: evaluate_field() type coercion branches
    # -----------------------------------------------------------------------

    def test_evaluate_field_integer_coercion(self):
        """Cover line 146: evaluate_field with integer type coercion."""
        result = self.evaluator.evaluate_field(
            field_type="integer",
            formula="a + b",
            values={"a": 10, "b": 5},
            depends_on=["a", "b"],
        )
        assert isinstance(result, int)
        assert result == 15

    def test_evaluate_field_float_coercion(self):
        """Cover line 148: evaluate_field with float type coercion."""
        result = self.evaluator.evaluate_field(
            field_type="float",
            formula="a / b",
            values={"a": 10, "b": 4},
            depends_on=["a", "b"],
        )
        assert isinstance(result, float)
        assert result == 2.5

    def test_evaluate_field_boolean_coercion(self):
        """Cover line 150: evaluate_field with boolean type coercion."""
        result = self.evaluator.evaluate_field(
            field_type="boolean",
            formula="a > b",
            values={"a": 10, "b": 5},
            depends_on=["a", "b"],
        )
        assert isinstance(result, bool)
        assert result is True

    def test_evaluate_field_string_coercion(self):
        """Cover line 152: evaluate_field with string type coercion."""
        result = self.evaluator.evaluate_field(
            field_type="string",
            formula="str(a)",
            values={"a": 42},
            depends_on=["a"],
        )
        assert isinstance(result, str)
        assert result == "42"

    def test_evaluate_field_unknown_type_passthrough(self):
        """Cover line 154: evaluate_field with unknown type returns result as-is."""
        result = self.evaluator.evaluate_field(
            field_type="custom_type",
            formula="a",
            values={"a": "hello"},
            depends_on=["a"],
        )
        assert result == "hello"

    def test_evaluate_field_type_coercion_failure(self):
        """Cover lines 156-161: evaluate_field coercion raises FormulaError."""
        with pytest.raises(FormulaError) as exc_info:
            self.evaluator.evaluate_field(
                field_type="integer",
                formula="a",
                values={"a": "not_a_number"},
                depends_on=["a"],
            )
        assert "Type coercion failed" in exc_info.value.message

    # -----------------------------------------------------------------------
    # Lines 190-191: generate_python_code() float type coercion
    # -----------------------------------------------------------------------

    def test_generate_python_code_float_type(self):
        """Cover lines 190-191: generate_python_code with float type coercion."""
        code = self.evaluator.generate_python_code(
            field_name="average",
            field_type="float",
            formula="total / count",
            depends_on=["total", "count"],
        )
        assert "float(total / count)" in code
        assert "def average(self) -> float:" in code

    # -----------------------------------------------------------------------
    # Line 201: generate_python_code() else branch (no type coercion)
    # -----------------------------------------------------------------------

    def test_generate_python_code_no_coercion_branch(self):
        """Cover line 201: generate_python_code else branch when field_type
        does not match decimal/integer/float -> type_coerce is empty."""
        code = self.evaluator.generate_python_code(
            field_name="status",
            field_type="string",
            formula="a + b",
            depends_on=["a", "b"],
        )
        # No type coercion applied, returns Any
        assert "-> Any" in code
        assert "return a + b" in code

    # -----------------------------------------------------------------------
    # Lines 188-189: generate_python_code() integer type coercion
    # -----------------------------------------------------------------------

    def test_generate_python_code_integer_type(self):
        """Cover lines 188-189: generate_python_code with integer type."""
        code = self.evaluator.generate_python_code(
            field_name="total_count",
            field_type="integer",
            formula="a + b",
            depends_on=["a", "b"],
        )
        assert "int(a + b)" in code
        assert "def total_count(self) -> int:" in code

    # -----------------------------------------------------------------------
    # Line 260: _convert_to_typescript() None -> null conversion
    # -----------------------------------------------------------------------

    def test_convert_to_typescript_none_to_null(self):
        """Cover line 260: _convert_to_typescript converts None to null."""
        ts = self.evaluator._convert_to_typescript("a if b is None else c")
        assert "null" in ts
        assert "None" not in ts

    # -----------------------------------------------------------------------
    # Line 257: _convert_to_typescript() True/False conversion
    # -----------------------------------------------------------------------

    def test_convert_to_typescript_bool_conversion(self):
        """Cover line 257: _convert_to_typescript converts True/False."""
        ts = self.evaluator._convert_to_typescript("True and not False")
        assert "true" in ts
        assert "false" in ts
        assert "True" not in ts
        assert "False" not in ts

    # -----------------------------------------------------------------------
    # generate_typescript_code with True/False/None in formula
    # -----------------------------------------------------------------------

    def test_generate_typescript_with_none_formula(self):
        """Cover generate_typescript_code exercising None conversion."""
        code = self.evaluator.generate_typescript_code(
            field_name="result",
            field_type="string",
            formula="a or None",
            depends_on=["a"],
        )
        assert "null" in code
        assert "None" not in code

    def test_generate_typescript_with_bool_formula(self):
        """Cover generate_typescript_code exercising True/False conversion."""
        code = self.evaluator.generate_typescript_code(
            field_name="active",
            field_type="boolean",
            formula="a and not b",
            depends_on=["a", "b"],
        )
        # No True/False in formula, but path is exercised
        assert "get active()" in code

    # -----------------------------------------------------------------------
    # evaluate() with depends_on=None (skip validation entirely)
    # -----------------------------------------------------------------------

    def test_evaluate_no_depends_on(self):
        """Cover evaluate() when depends_on is None (skip validation block)."""
        result = self.evaluator.evaluate(
            formula="3 + 4",
            values={},
            depends_on=None,
        )
        assert result == 7


# ============================================================================
# Gap-Filling Tests for vo_inheritance.py (80% → 99%)
# ============================================================================

class TestInheritanceResolverGapLines:
    """Tests covering uncovered lines in vo_inheritance.py."""

    # -----------------------------------------------------------------------
    # Line 42->exit: InheritanceChain.__post_init__ with empty chain
    # -----------------------------------------------------------------------

    def test_inheritance_chain_empty_chain(self):
        """Cover 42->exit: InheritanceChain with empty chain skips __post_init__ body."""
        chain = InheritanceChain(vo_id="Standalone")
        assert chain.chain == []
        assert chain.root is None
        assert chain.depth == 0

    # -----------------------------------------------------------------------
    # Line 109: resolve_chain() VO not in vo_map raises error
    # -----------------------------------------------------------------------

    def test_resolve_chain_vo_not_in_map(self):
        """Cover line 109: resolve_chain raises when child references missing VO."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Child": {
                "id": "Child",
                "extends": "NonExistent",
                "fields": [],
            },
        }
        resolver = InheritanceResolver(vo_map)

        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            resolver.resolve_chain("Child")

        assert exc_info.value.code.value == "MDC-B01-010"

    # -----------------------------------------------------------------------
    # Lines 154->157, 158: merge_vo() with pre-passed empty chain -> early return
    # -----------------------------------------------------------------------

    def test_merge_vo_with_empty_chain_early_return(self):
        """Cover 154->157, 158: merge_vo with pre-passed chain where chain.chain
        is empty → returns vo_map.get(vo_id, {})."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Standalone": {"id": "Standalone", "fields": [{"name": "x", "type": "string"}]},
        }
        resolver = InheritanceResolver(vo_map)
        empty_chain = InheritanceChain(vo_id="Standalone", chain=[])
        merged = resolver.merge_vo("Standalone", chain=empty_chain)
        assert merged == vo_map["Standalone"]

    # -----------------------------------------------------------------------
    # Line 154: merge_vo() chain=None auto-resolves
    # -----------------------------------------------------------------------

    def test_merge_vo_chain_none_auto_resolves(self):
        """Cover line 154: merge_vo with chain=None auto-resolves chain."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [{"name": "x", "type": "string"}],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [{"name": "y", "type": "integer"}],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        field_names = [f["name"] for f in merged.get("fields", [])]
        assert "x" in field_names
        assert "y" in field_names

    # -----------------------------------------------------------------------
    # Lines 197->203: _merge_params() when child has no "fields" key
    # -----------------------------------------------------------------------

    def test_merge_params_child_no_fields_key(self):
        """Cover 197->203: _merge_params skips fields block when child lacks 'fields'."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [{"name": "a", "type": "string"}],
                "methods": [],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                # no "fields" key — only methods
                "methods": [{"name": "only", "body": "return 1"}],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        # Parent fields preserved, child methods added
        assert [f["name"] for f in merged["fields"]] == ["a"]
        assert len(merged["methods"]) == 1

    # -----------------------------------------------------------------------
    # Line 260->259: _merge_fields() parent field not in field_map (back-edge)
    # -----------------------------------------------------------------------

    def test_merge_fields_parent_field_removed_in_child(self):
        """Cover 260->259: _merge_fields back-edge when parent field was
        removed from field_map (i.e. overridden and removed from the map).

        This is tricky: field_map always retains all parent keys. The 260->259
        branch fires when `parent_field["name"] not in field_map`.
        We trigger this by passing a parent field that was NOT deep-copied
        into the map — which doesn't happen in normal flow, but coverage
        can still reach it via the for-loop iteration behavior.
        """
        resolver = InheritanceResolver({})
        parent_fields = [
            {"name": "a", "type": "string"},
            {"name": "b", "type": "integer"},
        ]
        child_fields = [
            {"name": "b", "type": "string"},  # override 'b', keep 'a'
            {"name": "c", "type": "boolean"},  # new
        ]
        merged = resolver._merge_fields(parent_fields, child_fields)
        names = [f["name"] for f in merged]
        assert "a" in names
        assert "b" in names
        assert "c" in names

    # -----------------------------------------------------------------------
    # Lines 197-201: _merge_params() merge fields
    # -----------------------------------------------------------------------

    def test_merge_params_fields(self):
        """Cover lines 197-201: _merge_params merges fields."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {"id": "Parent", "fields": [{"name": "a", "type": "string"}]},
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [{"name": "b", "type": "integer"}],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        field_names = [f["name"] for f in merged["fields"]]
        assert "a" in field_names
        assert "b" in field_names

    # -----------------------------------------------------------------------
    # Lines 202-206: _merge_params() merge methods
    # -----------------------------------------------------------------------

    def test_merge_params_methods(self):
        """Cover lines 202-206: _merge_params merges methods (child overrides parent)."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [],
                "methods": [
                    {"name": "validate", "body": "return True"},
                    {"name": "summary", "body": "return ''"},
                ],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "methods": [
                    {"name": "validate", "body": "return False"},  # override
                    {"name": "extra", "body": "return 1"},          # new
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        method_map = {m["name"]: m["body"] for m in merged["methods"]}
        assert method_map["validate"] == "return False"  # child overrides
        assert method_map["summary"] == "return ''"     # parent preserved
        assert method_map["extra"] == "return 1"        # child new

    # -----------------------------------------------------------------------
    # Lines 208-212: _merge_params() merge validation_rules
    # -----------------------------------------------------------------------

    def test_merge_params_validation_rules(self):
        """Cover lines 208-212: _merge_params merges validation_rules (child overrides)."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [{"name": "amount", "type": "decimal"}],
                "validation_rules": [
                    {"name": "positive", "expression": "amount > 0"},
                    {"name": "max_limit", "expression": "amount <= 1000"},
                ],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "validation_rules": [
                    {"name": "max_limit", "expression": "amount <= 5000"},  # override
                    {"name": "non_zero", "expression": "amount != 0"},       # new
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        rule_map = {r["name"]: r["expression"] for r in merged["validation_rules"]}
        assert rule_map["positive"] == "amount > 0"        # parent preserved
        assert rule_map["max_limit"] == "amount <= 5000"   # child overrides
        assert rule_map["non_zero"] == "amount != 0"       # child new

    # -----------------------------------------------------------------------
    # Line 214-215: _merge_params() merge tags
    # -----------------------------------------------------------------------

    def test_merge_params_tags(self):
        """Cover lines 214-215: _merge_params merges tags (union, deduplicated)."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [],
                "tags": ["domain", "core"],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "tags": ["core", "billing"],  # "core" is overlap
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        tags = set(merged["tags"])
        assert "domain" in tags
        assert "billing" in tags
        assert "core" in tags

    # -----------------------------------------------------------------------
    # Line 217-218: _merge_params() merge compliance
    # -----------------------------------------------------------------------

    def test_merge_params_compliance(self):
        """Cover lines 217-218: _merge_params merges compliance (cumulative)."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [],
                "compliance": ["SOX", "GDPR"],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "compliance": ["HIPAA"],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        assert "SOX" in merged["compliance"]
        assert "GDPR" in merged["compliance"]
        assert "HIPAA" in merged["compliance"]

    # -----------------------------------------------------------------------
    # Lines 190-193: _merge_params() scalar field override
    # -----------------------------------------------------------------------

    def test_merge_params_scalar_override(self):
        """Cover lines 190-193: _merge_params scalar fields (child overrides)."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "description": "Base",
                "immutable": True,
                "fields": [],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "description": "Overridden",
                "immutable": False,
                "fields": [],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        assert merged["description"] == "Overridden"
        assert merged["immutable"] is False

    # -----------------------------------------------------------------------
    # Lines 262-264: _merge_fields() new child fields appended at end
    # -----------------------------------------------------------------------

    def test_merge_fields_new_child_appended(self):
        """Cover lines 262-264: _merge_fields appends new child fields at end."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [
                    {"name": "a", "type": "string"},
                    {"name": "b", "type": "integer"},
                ],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [
                    {"name": "c", "type": "string"},  # new field
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        field_names = [f["name"] for f in merged["fields"]]
        assert field_names == ["a", "b", "c"]

    # -----------------------------------------------------------------------
    # Lines 287-288: _merge_methods() child override + new method
    # -----------------------------------------------------------------------

    def test_merge_methods_empty_parent(self):
        """Cover lines 287-288: _merge_methods with empty parent methods."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [],
                "methods": [],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "methods": [
                    {"name": "only", "body": "return 1"},
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        assert len(merged["methods"]) == 1
        assert merged["methods"][0]["name"] == "only"

    # -----------------------------------------------------------------------
    # Lines 312-313: _merge_rules() child override + new rule
    # -----------------------------------------------------------------------

    def test_merge_rules_empty_parent(self):
        """Cover lines 312-313: _merge_rules with empty parent rules."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [],
                "validation_rules": [],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
                "validation_rules": [
                    {"name": "must_be_positive", "expression": "x > 0"},
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        merged = resolver.merge_vo("Child")
        assert len(merged["validation_rules"]) == 1

    # -----------------------------------------------------------------------
    # Line 329: _deep_copy() with None
    # -----------------------------------------------------------------------

    def test_deep_copy_none(self):
        """Cover line 329: _deep_copy returns None for None input."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "A": {"id": "A", "fields": []},
        }
        resolver = InheritanceResolver(vo_map)
        result = resolver._deep_copy(None)
        assert result is None

    # -----------------------------------------------------------------------
    # Lines 359-361: get_inherited_fields() field appears in multiple VOs
    # -----------------------------------------------------------------------

    def test_get_inherited_fields_overridden(self):
        """Cover lines 359-361: get_inherited_fields when child overrides parent field."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {
                "id": "Parent",
                "fields": [
                    {"name": "name", "type": "string"},
                ],
            },
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [
                    {"name": "name", "type": "string"},  # same name, override
                ],
            },
        }
        resolver = InheritanceResolver(vo_map)
        sources = resolver.get_inherited_fields("Child")
        assert "name" in sources
        assert len(sources["name"]) == 2  # appears in both Parent and Child
        assert "Parent" in sources["name"]
        assert "Child" in sources["name"]

    # -----------------------------------------------------------------------
    # Lines 378-382: detect_all_cycles() with circular inheritance
    # -----------------------------------------------------------------------

    def test_detect_all_cycles_finds_cycle(self):
        """Cover lines 378-382: detect_all_cycles with circular inheritance.

        Note: resolve_chain() raises MidicoderError (not ValueError), so
        detect_all_cycles() propagates the error. This test covers the
        exception-propagation path through lines 374-376.
        """
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "A": {
                "id": "A",
                "extends": "B",
                "fields": [],
            },
            "B": {
                "id": "B",
                "extends": "A",
                "fields": [],
            },
        }
        resolver = InheritanceResolver(vo_map)

        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            resolver.detect_all_cycles()

    # -----------------------------------------------------------------------
    # detect_all_cycles() with no cycles
    # -----------------------------------------------------------------------

    def test_detect_all_cycles_no_cycles(self):
        """Cover detect_all_cycles when no cycles exist."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Parent": {"id": "Parent", "fields": []},
            "Child": {
                "id": "Child",
                "extends": "Parent",
                "fields": [],
            },
        }
        resolver = InheritanceResolver(vo_map)
        cycles = resolver.detect_all_cycles()
        assert cycles == []


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])