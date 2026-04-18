"""
Test suite cho DSL v1 Validator Module.

Test coverage cho:
- Validation pipeline
- Constraint validation
- Validation caching
- ValidationReport
- Actionable insights

Mục tiêu coverage: >80%
"""

from unittest import TestCase

import pytest

from midicoder.dsl.validator import (
    ValidationStatus,
    ValidationReport,
    Validator,
    ValidationError,
    ValidationCache,
    validate_tree,
    quick_validate,
    get_actionable_insights,
)
from midicoder.dsl.constraints import (
    ConstraintLevel,
    ConstraintResult,
)
from midicoder.dsl.dependencies import (
    DependencyAnalysis,
    CycleInfo,
)
from midicoder.dsl.projection import (
    NodeKind,
    ProjectionNode,
    ProjectionTree,
)


# ============================================================================
# ValidationStatus Tests
# ============================================================================


class TestValidationStatus(TestCase):
    """Test ValidationStatus enum."""

    def test_valid_status(self):
        """Test VALID status."""
        self.assertEqual(ValidationStatus.VALID.value, "valid")

    def test_warnings_status(self):
        """Test WARNINGS status."""
        self.assertEqual(ValidationStatus.WARNINGS.value, "warnings")

    def test_errors_status(self):
        """Test ERRORS status."""
        self.assertEqual(ValidationStatus.ERRORS.value, "errors")

    def test_fatal_status(self):
        """Test FATAL status."""
        self.assertEqual(ValidationStatus.FATAL.value, "fatal")


# ============================================================================
# ValidationReport Tests
# ============================================================================


class TestValidationReport(TestCase):
    """Test ValidationReport class."""

    def test_valid_report(self):
        """Test valid report (no errors)."""
        report = ValidationReport(
            status=ValidationStatus.VALID,
            constraint_results=[],
            dependency_analysis=None,
        )
        self.assertTrue(report.is_valid())
        self.assertEqual(report.total_errors, 0)

    def test_report_with_errors(self):
        """Test report with errors."""
        error_result = ConstraintResult(
            constraint_id="TEST001",
            level=ConstraintLevel.ERROR,
            message="Test error",
            node_id="TestNode",
        )

        report = ValidationReport(
            status=ValidationStatus.ERRORS,
            constraint_results=[error_result],
            dependency_analysis=None,
            total_errors=1,
        )
        self.assertFalse(report.is_valid())
        self.assertEqual(len(report.get_errors()), 1)

    def test_report_with_warnings(self):
        """Test report with warnings."""
        warning_result = ConstraintResult(
            constraint_id="TEST002",
            level=ConstraintLevel.WARNING,
            message="Test warning",
            node_id="TestNode",
        )

        report = ValidationReport(
            status=ValidationStatus.WARNINGS,
            constraint_results=[warning_result],
            dependency_analysis=None,
            total_warnings=1,
        )
        self.assertTrue(report.is_valid())  # Warnings still valid
        self.assertEqual(len(report.get_warnings()), 1)

    def test_get_errors_by_node(self):
        """Test grouping errors by node."""
        error1 = ConstraintResult(
            constraint_id="TEST001",
            level=ConstraintLevel.ERROR,
            message="Error 1",
            node_id="Node1",
        )
        error2 = ConstraintResult(
            constraint_id="TEST002",
            level=ConstraintLevel.ERROR,
            message="Error 2",
            node_id="Node1",
        )
        error3 = ConstraintResult(
            constraint_id="TEST003",
            level=ConstraintLevel.ERROR,
            message="Error 3",
            node_id="Node2",
        )

        report = ValidationReport(
            status=ValidationStatus.ERRORS,
            constraint_results=[error1, error2, error3],
            dependency_analysis=None,
            total_errors=3,
        )

        by_node = report.get_errors_by_node()
        self.assertEqual(len(by_node["Node1"]), 2)
        self.assertEqual(len(by_node["Node2"]), 1)

    def test_to_dict(self):
        """Test to_dict serialization."""
        report = ValidationReport(
            status=ValidationStatus.VALID,
            constraint_results=[],
            dependency_analysis=None,
        )
        data = report.to_dict()

        self.assertIn("status", data)
        self.assertIn("total_errors", data)
        self.assertIn("is_valid", data)
        self.assertEqual(data["status"], "valid")


