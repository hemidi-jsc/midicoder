"""
Unit Tests cho CP01 Entity Model Utilities.

Test coverage:
- Field type mapping (get_sqlalchemy_type, get_python_type)
- Relationship helpers (validate_relationship, get_relationship_options)
- Lifecycle event validation
- Constraint helpers
- Utility functions

Sử dụng:
    pytest midicoder/tests/emitters/test_cp01_utils.py -v

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON, LargeBinary

from midicoder.errors import ErrorCode, MidicoderError
from midicoder.emitters.cp01_utils import (
    # Field types
    SUPPORTED_FIELD_TYPES,
    get_sqlalchemy_type,
    get_python_type,
    get_field_imports,
    # Relationships
    SUPPORTED_RELATIONSHIP_TYPES,
    validate_relationship,
    get_relationship_options,
    get_relationship_type_hint,
    # Lifecycle events
    VALID_LIFECYCLE_EVENTS,
    validate_lifecycle_event,
    get_event_decorator_code,
    # Constraints
    get_column_constraints,
    get_check_constraint,
    get_index_code,
    # Utilities
    to_snake_case,
    to_table_name,
    get_model_imports,
)


# ============================================================================
# Test: Field Type Constants
# ============================================================================

class TestFieldTypes:
    """Test field type constants và mappings."""
    
    def test_supported_field_types_count(self):
        """Kiểm tra số lượng field types được hỗ trợ."""
        # Phải có đủ 12 field types theo requirement
        assert len(SUPPORTED_FIELD_TYPES) == 12
        
    def test_all_required_field_types_present(self):
        """Kiểm tra tất cả field types bắt buộc đều có."""
        required_types = {
            "string", "integer", "float", "boolean",
            "datetime", "text", "uuid", "json",
            "enum", "decimal", "largebinary", "array"
        }
        assert required_types.issubset(SUPPORTED_FIELD_TYPES)


# ============================================================================
# Test: get_sqlalchemy_type
# ============================================================================

class TestGetSQLAlchemyType:
    """Test hàm get_sqlalchemy_type."""
    
    def test_string_type_default(self):
        """Test string type với default length."""
        result = get_sqlalchemy_type("string")
        assert isinstance(result, String)
        assert result.length == 255
        
    def test_string_type_custom_length(self):
        """Test string type với custom length."""
        result = get_sqlalchemy_type("string", {"length": 100})
        assert isinstance(result, String)
        assert result.length == 100
        
    def test_integer_type(self):
        """Test integer type."""
        result = get_sqlalchemy_type("integer")
        assert isinstance(result, Integer)
        
    def test_float_type(self):
        """Test float type."""
        result = get_sqlalchemy_type("float")
        assert isinstance(result, Float)
        
    def test_boolean_type(self):
        """Test boolean type."""
        result = get_sqlalchemy_type("boolean")
        assert isinstance(result, Boolean)
        
    def test_datetime_type(self):
        """Test datetime type."""
        result = get_sqlalchemy_type("datetime")
        assert isinstance(result, DateTime)
        
    def test_text_type(self):
        """Test text type."""
        result = get_sqlalchemy_type("text")
        assert isinstance(result, Text)
        
    def test_json_type(self):
        """Test json type."""
        result = get_sqlalchemy_type("json")
        assert isinstance(result, JSON)
        
    def test_decimal_type_default(self):
        """Test decimal type với default precision/scale."""
        result = get_sqlalchemy_type("decimal")
        # SQLAlchemy Decimal type
        assert result.precision == 10
        assert result.scale == 2
        
    def test_decimal_type_custom(self):
        """Test decimal type với custom precision/scale."""
        result = get_sqlalchemy_type("decimal", {"precision": 12, "scale": 4})
        assert result.precision == 12
        assert result.scale == 4
        
    def test_uuid_type(self):
        """Test uuid type."""
        result = get_sqlalchemy_type("uuid")
        # UUID type with as_uuid=True
        assert result.as_uuid is True
        
    def test_largebinary_type(self):
        """Test largebinary type."""
        result = get_sqlalchemy_type("largebinary")
        assert isinstance(result, LargeBinary)
        
    def test_invalid_field_type_raises_error(self):
        """Test invalid field type raises MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            get_sqlalchemy_type("invalid_type")
            
        assert exc_info.value.code == ErrorCode.CP01_INVALID_FIELD_TYPE
        assert "invalid_type" in str(exc_info.value.context)
        
    def test_enum_type_without_enum_class_raises_error(self):
        """Test enum type without enum_class raises error."""
        with pytest.raises(MidicoderError) as exc_info:
            get_sqlalchemy_type("enum", {})
            
        assert exc_info.value.code == ErrorCode.CP01_INVALID_FIELD_TYPE


