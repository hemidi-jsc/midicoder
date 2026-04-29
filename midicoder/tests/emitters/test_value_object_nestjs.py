"""
NestJS Value Object Emitter Tests

Tests cho NestJS-specific Value Object emitter:
- Basic VO emission (TypeScript)
- Complex fields (object, array, map, ref)
- Inheritance
- Computed fields
- Methods
- Class-validator decorators

Author: Midicoder Team
Version: 2.0.0
"""

import pytest
from pathlib import Path
from decimal import Decimal

from midicoder.emitters.value_object import (
    NestJSValueObjectEmitter,
    EmittedValueObject,
)

from midicoder.dsl.projection import (
    FieldDefinition,
    ExtendedValueObjectParams,
)


# ============================================================================
# Test NestJSValueObjectEmitter - Initialization
# ============================================================================

class TestNestJSValueObjectEmitterInit:
    """Tests cho NestJSValueObjectEmitter initialization."""

    def test_create_emitter(self, tmp_path):
        """Test tạo NestJSValueObjectEmitter."""
        stack_dir = tmp_path / "stacks" / "nestjs" / "templates"
        stack_dir.mkdir(parents=True)

        emitter = NestJSValueObjectEmitter(stack_dir=stack_dir)

        assert emitter.stack_dir == stack_dir
        assert emitter.target_language == "typescript"
        assert emitter.type_resolver is not None
        assert emitter.computed_evaluator is not None

    def test_create_emitter_with_invalid_dir(self):
        """Test tạo emitter với invalid directory."""
        emitter = NestJSValueObjectEmitter(stack_dir=Path("/nonexistent/path"))
        assert emitter.stack_dir == Path("/nonexistent/path")


# ============================================================================
# Test NestJSValueObjectEmitter - Basic Emission
# ============================================================================

