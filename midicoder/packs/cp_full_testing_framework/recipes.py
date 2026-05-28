# coding: utf-8
"""
Recipe module cho CP23 Testing Framework Generator.

Recipes cung cấp auto-generate test cases từ MIR metadata
(entities, commands, queries) khi không có DSL test nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp_full_testing_framework.models import (
    AssertionCheck,
    TestCase,
    TestCollection,
    TestFramework,
    TestPolicy,
    TestStep,
    TestSuite,
    TestType,
    TestAssertion,
)


# ===========================================================================
# Auto-generate unit tests từ entity metadata
# ===========================================================================


def generate_entity_unit_tests(
    entity: dict,
    all_entities: list[dict] | None = None,
    framework: TestFramework = TestFramework.PYTEST,
) -> TestSuite:
    """
    Auto-generate unit tests cho entity model.

    Sinh ra:
    - Test tạo instance hợp lệ
    - Test validation với dữ liệu không hợp lệ
    - Test serialization (to_dict/from_dict)
    - Test relationship (nếu có)

    Args:
        entity: Entity dict từ MIR metadata
        all_entities: Tất cả entities (cho relationship resolution)
        framework: Test framework (pytest/jest/karma)

    Returns:
        TestSuite chứa unit tests cho entity
    """
    entity_id = entity.get("id", "unknown")
    suite = TestSuite(
        name=f"{entity_id}_unit_tests",
        framework=framework,
        test_type=TestType.UNIT,
    )

    # Test: tạo instance hợp lệ
    suite.add_case(TestCase(
        id=f"test_{entity_id.lower()}_create_valid",
        type=TestType.UNIT,
        target=entity_id,
        scenario="tạo instance hợp lệ",
        description=f"Kiểm tra tạo {entity_id} với dữ liệu hợp lệ",
        setup={"entity": entity},
        assertions=[
            TestAssertion(
                check=AssertionCheck.TRUTHY,
                expected=True,
                actual_path="instance",
                message=f"{entity_id} phải được tạo thành công",
            ),
        ],
        tags=["unit", "entity", "create"],
    ))

    # Test: validation với dữ liệu rỗng
    suite.add_case(TestCase(
        id=f"test_{entity_id.lower()}_validation_empty",
        type=TestType.UNIT,
        target=entity_id,
        scenario="validation với dữ liệu rỗng",
        description=f"Kiểm tra validation {entity_id} khi dữ liệu rỗng",
        assertions=[
            TestAssertion(
                check=AssertionCheck.TYPE,
                expected="ValidationError",
                actual_path="error_type",
                message=f"{entity_id} phải throw validation error",
            ),
        ],
        tags=["unit", "entity", "validation"],
    ))

    # Test: serialization
    suite.add_case(TestCase(
        id=f"test_{entity_id.lower()}_serialization",
        type=TestType.UNIT,
        target=entity_id,
        scenario="serialization roundtrip",
        description=f"Kiểm tra to_dict/from_dict cho {entity_id}",
        setup={"entity": entity},
        assertions=[
            TestAssertion(
                check=AssertionCheck.EQUAL,
                expected=True,
                actual_path="roundtrip_equal",
                message="Serialization roundtrip phải giữ nguyên data",
            ),
        ],
        tags=["unit", "entity", "serialization"],
    ))

    return suite


def generate_command_unit_tests(
    command: dict,
    framework: TestFramework = TestFramework.PYTEST,
) -> TestSuite:
    """
    Auto-generate unit tests cho command handler.

    Sinh ra:
    - Test execute với input hợp lệ
    - Test validation với input không hợp lệ
    - Test guard failure
    - Test effect application

    Args:
        command: Command dict từ MIR metadata
        framework: Test framework

    Returns:
        TestSuite chứa unit tests cho command
    """
    cmd_id = command.get("id", "unknown")
    suite = TestSuite(
        name=f"{cmd_id}_unit_tests",
        framework=framework,
        test_type=TestType.UNIT,
    )

    # Test: execute hợp lệ
    suite.add_case(TestCase(
        id=f"test_{cmd_id.lower()}_execute_valid",
        type=TestType.UNIT,
        target=cmd_id,
        scenario="execute với input hợp lệ",
        description=f"Kiểm tra execute {cmd_id} với input hợp lệ",
        setup={"command": command},
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=200,
                actual_path="response.status",
                message=f"{cmd_id} phải trả về 200",
            ),
        ],
        tags=["unit", "command", "execute"],
    ))

    # Test: validation fail
    suite.add_case(TestCase(
        id=f"test_{cmd_id.lower()}_validation_fail",
        type=TestType.UNIT,
        target=cmd_id,
        scenario="validation với input không hợp lệ",
        description=f"Kiểm tra validation {cmd_id} khi input sai",
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=400,
                actual_path="response.status",
                message=f"{cmd_id} phải trả về 400 cho input không hợp lệ",
            ),
        ],
        tags=["unit", "command", "validation"],
    ))

    return suite


def generate_query_unit_tests(
    query: dict,
    framework: TestFramework = TestFramework.PYTEST,
) -> TestSuite:
    """
    Auto-generate unit tests cho query handler.

    Args:
        query: Query dict từ MIR metadata
        framework: Test framework

    Returns:
        TestSuite chứa unit tests cho query
    """
    query_id = query.get("id", "unknown")
    suite = TestSuite(
        name=f"{query_id}_unit_tests",
        framework=framework,
        test_type=TestType.UNIT,
    )

    # Test: query trả về kết quả
    suite.add_case(TestCase(
        id=f"test_{query_id.lower()}_returns_results",
        type=TestType.UNIT,
        target=query_id,
        scenario="query trả về kết quả hợp lệ",
        description=f"Kiểm tra {query_id} trả về kết quả đúng",
        setup={"query": query},
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=200,
                actual_path="response.status",
            ),
            TestAssertion(
                check=AssertionCheck.TRUTHY,
                expected=True,
                actual_path="response.data",
            ),
        ],
        tags=["unit", "query"],
    ))

    # Test: pagination
    suite.add_case(TestCase(
        id=f"test_{query_id.lower()}_pagination",
        type=TestType.UNIT,
        target=query_id,
        scenario="pagination hoạt động đúng",
        description=f"Kiểm tra pagination {query_id}",
        assertions=[
            TestAssertion(
                check=AssertionCheck.LENGTH,
                expected=10,
                actual_path="response.data.items",
            ),
        ],
        tags=["unit", "query", "pagination"],
    ))

    return suite


# ===========================================================================
# Auto-generate integration tests
# ===========================================================================


def generate_api_integration_tests(
    entity: dict,
    framework: TestFramework = TestFramework.PYTEST,
) -> TestSuite:
    """
    Auto-generate integration tests cho API endpoints.

    Sinh ra:
    - Test GET /{entity}
    - Test POST /{entity}
    - Test PUT /{entity}/{id}
    - Test DELETE /{entity}/{id}

    Args:
        entity: Entity dict
        framework: Test framework

    Returns:
        TestSuite chứa integration tests
    """
    entity_id = entity.get("id", "unknown")
    entity_lower = entity_id.lower()
    suite = TestSuite(
        name=f"{entity_id}_integration_tests",
        framework=framework,
        test_type=TestType.INTEGRATION,
    )

    # Test: GET list
    suite.add_case(TestCase(
        id=f"test_{entity_lower}_list",
        type=TestType.INTEGRATION,
        target=entity_id,
        scenario="GET list entities",
        setup={"entity": entity},
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=200,
                actual_path="response.status",
            ),
        ],
        tags=["integration", "api", "crud", "read"],
    ))

    # Test: POST create
    suite.add_case(TestCase(
        id=f"test_{entity_lower}_create",
        type=TestType.INTEGRATION,
        target=entity_id,
        scenario="POST create entity",
        setup={"entity": entity},
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=201,
                actual_path="response.status",
            ),
            TestAssertion(
                check=AssertionCheck.ENTITY_EXISTS,
                expected=entity_id,
                actual_path="created_entity",
            ),
        ],
        tags=["integration", "api", "crud", "create"],
    ))

    # Test: GET by ID
    suite.add_case(TestCase(
        id=f"test_{entity_lower}_get_by_id",
        type=TestType.INTEGRATION,
        target=entity_id,
        scenario="GET entity by ID",
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=200,
                actual_path="response.status",
            ),
        ],
        tags=["integration", "api", "crud", "read"],
    ))

    # Test: PUT update
    suite.add_case(TestCase(
        id=f"test_{entity_lower}_update",
        type=TestType.INTEGRATION,
        target=entity_id,
        scenario="PUT update entity",
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=200,
                actual_path="response.status",
            ),
        ],
        tags=["integration", "api", "crud", "update"],
    ))

    # Test: DELETE
    suite.add_case(TestCase(
        id=f"test_{entity_lower}_delete",
        type=TestType.INTEGRATION,
        target=entity_id,
        scenario="DELETE entity",
        assertions=[
            TestAssertion(
                check=AssertionCheck.STATUS_CODE,
                expected=204,
                actual_path="response.status",
            ),
            TestAssertion(
                check=AssertionCheck.ENTITY_NOT_EXISTS,
                expected=entity_id,
                actual_path="deleted_entity",
            ),
        ],
        tags=["integration", "api", "crud", "delete"],
    ))

    return suite


# ===========================================================================
# Auto-generate E2E tests
# ===========================================================================


def generate_e2e_flow_tests(
    entities: list[dict],
    commands: list[dict],
    framework: TestFramework = TestFramework.PYTEST,
) -> TestSuite:
    """
    Auto-generate E2E test flows từ entities + commands.

    Sinh ra flow: browse → create → verify → update → delete

    Args:
        entities: List entity dicts
        commands: List command dicts
        framework: Test framework

    Returns:
        TestSuite chứa E2E test flows
    """
    suite = TestSuite(
        name="e2e_flow_tests",
        framework=framework,
        test_type=TestType.E2E,
    )

    if not entities:
        return suite

    primary_entity = entities[0]
    entity_id = primary_entity.get("id", "unknown")
    entity_lower = entity_id.lower()

    # E2E flow: full CRUD
    suite.add_case(TestCase(
        id=f"test_e2e_{entity_lower}_crud_flow",
        type=TestType.E2E,
        target=entity_id,
        scenario="full CRUD flow",
        description=f"E2E flow: navigate → create → verify → update → delete cho {entity_id}",
        steps=[
            TestStep(action="navigate", params={"url": f"/{entity_lower}s"}),
            TestStep(action="click", params={"selector": f".{entity_lower}-create-btn"}),
            TestStep(action="fill", params={"selector": f".{entity_lower}-name-input", "text": f"Test {entity_id}"}),
            TestStep(action="click", params={"selector": ".submit-btn"}),
            TestStep(action="assert", params={"selector": f".{entity_lower}-created"}),
            TestStep(action="click", params={"selector": f".{entity_lower}-edit-btn"}),
            TestStep(action="fill", params={"selector": f".{entity_lower}-name-input", "text": f"Updated {entity_id}"}),
            TestStep(action="click", params={"selector": ".submit-btn"}),
            TestStep(action="assert", params={"selector": f".{entity_lower}-updated"}),
            TestStep(action="click", params={"selector": f".{entity_lower}-delete-btn"}),
            TestStep(action="assert", params={"selector": ".delete-confirmed"}),
        ],
        assertions=[
            TestAssertion(
                check=AssertionCheck.SELECTOR_EXISTS,
                expected=True,
                actual_path=f".{entity_lower}-created",
            ),
        ],
        tags=["e2e", "crud", "flow"],
    ))

    return suite


# ===========================================================================
# Master recipe: auto-generate từ MIR metadata
# ===========================================================================


def auto_generate_tests_from_mir(
    entities: list[dict],
    commands: list[dict] | None = None,
    queries: list[dict] | None = None,
    framework: TestFramework = TestFramework.PYTEST,
    coverage_threshold: int = 80,
) -> TestCollection:
    """
    Auto-generate toàn bộ test collection từ MIR metadata.

    Đây là fallback khi không có DSL test nodes explicit.

    Args:
        entities: List entity dicts từ MIR metadata
        commands: List command dicts (optional)
        queries: List query dicts (optional)
        framework: Test framework
        coverage_threshold: Coverage threshold

    Returns:
        TestCollection chứa suites cho unit, integration, e2e
    """
    collection = TestCollection()
    collection.global_policy = TestPolicy(
        coverage_threshold=coverage_threshold,
    )

    # Unit tests cho entities
    for entity in entities:
        suite = generate_entity_unit_tests(entity, entities, framework)
        collection.add_suite(suite)

    # Unit tests cho commands
    if commands:
        for command in commands:
            suite = generate_command_unit_tests(command, framework)
            collection.add_suite(suite)

    # Unit tests cho queries
    if queries:
        for query in queries:
            suite = generate_query_unit_tests(query, framework)
            collection.add_suite(suite)

    # Integration tests
    for entity in entities:
        suite = generate_api_integration_tests(entity, framework)
        collection.add_suite(suite)

    # E2E flow tests
    e2e_suite = generate_e2e_flow_tests(entities, commands or [], framework)
    collection.add_suite(e2e_suite)

    return collection


__all__ = [
    "auto_generate_tests_from_mir",
    "generate_entity_unit_tests",
    "generate_command_unit_tests",
    "generate_query_unit_tests",
    "generate_api_integration_tests",
    "generate_e2e_flow_tests",
]
