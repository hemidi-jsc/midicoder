"""
Tests for Value Object Parser Module.

Test suite cho ValueObjectParser:
- Parse YAML → ValueObject models
- Field validation
- Inheritance (extends)
- Error handling

Theo TDD: Tests viết trước implementation.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_base_domain_model.models import (
    ValueObject,
    VOField,
    VOFieldType,
)
from midicoder.packs.cp_base_domain_model.vo_parser import ValueObjectParser


# ============================================================================
# Test Data
# ============================================================================

VALID_VO_YAML = """
value_objects:
  - id: Money
    description: "Giá tiền với currency"
    fields:
      - name: amount
        type: decimal
        precision: 10
        scale: 2
        required: true
      - name: currency
        type: string
        enum_values:
          - VND
          - USD
          - EUR
        required: true
    immutable: true
    comparable: true

  - id: EmailAddress
    description: "Địa chỉ email"
    fields:
      - name: value
        type: string
        pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
        required: true
    immutable: true

  - id: Address
    description: "Địa chỉ giao hàng"
    fields:
      - name: street
        type: string
        required: true
      - name: city
        type: string
        required: true
      - name: postal_code
        type: string
        required: true
      - name: country
        type: string
        required: true
    immutable: false
"""

INHERITANCE_VO_YAML = """
value_objects:
  - id: BaseContact
    description: "Contact thông tin cơ bản"
    fields:
      - name: name
        type: string
        required: true
      - name: email
        type: string
        required: true

  - id: CustomerContact
    description: "Khách hàng contact"
    extends: BaseContact
    fields:
      - name: customer_id
        type: string
        required: true
      - name: preferred_channel
        type: string
        enum_values:
          - email
          - phone
          - sms

  - id: SupplierContact
    description: "Nhà cung cấp contact"
    extends: BaseContact
    fields:
      - name: supplier_id
        type: string
        required: true
