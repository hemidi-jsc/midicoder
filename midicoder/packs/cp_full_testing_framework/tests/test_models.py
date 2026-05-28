# coding: utf-8
"""
Test cases cho CP23 Testing Framework models.

Kiểm tra:
- Enums: TestType, TestFramework, AssertionCheck
- TestAssertion: Validation
- TestStep: Default values
- TestCase: Validation (empty id, missing target, e2e steps)
- TestPolicy: Validation (coverage threshold)
- TestSuite: CRUD, filtering
- TestCollection: CRUD, counting, serialization
"""

import pytest

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
from midicoder.errors import ErrorCode, MidicoderError


class TestEnums:
    """Test các enum types."""

    def test_test_type_values(self):
        """Kiểm tra TestType enum values."""
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.E2E.value == "e2e"
        assert len(TestType) == 3

    def test_test_framework_values(self):
        """Kiểm tra TestFramework enum values."""
        assert TestFramework.PYTEST.value == "pytest"
        assert TestFramework.JEST.value == "jest"
        assert TestFramework.KARMA.value == "karma"
        assert len(TestFramework) == 3

    def test_assertion_check_values(self):
        """Kiểm tra AssertionCheck enum values."""
        assert AssertionCheck.STATUS_CODE.value == "status_code"
        assert AssertionCheck.ENTITY_EXISTS.value == "entity_exists"
        assert AssertionCheck.EQUAL.value == "equal"
        assert AssertionCheck.CONTAINS.value == "contains"
        assert AssertionCheck.SELECTOR_EXISTS.value == "selector_exists"
        assert len(AssertionCheck) == 14


class TestTestAssertion:
    """Test TestAssertion model."""

    def test_create_valid_assertion(self):
        """Kiểm tra tạo assertion hợp lệ."""
        assertion = TestAssertion(
            check=AssertionCheck.STATUS_CODE,
            expected=200,
            actual_path="response.status",
            message="Status phải là 200",
        )
        assert assertion.check == AssertionCheck.STATUS_CODE
        assert assertion.expected == 200
        assert assertion.actual_path == "response.status"
        assert assertion.message == "Status phải là 200"

    def test_default_values(self):
        """Kiểm tra default values."""
        assertion = TestAssertion(
            check=AssertionCheck.EQUAL,
            expected="test",
        )
        assert assertion.actual_path == ""
        assert assertion.message == ""


class TestTestStep:
    """Test TestStep model."""

    def test_create_step(self):
        """Kiểm tra tạo test step."""
        step = TestStep(
            action="navigate",
            params={"url": "/products"},
        )
        assert step.action == "navigate"
        assert step.params["url"] == "/products"

    def test_default_params(self):
        """Kiểm tra default params."""
        step = TestStep(action="click")
        assert step.params == {}