class TestNestJSEmitterBasic:
    """Tests cho basic VO emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)

        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_simple_vo(self):
        """Test emit simple Value Object."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Money",
            "description": "Giá tiền tệ",
            "fields": [
                {"name": "amount", "type": "decimal", "required": True},
                {"name": "currency", "type": "string", "required": True},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert emitted_vo.id == "Money"
        assert emitted_vo.name == "Money"
        assert len(emitted_vo.fields) == 2
        assert "export class Money" in emitted_vo.full_content

    def test_emit_vo_with_optional_fields(self):
        """Test emit VO với optional fields."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Address",
            "fields": [
                {"name": "street", "type": "string", "required": True},
                {"name": "city", "type": "string", "required": True},
                {"name": "apartment", "type": "string", "required": False},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@IsOptional()" in emitted_vo.full_content
        assert "street: string" in emitted_vo.full_content

    def test_emit_vo_with_validation(self):
        """Test emit VO với validation rules."""
        vo_params: ExtendedValueObjectParams = {
            "id": "EmailAddress",
            "fields": [
                {
                    "name": "email",
                    "type": "string",
                    "required": True,
                    "min_length": 5,
                    "max_length": 255,
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check class-validator decorators
        assert "@IsString()" in emitted_vo.full_content
        assert "@MinLength(5)" in emitted_vo.full_content
        assert "@MaxLength(255)" in emitted_vo.full_content


# ============================================================================
# Test NestJSValueObjectEmitter - Complex Fields
# ============================================================================

class TestNestJSEmitterComplexFields:
    """Tests cho complex field emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_object_field(self):
        """Test emit VO với object field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Product",
            "fields": [
                {"name": "name", "type": "string", "required": True},
                {
                    "name": "dimensions",
                    "type": "object",
                    "fields": [
                        {"name": "width", "type": "decimal"},
                        {"name": "height", "type": "decimal"},
                        {"name": "depth", "type": "decimal"},
                    ],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check nested class type is referenced
        assert "DimensionsItem" in emitted_vo.full_content
        assert emitted_vo.fields[1].nested_class == "DimensionsItem"

    def test_emit_vo_with_array_field(self):
        """Test emit VO với array field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Cart",
            "fields": [
                {
                    "name": "items",
                    "type": "array",
                    "item_fields": [
                        {"name": "productId", "type": "string"},
                        {"name": "quantity", "type": "integer"},
                    ],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check nested class type is referenced
        assert "ItemsItem" in emitted_vo.full_content
        # TypeScript array syntax uses Type[]
        assert "ItemsItem[]" in emitted_vo.full_content

    def test_emit_vo_with_map_field(self):
        """Test emit VO với map field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "ProductMetadata",
            "fields": [
                {
                    "name": "attributes",
                    "type": "map",
                    "key_type": "string",
                    "value_type": "string",
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # TypeScript Record syntax
        assert "Record<string, string>" in emitted_vo.full_content

    def test_emit_vo_with_ref_to_entity(self):
        """Test emit VO với ref to entity."""
        vo_params: ExtendedValueObjectParams = {
            "id": "CartItem",
            "fields": [
                {
                    "name": "productId",
                    "type": "ref",
                    "ref_type": "entity",
                    "ref_to": "Product",
                },
                {"name": "quantity", "type": "integer"},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Entity refs should use string ID
        assert "productId: string" in emitted_vo.full_content

    def test_emit_vo_with_ref_to_vo(self):
        """Test emit VO với ref to value object."""
        vo_params: ExtendedValueObjectParams = {
            "id": "OrderItem",
            "fields": [
                {
                    "name": "unitPrice",
                    "type": "ref",
                    "ref_type": "value_object",
                    "ref_to": "Money",
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "unitPrice: Money" in emitted_vo.full_content


# ============================================================================
# Test NestJSValueObjectEmitter - Computed Fields
# ============================================================================

class TestNestJSEmitterComputedFields:
    """Tests cho computed field emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_computed_field(self):
        """Test emit VO với computed field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "OrderTotal",
            "fields": [
                {"name": "subtotal", "type": "decimal", "required": True},
                {"name": "taxRate", "type": "decimal", "required": True},
                {
                    "name": "total",
                    "type": "decimal",
                    "computed": True,
                    "formula": "subtotal * (1 + taxRate)",
                    "depends_on": ["subtotal", "taxRate"],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check computed getter
        assert "get total()" in emitted_vo.full_content or "get total" in emitted_vo.full_content

    def test_emit_vo_with_integer_computed(self):
        """Test emit VO với integer computed field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Count",
            "fields": [
                {"name": "a", "type": "integer", "required": True},
                {"name": "b", "type": "integer", "required": True},
                {
                    "name": "sum",
                    "type": "integer",
                    "computed": True,
                    "formula": "a + b",
                    "depends_on": ["a", "b"],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "get sum" in emitted_vo.full_content


# ============================================================================
# Test NestJSValueObjectEmitter - Inheritance
# ============================================================================

class TestNestJSEmitterInheritance:
    """Tests cho inheritance emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_inheritance(self):
        """Test emit VO với inheritance."""
        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Address": {
                "id": "Address",
                "fields": [
                    {"name": "street", "type": "string", "required": True},
                    {"name": "city", "type": "string", "required": True},
                    {"name": "country", "type": "string", "required": True},
                ],
            },
            "BillingAddress": {
                "id": "BillingAddress",
                "extends": "Address",
                "fields": [
                    {"name": "companyName", "type": "string"},
                ],
            },
        }

        # Emit parent first
        parent_vo = self.emitter.emit(vo_map["Address"])
        assert "street" in parent_vo.full_content

        # Emit child with inheritance
        child_vo = self.emitter.emit(vo_map["BillingAddress"], parent_vo_map=vo_map)

        # Should have both parent and child fields
        assert "street" in child_vo.full_content
        assert "companyName" in child_vo.full_content
        assert child_vo.inherits_from == "Address"


# ============================================================================
# Test NestJSValueObjectEmitter - Methods
# ============================================================================

class TestNestJSEmitterMethods:
    """Tests cho method emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_methods(self):
        """Test emit VO với methods - methods are emitted but not rendered in fallback mode."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Money",
            "fields": [
                {"name": "amount", "type": "decimal"},
                {"name": "currency", "type": "string"},
            ],
            "methods": [
                {
                    "name": "add",
                    "description": "Thêm tiền",
                    "params": [
                        {
                            "name": "other",
                            "type": "ref",
                            "ref_to": "Money",
                            "ref_type": "value_object",
                        }
                    ],
                    "returns": "Money",
                    "logic": "Currency check + amount addition",
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Methods are parsed and stored
        assert len(emitted_vo.methods) == 1
        assert emitted_vo.methods[0].name == "add"
        # Note: Methods rendering requires template, fallback doesn't render methods


# ============================================================================
# Test NestJSValueObjectEmitter - TypeScript Types
# ============================================================================

class TestNestJSEmitterTypes:
    """Tests cho TypeScript type generation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_number_type(self):
        """Test number type generation (TypeScript)."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Price",
            "fields": [{"name": "value", "type": "decimal"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # TypeScript uses number for all numeric types
        assert "value: number" in emitted_vo.full_content

    def test_string_type(self):
        """Test string type generation."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Name",
            "fields": [{"name": "value", "type": "string"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "value: string" in emitted_vo.full_content

    def test_boolean_type(self):
        """Test boolean type generation."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Flag",
            "fields": [{"name": "value", "type": "boolean"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "value: boolean" in emitted_vo.full_content

    def test_datetime_type(self):
        """Test datetime type generation (TypeScript Date)."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Timestamp",
            "fields": [{"name": "created", "type": "datetime"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "created: Date" in emitted_vo.full_content


# ============================================================================
# Test NestJSValueObjectEmitter - Class Validator Decorators
# ============================================================================

class TestNestJSEmitterDecorators:
    """Tests cho class-validator decorator generation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = NestJSValueObjectEmitter(stack_dir=self.tmp_path)

    def test_is_string_decorator(self):
        """Test @IsString decorator."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Name",
            "fields": [{"name": "value", "type": "string"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@IsString()" in emitted_vo.full_content

    def test_is_number_decorator(self):
        """Test @IsNumber decorator."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Price",
            "fields": [{"name": "value", "type": "decimal"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@IsNumber()" in emitted_vo.full_content

    def test_is_boolean_decorator(self):
        """Test @IsBoolean decorator."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Flag",
            "fields": [{"name": "value", "type": "boolean"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@IsBoolean()" in emitted_vo.full_content

    def test_min_max_decorators(self):
        """Test @Min and @Max decorators."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Age",
            "fields": [
                {"name": "value", "type": "integer", "min": 1, "max": 150},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@Min(1)" in emitted_vo.full_content
        assert "@Max(150)" in emitted_vo.full_content

    def test_min_length_max_length_decorators(self):
        """Test @MinLength and @MaxLength decorators."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Username",
            "fields": [
                {"name": "value", "type": "string", "min_length": 3, "max_length": 50},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "@MinLength(3)" in emitted_vo.full_content
        assert "@MaxLength(50)" in emitted_vo.full_content


# ============================================================================
# Test NestJSValueObjectEmitter - Integration
# ============================================================================

class TestNestJSEmitterIntegration:
    """Integration tests cho NestJSValueObjectEmitter."""

    def test_emit_all_vos(self, tmp_path):
        """Test emit_all method."""
        vo_dir = tmp_path / "value_objects"
        vo_dir.mkdir()

        emitter = NestJSValueObjectEmitter(stack_dir=tmp_path)

        vo_map: dict[str, ExtendedValueObjectParams] = {
            "Money": {
                "id": "Money",
                "fields": [
                    {"name": "amount", "type": "decimal"},
                    {"name": "currency", "type": "string"},
                ],
            },
            "Address": {
                "id": "Address",
                "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                ],
            },
        }

        files = emitter.emit_all(vo_map, output_dir=vo_dir)

        assert len(files) == 2
        assert (vo_dir / "money.ts").exists()
        assert (vo_dir / "address.ts").exists()

    def test_emit_all_with_circular_inheritance(self, tmp_path):
        """Test emit_all detect circular inheritance."""
        vo_dir = tmp_path / "value_objects"
        vo_dir.mkdir()

        emitter = NestJSValueObjectEmitter(stack_dir=tmp_path)

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

        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            emitter.emit_all(vo_map, output_dir=vo_dir)

        assert exc_info.value.code.value == "MDC-CP01-011"


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])