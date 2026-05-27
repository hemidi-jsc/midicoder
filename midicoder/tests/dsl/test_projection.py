"""
Test suite cho DSL v1 Projection Module.

Test coverage cho:
- ProjectionNode creation và validation
- ProjectionTree operations
- NodeKind enum
- TypedDict param models

Mục tiêu coverage: >80%
"""

from pathlib import Path
from unittest import TestCase

import pytest

from midicoder.dsl.projection import (
    NodeKind,
    ProjectionNode,
    ProjectionTree,
)


# ============================================================================
# ProjectionNode Tests
# ============================================================================


class TestProjectionNodeCreation(TestCase):
    """Test ProjectionNode creation và validation."""

    def test_create_entity_node(self):
        """Test tạo Entity node thành công."""
        node = ProjectionNode(
            id="Order",
            kind=NodeKind.ENTITY,
            params={
                "id": "Order",
                "fields": [{"name": "order_id", "type": "string"}],
                "tenant_scope": "tenant_isolated",
            },
        )
        self.assertEqual(node.id, "Order")
        self.assertEqual(node.kind, NodeKind.ENTITY)
        self.assertEqual(node.params["tenant_scope"], "tenant_isolated")

    def test_create_command_node(self):
        """Test tạo Command node thành công."""
        node = ProjectionNode(
            id="CreateOrder",
            kind=NodeKind.COMMAND,
            params={
                "id": "CreateOrder",
                "input": [{"name": "product_id", "type": "string"}],
                "category": "create",
            },
        )
        self.assertEqual(node.id, "CreateOrder")
        self.assertEqual(node.kind, NodeKind.COMMAND)
        self.assertEqual(node.params["category"], "create")

    def test_node_missing_id_raises_error(self):
        """Test node không có ID throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="",
                kind=NodeKind.ENTITY,
                params={"fields": []},
            )
        self.assertIn("id là bắt buộc", str(context.exception))

    def test_node_missing_required_field_raises_error(self):
        """Test node thiếu required field throw error."""
        with self.assertRaises(ValueError) as context:
            ProjectionNode(
                id="TestEntity",
                kind=NodeKind.ENTITY,
                params={"id": "TestEntity"},  # Thiếu "fields"
            )
        self.assertIn("cần field: fields", str(context.exception))


class TestProjectionNodeMethods(TestCase):
    """Test ProjectionNode methods."""

    def test_get_param_with_default(self):
        """Test get_param với default value."""
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.ENTITY,
            params={"id": "Test", "fields": []},
        )
        self.assertIsNone(node.get_param("missing_key"))
        self.assertEqual(node.get_param("missing_key", "default"), "default")

    def test_add_child(self):
        """Test add child node."""
        parent = ProjectionNode(
            id="Parent",
            kind=NodeKind.ENTITY,
            params={"id": "Parent", "fields": []},
        )
        child = ProjectionNode(
            id="Child",
            kind=NodeKind.VALUE_OBJECT,
            params={"id": "Child", "fields": []},
        )
        parent.add_child(child)
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(parent.children[0].id, "Child")

    def test_add_dependency(self):
        """Test add dependency."""
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.COMMAND,
            params={"id": "Test", "input": []},
        )
        node.add_dependency("Entity1")
        node.add_dependency("Entity2")
        self.assertEqual(len(node.dependencies), 2)
        self.assertIn("Entity1", node.dependencies)

    def test_add_dependency_no_duplicates(self):
        """Test add dependency không tạo duplicates."""
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.COMMAND,
            params={"id": "Test", "input": []},
        )
        node.add_dependency("Entity1")
        node.add_dependency("Entity1")  # Duplicate
        self.assertEqual(len(node.dependencies), 1)

    def test_get_tags_empty_default(self):
        """Test get_tags trả về empty list khi không có tags."""
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.ENTITY,
            params={"id": "Test", "fields": []},
        )
        self.assertEqual(node.get_tags(), [])

    def test_get_tags_from_params(self):
        """Test get_tags trả về tags từ params."""
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.ENTITY,
            params={"id": "Test", "fields": [], "tags": ["tag1", "tag2"]},
        )
        self.assertEqual(node.get_tags(), ["tag1", "tag2"])


# ============================================================================
# ProjectionTree Tests
# ============================================================================


class TestProjectionTreeOperations(TestCase):
    """Test ProjectionTree operations."""

    def test_add_node(self):
        """Test add node vào tree."""
        tree = ProjectionTree()
        node = ProjectionNode(
            id="Test",
            kind=NodeKind.ENTITY,
            params={"id": "Test", "fields": []},
        )
        tree.add_node(node)
        self.assertEqual(tree.node_count(), 1)
        self.assertEqual(tree.get_node("Test"), node)

    def test_get_node_not_found(self):
        """Test get_node trả về None khi không tìm thấy."""
        tree = ProjectionTree()
        self.assertIsNone(tree.get_node("NonExistent"))

    def test_get_nodes_by_kind(self):
        """Test get_nodes_by_kind trả về danh sách nodes."""
        tree = ProjectionTree()
        entity1 = ProjectionNode(
            id="Entity1",
            kind=NodeKind.ENTITY,
            params={"id": "Entity1", "fields": []},
        )
        entity2 = ProjectionNode(
            id="Entity2",
            kind=NodeKind.ENTITY,
            params={"id": "Entity2", "fields": []},
        )
        command = ProjectionNode(
            id="Command1",
            kind=NodeKind.COMMAND,
            params={"id": "Command1", "input": []},
        )
        tree.add_node(entity1)
        tree.add_node(entity2)
        tree.add_node(command)

        entities = tree.get_nodes_by_kind(NodeKind.ENTITY)
        self.assertEqual(len(entities), 2)

    def test_get_entities(self):
        """Test get_entities convenience method."""
        tree = ProjectionTree()
        entity = ProjectionNode(
            id="Test",
            kind=NodeKind.ENTITY,
            params={"id": "Test", "fields": []},
        )
        tree.add_node(entity)
        self.assertEqual(len(tree.get_entities()), 1)

    def test_get_commands(self):
        """Test get_commands convenience method."""
        tree = ProjectionTree()
        command = ProjectionNode(
            id="Test",
            kind=NodeKind.COMMAND,
            params={"id": "Test", "input": []},
        )
        tree.add_node(command)
        self.assertEqual(len(tree.get_commands()), 1)

    def test_node_count(self):
        """Test node_count trả về tổng số nodes."""
        tree = ProjectionTree()
        self.assertEqual(tree.node_count(), 0)

        for i in range(5):
            node = ProjectionNode(
                id=f"Node{i}",
                kind=NodeKind.ENTITY,
                params={"id": f"Node{i}", "fields": []},
            )
            tree.add_node(node)

        self.assertEqual(tree.node_count(), 5)

    def test_kind_count(self):
        """Test kind_count trả về số nodes theo kind."""
        tree = ProjectionTree()

        for i in range(3):
            node = ProjectionNode(
                id=f"Entity{i}",
                kind=NodeKind.ENTITY,
                params={"id": f"Entity{i}", "fields": []},
            )
            tree.add_node(node)

        for i in range(2):
            node = ProjectionNode(
                id=f"Command{i}",
                kind=NodeKind.COMMAND,
                params={"id": f"Command{i}", "input": []},
            )
            tree.add_node(node)

        self.assertEqual(tree.kind_count(NodeKind.ENTITY), 3)
        self.assertEqual(tree.kind_count(NodeKind.COMMAND), 2)

    def test_all_kinds(self):
        """Test all_kinds trả về danh sách kinds có trong tree."""
        tree = ProjectionTree()

        ProjectionNode(
            id="Entity1",
            kind=NodeKind.ENTITY,
            params={"id": "Entity1", "fields": []},
        )
        tree.add_node(
            ProjectionNode(
                id="Entity1",
                kind=NodeKind.ENTITY,
                params={"id": "Entity1", "fields": []},
            )
        )
        tree.add_node(
            ProjectionNode(
                id="Command1",
                kind=NodeKind.COMMAND,
                params={"id": "Command1", "input": []},
            )
        )

        kinds = tree.all_kinds()
        self.assertIn(NodeKind.ENTITY, kinds)
        self.assertIn(NodeKind.COMMAND, kinds)
        self.assertEqual(len(kinds), 2)


# ============================================================================
# NodeKind Enum Tests
# ============================================================================


class TestNodeKind(TestCase):
    """Test NodeKind enum."""

    def test_node_kind_count(self):
        """Test số lượng NodeKind values (101 node types)."""
        kind_count = len(list(NodeKind))
        self.assertGreater(kind_count, 100, "Nên có ít nhất 101 node types")

    def test_node_kind_values_are_strings(self):
        """Test NodeKind values đều là strings."""
        for kind in NodeKind:
            self.assertIsInstance(kind.value, str)

    def test_node_kind_organization(self):
        """Test NodeKind organized theo layers."""
        # Domain layer
        self.assertEqual(NodeKind.ENTITY.value, "domain.entity")
        self.assertEqual(NodeKind.VALUE_OBJECT.value, "domain.value_object")

        # Application layer
        self.assertEqual(NodeKind.COMMAND.value, "app.command")
        self.assertEqual(NodeKind.QUERY.value, "app.query")

        # API layer
        self.assertEqual(NodeKind.HTTP_ROUTE.value, "api.http_route")

        # Infrastructure layer
        self.assertEqual(NodeKind.DATASOURCE.value, "infra.datasource")

        # Observability
        self.assertEqual(NodeKind.METRIC.value, "ops.metric")


# ============================================================================
# Integration Tests
# ============================================================================


class TestProjectionIntegration(TestCase):
    """Integration tests cho Projection module."""

    def test_full_workflow_entity_command(self):
        """Test full workflow: create entity, command, add to tree."""
        # Create entity
        entity = ProjectionNode(
            id="Order",
            kind=NodeKind.ENTITY,
            params={
                "id": "Order",
                "fields": [
                    {"name": "order_id", "type": "string"},
                    {"name": "total", "type": "decimal"},
                ],
                "tenant_scope": "tenant_isolated",
            },
        )

        # Create command
        command = ProjectionNode(
            id="CreateOrder",
            kind=NodeKind.COMMAND,
            params={
                "id": "CreateOrder",
                "input": [
                    {"name": "product_id", "type": "string"},
                    {"name": "quantity", "type": "int"},
                ],
                "category": "create",
                "writes_to": ["Order"],
            },
        )

        # Add command dependency on entity
        command.add_dependency("Order")

        # Add to tree
        tree = ProjectionTree()
        tree.add_node(entity)
        tree.add_node(command)

        # Verify
        self.assertEqual(tree.node_count(), 2)
        self.assertEqual(len(tree.get_entities()), 1)
        self.assertEqual(len(tree.get_commands()), 1)
        self.assertEqual(len(command.dependencies), 1)

    def test_multiple_node_types_in_tree(self):
        """Test tree với nhiều loại nodes."""
        tree = ProjectionTree()

        # Entity
        tree.add_node(
            ProjectionNode(
                id="Product",
                kind=NodeKind.ENTITY,
                params={"id": "Product", "fields": []},
            )
        )

        # Query
        tree.add_node(
            ProjectionNode(
                id="GetProduct",
                kind=NodeKind.QUERY,
                params={"id": "GetProduct", "returns": []},
            )
        )

        # HTTP Route
        tree.add_node(
            ProjectionNode(
                id="GetProductRoute",
                kind=NodeKind.HTTP_ROUTE,
                params={"id": "GetProductRoute", "method": "GET", "path": "/products/{id}"},
            )
        )

        # Verify counts
        self.assertEqual(tree.node_count(), 3)
        self.assertEqual(tree.kind_count(NodeKind.ENTITY), 1)
        self.assertEqual(tree.kind_count(NodeKind.QUERY), 1)
        self.assertEqual(tree.kind_count(NodeKind.HTTP_ROUTE), 1)


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])