class TestTestCase:
    """Test TestCase model."""

    def test_create_valid_case(self):
        """Kiểm tra tạo test case hợp lệ."""
        case = TestCase(
            id="test_user_create",
            type=TestType.UNIT,
            target="User",
            scenario="create_valid_user",
            description="Test tạo user hợp lệ",
            setup={"name": "test"},
            assertions=[
                TestAssertion(check=AssertionCheck.STATUS_CODE, expected=201),
            ],
            tags=["unit", "user"],
        )
        assert case.id == "test_user_create"
        assert case.type == TestType.UNIT
        assert case.target == "User"
        assert case.enabled is True
        assert len(case.assertions) == 1

    def test_empty_id_raises_error(self):
        """Kiểm tra ID rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestCase(
                id="",
                type=TestType.UNIT,
                target="User",
                scenario="test",
            )
        assert exc_info.value.code == ErrorCode.MDC-F05_EMPTY_TEST_ID

    def test_missing_target_raises_error(self):
        """Kiểm tra target rỗng throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestCase(
                id="test_1",
                type=TestType.UNIT,
                target="",
                scenario="test",
            )
        assert exc_info.value.code == ErrorCode.MDC-F05_MISSING_TEST_TARGET

    def test_e2e_without_steps_raises_error(self):
        """Kiểm tra E2E test không có steps throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestCase(
                id="test_e2e_1",
                type=TestType.E2E,
                target="User",
                scenario="flow",
                steps=[],
            )
        assert exc_info.value.code == ErrorCode.MDC-F05_MISSING_TEST_TARGET

    def test_e2e_with_steps_valid(self):
        """Kiểm tra E2E test có steps hợp lệ."""
        case = TestCase(
            id="test_e2e_1",
            type=TestType.E2E,
            target="User",
            scenario="crud_flow",
            steps=[
                TestStep(action="navigate", params={"url": "/users"}),
            ],
        )
        assert len(case.steps) == 1
        assert case.steps[0].action == "navigate"


class TestTestPolicy:
    """Test TestPolicy model."""

    def test_create_valid_policy(self):
        """Kiểm tra tạo policy hợp lệ."""
        policy = TestPolicy(
            coverage_threshold=90,
            coverage_branch=80,
            retry_count=2,
            parallel=True,
            parallel_workers=8,
            timeout_seconds=60,
        )
        assert policy.coverage_threshold == 90
        assert policy.coverage_branch == 80
        assert policy.retry_count == 2
        assert policy.parallel is True
        assert policy.parallel_workers == 8
        assert policy.timeout_seconds == 60

    def test_default_values(self):
        """Kiểm tra default values."""
        policy = TestPolicy()
        assert policy.coverage_threshold == 80
        assert policy.coverage_branch == 0
        assert policy.retry_count == 0
        assert policy.parallel is False
        assert policy.parallel_workers == 4
        assert policy.timeout_seconds == 30

    def test_invalid_threshold_raises_error(self):
        """Kiểm tra coverage threshold > 100 throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestPolicy(coverage_threshold=150)
        assert exc_info.value.code == ErrorCode.MDC-F05_INVALID_COVERAGE_THRESHOLD

    def test_negative_threshold_raises_error(self):
        """Kiểm tra coverage threshold âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestPolicy(coverage_threshold=-10)
        assert exc_info.value.code == ErrorCode.MDC-F05_INVALID_COVERAGE_THRESHOLD

    def test_negative_branch_raises_error(self):
        """Kiểm tra coverage_branch âm throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            TestPolicy(coverage_branch=-10)
        assert exc_info.value.code == ErrorCode.MDC-F05_INVALID_COVERAGE_THRESHOLD

    def test_negative_retry_auto_fix(self):
        """Kiểm tra retry_count âm được auto fix."""
        policy = TestPolicy(retry_count=-5)
        assert policy.retry_count == 0

    def test_zero_workers_auto_fix(self):
        """Kiểm tra parallel_workers=0 được auto fix."""
        policy = TestPolicy(parallel_workers=0)
        assert policy.parallel_workers == 1


class TestTestSuite:
    """Test TestSuite model."""

    def test_create_suite(self):
        """Kiểm tra tạo test suite."""
        suite = TestSuite(
            name="user_tests",
            framework=TestFramework.PYTEST,
            test_type=TestType.UNIT,
        )
        assert suite.name == "user_tests"
        assert suite.framework == TestFramework.PYTEST
        assert suite.test_type == TestType.UNIT

    def test_add_case(self):
        """Kiểm tra thêm test case."""
        suite = TestSuite(name="test", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(
            id="test_1", type=TestType.UNIT, target="User",
            scenario="create", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        )
        suite.add_case(case)
        assert len(suite.cases) == 1
        assert suite.get_case_by_id("test_1") is case

    def test_duplicate_case_raises_error(self):
        """Kiểm tra case ID trùng throw error."""
        suite = TestSuite(name="test", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        case = TestCase(
            id="test_1", type=TestType.UNIT, target="User",
            scenario="create", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        )
        suite.add_case(case)
        dup = TestCase(
            id="test_1", type=TestType.UNIT, target="User",
            scenario="dup", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=2)],
        )
        with pytest.raises(MidicoderError) as exc_info:
            suite.add_case(dup)
        assert exc_info.value.code == ErrorCode.MDC-F05_DUPLICATE_TEST_ID

    def test_get_enabled_cases(self):
        """Kiểm tra lọc enabled cases."""
        suite = TestSuite(name="test", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="s1",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        ))
        suite.add_case(TestCase(
            id="t2", type=TestType.UNIT, target="User", scenario="s2",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=2)],
            enabled=False,
        ))
        assert len(suite.get_enabled_cases()) == 1

    def test_get_cases_by_target(self):
        """Kiểm tra lọc cases theo target."""
        suite = TestSuite(name="test", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="s1",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        ))
        suite.add_case(TestCase(
            id="t2", type=TestType.UNIT, target="Order", scenario="s2",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=2)],
        ))
        assert len(suite.get_cases_by_target("User")) == 1
        assert len(suite.get_cases_by_target("Order")) == 1
        assert len(suite.get_cases_by_target("Product")) == 0

    def test_to_dict(self):
        """Kiểm tra serialization."""
        suite = TestSuite(
            name="test_suite",
            framework=TestFramework.PYTEST,
            test_type=TestType.UNIT,
            policy=TestPolicy(coverage_threshold=90),
        )
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="s1",
            assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)],
        ))
        data = suite.to_dict()
        assert data["name"] == "test_suite"
        assert data["framework"] == "pytest"
        assert data["test_type"] == "unit"
        assert len(data["cases"]) == 1
        assert data["policy"]["coverage_threshold"] == 90


