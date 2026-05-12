"""
Tests cho Command Compliance Guards và RX Validation.

Test coverage:
- RX02: Financial Integrity (double-entry, immutability)
- RX03: AML/KYC compliance
- RX04: HIPAA compliance
- Tenant-aware guards (KPI-029)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from midicoder.emitters.core.domain_model.command_models import Command, CommandGuard, GuardType
from midicoder.emitters.core.domain_model.command_guards import CommandGuards
from midicoder.emitters.core.domain_model.command_validator import CommandValidator
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_compliance_service():
    """Mock compliance service."""
    service = AsyncMock()
    service.check_kyc = AsyncMock(return_value=True)
    service.check_aml = AsyncMock(return_value=True)
    service.check_hipaa_clearance = AsyncMock(return_value=True)
    service.log_compliance_check = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_tenant_service():
    """Mock tenant service."""
    service = AsyncMock()
    service.belongs_to_tenant = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_auth_service():
    """Mock auth service."""
    service = AsyncMock()
    service.check_permission = AsyncMock(return_value=True)
    service.check_rate_limit = AsyncMock(return_value=False)
    return service


@pytest.fixture
def banking_command(mock_compliance_service):
    """Banking command with KYC and AML guards."""
    command = Command(
        id="TransferFunds",
        description="Chuyển tiền giữa các tài khoản",
        category="write",
        tenant_scope="tenant_isolated",
        input=[],
        returns=[],
        effects=[],
        guards=[
            CommandGuard(guard_type=GuardType.KYC_CHECK),
            CommandGuard(guard_type=GuardType.AML_SCREENING),
        ],
    )
    return CommandGuards(
        command=command,
        auth_service=AsyncMock(),
        tenant_service=AsyncMock(),
        compliance_service=mock_compliance_service,
    )


@pytest.fixture
def healthcare_command(mock_compliance_service):
    """Healthcare command with HIPAA guard."""
    command = Command(
        id="WriteClinicalNote",
        description="Viết ghi chú y khoa",
        category="write",
        tenant_scope="tenant_isolated",
        input=[],
        returns=[],
        effects=[],
        guards=[
            CommandGuard(guard_type=GuardType.HIPAA_ACCESS),
        ],
    )
    return CommandGuards(
        command=command,
        auth_service=AsyncMock(),
        tenant_service=AsyncMock(),
        compliance_service=mock_compliance_service,
    )


@pytest.fixture
def validator_command():
    """Command cho validator tests."""
    return Command(
        id="TestCommand",
        description="Test command",
        category="write",
        tenant_scope="tenant_isolated",
        input=[],
        returns=[],
        effects=[],
        guards=[],
    )


# ============================================================================
# RX02: Financial Integrity Tests
# ============================================================================

class TestRX02FinancialIntegrity:
    """Tests cho RX02 Financial Integrity validation."""

    @pytest.mark.asyncio
    async def test_validate_double_entry_balanced(self, validator_command):
        """Test double-entry validation với debit = credit."""
        validator = CommandValidator(validator_command)
        data = {"debit": 1000000, "credit": 1000000}

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_double_entry_imbalanced(self, validator_command):
        """Test double-entry validation với debit != credit."""
        validator = CommandValidator(validator_command)
        data = {"debit": 1000000, "credit": 500000}

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "double-entry" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_double_entry_with_tolerance(self, validator_command):
        """Test double-entry validation với rounding tolerance."""
        validator = CommandValidator(validator_command)
        data = {"debit": 1000000, "credit": 1000000.009}  # < 0.01 difference

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert result.is_valid  # Should pass due to tolerance (< 0.01)

    @pytest.mark.asyncio
    async def test_validate_transaction_immutability_completed(self, validator_command):
        """Test transaction immutability cho completed transaction."""
        validator = CommandValidator(validator_command)
        data = {"status": "completed", "is_update": True}

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "immu" in result.errors[0].lower()  # Contains "immutability"

    @pytest.mark.asyncio
    async def test_validate_transaction_immutability_pending(self, validator_command):
        """Test transaction immutability cho pending transaction."""
        validator = CommandValidator(validator_command)
        data = {"status": "pending", "is_update": True}

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert result.is_valid  # Pending transactions can be updated

    @pytest.mark.asyncio
    async def test_validate_rx02_tenant_aware(self, validator_command):
        """Test RX02 validation với tenant context."""
        validator = CommandValidator(validator_command)
        data = {"debit": 1000000, "credit": 1000000}

        result = await validator.validate_rx02(data, tenant_id="tenant_1")

        assert result.is_valid
        # Tenant context should be available for audit logging


# ============================================================================
# RX03: AML/KYC Compliance Tests
# ============================================================================

class TestRX03AMLKYC:
    """Tests cho RX03 AML/KYC validation."""

    @pytest.mark.asyncio
    async def test_validate_kyc_verified(self, validator_command):
        """Test KYC verification với verified user."""
        validator = CommandValidator(validator_command)
        data = {
            "kyc_verified": True,
            "aml_cleared": True,  # Also need AML cleared
            "amount": 50000000
        }

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_kyc_not_verified(self, validator_command):
        """Test KYC verification với unverified user."""
        validator = CommandValidator(validator_command)
        data = {"kyc_verified": False, "amount": 50000000}

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert not result.is_valid
        assert len(result.errors) >= 1
        assert any("kyc" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_aml_cleared(self, validator_command):
        """Test AML screening với cleared transaction."""
        validator = CommandValidator(validator_command)
        data = {"kyc_verified": True, "aml_cleared": True, "amount": 50000000}

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_aml_not_cleared(self, validator_command):
        """Test AML screening với uncleared transaction."""
        validator = CommandValidator(validator_command)
        data = {"kyc_verified": True, "aml_cleared": False, "amount": 50000000}

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert not result.is_valid
        assert any("aml" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_suspicious_activity_above_threshold(self, validator_command):
        """Test suspicious activity detection với amount > threshold."""
        validator = CommandValidator(validator_command)
        data = {
            "kyc_verified": True,
            "aml_cleared": True,
            "amount": 150000000,  # 150 triệu > 100 triệu threshold
        }

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        # Should be valid but with warning
        assert result.is_valid
        assert len(result.warnings) >= 1
        assert any("SAR" in warning or "threshold" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_suspicious_activity_below_threshold(self, validator_command):
        """Test suspicious activity detection với amount < threshold."""
        validator = CommandValidator(validator_command)
        data = {
            "kyc_verified": True,
            "aml_cleared": True,
            "amount": 50000000,  # 50 triệu < 100 triệu threshold
        }

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_rx03_tenant_aware(self, validator_command):
        """Test RX03 validation với tenant context."""
        validator = CommandValidator(validator_command)
        data = {"kyc_verified": True, "aml_cleared": True, "amount": 50000000}

        result = await validator.validate_rx03(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid


# ============================================================================
# RX04: HIPAA Compliance Tests
# ============================================================================

class TestRX04HIPAA:
    """Tests cho RX04 HIPAA compliance validation."""

    @pytest.mark.asyncio
    async def test_validate_phi_encrypted(self, validator_command):
        """Test PHI encryption với encrypted fields."""
        validator = CommandValidator(validator_command)
        data = {
            "ssn": "123-45-6789",
            "ssn_encrypted": True,
            "full_name": "John Doe",
            "full_name_encrypted": True,
            "audit_log_written": True,
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_phi_not_encrypted(self, validator_command):
        """Test PHI encryption với unencrypted fields."""
        validator = CommandValidator(validator_command)
        data = {
            "ssn": "123-45-6789",
            "ssn_encrypted": False,  # Not encrypted!
            "audit_log_written": True,
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert not result.is_valid
        assert any("encrypt" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_minimum_necessary_access_allowed(self, validator_command):
        """Test minimum necessary access với allowed fields."""
        validator = CommandValidator(validator_command)
        data = {
            "requested_phi_fields": ["ssn", "full_name"],
            "user_allowed_fields": ["ssn", "full_name", "date_of_birth"],
            "audit_log_written": True,
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_minimum_necessary_access_denied(self, validator_command):
        """Test minimum necessary access với denied fields."""
        validator = CommandValidator(validator_command)
        data = {
            "requested_phi_fields": ["ssn", "medical_history", "genetic_data"],
            "user_allowed_fields": ["ssn", "full_name"],  # Not allowed to access medical_history
            "audit_log_written": True,
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert not result.is_valid
        assert any("phi" in error.lower() or "access" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_audit_trail_written(self, validator_command):
        """Test audit trail với log written."""
        validator = CommandValidator(validator_command)
        data = {
            "ssn": "123-45-6789",
            "ssn_encrypted": True,
            "audit_log_written": True,
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_audit_trail_missing(self, validator_command):
        """Test audit trail với log missing."""
        validator = CommandValidator(validator_command)
        data = {
            "ssn": "123-45-6789",
            "ssn_encrypted": True,
            "audit_log_written": False,  # Missing audit log!
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert not result.is_valid
        assert any("audit" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_rx04_tenant_aware(self, validator_command):
        """Test RX04 validation với tenant context."""
        validator = CommandValidator(validator_command)
        data = {
            "ssn": "123-45-6789",
            "ssn_encrypted": True,
            "audit_log_written": True,
            "requested_phi_fields": ["ssn"],
            "user_allowed_fields": ["ssn", "full_name"],
        }

        result = await validator.validate_rx04(data, user_id="user_1", tenant_id="tenant_1")

        assert result.is_valid


# ============================================================================
# Tenant-Aware Guards Tests (KPI-029)
# ============================================================================

class TestTenantAwareGuards:
    """Tests cho tenant-aware compliance guards."""

    @pytest.mark.asyncio
    async def test_check_kyc_with_audit_tenant_isolated(
        self,
        banking_command,
        mock_compliance_service,
    ):
        """Test KYC check với audit logging và tenant isolation."""
        data = {"amount": 50000000}

        # Should pass with tenant_id
        await banking_command._check_kyc_with_audit(
            guard=banking_command._command.guards[0],
            user_id="user_1",
            tenant_id="tenant_1",
        )

        # Verify compliance service was called with tenant_id
        mock_compliance_service.check_kyc.assert_called_once()
        call_kwargs = mock_compliance_service.check_kyc.call_args.kwargs
        assert call_kwargs.get("tenant_id") == "tenant_1"

    @pytest.mark.asyncio
    async def test_check_kyc_with_audit_kyc_failed(
        self,
        banking_command,
        mock_compliance_service,
    ):
        """Test KYC check failed với audit logging."""
        mock_compliance_service.check_kyc = AsyncMock(return_value=False)

        with pytest.raises(MidicoderError) as exc_info:
            await banking_command._check_kyc_with_audit(
                guard=banking_command._command.guards[0],
                user_id="user_1",
                tenant_id="tenant_1",
            )

        assert exc_info.value.code == ErrorCode.CP01_GUARD_KYC_NOT_VERIFIED

    @pytest.mark.asyncio
    async def test_check_aml_with_audit_tenant_isolated(
        self,
        banking_command,
        mock_compliance_service,
    ):
        """Test AML check với audit logging và tenant isolation."""
        data = {"amount": 50000000}

        await banking_command._check_aml_with_audit(
            guard=banking_command._command.guards[1],
            data=data,
            user_id="user_1",
            tenant_id="tenant_1",
        )

        # Verify compliance service was called with tenant_id
        mock_compliance_service.check_aml.assert_called_once()
        call_kwargs = mock_compliance_service.check_aml.call_args.kwargs
        assert call_kwargs.get("tenant_id") == "tenant_1"

    @pytest.mark.asyncio
    async def test_check_hipaa_with_audit_tenant_isolated(
        self,
        healthcare_command,
        mock_compliance_service,
    ):
        """Test HIPAA check với audit logging và tenant isolation."""
        await healthcare_command._check_hipaa_with_audit(
            guard=healthcare_command._command.guards[0],
            user_id="user_1",
            tenant_id="tenant_1",
        )

        # Verify compliance service was called with tenant_id
        mock_compliance_service.check_hipaa_clearance.assert_called_once()
        call_kwargs = mock_compliance_service.check_hipaa_clearance.call_args.kwargs
        assert call_kwargs.get("tenant_id") == "tenant_1"

    @pytest.mark.asyncio
    async def test_log_compliance_check_tenant_aware(
        self,
        banking_command,
        mock_compliance_service,
    ):
        """Test compliance check logging với tenant context."""
        await banking_command._log_compliance_check(
            guard_type=GuardType.KYC_CHECK,
            user_id="user_1",
            tenant_id="tenant_1",
            result="passed",
            details={"test": "data"},
        )

        # Verify log_compliance_check was called
        mock_compliance_service.log_compliance_check.assert_called_once()
        call_args = mock_compliance_service.log_compliance_check.call_args.args[0]

        assert call_args["tenant_id"] == "tenant_1"
        assert call_args["user_id"] == "user_1"
        assert call_args["result"] == "passed"
        assert call_args["guard_type"] == "kyc_check"

    @pytest.mark.asyncio
    async def test_check_kyc_no_user_id(self, banking_command):
        """Test KYC check với missing user_id."""
        with pytest.raises(MidicoderError) as exc_info:
            await banking_command._check_kyc_with_audit(
                guard=banking_command._command.guards[0],
                user_id=None,
                tenant_id="tenant_1",
            )

        assert exc_info.value.code == ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_check_kyc_no_compliance_service(self, banking_command):
        """Test KYC check với missing compliance service (skip)."""
        banking_command._compliance_service = None

        # Should not raise, just skip
        await banking_command._check_kyc_with_audit(
            guard=banking_command._command.guards[0],
            user_id="user_1",
            tenant_id="tenant_1",
        )


# ============================================================================
# Error Code Tests
# ============================================================================

class TestComplianceErrorCodes:
    """Tests cho compliance error codes."""

    def test_cp01_guard_double_entry_imbalance_exists(self):
        """Test CP01_GUARD_DOUBLE_ENTRY_IMBALANCE error code."""
        assert ErrorCode.CP01_GUARD_DOUBLE_ENTRY_IMBALANCE.value == "MDC-CP01-072"

    def test_cp01_guard_phi_not_encrypted_exists(self):
        """Test CP01_GUARD_PHI_NOT_ENCRYPTED error code."""
        assert ErrorCode.CP01_GUARD_PHI_NOT_ENCRYPTED.value == "MDC-CP01-073"

    def test_cp01_guard_minimum_necessary_violation_exists(self):
        """Test CP01_GUARD_MINIMUM_NECESSARY_VIOLATION error code."""
        assert ErrorCode.CP01_GUARD_MINIMUM_NECESSARY_VIOLATION.value == "MDC-CP01-074"

    def test_cp01_guard_compliance_log_failed_exists(self):
        """Test CP01_GUARD_COMPLIANCE_LOG_FAILED error code."""
        assert ErrorCode.CP01_GUARD_COMPLIANCE_LOG_FAILED.value == "MDC-CP01-068"

    def test_cp01_guard_external_api_timeout_exists(self):
        """Test CP01_GUARD_EXTERNAL_API_TIMEOUT error code."""
        assert ErrorCode.CP01_GUARD_EXTERNAL_API_TIMEOUT.value == "MDC-CP01-069"


# ============================================================================
# End of Test File
# ============================================================================