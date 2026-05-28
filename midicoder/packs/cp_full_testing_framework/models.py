# coding: utf-8
"""
Mô-đun models cho Testing Framework Generator (CP23).

Định nghĩa các dataclass biểu diễn:
- TestType: Enum các loại test (unit, integration, e2e)
- TestAssertion: Một assertion trong test case
- TestStep: Một bước thực thi (E2E)
- TestCase: Một test case đơn lẻ
- TestPolicy: Policy cho test suite (coverage threshold, retry, parallel)
- TestSuite: Collection của test cases

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class TestType(str, Enum):
    """Enum các loại test."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"

    __test__ = False  # Prevent pytest collection


class TestFramework(str, Enum):
    """Enum test frameworks cho từng stack."""
    PYTEST = "pytest"
    JEST = "jest"
    KARMA = "karma"

    __test__ = False  # Prevent pytest collection


class AssertionCheck(str, Enum):
    """Enum các loại assertion check."""
    STATUS_CODE = "status_code"
    ENTITY_EXISTS = "entity_exists"
    ENTITY_NOT_EXISTS = "entity_not_exists"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    CONTAINS = "contains"
    LENGTH = "length"
    TYPE = "type"
    TRUTHY = "truthy"
    FALSY = "falsy"
    REGEX_MATCH = "regex_match"
    JSON_PATH = "json_path"
    SELECTOR_EXISTS = "selector_exists"
    SELECTOR_TEXT = "selector_text"


# ===========================================================================
# TestAssertion
# ===========================================================================


@dataclass
class TestAssertion:
    """
    Một assertion trong test case — xác minh kết quả mong đợi.

    Attributes:
        check: Loại kiểm tra (status_code, equal, contains, ...)
        expected: Giá trị mong đợi
        actual_path: Đường dẫn đến giá trị thực (JSON path hoặc field name)
        message: Thông báo khi assertion fail (optional)
    """
    __test__ = False  # Prevent pytest collection

    check: AssertionCheck
    expected: Any
    actual_path: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        """Validate assertion sau khi khởi tạo."""
        if not self.check:
            EM.raise_error(ErrorCode.MDC-F05_INVALID_ASSERTION, field="check")


@dataclass
class TestStep:
    """
    Một bước thực thi trong E2E test.

    Attributes:
        action: Hành động (navigate, click, type, assert, wait, select)
        params: Tham số cho hành động (selector, url, text, ...)
    """
    __test__ = False  # Prevent pytest collection

    action: str
    params: dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# TestCase
# ===========================================================================


@dataclass
class TestCase:
    """
    Một test case đơn lẻ.

    Attributes:
        id: Định danh duy nhất của test case
        type: Loại test (unit, integration, e2e)
        target: Target entity/command/query ID
        scenario: Tên scenario (mô tả ngắn)
        description: Mô tả chi tiết (optional)
        setup: Dữ liệu setup (dict)
        steps: Danh sách bước thực thi (E2E only)
        assertions: Danh sách assertions
        enabled: Có kích hoạt test không (default True)
        tags: Danh sách tags để filter
    """
    __test__ = False  # Prevent pytest collection

    id: str
    type: TestType
    target: str
    scenario: str
    description: str = ""
    setup: dict[str, Any] = field(default_factory=dict)
    steps: list[TestStep] = field(default_factory=list)
    assertions: list[TestAssertion] = field(default_factory=list)
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate test case sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F05_EMPTY_TEST_ID, field="test_case.id")
        if not self.target or not self.target.strip():
            EM.raise_error(ErrorCode.MDC-F05_MISSING_TEST_TARGET, test_id=self.id)
        # E2E tests must have steps
        if self.type == TestType.E2E and not self.steps:
            EM.raise_error(
                ErrorCode.MDC-F05_MISSING_TEST_TARGET,
                test_id=self.id,
                reason="E2E test phải có ít nhất 1 step"
            )


# ===========================================================================
# TestPolicy
# ===========================================================================


