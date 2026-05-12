"""
Tests for Command Parser Module.

Test suite cho CommandParser:
- Parse YAML → Command models
- Field validation
- Error handling

Theo TDD: Tests viết trước implementation.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from dataclasses import dataclass, field

# Import models trực tiếp từ models module
from midicoder.emitters.core.cp01_domain_model.command_models import (
    Command,
    Field as CommandField,
    FieldType as CommandFieldType,
)
from midicoder.emitters.core.cp01_domain_model.command_parser import CommandParser

# Alias cho tests
Field = CommandField
FieldType = CommandFieldType


# ============================================================================
# Test Data
# ============================================================================

VALID_COMMAND_YAML = """
commands:
  - id: CreateOrder
    description: "Tạo đơn hàng mới"
    input:
      - name: order_id
        type: string
        required: true
      - name: total
        type: decimal
        precision: 10
        scale: 2
        required: true
      - name: items
        type: array
        required: true
    fetches:
      - Customer
      - Product
    guards:
      - AuthGuard
      - PermissionGuard
    effects:
      - SendOrderConfirmation
      - UpdateInventory
    errors:
      - ORDER_NOT_FOUND
      - INSUFFICIENT_STOCK
    returns:
      - name: order
        type: object
    category: create
    emits:
      - OrderCreated
    required_roles:
      - admin
      - cashier
    required_permissions:
      - order.create
    writes_to:
      - Order
      - OrderItem
    transaction: true
    tenant_scope: tenant_isolated
"""

MULTIPLE_COMMANDS_YAML = """
commands:
  - id: CreateOrder
    description: "Tạo đơn hàng"
    input:
      - name: data
        type: object
    writes_to:
      - Order
    category: create
    transaction: true

  - id: UpdateOrder
    description: "Cập nhật đơn hàng"
    input:
      - name: order_id
        type: string
        required: true
      - name: status
        type: string
    writes_to:
      - Order
    category: update
    transaction: true

  - id: DeleteOrder
    description: "Xóa đơn hàng"
    input:
      - name: order_id
        type: string
        required: true
    writes_to:
      - Order
    category: delete
    transaction: false