# ============================================================================
# Test: get_python_type
# ============================================================================

class TestGetPythonType:
    """Test hàm get_python_type."""
    
    def test_string_python_type(self):
        """Test string → str."""
        result = get_python_type("string")
        assert result == str
        
    def test_integer_python_type(self):
        """Test integer → int."""
        result = get_python_type("integer")
        assert result == int
        
    def test_float_python_type(self):
        """Test float → float."""
        result = get_python_type("float")
        assert result == float
        
    def test_boolean_python_type(self):
        """Test boolean → bool."""
        result = get_python_type("boolean")
        assert result == bool
        
    def test_uuid_python_type(self):
        """Test uuid → UUID."""
        result = get_python_type("uuid")
        assert result == UUID
        
    def test_decimal_python_type(self):
        """Test decimal → Decimal."""
        result = get_python_type("decimal")
        assert result == Decimal
        
    def test_largebinary_python_type(self):
        """Test largebinary → bytes."""
        result = get_python_type("largebinary")
        assert result == bytes
        
    def test_invalid_type_returns_any(self):
        """Test invalid type returns 'Any'."""
        result = get_python_type("nonexistent")
        assert result == "Any"


# ============================================================================
# Test: get_field_imports
# ============================================================================

class TestGetFieldImports:
    """Test hàm get_field_imports."""
    
    def test_empty_fields(self):
        """Test empty fields returns empty set."""
        result = get_field_imports([])
        assert len(result) == 0
        
    def test_uuid_field_import(self):
        """Test uuid field adds UUID import."""
        result = get_field_imports([{"type": "uuid"}])
        assert "from uuid import UUID" in result
        
    def test_datetime_field_import(self):
        """Test datetime field adds datetime import."""
        result = get_field_imports([{"type": "datetime"}])
        assert "from datetime import datetime" in result
        
    def test_decimal_field_import(self):
        """Test decimal field adds Decimal import."""
        result = get_field_imports([{"type": "decimal"}])
        assert "from decimal import Decimal" in result
        
    def test_multiple_field_imports(self):
        """Test multiple fields with different types."""
        fields = [
            {"type": "uuid"},
            {"type": "datetime"},
            {"type": "decimal"}
        ]
        result = get_field_imports(fields)
        assert "from uuid import UUID" in result
        assert "from datetime import datetime" in result
        assert "from decimal import Decimal" in result


# ============================================================================
# Test: Relationship Helpers
# ============================================================================

