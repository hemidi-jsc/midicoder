"""
FastAPI Value Object Emitter Tests

Tests cho FastAPI-specific Value Object emitter:
- Basic VO emission
- Complex fields (object, array, map, ref)
- Inheritance
- Computed fields
- Methods
- Integration with backend_fastapi.py

Author: Midicoder Team
Version: 2.0.0
"""

import pytest
from pathlib import Path
from decimal import Decimal
from typing import Any

from midicoder.packs.cp01_domain_model import (
    FastAPIValueObjectEmitter,
    EmittedValueObject,
)

from midicoder.dsl.projection import (
    FieldDefinition,
    ExtendedValueObjectParams,
)


# ============================================================================
# Test FastAPIValueObjectEmitter - Initialization
# ============================================================================

class TestFastAPIValueObjectEmitterInit:
    """Tests cho FastAPIValueObjectEmitter initialization."""

    def test_create_emitter(self, tmp_path):
        """Test tạo FastAPIValueObjectEmitter."""
        stack_dir = tmp_path / "stacks" / "fastapi" / "templates"
        stack_dir.mkdir(parents=True)

        emitter = FastAPIValueObjectEmitter(stack_dir=stack_dir)

        assert emitter.stack_dir == stack_dir
        assert emitter.target_language == "python"
        assert emitter.type_resolver is not None
        assert emitter.computed_evaluator is not None

    def test_create_emitter_with_invalid_dir(self):
        """Test tạo emitter với invalid directory."""
        # Emitter doesn't validate dir on init, only when template is accessed
        emitter = FastAPIValueObjectEmitter(stack_dir=Path("/nonexistent/path"))
        # Template access would fail
        assert emitter.stack_dir == Path("/nonexistent/path")


# ============================================================================
# Test FastAPIValueObjectEmitter - Basic Emission
# ============================================================================

