"""
Mô-đun models cho Invariant Enforcement System.

Định nghĩa các data class và enum dùng chung cho toàn bộ hệ thống invariant:
- InvariantCategory: Phân loại invariants (business, compliance, failure_mode)
- EnforcementMode: Chế độ enforce (compile-time, runtime, both)
- InvariantDefinition: Định nghĩa đầy đủ của một invariant
- InvariantResult: Kết quả check một invariant
- InvariantReport: Báo cáo tổng hợp tất cả invariant checks

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


# ============================================================================
# Invariant Category Enum
# ============================================================================


class InvariantCategory(str, Enum):
    """
    Phân loại invariants theo mục đích sử dụng.

    Values:
        BUSINESS: Business invariants - đảm bảo domain logic đúng
        COMPLIANCE: Compliance invariants - đảm bảo regulatory compliance
        FAILURE_MODE: Failure-mode invariants - đảm bảo reliability
    """

    BUSINESS = "business"
    COMPLIANCE = "compliance"
    FAILURE_MODE = "failure_mode"


# ============================================================================
# Enforcement Mode Enum
# ============================================================================


class EnforcementMode(str, Enum):
    """
    Chế độ enforcement của invariant.

    Values:
        COMPILE_TIME: Check tại compile-time, fail nếu vi phạm
        RUNTIME: Check tại runtime, generate guard code
        BOTH: Check cả compile-time và runtime
    """

    COMPILE_TIME = "compile-time"
    RUNTIME = "runtime"
    BOTH = "both"


# ============================================================================
# Severity Enum
# ============================================================================


class InvariantSeverity(str, Enum):
    """
    Mức độ nghiêm trọng của invariant violation.

    Values:
        ERROR: Violation là critical error, phải fix
        WARNING: Violation là warning, nên review
    """

    ERROR = "error"
    WARNING = "warning"


# ============================================================================
# Invariant Definition
# ============================================================================


@dataclass
class InvariantDefinition:
    """
    Định nghĩa đầy đủ của một invariant.

    Mỗi InvariantDefinition mô tả một business rule cần enforce,
    bao gồm cả compile-time check và runtime guard.

    Attributes:
        id: Identifier duy nhất (ví dụ: INV-BIZ-001)
        name: Tên hiển thị của invariant
        description: Mô tả chi tiết invariant
        category: Phân loại invariant
        enforcement: Chế độ enforcement
        severity: Mức độ nghiêm trọng khi vi phạm
        violation_code: ErrorCode khi vi phạm (MDC-INV-XXX)
        overlay: Regulatory overlay reference (RX01-RX12, optional)
        domain: Domain pack reference (DP01-DP26, optional)
        validator_fn: Tên hàm check compile-time
        runtime_guard: Tên class guard cho runtime (optional)
        check_fn: Callable để check compile-time (optional)
        tags: Danh sách tags để phân loại
    """

    id: str
    name: str
    description: str
    category: InvariantCategory
    enforcement: EnforcementMode
    severity: str = "error"
    violation_code: str = ""
    overlay: str | None = None
    domain: str | None = None
    validator_fn: str = ""
    runtime_guard: str | None = None
    check_fn: Callable | None = None
    tags: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        """Hash dựa trên id để dùng trong set và dict key."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """So sánh bằng dựa trên id."""
        if not isinstance(other, InvariantDefinition):
            return False
        return self.id == other.id

    @property
    def is_compile_time(self) -> bool:
        """Kiểm tra invariant có enforce tại compile-time không."""
        return self.enforcement in (
            EnforcementMode.COMPILE_TIME,
            EnforcementMode.BOTH,
        )

    @property
    def is_runtime(self) -> bool:
        """Kiểm tra invariant có enforce tại runtime không."""
        return self.enforcement in (
            EnforcementMode.RUNTIME,
            EnforcementMode.BOTH,
        )

    @property
    def is_critical(self) -> bool:
        """Kiểm tra invariant có severity là error không."""
        return self.severity == "error"

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển InvariantDefinition sang dict để serialization.

        Returns:
            Dictionary representation của invariant
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "enforcement": self.enforcement.value,
            "severity": self.severity,
            "violation_code": self.violation_code,
            "overlay": self.overlay,
            "domain": self.domain,
            "validator_fn": self.validator_fn,
            "runtime_guard": self.runtime_guard,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InvariantDefinition:
        """
        Tạo InvariantDefinition từ dictionary.

        Args:
            data: Dictionary chứa các fields của invariant

        Returns:
            InvariantDefinition instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=InvariantCategory(data["category"]),
            enforcement=EnforcementMode(data["enforcement"]),
            severity=data.get("severity", "error"),
            violation_code=data.get("violation_code", ""),
            overlay=data.get("overlay"),
            domain=data.get("domain"),
            validator_fn=data.get("validator_fn", ""),
            runtime_guard=data.get("runtime_guard"),
            check_fn=data.get("check_fn"),
            tags=data.get("tags", []),
        )