class TestRelationshipHelpers:
    """Test relationship validation và helpers."""
    
    def test_supported_relationship_types(self):
        """Kiểm tra các relationship types được hỗ trợ."""
        assert "one-to-one" in SUPPORTED_RELATIONSHIP_TYPES
        assert "one-to-many" in SUPPORTED_RELATIONSHIP_TYPES
        assert "many-to-many" in SUPPORTED_RELATIONSHIP_TYPES
        
    def test_validate_valid_relationship(self):
        """Test valid relationship passes validation."""
        rel_config = {
            "type": "one-to-many",
            "target": "OrderItem",
            "back_populates": "order"
        }
        # Should not raise
        validate_relationship(rel_config)
        
    def test_validate_invalid_relationship_type(self):
        """Test invalid relationship type raises error."""
        rel_config = {
            "type": "invalid-type",
            "target": "OrderItem",
            "back_populates": "order"
        }
        with pytest.raises(MidicoderError) as exc_info:
            validate_relationship(rel_config)
        assert exc_info.value.code == ErrorCode.CP01_RELATIONSHIP_TARGET_NOT_FOUND
        
    def test_validate_missing_required_field(self):
        """Test missing required field raises error."""
        rel_config = {
            "type": "one-to-many",
            # missing "target"
            "back_populates": "order"
        }
        with pytest.raises(MidicoderError) as exc_info:
            validate_relationship(rel_config)
            
    def test_validate_many_to_many_without_secondary(self):
        """Test many-to-many without secondary raises error."""
        rel_config = {
            "type": "many-to-many",
            "target": "Category",
            "back_populates": "products"
            # missing "secondary"
        }
        with pytest.raises(MidicoderError) as exc_info:
            validate_relationship(rel_config)
            
    def test_get_relationship_options_one_to_one(self):
        """Test get_relationship_options for one-to-one."""
        rel_config = {
            "type": "one-to-one",
            "target": "Profile"
        }
        options = get_relationship_options(rel_config)
        assert options["uselist"] is False
        
    def test_get_relationship_options_one_to_many(self):
        """Test get_relationship_options for one-to-many."""
        rel_config = {
            "type": "one-to-many",
            "target": "OrderItem"
        }
        options = get_relationship_options(rel_config)
        assert options["uselist"] is True
        
    def test_get_relationship_options_many_to_many(self):
        """Test get_relationship_options for many-to-many."""
        rel_config = {
            "type": "many-to-many",
            "target": "Category",
            "secondary": "product_categories"
        }
        options = get_relationship_options(rel_config)
        assert options["uselist"] is True
        assert options["secondary"] == "product_categories"
        
    def test_get_relationship_options_with_cascade(self):
        """Test get_relationship_options with cascade."""
        rel_config = {
            "type": "one-to-many",
            "target": "OrderItem",
            "cascade": "all, delete-orphan"
        }
        options = get_relationship_options(rel_config)
        assert options["cascade"] == "all, delete-orphan"
        
    def test_get_relationship_type_hint_one_to_one(self):
        """Test get_relationship_type_hint for one-to-one."""
        rel_config = {"type": "one-to-one", "target": "Profile"}
        hint = get_relationship_type_hint(rel_config)
        assert hint == "Mapped[Profile]"
        
    def test_get_relationship_type_hint_one_to_many(self):
        """Test get_relationship_type_hint for one-to-many."""
        rel_config = {"type": "one-to-many", "target": "OrderItem"}
        hint = get_relationship_type_hint(rel_config)
        assert hint == "Mapped[list[OrderItem]]"


# ============================================================================
# Test: Lifecycle Event Helpers
# ============================================================================

class TestLifecycleEventHelpers:
    """Test lifecycle event validation và helpers."""
    
    def test_valid_lifecycle_events(self):
        """Kiểm tra các lifecycle events được hỗ trợ."""
        expected_events = {
            "before_insert", "after_insert",
            "before_update", "after_update",
            "before_delete", "after_delete"
        }
        assert VALID_LIFECYCLE_EVENTS == expected_events
        
    def test_validate_valid_event(self):
        """Test valid event passes validation."""
        # Should not raise
        validate_lifecycle_event("before_insert")
        
    def test_validate_invalid_event(self):
        """Test invalid event raises error."""
        with pytest.raises(MidicoderError) as exc_info:
            validate_lifecycle_event("invalid_event")
        assert exc_info.value.code == ErrorCode.CP01_INVALID_LIFECYCLE_EVENT
        
    def test_get_event_decorator_code(self):
        """Test get_event_decorator_code generates correct decorator."""
        result = get_event_decorator_code("before_insert", "User")
        assert result == "@event.listens_for(User, 'before_insert')"


# ============================================================================
# Test: Constraint Helpers
# ============================================================================

class TestConstraintHelpers:
    """Test constraint helpers."""
    
    def test_get_column_constraints_nullable(self):
        """Test nullable constraint."""
        constraints = get_column_constraints({"nullable": False})
        assert constraints["nullable"] is False
        
    def test_get_column_constraints_primary_key(self):
        """Test primary_key constraint."""
        constraints = get_column_constraints({"primary_key": True})
        assert constraints["primary_key"] is True
        
    def test_get_column_constraints_unique(self):
        """Test unique constraint."""
        constraints = get_column_constraints({"unique": True})
        assert constraints["unique"] is True
        
    def test_get_column_constraints_index(self):
        """Test index constraint."""
        constraints = get_column_constraints({"index": True})
        assert constraints["index"] is True
        
    def test_get_column_constraints_default(self):
        """Test default constraint."""
        constraints = get_column_constraints({"default": "pending"})
        assert constraints["default"] == "pending"
        
    def test_get_check_constraint(self):
        """Test get_check_constraint."""
        result = get_check_constraint("price", "price > 0")
        assert result == "CheckConstraint('price > 0')"
        
    def test_get_index_code_with_name(self):
        """Test get_index_code with custom name."""
        result = get_index_code(["tenant_id", "created_at"], "idx_tenant_created")
        assert "idx_tenant_created" in result
        
    def test_get_index_code_without_name(self):
        """Test get_index_code auto-generates name."""
        result = get_index_code(["tenant_id", "created_at"])
        assert "idx_tenant_id_created_at" in result


