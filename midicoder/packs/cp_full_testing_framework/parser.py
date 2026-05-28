# coding: utf-8
"""
Mô-đun parser cho Testing Framework Generator (CP23).

Parse DSL test nodes từ MIR metadata / Contract YAML thành TestCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_full_testing_framework.models import (
    AssertionCheck,
    TestCase,
    TestCollection,
    TestFramework,
    TestPolicy,
    TestStep,
    TestSuite,
    TestType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# Mapping từ stack name sang test framework
STACK_TO_FRAMEWORK: dict[str, TestFramework] = {
    "fastapi": TestFramework.PYTEST,
    "nestjs": TestFramework.JEST,
    "angular": TestFramework.KARMA,
    "react": TestFramework.JEST,
}


class TestParser:
    """
    Parser cho DSL test nodes.

    Parse YAML DSL hoặc dict metadata thành TestCollection.

    Ví dụ DSL:
        tests:
          - id: test_user_create
            type: unit
            target: User
            scenario: create_valid_user
            assertions:
              - check: status_code
                expected: 201
    """

    def parse(self, raw: str | dict[str, Any]) -> TestCollection:
        """
        Parse YAML string hoặc dict thành TestCollection.

        Args:
            raw: YAML string hoặc dict chứa test definitions

        Returns:
            TestCollection chứa suites và test cases

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return TestCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.MDC-F05_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML test nodes: {e}",
                    error=str(e)
                )
            if data is None:
                return TestCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return TestCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-F05_DSL_PARSE_ERROR,
                message="DSL test nodes phải là YAML mapping"
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any]) -> TestCollection:
        """
        Parse từ MIR metadata dict.

        MIR metadata có thể chứa key 'tests' hoặc 'test_suites'.

        Args:
            metadata: MIR metadata dict

        Returns:
            TestCollection
        """
        tests_data = metadata.get("tests", metadata.get("test_suites", []))
        if not tests_data:
            return TestCollection()

        global_policy_data = metadata.get("test_policy")
        collection = TestCollection()
        if global_policy_data and isinstance(global_policy_data, dict):
            collection.global_policy = self._parse_policy(global_policy_data)

        # Nếu là list raw test cases — wrap vào suite tự động
        if isinstance(tests_data, list) and tests_data and isinstance(tests_data[0], dict):
            first = tests_data[0]
            if "id" in first and "type" in first:
                # Raw list of test cases — group by type
                suites = self._group_cases_into_suites(tests_data)
                for suite in suites:
                    collection.add_suite(suite)
                return collection

        # Nếu là dict với key là suite names
        if isinstance(tests_data, dict):
            for suite_name, suite_data in tests_data.items():
                if isinstance(suite_data, dict):
                    suite = self._parse_suite(suite_data, suite_name)
                    collection.add_suite(suite)
                elif isinstance(suite_data, list):
                    suite = TestSuite(
                        name=suite_name,
                        framework=TestFramework.PYTEST,
                        test_type=TestType.UNIT,
                    )
                    for case_data in suite_data:
                        case = self._parse_case(case_data)
                        suite.add_case(case)
                    collection.add_suite(suite)

        return collection

    def _parse_test_type(self, value: str) -> TestType:
        """Parse string thành TestType enum."""
        try:
            return TestType(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_TEST_TYPE,
                test_type=value,
                valid=[t.value for t in TestType]
            )

    def _group_cases_into_suites(self, cases_data: list[dict[str, Any]]) -> list[TestSuite]:
        """Group raw test cases vào suites theo type."""
        grouped: dict[tuple[TestType, TestFramework], list[dict[str, Any]]] = {}

        for case_data in cases_data:
            test_type = self._parse_test_type(case_data.get("type", "unit"))
            framework_str = case_data.get("framework", "pytest")
            try:
                framework = TestFramework(framework_str)
            except ValueError:
                framework = TestFramework.PYTEST

            key = (test_type, framework)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(case_data)

        suites: list[TestSuite] = []
        for (test_type, framework), case_list in grouped.items():
            suite = TestSuite(
                name=f"{test_type.value}_tests",
                framework=framework,
                test_type=test_type,
            )
            for case_data in case_list:
                case = self._parse_case(case_data)
                suite.add_case(case)
            suites.append(suite)

        return suites

    def _parse_from_dict(self, data: dict[str, Any]) -> TestCollection:
        """Parse từ dict đã load."""
        collection = TestCollection()

        # Parse global policy
        policy_data = data.get("test_policy", data.get("policy"))
        if policy_data and isinstance(policy_data, dict):
            collection.global_policy = self._parse_policy(policy_data)

        # Parse test suites
        suites_data = data.get("test_suites", data.get("suites", []))
        if isinstance(suites_data, list):
            for suite_data in suites_data:
                if isinstance(suite_data, dict):
                    suite = self._parse_suite(suite_data)
                    collection.add_suite(suite)

        # Parse raw tests (flat list)
        tests_data = data.get("tests", [])
        if isinstance(tests_data, list) and tests_data:
            first = tests_data[0]
            if isinstance(first, dict) and "id" in first:
                suites = self._group_cases_into_suites(tests_data)
                for suite in suites:
                    collection.add_suite(suite)
            elif isinstance(first, dict) and "name" in first:
                # Suite definitions
                for suite_data in tests_data:
                    suite = self._parse_suite(suite_data)
                    collection.add_suite(suite)

        return collection

    def _parse_suite(self, data: dict[str, Any], default_name: str = "") -> TestSuite:
        """Parse suite definition."""
        name = data.get("name", default_name or "test_suite")
        framework_str = data.get("framework", "pytest")
        test_type_str = data.get("test_type", data.get("type", "unit"))

        try:
            framework = TestFramework(framework_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_FRAMEWORK,
                framework=framework_str,
                valid=[f.value for f in TestFramework]
            )

        try:
            test_type = TestType(test_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_TEST_TYPE,
                test_type=test_type_str,
                valid=[t.value for t in TestType]
            )

        suite = TestSuite(
            name=name,
            framework=framework,
            test_type=test_type,
            setup=data.get("setup", {}),
        )

        # Parse suite-level policy
        if data.get("policy"):
            suite.policy = self._parse_policy(data["policy"])

        # Parse test cases
        cases_data = data.get("cases", data.get("test_cases", data.get("tests", [])))
        for case_data in cases_data:
            if isinstance(case_data, dict):
                case = self._parse_case(case_data)
                suite.add_case(case)

        return suite

    def _parse_case(self, data: dict[str, Any]) -> TestCase:
        """Parse test case definition."""
        test_type_str = data.get("type", "unit")
        try:
            test_type = TestType(test_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_TEST_TYPE,
                test_type=test_type_str,
                valid=[t.value for t in TestType]
            )

        return TestCase(
            id=data.get("id", ""),
            type=test_type,
            target=data.get("target", ""),
            scenario=data.get("scenario", data.get("name", "")),
            description=data.get("description", ""),
            setup=data.get("setup", {}),
            steps=[
                TestStep(action=s["action"], params=s.get("params", {}))
                for s in data.get("steps", [])
                if isinstance(s, dict)
            ],
            assertions=[
                self._parse_assertion(a)
                for a in data.get("assertions", [])
                if isinstance(a, dict)
            ],
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
        )

    def _parse_assertion(self, data: dict[str, Any]) -> "TestAssertion":
        """Parse assertion definition."""
        from midicoder.packs.cp_full_testing_framework.models import TestAssertion

        check_str = data.get("check", "equal")
        try:
            check = AssertionCheck(check_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_ASSERTION,
                check=check_str,
                valid=[c.value for c in AssertionCheck]
            )

        return TestAssertion(
            check=check,
            expected=data.get("expected"),
            actual_path=data.get("actual_path", ""),
            message=data.get("message", ""),
        )

    def _parse_policy(self, data: dict[str, Any]) -> TestPolicy:
        """Parse test policy definition."""
        return TestPolicy(
            coverage_threshold=data.get("coverage_threshold", 80),
            coverage_branch=data.get("coverage_branch", 0),
            retry_count=data.get("retry_count", 0),
            parallel=data.get("parallel", False),
            parallel_workers=data.get("parallel_workers", 4),
            timeout_seconds=data.get("timeout_seconds", 30),
            random_seed=data.get("random_seed"),
        )
