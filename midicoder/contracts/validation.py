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
        """Create from dictionary."""
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
        critical_codes = {
            ErrorCode.MISSING_PERMISSION_CHECK.value,
            ErrorCode.MISSING_TENANT_FILTER.value,
            ErrorCode.MISSING_TRANSACTION.value,
            ErrorCode.OBLIGATION_NOT_COVERED.value,
            ErrorCode.TENANT_LEAK.value,
            ErrorCode.PII_EXPOSURE.value,
            ErrorCode.COMPLIANCE_VIOLATION.value,
        }
        return self.code in critical_codes


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
        """Create from dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            path=data.get("path"),
            source=data.get("source"),
            suggestion=data.get("suggestion"),
        )


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
        
    Example:
        report = ValidationReport(
            status=ValidationStatus.FAIL,
            artifact_type="capability_graph",
            artifact_ref="contracts/graph.json",
            errors=[
                ValidationError(
                    code=ErrorCode.MISSING_TENANT_FILTER,
                    message="Command thiếu tenant filter",
                    path="instances.create_order",
                ),
            ],
            warnings=[],
            checks={
                "syntax": ValidationStatus.PASS,
                "references": ValidationStatus.PASS,
                "obligations": ValidationStatus.FAIL,
            },
            metadata=ArtifactMetadata.with_timestamp(...),
        )
    """
    status: str = "pass"  # Use string for flexibility
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
        """Create from dictionary."""
        metadata = ArtifactMetadata.from_dict(data.get("metadata", {}))
        
        return cls(
            metadata=metadata,
            status=data["status"],
            artifact_type=data["artifact_type"],
            artifact_ref=data["artifact_ref"],
            errors=[ValidationError.from_dict(e) for e in data.get("errors", [])],
            warnings=[ValidationWarning.from_dict(w) for w in data.get("warnings", [])],
            checks=data.get("checks", {}),
            summary=data.get("summary", {}),
        )
    
    # =========================================================================
    # Factory Methods
    # =========================================================================
    
    @classmethod
    def pass_(
        cls,
        artifact_type: str,
        artifact_ref: str,
        metadata: ArtifactMetadata | None = None,
    ) -> "ValidationReport":
        """
        Tạo validation report với status PASS.
        
        Args:
            artifact_type: Loại artifact
            artifact_ref: Reference vào artifact
            metadata: Artifact metadata
            
        Returns:
            ValidationReport với status PASS
        """
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
        """
        Tạo validation report với status FAIL.
        
        Args:
            artifact_type: Loại artifact
            artifact_ref: Reference vào artifact
            errors: Danh sách errors
            metadata: Artifact metadata
            
        Returns:
            ValidationReport với status FAIL
        """
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
        """
        Tạo validation report với status WARNING.
        
        Args:
            artifact_type: Loại artifact
            artifact_ref: Reference vào artifact
            warnings: Danh sách warnings
            metadata: Artifact metadata
            
        Returns:
            ValidationReport với status WARNING
        """
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
    
    # =========================================================================
    # Error Management
    # =========================================================================
    
    def add_error(
        self,
        code: str,
        message: str,
        path: str | None = None,
        source: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Thêm validation error.
        
        Args:
            code: Error code
            message: Error message
            path: Path đến element lỗi
            source: Source artifact/file
            context: Additional context
        """
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
        """
        Thêm validation warning.
        
        Args:
            code: Warning code
            message: Warning message
            path: Path đến element
            source: Source artifact/file
            suggestion: Gợi ý fix
        """
        warning = ValidationWarning(
            code=code,
            message=message,
            path=path,
            source=source,
            suggestion=suggestion,
        )
        self.warnings.append(warning)
        
        # Only set WARNING if not already FAILED
        if self.status == ValidationStatus.PASS.value:
            self.status = ValidationStatus.WARNING.value
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def get_errors_by_code(self, code: str) -> list[ValidationError]:
        """Lấy errors theo code."""
        return [e for e in self.errors if e.code == code]
    
    def get_critical_errors(self) -> list[ValidationError]:
        """Lấy critical errors."""
        return [e for e in self.errors if e.is_critical]
    
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
    
    # =========================================================================
    # Summary Generation
    # =========================================================================
    
    def generate_summary(self) -> None:
        """Generate summary từ errors và warnings."""
        self.summary = {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "critical_errors": sum(1 for e in self.errors if e.is_critical),
            "error_codes": list(set(e.code for e in self.errors)),
            "warning_codes": list(set(w.code for w in self.warnings)),
        }
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self) -> list[str]:
        """
        Validate validation report.
        
        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        errors = super().validate()
        
        # Check required fields
        if not self.artifact_type:
            errors.append("ValidationReport.artifact_type is required")
        
        if not self.artifact_ref:
            errors.append("ValidationReport.artifact_ref is required")
        
        # Check status consistency
        if self.errors and self.status == ValidationStatus.PASS.value:
            errors.append("Report has errors but status is PASS")
        
        return errors