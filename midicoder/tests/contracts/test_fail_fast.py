"""
Tests cho Fail-Fast Logic - Epic E05 Task E05-007

Module này test logic fail-fast cho critical errors trong pipeline validation.

Theo SoT requirement.md lines 1664-1678:
- Critical errors làm compilation FAIL ngay lập tức
- Pipeline dừng khi có critical errors
- 7 loại critical error codes được định nghĩa

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.graph import (
    CapabilityGraph,
    CapabilityInstance,
    Obligation,
)
from midicoder.contracts.validation import (
    ValidationReport,
    ValidationError,
    ValidationStatus,
    ErrorCode,
    CRITICAL_ERROR_CODES,
    is_critical_error,
    has_critical_errors,
    raise_on_critical_errors,
    should_fail_fast,
)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def report_with_critical_errors() -> ValidationReport:
    """
    Tạo validation report với critical errors.
    
    Returns:
        ValidationReport có critical errors
    """
    report = ValidationReport(
        status=ValidationStatus.FAIL.value,
        artifact_type="capability_graph",
        artifact_ref="test_graph.json",
        errors=[
            ValidationError(
                code=ErrorCode.MISSING_PERMISSION_CHECK.value,
                message="Thiếu permission check",
                path="instances.create_order",
            ),
            ValidationError(
                code=ErrorCode.OBLIGATION_NOT_COVERED.value,
                message="Obligation chưa được satisfy",
                path="instances.delete_customer",
            ),
        ],
    )
    return report


@pytest.fixture
def report_with_non_critical_errors() -> ValidationReport:
    """
    Tạo validation report với non-critical errors.
    
    Returns:
        ValidationReport có non-critical errors
    """
    report = ValidationReport(
        status=ValidationStatus.FAIL.value,
        artifact_type="capability_graph",
        artifact_ref="test_graph.json",
        errors=[
            ValidationError(
                code=ErrorCode.SYNTAX_ERROR.value,
                message="Lỗi syntax",
                path="entities.order",
            ),
            ValidationError(
                code=ErrorCode.UNRESOLVED_REFERENCE.value,
                message="Reference không tìm thấy",
                path="commands.get_order",
            ),
        ],
    )
    return report


@pytest.fixture
def report_with_mixed_errors() -> ValidationReport:
    """
    Tạo validation report với mixed critical/non-critical errors.
    
    Returns:
        ValidationReport có cả critical và non-critical errors
    """
    report = ValidationReport(
        status=ValidationStatus.FAIL.value,
        artifact_type="capability_graph",
        artifact_ref="test_graph.json",
        errors=[
            ValidationError(
                code=ErrorCode.SYNTAX_ERROR.value,
                message="Lỗi syntax",
                path="entities.order",
            ),
            ValidationError(
                code=ErrorCode.MISSING_TENANT_FILTER.value,
                message="Thiếu tenant filter",
                path="instances.create_order",
            ),
            ValidationError(
                code=ErrorCode.UNRESOLVED_REFERENCE.value,
                message="Reference không tìm thấy",
                path="commands.get_order",
            ),
        ],
    )
    return report


@pytest.fixture
def report_pass() -> ValidationReport:
    """
    Tạo validation report pass.
    
    Returns:
        ValidationReport với status PASS
    """
    return ValidationReport(
        status=ValidationStatus.PASS.value,
        artifact_type="capability_graph",
        artifact_ref="test_graph.json",
        errors=[],
    )


@pytest.fixture
def all_critical_error_codes() -> list[str]:
    """
    Danh sách tất cả critical error codes.
    
    Returns:
        List chứa 7 critical error codes
    """
    return [
        ErrorCode.MISSING_PERMISSION_CHECK.value,
        ErrorCode.MISSING_TENANT_FILTER.value,
        ErrorCode.MISSING_TRANSACTION.value,
        ErrorCode.OBLIGATION_NOT_COVERED.value,
        ErrorCode.TENANT_LEAK.value,
        ErrorCode.PII_EXPOSURE.value,
        ErrorCode.COMPLIANCE_VIOLATION.value,
    ]


# ============================================================================
# Test CRITICAL_ERROR_CODES Constant
# ============================================================================

class TestCriticalErrorCodes:
    """Tests cho constant CRITICAL_ERROR_CODES."""

    def test_contains_all_critical_codes(self, all_critical_error_codes: list[str]) -> None:
        """
        Test: CRITICAL_ERROR_CODES chứa đủ 7 critical error codes.
        
        Case: Kiểm tra constant
        Expected: Có đủ 7 codes
        """
        assert len(CRITICAL_ERROR_CODES) == 7
        
        for code in all_critical_error_codes:
            assert code in CRITICAL_ERROR_CODES

    def test_missing_permission_check_is_critical(self) -> None:
        """
        Test: MISSING_PERMISSION_CHECK là critical.
        """
        assert ErrorCode.MISSING_PERMISSION_CHECK.value in CRITICAL_ERROR_CODES

    def test_missing_tenant_filter_is_critical(self) -> None:
        """
        Test: MISSING_TENANT_FILTER là critical.
        """
        assert ErrorCode.MISSING_TENANT_FILTER.value in CRITICAL_ERROR_CODES

    def test_missing_transaction_is_critical(self) -> None:
        """
        Test: MISSING_TRANSACTION là critical.
        """
        assert ErrorCode.MISSING_TRANSACTION.value in CRITICAL_ERROR_CODES

    def test_obligation_not_covered_is_critical(self) -> None:
        """
        Test: OBLIGATION_NOT_COVERED là critical.
        """
        assert ErrorCode.OBLIGATION_NOT_COVERED.value in CRITICAL_ERROR_CODES

    def test_tenant_leak_is_critical(self) -> None:
        """
        Test: TENANT_LEAK là critical.
        """
        assert ErrorCode.TENANT_LEAK.value in CRITICAL_ERROR_CODES

    def test_pii_exposure_is_critical(self) -> None:
        """
        Test: PII_EXPOSURE là critical.
        """
        assert ErrorCode.PII_EXPOSURE.value in CRITICAL_ERROR_CODES

    def test_compliance_violation_is_critical(self) -> None:
        """
        Test: COMPLIANCE_VIOLATION là critical.
        """
        assert ErrorCode.COMPLIANCE_VIOLATION.value in CRITICAL_ERROR_CODES

    def test_syntax_error_not_critical(self) -> None:
        """
        Test: SYNTAX_ERROR không phải critical.
        """
        assert ErrorCode.SYNTAX_ERROR.value not in CRITICAL_ERROR_CODES

    def test_unresolved_reference_not_critical(self) -> None:
        """
        Test: UNRESOLVED_REFERENCE không phải critical.
        """
        assert ErrorCode.UNRESOLVED_REFERENCE.value not in CRITICAL_ERROR_CODES


# ============================================================================
# Test is_critical_error
# ============================================================================

class TestIsCriticalError:
    """Tests cho hàm is_critical_error."""

    def test_returns_true_for_permission_check_error(self) -> None:
        """
        Test: Trả về True cho MISSING_PERMISSION_CHECK.
        """
        assert is_critical_error(ErrorCode.MISSING_PERMISSION_CHECK.value) is True

    def test_returns_true_for_tenant_filter_error(self) -> None:
        """
        Test: Trả về True cho MISSING_TENANT_FILTER.
        """
        assert is_critical_error(ErrorCode.MISSING_TENANT_FILTER.value) is True

    def test_returns_false_for_syntax_error(self) -> None:
        """
        Test: Trả về False cho SYNTAX_ERROR.
        """
        assert is_critical_error(ErrorCode.SYNTAX_ERROR.value) is False

    def test_returns_false_for_unknown_code(self) -> None:
        """
        Test: Trả về False cho code không rõ.
        """
        assert is_critical_error("UNKNOWN_ERROR_CODE") is False

    def test_returns_false_for_empty_string(self) -> None:
        """
        Test: Trả về False cho string rỗng.
        """
        assert is_critical_error("") is False


# ============================================================================
# Test has_critical_errors
# ============================================================================

class TestHasCriticalErrors:
    """Tests cho hàm has_critical_errors."""

    def test_returns_true_for_report_with_critical_errors(
        self,
        report_with_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về True khi report có critical errors.
        
        Case: Report có 2 critical errors
        Expected: True
        """
        assert has_critical_errors(report_with_critical_errors) is True

    def test_returns_false_for_report_with_non_critical_errors(
        self,
        report_with_non_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về False khi report chỉ có non-critical errors.
        
        Case: Report có 2 non-critical errors
        Expected: False
        """
        assert has_critical_errors(report_with_non_critical_errors) is False

    def test_returns_true_for_report_with_mixed_errors(
        self,
        report_with_mixed_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về True khi report có ít nhất 1 critical error.
        
        Case: Report có 1 critical + 2 non-critical errors
        Expected: True
        """
        assert has_critical_errors(report_with_mixed_errors) is True

    def test_returns_false_for_pass_report(self, report_pass: ValidationReport) -> None:
        """
        Test: Trả về False khi report pass.
        
        Case: Report không có errors
        Expected: False
        """
        assert has_critical_errors(report_pass) is False

    def test_returns_false_for_warning_only_report(self) -> None:
        """
        Test: Trả về False khi report chỉ có warnings.
        
        Case: Report với status WARNING và không có errors
        Expected: False
        """
        report = ValidationReport(
            status=ValidationStatus.WARNING.value,
            artifact_type="capability_graph",
            artifact_ref="test.json",
            errors=[],
        )
        assert has_critical_errors(report) is False


# ============================================================================
# Test get_critical_errors (helper function)
# ============================================================================

class TestGetCriticalErrors:
    """Tests cho hàm get_critical_errors."""

    def test_returns_only_critical_errors(
        self,
        report_with_mixed_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về chỉ critical errors.
        
        Case: Report có 3 errors (1 critical, 2 non-critical)
        Expected: Chỉ trả về 1 critical error
        """
        from midicoder.contracts.validation import get_critical_errors
        
        critical = get_critical_errors(report_with_mixed_errors)
        assert len(critical) == 1
        assert critical[0].code == ErrorCode.MISSING_TENANT_FILTER.value

    def test_returns_empty_for_no_critical_errors(
        self,
        report_with_non_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về empty list khi không có critical errors.
        """
        from midicoder.contracts.validation import get_critical_errors
        
        critical = get_critical_errors(report_with_non_critical_errors)
        assert len(critical) == 0

    def test_returns_all_when_all_critical(
        self,
        report_with_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về tất cả khi tất cả đều critical.
        """
        from midicoder.contracts.validation import get_critical_errors
        
        critical = get_critical_errors(report_with_critical_errors)
        assert len(critical) == 2


# ============================================================================
# Test should_fail_fast
# ============================================================================

class TestShouldFailFast:
    """Tests cho hàm should_fail_fast."""

    def test_returns_true_when_has_critical_errors(
        self,
        report_with_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về True khi có critical errors.
        
        Case: Report có critical errors
        Expected: True - pipeline nên dừng
        """
        assert should_fail_fast(report_with_critical_errors) is True

    def test_returns_false_when_no_critical_errors(
        self,
        report_with_non_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Trả về False khi không có critical errors.
        
        Case: Report chỉ có non-critical errors
        Expected: False - pipeline có thể tiếp tục
        """
        assert should_fail_fast(report_with_non_critical_errors) is False

    def test_returns_false_for_pass_report(self, report_pass: ValidationReport) -> None:
        """
        Test: Trả về False khi report pass.
        """
        assert should_fail_fast(report_pass) is False


# ============================================================================
# Test raise_on_critical_errors
# ============================================================================

class TestRaiseOnCriticalErrors:
    """Tests cho hàm raise_on_critical_errors."""

    def test_raises_exception_for_critical_errors(
        self,
        report_with_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Ném exception khi có critical errors.
        
        Case: Report có critical errors
        Expected: ValidationException được raise
        """
        from midicoder.contracts.validation import ValidationException
        
        with pytest.raises(ValidationException) as exc_info:
            raise_on_critical_errors(report_with_critical_errors)
        
        # Kiểm tra exception message
        assert "critical error" in str(exc_info.value).lower()
        assert "MISSING_PERMISSION_CHECK" in str(exc_info.value)

    def test_does_not_raise_for_non_critical_errors(
        self,
        report_with_non_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Không ném exception khi chỉ có non-critical errors.
        
        Case: Report có non-critical errors
        Expected: Không có exception
        """
        # Should not raise
        raise_on_critical_errors(report_with_non_critical_errors)

    def test_does_not_raise_for_pass_report(self, report_pass: ValidationReport) -> None:
        """
        Test: Không ném exception khi report pass.
        """
        raise_on_critical_errors(report_pass)

    def test_exception_message_includes_error_codes(
        self,
        report_with_critical_errors: ValidationReport,
    ) -> None:
        """
        Test: Exception message chứa error codes.
        
        Case: Report có 2 critical errors
        Expected: Message chứa cả 2 error codes
        """
        from midicoder.contracts.validation import ValidationException
        
        with pytest.raises(ValidationException) as exc_info:
            raise_on_critical_errors(report_with_critical_errors)
        
        error_str = str(exc_info.value)
        assert "MISSING_PERMISSION_CHECK" in error_str
        assert "OBLIGATION_NOT_COVERED" in error_str


# ============================================================================
# Integration Tests
# ============================================================================

class TestFailFastIntegration:
    """Integration tests cho fail-fast logic."""

    def test_full_pipeline_with_critical_error(self) -> None:
        """
        Test: Full pipeline với critical error.
        
        Case: 
        1. Tạo report với critical error
        2. Check should_fail_fast
        3. Call raise_on_critical_errors
        
        Expected: Pipeline dừng, exception được raise
        """
        from midicoder.contracts.validation import (
            ValidationException,
            get_critical_errors,
        )
        
        # Step 1: Tạo report với critical error
        report = ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref="pipeline_test.json",
            errors=[
                ValidationError(
                    code=ErrorCode.MISSING_TENANT_FILTER.value,
                    message="Thiếu tenant filter",
                    path="instances.create_order",
                ),
            ],
        )
        
        # Step 2: Check should_fail_fast
        assert should_fail_fast(report) is True
        
        # Step 3: Get critical errors
        critical = get_critical_errors(report)
        assert len(critical) == 1
        
        # Step 4: Raise exception
        with pytest.raises(ValidationException):
            raise_on_critical_errors(report)

    def test_pipeline_continues_with_warnings(self) -> None:
        """
        Test: Pipeline tiếp tục với warnings.
        
        Case: Report với status WARNING
        Expected: should_fail_fast = False, không raise
        """
        report = ValidationReport(
            status=ValidationStatus.WARNING.value,
            artifact_type="capability_graph",
            artifact_ref="warning_test.json",
            errors=[],
        )
        
        assert should_fail_fast(report) is False
        # Should not raise
        raise_on_critical_errors(report)

    def test_multiple_critical_errors_stops_pipeline(self) -> None:
        """
        Test: Nhiều critical errors vẫn stop pipeline.
        
        Case: Report với 5+ critical errors
        Expected: Pipeline dừng, exception list tất cả
        """
        from midicoder.contracts.validation import ValidationException
        
        errors = [
            ValidationError(
                code=code,
                message=f"Lỗi {code}",
                path=f"instance_{i}",
            )
            for i, code in enumerate([
                ErrorCode.MISSING_PERMISSION_CHECK.value,
                ErrorCode.MISSING_TENANT_FILTER.value,
                ErrorCode.MISSING_TRANSACTION.value,
                ErrorCode.TENANT_LEAK.value,
                ErrorCode.PII_EXPOSURE.value,
            ])
        ]
        
        report = ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref="multi_critical.json",
            errors=errors,
        )
        
        assert should_fail_fast(report) is True
        
        with pytest.raises(ValidationException) as exc_info:
            raise_on_critical_errors(report)
        
        # Kiểm tra exception message có nhiều errors
        assert "5 critical error" in str(exc_info.value)


# ============================================================================
# Edge Cases
# ============================================================================

class TestFailFastEdgeCases:
    """Tests cho edge cases."""

    def test_empty_report(self) -> None:
        """
        Test: Empty report.
        
        Case: Report mới tạo không có errors
        Expected: should_fail_fast = False
        """
        report = ValidationReport()
        assert should_fail_fast(report) is False
        raise_on_critical_errors(report)  # Should not raise

    def test_only_warnings_no_errors(self) -> None:
        """
        Test: Chỉ có warnings không có errors.
        
        Case: Report với warnings nhưng không có errors
        Expected: should_fail_fast = False
        """
        from midicoder.contracts.validation import ValidationWarning
        
        report = ValidationReport(
            status=ValidationStatus.WARNING.value,
            artifact_type="capability_graph",
            artifact_ref="warnings_only.json",
            errors=[],
            warnings=[
                ValidationWarning(
                    code="MISSING_DESCRIPTION",
                    message="Nên có description",
                ),
            ],
        )
        
        assert should_fail_fast(report) is False
        raise_on_critical_errors(report)  # Should not raise

    def test_critical_error_with_none_message(self) -> None:
        """
        Test: Critical error với message None.
        
        Case: ValidationError không có message
        Expected: Vẫn là critical, exception vẫn raise
        """
        from midicoder.contracts.validation import ValidationException
        
        report = ValidationReport(
            status=ValidationStatus.FAIL.value,
            artifact_type="capability_graph",
            artifact_ref="edge_case.json",
            errors=[
                ValidationError(
                    code=ErrorCode.MISSING_PERMISSION_CHECK.value,
                    message="",
                ),
            ],
        )
        
        assert has_critical_errors(report) is True
        assert should_fail_fast(report) is True
        
        with pytest.raises(ValidationException):
            raise_on_critical_errors(report)