"""
Validation Report Contract cho Midicoder v1.0.0

Module này định nghĩa Validation Report - kết quả validation tại compile time.

Theo Rule 7 trong MIDICODER_STRATEGY.md:
- Verification là first-class, không phải hậu kiểm trang trí
- Midicoder phải verify được: syntax, import graph, obligations, etc.
- Fail hard nếu obligation không được phủ

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .artifact import ArtifactBase, ArtifactMetadata
from .graph import CapabilityGraph, Obligation


# ============================================================================
# Validation Status
# ============================================================================


class ValidationStatus(Enum):
    """
    Trạng thái validation.
    """
    PASS = "pass"           # Validation thành công
    WARNING = "warning"     # Có warnings nhưng pass
    FAIL = "fail"           # Validation thất bại
    ERROR = "error"         # Lỗi hệ thống khi validate


# ============================================================================
# Error Codes
# ============================================================================


class ErrorCode(Enum):
    """
    Error codes chuẩn cho validation errors.
    
    Theo Rule 7: Mọi lỗi trọng yếu có mã chuẩn.
    """
    # Syntax Errors
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INVALID_JSON = "INVALID_JSON"
    INVALID_YAML = "INVALID_YAML"
    
    # Reference Errors
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    DUPLICATE_ID = "DUPLICATE_ID"
    
    # Authorization Errors
    MISSING_PERMISSION_CHECK = "MISSING_PERMISSION_CHECK"
    MISSING_AUTH_GUARD = "MISSING_AUTH_GUARD"
    INVALID_ROLE_BINDING = "INVALID_ROLE_BINDING"
    INVALID_POLICY = "INVALID_POLICY"
    
    # Tenant Safety Errors
    MISSING_TENANT_FILTER = "MISSING_TENANT_FILTER"
    INVALID_TENANT_SCOPE = "INVALID_TENANT_SCOPE"
    TENANT_LEAK = "TENANT_LEAK"
    
    # Transaction Errors
    MISSING_TRANSACTION = "MISSING_TRANSACTION"
    INVALID_TRANSACTION_BOUNDARY = "INVALID_TRANSACTION_BOUNDARY"
    
    # Obligation Errors
    OBLIGATION_NOT_COVERED = "OBLIGATION_NOT_COVERED"
    OBLIGATION_CONFLICT = "OBLIGATION_CONFLICT"
    
    # Data Flow Errors
    UNVALIDATED_INPUT = "UNVALIDATED_INPUT"
    UNSAFE_OUTPUT = "UNSAFE_OUTPUT"
    DATA_LEAK = "DATA_LEAK"
    
    # Integration Errors
    MISSING_ERROR_HANDLER = "MISSING_ERROR_HANDLER"
    MISSING_TIMEOUT = "MISSING_TIMEOUT"
    MISSING_RETRY_POLICY = "MISSING_RETRY_POLICY"
    
    # Compliance Errors
    MISSING_AUDIT_LOG = "MISSING_AUDIT_LOG"
    PII_EXPOSURE = "PII_EXPOSURE"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
    
    # IDempotency Errors
    MISSING_IDEMPOTENCY = "MISSING_IDEMPOTENCY"
    INVALID_IDEMPOTENCY_KEY = "INVALID_IDEMPOTENCY_KEY"
    
    # Schema Errors
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"


# ============================================================================
# Critical Error Codes (Fail-Fast)
# ============================================================================

# Tập hợp các error codes critical - làm compilation FAIL ngay lập tức
# Theo SoT: Critical errors stop pipeline, không cho code generation
CRITICAL_ERROR_CODES: set[str] = {
    ErrorCode.MISSING_PERMISSION_CHECK.value,
    ErrorCode.MISSING_TENANT_FILTER.value,
    ErrorCode.MISSING_TRANSACTION.value,
    ErrorCode.OBLIGATION_NOT_COVERED.value,
    ErrorCode.TENANT_LEAK.value,
    ErrorCode.PII_EXPOSURE.value,
    ErrorCode.COMPLIANCE_VIOLATION.value,
}


# ============================================================================
# Validation Error
# ============================================================================


@dataclass
class ValidationError:
    """
    Validation Error đại diện cho một lỗi validation.
    
    Theo Rule 7: Fail-fast đúng lý do cho các lỗi trọng yếu.
    
    Attributes:
        code: Error code (từ ErrorCode enum)
        message: Thông báo lỗi chi tiết
        path: Path đến element lỗi (ví dụ: "commands[0].guards")
        source: Source artifact/file
        context: Additional context information
        
    Example:
        ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER,
            message="Command 'CreateOrder' thiếu tenant filter",
            path="instances.create_order",
            source="capability_graph.json",
        )
    """
    code: str
    message: str
    path: str | None = None
    source: str | None = None
    context: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "source": self.source,
            "context": self.context,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationError":
        """Tạo ValidationError từ dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            path=data.get("path"),
            source=data.get("source"),
            context=data.get("context"),
        )
    
    @property
    def is_critical(self) -> bool:
        """Kiểm tra error có critical không."""
        return self.code in CRITICAL_ERROR_CODES


