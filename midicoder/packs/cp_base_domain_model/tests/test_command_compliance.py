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

from midicoder.packs.cp_base_domain_model.models import Command, CommandGuard, GuardType
from midicoder.packs.cp_base_domain_model.command_guards import CommandGuards
from midicoder.packs.cp_base_domain_model.command_validator import CommandValidator
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

        assert exc_info.value.code == ErrorCode.B01_GUARD_KYC_NOT_VERIFIED

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

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

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
        assert ErrorCode.B01_GUARD_DOUBLE_ENTRY_IMBALANCE.value == "MDC-B01-034"

    def test_cp01_guard_phi_not_encrypted_exists(self):
        """Test CP01_GUARD_PHI_NOT_ENCRYPTED error code."""
        assert ErrorCode.B01_GUARD_PHI_NOT_ENCRYPTED.value == "MDC-B01-035"

    def test_cp01_guard_minimum_necessary_violation_exists(self):
        """Test CP01_GUARD_MINIMUM_NECESSARY_VIOLATION error code."""
        assert ErrorCode.B01_GUARD_MINIMUM_NECESSARY_VIOLATION.value == "MDC-B01-036"

    def test_cp01_guard_compliance_log_failed_exists(self):
        """Test CP01_GUARD_COMPLIANCE_LOG_FAILED error code."""
        assert ErrorCode.B01_GUARD_COMPLIANCE_LOG_FAILED.value == "MDC-B01-018"

    def test_cp01_guard_external_api_timeout_exists(self):
        """Test CP01_GUARD_EXTERNAL_API_TIMEOUT error code."""
        assert ErrorCode.B01_GUARD_EXTERNAL_API_TIMEOUT.value == "MDC-B01-037"


# ============================================================================
# Models Gap Coverage Tests
# ============================================================================