class TestFastAPIEmitterBasic:
    """Tests cho basic VO emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)

        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

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
        assert "Money(**self.to_dict())" in emitted_vo.full_content

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

        assert "apartment: str = None" in emitted_vo.full_content
        assert "city: str" in emitted_vo.full_content

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

        # Check __post_init__ validation
        assert "__post_init__" in emitted_vo.full_content
        assert "email" in emitted_vo.full_content


# ============================================================================
# Test FastAPIValueObjectEmitter - Complex Fields
# ============================================================================

class TestFastAPIEmitterComplexFields:
    """Tests cho complex field emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

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
        # Check nested class fields are in the _nested_classes
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
                        {"name": "product_id", "type": "string"},
                        {"name": "quantity", "type": "integer"},
                    ],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check nested class type is referenced
        assert "ItemsItem" in emitted_vo.full_content
        # Check array type annotation
        assert "list[ItemsItem]" in emitted_vo.full_content

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

        # Python 3.9+ uses lowercase dict
        assert "dict[str, str]" in emitted_vo.full_content

    def test_emit_vo_with_ref_to_entity(self):
        """Test emit VO với ref to entity."""
        vo_params: ExtendedValueObjectParams = {
            "id": "CartItem",
            "fields": [
                {
                    "name": "product_id",
                    "type": "ref",
                    "ref_type": "entity",
                    "ref_to": "Product",
                },
                {"name": "quantity", "type": "integer"},
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Entity refs should use string ID
        assert "product_id: str" in emitted_vo.full_content

    def test_emit_vo_with_ref_to_vo(self):
        """Test emit VO với ref to value object."""
        vo_params: ExtendedValueObjectParams = {
            "id": "OrderItem",
            "fields": [
                {
                    "name": "unit_price",
                    "type": "ref",
                    "ref_type": "value_object",
                    "ref_to": "Money",
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "unit_price: Money" in emitted_vo.full_content


# ============================================================================
# Test FastAPIValueObjectEmitter - Computed Fields
# ============================================================================

class TestFastAPIEmitterComputedFields:
    """Tests cho computed field emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_computed_field(self):
        """Test emit VO với computed field."""
        vo_params: ExtendedValueObjectParams = {
            "id": "OrderTotal",
            "fields": [
                {"name": "subtotal", "type": "decimal", "required": True},
                {"name": "tax_rate", "type": "decimal", "required": True},
                {
                    "name": "total",
                    "type": "decimal",
                    "computed": True,
                    "formula": "subtotal * (1 + tax_rate)",
                    "depends_on": ["subtotal", "tax_rate"],
                },
            ],
        }

        emitted_vo = self.emitter.emit(vo_params)

        # Check computed property
        assert "@property" in emitted_vo.full_content
        assert "def total(self)" in emitted_vo.full_content

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

        assert "def sum(self)" in emitted_vo.full_content


# ============================================================================
# Test FastAPIValueObjectEmitter - Inheritance
# ============================================================================

class TestFastAPIEmitterInheritance:
    """Tests cho inheritance emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

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
                    {"name": "company_name", "type": "string"},
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
        assert "company_name" in child_vo.full_content
        assert child_vo.inherits_from == "Address"

    def test_emit_vo_multi_level_inheritance(self):
        """Test emit VO với multi-level inheritance."""
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

        # Note: Current implementation only merges immediate parent
        # Full multi-level needs emit_all which uses InheritanceResolver
        emitted = self.emitter.emit(vo_map["ShippingAddress"], parent_vo_map=vo_map)

        # Should have parent (Address) fields + child fields
        assert "street" in emitted.full_content
        assert "floor" in emitted.full_content
        # country is in BaseAddress (grandparent) - not merged in single emit
        # This is expected behavior - use emit_all for full inheritance chain


# ============================================================================
# Test FastAPIValueObjectEmitter - Methods
# ============================================================================

class TestFastAPIEmitterMethods:
    """Tests cho method emission."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

    def test_emit_vo_with_methods(self):
        """Test emit VO với methods."""
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

        assert "def add" in emitted_vo.full_content
        assert "Currency check" in emitted_vo.full_content


# ============================================================================
# Test FastAPIValueObjectEmitter - Integration
# ============================================================================

class TestFastAPIEmitterIntegration:
    """Integration tests cho FastAPIValueObjectEmitter."""

    def test_emit_all_vos(self, tmp_path):
        """Test emit_all method."""
        vo_dir = tmp_path / "value_objects"
        vo_dir.mkdir()

        emitter = FastAPIValueObjectEmitter(stack_dir=tmp_path)

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
        assert (vo_dir / "money.py").exists()
        assert (vo_dir / "address.py").exists()

    def test_emit_all_with_inheritance(self, tmp_path):
        """Test emit_all với inheritance."""
        vo_dir = tmp_path / "value_objects"
        vo_dir.mkdir()

        emitter = FastAPIValueObjectEmitter(stack_dir=tmp_path)

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
                    {"name": "tax_id", "type": "string"},
                ],
            },
        }

        files = emitter.emit_all(vo_map, output_dir=vo_dir)

        assert len(files) == 2

        # Check billing address has inherited fields
        billing_content = (vo_dir / "billingaddress.py").read_text()
        assert "street" in billing_content
        assert "tax_id" in billing_content

    def test_emit_all_with_circular_inheritance(self, tmp_path):
        """Test emit_all detect circular inheritance."""
        vo_dir = tmp_path / "value_objects"
        vo_dir.mkdir()

        emitter = FastAPIValueObjectEmitter(stack_dir=tmp_path)

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
# Test FastAPIValueObjectEmitter - Type Generation
# ============================================================================

class TestFastAPIEmitterTypes:
    """Tests cho type generation."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tmp_path = Path(__file__).parent.parent.parent / "tmp_test"
        self.tmp_path.mkdir(exist_ok=True)
        self.emitter = FastAPIValueObjectEmitter(stack_dir=self.tmp_path)

    def test_decimal_type(self):
        """Test decimal type generation."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Price",
            "fields": [{"name": "value", "type": "decimal"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "from decimal import Decimal" in emitted_vo.full_content
        assert "value: Decimal" in emitted_vo.full_content

    def test_datetime_type(self):
        """Test datetime type generation."""
        vo_params: ExtendedValueObjectParams = {
            "id": "Timestamp",
            "fields": [{"name": "created", "type": "datetime"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "from datetime import datetime" in emitted_vo.full_content
        assert "created: datetime" in emitted_vo.full_content

    def test_uuid_type(self):
        """Test UUID type generation."""
        vo_params: ExtendedValueObjectParams = {
            "id": "UuidId",
            "fields": [{"name": "id", "type": "uuid"}],
        }

        emitted_vo = self.emitter.emit(vo_params)

        assert "from uuid import UUID" in emitted_vo.full_content
        assert "id: UUID" in emitted_vo.full_content


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])