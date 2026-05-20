# coding: utf-8
"""
Test cases cho CP23 TestParser.

Kiểm tra:
- Parse YAML string thành TestCollection
- Parse dict metadata
- Parse từ MIR metadata
- Error handling: invalid YAML, invalid types
- Edge cases: empty input, nested structures
"""

import pytest

from midicoder.emitters.core.cp23_testing_framework.parser import TestParser, STACK_TO_FRAMEWORK
from midicoder.emitters.core.cp23_testing_framework.models import (
    AssertionCheck,
    TestCollection,
    TestFramework,
    TestPolicy,
    TestSuite,
    TestType,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestStackToFramework:
    """Test mapping stack → framework."""

    def test_fastapi_maps_to_pytest(self):
        assert STACK_TO_FRAMEWORK["fastapi"] == TestFramework.PYTEST

    def test_nestjs_maps_to_jest(self):
        assert STACK_TO_FRAMEWORK["nestjs"] == TestFramework.JEST

    def test_angular_maps_to_karma(self):
        assert STACK_TO_FRAMEWORK["angular"] == TestFramework.KARMA

    def test_react_maps_to_jest(self):
        assert STACK_TO_FRAMEWORK["react"] == TestFramework.JEST


class TestTestParser:
    """Test TestParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = TestParser()

    def test_parse_empty_string(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, TestCollection)
        assert len(result.suites) == 0

    def test_parse_whitespace_only(self):
        """Kiểm tra parse whitespace trả về collection rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert len(result.suites) == 0

    def test_parse_invalid_yaml(self):
        """Kiểm tra parse YAML không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("invalid: [yaml: }")
        assert exc_info.value.code == ErrorCode.CP23_DSL_PARSE_ERROR

    def test_parse_non_dict_yaml(self):
        """Kiểm tra parse YAML list throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("- item1\n- item2")
        assert exc_info.value.code == ErrorCode.CP23_DSL_PARSE_ERROR

    def test_parse_dict(self):
        """Kiểm tra parse dict trực tiếp."""
        data = {
            "tests": [
                {
                    "id": "test_1",
                    "type": "unit",
                    "target": "User",
                    "scenario": "create",
                    "assertions": [{"check": "status_code", "expected": 201}],
                }
            ]
        }
        result = self.parser.parse(data)
        assert len(result.suites) >= 1
        all_cases = result.get_all_cases()
        assert len(all_cases) >= 1
        assert all_cases[0].id == "test_1"

    def test_parse_raw_tests_flat_list(self):
        """Kiểm tra parse flat list tests."""
        yaml_str = """
tests:
  - id: test_user_create
    type: unit
    target: User
    scenario: create_valid_user
    assertions:
      - check: status_code
        expected: 201
  - id: test_order_create
    type: integration
    target: Order
    scenario: order_flow
    assertions:
      - check: equal
        expected: true
"""
        result = self.parser.parse(yaml_str)
        assert len(result.suites) >= 2  # unit + integration suites
        # Verify unit suite
        unit_suites = result.get_suites_by_type(TestType.UNIT)
        assert len(unit_suites) >= 1
        assert len(unit_suites[0].cases) >= 1

    def test_parse_with_test_suites(self):
        """Kiểm tra parse test_suites format."""
        yaml_str = """
test_suites:
  - name: user_unit_tests
    framework: pytest
    test_type: unit
    cases:
      - id: test_user_create
        type: unit
        target: User
        scenario: create
        assertions:
          - check: status_code
            expected: 201
"""
        result = self.parser.parse(yaml_str)
        assert len(result.suites) == 1
        assert result.suites[0].name == "user_unit_tests"
        assert result.suites[0].framework == TestFramework.PYTEST
        assert len(result.suites[0].cases) == 1

    def test_parse_with_global_policy(self):
        """Kiểm tra parse global policy."""
        yaml_str = """
test_policy:
  coverage_threshold: 90
  retry_count: 2
  parallel: true
tests:
  - id: test_1
    type: unit
    target: User
    scenario: test
    assertions:
      - check: equal
        expected: 1
"""
        result = self.parser.parse(yaml_str)
        assert result.global_policy is not None
        assert result.global_policy.coverage_threshold == 90
        assert result.global_policy.retry_count == 2
        assert result.global_policy.parallel is True

    def test_parse_e2e_with_steps(self):
        """Kiểm tra parse E2E test có steps."""
        yaml_str = """
tests:
  - id: test_e2e_flow
    type: e2e
    target: Product
    scenario: full_checkout
    steps:
      - action: navigate
        params:
          url: /products
      - action: click
        params:
          selector: .add-to-cart
      - action: assert
        params:
          selector: .checkout-success
    assertions:
      - check: selector_exists
        expected: true
        actual_path: .checkout-success
"""
        result = self.parser.parse(yaml_str)
        e2e_cases = result.get_cases_by_type(TestType.E2E)
        assert len(e2e_cases) >= 1
        case = e2e_cases[0]
        assert len(case.steps) == 3
        assert case.steps[0].action == "navigate"
        assert case.steps[0].params["url"] == "/products"

    def test_parse_invalid_test_type(self):
        """Kiểm tra parse test type không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({"tests": [{"id": "t1", "type": "invalid_type", "target": "User", "scenario": "s"}]})
        assert exc_info.value.code == ErrorCode.CP23_INVALID_TEST_TYPE

    def test_parse_invalid_framework(self):
        """Kiểm tra parse framework không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({
                "test_suites": [{
                    "name": "test", "framework": "invalid_fw", "test_type": "unit",
                }]
            })
        assert exc_info.value.code == ErrorCode.CP23_INVALID_FRAMEWORK

    def test_parse_invalid_assertion_check(self):
        """Kiểm tra parse assertion check không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse({"tests": [
                {"id": "t1", "type": "unit", "target": "User", "scenario": "s",
                 "assertions": [{"check": "invalid_check", "expected": 1}]}
            ]})
        assert exc_info.value.code == ErrorCode.CP23_INVALID_ASSERTION

    def test_parse_with_tags(self):
        """Kiểm tra parse test case có tags."""
        yaml_str = """
tests:
  - id: test_1
    type: unit
    target: User
    scenario: test
    tags: [unit, user, create]
    assertions:
      - check: equal
        expected: 1
"""
        result = self.parser.parse(yaml_str)
        cases = result.get_all_cases()
        assert len(cases) >= 1
        assert "unit" in cases[0].tags

    def test_parse_from_metadata(self):
        """Kiểm tra parse từ MIR metadata."""
        metadata = {
            "tests": [
                {"id": "t1", "type": "unit", "target": "User", "scenario": "s",
                 "assertions": [{"check": "equal", "expected": 1}]}
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.suites) >= 1

    def test_parse_from_metadata_empty(self):
        """Kiểm tra parse metadata rỗng."""
        result = self.parser.parse_from_metadata({})
        assert len(result.suites) == 0

    def test_parse_from_metadata_with_test_suites_key(self):
        """Kiểm tra parse metadata có key test_suites."""
        metadata = {
            "test_suites": {
                "user_tests": {
                    "name": "user_tests",
                    "framework": "pytest",
                    "test_type": "unit",
                    "cases": [
                        {"id": "t1", "type": "unit", "target": "User", "scenario": "s",
                         "assertions": [{"check": "equal", "expected": 1}]}
                    ],
                }
            }
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.suites) == 1

    def test_parse_disabled_case(self):
        """Kiểm tra parse disabled test case."""
        yaml_str = """
tests:
  - id: test_1
    type: unit
    target: User
    scenario: test
    enabled: false
    assertions:
      - check: equal
        expected: 1
"""
        result = self.parser.parse(yaml_str)
        cases = result.get_all_cases()
        assert len(cases) >= 1
        assert cases[0].enabled is False

    def test_parse_all_assertion_types(self):
        """Kiểm tra parse tất cả loại assertion."""
        yaml_str = """
tests:
  - id: test_1
    type: unit
    target: User
    scenario: all_assertions
    assertions:
      - check: status_code
        expected: 200
      - check: entity_exists
        expected: User
      - check: equal
        expected: true
      - check: contains
        expected: hello
      - check: length
        expected: 10
      - check: truthy
        expected: true
      - check: falsy
        expected: false
"""
        result = self.parser.parse(yaml_str)
        cases = result.get_all_cases()
        assert len(cases) >= 1
        assert len(cases[0].assertions) == 7
