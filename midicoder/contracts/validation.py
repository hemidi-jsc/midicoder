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
    
    # ========================================================================
    # Invariant Gates Errors (INV001-INV008) - Epic E10
    # ========================================================================
    
    # INV001: Entity ref resolution - Entity references không resolve được
    UNRESOLVED_ENTITY_REF = "UNRESOLVED_ENTITY_REF"
    
    # INV002: Permission ref resolution - Permission references không resolve được
    UNRESOLVED_PERMISSION_REF = "UNRESOLVED_PERMISSION_REF"
    
    # INV003: Role ref resolution - Role references không resolve được
    UNRESOLVED_ROLE_REF = "UNRESOLVED_ROLE_REF"
    
    # INV004: Command permission guard - Commands thiếu permission guard
    MISSING_PERMISSION_GUARD = "MISSING_PERMISSION_GUARD"
    
    # INV005: Query tenant filter - Queries thiếu tenant filter (đã có ở trên nhưng add vào đây cho rõ)
    # MISSING_TENANT_FILTER đã được define ở Tenant Safety Errors
    
    # INV006: Mutation transaction scope - Mutations thiếu transaction scope
    MISSING_TRANSACTION_SCOPE = "MISSING_TRANSACTION_SCOPE"
    
    # INV007: Role policy binding - Roles thiếu policy binding
    MISSING_ROLE_POLICY = "MISSING_ROLE_POLICY"
    
    # INV008: Policy syntax validation - Policies có syntax không hợp lệ
    INVALID_POLICY_SYNTAX = "INVALID_POLICY_SYNTAX"
    
    # ========================================================================
    # Domain Invariants - Banking (FIN)
    # ========================================================================
    
    # Banking: Double-entry imbalance - Tổng debit không bằng tổng credit
    FIN_DOUBLE_ENTRY_IMBALANCE = "FIN_DOUBLE_ENTRY_IMBALANCE"
    
    # Banking: KYC not verified - Giao dịch cần KYC nhưng không verify
    FIN_KYC_NOT_VERIFIED = "FIN_KYC_NOT_VERIFIED"
    
    # ========================================================================
    # Domain Invariants - Healthcare (HLT)
    # ========================================================================
    
    # Healthcare: PHI not encrypted - PHI fields không được encrypt
    HLT_PHI_NOT_ENCRYPTED = "HLT_PHI_NOT_ENCRYPTED"
    
    # Healthcare: Missing clinical audit - Clinical action không có audit trail
    HLT_MISSING_CLINICAL_AUDIT = "HLT_MISSING_CLINICAL_AUDIT"
    
    # ========================================================================
    # Domain Invariants - Exchange (EXC)
    # ========================================================================
    
    # Exchange: Order risk check missing - Order không có risk check
    EXC_ORDER_RISK_CHECK_MISSING = "EXC_ORDER_RISK_CHECK_MISSING"
    
    # Exchange: Settlement not atomic - Settlement không atomic
    EXC_SETTLEMENT_NOT_ATOMIC = "EXC_SETTLEMENT_NOT_ATOMIC"


# ============================================================================
# Critical Error Codes (Fail-Fast)
# ============================================================================

