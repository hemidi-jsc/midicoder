# coding: utf-8
"""
Test cases cho CP23 recipes.

Kiểm tra:
- generate_entity_unit_tests
- generate_command_unit_tests
- generate_query_unit_tests
- generate_api_integration_tests
- generate_e2e_flow_tests
- auto_generate_tests_from_mir
"""

import pytest

from midicoder.emitters.core.cp23_testing_framework.recipes import (
    auto_generate_tests_from_mir,
    generate_api_integration_tests,
    generate_command_unit_tests,
    generate_e2e_flow_tests,
    generate_entity_unit_tests,
    generate_query_unit_tests,
)
from midicoder.emitters.core.cp23_testing_framework.models import (
    TestCollection,
    TestFramework,
    TestSuite,
    TestType,
)


class TestGenerateEntityUnitTests:
    """Test generate_entity_unit_tests recipe."""

    def test_generates_suite_with_cases(self):
        """Kiểm tra generate suite có cases."""
        entity = {"id": "User", "fields": [{"name": "email"}, {"name": "name"}]}
        suite = generate_entity_unit_tests(entity)
        assert isinstance(suite, TestSuite)
        assert suite.test_type == TestType.UNIT
        assert len(suite.cases) >= 3  # create, validation, serialization

    def test_case_ids_contain_entity_id(self):
        """Kiểm tra case IDs chứa entity ID."""
        entity = {"id": "Product"}
        suite = generate_entity_unit_tests(entity)
        for case in suite.cases:
            assert "product" in case.id.lower()
            assert case.target == "Product"

    def test_tags_include_entity(self):
        """Kiểm tra tags có chứa 'entity'."""
        entity = {"id": "Order"}
        suite = generate_entity_unit_tests(entity)
        for case in suite.cases:
            assert "entity" in case.tags


class TestGenerateCommandUnitTests:
    """Test generate_command_unit_tests recipe."""

    def test_generates_command_tests(self):
        """Kiểm tra generate command unit tests."""
        command = {"id": "CreateOrder"}
        suite = generate_command_unit_tests(command)
        assert isinstance(suite, TestSuite)
        assert suite.test_type == TestType.UNIT
        assert len(suite.cases) >= 2  # execute, validation

    def test_case_has_command_tag(self):
        """Kiểm tra case có tag 'command'."""
        command = {"id": "DeleteUser"}
        suite = generate_command_unit_tests(command)
        for case in suite.cases:
            assert "command" in case.tags


class TestGenerateQueryUnitTests:
    """Test generate_query_unit_tests recipe."""

    def test_generates_query_tests(self):
        """Kiểm tra generate query unit tests."""
        query = {"id": "ListProducts"}
        suite = generate_query_unit_tests(query)
        assert isinstance(suite, TestSuite)
        assert suite.test_type == TestType.UNIT
        assert len(suite.cases) >= 2  # returns_results, pagination

    def test_case_has_query_tag(self):
        """Kiểm tra case có tag 'query'."""
        query = {"id": "GetUser"}
        suite = generate_query_unit_tests(query)
        for case in suite.cases:
            assert "query" in case.tags


class TestGenerateApiIntegrationTests:
    """Test generate_api_integration_tests recipe."""

    def test_generates_crud_tests(self):
        """Kiểm tra generate CRUD integration tests."""
        entity = {"id": "User"}
        suite = generate_api_integration_tests(entity)
        assert suite.test_type == TestType.INTEGRATION
        # CRUD: list, create, get_by_id, update, delete
        assert len(suite.cases) == 5

    def test_has_correct_tags(self):
        """Kiểm tra tags đúng."""
        entity = {"id": "Product"}
        suite = generate_api_integration_tests(entity)
        for case in suite.cases:
            assert "integration" in case.tags
            assert "api" in case.tags
            assert "crud" in case.tags


class TestGenerateE2EFlowTests:
    """Test generate_e2e_flow_tests recipe."""

    def test_generates_e2e_flow(self):
        """Kiểm tra generate E2E flow."""
        entities = [{"id": "User"}]
        commands = [{"id": "CreateUser"}]
        suite = generate_e2e_flow_tests(entities, commands)
        assert suite.test_type == TestType.E2E
        assert len(suite.cases) >= 1

    def test_e2e_has_steps(self):
        """Kiểm tra E2E case có steps."""
        entities = [{"id": "Product"}]
        suite = generate_e2e_flow_tests(entities, [])
        for case in suite.cases:
            assert len(case.steps) > 0

    def test_empty_entities_returns_empty_suite(self):
        """Kiểm tra entities rỗng trả về suite rỗng."""
        suite = generate_e2e_flow_tests([], [])
        assert len(suite.cases) == 0


class TestAutoGenerateTestsFromMir:
    """Test auto_generate_tests_from_mir recipe (master)."""

    def test_generates_full_collection(self):
        """Kiểm tra generate full collection từ MIR."""
        entities = [{"id": "User", "fields": [{"name": "email"}]}]
        commands = [{"id": "CreateUser"}]
        queries = [{"id": "ListUsers"}]

        collection = auto_generate_tests_from_mir(entities, commands, queries)

        assert isinstance(collection, TestCollection)
        assert collection.global_policy is not None
        assert collection.global_policy.coverage_threshold == 80

    def test_has_all_test_types(self):
        """Kiểm tra có đầy đủ unit, integration, e2e."""
        entities = [{"id": "Product"}]
        collection = auto_generate_tests_from_mir(entities)
        counts = collection.count_cases()
        assert counts["unit"] > 0
        assert counts["integration"] > 0
        assert counts["e2e"] > 0

    def test_multiple_entities(self):
        """Kiểm tra multiple entities."""
        entities = [
            {"id": "User", "fields": []},
            {"id": "Order", "fields": []},
            {"id": "Product", "fields": []},
        ]
        collection = auto_generate_tests_from_mir(entities)
        # 3 entities × (3 unit + 5 integration) + 1 e2e
        total = collection.count_cases()
        assert total["unit"] >= 3 * 3  # 3 entities × 3 unit tests
        assert total["integration"] >= 3 * 5  # 3 entities × 5 CRUD tests

    def test_with_custom_framework(self):
        """Kiểm tra custom framework."""
        entities = [{"id": "User", "fields": []}]
        collection = auto_generate_tests_from_mir(entities, framework=TestFramework.JEST)
        for suite in collection.suites:
            assert suite.framework == TestFramework.JEST

    def test_with_custom_coverage_threshold(self):
        """Kiểm tra custom coverage threshold."""
        collection = auto_generate_tests_from_mir([], coverage_threshold=95)
        assert collection.global_policy.coverage_threshold == 95

    def test_empty_input(self):
        """Kiểm tra input rỗng."""
        collection = auto_generate_tests_from_mir([])
        assert collection.global_policy is not None
        # Có e2e suite nhưng rỗng
        e2e_suites = collection.get_suites_by_type(TestType.E2E)
        assert len(e2e_suites) >= 1