@dataclass
class TestPolicy:
    """
    Policy cho test suite — cấu hình coverage threshold, retry, parallel.

    Attributes:
        coverage_threshold: Mức coverage tối thiểu (0-100, default 80)
        coverage_branch: Branch coverage threshold (0-100, default 0 = off)
        retry_count: Số lần retry cho test flaky (default 0)
        parallel: Chạy song song (default False)
        parallel_workers: Số worker khi parallel (default 4)
        timeout_seconds: Timeout cho mỗi test case (default 30s)
        random_seed: Seed cho random (optional, cho reproducibility)
    """
    coverage_threshold: int = 80
    coverage_branch: int = 0
    retry_count: int = 0
    parallel: bool = False
    parallel_workers: int = 4
    timeout_seconds: int = 30
    random_seed: Optional[int] = None

    __test__ = False  # Prevent pytest collection

    def __post_init__(self) -> None:
        """Validate test policy sau khi khởi tạo."""
        if not 0 <= self.coverage_threshold <= 100:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_COVERAGE_THRESHOLD,
                threshold=self.coverage_threshold
            )
        if not 0 <= self.coverage_branch <= 100:
            EM.raise_error(
                ErrorCode.MDC-F05_INVALID_COVERAGE_THRESHOLD,
                threshold=self.coverage_branch,
                field="coverage_branch"
            )
        if self.retry_count < 0:
            self.retry_count = 0
        if self.parallel_workers < 1:
            self.parallel_workers = 1
        if self.timeout_seconds < 1:
            self.timeout_seconds = 30


# ===========================================================================
# TestSuite
# ===========================================================================


