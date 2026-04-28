"""
Tests cho Extended Value Object DSL (REBUILD).

Test cases cho Phase 1 - DSL Extensions:
- FieldDefinition: Basic types, complex types, computed fields, references
- MethodDefinition: Method definitions với params và returns
- ValidationRule: Cross-field validation rules
- ExtendedValueObjectParams: Full VO DSL với inheritance

TDD: Tests viết trước, sau đó extend projection.py để pass.

Author: Midicoder Team
Version: 2.0.0 (REBUILD)
"""

import pytest
from typing import Any


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_basic_field() -> dict[str, Any]:
    """Sample basic field definition."""
    return {
        "name": "amount",
        "type": "decimal",
        "precision": 18,
        "scale": 2,
        "required": True,
        "min": 0,
        "description": "Số tiền"
    }


@pytest.fixture
def sample_complex_field() -> dict[str, Any]:
    """Sample complex nested field definition."""
    return {
        "name": "frequency",
        "type": "object",
        "required": True,
        "fields": [
            {
                "name": "interval",
                "type": "enum",
                "enum_values": ["minutely", "hourly", "daily", "weekly"],
                "required": True
            },
            {
                "name": "count",
                "type": "integer",
                "min": 1,
                "required": True
            }
        ]
    }


@pytest.fixture
def sample_computed_field() -> dict[str, Any]:
    """Sample computed field definition."""
    return {
        "name": "apr",
        "type": "decimal",
        "computed": True,
        "formula": "((1 + nominal_rate / n_compounds) ** n_compounds) - 1",
        "depends_on": ["nominal_rate", "compounding"]
    }


@pytest.fixture
def sample_reference_field() -> dict[str, Any]:
    """Sample reference field definition."""
    return {
        "name": "unit_price",
        "type": "ref",
        "ref_type": "value_object",
        "ref_to": "Money",
        "required": True
    }


@pytest.fixture
def sample_method() -> dict[str, Any]:
    """Sample method definition."""
    return {
        "name": "add",
        "description": "Cộng hai giá trị Money",
        "params": [
            {
                "name": "other",
                "type": "ref",
                "ref_type": "value_object",
                "ref_to": "Money"
            }
        ],
        "returns": "Money",
        "logic": "Kiểm tra currency giống nhau, sau đó cộng amount"
    }


@pytest.fixture
def sample_validation_rule() -> dict[str, Any]:
    """Sample validation rule."""
    return {
        "name": "valid_email",
        "condition": "local_part + '@' + domain matches email_regex",
        "error_code": "MDC-VO-EMAIL-001",
        "error_message": "Địa chỉ email không hợp lệ",
        "severity": "error"
    }


@pytest.fixture
def sample_extended_vo() -> dict[str, Any]:
    """Sample extended Value Object (with inheritance)."""
    return {
        "id": "BillingAddress",
        "description": "Địa chỉ thanh toán",
        "extends": "Address",
        "fields": [
            {
                "name": "company_name",
                "type": "string",
                "max_length": 255
            },
            {
                "name": "tax_id",
                "type": "string",
                "pattern": "^[A-Z0-9]{10,12}$",
                "description": "Mã số thuế"
            }
        ],
        "tags": ["address", "billing"]
    }


# ============================================================================
# Tests for FieldDefinition (RED Phase - Should Fail Initially)
# ============================================================================