class TestModelsGapCoverage:
    """Gap coverage tests cho models.py — push ≥99%."""

    def test_command_to_dict_with_dict_guards_effects_errors(self):
        """Test Command.to_dict() else branches: raw dict guards/effects/errors (lines 1238, 1254, 1268)."""
        cmd = Command(
            id="GapCmd",
            guards=[{"guard_type": "auth"}],
            effects=[{"effect_type": "create_record"}],
            errors=[{"code": "ERR_1", "message": "fail"}],
        )
        d = cmd.to_dict()
        assert d["guards"] == [{"guard_type": "auth"}]
        assert d["effects"] == [{"effect_type": "create_record"}]
        assert d["errors"] == [{"code": "ERR_1", "message": "fail"}]

    def test_command_get_required_permissions_already_present(self):
        """Test get_required_permissions() when permission already in required_permissions (line 1341->1339)."""
        cmd = Command(
            id="PermCmd",
            required_permissions=["order.create"],
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="order.create")],
        )
        perms = cmd.get_required_permissions()
        assert perms == ["order.create"]

    def test_command_get_update_effects(self):
        """Test Command.get_update_effects() (line 1366)."""
        from midicoder.packs.cp_base_domain_model.models import CommandEffect, EffectType
        cmd = Command(
            id="UpdateCmd",
            effects=[
                CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="Order"),
            ],
        )
        effects = cmd.get_update_effects()
        assert len(effects) == 1

    def test_command_get_delete_effects(self):
        """Test Command.get_delete_effects() (line 1375)."""
        from midicoder.packs.cp_base_domain_model.models import CommandEffect, EffectType
        cmd = Command(
            id="DeleteCmd",
            effects=[
                CommandEffect(effect_type=EffectType.DELETE_RECORD, entity="Order"),
            ],
        )
        effects = cmd.get_delete_effects()
        assert len(effects) == 1

    def test_command_get_event_effects(self):
        """Test Command.get_event_effects() (line 1384)."""
        from midicoder.packs.cp_base_domain_model.models import CommandEffect, EffectType
        cmd = Command(
            id="EventCmd",
            effects=[
                CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="OrderPlaced"),
            ],
        )
        effects = cmd.get_event_effects()
        assert len(effects) == 1

    def test_filter_expression_gt_gte_lt_lte(self):
        """Test FilterExpression.to_sqlalchemy() GT/GTE/LT/LTE branches (lines 1616, 1622, 1624, 1628, 1632, 1637-1640)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterOp

        # NE (1616)
        fe = FilterExpression(field="status", operator=FilterOp.NE, value="deleted")
        assert fe.to_sqlalchemy() is not None

        # GT (1618)
        fe = FilterExpression(field="age", operator=FilterOp.GT, value=18)
        assert fe.to_sqlalchemy() is not None

        # GTE (1620)
        fe = FilterExpression(field="age", operator=FilterOp.GTE, value=18)
        assert fe.to_sqlalchemy() is not None

        # LT (1622)
        fe = FilterExpression(field="age", operator=FilterOp.LT, value=100)
        assert fe.to_sqlalchemy() is not None

        # LTE (1624)
        fe = FilterExpression(field="age", operator=FilterOp.LTE, value=100)
        assert fe.to_sqlalchemy() is not None

        # IN (1626)
        fe = FilterExpression(field="status", operator=FilterOp.IN, value=["active", "pending"])
        assert fe.to_sqlalchemy() is not None

        # NOT_IN (1628)
        fe = FilterExpression(field="status", operator=FilterOp.NOT_IN, value=["deleted"])
        assert fe.to_sqlalchemy() is not None

        # LIKE (1630)
        fe = FilterExpression(field="name", operator=FilterOp.LIKE, value="test%")
        assert fe.to_sqlalchemy() is not None

        # ILIKE (1632)
        fe = FilterExpression(field="name", operator=FilterOp.ILIKE, value="%test%")
        assert fe.to_sqlalchemy() is not None

    def test_filter_expression_between_and_is_null(self):
        """Test FilterExpression.to_sqlalchemy() BETWEEN/IS_NULL branches (lines 1637-1640)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterOp
        fe = FilterExpression(field="age", operator=FilterOp.BETWEEN, value=[18, 65])
        assert fe.to_sqlalchemy() is not None

        fe = FilterExpression(field="deleted_at", operator=FilterOp.IS_NULL, value=None)
        assert fe.to_sqlalchemy() is not None

    def test_filter_group_or_operator(self):
        """Test FilterGroup.to_sqlalchemy() with 'or' operator (line 1698)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterGroup, FilterOp
        fg = FilterGroup(
            operator="or",
            filters=[
                FilterExpression(field="status", operator=FilterOp.EQ, value="active"),
                FilterExpression(field="tenant_id", operator=FilterOp.EQ, value="t1"),
            ],
        )
        result = fg.to_sqlalchemy()
        assert result is not None

    def test_filter_group_nested_filter_group(self):
        """Test FilterGroup.to_sqlalchemy() with nested FilterGroup (line 1697)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterGroup, FilterOp
        fg = FilterGroup(
            operator="or",
            filters=[
                FilterGroup(
                    operator="and",
                    filters=[
                        FilterExpression(field="status", operator=FilterOp.EQ, value="active"),
                        FilterExpression(field="age", operator=FilterOp.GT, value=18),
                    ],
                ),
                FilterExpression(field="tenant_id", operator=FilterOp.EQ, value="t1"),
            ],
        )
        result = fg.to_sqlalchemy()
        assert result is not None

    def test_projection_config_get_sensitive_fields(self):
        """Test ProjectionConfig.get_sensitive_fields_to_exclude() (line 1843)."""
        from midicoder.packs.cp_base_domain_model.models import ProjectionConfig
        pc = ProjectionConfig()
        sensitive = pc.get_sensitive_fields_to_exclude()
        assert "password" in sensitive
        assert "secret_key" in sensitive
        assert "api_key" in sensitive

    def test_vo_field_to_dict_with_all_optional_fields(self):
        """Test VOField.to_dict() with all optional fields set (lines 2312-2326)."""
        from midicoder.packs.cp_base_domain_model.models import VOField, VOFieldType
        vf = VOField(
            name="test_field",
            field_type=VOFieldType.DECIMAL,
            required=True,
            default=0.0,
            description="Test field",
            precision=10,
            scale=2,
            min_length=1,
            max_length=50,
            pattern=r"^\d+$",
            enum_values=["a", "b"],
        )
        d = vf.to_dict()
        assert d["default"] == 0.0
        assert d["description"] == "Test field"
        assert d["precision"] == 10
        assert d["scale"] == 2
        assert d["min_length"] == 1
        assert d["max_length"] == 50
        assert d["pattern"] == r"^\d+$"
        assert d["enum_values"] == ["a", "b"]

    def test_vo_to_dict_without_optional_fields(self):
        """Test ValueObject.to_dict() else branches: no description, no extends (line 2413->2415)."""
        from midicoder.packs.cp_base_domain_model.models import ValueObject
        vo = ValueObject(id="MinimalVO", fields=[], immutable=False, comparable=False)
        d = vo.to_dict()
        assert "description" not in d
        assert "extends" not in d