@dataclass
class TestSuite:
    """
    Collection của test cases — unit, integration, e2e.

    Attributes:
        name: Tên test suite
        framework: Test framework (pytest, jest, karma)
        test_type: Loại test (unit, integration, e2e)
        cases: Danh sách test cases
        policy: Test policy (optional)
        setup: Global setup data (optional)
    """
    name: str
    framework: TestFramework
    test_type: TestType
    cases: list[TestCase] = field(default_factory=list)
    policy: Optional[TestPolicy] = None
    setup: dict[str, Any] = field(default_factory=dict)

    __test__ = False  # Prevent pytest collection

    def add_case(self, case: TestCase) -> None:
        """Thêm test case vào suite."""
        if self.get_case_by_id(case.id):
            EM.raise_error(ErrorCode.MDC-F05_DUPLICATE_TEST_ID, id=case.id)
        self.cases.append(case)

    def get_case_by_id(self, case_id: str) -> Optional[TestCase]:
        """Tìm test case theo ID."""
        for case in self.cases:
            if case.id == case_id:
                return case
        return None

    def get_enabled_cases(self) -> list[TestCase]:
        """Lọc các test cases đang active."""
        return [c for c in self.cases if c.enabled]

    def get_cases_by_target(self, target: str) -> list[TestCase]:
        """Lọc test cases theo target entity."""
        return [c for c in self.cases if c.target == target]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển test suite sang dict format."""
        return {
            "name": self.name,
            "framework": self.framework.value,
            "test_type": self.test_type.value,
            "cases": [
                {
                    "id": c.id,
                    "type": c.type.value,
                    "target": c.target,
                    "scenario": c.scenario,
                    "description": c.description,
                    "setup": c.setup,
                    "steps": [{"action": s.action, "params": s.params} for s in c.steps],
                    "assertions": [
                        {"check": a.check.value, "expected": a.expected, "actual_path": a.actual_path, "message": a.message}
                        for a in c.assertions
                    ],
                    "enabled": c.enabled,
                    "tags": c.tags,
                }
                for c in self.cases
            ],
            "policy": {
                "coverage_threshold": self.policy.coverage_threshold,
                "coverage_branch": self.policy.coverage_branch,
                "retry_count": self.policy.retry_count,
                "parallel": self.policy.parallel,
                "parallel_workers": self.policy.parallel_workers,
                "timeout_seconds": self.policy.timeout_seconds,
            } if self.policy else None,
            "setup": self.setup,
        }


# ===========================================================================
# TestCollection — output chính của TestParser
# ===========================================================================


@dataclass
class TestCollection:
    """
    Collection chứa tất cả test suites và policy global.

    Dùng làm output của TestParser và input cho Stack Emitters.

    Attributes:
        suites: Danh sách test suites
        global_policy: Global test policy (optional)
    """
    suites: list[TestSuite] = field(default_factory=list)
    global_policy: Optional[TestPolicy] = None

    __test__ = False  # Prevent pytest collection

    def add_suite(self, suite: TestSuite) -> None:
        """Thêm test suite vào collection."""
        self.suites.append(suite)

    def get_suites_by_type(self, test_type: TestType) -> list[TestSuite]:
        """Lọc suites theo test type."""
        return [s for s in self.suites if s.test_type == test_type]

    def get_suites_by_framework(self, framework: TestFramework) -> list[TestSuite]:
        """Lọc suites theo framework."""
        return [s for s in self.suites if s.framework == framework]

    def get_all_cases(self) -> list[TestCase]:
        """Lấy tất cả test cases từ mọi suite."""
        cases: list[TestCase] = []
        for suite in self.suites:
            cases.extend(suite.cases)
        return cases

    def get_cases_by_type(self, test_type: TestType) -> list[TestCase]:
        """Lọc test cases theo type."""
        cases: list[TestCase] = []
        for suite in self.suites:
            if suite.test_type == test_type:
                cases.extend(suite.cases)
        return cases

    def get_cases_for_target(self, target: str) -> list[TestCase]:
        """Lọc test cases theo target entity."""
        cases: list[TestCase] = []
        for suite in self.suites:
            cases.extend(suite.get_cases_by_target(target))
        return cases

    def count_cases(self) -> dict[str, int]:
        """Đếm số test cases theo type."""
        counts = {"unit": 0, "integration": 0, "e2e": 0}
        for suite in self.suites:
            for case in suite.cases:
                counts[case.type.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "suites": [s.to_dict() for s in self.suites],
            "global_policy": {
                "coverage_threshold": self.global_policy.coverage_threshold,
                "coverage_branch": self.global_policy.coverage_branch,
                "retry_count": self.global_policy.retry_count,
                "parallel": self.global_policy.parallel,
                "parallel_workers": self.global_policy.parallel_workers,
                "timeout_seconds": self.global_policy.timeout_seconds,
            } if self.global_policy else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCollection":
        """Tạo TestCollection từ dict."""
        collection = cls()
        if data.get("global_policy"):
            gp = data["global_policy"]
            collection.global_policy = TestPolicy(
                coverage_threshold=gp.get("coverage_threshold", 80),
                coverage_branch=gp.get("coverage_branch", 0),
                retry_count=gp.get("retry_count", 0),
                parallel=gp.get("parallel", False),
                parallel_workers=gp.get("parallel_workers", 4),
                timeout_seconds=gp.get("timeout_seconds", 30),
            )
        for suite_data in data.get("suites", []):
            suite = TestSuite(
                name=suite_data["name"],
                framework=TestFramework(suite_data["framework"]),
                test_type=TestType(suite_data["test_type"]),
                setup=suite_data.get("setup", {}),
            )
            if suite_data.get("policy"):
                sp = suite_data["policy"]
                suite.policy = TestPolicy(
                    coverage_threshold=sp.get("coverage_threshold", 80),
                    coverage_branch=sp.get("coverage_branch", 0),
                    retry_count=sp.get("retry_count", 0),
                    parallel=sp.get("parallel", False),
                    parallel_workers=sp.get("parallel_workers", 4),
                    timeout_seconds=sp.get("timeout_seconds", 30),
                )
            for case_data in suite_data.get("cases", []):
                case = TestCase(
                    id=case_data["id"],
                    type=TestType(case_data["type"]),
                    target=case_data["target"],
                    scenario=case_data["scenario"],
                    description=case_data.get("description", ""),
                    setup=case_data.get("setup", {}),
                    steps=[
                        TestStep(action=s["action"], params=s.get("params", {}))
                        for s in case_data.get("steps", [])
                    ],
                    assertions=[
                        TestAssertion(
                            check=AssertionCheck(a["check"]),
                            expected=a["expected"],
                            actual_path=a.get("actual_path", ""),
                            message=a.get("message", ""),
                        )
                        for a in case_data.get("assertions", [])
                    ],
                    enabled=case_data.get("enabled", True),
                    tags=case_data.get("tags", []),
                )
                suite.add_case(case)
            collection.add_suite(suite)
        return collection