# ============================================================================
# Test: Utility Functions
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_to_snake_case_pascal_case(self):
        """Test to_snake_case với PascalCase."""
        assert to_snake_case("OrderItem") == "order_item"
        
    def test_to_snake_case_camel_case(self):
        """Test to_snake_case với camelCase."""
        assert to_snake_case("orderItem") == "order_item"
        
    def test_to_snake_case_already_snake(self):
        """Test to_snake_case với snake_case."""
        assert to_snake_case("order_item") == "order_item"
        
    def test_to_snake_case_with_numbers(self):
        """Test to_snake_case với numbers."""
        assert to_snake_case("UserID123") == "user_id123"
        
    def test_to_table_name_singular(self):
        """Test to_table_name với singular name."""
        assert to_table_name("Order") == "orders"
        
    def test_to_table_name_already_plural(self):
        """Test to_table_name với plural name."""
        assert to_table_name("Orders") == "orders"
        
    def test_to_table_name_with_camel_case(self):
        """Test to_table_name với camelCase."""
        assert to_table_name("OrderItem") == "order_items"
        
    def test_get_model_imports_basic(self):
        """Test get_model_imports với basic fields."""
        imports = get_model_imports(
            fields=[{"type": "string"}],
            relationships=[]
        )
        assert "from sqlalchemy import Column" in imports
        assert "from sqlalchemy.orm import Mapped, relationship" in imports
        
    def test_get_model_imports_with_uuid(self):
        """Test get_model_imports với UUID field."""
        imports = get_model_imports(
            fields=[{"type": "uuid"}],
            relationships=[]
        )
        assert "from uuid import UUID" in imports
        
    def test_get_model_imports_with_relationships(self):
        """Test get_model_imports với relationships."""
        imports = get_model_imports(
            fields=[],
            relationships=[{"type": "one-to-many", "target": "OrderItem"}]
        )
        assert "from typing import TYPE_CHECKING" in imports


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests cho cp01_utils."""
    
    def test_full_entity_processing(self):
        """Test full entity processing flow."""
        entity = {
            "id": "Order",
            "fields": [
                {"name": "order_id", "type": "uuid", "primary_key": True},
                {"name": "total", "type": "decimal", "precision": 10, "scale": 2},
                {"name": "status", "type": "string", "length": 20, "default": "pending"},
                {"name": "created_at", "type": "datetime"},
            ],
            "relationships": [
                {
                    "type": "one-to-many",
                    "target": "OrderItem",
                    "back_populates": "order",
                    "cascade": "all, delete-orphan"
                }
            ]
        }
        
        # Validate all fields
        for field in entity["fields"]:
            sa_type = get_sqlalchemy_type(field["type"], field)
            assert sa_type is not None
            
        # Validate relationships
        for rel in entity["relationships"]:
            validate_relationship(rel)
            options = get_relationship_options(rel)
            assert "uselist" in options
            
        # Get imports
        imports = get_model_imports(entity["fields"], entity["relationships"])
        assert len(imports) > 0
        
        # Get table name
        table_name = to_table_name(entity["id"])
        assert table_name == "orders"
        
    def test_error_handling_chain(self):
        """Test error handling flows correctly."""
        # Invalid field type
        with pytest.raises(MidicoderError) as exc_info:
            get_sqlalchemy_type("nonexistent")
        assert exc_info.value.code == ErrorCode.CP01_INVALID_FIELD_TYPE
        
        # Invalid relationship
        with pytest.raises(MidicoderError) as exc_info:
            validate_relationship({"type": "invalid"})
        assert exc_info.value.code == ErrorCode.CP01_RELATIONSHIP_TARGET_NOT_FOUND
        
        # Invalid lifecycle event
        with pytest.raises(MidicoderError) as exc_info:
            validate_lifecycle_event("on_create")
        assert exc_info.value.code == ErrorCode.CP01_INVALID_LIFECYCLE_EVENT