# ============================================================================
# Models Gap Coverage — 100% push
# ============================================================================

class TestGapModelsValidationResult:
    """TestGapModels: ValidationResult __post_init__ branch 1073->1075, 1075->exit."""

    def test_validation_result_post_init_with_explicit_lists(self):
        """ValidationResult.__post_init__ with non-None errors/warnings (lines 1073->1075, 1075->exit)."""
        from midicoder.packs.cp_base_domain_model.models import ValidationResult
        vr = ValidationResult(is_valid=True, errors=["pre_error"], warnings=["pre_warn"])
        assert vr.errors == ["pre_error"]
        assert vr.warnings == ["pre_warn"]


class TestGapModelsCommandInit:
    """TestGapModels: Command.__init__ backward compat (line 1199)."""

    def test_command_init_transaction_alias(self):
        """Command.__init__ with transaction= alias (line 1199)."""
        cmd = Command(
            id="TxAlias",
            transaction=True,
        )
        assert cmd.transaction_required is True


class TestGapModelsCommandToDict:
    """TestGapModels: Command.to_dict() if-branches (1229, 1244, 1260, 1297, 1309, 1321-1326)."""

    def test_command_to_dict_instance_branch_guards(self):
        """Command.to_dict() isinstance(g, CommandGuard) True branch (line 1229)."""
        cmd = Command(
            id="DictGuard",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="x")],
        )
        d = cmd.to_dict()
        assert d["guards"][0]["guard_type"] == "auth"

    def test_command_to_dict_instance_branch_effects(self):
        """Command.to_dict() isinstance(e, CommandEffect) True branch (line 1244)."""
        from midicoder.packs.cp_base_domain_model.models import CommandEffect, EffectType
        cmd = Command(
            id="DictEffect",
            effects=[CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="Order")],
        )
        d = cmd.to_dict()
        assert d["effects"][0]["effect_type"] == "create_record"

    def test_command_to_dict_instance_branch_errors(self):
        """Command.to_dict() isinstance(err, CommandError) True branch (line 1260)."""
        from midicoder.packs.cp_base_domain_model.models import CommandError
        cmd = Command(
            id="DictError",
            errors=[CommandError(code="ERR_1", message="fail")],
        )
        d = cmd.to_dict()
        assert d["errors"][0]["code"] == "ERR_1"

    def test_command_has_auth_guard_false(self):
        """Command.has_auth_guard() returns False when no AUTH guard (line 1297)."""
        cmd = Command(
            id="NoAuth",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE)],
        )
        assert cmd.has_auth_guard() is False

    def test_command_has_tenant_guard_false(self):
        """Command.has_tenant_guard() returns False when no TENANT guard (line 1309)."""
        cmd = Command(
            id="NoTenant",
            guards=[CommandGuard(guard_type=GuardType.AUTH)],
        )
        assert cmd.has_tenant_guard() is False

    def test_command_has_transaction_effects_false(self):
        """Command.has_transaction_effects() False (lines 1321-1326)."""
        cmd = Command(
            id="NoTx",
            effects=[],
        )
        assert cmd.has_transaction_effects() is False


class TestGapModelsCommandPerms:
    """TestGapModels: Command.get_required_permissions branches (1340->1339, 1342, 1352)."""

    def test_command_get_required_permissions_guard_no_permission(self):
        """get_required_permissions() AUTH guard with permission=None, skipped (line 1342)."""
        cmd = Command(
            id="NoPermGuard",
            guards=[CommandGuard(guard_type=GuardType.AUTH)],
        )
        perms = cmd.get_required_permissions()
        assert perms == []

    def test_command_get_required_permissions_non_auth_guard(self):
        """get_required_permissions() non-AUTH guard skipped (line 1352)."""
        cmd = Command(
            id="NonAuthGuard",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE)],
        )
        perms = cmd.get_required_permissions()
        assert perms == []


class TestGapModelsCommandAlias:
    """TestGapModels: Command.transaction() alias (line 1401) and from_dict (line 1414)."""

    def test_command_transaction_alias(self):
        """Command.transaction property alias (line 1401)."""
        cmd = Command(id="AliasTx", transaction=True)
        assert cmd.transaction is True

    def test_command_from_dict(self):
        """Command.from_dict() class method (line 1414)."""
        cmd = Command.from_dict({"id": "FromDict", "description": "test"})
        assert cmd.id == "FromDict"