"""

EMPTY_VO_YAML = """
value_objects: []
"""

INVALID_YAML = """
value_objects:
  - id: Test
    invalid: [
"""

MISSING_ID_YAML = """
value_objects:
  - description: "Missing ID"
    fields: []
"""

INVALID_FIELD_TYPE_YAML = """
value_objects:
  - id: TestVO
    fields:
      - name: test
        type: invalid_type
"""


# ============================================================================
# Test ValueObjectParser
# ============================================================================

class TestValueObjectParser:
    """Test suite cho ValueObjectParser."""

    def setup_method(self):
        """Setup trước mỗi test."""
        self.parser = ValueObjectParser()

    def test_parse_valid_value_objects(self):
        """Test parse valid value objects YAML."""
        vos = self.parser.parse(VALID_VO_YAML)
        
        assert len(vos) == 3
        
        # Check Money
        money = vos[0]
        assert money.id == "Money"
        assert money.description == "Giá tiền với currency"
        assert money.immutable is True
        assert money.comparable is True
        assert len(money.fields) == 2
        
        # Check Money fields
        assert money.fields[0].name == "amount"
        assert money.fields[0].field_type == VOFieldType.DECIMAL
        assert money.fields[0].precision == 10
        assert money.fields[0].scale == 2
        assert money.fields[0].required is True
        
        assert money.fields[1].name == "currency"
        assert money.fields[1].enum_values == ["VND", "USD", "EUR"]

    def test_parse_email_with_pattern(self):
        """Test parse VO với pattern validation."""
        vos = self.parser.parse(VALID_VO_YAML)
        
        email = vos[1]
        assert email.id == "EmailAddress"
        assert len(email.fields) == 1
        assert email.fields[0].name == "value"
        assert email.fields[0].pattern is not None

    def test_parse_inheritance(self):
        """Test parse VO với inheritance (extends)."""
        vos = self.parser.parse(INHERITANCE_VO_YAML)
        
        assert len(vos) == 3
        
        # BaseContact
        base = vos[0]
        assert base.id == "BaseContact"
        assert base.extends is None
        
        # CustomerContact extends BaseContact
        customer = vos[1]
        assert customer.id == "CustomerContact"
        assert customer.extends == "BaseContact"
        
        # SupplierContact extends BaseContact
        supplier = vos[2]
        assert supplier.id == "SupplierContact"
        assert supplier.extends == "BaseContact"

    def test_parse_empty_value_objects(self):
        """Test parse empty value objects list."""
        vos = self.parser.parse(EMPTY_VO_YAML)
        assert len(vos) == 0

    def test_parse_missing_value_objects_key(self):
        """Test parse missing 'value_objects' key."""
        yaml_content = "entities: []"
        
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(yaml_content)
        
        assert "value_object" in str(exc_info.value).lower() or "value_objects" in str(exc_info.value).lower()

    def test_parse_invalid_yaml(self):
        """Test parse invalid YAML."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(INVALID_YAML)
        
        assert "yaml" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_parse_missing_id(self):
        """Test parse VO missing ID."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(MISSING_ID_YAML)
        
        assert "id" in str(exc_info.value).lower()

    def test_parse_invalid_field_type(self):
        """Test parse VO với invalid field type."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(INVALID_FIELD_TYPE_YAML)
        
        assert "type" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_parse_vo_with_optional_fields(self):
        """Test parse VO với optional fields."""
        yaml_content = """
value_objects:
  - id: SimpleVO
    fields:
      - name: value
        type: string
"""
        vos = self.parser.parse(yaml_content)
        
        assert len(vos) == 1
        vo = vos[0]
        
        assert vo.description == ""
        assert vo.immutable is False
        assert vo.comparable is False
        assert vo.extends is None

    def test_parse_vo_with_all_field_types(self):
        """Test parse VO với tất cả field types."""
        yaml_content = """
value_objects:
  - id: AllTypesVO
    fields:
      - name: str_field
        type: string
      - name: int_field
        type: integer
      - name: bool_field
        type: boolean
      - name: dt_field
        type: datetime
      - name: uuid_field
        type: uuid
      - name: json_field
        type: json
      - name: dec_field
        type: decimal
        precision: 18
        scale: 4
"""
        vos = self.parser.parse(yaml_content)
        
        assert len(vos) == 1
        vo = vos[0]
        
        assert vo.fields[0].field_type == VOFieldType.STRING
        assert vo.fields[1].field_type == VOFieldType.INTEGER
        assert vo.fields[2].field_type == VOFieldType.BOOLEAN
        assert vo.fields[3].field_type == VOFieldType.DATETIME
        assert vo.fields[4].field_type == VOFieldType.UUID
        assert vo.fields[5].field_type == VOFieldType.JSON
        assert vo.fields[6].field_type == VOFieldType.DECIMAL


# ============================================================================
# Test ValueObject Model
# ============================================================================

class TestValueObjectModel:
    """Test suite cho ValueObject model."""

    def test_vo_defaults(self):
        """Test ValueObject default values."""
        vo = ValueObject(
            id="Test",
            fields=[]
        )
        
        assert vo.description == ""
        assert vo.immutable is False
        assert vo.comparable is False
        assert vo.extends is None

    def test_vo_to_dict(self):
        """Test ValueObject.to_dict() method."""
        vo = ValueObject(
            id="Test",
            description="Test VO",
            fields=[VOField(name="value", field_type=VOFieldType.STRING)],
            immutable=True,
            comparable=True,
            extends="Base"
        )
        
        data = vo.to_dict()
        
        assert data["id"] == "Test"
        assert data["description"] == "Test VO"
        assert data["immutable"] is True
        assert data["comparable"] is True
        assert data["extends"] == "Base"
        assert len(data["fields"]) == 1

    def test_vo_from_dict(self):
        """Test ValueObject.from_dict() method."""
        data = {
            "id": "Test",
            "description": "Test",
            "fields": [
                {"name": "value", "type": "string", "required": True}
            ],
            "immutable": True
        }
        
        vo = ValueObject.from_dict(data)
        
        assert vo.id == "Test"
        assert vo.immutable is True
        assert len(vo.fields) == 1
        assert vo.fields[0].required is True


# ============================================================================
# VO Emitter Gap Coverage Tests
# ============================================================================

class TestVOEmitterGapCoverage:
    """Gap coverage tests cho vo_emitter.py — push ≥99%."""

    def setup_method(self):
        """Setup trước mỗi test."""
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.vo_fastapi import FastAPIValueObjectEmitter
        self.emitter = FastAPIValueObjectEmitter(stack_dir=Path("/tmp"))

    def test_emit_validation_rule(self):
        """Test _emit_validation_rule() (lines 353-355)."""
        rule = {
            "name": "amount_positive",
            "condition": "self.amount > 0",
            "error_code": "MDC-B01-999",
            "error_message": "Số tiền phải dương",
        }
        emitted = self.emitter._emit_validation_rule(rule)
        assert emitted.name == "amount_positive"
        assert emitted.error_message == "Số tiền phải dương"

    def test_build_method_params_empty(self):
        """Test _build_method_params() với empty params (line 427)."""
        result = self.emitter._build_method_params([])
        assert result == "self"

    def test_get_nested_classes(self):
        """Test get_nested_classes() (line 479)."""
        nested = self.emitter.get_nested_classes()
        assert isinstance(nested, dict)
        assert len(nested) == 0

    def test_emit_field_with_nested_class_object_type(self):
        """Test _emit_field() with object type (nested class branch)."""
        from midicoder.dsl.projection import FieldDefinition
        fd: FieldDefinition = {"name": "config", "type": "object", "required": False}
        ef = self.emitter._emit_field(fd)
        assert ef.nested_class is not None

    def test_emit_field_with_nested_class_array_type(self):
        """Test _emit_field() with array type (nested class branch)."""
        from midicoder.dsl.projection import FieldDefinition
        fd: FieldDefinition = {"name": "items", "type": "array", "required": False}
        ef = self.emitter._emit_field(fd)
        assert ef.nested_class is not None

    def test_emit_raises_when_parent_not_found(self):
        """Test emit() raises B01_VALUE_OBJECT_NOT_FOUND when parent missing (line 246)."""
        from midicoder.errors import MidicoderError
        vo_params = {
            "id": "ChildVO",
            "extends": "MissingParent",
            "fields": [],
        }
        # non-empty dict so `if inherits_from and parent_vo_map` is True
        parent_map = {"OtherParent": {"id": "OtherParent", "fields": []}}
        with pytest.raises(MidicoderError):
            self.emitter.emit(vo_params, parent_vo_map=parent_map)


# ============================================================================
# VO Parser Gap Coverage Tests
# ============================================================================

class TestVOParserGapCoverage:
    """Gap coverage tests cho vo_parser.py — push ≥99%."""

    def setup_method(self):
        """Setup trước mỗi test."""
        self.parser = ValueObjectParser()

    def test_parse_vo_without_fields_key(self):
        """Test parse VO khi không có key 'fields' (line 118->122 branch)."""
        yaml_content = """
value_objects:
  - id: MarkerVO
    description: "VO không có fields"
"""
        vos = self.parser.parse(yaml_content)
        assert len(vos) == 1
        assert vos[0].id == "MarkerVO"
        assert len(vos[0].fields) == 0

    def test_parse_field_missing_name(self):
        """Test parse field khi thiếu 'name' (line 151 branch)."""
        yaml_content = """
value_objects:
  - id: BadFieldVO
    fields:
      - type: string
"""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(yaml_content)

        assert "name" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower() or "field" in str(exc_info.value).lower()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "TestValueObjectParser",
    "TestValueObjectModel",
    "TestVOEmitterGapCoverage",
    "TestVOParserGapCoverage",
]