# ============================================================================
# Validation Warning
# ============================================================================


@dataclass
class ValidationWarning:
    """
    Validation Warning đại diện cho một cảnh báo.
    
    Warnings không làm validation fail nhưng nên được review.
    
    Attributes:
        code: Warning code
        message: Thông báo cảnh báo
        path: Path đến element
        source: Source artifact/file
        suggestion: Gợi ý fix
        
    Example:
        ValidationWarning(
            code="MISSING_DESCRIPTION",
            message="Entity 'Order' nên có description",
            path="entities.Order",
            suggestion="Thêm field 'description' vào entity definition",
        )
    """
    code: str
    message: str
    path: str | None = None
    source: str | None = None
    suggestion: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "source": self.source,
            "suggestion": self.suggestion,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationWarning":
        """Tạo ValidationWarning từ dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            path=data.get("path"),
            source=data.get("source"),
            suggestion=data.get("suggestion"),
        )


# ============================================================================
# Validation Exception
# ============================================================================


class ValidationException(Exception):
    """
    Exception cho validation failures với critical errors.
    
    Exception này được raise khi có critical errors, làm pipeline dừng ngay.
    
    Attributes:
        message: Thông báo lỗi chi tiết
        errors: Danh sách critical errors
        error_codes: Danh sách error codes
        
    Example:
        try:
            raise_on_critical_errors(report)
        except ValidationException as e:
            print(f"Validation failed with {len(e.errors)} critical errors")
    """
    
    def __init__(
        self,
        message: str,
        errors: list[ValidationError],
        error_codes: list[str] | None = None,
    ) -> None:
        """
        Khởi tạo ValidationException.
        
        Args:
            message: Thông báo lỗi
            errors: Danh sách errors
            error_codes: Danh sách error codes
        """
        super().__init__(message)
        self.message = message
        self.errors = errors
        self.error_codes = error_codes or [e.code for e in errors]
    
    def __str__(self) -> str:
        """Trả về string representation của exception."""
        return self.message


# ============================================================================
# Validation Report
# ============================================================================


@dataclass
class ValidationReport(ArtifactBase):
    """
    Validation Report - Kết quả validation tại compile time.
    
    Theo Rule 7: Verifier phải check coverage của obligations.
    Fail hard nếu obligation không được phủ.
    
    Attributes:
        status: Validation status (pass/warning/fail/error)
        artifact_type: Loại artifact được validate
        artifact_ref: Reference vào artifact
        errors: Danh sách validation errors
        warnings: Danh sách validation warnings
        checks: Kết quả của từng check
        summary: Tổng kết validation
        metadata: Artifact metadata
    """
    status: str = "pass"
    artifact_type: str = ""
    artifact_ref: str = ""
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    
    @property
    def artifact_type_name(self) -> str:
        """Return artifact type."""
        return "validation_report"
    
    @property
    def artifact_type_base(self) -> str:
        """Override for base class compatibility."""
        return "validation_report"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.artifact_type_name,
            "version": "1.0.0",
            "metadata": self.metadata.to_dict(),
            "status": self.status,
            "artifact_type": self.artifact_type,
            "artifact_ref": self.artifact_ref,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "checks": self.checks,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationReport":
        """Tạo ValidationReport từ dictionary."""
        report = cls(
            status=data.get("status", "pass"),
            artifact_type=data.get("artifact_type", ""),
            artifact_ref=data.get("artifact_ref", ""),
            errors=[ValidationError.from_dict(e) for e in data.get("errors", [])],
            warnings=[ValidationWarning.from_dict(w) for w in data.get("warnings", [])],
            checks=data.get("checks", {}),
            summary=data.get("summary", {}),
        )
        object.__setattr__(report, 'metadata', ArtifactMetadata.from_dict(data.get("metadata", {})))
        return report
    
    @classmethod
    def pass_(
        cls,
        artifact_type: str,
        artifact_ref: str,
        metadata: ArtifactMetadata | None = None,
    ) -> "ValidationReport":
        """Tạo validation report với status PASS."""
        return cls(
            status=ValidationStatus.PASS.value,
            artifact_type=artifact_type,
            artifact_ref=artifact_ref,
            metadata=metadata or ArtifactMetadata.with_timestamp(),
            summary={
                "total_errors": 0,
                "total_warnings": 0,
                "critical_errors": 0,
            },
        )
    
    @classmethod
    def fail(
        cls,
        artifact_type: str,
        artifact_ref: str,
        errors: list[ValidationError],
        metadata: ArtifactMetadata | None = None,
    ) -> "ValidationReport":
        """Tạo validation report với status FAIL."""
        return cls(
            status=ValidationStatus.FAIL.value,
            artifact_type=artifact_type,
            artifact_ref=artifact_ref,
            errors=errors,
            metadata=metadata or ArtifactMetadata.with_timestamp(),
            summary={
                "total_errors": len(errors),
                "total_warnings": 0,
                "critical_errors": sum(1 for e in errors if e.is_critical),
            },
        )
    
    @classmethod
    def warning(
        cls,
        artifact_type: str,
        artifact_ref: str,
        warnings: list[ValidationWarning],
        metadata: ArtifactMetadata | None = None,
    ) -> "ValidationReport":
        """Tạo validation report với status WARNING."""
        return cls(
            status=ValidationStatus.WARNING.value,
            artifact_type=artifact_type,
            artifact_ref=artifact_ref,
            warnings=warnings,
            metadata=metadata or ArtifactMetadata.with_timestamp(),
            summary={
                "total_errors": 0,
                "total_warnings": len(warnings),
                "critical_errors": 0,
            },
        )
    
    def add_error(
        self,
        code: str,
        message: str,
        path: str | None = None,
        source: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Thêm validation error."""
        error = ValidationError(
            code=code,
            message=message,
            path=path,
            source=source,
            context=context,
        )
        self.errors.append(error)
        self.status = ValidationStatus.FAIL.value
    
    def add_warning(
        self,
        code: str,
        message: str,
        path: str | None = None,
        source: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Thêm validation warning."""
        warning = ValidationWarning(
            code=code,
            message=message,
            path=path,
            source=source,
            suggestion=suggestion,
        )
        self.warnings.append(warning)
        
        if self.status == ValidationStatus.PASS.value:
            self.status = ValidationStatus.WARNING.value
    
    def get_errors_by_code(self, code: str) -> list[ValidationError]:
        """Lấy errors theo code."""
        return [e for e in self.errors if e.code == code]
    
    def has_errors(self) -> bool:
        """Kiểm tra có errors không."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Kiểm tra có warnings không."""
        return len(self.warnings) > 0
    
    def is_valid(self) -> bool:
        """Kiểm tra validation pass."""
        return self.status in (
            ValidationStatus.PASS.value,
            ValidationStatus.WARNING.value,
        )
    
    def generate_summary(self) -> None:
        """Generate summary từ errors và warnings."""
        self.summary = {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "critical_errors": sum(1 for e in self.errors if e.is_critical),
            "error_codes": list(set(e.code for e in self.errors)),
            "warning_codes": list(set(w.code for w in self.warnings)),
        }
    
    def validate(self) -> list[str]:
        """Validate validation report."""
        errors = super().validate()
        
        if not self.artifact_type:
            errors.append("ValidationReport.artifact_type is required")
        
        if not self.artifact_ref:
            errors.append("ValidationReport.artifact_ref is required")
        
        if self.errors and self.status == ValidationStatus.PASS.value:
            errors.append("Report has errors but status is PASS")
        
        return errors


# ============================================================================
# Obligation Coverage Check Functions
# ============================================================================


def get_unsatisfied_obligations(graph: CapabilityGraph) -> list[Obligation]:
    """
    Lấy danh sách tất cả obligations chưa được satisfy.
    
    Args:
        graph: CapabilityGraph chứa obligations
        
    Returns:
        Danh sách Obligations với satisfied=False
    """
    return [o for o in graph.obligations if not o.satisfied]


def get_obligation_coverage_summary(graph: CapabilityGraph) -> dict[str, Any]:
    """
    Lấy summary về coverage của obligations.
    
    Args:
        graph: CapabilityGraph chứa obligations
        
    Returns:
        Dictionary với obligation coverage statistics
    """
    total = len(graph.obligations)
    satisfied_count = sum(1 for o in graph.obligations if o.satisfied)
    unsatisfied_count = total - satisfied_count
    
    coverage_percentage = 0.0
    if total > 0:
        coverage_percentage = (satisfied_count / total) * 100
    
    obligations_by_type: dict[str, dict[str, int]] = {}
    for oblig in graph.obligations:
        if oblig.type not in obligations_by_type:
            obligations_by_type[oblig.type] = {"total": 0, "satisfied": 0, "unsatisfied": 0}
        obligations_by_type[oblig.type]["total"] += 1
        if oblig.satisfied:
            obligations_by_type[oblig.type]["satisfied"] += 1
        else:
            obligations_by_type[oblig.type]["unsatisfied"] += 1
    
    unsatisfied_by_source: dict[str, list[str]] = {}
    for oblig in get_unsatisfied_obligations(graph):
        source = oblig.source or "unknown"
        if source not in unsatisfied_by_source:
            unsatisfied_by_source[source] = []
        unsatisfied_by_source[source].append(oblig.id)
    
    return {
        "total_obligations": total,
        "satisfied_count": satisfied_count,
        "unsatisfied_count": unsatisfied_count,
        "coverage_percentage": round(coverage_percentage, 2),
        "obligations_by_type": obligations_by_type,
        "unsatisfied_by_source": unsatisfied_by_source,
    }


def check_obligation_coverage(
    graph: CapabilityGraph,
    artifact_ref: str,
) -> ValidationReport:
    """
    Kiểm tra coverage của tất cả obligations trong graph.
    
    Theo SoT requirement.md:
    - Verifier phải check coverage của obligations tại compile-time
    - Fail hard nếu obligation không được phủ
    - OBLIGATION_NOT_COVERED là critical error
    
    Args:
        graph: CapabilityGraph chứa obligations cần check
        artifact_ref: Reference vào artifact đang được validate
        
    Returns:
        ValidationReport với kết quả check obligation coverage
    """
    unsatisfied = get_unsatisfied_obligations(graph)
    summary = get_obligation_coverage_summary(graph)
    
    if not unsatisfied:
        report = ValidationReport(
            status=ValidationStatus.PASS.value,
            artifact_type="capability_graph",
            artifact_ref=artifact_ref,
            checks={
                "obligation_coverage": ValidationStatus.PASS.value,
            },
            summary={
                "total_obligations": summary["total_obligations"],
                "satisfied_obligations": summary["satisfied_count"],
                "unsatisfied_obligations": summary["unsatisfied_count"],
                "coverage_percentage": summary["coverage_percentage"],
            },
        )
        return report
    
    errors: list[ValidationError] = []
    
    for oblig in unsatisfied:
        path = oblig.source if oblig.source else "unknown"
        
        message = (
            f"Obligation '{oblig.id}' (type: {oblig.type}) chưa được satisfy. "
            f"Source: {path}. "
            f"Description: {oblig.description or 'Không có mô tả'}"
        )
        
        error = ValidationError(
            code=ErrorCode.OBLIGATION_NOT_COVERED.value,
            message=message,
            path=path,
            source=artifact_ref,
            context={
                "obligation_id": oblig.id,
                "obligation_type": oblig.type,
                "obligation_description": oblig.description,
                "is_critical": True,
            },
        )
        errors.append(error)
    
    report = ValidationReport(
        status=ValidationStatus.FAIL.value,
        artifact_type="capability_graph",
        artifact_ref=artifact_ref,
        errors=errors,
        checks={
            "obligation_coverage": ValidationStatus.FAIL.value,
        },
        summary={
            "total_obligations": summary["total_obligations"],
            "satisfied_obligations": summary["satisfied_count"],
            "unsatisfied_obligations": summary["unsatisfied_count"],
            "coverage_percentage": summary["coverage_percentage"],
            "obligations_by_type": summary["obligations_by_type"],
            "unsatisfied_by_source": summary["unsatisfied_by_source"],
        },
    )
    
    return report


# ============================================================================
# Fail-Fast Logic Functions
# ============================================================================


def is_critical_error(error_code: str) -> bool:
    """
    Kiểm tra error code có phải critical không.
    
    Critical errors làm compilation FAIL và stop pipeline.
    
    Args:
        error_code: Error code để kiểm tra
        
    Returns:
        True nếu là critical error, False nếu không
    """
    return error_code in CRITICAL_ERROR_CODES


def has_critical_errors(report: ValidationReport) -> bool:
    """
    Kiểm tra report có critical errors không.
    
    Hàm này dùng để quyết định có nên fail-fast hay không.
    
    Args:
        report: ValidationReport cần kiểm tra
        
    Returns:
        True nếu có ít nhất 1 critical error, False nếu không
    """
    for error in report.errors:
        if error.is_critical:
            return True
    return False


def get_critical_errors(report: ValidationReport) -> list[ValidationError]:
    """
    Lấy danh sách critical errors từ report.
    
    Args:
        report: ValidationReport
        
    Returns:
        Danh sách critical errors (rỗng nếu không có)
    """
    return [error for error in report.errors if error.is_critical]


def should_fail_fast(report: ValidationReport) -> bool:
    """
    Quyết định có nên fail-fast hay không.
    
    Theo SoT: Fail-fast khi có critical errors để stop pipeline.
    
    Args:
        report: ValidationReport
        
    Returns:
        True nếu nên dừng pipeline (có critical errors), False nếu tiếp tục
    """
    return has_critical_errors(report)


def raise_on_critical_errors(report: ValidationReport) -> None:
    """
    Raise ValidationException nếu có critical errors.
    
    Hàm này dùng để enforce fail-fast logic trong pipeline.
    Nếu có critical errors, exception được raise và pipeline dừng.
    
    Args:
        report: ValidationReport
        
    Raises:
        ValidationException: Nếu có critical errors
    """
    critical_errors = get_critical_errors(report)
    
    if not critical_errors:
        return
    
    error_codes = list(set(e.code for e in critical_errors))
    
    error_details = "\n".join(
        f"  - [{e.code}] {e.message}" for e in critical_errors
    )
    
    message = (
        f"Validation failed with {len(critical_errors)} critical error(s). "
        f"Pipeline stopped.\n\n"
        f"Critical errors:\n{error_details}"
    )
    
    raise ValidationException(
        message=message,
        errors=critical_errors,
        error_codes=error_codes,
    )