class TestTestCollection:
    """Test TestCollection model."""

    def test_create_empty(self):
        """Kiểm tra tạo collection rỗng."""
        coll = TestCollection()
        assert len(coll.suites) == 0
        assert coll.global_policy is None

    def test_add_suite(self):
        """Kiểm tra thêm suite."""
        coll = TestCollection()
        suite = TestSuite(name="s1", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        coll.add_suite(suite)
        assert len(coll.suites) == 1

    def test_get_suites_by_type(self):
        """Kiểm tra lọc suites theo type."""
        coll = TestCollection()
        coll.add_suite(TestSuite(name="unit", framework=TestFramework.PYTEST, test_type=TestType.UNIT))
        coll.add_suite(TestSuite(name="int", framework=TestFramework.PYTEST, test_type=TestType.INTEGRATION))
        assert len(coll.get_suites_by_type(TestType.UNIT)) == 1
        assert len(coll.get_suites_by_type(TestType.INTEGRATION)) == 1
        assert len(coll.get_suites_by_type(TestType.E2E)) == 0

    def test_get_suites_by_framework(self):
        """Kiểm tra lọc suites theo framework."""
        coll = TestCollection()
        coll.add_suite(TestSuite(name="p1", framework=TestFramework.PYTEST, test_type=TestType.UNIT))
        coll.add_suite(TestSuite(name="j1", framework=TestFramework.JEST, test_type=TestType.UNIT))
        assert len(coll.get_suites_by_framework(TestFramework.PYTEST)) == 1
        assert len(coll.get_suites_by_framework(TestFramework.JEST)) == 1

    def test_count_cases(self):
        """Kiểm tra đếm cases theo type."""
        coll = TestCollection()
        s1 = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        s1.add_case(TestCase(id="c1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)]))
        coll.add_suite(s1)
        s2 = TestSuite(name="e", framework=TestFramework.PYTEST, test_type=TestType.E2E)
        s2.add_case(TestCase(id="c2", type=TestType.E2E, target="User", scenario="flow", steps=[TestStep(action="navigate")], assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)]))
        coll.add_suite(s2)
        counts = coll.count_cases()
        assert counts["unit"] == 1
        assert counts["e2e"] == 1
        assert counts["integration"] == 0

    def test_get_all_cases(self):
        """Kiểm tra lấy tất cả cases."""
        coll = TestCollection()
        s = TestSuite(name="u", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        s.add_case(TestCase(id="c1", type=TestType.UNIT, target="User", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=1)]))
        s.add_case(TestCase(id="c2", type=TestType.UNIT, target="Order", scenario="s", assertions=[TestAssertion(check=AssertionCheck.EQUAL, expected=2)]))
        coll.add_suite(s)
        assert len(coll.get_all_cases()) == 2

    def test_to_dict_and_from_dict(self):
        """Kiểm tra serialization roundtrip."""
        coll = TestCollection()
        coll.global_policy = TestPolicy(coverage_threshold=85, retry_count=1)
        suite = TestSuite(name="user_unit", framework=TestFramework.PYTEST, test_type=TestType.UNIT)
        suite.add_case(TestCase(
            id="t1", type=TestType.UNIT, target="User", scenario="create",
            assertions=[TestAssertion(check=AssertionCheck.STATUS_CODE, expected=201, actual_path="status")],
            tags=["unit"],
        ))
        coll.add_suite(suite)

        data = coll.to_dict()
        restored = TestCollection.from_dict(data)

        assert len(restored.suites) == 1
        assert restored.global_policy is not None
        assert restored.global_policy.coverage_threshold == 85
        assert restored.global_policy.retry_count == 1
        assert len(restored.suites[0].cases) == 1
        assert restored.suites[0].cases[0].id == "t1"

    def test_from_dict_empty(self):
        """Kiểm tra from_dict từ dict rỗng."""
        coll = TestCollection.from_dict({})
        assert len(coll.suites) == 0
        assert coll.global_policy is None