class TestFieldDefinition:
    """Tests cho FieldDefinition DSL."""

    def test_import_field_definition(self):
        """Test: Import FieldDefinition từ projection module."""
        # This will fail until we extend projection.py
        from midicoder.dsl.projection import FieldDefinition
        assert FieldDefinition is not None

    def test_basic_field_structure(self, sample_basic_field: dict):
        """Test: Basic field có đúng structure."""
        # This will fail until FieldDefinition TypedDict exists
        from midicoder.dsl.projection import FieldDefinition
        
        # Type check
        field: FieldDefinition = sample_basic_field
        assert field["name"] == "amount"
        assert field["type"] == "decimal"
        assert field["required"] is True

    def test_decimal_field_with_precision_scale(self, sample_basic_field: dict):
        """Test: Decimal field có precision và scale."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_basic_field
        assert field.get("precision") == 18
        assert field.get("scale") == 2

    def test_decimal_field_with_min_max(self, sample_basic_field: dict):
        """Test: Decimal field có min validation."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_basic_field
        assert field.get("min") == 0

    def test_enum_field_with_values(self):
        """Test: Enum field với enum_values."""
        enum_field = {
            "name": "unit",
            "type": "enum",
            "enum_values": ["mg", "ml", "g", "mcg"],
            "required": True
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = enum_field
        
        assert field.get("enum_values") == ["mg", "ml", "g", "mcg"]

    def test_complex_nested_object_field(self, sample_complex_field: dict):
        """Test: Complex nested object field."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_complex_field
        assert field["type"] == "object"
        assert "fields" in field
        assert len(field["fields"]) == 2

    def test_complex_field_nested_enum(self, sample_complex_field: dict):
        """Test: Complex field với nested enum."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_complex_field
        nested_enum = field["fields"][0]
        assert nested_enum["type"] == "enum"
        assert "interval" in nested_enum["name"]

    def test_array_field_with_item_type(self):
        """Test: Array field với item_type."""
        array_field = {
            "name": "amounts",
            "type": "array",
            "item_type": "object",
            "item_fields": [
                {"name": "currency", "type": "string", "length": 3},
                {"name": "amount", "type": "decimal"}
            ]
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = array_field
        
        assert field["type"] == "array"
        assert field["item_type"] == "object"
        assert len(field["item_fields"]) == 2

    def test_map_field_with_key_value_types(self):
        """Test: Map field với key_type và value_type."""
        map_field = {
            "name": "metadata",
            "type": "map",
            "key_type": "string",
            "value_type": "string"
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = map_field
        
        assert field["type"] == "map"
        assert field["key_type"] == "string"
        assert field["value_type"] == "string"

    def test_reference_field_to_value_object(self, sample_reference_field: dict):
        """Test: Reference field to another Value Object."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_reference_field
        assert field["type"] == "ref"
        assert field["ref_type"] == "value_object"
        assert field["ref_to"] == "Money"

    def test_reference_field_to_entity(self):
        """Test: Reference field to Entity."""
        ref_field = {
            "name": "product_id",
            "type": "ref",
            "ref_type": "entity",
            "ref_to": "Product"
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = ref_field
        
        assert field["ref_type"] == "entity"
        assert field["ref_to"] == "Product"

    def test_computed_field_with_formula(self, sample_computed_field: dict):
        """Test: Computed field với formula."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_computed_field
        assert field["computed"] is True
        assert "formula" in field
        assert "depends_on" in field

    def test_computed_field_depends_on(self, sample_computed_field: dict):
        """Test: Computed field có depends_on list."""
        from midicoder.dsl.projection import FieldDefinition
        
        field: FieldDefinition = sample_computed_field
        assert field["depends_on"] == ["nominal_rate", "compounding"]

    def test_string_field_with_pattern(self):
        """Test: String field với pattern validation."""
        string_field = {
            "name": "tax_id",
            "type": "string",
            "pattern": "^[A-Z0-9]{10,12}$",
            "description": "Mã số thuế"
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = string_field
        
        assert field["pattern"] == "^[A-Z0-9]{10,12}$"

    def test_field_with_default_value(self):
        """Test: Field với default value."""
        field_with_default = {
            "name": "compounding",
            "type": "enum",
            "enum_values": ["monthly", "quarterly", "annually"],
            "default": "annually"
        }
        
        from midicoder.dsl.projection import FieldDefinition
        field: FieldDefinition = field_with_default
        
        assert field["default"] == "annually"


# ============================================================================
# Tests for MethodDefinition (RED Phase)
# ============================================================================


class TestMethodDefinition:
    """Tests cho MethodDefinition DSL."""

    def test_import_method_definition(self):
        """Test: Import MethodDefinition từ projection module."""
        from midicoder.dsl.projection import MethodDefinition
        assert MethodDefinition is not None

    def test_method_basic_structure(self, sample_method: dict):
        """Test: Method có đúng basic structure."""
        from midicoder.dsl.projection import MethodDefinition
        
        method: MethodDefinition = sample_method
        assert method["name"] == "add"
        assert "description" in method
        assert "params" in method
        assert "returns" in method

    def test_method_with_params(self, sample_method: dict):
        """Test: Method có params list."""
        from midicoder.dsl.projection import MethodDefinition
        
        method: MethodDefinition = sample_method
        assert len(method["params"]) == 1
        assert method["params"][0]["name"] == "other"

    def test_method_return_type(self, sample_method: dict):
        """Test: Method có return type."""
        from midicoder.dsl.projection import MethodDefinition
        
        method: MethodDefinition = sample_method
        assert method["returns"] == "Money"

    def test_method_with_logic_description(self, sample_method: dict):
        """Test: Method có logic description."""
        from midicoder.dsl.projection import MethodDefinition
        
        method: MethodDefinition = sample_method
        assert "logic" in method
        assert "currency" in method["logic"].lower()

    def test_async_method(self):
        """Test: Async method flag."""
        async_method = {
            "name": "fetch_exchange_rate",
            "async_": True,
            "params": [],
            "returns": "decimal"
        }
        
        from midicoder.dsl.projection import MethodDefinition
        method: MethodDefinition = async_method
        
        assert method["async_"] is True


# ============================================================================
# Tests for ValidationRule (RED Phase)
# ============================================================================


class TestValidationRule:
    """Tests cho ValidationRule DSL."""

    def test_import_validation_rule(self):
        """Test: Import ValidationRule từ projection module."""
        from midicoder.dsl.projection import ValidationRule
        assert ValidationRule is not None

    def test_validation_rule_structure(self, sample_validation_rule: dict):
        """Test: Validation rule có đúng structure."""
        from midicoder.dsl.projection import ValidationRule
        
        rule: ValidationRule = sample_validation_rule
        assert "name" in rule
        assert "condition" in rule
        assert "error_code" in rule
        assert "error_message" in rule

    def test_validation_rule_error_code(self, sample_validation_rule: dict):
        """Test: Validation rule có error code chuẩn."""
        from midicoder.dsl.projection import ValidationRule
        
        rule: ValidationRule = sample_validation_rule
        assert rule["error_code"] == "MDC-VO-EMAIL-001"

    def test_validation_rule_severity(self, sample_validation_rule: dict):
        """Test: Validation rule có severity."""
        from midicoder.dsl.projection import ValidationRule
        
        rule: ValidationRule = sample_validation_rule
        assert rule["severity"] == "error"

    def test_validation_rule_warning_severity(self):
        """Test: Validation rule với warning severity."""
        warning_rule = {
            "name": "deprecation_warning",
            "condition": "legacy_field is not None",
            "error_code": "MDC-VO-WARN-001",
            "error_message": "Field này sẽ bị deprecated",
            "severity": "warning"
        }
        
        from midicoder.dsl.projection import ValidationRule
        rule: ValidationRule = warning_rule
        
        assert rule["severity"] == "warning"


# ============================================================================
# Tests for ExtendedValueObjectParams (RED Phase)
# ============================================================================


class TestExtendedValueObjectParams:
    """Tests cho Extended Value Object DSL."""

    def test_import_extended_value_object_params(self):
        """Test: Import ExtendedValueObjectParams từ projection module."""
        from midicoder.dsl.projection import ExtendedValueObjectParams
        assert ExtendedValueObjectParams is not None

    def test_vo_with_inheritance(self, sample_extended_vo: dict):
        """Test: Value Object với inheritance (extends)."""
        from midicoder.dsl.projection import ExtendedValueObjectParams
        
        vo: ExtendedValueObjectParams = sample_extended_vo
        assert vo["id"] == "BillingAddress"
        assert vo["extends"] == "Address"

    def test_vo_with_methods(self):
        """Test: Value Object với methods list."""
        vo_with_methods = {
            "id": "Money",
            "fields": [
                {"name": "amount", "type": "decimal", "required": True},
                {"name": "currency", "type": "string", "length": 3}
            ],
            "methods": [
                {
                    "name": "add",
                    "params": [{"name": "other", "type": "ref", "ref_to": "Money"}],
                    "returns": "Money"
                }
            ]
        }
        
        from midicoder.dsl.projection import ExtendedValueObjectParams
        vo: ExtendedValueObjectParams = vo_with_methods
        
        assert "methods" in vo
        assert len(vo["methods"]) == 1

    def test_vo_with_validation_rules(self):
        """Test: Value Object với validation rules."""
        vo_with_validation = {
            "id": "EmailAddress",
            "fields": [
                {"name": "local_part", "type": "string"},
                {"name": "domain", "type": "string"}
            ],
            "validation_rules": [
                {
                    "name": "valid_email",
                    "condition": "matches email_regex",
                    "error_code": "MDC-VO-EMAIL-001",
                    "error_message": "Email không hợp lệ"
                }
            ]
        }
        
        from midicoder.dsl.projection import ExtendedValueObjectParams
        vo: ExtendedValueObjectParams = vo_with_validation
        
        assert "validation_rules" in vo
        assert len(vo["validation_rules"]) == 1

    def test_vo_with_compliance_tags(self):
        """Test: Value Object với compliance và tags."""
        vo_with_compliance = {
            "id": "PatientId",
            "fields": [{"name": "id", "type": "string"}],
            "tags": ["pii", "healthcare"],
            "compliance": [
                {
                    "overlay": "RX01",
                    "rules": ["encrypt_at_rest", "audit_access"]
                }
            ]
        }
        
        from midicoder.dsl.projection import ExtendedValueObjectParams
        vo: ExtendedValueObjectParams = vo_with_compliance
        
        assert "tags" in vo
        assert "compliance" in vo
        assert "pii" in vo["tags"]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])