# ============================================================================
# ValidationCache Tests
# ============================================================================


class TestValidationCache(TestCase):
    """Test ValidationCache class."""

    def setUp(self):
        """Setup before each test."""
        self.cache = ValidationCache(max_size=10)

    def test_cache_tree_result(self):
        """Test caching tree validation result."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="Test",
                kind=NodeKind.ENTITY,
                params={"id": "Test", "fields": []},
            )
        )

        report = ValidationReport(
            status=ValidationStatus.VALID,
            constraint_results=[],
            dependency_analysis=None,
        )

        self.cache.set_tree_result(tree, report)

        cached = self.cache.get_tree_result(tree)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.status, ValidationStatus.VALID)

    def test_cache_miss_for_different_tree(self):
        """Test cache miss for different tree."""
        tree1 = ProjectionTree()
        tree1.add_node(
            ProjectionNode(
                id="Node1",
                kind=NodeKind.ENTITY,
                params={"id": "Node1", "fields": []},
            )
        )

        tree2 = ProjectionTree()
        tree2.add_node(
            ProjectionNode(
                id="Node2",
                kind=NodeKind.ENTITY,
                params={"id": "Node2", "fields": []},
            )
        )

        report = ValidationReport(
            status=ValidationStatus.VALID,
            constraint_results=[],
            dependency_analysis=None,
        )

        self.cache.set_tree_result(tree1, report)
        cached = self.cache.get_tree_result(tree2)

        self.assertIsNone(cached)

    def test_cache_clear(self):
        """Test clear all cache."""
        self.cache.clear()
        # Cache should be empty
        self.assertEqual(len(self.cache._tree_cache), 0)
        self.assertEqual(len(self.cache._node_cache), 0)


# ============================================================================
# Validator Tests
# ============================================================================


class TestValidator(TestCase):
    """Test Validator class."""

    def test_validate_empty_tree(self):
        """Test validating empty tree."""
        tree = ProjectionTree()
        validator = Validator()

        report = validator.validate(tree)

        self.assertIsNotNone(report)
        self.assertTrue(report.is_valid())

    def test_validate_tree_with_nodes(self):
        """Test validating tree with nodes."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="TestEntity",
                kind=NodeKind.ENTITY,
                params={
                    "id": "TestEntity",
                    "fields": [
                        {"name": "id", "type": "string"},
                    ],
                },
            )
        )

        validator = Validator()
        report = validator.validate(tree)

        self.assertIsNotNone(report)

    def test_validator_with_caching(self):
        """Test validator with caching enabled."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="TestEntity",
                kind=NodeKind.ENTITY,
                params={"id": "TestEntity", "fields": []},
            )
        )

        cache = ValidationCache()
        validator = Validator(cache=cache, use_cache=True)

        # First validation
        report1 = validator.validate(tree)

        # Second validation should use cache
        report2 = validator.validate(tree)

        self.assertEqual(report1.status, report2.status)

    def test_validator_without_dependency_analysis(self):
        """Test validator without dependency analysis."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="TestEntity",
                kind=NodeKind.ENTITY,
                params={"id": "TestEntity", "fields": []},
            )
        )

        validator = Validator(include_dependency_analysis=False)
        report = validator.validate(tree)

        self.assertIsNone(report.dependency_analysis)


# ============================================================================
# validate_tree Function Tests
# ============================================================================


