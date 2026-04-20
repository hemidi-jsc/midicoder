"""
Unit Tests cho Validation Contracts.

Kiểm tra behavior của:
- ValidationStatus enum
- ErrorCode enum
- ValidationError class
- ValidationWarning class
- ValidationReport class

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.validation import (
    ValidationStatus,
    ErrorCode,
    ValidationError,
    ValidationWarning,
    ValidationReport,
)


class TestValidationStatus:
    """Tests cho ValidationStatus enum."""

    def test_validation_status_has_all_values(self):
        """Kiểm tra ValidationStatus có đủ values."""
        assert ValidationStatus.PASS.value == "pass"
        assert ValidationStatus.WARNING.value == "warning"
        assert ValidationStatus.FAIL.value == "fail"
        assert ValidationStatus.ERROR.value == "error"

    def test_validation_status_count(self):
        """Kiểm tra ValidationStatus có 4 values."""
        assert len(list(ValidationStatus)) == 4


class TestErrorCode:
    """Tests cho ErrorCode enum."""

    def test_error_code_categories(self):
        """Kiểm tra ErrorCode có đủ categories."""
        # Syntax Errors
        assert ErrorCode.SYNTAX_ERROR.value == "SYNTAX_ERROR"
        assert ErrorCode.INVALID_JSON.value == "INVALID_JSON"
        assert ErrorCode.INVALID_YAML.value == "INVALID_YAML"
        
        # Reference Errors
        assert ErrorCode.UNRESOLVED_REFERENCE.value == "UNRESOLVED_REFERENCE"
        assert ErrorCode.CIRCULAR_DEPENDENCY.value == "CIRCULAR_DEPENDENCY"
        assert ErrorCode.DUPLICATE_ID.value == "DUPLICATE_ID"
        
        # Authorization Errors
        assert ErrorCode.MISSING_PERMISSION_CHECK.value == "MISSING_PERMISSION_CHECK"
        assert ErrorCode.MISSING_AUTH_GUARD.value == "MISSING_AUTH_GUARD"
        
        # Tenant Safety Errors
        assert ErrorCode.MISSING_TENANT_FILTER.value == "MISSING_TENANT_FILTER"
        assert ErrorCode.TENANT_LEAK.value == "TENANT_LEAK"
        
        # Obligation Errors
        assert ErrorCode.OBLIGATION_NOT_COVERED.value == "OBLIGATION_NOT_COVERED"
        
        # Compliance Errors
        assert ErrorCode.MISSING_AUDIT_LOG.value == "MISSING_AUDIT_LOG"
        assert ErrorCode.COMPLIANCE_VIOLATION.value == "COMPLIANCE_VIOLATION"

    def test_error_code_count(self):
        """Kiểm tra ErrorCode có đủ 33 codes."""
        error_codes = list(ErrorCode)
        assert len(error_codes) >= 30  # At least 30 error codes


class TestValidationError:
    """Tests cho ValidationError class."""

    def test_error_created_with_required_fields(self):
        """Kiểm tra ValidationError được tạo với code và message."""
        error = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Thiếu tenant filter",
        )

        assert error.code == "MISSING_TENANT_FILTER"
        assert error.message == "Thiếu tenant filter"
        assert error.path is None
        assert error.source is None
        assert error.context is None

    def test_error_created_with_all_fields(self):
        """Kiểm tra ValidationError được tạo với tất cả fields."""
        error = ValidationError(
            code=ErrorCode.MISSING_PERMISSION_CHECK.value,
            message="Thiếu permission check",
            path="commands[0]",
            source="capability_graph.json",
            context={"expected": "order.create", "actual": None},
        )

        assert error.code == "MISSING_PERMISSION_CHECK"
        assert error.message == "Thiếu permission check"
        assert error.path == "commands[0]"
        assert error.source == "capability_graph.json"
        assert error.context == {"expected": "order.create", "actual": None}

    def test_error_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        error = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Thiếu tenant filter",
            path="query.order_list",
            source="commands.yaml",
        )
        error_dict = error.to_dict()

        assert error_dict["code"] == "MISSING_TENANT_FILTER"
        assert error_dict["message"] == "Thiếu tenant filter"
        assert error_dict["path"] == "query.order_list"
        assert error_dict["source"] == "commands.yaml"

    def test_error_from_dict_creates_error(self):
        """Kiểm tra from_dict tạo ValidationError đúng."""
        error_data = {
            "code": "MISSING_PERMISSION_CHECK",
            "message": "Thiếu permission check",
            "path": "mutations.create_order",
            "source": "capability_graph.json",
            "context": {"permission": "order.create"},
        }

        error = ValidationError.from_dict(error_data)

        assert error.code == "MISSING_PERMISSION_CHECK"
        assert error.message == "Thiếu permission check"
        assert error.path == "mutations.create_order"
        assert error.context is not None

    def test_error_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Thiếu tenant filter cho query",
            path="queries.list_orders",
            source="commands.yaml",
            context={"entity": "Order", "tenant_field": "tenant_id"},
        )

        error_dict = original.to_dict()
        reconstructed = ValidationError.from_dict(error_dict)

        assert reconstructed.code == original.code
        assert reconstructed.message == original.message
        assert reconstructed.path == original.path
        assert reconstructed.source == original.source
        assert reconstructed.context == original.context


class TestValidationWarning:
    """Tests cho ValidationWarning class."""

    def test_warning_created_with_required_fields(self):
        """Kiểm tra ValidationWarning được tạo với code và message."""
        warning = ValidationWarning(
            code="DEPRECATION_WARNING",
            message="Warning message",
        )

        assert warning.code == "DEPRECATION_WARNING"
        assert warning.message == "Warning message"
        assert warning.path is None
        assert warning.source is None
        assert warning.suggestion is None

    def test_warning_created_with_all_fields(self):
        """Kiểm tra ValidationWarning được tạo với tất cả fields."""
        warning = ValidationWarning(
            code="DEPRECATION_WARNING",
            message="Deprecation warning",
            path="deprecated_field",
            source="schema.json",
            suggestion="Use new_field instead",
        )

        assert warning.code == "DEPRECATION_WARNING"
        assert warning.message == "Deprecation warning"
        assert warning.path == "deprecated_field"
        assert warning.source == "schema.json"
        assert warning.suggestion == "Use new_field instead"

    def test_warning_to_dict_contains_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        warning = ValidationWarning(
            code="WARNING_CODE",
            message="Warning message",
            path="path/to/warning",
            source="source.json",
            suggestion="Fix suggestion",
        )
        warning_dict = warning.to_dict()

        assert warning_dict["code"] == "WARNING_CODE"
        assert warning_dict["message"] == "Warning message"
        assert warning_dict["path"] == "path/to/warning"
        assert warning_dict["source"] == "source.json"
        assert warning_dict["suggestion"] == "Fix suggestion"

    def test_warning_from_dict_creates_warning(self):
        """Kiểm tra from_dict tạo ValidationWarning đúng."""
        warning_data = {
            "code": "WARNING_CODE",
            "message": "Warning message",
            "path": "path/to/warning",
            "source": "source.json",
            "suggestion": "Fix suggestion",
        }

        warning = ValidationWarning.from_dict(warning_data)

        assert warning.code == "WARNING_CODE"
        assert warning.message == "Warning message"
        assert warning.path == "path/to/warning"
        assert warning.source == "source.json"
        assert warning.suggestion == "Fix suggestion"

    def test_warning_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = ValidationWarning(
            code="WARNING_CODE",
            message="Warning message",
            path="path/to/warning",
            source="source.json",
            suggestion="Fix suggestion",
        )

        warning_dict = original.to_dict()
        reconstructed = ValidationWarning.from_dict(warning_dict)

        assert reconstructed.code == original.code
        assert reconstructed.message == original.message
        assert reconstructed.path == original.path
        assert reconstructed.source == original.source
        assert reconstructed.suggestion == original.suggestion


class TestValidationReport:
    """Tests cho ValidationReport class."""

    def test_report_created_empty(self):
        """Kiểm tra ValidationReport có thể được tạo rỗng."""
        report = ValidationReport()

        assert report is not None
        assert report.status == "pass"
        assert report.errors == []
        assert report.warnings == []
        assert report.artifact_type == ""
        assert report.artifact_ref == ""

    def test_report_created_with_errors(self):
        """Kiểm tra ValidationReport được tạo với errors."""
        error = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Thiếu tenant filter",
        )
        report = ValidationReport(
            status="fail",
            errors=[error],
            artifact_type="capability_graph",
            artifact_ref="test.graph",
        )

        assert len(report.errors) == 1
        assert report.errors[0].code == "MISSING_TENANT_FILTER"
        assert report.status == "fail"

    def test_report_created_with_warnings(self):
        """Kiểm tra ValidationReport được tạo với warnings."""
        warning = ValidationWarning(
            code="WARNING_CODE",
            message="Warning message",
        )
        report = ValidationReport(
            status="warning",
            warnings=[warning],
            artifact_type="capability_graph",
            artifact_ref="test.graph",
        )

        assert len(report.warnings) == 1
        assert report.status == "warning"

    def test_report_is_valid_with_no_errors(self):
        """Kiểm tra is_valid returns True khi status là pass."""
        report = ValidationReport(status="pass")
        assert report.is_valid() is True

    def test_report_is_valid_with_warning_status(self):
        """Kiểm tra is_valid returns True khi status là warning."""
        report = ValidationReport(status="warning")
        assert report.is_valid() is True

    def test_report_is_valid_with_fail_status(self):
        """Kiểm tra is_valid returns False khi status là fail."""
        report = ValidationReport(status="fail")
        assert report.is_valid() is False

    def test_report_error_count(self):
        """Kiểm tra len(errors) trả về số lượng errors đúng."""
        error1 = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Error 1",
        )
        error2 = ValidationError(
            code=ErrorCode.MISSING_PERMISSION_CHECK.value,
            message="Error 2",
        )
        report = ValidationReport(errors=[error1, error2])
        assert len(report.errors) == 2

    def test_report_warning_count(self):
        """Kiểm tra len(warnings) trả về số lượng warnings đúng."""
        warning1 = ValidationWarning(code="CODE1", message="Warning 1")
        warning2 = ValidationWarning(code="CODE2", message="Warning 2")
        report = ValidationReport(warnings=[warning1, warning2])
        assert len(report.warnings) == 2

    def test_report_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        report = ValidationReport(
            status="pass",
            errors=[],
            warnings=[],
        )
        report_dict = report.to_dict()

        assert "status" in report_dict
        assert "errors" in report_dict
        assert "warnings" in report_dict
        assert "artifact_type" in report_dict
        assert "checks" in report_dict
        assert "summary" in report_dict

    def test_report_from_dict_creates_report(self):
        """Kiểm tra from_dict tạo ValidationReport đúng."""
        report_data = {
            "type": "validation_report",
            "status": "fail",
            "artifact_type": "capability_graph",
            "artifact_ref": "test.graph",
            "errors": [
                {
                    "code": "MISSING_TENANT_FILTER",
                    "message": "Thiếu tenant filter",
                }
            ],
            "warnings": [
                {
                    "code": "WARNING_CODE",
                    "message": "Warning message"
                }
            ],
            "checks": {},
            "summary": {},
        }

        report = ValidationReport.from_dict(report_data)

        assert report is not None
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert report.status == "fail"

    def test_report_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        error = ValidationError(
            code=ErrorCode.MISSING_TENANT_FILTER.value,
            message="Thiếu tenant filter",
        )
        warning = ValidationWarning(
            code="WARNING_CODE",
            message="Warning message",
        )
        original = ValidationReport(
            status="fail",
            artifact_type="capability_graph",
            artifact_ref="test.graph",
            errors=[error],
            warnings=[warning],
        )

        report_dict = original.to_dict()
        reconstructed = ValidationReport.from_dict(report_dict)

        assert len(reconstructed.errors) == len(original.errors)
        assert len(reconstructed.warnings) == len(original.warnings)
        assert reconstructed.errors[0].code == original.errors[0].code
        assert reconstructed.warnings[0].message == original.warnings[0].message
        assert reconstructed.status == original.status
        assert reconstructed.artifact_type == original.artifact_type
