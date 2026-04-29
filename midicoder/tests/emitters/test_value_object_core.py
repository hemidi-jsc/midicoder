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

from midicoder.emitters.value_object import (
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

        assert exc_info.value.code.value == "MDC-CP01-011"

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
# Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])