class TestValidateTree(TestCase):
    """Test validate_tree function."""

    def test_validate_empty_tree(self):
        """Test validate_tree with empty tree."""
        tree = ProjectionTree()
        report = validate_tree(tree)

        self.assertIsNotNone(report)

    def test_validate_tree_with_valid_entity(self):
        """Test validate_tree with valid entity."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="ValidEntity",
                kind=NodeKind.ENTITY,
                params={
                    "id": "ValidEntity",
                    "fields": [{"name": "id", "type": "string"}],
                },
            )
        )

        report = validate_tree(tree)
        self.assertIsNotNone(report)


# ============================================================================
# quick_validate Function Tests
# ============================================================================


class TestQuickValidate(TestCase):
    """Test quick_validate function."""

    def test_quick_validate_valid(self):
        """Test quick_validate with valid tree."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="Test",
                kind=NodeKind.ENTITY,
                params={"id": "Test", "fields": []},
            )
        )

        is_valid = quick_validate(tree)
        self.assertIsInstance(is_valid, bool)

    def test_quick_validate_returns_bool(self):
        """Test quick_validate returns boolean."""
        tree = ProjectionTree()
        tree.add_node(
            ProjectionNode(
                id="TestEntity",
                kind=NodeKind.ENTITY,
                params={
                    "id": "TestEntity",
                    "fields": [
                        {"name": "id", "type": "string"},
                    ],
                },
            )
        )

        result = quick_validate(tree)
        self.assertIsInstance(result, bool)


# ============================================================================
# get_actionable_insights Function Tests
# ============================================================================


class TestGetActionableInsights(TestCase):
    """Test get_actionable_insights function."""

    def test_insights_for_empty_report(self):
        """Test insights for empty report."""
        report = ValidationReport(
            status=ValidationStatus.VALID,
            constraint_results=[],
            dependency_analysis=None,
        )

        insights = get_actionable_insights(report)
        self.assertIsInstance(insights, list)

    def test_insights_for_errors(self):
        """Test insights for report with errors."""
        error_result = ConstraintResult(
            constraint_id="TEST001",
            level=ConstraintLevel.ERROR,
            message="Test error",
            node_id="TestNode",
        )

        report = ValidationReport(
            status=ValidationStatus.ERRORS,
            constraint_results=[error_result],
            dependency_analysis=None,
            total_errors=1,
        )

        insights = get_actionable_insights(report)
        self.assertIsInstance(insights, list)


# ============================================================================
# Integration Tests
# ============================================================================


class TestValidatorIntegration(TestCase):
    """Integration tests for validator."""

    def test_full_validation_workflow(self):
        """Test full validation workflow."""
        # Create tree with multiple nodes
        tree = ProjectionTree()

        # Add entity
        tree.add_node(
            ProjectionNode(
                id="Order",
                kind=NodeKind.ENTITY,
                params={
                    "id": "Order",
                    "fields": [
                        {"name": "order_id", "type": "string"},
                        {"name": "total", "type": "decimal"},
                    ],
                    "primary_key": "order_id",
                },
            )
        )

        # Add command
        tree.add_node(
            ProjectionNode(
                id="CreateOrder",
                kind=NodeKind.COMMAND,
                params={
                    "id": "CreateOrder",
                    "input": [{"name": "product_id", "type": "string"}],
                    "category": "create",
                    "writes_to": ["Order"],
                },
            )
        )

        # Validate
        report = validate_tree(tree)

        self.assertIsNotNone(report)
        self.assertIsNotNone(report.to_dict())

    def test_validation_with_cycle_detection(self):
        """Test validation with dependency cycle detection."""
        # This test creates a tree that would have cycles if dependencies were set up
        tree = ProjectionTree()

        tree.add_node(
            ProjectionNode(
                id="Entity1",
                kind=NodeKind.ENTITY,
                params={"id": "Entity1", "fields": []},
            )
        )
        tree.add_node(
            ProjectionNode(
                id="Entity2",
                kind=NodeKind.ENTITY,
                params={"id": "Entity2", "fields": []},
            )
        )

        report = validate_tree(tree)
        self.assertIsNotNone(report)

        # Check dependency analysis
        if report.dependency_analysis:
            self.assertIsInstance(report.dependency_analysis.has_cycles, bool)


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])