# Tập hợp các error codes critical - làm compilation FAIL ngay lập tức
# Theo SoT: Critical errors stop pipeline, không cho code generation
CRITICAL_ERROR_CODES: set[str] = {
    ErrorCode.MISSING_PERMISSION_CHECK.value,
    ErrorCode.MISSING_TENANT_FILTER.value,
    ErrorCode.MISSING_TRANSACTION.value,
    ErrorCode.MISSING_TRANSACTION_SCOPE.value,  # INV006: Mutation transaction scope
    ErrorCode.OBLIGATION_NOT_COVERED.value,
    ErrorCode.TENANT_LEAK.value,
    ErrorCode.PII_EXPOSURE.value,
    ErrorCode.COMPLIANCE_VIOLATION.value,
    # Invariant Gates critical errors
    ErrorCode.UNRESOLVED_ENTITY_REF.value,      # INV001: Entity ref resolution
    ErrorCode.UNRESOLVED_PERMISSION_REF.value,  # INV002: Permission ref resolution
    ErrorCode.UNRESOLVED_ROLE_REF.value,        # INV003: Role ref resolution
    ErrorCode.MISSING_PERMISSION_GUARD.value,   # INV004: Command permission guard
    ErrorCode.MISSING_ROLE_POLICY.value,        # INV007: Role policy binding
    ErrorCode.INVALID_POLICY_SYNTAX.value,      # INV008: Policy syntax validation
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


# ============================================================================
# InvariantValidator - Epic E10: Invariant Gates
# ============================================================================


class InvariantValidator:
    """
    InvariantValidator - Validator cho các invariants INV001-INV008.
    
    Theo SoT requirement.md Epic E10:
    - INV001: Entity ref resolution - Kiểm tra entity references
    - INV002: Permission ref resolution - Kiểm tra permission references
    - INV003: Role ref resolution - Kiểm tra role references
    - INV004: Command permission guard - Kiểm tra commands có permission
    - INV005: Query tenant filter - Kiểm tra queries có tenant filter
    - INV006: Mutation transaction scope - Kiểm tra mutations có transaction
    - INV007: Role policy binding - Kiểm tra roles có policy binding
    - INV008: Policy syntax validation - Kiểm tra policy syntax
    
    Args:
        graph: CapabilityGraph cần validate
        
    Example:
        validator = InvariantValidator(graph)
        report = validator.validate_all()
        if not report.is_valid():
            print(f"Validation failed: {report.errors}")
    """
    
    # Loại instances cần check cho từng invariant
    MUTATION_TYPES = {"authorized_mutation", "create_record", "update_record", "delete_record"}
    QUERY_TYPES = {"authorized_query", "query_records", "load_entity"}
    ROLE_TYPES = {"role"}
    POLICY_TYPES = {"policy"}
    PERMISSION_TYPES = {"permission"}
    
    # Các giá trị effect hợp lệ cho policies
    VALID_POLICY_EFFECTS = {"allow", "deny"}
    
    def __init__(self, graph: CapabilityGraph) -> None:
        """
        Khởi tạo InvariantValidator.
        
        Args:
            graph: CapabilityGraph cần validate
        """
        self.graph = graph
        self._build_symbol_table()
    
    def _build_symbol_table(self) -> None:
        """
        Xây dựng symbol table cho fast lookups.
        
        Symbol table bao gồm:
        - entities: Tập hợp entity names từ tất cả reads
        - permissions: Tập hợp permission names từ permission definitions
        - roles: Tập hợp role names từ role definitions
        - policies: Tập hợp policy names từ policy definitions
        """
        # Build entity set từ tất cả reads của instances
        self._entities: set[str] = set()
        for instance in self.graph.instances:
            self._entities.update(instance.reads)
            self._entities.update(instance.writes)
        
        # Build permission set từ permission definitions
        self._permissions: set[str] = set()
        for instance in self.graph.instances:
            if instance.type in self.PERMISSION_TYPES:
                if "name" in instance.params:
                    self._permissions.add(instance.params["name"])
        
        # Build role set từ role definitions
        self._roles: set[str] = set()
        for instance in self.graph.instances:
            if instance.type in self.ROLE_TYPES:
                # Role name có thể ở field "name" hoặc dùng instance.id
                if "name" in instance.params:
                    self._roles.add(instance.params["name"])
                else:
                    self._roles.add(instance.id)
        
        # Build policy set từ policy definitions
        self._policies: set[str] = set()
        for instance in self.graph.instances:
            if instance.type in self.POLICY_TYPES:
                if "name" in instance.params:
                    self._policies.add(instance.params["name"])
                else:
                    self._policies.add(instance.id)
    
    def validate_entity_refs(self) -> ValidationReport:
        """
        INV001: Entity ref resolution - Kiểm tra entity references.
        
        Kiểm tra rằng tất cả entity_ref trong params đều resolve được
        đến một entity đã được declare trong graph.
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            entity_ref = instance.params.get("entity_ref")
            if entity_ref:
                # Check entity_ref có tồn tại trong entities không
                if entity_ref not in self._entities:
                    error = ValidationError(
                        code=ErrorCode.UNRESOLVED_ENTITY_REF.value,
                        message=(
                            f"Entity reference '{entity_ref}' trong instance "
                            f"'{instance.id}' không tìm thấy. "
                            f"Đã declare entities: {', '.join(sorted(self._entities)) if self._entities else 'không có'}"
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "entity_ref": entity_ref,
                            "available_entities": list(sorted(self._entities)),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV001": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV001": ValidationStatus.FAIL.value},
        )
    
    def validate_permission_refs(self) -> ValidationReport:
        """
        INV002: Permission ref resolution - Kiểm tra permission references.
        
        Kiểm tra rằng tất cả permission_ref trong params đều resolve được
        đến một permission đã được declare trong graph.
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            permission_ref = instance.params.get("permission_ref")
            if permission_ref:
                # Check permission_ref có tồn tại trong permissions không
                if permission_ref not in self._permissions:
                    error = ValidationError(
                        code=ErrorCode.UNRESOLVED_PERMISSION_REF.value,
                        message=(
                            f"Permission reference '{permission_ref}' trong instance "
                            f"'{instance.id}' không tìm thấy. "
                            f"Đã declare permissions: {', '.join(sorted(self._permissions)) if self._permissions else 'không có'}"
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "permission_ref": permission_ref,
                            "available_permissions": list(sorted(self._permissions)),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV002": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV002": ValidationStatus.FAIL.value},
        )
    
    def validate_role_refs(self) -> ValidationReport:
        """
        INV003: Role ref resolution - Kiểm tra role references.
        
        Kiểm tra rằng tất cả role_ref trong params đều resolve được
        đến một role đã được declare trong graph.
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            role_ref = instance.params.get("role_ref")
            if role_ref:
                # Check role_ref có tồn tại trong roles không
                if role_ref not in self._roles:
                    error = ValidationError(
                        code=ErrorCode.UNRESOLVED_ROLE_REF.value,
                        message=(
                            f"Role reference '{role_ref}' trong instance "
                            f"'{instance.id}' không tìm thấy. "
                            f"Đã declare roles: {', '.join(sorted(self._roles)) if self._roles else 'không có'}"
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "role_ref": role_ref,
                            "available_roles": list(sorted(self._roles)),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV003": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV003": ValidationStatus.FAIL.value},
        )
    
    def validate_command_permission_guards(self) -> ValidationReport:
        """
        INV004: Command permission guard - Kiểm tra commands có permission.
        
        Kiểm tra rằng tất cả mutation instances đều có permission guard
        (tức là có field "permission" trong params).
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            if instance.type in self.MUTATION_TYPES:
                # Check instance có permission field không
                if "permission" not in instance.params:
                    error = ValidationError(
                        code=ErrorCode.MISSING_PERMISSION_GUARD.value,
                        message=(
                            f"Mutation '{instance.id}' (type: {instance.type}) "
                            f"thiếu permission guard. "
                            f"Tất cả mutations phải có 'permission' field trong params."
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "instance_type": instance.type,
                            "current_params": list(instance.params.keys()),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV004": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV004": ValidationStatus.FAIL.value},
        )
    
    def validate_query_tenant_filters(self) -> ValidationReport:
        """
        INV005: Query tenant filter - Kiểm tra queries có tenant filter.
        
        Kiểm tra rằng tất cả query instances đều có tenant filter
        (tức là có field "tenant_filter" hoặc "tenant_scope" trong params).
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            if instance.type in self.QUERY_TYPES:
                # Check instance có tenant_filter hoặc tenant_scope không
                has_tenant_filter = "tenant_filter" in instance.params
                has_tenant_scope = "tenant_scope" in instance.params
                
                if not has_tenant_filter and not has_tenant_scope:
                    error = ValidationError(
                        code=ErrorCode.MISSING_TENANT_FILTER.value,
                        message=(
                            f"Query '{instance.id}' (type: {instance.type}) "
                            f"thiếu tenant filter. "
                            f"Tất cả queries phải có 'tenant_filter' hoặc 'tenant_scope' field trong params."
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "instance_type": instance.type,
                            "current_params": list(instance.params.keys()),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV005": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV005": ValidationStatus.FAIL.value},
        )
    
    def validate_mutation_transaction_scopes(self) -> ValidationReport:
        """
        INV006: Mutation transaction scope - Kiểm tra mutations có transaction.
        
        Kiểm tra rằng tất cả mutation instances đều có transaction scope
        (tức là có field "transaction" trong params).
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            if instance.type in self.MUTATION_TYPES:
                # Check instance có transaction field không
                if "transaction" not in instance.params:
                    error = ValidationError(
                        code=ErrorCode.MISSING_TRANSACTION_SCOPE.value,
                        message=(
                            f"Mutation '{instance.id}' (type: {instance.type}) "
                            f"thiếu transaction scope. "
                            f"Tất cả mutations phải có 'transaction' field trong params."
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "instance_type": instance.type,
                            "current_params": list(instance.params.keys()),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV006": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV006": ValidationStatus.FAIL.value},
        )
    
    def validate_role_policy_bindings(self) -> ValidationReport:
        """
        INV007: Role policy binding - Kiểm tra roles có policy binding.
        
        Kiểm tra rằng tất cả role instances đều có policy binding
        (tức là có field "policy_ref" trong params).
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            if instance.type in self.ROLE_TYPES:
                # Check instance có policy_ref field không
                if "policy_ref" not in instance.params:
                    error = ValidationError(
                        code=ErrorCode.MISSING_ROLE_POLICY.value,
                        message=(
                            f"Role '{instance.id}' thiếu policy binding. "
                            f"Tất cả roles phải có 'policy_ref' field trong params."
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "current_params": list(instance.params.keys()),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV007": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV007": ValidationStatus.FAIL.value},
        )
    
    def validate_policy_syntax(self) -> ValidationReport:
        """
        INV008: Policy syntax validation - Kiểm tra policy syntax.
        
        Kiểm tra rằng tất cả policy instances đều có syntax hợp lệ:
        - Phải có field "effect" với giá trị "allow" hoặc "deny"
        - Phải có field "subject"
        - Phải có field "action"
        
        Returns:
            ValidationReport với kết quả validation
        """
        errors: list[ValidationError] = []
        
        for instance in self.graph.instances:
            if instance.type in self.POLICY_TYPES:
                policy_errors: list[str] = []
                
                # Check effect field
                if "effect" not in instance.params:
                    policy_errors.append("thiếu field 'effect'")
                elif instance.params.get("effect") not in self.VALID_POLICY_EFFECTS:
                    policy_errors.append(
                        f"field 'effect' có giá trị không hợp lệ: "
                        f"'{instance.params.get('effect')}' (phải là 'allow' hoặc 'deny')"
                    )
                
                # Check subject field
                if "subject" not in instance.params:
                    policy_errors.append("thiếu field 'subject'")
                
                # Check action field
                if "action" not in instance.params:
                    policy_errors.append("thiếu field 'action'")
                
                if policy_errors:
                    error = ValidationError(
                        code=ErrorCode.INVALID_POLICY_SYNTAX.value,
                        message=(
                            f"Policy '{instance.id}' có syntax không hợp lệ: "
                            f"{'; '.join(policy_errors)}."
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "policy_errors": policy_errors,
                            "current_params": list(instance.params.keys()),
                            "valid_effects": list(self.VALID_POLICY_EFFECTS),
                        },
                    )
                    errors.append(error)
        
        if not errors:
            return ValidationReport(
                status=ValidationStatus.PASS.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                checks={"INV008": ValidationStatus.PASS.value},
            )
        
        return ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=errors,
            checks={"INV008": ValidationStatus.FAIL.value},
        )
    
    def validate_all(self) -> ValidationReport:
        """
        Chạy tất cả invariants INV001-INV008 và gộp results.
        
        Returns:
            ValidationReport với kết quả tất cả invariants
        """
        # Chạy tất cả validators
        reports = [
            self.validate_entity_refs(),       # INV001
            self.validate_permission_refs(),   # INV002
            self.validate_role_refs(),         # INV003
            self.validate_command_permission_guards(),  # INV004
            self.validate_query_tenant_filters(),       # INV005
            self.validate_mutation_transaction_scopes(), # INV006
            self.validate_role_policy_bindings(),       # INV007
            self.validate_policy_syntax(),      # INV008
        ]
        
        # Gộp tất cả errors
        all_errors: list[ValidationError] = []
        all_checks: dict[str, str] = {}
        
        for report in reports:
            all_errors.extend(report.errors)
            all_checks.update(report.checks)
        
        # Xác định status tổng thể
        if all_errors:
            status = ValidationStatus.FAIL.value
        else:
            status = ValidationStatus.PASS.value
        
        # Tạo tổng kết
        summary = {
            "total_invariants": 8,
            "passed_invariants": sum(
                1 for r in reports if r.status == ValidationStatus.PASS.value
            ),
            "failed_invariants": sum(
                1 for r in reports if r.status == ValidationStatus.FAIL.value
            ),
            "total_errors": len(all_errors),
            "critical_errors": sum(1 for e in all_errors if e.is_critical),
        }
        
        return ValidationReport(
            status=status,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            errors=all_errors,
            checks=all_checks,
            summary=summary,
        )
    
    # ========================================================================
    # Domain Invariants - Banking
    # ========================================================================
    
    def validate_banking_invariants(self) -> ValidationReport:
        """
        Validate Banking domain invariants.
        
        Banking invariants bao gồm:
        - FIN_DOUBLE_ENTRY_BALANCE: Double-entry phải balance (debit = credit)
        - FIN_KYC_VERIFIED: Giao dịch cần KYC phải verify
        
        Returns:
            ValidationReport với kết quả Banking invariants
        """
        errors: list[ValidationError] = []
        checks: dict[str, str] = {}
        
        # Validate double-entry balance
        double_entry_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "banking":
                continue
            
            double_entry = instance.params.get("double_entry")
            if double_entry and "entries" in double_entry:
                entries = double_entry["entries"]
                total_debit = sum(e.get("debit", 0) for e in entries)
                total_credit = sum(e.get("credit", 0) for e in entries)
                
                if total_debit != total_credit:
                    error = ValidationError(
                        code=ErrorCode.FIN_DOUBLE_ENTRY_IMBALANCE.value,
                        message=(
                            f"Double-entry trong instance '{instance.id}' không balance. "
                            f"Total debit: {total_debit}, Total credit: {total_credit}. "
                            f"Sai lệch: {abs(total_debit - total_credit)}"
                        ),
                        path=f"instances.{instance.id}",
                        source=self.graph.artifact_type,
                        context={
                            "instance_id": instance.id,
                            "total_debit": total_debit,
                            "total_credit": total_credit,
                            "imbalance": abs(total_debit - total_credit),
                        },
                    )
                    double_entry_errors.append(error)
        
        if double_entry_errors:
            errors.extend(double_entry_errors)
            checks["FIN_DOUBLE_ENTRY_BALANCE"] = ValidationStatus.FAIL.value
        else:
            checks["FIN_DOUBLE_ENTRY_BALANCE"] = ValidationStatus.PASS.value
        
        # Validate KYC verification
        kyc_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "banking":
                continue
            
            requires_kyc = instance.params.get("requires_kyc", False)
            kyc_verified = instance.params.get("kyc_verified", False)
            
            if requires_kyc and not kyc_verified:
                error = ValidationError(
                    code=ErrorCode.FIN_KYC_NOT_VERIFIED.value,
                    message=(
                        f"Giao dịch '{instance.id}' yêu cầu KYC nhưng chưa verify. "
                        f"Instance không thể thực hiện cho đến khi KYC được xác minh."
                    ),
                    path=f"instances.{instance.id}",
                    source=self.graph.artifact_type,
                    context={
                        "instance_id": instance.id,
                        "requires_kyc": requires_kyc,
                        "kyc_verified": kyc_verified,
                    },
                )
                kyc_errors.append(error)
        
        if kyc_errors:
            errors.extend(kyc_errors)
            checks["FIN_KYC_VERIFIED"] = ValidationStatus.FAIL.value
        else:
            checks["FIN_KYC_VERIFIED"] = ValidationStatus.PASS.value
        
        if errors:
            return ValidationReport(
                status=ValidationStatus.FAIL.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                errors=errors,
                checks=checks,
                summary={"domain": "banking", "total_errors": len(errors)},
            )
        
        return ValidationReport(
            status=ValidationStatus.PASS.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            checks=checks,
            summary={"domain": "banking", "total_errors": 0},
        )
    
    # ========================================================================
    # Domain Invariants - Healthcare
    # ========================================================================
    
    def validate_healthcare_invariants(self) -> ValidationReport:
        """
        Validate Healthcare domain invariants.
        
        Healthcare invariants bao gồm:
        - HLT_PHI_ENCRYPTED: PHI fields phải được encrypt
        - HLT_CLINICAL_AUDIT: Clinical actions phải có audit trail
        
        Returns:
            ValidationReport với kết quả Healthcare invariants
        """
        errors: list[ValidationError] = []
        checks: dict[str, str] = {}
        
        # Validate PHI encryption
        phi_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "healthcare":
                continue
            
            phi_fields = instance.params.get("phi_fields", [])
            encryption_enabled = instance.params.get("encryption_enabled", False)
            
            if phi_fields and not encryption_enabled:
                error = ValidationError(
                    code=ErrorCode.HLT_PHI_NOT_ENCRYPTED.value,
                    message=(
                        f"Instance '{instance.id}' chứa PHI fields nhưng không enable encryption. "
                        f"PHI fields: {phi_fields}. "
                        f"Vi phạm HIPAA compliance - PHI phải được encrypt."
                    ),
                    path=f"instances.{instance.id}",
                    source=self.graph.artifact_type,
                    context={
                        "instance_id": instance.id,
                        "phi_fields": phi_fields,
                        "encryption_enabled": encryption_enabled,
                    },
                )
                phi_errors.append(error)
        
        if phi_errors:
            errors.extend(phi_errors)
            checks["HLT_PHI_ENCRYPTED"] = ValidationStatus.FAIL.value
        else:
            checks["HLT_PHI_ENCRYPTED"] = ValidationStatus.PASS.value
        
        # Validate clinical audit trail
        audit_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "healthcare":
                continue
            
            clinical_action = instance.params.get("clinical_action", False)
            audit_trail_enabled = instance.params.get("audit_trail_enabled", False)
            
            if clinical_action and not audit_trail_enabled:
                error = ValidationError(
                    code=ErrorCode.HLT_MISSING_CLINICAL_AUDIT.value,
                    message=(
                        f"Clinical action '{instance.id}' không có audit trail. "
                        f"Tất cả clinical actions phải có audit trail cho compliance."
                    ),
                    path=f"instances.{instance.id}",
                    source=self.graph.artifact_type,
                    context={
                        "instance_id": instance.id,
                        "clinical_action": clinical_action,
                        "audit_trail_enabled": audit_trail_enabled,
                    },
                )
                audit_errors.append(error)
        
        if audit_errors:
            errors.extend(audit_errors)
            checks["HLT_CLINICAL_AUDIT"] = ValidationStatus.FAIL.value
        else:
            checks["HLT_CLINICAL_AUDIT"] = ValidationStatus.PASS.value
        
        if errors:
            return ValidationReport(
                status=ValidationStatus.FAIL.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                errors=errors,
                checks=checks,
                summary={"domain": "healthcare", "total_errors": len(errors)},
            )
        
        return ValidationReport(
            status=ValidationStatus.PASS.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            checks=checks,
            summary={"domain": "healthcare", "total_errors": 0},
        )
    
    # ========================================================================
    # Domain Invariants - Exchange
    # ========================================================================
    
    def validate_exchange_invariants(self) -> ValidationReport:
        """
        Validate Exchange domain invariants.
        
        Exchange invariants bao gồm:
        - EXC_ORDER_RISK_CHECK: Orders phải có risk check
        - EXC_SETTLEMENT_ATOMIC: Settlements phải atomic
        
        Returns:
            ValidationReport với kết quả Exchange invariants
        """
        errors: list[ValidationError] = []
        checks: dict[str, str] = {}
        
        # Validate order risk check
        risk_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "exchange":
                continue
            
            # Check if this is an order-related instance
            order_type = instance.params.get("order_type")
            risk_check_enabled = instance.params.get("risk_check_enabled", False)
            
            if order_type and not risk_check_enabled:
                error = ValidationError(
                    code=ErrorCode.EXC_ORDER_RISK_CHECK_MISSING.value,
                    message=(
                        f"Order '{instance.id}' (type: {order_type}) không có risk check. "
                        f"Tất cả orders phải có risk check trước khi execute."
                    ),
                    path=f"instances.{instance.id}",
                    source=self.graph.artifact_type,
                    context={
                        "instance_id": instance.id,
                        "order_type": order_type,
                        "risk_check_enabled": risk_check_enabled,
                    },
                )
                risk_errors.append(error)
        
        if risk_errors:
            errors.extend(risk_errors)
            checks["EXC_ORDER_RISK_CHECK"] = ValidationStatus.FAIL.value
        else:
            checks["EXC_ORDER_RISK_CHECK"] = ValidationStatus.PASS.value
        
        # Validate settlement atomicity
        atomic_errors: list[ValidationError] = []
        for instance in self.graph.instances:
            if instance.params.get("domain") != "exchange":
                continue
            
            settlement_type = instance.params.get("settlement_type")
            atomic_settlement = instance.params.get("atomic_settlement", False)
            transaction = instance.params.get("transaction", "")
            
            if settlement_type and not atomic_settlement:
                error = ValidationError(
                    code=ErrorCode.EXC_SETTLEMENT_NOT_ATOMIC.value,
                    message=(
                        f"Settlement '{instance.id}' (type: {settlement_type}) không atomic. "
                        f"Tất cả settlements phải có atomic transaction để đảm bảo integrity. "
                        f"Current transaction setting: {transaction}"
                    ),
                    path=f"instances.{instance.id}",
                    source=self.graph.artifact_type,
                    context={
                        "instance_id": instance.id,
                        "settlement_type": settlement_type,
                        "atomic_settlement": atomic_settlement,
                        "transaction": transaction,
                    },
                )
                atomic_errors.append(error)
        
        if atomic_errors:
            errors.extend(atomic_errors)
            checks["EXC_SETTLEMENT_ATOMIC"] = ValidationStatus.FAIL.value
        else:
            checks["EXC_SETTLEMENT_ATOMIC"] = ValidationStatus.PASS.value
        
        if errors:
            return ValidationReport(
                status=ValidationStatus.FAIL.value,
                artifact_type="capability_graph",
                artifact_ref=self.graph.artifact_type,
                errors=errors,
                checks=checks,
                summary={"domain": "exchange", "total_errors": len(errors)},
            )
        
        return ValidationReport(
            status=ValidationStatus.PASS.value,
            artifact_type="capability_graph",
            artifact_ref=self.graph.artifact_type,
            checks=checks,
            summary={"domain": "exchange", "total_errors": 0},
        )
