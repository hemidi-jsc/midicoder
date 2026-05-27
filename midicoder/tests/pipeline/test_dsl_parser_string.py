"""
Tests cho DSLParser - String parsing (thay thế parse_directory).

Tests này validate:
- parse_yaml_string() cho mỗi category
- Validation missing category → error
- Integration: build_mir() flow mới

Theo CURRENT_TASK_REQUIREMENT.md (P0-1A).

Author: Midicoder Team
"""

import pytest
import yaml

from midicoder.dsl.projection import ProjectionTree, NodeKind


# ============================================================================
# Test data - YAML templates cho mỗi category
# ============================================================================

ENTITIES_YAML = """
entities:
  - id: Order
    description: "Đơn hàng"
    fields:
      - name: id
        type: uuid
        required: true
      - name: tenant_id
        type: uuid
        required: true
      - name: total
        type: decimal
"""

COMMANDS_YAML = """
commands:
  - id: CreateOrder
    description: "Tạo đơn hàng mới"
    input:
      - name: order_id
        type: uuid
        required: true
      - name: tenant_id
        type: uuid
        required: true
      - name: total
        type: decimal
    fetches: []
    guards: []
    effects:
      - type: create
        target: Order
    errors: []
    returns:
      - name: order_id
        type: uuid
    category: create
    emits: [OrderCreated]
    required_roles: []
    required_permissions: [order.create]
    writes_to: [Order]
    transaction: true
    tenant_scope: tenant_isolated
"""

QUERIES_YAML = """
queries:
  - id: ListOrders
    description: "Liệt kê đơn hàng"
    input:
      - name: tenant_id
        type: uuid
        required: true
      - name: page
        type: integer
      - name: page_size
        type: integer
    fetches: []
    guards: []
    returns:
      - name: orders
        type: array
      - name: total
        type: integer
    category: list
    reads_from: [Order]
    required_roles: []
    required_permissions: [order.read]
    tenant_scope: tenant_isolated
"""

EVENTS_YAML = """
events:
  - id: OrderCreated
    description: "Sự kiện đơn hàng được tạo"
    type: domain_event
    source_entity: Order
    fields:
      - name: order_id
        type: uuid
      - name: tenant_id
        type: uuid
      - name: total
        type: decimal
    version: "1.0.0"
    tenant_scope: tenant_isolated
"""

WORKFLOWS_YAML = """
workflows:
  - id: Checkout
    description: "Quy trình checkout"
    states:
      - id: cart
        description: "Giỏ hàng"
      - id: payment
        description: "Thanh toán"
      - id: confirmation
        description: "Xác nhận"
    transitions:
      - from: cart
        to: payment
        event: SubmitPayment
      - from: payment
        to: confirmation
        event: PaymentSuccess
    guards: []
    effects: []
    tenant_scope: tenant_isolated
"""

VALUE_OBJECTS_YAML = """
value_objects:
  - id: Money
    description: "Giá trị tiền tệ"
    fields:
      - name: amount
        type: decimal
        required: true
      - name: currency
        type: string
        required: true
    immutable: true
    comparable: true
    extends: null
"""

GUARDS_YAML = """
guards:
  - id: ValidateStock
    description: "Kiểm tra kho hàng"
    type: validation
    condition:
      field: stock_quantity
      operator: ">"
      value: 0
    error: InsufficientStock
"""