# ============================================================================
# Invariant Result
# ============================================================================


@dataclass
class InvariantResult:
    """
    Kết quả check của một invariant.

    Mỗi InvariantResult đại diện cho kết quả validate một invariant
    cụ thể trên một artifact (blueprint, graph, etc.).

    Attributes:
        invariant_id: ID của invariant được check
        category: Phân loại của invariant
        enforcement_mode: Chế độ enforcement
        passed: Kết quả check (True = pass, False = fail)
        severity: Mức độ nghiêm trọng
        violation_code: Error code khi vi phạm (nếu có)
        message: Thông báo kết quả
        context: Context thông tin bổ sung cho debugging
    """

    invariant_id: str
    category: InvariantCategory
    enforcement_mode: EnforcementMode
    passed: bool
    severity: str
    violation_code: str | None = None
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_violation(self) -> bool:
        """Kiểm tra đây có phải là violation không."""
        return not self.passed

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển InvariantResult sang dict.

        Returns:
            Dictionary representation của result
        """
        return {
            "invariant_id": self.invariant_id,
            "category": self.category.value,
            "enforcement_mode": self.enforcement_mode.value,
            "passed": self.passed,
            "severity": self.severity,
            "violation_code": self.violation_code,
            "message": self.message,
            "context": self.context,
        }


# ============================================================================
# Invariant Report
# ============================================================================


@dataclass
class InvariantReport:
    """
    Báo cáo tổng hợp kết quả enforce tất cả invariants.

    InvariantReport chứa kết quả validate tất cả invariants
    cho một blueprint cụ thể, với summary và chi tiết từng invariant.

    Attributes:
        blueprint_id: ID của blueprint được validate
        timestamp: Thời gian tạo report
        total_invariants: Tổng số invariants được check
        passed: Số invariants pass
        failed: Số invariants fail (severity=error)
        warnings: Số invariants warning
        results: Danh sách kết quả từng invariant
        summary: Summary statistics
    """

    blueprint_id: str
    timestamp: str = ""
    total_invariants: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    results: list[InvariantResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Khởi tạo timestamp nếu chưa có."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def is_passing(self) -> bool:
        """
        Kiểm tra report có pass không.

        Report pass khi không có failed invariants (severity=error).
        Warnings không làm report fail.

        Returns:
            True nếu không có failures, False nếu có
        """
        return self.failed == 0

    def get_violations(self) -> list[InvariantResult]:
        """
        Lấy danh sách tất cả violations (passed=False).

        Returns:
            Danh sách InvariantResult có passed=False
        """
        return [r for r in self.results if r.is_violation]

    def get_by_category(self, category: InvariantCategory) -> list[InvariantResult]:
        """
        Lấy results theo category.

        Args:
            category: InvariantCategory cần lọc

        Returns:
            Danh sách InvariantResult thuộc category
        """
        return [r for r in self.results if r.category == category]

    def get_critical_violations(self) -> list[InvariantResult]:
        """
        Lấy danh sách violations có severity = error.

        Returns:
            Danh sách InvariantResult có passed=False và severity="error"
        """
        return [
            r for r in self.results
            if r.is_violation and r.severity == "error"
        ]

    def add_result(self, result: InvariantResult) -> None:
        """
        Thêm kết quả invariant vào report và update counters.

        Args:
            result: InvariantResult cần thêm
        """
        self.results.append(result)
        self.total_invariants += 1

        if result.passed:
            self.passed += 1
        elif result.severity == "error":
            self.failed += 1
        else:
            self.warnings += 1

    def generate_summary(self) -> dict[str, Any]:
        """
        Generate summary statistics từ results.

        Returns:
            Dictionary với summary statistics
        """
        by_category: dict[str, dict[str, int]] = {}
        by_enforcement: dict[str, dict[str, int]] = {}

        for result in self.results:
            cat_key = result.category.value
            if cat_key not in by_category:
                by_category[cat_key] = {"total": 0, "passed": 0, "failed": 0}
            by_category[cat_key]["total"] += 1
            if result.passed:
                by_category[cat_key]["passed"] += 1
            else:
                by_category[cat_key]["failed"] += 1

            enf_key = result.enforcement_mode.value
            if enf_key not in by_enforcement:
                by_enforcement[enf_key] = {"total": 0, "passed": 0, "failed": 0}
            by_enforcement[enf_key]["total"] += 1
            if result.passed:
                by_enforcement[enf_key]["passed"] += 1
            else:
                by_enforcement[enf_key]["failed"] += 1

        self.summary = {
            "total_invariants": self.total_invariants,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "is_passing": self.is_passing,
            "by_category": by_category,
            "by_enforcement": by_enforcement,
            "violation_codes": list(set(
                r.violation_code for r in self.get_violations() if r.violation_code
            )),
        }

        return self.summary

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển InvariantReport sang dict.

        Returns:
            Dictionary representation của report
        """
        self.generate_summary()

        return {
            "blueprint_id": self.blueprint_id,
            "timestamp": self.timestamp,
            "total_invariants": self.total_invariants,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "is_passing": self.is_passing,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InvariantReport:
        """
        Tạo InvariantReport từ dictionary.

        Args:
            data: Dictionary chứa data của report

        Returns:
            InvariantReport instance
        """
        results = [
            InvariantResult(
                invariant_id=r["invariant_id"],
                category=InvariantCategory(r["category"]),
                enforcement_mode=EnforcementMode(r["enforcement_mode"]),
                passed=r["passed"],
                severity=r["severity"],
                violation_code=r.get("violation_code"),
                message=r.get("message", ""),
                context=r.get("context", {}),
            )
            for r in data.get("results", [])
        ]

        return cls(
            blueprint_id=data["blueprint_id"],
            timestamp=data.get("timestamp", ""),
            total_invariants=data.get("total_invariants", len(results)),
            passed=data.get("passed", sum(1 for r in results if r.passed)),
            failed=data.get("failed", sum(1 for r in results if not r.passed and r.severity == "error")),
            warnings=data.get("warnings", sum(1 for r in results if not r.passed and r.severity == "warning")),
            results=results,
            summary=data.get("summary", {}),
        )


# ============================================================================
# Compile-Time Check Spec
# ============================================================================


@dataclass
class CompileTimeCheckSpec:
    """
    Spec cho compile-time check của invariant.

    Attributes:
        invariant_id: ID của invariant
        check_function: Tên hàm check
        target_artifact: Loại artifact cần check (blueprint, graph, etc.)
        params: Parameters cho check function
    """

    invariant_id: str
    check_function: str
    target_artifact: str = "blueprint"
    params: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Runtime Guard Spec
# ============================================================================


@dataclass
class RuntimeGuardSpec:
    """
    Spec cho runtime guard của invariant.

    Attributes:
        invariant_id: ID của invariant
        guard_class: Tên class guard để emit
        target_component: Component cần attach guard (handler, service, etc.)
        guard_params: Parameters cho guard
        error_code: Error code khi guard fail
        stack: Target stack (fastapi, nestjs)
    """

    invariant_id: str
    guard_class: str
    target_component: str = "handler"
    guard_params: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    stack: str = "fastapi"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RuntimeGuardSpec sang dict."""
        return {
            "invariant_id": self.invariant_id,
            "guard_class": self.guard_class,
            "target_component": self.target_component,
            "guard_params": self.guard_params,
            "error_code": self.error_code,
            "stack": self.stack,
        }