class TestGapModelsFilterExpressionISNotNull:
    """TestGapModels: FilterExpression IS_NOT_NULL (lines 1637-1640)."""

    def test_filter_expression_is_not_null(self):
        """FilterExpression.to_sqlalchemy() IS_NOT_NULL (lines 1637-1640)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterOp
        fe = FilterExpression(field="deleted_at", operator=FilterOp.IS_NOT_NULL, value=None)
        assert fe.to_sqlalchemy() is not None


class TestGapModelsFilterGroupEmpty:
    """TestGapModels: FilterGroup empty filters (lines 1685-1686)."""

    def test_filter_group_empty_filters(self):
        """FilterGroup.to_sqlalchemy() with empty filters (lines 1685-1686)."""
        from midicoder.packs.cp_base_domain_model.models import FilterGroup
        fg = FilterGroup(operator="and", filters=[])
        result = fg.to_sqlalchemy()
        assert result is not None


class TestGapModelsFilterGroupLoopBranch:
    """TestGapModels: FilterGroup loop with non-FilterGroup in body (line 1698)."""

    def test_filter_group_loop_non_fg_branch(self):
        """FilterGroup loop: second filter is FilterExpression not FilterGroup (line 1698)."""
        from midicoder.packs.cp_base_domain_model.models import FilterExpression, FilterGroup, FilterOp
        fg = FilterGroup(
            operator="and",
            filters=[
                FilterGroup(
                    operator="and",
                    filters=[FilterExpression(field="a", operator=FilterOp.EQ, value=1)],
                ),
                FilterExpression(field="b", operator=FilterOp.EQ, value=2),  # non-FG in loop -> line 1698
            ],
        )
        result = fg.to_sqlalchemy()
        assert result is not None


class TestGapModelsPHIMasking:
    """TestGapModels: PHIMaskingConfig should_mask/mask_value (1746-1767, 1780-1782)."""

    def test_phi_masking_disabled(self):
        """PHIMaskingConfig.should_mask() with enabled=False (line 1746)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=False)
        assert cfg.should_mask("ssn") is False

    def test_phi_masking_allowed_field(self):
        """PHIMaskingConfig.should_mask() field in allowed_fields (line 1752)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, allowed_fields=["name"])
        assert cfg.should_mask("name") is False

    def test_phi_masking_pattern_match(self):
        """PHIMaskingConfig.should_mask() pattern match (line 1756)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, mask_patterns=["^ssn"])
        assert cfg.should_mask("ssn") is True

    def test_phi_masking_no_match(self):
        """PHIMaskingConfig.should_mask() no pattern match (line 1767)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, mask_patterns=["^ssn"])
        assert cfg.should_mask("name") is False

    def test_phi_mask_value_should_mask_true(self):
        """PHIMaskingConfig.mask_value() should_mask=True (lines 1780-1782)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, mask_patterns=["^ssn"], default_mask_value="[HIDDEN]")
        assert cfg.mask_value("ssn", "123-45-6789") == "[HIDDEN]"

    def test_phi_mask_value_should_mask_false(self):
        """PHIMaskingConfig.mask_value() should_mask=False (line 1782)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, mask_patterns=["^ssn"])
        assert cfg.mask_value("name", "John") == "John"


class TestGapModelsPagination:
    """TestGapModels: PaginationConfig.__post_init__ (lines 1820-1821)."""

    def test_pagination_offset_calculation(self):
        """PaginationConfig.__post_init__ offset calc from page (lines 1820-1821)."""
        from midicoder.packs.cp_base_domain_model.models import PaginationConfig, PaginationType
        pc = PaginationConfig(type=PaginationType.OFFSET, page_size=20, page=3)
        assert pc.offset == 40  # (3-1)*20


class TestGapModelsProjection:
    """TestGapModels: ProjectionConfig.get_sensitive_fields_to_exclude (line 1858)."""

    def test_projection_sensitive_fields(self):
        """ProjectionConfig.get_sensitive_fields_to_exclude() (line 1858)."""
        from midicoder.packs.cp_base_domain_model.models import ProjectionConfig
        pc = ProjectionConfig()
        sensitive = pc.get_sensitive_fields_to_exclude()
        assert "password" in sensitive

    def test_projection_flat_include(self):
        """ProjectionConfig.get_flat_include_fields() (line 1858)."""
        from midicoder.packs.cp_base_domain_model.models import ProjectionConfig
        pc = ProjectionConfig(include=["a", "b"])
        assert pc.get_flat_include_fields() == ["a", "b"]


class TestGapModelsQuery:
    """TestGapModels: Query methods (1925, 1934, 1943, 1955, 1967, 1979)."""

    def test_query_has_auth_guard_false(self):
        """Query.has_auth_guard() False (line 1925)."""
        from midicoder.packs.cp_base_domain_model.models import Query, QueryGuard, QueryGuardType
        q = Query(id="q1", description="test", reads_from="e1", guards=[QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE)])
        assert q.has_auth_guard() is False

    def test_query_has_tenant_guard_false(self):
        """Query.has_tenant_guard() False (line 1934)."""
        from midicoder.packs.cp_base_domain_model.models import Query, QueryGuard, QueryGuardType
        q = Query(id="q1", description="test", reads_from="e1", guards=[QueryGuard(guard_type=QueryGuardType.AUTH)])
        assert q.has_tenant_guard() is False

    def test_query_has_audit_effects_false(self):
        """Query.has_audit_effects() False (line 1943)."""
        from midicoder.packs.cp_base_domain_model.models import Query
        q = Query(id="q1", description="test", reads_from="e1", effects=[])
        assert q.has_audit_effects() is False

    def test_query_get_required_permissions_empty(self):
        """Query.get_required_permissions() no auth perms (line 1955)."""
        from midicoder.packs.cp_base_domain_model.models import Query, QueryGuard, QueryGuardType
        q = Query(id="q1", description="test", reads_from="e1", guards=[QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE)])
        assert q.get_required_permissions() == []

    def test_query_get_audit_actions_empty(self):
        """Query.get_audit_actions() no audit effects (line 1967)."""
        from midicoder.packs.cp_base_domain_model.models import Query
        q = Query(id="q1", description="test", reads_from="e1", effects=[])
        assert q.get_audit_actions() == []

    def test_query_to_dict(self):
        """Query.to_dict() (line 1979)."""
        from midicoder.packs.cp_base_domain_model.models import Query
        q = Query(id="q1", description="test", reads_from="e1")
        d = q.to_dict()
        assert d["id"] == "q1"


class TestGapModelsQueryFromDict:
    """TestGapModels: Query.from_dict() (lines 2051-2120)."""

    def test_query_from_dict_full(self):
        """Query.from_dict() with all fields (lines 2051-2120)."""
        from midicoder.packs.cp_base_domain_model.models import Query
        q = Query.from_dict({
            "id": "FullQuery",
            "description": "Full query test",
            "reads_from": "Entity1",
            "input": [{"name": "field1", "field_type": "string"}],
            "filters": [{"field": "status", "operator": "eq", "value": "active"}],
            "pagination": {"type": "offset", "page_size": 10, "page": 1},
            "projection": {"include": ["id", "name"], "exclude": []},
            "sort": [{"field": "name", "direction": "asc"}],
            "guards": [{"guard_type": "auth", "permission": "read"}],
            "effects": [{"effect_type": "write_audit_log", "audit_action": "query"}],
        })
        assert q.id == "FullQuery"
        assert len(q.filters) == 1
        assert len(q.guards) == 1


class TestGapModelsAggQuery:
    """TestGapModels: AggregationQuery methods (2162, 2166, 2175)."""

    def test_agg_query_has_auth_guard_false(self):
        """AggregationQuery.has_auth_guard() False (line 2162)."""
        from midicoder.packs.cp_base_domain_model.models import AggregationQuery, AggregationConfig, AggFunction, QueryGuard, QueryGuardType
        aq = AggregationQuery(
            id="aq1",
            description="test agg",
            reads_from="e1",
            aggregation=AggregationConfig(function=AggFunction.COUNT),
            guards=[QueryGuard(guard_type=QueryGuardType.TENANT_SCOPE)],
        )
        assert aq.has_auth_guard() is False

    def test_agg_query_has_tenant_guard_false(self):
        """AggregationQuery.has_tenant_guard() False (line 2166)."""
        from midicoder.packs.cp_base_domain_model.models import AggregationQuery, AggregationConfig, AggFunction, QueryGuard, QueryGuardType
        aq = AggregationQuery(
            id="aq1",
            description="test agg",
            reads_from="e1",
            aggregation=AggregationConfig(function=AggFunction.COUNT),
            guards=[QueryGuard(guard_type=QueryGuardType.AUTH)],
        )
        assert aq.has_tenant_guard() is False

    def test_agg_query_to_dict(self):
        """AggregationQuery.to_dict() (line 2175)."""
        from midicoder.packs.cp_base_domain_model.models import AggregationQuery, AggregationConfig, AggFunction
        aq = AggregationQuery(
            id="aq1",
            description="test agg",
            reads_from="e1",
            aggregation=AggregationConfig(function=AggFunction.COUNT),
        )
        d = aq.to_dict()
        assert d["id"] == "aq1"


class TestGapModelsVOFieldToDict:
    """TestGapModels: VOField.to_dict() branches (2311->2313..2325->2328) and from_dict (2341-2344)."""

    def test_vo_field_to_dict_minimal(self):
        """VOField.to_dict() with only required fields - all optional branches False (lines 2311->2313..2325->2328)."""
        from midicoder.packs.cp_base_domain_model.models import VOField, VOFieldType
        vf = VOField(name="minimal", field_type=VOFieldType.STRING)
        d = vf.to_dict()
        assert "default" not in d
        assert "description" not in d
        assert "precision" not in d
        assert "scale" not in d
        assert "min_length" not in d
        assert "max_length" not in d
        assert "pattern" not in d
        assert "enum_values" not in d

    def test_vo_field_from_dict(self):
        """VOField.from_dict() (lines 2341-2344)."""
        from midicoder.packs.cp_base_domain_model.models import VOField
        vf = VOField.from_dict({"name": "from_dict", "type": "string", "required": True})
        assert vf.name == "from_dict"
        assert vf.required is True


class TestGapModelsValueObject:
    """TestGapModels: ValueObject.to_dict() branches (2414, 2416) and from_dict (2431)."""

    def test_value_object_to_dict_with_optional(self):
        """ValueObject.to_dict() with description and extends set (lines 2414, 2416)."""
        from midicoder.packs.cp_base_domain_model.models import ValueObject
        vo = ValueObject(id="FullVO", description="desc", extends="BaseVO")
        d = vo.to_dict()
        assert d["description"] == "desc"
        assert d["extends"] == "BaseVO"

    def test_value_object_from_dict(self):
        """ValueObject.from_dict() (line 2431)."""
        from midicoder.packs.cp_base_domain_model.models import ValueObject
        vo = ValueObject.from_dict({"id": "FromDictVO", "immutable": True})
        assert vo.id == "FromDictVO"
        assert vo.immutable is True


# ============================================================================
# Models Gap Coverage — Final push to 100%
# ============================================================================

class TestGapModelsCommandFieldStringType:
    """TestGapModels: CommandField.to_dict()/from_dict() string type path (905-906, 934-937)."""

    def test_command_field_to_dict_with_string_type(self):
        """CommandField.to_dict() when field_type is a string, not enum (lines 905-906)."""
        from midicoder.packs.cp_base_domain_model.models import CommandField
        cf = CommandField(name="str_type", field_type="integer")  # string, not enum
        d = cf.to_dict()
        assert d["type"] == "integer"

    def test_command_field_from_dict_with_enum_type(self):
        """CommandField.from_dict() when type is already enum, not string (lines 934-937)."""
        from midicoder.packs.cp_base_domain_model.models import CommandField, CommandFieldType
        cf = CommandField.from_dict({"name": "enum_type", "type": CommandFieldType.INTEGER})
        assert cf.field_type == CommandFieldType.INTEGER


class TestGapModelsCommandPermsFalsy:
    """TestGapModels: Command.get_required_permissions() falsy permission (1342, 1352)."""

    def test_command_get_required_permissions_empty_string_perm(self):
        """get_required_permissions() AUTH guard with empty string permission (line 1342)."""
        cmd = Command(
            id="EmptyPerm",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="")],
        )
        perms = cmd.get_required_permissions()
        assert perms == []


class TestGapModelsPHICommonFields:
    """TestGapModels: PHIMaskingConfig common PHI fields check (line 1765)."""

    def test_phi_masking_common_phi_field(self):
        """PHIMaskingConfig.should_mask() common PHI field fallback (line 1765)."""
        from midicoder.packs.cp_base_domain_model.models import PHIMaskingConfig
        cfg = PHIMaskingConfig(enabled=True, mask_patterns=[], allowed_fields=[])
        assert cfg.should_mask("ssn") is True
        assert cfg.should_mask("mrn") is True
        assert cfg.should_mask("patient_id") is True


# ============================================================================
# End of Test File
# ============================================================================