class TestDSLParserParseYamlString:
    """Tests cho DSLParser.parse_yaml_string()."""

    @pytest.fixture
    def dsl_parser(self):
        """DSLParser fixture."""
        from midicoder.pipeline.dsl_parser import DSLParser
        return DSLParser()

    def test_parse_entities_yaml(self, dsl_parser):
        """Test parse YAML entities string."""
        nodes = dsl_parser.parse_yaml_string(ENTITIES_YAML, "entities")

        assert len(nodes) == 1
        assert nodes[0].id == "Order"
        assert nodes[0].kind == NodeKind.ENTITY
        assert nodes[0].params["description"] == "Đơn hàng"
        assert len(nodes[0].params["fields"]) == 3

    def test_parse_commands_yaml(self, dsl_parser):
        """Test parse YAML commands string."""
        nodes = dsl_parser.parse_yaml_string(COMMANDS_YAML, "commands")

        assert len(nodes) == 1
        assert nodes[0].id == "CreateOrder"
        assert nodes[0].kind == NodeKind.COMMAND
        assert nodes[0].params["category"] == "create"
        assert nodes[0].params["tenant_scope"] == "tenant_isolated"

    def test_parse_queries_yaml(self, dsl_parser):
        """Test parse YAML queries string."""
        nodes = dsl_parser.parse_yaml_string(QUERIES_YAML, "queries")

        assert len(nodes) == 1
        assert nodes[0].id == "ListOrders"
        assert nodes[0].kind == NodeKind.QUERY
        assert nodes[0].params["category"] == "list"

    def test_parse_events_yaml(self, dsl_parser):
        """Test parse YAML events string."""
        nodes = dsl_parser.parse_yaml_string(EVENTS_YAML, "events")

        assert len(nodes) == 1
        assert nodes[0].id == "OrderCreated"
        assert nodes[0].kind == NodeKind.EVENT
        assert nodes[0].params["type"] == "domain_event"

    def test_parse_workflows_yaml(self, dsl_parser):
        """Test parse YAML workflows string."""
        nodes = dsl_parser.parse_yaml_string(WORKFLOWS_YAML, "workflows")

        assert len(nodes) == 1
        assert nodes[0].id == "Checkout"
        assert nodes[0].kind == NodeKind.WORKFLOW
        assert len(nodes[0].params["states"]) == 3

    def test_parse_value_objects_yaml(self, dsl_parser):
        """Test parse YAML value objects string."""
        nodes = dsl_parser.parse_yaml_string(VALUE_OBJECTS_YAML, "value_objects")

        assert len(nodes) == 1
        assert nodes[0].id == "Money"
        assert nodes[0].kind == NodeKind.VALUE_OBJECT
        assert nodes[0].params["immutable"] is True

    def test_parse_guards_yaml(self, dsl_parser):
        """Test parse YAML guards string."""
        nodes = dsl_parser.parse_yaml_string(GUARDS_YAML, "guards")

        assert len(nodes) == 1
        assert nodes[0].id == "ValidateStock"
        assert nodes[0].kind == NodeKind.GUARD
        assert nodes[0].params["type"] == "validation"

    def test_parse_unknown_category_raises(self, dsl_parser):
        """Test parse category không hợp lệ → throw error."""
        with pytest.raises(ValueError, match="Unknown contract type"):
            dsl_parser.parse_yaml_string("some: data", "unknown")

    def test_parse_empty_yaml_returns_empty_list(self, dsl_parser):
        """Test parse YAML rỗng → trả về list rỗng."""
        empty_yaml = "entities:\n"
        nodes = dsl_parser.parse_yaml_string(empty_yaml, "entities")
        assert len(nodes) == 0


class TestDSLParserNoDirectoryParsing:
    """Tests xác nhận parse_directory() đã bị loại bỏ."""

    def test_parse_directory_does_not_exist(self):
        """Test parse_directory không còn tồn tại."""
        from midicoder.pipeline.dsl_parser import DSLParser
        parser = DSLParser()
        assert not hasattr(parser, "parse_directory"), \
            "parse_directory() đã bị loại bỏ, dùng parse_yaml_string() thay thế"

    def test_parse_file_does_not_exist(self):
        """Test parse_file không còn tồn tại."""
        from midicoder.pipeline.dsl_parser import DSLParser
        parser = DSLParser()
        assert not hasattr(parser, "parse_file"), \
            "parse_file() đã bị loại bỏ, dùng parse_yaml_string() thay thế"


class TestDSLParserBuildProjectionTree:
    """Tests cho build_projection_tree() — phương thức mới kết hợp nhiều YAML strings."""

    @pytest.fixture
    def dsl_parser(self):
        """DSLParser fixture."""
        from midicoder.pipeline.dsl_parser import DSLParser
        return DSLParser()

    def test_build_projection_tree_all_categories(self, dsl_parser):
        """Test build ProjectionTree từ tất cả categories."""
        yaml_dict = {
            "entities": ENTITIES_YAML,
            "commands": COMMANDS_YAML,
            "queries": QUERIES_YAML,
            "events": EVENTS_YAML,
            "workflows": WORKFLOWS_YAML,
            "value_objects": VALUE_OBJECTS_YAML,
            "guards": GUARDS_YAML,
        }

        tree = dsl_parser.build_projection_tree(yaml_dict)

        assert isinstance(tree, ProjectionTree)
        assert tree.node_count() == 7  # 1 entity + 1 command + 1 query + 1 event + 1 workflow + 1 vo + 1 guard

    def test_build_projection_tree_partial_categories(self, dsl_parser):
        """Test build ProjectionTree từ một số categories."""
        yaml_dict = {
            "entities": ENTITIES_YAML,
            "commands": COMMANDS_YAML,
        }

        tree = dsl_parser.build_projection_tree(yaml_dict)

        assert isinstance(tree, ProjectionTree)
        assert tree.node_count() == 2  # 1 entity + 1 command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])