"""

INVALID_YAML = """
commands:
  - id: Test
    invalid_syntax: [
"""

MISSING_ID_YAML = """
commands:
  - description: "Missing ID"
    input: []
    writes_to: []
    category: custom
"""

INVALID_FIELD_TYPE_YAML = """
commands:
  - id: TestCommand
    input:
      - name: test
        type: invalid_type
    writes_to:
      - Test
    category: custom
"""


# ============================================================================
# Test CommandParser
# ============================================================================

class TestCommandParser:
    """Test suite cho CommandParser."""

    def setup_method(self):
        """Setup trước mỗi test."""
        self.parser = CommandParser()

    def test_parse_valid_command(self):
        """Test parse command YAML hợp lệ."""
        commands = self.parser.parse(VALID_COMMAND_YAML)
        
        assert len(commands) == 1
        cmd = commands[0]
        
        assert cmd.id == "CreateOrder"
        assert cmd.description == "Tạo đơn hàng mới"
        assert cmd.category == "create"
        assert cmd.transaction is True
        assert cmd.tenant_scope == "tenant_isolated"
        
        # Check input fields
        assert len(cmd.input) == 3
        assert cmd.input[0].name == "order_id"
        assert cmd.input[0].field_type == FieldType.STRING
        assert cmd.input[0].required is True
        
        # Check writes_to
        assert "Order" in cmd.writes_to
        assert "OrderItem" in cmd.writes_to
        
        # Check emits
        assert "OrderCreated" in cmd.emits
        
        # Check permissions
        assert "order.create" in cmd.required_permissions

    def test_parse_multiple_commands(self):
        """Test parse nhiều commands trong một file."""
        commands = self.parser.parse(MULTIPLE_COMMANDS_YAML)
        
        assert len(commands) == 3
        assert commands[0].id == "CreateOrder"
        assert commands[1].id == "UpdateOrder"
        assert commands[2].id == "DeleteOrder"
        
        # Check categories
        assert commands[0].category == "create"
        assert commands[1].category == "update"
        assert commands[2].category == "delete"
        
        # Check transaction flags
        assert commands[0].transaction is True
        assert commands[1].transaction is True
        assert commands[2].transaction is False

    def test_parse_empty_commands(self):
        """Test parse file với empty commands list."""
        yaml_content = "commands: []"
        commands = self.parser.parse(yaml_content)
        
        assert len(commands) == 0

    def test_parse_missing_commands_key(self):
        """Test parse file thiếu 'commands' key."""
        yaml_content = "entities: []"
        
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(yaml_content)
        
        assert "commands" in str(exc_info.value).lower()

    def test_parse_invalid_yaml(self):
        """Test parse YAML không hợp lệ."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(INVALID_YAML)
        
        # Should raise YAML parse error
        assert "yaml" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_parse_command_missing_id(self):
        """Test parse command thiếu ID."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(MISSING_ID_YAML)
        
        assert "id" in str(exc_info.value).lower()

    def test_parse_command_with_invalid_field_type(self):
        """Test parse command với field type không hợp lệ."""
        with pytest.raises(Exception) as exc_info:
            self.parser.parse(INVALID_FIELD_TYPE_YAML)
        
        assert "type" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_parse_command_with_optional_fields(self):
        """Test parse command với optional fields."""
        yaml_content = """
commands:
  - id: SimpleCommand
    input:
      - name: data
        type: string
    writes_to:
      - Test
    category: custom
"""
        commands = self.parser.parse(yaml_content)
        
        assert len(commands) == 1
        cmd = commands[0]
        
        # Optional fields should have defaults
        assert cmd.fetches == []
        assert cmd.guards == []
        assert cmd.effects == []
        assert cmd.errors == []
        assert cmd.emits == []
        assert cmd.required_roles == []
        assert cmd.required_permissions == []
        assert cmd.transaction is False
        assert cmd.tenant_scope == "global"

    def test_parse_command_with_pagination(self):
        """Test parse command với pagination config."""
        # Query commands need writes_to for now (simplified validation)
        yaml_content = """
commands:
  - id: QueryCommand
    input:
      - name: page
        type: integer
        default: 1
      - name: page_size
        type: integer
        default: 20
      - name: sort_by
        type: string
    fetches:
      - Order
    writes_to:
      - QueryCache
    category: query
"""
        commands = self.parser.parse(yaml_content)
        
        assert len(commands) == 1
        cmd = commands[0]
        
        # Check default values
        assert cmd.input[0].default == 1
        assert cmd.input[1].default == 20

    def test_parse_command_with_complex_fields(self):
        """Test parse command với complex field types."""
        yaml_content = """
commands:
  - id: ComplexCommand
    input:
      - name: metadata
        type: json
      - name: created_at
        type: datetime
      - name: is_active
        type: boolean
        default: true
      - name: status
        type: enum
        enum_values:
          - pending
          - approved
          - rejected
    writes_to:
      - Test
    category: create
"""
        commands = self.parser.parse(yaml_content)
        
        assert len(commands) == 1
        cmd = commands[0]
        
        # Check field types
        assert cmd.input[0].field_type == FieldType.JSON
        assert cmd.input[1].field_type == FieldType.DATETIME
        assert cmd.input[2].field_type == FieldType.BOOLEAN
        assert cmd.input[3].field_type == FieldType.ENUM
        assert cmd.input[3].enum_values == ["pending", "approved", "rejected"]


# ============================================================================
# Test Command Model
# ============================================================================

class TestCommandModel:
    """Test suite cho Command model."""

    def test_command_defaults(self):
        """Test Command model default values."""
        cmd = Command(
            id="Test",
            input=[],
            writes_to=[],
            category="custom"
        )
        
        assert cmd.fetches == []
        assert cmd.guards == []
        assert cmd.effects == []
        assert cmd.errors == []
        assert cmd.returns == []
        assert cmd.emits == []
        assert cmd.required_roles == []
        assert cmd.required_permissions == []
        assert cmd.transaction is False
        assert cmd.tenant_scope == "global"
        assert cmd.description == ""

    def test_command_to_dict(self):
        """Test Command.to_dict() method."""
        cmd = Command(
            id="Test",
            description="Test command",
            input=[Field(name="data", field_type=FieldType.STRING)],
            writes_to=["Test"],
            category="create",
            transaction=True,
            tenant_scope="tenant_isolated"
        )
        
        data = cmd.to_dict()
        
        assert data["id"] == "Test"
        assert data["description"] == "Test command"
        assert data["category"] == "create"
        assert data["transaction"] is True
        assert data["tenant_scope"] == "tenant_isolated"
        assert len(data["input"]) == 1
        assert data["writes_to"] == ["Test"]


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "TestCommandParser",
    "TestCommandModel",
]