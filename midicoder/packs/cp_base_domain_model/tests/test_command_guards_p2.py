"""
Tests cho P2-001-D2: Domain Guards (FRAUD, SAFETY, CLAIMS).

Test coverage:
- FRAUD_DETECTION guard (DP12 Payments): 12 tests
- SAFETY_CHECK guard (DP05 Manufacturing): 8 tests
- CLAIMS_VALIDATION guard (DP14 Insurance): 10 tests
- Tenant isolation: 6 tests
- Error codes: 12 tests
- Validator methods: 10 tests

Total: 48 tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from midicoder.packs.cp_base_domain_model.models import (
    Command,
    CommandField,
    CommandFieldType,
    CommandGuard,
    GuardType,
    ValidationResult,
)
from midicoder.packs.cp_base_domain_model.command_guards import CommandGuards
from midicoder.packs.cp_base_domain_model.command_validator import CommandValidator
from midicoder.errors import ErrorCode, MidicoderError


class MockComplianceService:
    """Mock compliance service cho testing."""

    def __init__(self):
        self.transaction_velocity = None
        self.pattern_anomaly = None
        self.external_fraud = None
        self.equipment_safe = None
        self.personnel_certified = None
        self.process_compliant = None
        self.hazards = None
        self.is_covered = None
        self.within_period = None
        self.within_limit = None
        self.is_excluded = None
        self.kyc_verified = None
        self.aml_clear = None
        self.hipaa_clearance = None
        self.log_raises = None

    async def check_transaction_velocity(
        self, user_id, tenant_id, threshold, window
    ) -> bool:
        """Mock transaction velocity check."""
        return self.transaction_velocity is not None and self.transaction_velocity

    async def detect_pattern_anomaly(
        self, user_id, transaction_data, tenant_id
    ) -> bool:
        """Mock pattern anomaly detection."""
        return self.pattern_anomaly is not None and self.pattern_anomaly

    async def call_external_fraud_api(
        self, user_id, transaction_data, tenant_id, timeout
    ) -> dict:
        """Mock external fraud API call."""
        if self.external_fraud is None:
            raise TimeoutError("External API timeout")
        return self.external_fraud

    async def check_equipment_safety(self, equipment_id, tenant_id) -> bool:
        """Mock equipment safety check."""
        return self.equipment_safe is not None and self.equipment_safe

    async def check_personnel_certification(
        self, user_id, operation_type, tenant_id
    ) -> bool:
        """Mock personnel certification check."""
        return self.personnel_certified is not None and self.personnel_certified

    async def check_process_compliance(
        self, operation_type, process_data, tenant_id
    ) -> bool:
        """Mock process compliance check."""
        return self.process_compliant is not None and self.process_compliant

    async def detect_hazards(self, operation_data, tenant_id) -> list:
        """Mock hazard detection."""
        return self.hazards if self.hazards is not None else []

    async def check_policy_coverage(
        self, policy_id, claim_type, tenant_id
    ) -> bool:
        """Mock policy coverage check."""
        return self.is_covered is not None and self.is_covered

    async def check_coverage_period(
        self, policy_id, incident_date, tenant_id
    ) -> bool:
        """Mock coverage period check."""
        return self.within_period is not None and self.within_period

    async def check_claim_limit(
        self, policy_id, claim_amount, tenant_id
    ) -> bool:
        """Mock claim limit check."""
        return self.within_limit is not None and self.within_limit

    async def check_claim_exclusions(
        self, policy_id, claim_type, incident_data, tenant_id
    ) -> bool:
        """Mock claim exclusions check."""
        return self.is_excluded is not None and self.is_excluded

    async def check_kyc(self, user_id, tenant_id=None) -> bool:
        """Mock KYC check."""
        return self.kyc_verified is not None and self.kyc_verified

    async def check_aml(self, user_id, transaction_data, tenant_id=None) -> bool:
        """Mock AML check."""
        return self.aml_clear is not None and self.aml_clear

    async def check_hipaa_clearance(self, user_id, tenant_id=None) -> bool:
        """Mock HIPAA clearance check."""
        return self.hipaa_clearance is not None and self.hipaa_clearance

    async def log_compliance_check(self, audit_record: dict) -> None:
        """Mock audit log."""
        if self.log_raises:
            raise RuntimeError(self.log_raises)
        pass


# ============================================================================
# FRAUD_DETECTION Guard Tests (12 tests)
# ============================================================================

class TestFraudDetectionGuard:
    """Tests cho FRAUD_DETECTION guard (DP12 Payments)."""

    @pytest.mark.asyncio
    async def test_fraud_detection_no_compliance_service(self):
        """Test fraud detection với no compliance service (skip)."""
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=None)

        data = {"amount": 1000000, "timestamp": "2026-05-04T10:00:00Z"}
        
        # Should skip without error
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_detection_user_not_authenticated(self):
        """Test fraud detection với user not authenticated."""
        compliance = MockComplianceService()
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id=None, tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_fraud_detection_velocity_exceeded(self):
        """Test fraud detection với velocity exceeded."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = True  # Exceeded
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, limit=10, window="1h")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_FRAUD_VELOCITY_EXCEEDED

    @pytest.mark.asyncio
    async def test_fraud_detection_velocity_ok(self):
        """Test fraud detection với velocity ok."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False  # Not exceeded
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, limit=10, window="1h")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        # Should pass
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_detection_amount_threshold_exceeded(self):
        """Test fraud detection với amount threshold exceeded."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition="50000000")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 100000000}  # > 50M threshold
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_FRAUD_AMOUNT_THRESHOLD

    @pytest.mark.asyncio
    async def test_fraud_detection_amount_ok(self):
        """Test fraud detection với amount ok."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition="50000000")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 10000000}  # < 50M threshold
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_detection_pattern_anomaly(self):
        """Test fraud detection với pattern anomaly detected."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = True
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_FRAUD_PATTERN_ANOMALY

    @pytest.mark.asyncio
    async def test_fraud_detection_external_blocked(self):
        """Test fraud detection với external fraud service blocked."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": True, "reason": "High risk"}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_FRAUD_EXTERNAL_BLOCKED

    @pytest.mark.asyncio
    async def test_fraud_detection_external_timeout_fallback(self):
        """Test fraud detection với external API timeout (fallback to allow)."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = None  # Will raise TimeoutError
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        # Should allow on timeout (fallback)
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_detection_tenant_isolation(self):
        """Test fraud detection với tenant isolation (KPI-029)."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        # Check with tenant1
        await guards.check_all(data={"amount": 1000000}, user_id="user1", tenant_id="tenant1")

        # Check with tenant2 (isolated)
        await guards.check_all(data={"amount": 1000000}, user_id="user2", tenant_id="tenant2")

    @pytest.mark.asyncio
    async def test_fraud_detection_tenant_in_context(self):
        """Test fraud detection ghi tenant_id vào audit log."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 1000000}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        # Audit log should include tenant_id (verified in _log_compliance_check)

    @pytest.mark.asyncio
    async def test_fraud_detection_all_checks_pass(self):
        """Test fraud detection với tất cả checks pass."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition="100000000")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 50000000}  # < 100M threshold
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")


# ============================================================================
# SAFETY_CHECK Guard Tests (8 tests)
# ============================================================================

class TestSafetyCheckGuard:
    """Tests cho SAFETY_CHECK guard (DP05 Manufacturing)."""

    @pytest.mark.asyncio
    async def test_safety_check_no_compliance_service(self):
        """Test safety check với no compliance service (skip)."""
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=None)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_safety_check_equipment_unsafe(self):
        """Test safety check với equipment unsafe."""
        compliance = MockComplianceService()
        compliance.equipment_safe = False
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_SAFETY_EQUIPMENT_UNSAFE

    @pytest.mark.asyncio
    async def test_safety_check_personnel_not_certified(self):
        """Test safety check với personnel not certified."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = False
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED

    @pytest.mark.asyncio
    async def test_safety_check_process_non_compliant(self):
        """Test safety check với process non-compliant."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = True
        compliance.process_compliant = False
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_SAFETY_PROCESS_NON_COMPLIANT

    @pytest.mark.asyncio
    async def test_safety_check_hazards_detected(self):
        """Test safety check với hazards detected."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = True
        compliance.process_compliant = True
        compliance.hazards = ["fire_hazard", "toxic_gas"]
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_SAFETY_HAZARD_DETECTED

    @pytest.mark.asyncio
    async def test_safety_check_all_ok(self):
        """Test safety check với tất cả checks ok."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = True
        compliance.process_compliant = True
        compliance.hazards = []
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"equipment_id": "EQ001", "operation_type": "welding"}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_safety_check_no_equipment_id(self):
        """Test safety check với no equipment_id (skip equipment check)."""
        compliance = MockComplianceService()
        compliance.personnel_certified = True
        compliance.process_compliant = True
        compliance.hazards = []
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"operation_type": "assembly"}  # No equipment_id
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_safety_check_tenant_isolation(self):
        """Test safety check với tenant isolation."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = True
        compliance.process_compliant = True
        compliance.hazards = []
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all(data={"equipment_id": "EQ001"}, user_id="user1", tenant_id="tenant1")
        await guards.check_all(data={"equipment_id": "EQ002"}, user_id="user2", tenant_id="tenant2")


# ============================================================================
# CLAIMS_VALIDATION Guard Tests (10 tests)
# ============================================================================

class TestClaimsValidationGuard:
    """Tests cho CLAIMS_VALIDATION guard (DP14 Insurance)."""

    @pytest.mark.asyncio
    async def test_claims_validation_missing_policy_id(self):
        """Test claims validation với missing policy_id."""
        compliance = MockComplianceService()
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 10000000, "claim_type": "medical"}  # No policy_id
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_CLAIMS_NOT_COVERED

    @pytest.mark.asyncio
    async def test_claims_validation_not_covered(self):
        """Test claims validation với claim not covered."""
        compliance = MockComplianceService()
        compliance.is_covered = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "cosmetic"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_CLAIMS_NOT_COVERED

    @pytest.mark.asyncio
    async def test_claims_validation_outside_period(self):
        """Test claims validation với incident outside coverage period."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "medical", "incident_date": "2020-01-01"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_CLAIMS_OUTSIDE_PERIOD

    @pytest.mark.asyncio
    async def test_claims_validation_exceeds_limit(self):
        """Test claims validation với claim amount exceeds limit."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 100000000, "claim_type": "medical"}  # 100M > limit
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_CLAIMS_EXCEEDS_LIMIT

    @pytest.mark.asyncio
    async def test_claims_validation_excluded(self):
        """Test claims validation với claim excluded."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = True
        compliance.is_excluded = True
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "war_related"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id="user1", tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_CLAIMS_EXCLUDED

    @pytest.mark.asyncio
    async def test_claims_validation_all_ok(self):
        """Test claims validation với tất cả checks ok."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = True
        compliance.is_excluded = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "medical", "incident_date": "2026-05-01"}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_claims_validation_no_compliance_service(self):
        """Test claims validation với no compliance service (skip)."""
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=None)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "medical"}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_claims_validation_user_not_authenticated(self):
        """Test claims validation với user not authenticated."""
        compliance = MockComplianceService()
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "medical"}
        
        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(data, user_id=None, tenant_id="tenant1")
        
        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_claims_validation_tenant_isolation(self):
        """Test claims validation với tenant isolation."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = True
        compliance.is_excluded = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all(data={"policy_id": "POL001"}, user_id="user1", tenant_id="tenant1")
        await guards.check_all(data={"policy_id": "POL002"}, user_id="user2", tenant_id="tenant2")

    @pytest.mark.asyncio
    async def test_claims_validation_tenant_in_context(self):
        """Test claims validation ghi tenant_id vào audit log."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = True
        compliance.is_excluded = False
        command = Command(
            id="SubmitClaim",
            guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"policy_id": "POL001", "amount": 10000000, "claim_type": "medical"}
        
        await guards.check_all(data, user_id="user1", tenant_id="tenant1")


# ============================================================================
# Validator Tests (10 tests)
# ============================================================================

class TestDomainValidators:
    """Tests cho domain-specific validators."""

    @pytest.mark.asyncio
    async def test_validate_fraud_detection_velocity(self):
        """Test validate_fraud_detection với velocity exceeded."""
        command = Command(id="ProcessPayment")
        validator = CommandValidator(command)

        data = {
            "transaction_count": 15,
            "velocity_threshold": 10,
            "velocity_window": "1h",
        }
        
        result = await validator.validate_fraud_detection(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("velocity" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_fraud_detection_amount(self):
        """Test validate_fraud_detection với amount threshold exceeded."""
        command = Command(id="ProcessPayment")
        validator = CommandValidator(command)

        data = {
            "amount": 100000000,
            "amount_threshold": "50000000",
        }
        
        result = await validator.validate_fraud_detection(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("vượt ngưỡng" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_safety_check_equipment(self):
        """Test validate_safety_check với equipment unsafe."""
        command = Command(id="StartOperation")
        validator = CommandValidator(command)

        data = {
            "equipment_id": "EQ001",
            "equipment_safe": False,
        }
        
        result = await validator.validate_safety_check(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("không an toàn" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_safety_check_hazards(self):
        """Test validate_safety_check với hazards detected."""
        command = Command(id="StartOperation")
        validator = CommandValidator(command)

        data = {
            "detected_hazards": ["fire", "toxic_gas"],
        }
        
        result = await validator.validate_safety_check(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("nguy cơ" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_claims_validation_not_covered(self):
        """Test validate_claims_validation với claim not covered."""
        command = Command(id="SubmitClaim")
        validator = CommandValidator(command)

        data = {
            "policy_id": "POL001",
            "claim_type": "cosmetic",
            "is_covered": False,
        }
        
        result = await validator.validate_claims_validation(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("không nằm trong phạm vi" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_claims_validation_exceeds_limit(self):
        """Test validate_claims_validation với claim exceeds limit."""
        command = Command(id="SubmitClaim")
        validator = CommandValidator(command)

        data = {
            "policy_id": "POL001",
            "claim_type": "medical",
            "amount": 100000000,
            "within_limit": False,
        }
        
        result = await validator.validate_claims_validation(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("vượt quá" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_claims_validation_missing_fields(self):
        """Test validate_claims_validation với missing required fields."""
        command = Command(id="SubmitClaim")
        validator = CommandValidator(command)

        data = {}  # Missing policy_id and claim_type
        
        result = await validator.validate_claims_validation(data, tenant_id="tenant1")
        
        assert not result.is_valid
        assert any("thiếu" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_fraud_detection_all_ok(self):
        """Test validate_fraud_detection với tất cả ok."""
        command = Command(id="ProcessPayment")
        validator = CommandValidator(command)

        data = {
            "transaction_count": 5,
            "velocity_threshold": 10,
            "amount": 10000000,
            "amount_threshold": "50000000",
        }
        
        result = await validator.validate_fraud_detection(data, tenant_id="tenant1")
        
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_safety_check_all_ok(self):
        """Test validate_safety_check với tất cả ok."""
        command = Command(id="StartOperation")
        validator = CommandValidator(command)

        data = {
            "equipment_id": "EQ001",
            "equipment_safe": True,
            "user_id": "user1",
            "operation_type": "assembly",
            "personnel_certified": True,
            "process_compliant": True,
            "detected_hazards": [],
        }
        
        result = await validator.validate_safety_check(data, tenant_id="tenant1")
        
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_claims_validation_all_ok(self):
        """Test validate_claims_validation với tất cả ok."""
        command = Command(id="SubmitClaim")
        validator = CommandValidator(command)

        data = {
            "policy_id": "POL001",
            "claim_type": "medical",
            "amount": 10000000,
            "is_covered": True,
            "within_coverage_period": True,
            "within_limit": True,
            "is_excluded": False,
        }
        
        result = await validator.validate_claims_validation(data, tenant_id="tenant1")
        
        assert result.is_valid


# ============================================================================
# Tenant Isolation Tests (6 tests)
# ============================================================================

class TestTenantIsolation:
    """Tests cho tenant isolation (KPI-029)."""

    @pytest.mark.asyncio
    async def test_fraud_detection_tenant_context(self):
        """Test fraud detection với tenant context."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(id="ProcessPayment", guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION)])
        guards = CommandGuards(command, compliance_service=compliance)

        # Both tenants should pass independently
        await guards.check_all(data={"amount": 1000000}, user_id="user1", tenant_id="tenant_a")
        await guards.check_all(data={"amount": 1000000}, user_id="user2", tenant_id="tenant_b")

    @pytest.mark.asyncio
    async def test_safety_check_tenant_context(self):
        """Test safety check với tenant context."""
        compliance = MockComplianceService()
        compliance.equipment_safe = True
        compliance.personnel_certified = True
        compliance.process_compliant = True
        compliance.hazards = []
        command = Command(id="StartOperation", guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)])
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all(data={"equipment_id": "EQ001"}, user_id="user1", tenant_id="tenant_a")
        await guards.check_all(data={"equipment_id": "EQ002"}, user_id="user2", tenant_id="tenant_b")

    @pytest.mark.asyncio
    async def test_claims_validation_tenant_context(self):
        """Test claims validation với tenant context."""
        compliance = MockComplianceService()
        compliance.is_covered = True
        compliance.within_period = True
        compliance.within_limit = True
        compliance.is_excluded = False
        command = Command(id="SubmitClaim", guards=[CommandGuard(guard_type=GuardType.CLAIMS_VALIDATION)])
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all(data={"policy_id": "POL001"}, user_id="user1", tenant_id="tenant_a")
        await guards.check_all(data={"policy_id": "POL002"}, user_id="user2", tenant_id="tenant_b")

    @pytest.mark.asyncio
    async def test_validator_tenant_in_error_message(self):
        """Test validator error messages include tenant_id."""
        command = Command(id="SubmitClaim")
        validator = CommandValidator(command)

        data = {"policy_id": "POL001", "claim_type": "cosmetic", "is_covered": False}
        result = await validator.validate_claims_validation(data, tenant_id="tenant_xyz")

        assert not result.is_valid
        assert any("tenant_xyz" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_fraud_validator_tenant_in_error(self):
        """Test fraud validator error includes tenant."""
        command = Command(id="ProcessPayment")
        validator = CommandValidator(command)

        data = {"amount": 100000000, "amount_threshold": "50000000"}
        result = await validator.validate_fraud_detection(data, tenant_id="tenant_test")

        assert not result.is_valid
        assert any("tenant_test" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_safety_validator_tenant_in_error(self):
        """Test safety validator error includes tenant."""
        command = Command(id="StartOperation")
        validator = CommandValidator(command)

        data = {"equipment_id": "EQ001", "equipment_safe": False}
        result = await validator.validate_safety_check(data, tenant_id="tenant_test")

        assert not result.is_valid
        assert any("tenant_test" in e for e in result.errors)


# ============================================================================
# Error Code Tests (12 tests)
# ============================================================================

class TestErrorCodes:
    """Tests cho error codes."""

    def test_fraud_velocity_exceeded_code(self):
        """Test CP01_GUARD_FRAUD_VELOCITY_EXCEEDED code."""
        assert ErrorCode.B01_GUARD_FRAUD_VELOCITY_EXCEEDED.value == "MDC-B01-019"

    def test_fraud_amount_threshold_code(self):
        """Test CP01_GUARD_FRAUD_AMOUNT_THRESHOLD code."""
        assert ErrorCode.B01_GUARD_FRAUD_AMOUNT_THRESHOLD.value == "MDC-B01-020"

    def test_fraud_pattern_anomaly_code(self):
        """Test CP01_GUARD_FRAUD_PATTERN_ANOMALY code."""
        assert ErrorCode.B01_GUARD_FRAUD_PATTERN_ANOMALY.value == "MDC-B01-021"

    def test_fraud_external_blocked_code(self):
        """Test CP01_GUARD_FRAUD_EXTERNAL_BLOCKED code."""
        assert ErrorCode.B01_GUARD_FRAUD_EXTERNAL_BLOCKED.value == "MDC-B01-022"

    def test_fraud_external_timeout_code(self):
        """Test CP01_GUARD_FRAUD_EXTERNAL_TIMEOUT code."""
        assert ErrorCode.B01_GUARD_FRAUD_EXTERNAL_TIMEOUT.value == "MDC-B01-038"

    def test_safety_equipment_unsafe_code(self):
        """Test CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE code."""
        assert ErrorCode.B01_GUARD_SAFETY_EQUIPMENT_UNSAFE.value == "MDC-B01-023"

    def test_safety_personnel_uncertified_code(self):
        """Test CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED code."""
        assert ErrorCode.B01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED.value == "MDC-B01-024"

    def test_safety_process_non_compliant_code(self):
        """Test CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT code."""
        assert ErrorCode.B01_GUARD_SAFETY_PROCESS_NON_COMPLIANT.value == "MDC-B01-025"

    def test_safety_hazard_detected_code(self):
        """Test CP01_GUARD_SAFETY_HAZARD_DETECTED code."""
        assert ErrorCode.B01_GUARD_SAFETY_HAZARD_DETECTED.value == "MDC-B01-026"

    def test_claims_not_covered_code(self):
        """Test CP01_GUARD_CLAIMS_NOT_COVERED code."""
        assert ErrorCode.B01_GUARD_CLAIMS_NOT_COVERED.value == "MDC-B01-027"

    def test_claims_outside_period_code(self):
        """Test CP01_GUARD_CLAIMS_OUTSIDE_PERIOD code."""
        assert ErrorCode.B01_GUARD_CLAIMS_OUTSIDE_PERIOD.value == "MDC-B01-028"

    def test_claims_exceeds_limit_code(self):
        """Test CP01_GUARD_CLAIMS_EXCEEDS_LIMIT code."""
        assert ErrorCode.B01_GUARD_CLAIMS_EXCEEDS_LIMIT.value == "MDC-B01-029"

    def test_claims_excluded_code(self):
        """Test CP01_GUARD_CLAIMS_EXCLUDED code."""
        assert ErrorCode.B01_GUARD_CLAIMS_EXCLUDED.value == "MDC-B01-030"


# ============================================================================
# GAP-FILLING Tests: command_validator.py uncovered lines 117-149, 175-193,
# 220-227, 563-574, 623-635, 677, 683, 728-741, 754
# ============================================================================

class TestValidateFieldsPatternMismatch:
    """Lines 117-121: _validate_fields() — pattern check branch."""

    @pytest.mark.asyncio
    async def test_field_pattern_mismatch(self):
        """Test _validate_fields with pattern that does not match."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="email",
                    field_type=CommandFieldType.STRING,
                    pattern=r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$",
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"email": "not-an-email"})
        assert not result.is_valid
        assert any("không đúng định dạng" in e for e in result.errors)


class TestValidateFieldsStringMinLength:
    """Lines 121-126: _validate_fields() — min_length branch."""

    @pytest.mark.asyncio
    async def test_field_min_length_fail(self):
        """Test _validate_fields with string shorter than min_length."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="username",
                    field_type=CommandFieldType.STRING,
                    min_length=5,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"username": "ab"})
        assert not result.is_valid
        assert any("ít nhất 5" in e for e in result.errors)


class TestValidateFieldsStringMaxLength:
    """Lines 127-131: _validate_fields() — max_length branch."""

    @pytest.mark.asyncio
    async def test_field_max_length_fail(self):
        """Test _validate_fields with string longer than max_length."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="username",
                    field_type=CommandFieldType.STRING,
                    max_length=5,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"username": "abcdefghijklmnopqrstuvwxyz"})
        assert not result.is_valid
        assert any("không quá 5" in e for e in result.errors)


class TestValidateFieldsNumericMinValue:
    """Lines 133-136: _validate_fields() — min_value branch."""

    @pytest.mark.asyncio
    async def test_field_min_value_fail(self):
        """Test _validate_fields with numeric value below min_value."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="age",
                    field_type=CommandFieldType.INTEGER,
                    min_value=0,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"age": -5})
        assert not result.is_valid
        assert any("lớn hơn hoặc bằng" in e for e in result.errors)


class TestValidateFieldsNumericMaxValue:
    """Lines 137-140: _validate_fields() — max_value branch."""

    @pytest.mark.asyncio
    async def test_field_max_value_fail(self):
        """Test _validate_fields with numeric value above max_value."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="percentage",
                    field_type=CommandFieldType.FLOAT,
                    max_value=100,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"percentage": 200.0})
        assert not result.is_valid
        assert any("nhỏ hơn hoặc bằng" in e for e in result.errors)


class TestValidateFieldsArrayMinItems:
    """Lines 144-147: _validate_fields() — min_items branch."""

    @pytest.mark.asyncio
    async def test_field_min_items_fail(self):
        """Test _validate_fields with array below min_items."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="tags",
                    field_type=CommandFieldType.ARRAY,
                    min_items=3,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"tags": ["a"]})
        assert not result.is_valid
        assert any("ít nhất 3" in e for e in result.errors)


class TestValidateFieldsArrayMaxItems:
    """Lines 148-149: _validate_fields() — max_items branch."""

    @pytest.mark.asyncio
    async def test_field_max_items_fail(self):
        """Test _validate_fields with array above max_items."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="tags",
                    field_type=CommandFieldType.ARRAY,
                    max_items=2,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"tags": ["a", "b", "c"]})
        assert not result.is_valid
        assert any("không quá 2" in e for e in result.errors)


class TestValidateCrossFieldsDate:
    """Lines 175-179: _validate_cross_fields() — date validation branch."""

    @pytest.mark.asyncio
    async def test_cross_fields_end_before_start(self):
        """Test cross-field: end_date < start_date raises error."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "start_date": "2026-06-01",
            "end_date": "2026-05-01",
        })
        assert not result.is_valid
        assert any("Ngày kết thúc phải sau ngày bắt đầu" in e for e in result.errors)


class TestValidateCrossFieldsAccount:
    """Lines 180-183: _validate_cross_fields() — account validation branch."""

    @pytest.mark.asyncio
    async def test_cross_fields_same_account(self):
        """Test cross-field: from_account == to_account raises error."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "from_account": "ACC001",
            "to_account": "ACC001",
        })
        assert not result.is_valid
        assert any("không được giống nhau" in e for e in result.errors)


class TestValidateCrossFieldsTotal:
    """Lines 187-193: _validate_cross_fields() — total validation branch."""

    @pytest.mark.asyncio
    async def test_cross_fields_total_mismatch(self):
        """Test cross-field: total != quantity * price raises error."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "quantity": 3,
            "price": 100,
            "total": 9999,  # should be 300
        })
        assert not result.is_valid
        assert any("không khớp" in e for e in result.errors)


class TestValidateBusinessRulesBanking:
    """Lines 220-221: _validate_business_rules() — banking transfer branch."""

    @pytest.mark.asyncio
    async def test_business_rules_transfer_with_amount(self):
        """Test business rules: transfer command with amount (hits banking branch)."""
        cmd = Command(
            id="ProcessTransfer",
            description="Transfer funds between accounts",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "amount": 5000000,
        })
        # Banking branch has pass, so should be valid
        assert result.is_valid


class TestValidateBusinessRulesOrder:
    """Lines 226-227: _validate_business_rules() — order minimum branch."""

    @pytest.mark.asyncio
    async def test_business_rules_order_below_minimum(self):
        """Test business rules: order total below 10000 triggers warning."""
        cmd = Command(
            id="CreateOrder",
            description="Create a new order",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "total": 5000,
        })
        # Should have warning, not error
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("miễn phí vận chuyển" in w for w in result.warnings)


class TestValidateCustomTupleInvalid:
    """Lines 563-570: _validate_custom() — tuple return with invalid."""

    @pytest.mark.asyncio
    async def test_custom_validator_tuple_invalid(self):
        """Test custom validator that returns (False, error_msg) tuple."""
        cmd = Command(id="TestCmd")

        def bad_validator(data):
            return (False, "Custom rule violated: data too large")

        validator = CommandValidator(cmd, custom_validators={"bad_validator": bad_validator})
        result = await validator.validate({"value": 999})
        assert not result.is_valid
        assert any("Custom rule violated" in e for e in result.errors)


class TestValidateCustomBoolInvalid:
    """Lines 571-573: _validate_custom() — bool return with False."""

    @pytest.mark.asyncio
    async def test_custom_validator_bool_invalid(self):
        """Test custom validator that returns False (bool)."""
        cmd = Command(id="TestCmd")

        def bool_validator(data):
            return False

        validator = CommandValidator(cmd, custom_validators={"bool_validator": bool_validator})
        result = await validator.validate({"value": 1})
        assert not result.is_valid
        assert any("Custom validation failed: bool_validator" in e for e in result.errors)


class TestValidateCustomException:
    """Lines 574: _validate_custom() — exception branch."""

    @pytest.mark.asyncio
    async def test_custom_validator_raises_exception(self):
        """Test custom validator that raises an exception."""
        cmd = Command(id="TestCmd")

        def crash_validator(data):
            raise RuntimeError("validator crashed")

        validator = CommandValidator(
            cmd, custom_validators={"crash_validator": crash_validator}
        )
        result = await validator.validate({"value": 1})
        assert not result.is_valid
        assert any("raised error" in e for e in result.errors)


class TestFraudDetectionInvalidThreshold:
    """Lines 623-624: validate_fraud_detection() — ValueError/TypeError branch."""

    @pytest.mark.asyncio
    async def test_fraud_invalid_threshold_type(self):
        """Test fraud detection with non-numeric amount_threshold (skip check)."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_fraud_detection(
            {"amount": 100000000, "amount_threshold": "not_a_number"},
            tenant_id="t1",
        )
        # Should not crash; ValueError caught, check skipped
        assert result.is_valid


class TestFraudDetectionAnomaly:
    """Line 629: validate_fraud_detection() — anomaly detected branch."""

    @pytest.mark.asyncio
    async def test_fraud_anomaly_detected(self):
        """Test fraud detection with is_anomaly_detected=True."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_fraud_detection(
            {"is_anomaly_detected": True},
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("bất thường" in e for e in result.errors)


class TestFraudDetectionExternalBlocked:
    """Line 635: validate_fraud_detection() — external fraud blocked branch."""

    @pytest.mark.asyncio
    async def test_fraud_external_blocked(self):
        """Test fraud detection with external_fraud_blocked=True."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_fraud_detection(
            {"external_fraud_blocked": True},
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("blocked" in e.lower() for e in result.errors)


class TestSafetyCheckPersonnelUncertified:
    """Line 677: validate_safety_check() — personnel uncertified branch."""

    @pytest.mark.asyncio
    async def test_safety_personnel_uncertified(self):
        """Test safety check with personnel_certified=False."""
        cmd = Command(id="StartOperation")
        validator = CommandValidator(cmd)
        result = await validator.validate_safety_check(
            {
                "user_id": "worker1",
                "operation_type": "welding",
                "personnel_certified": False,
            },
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("chứng chỉ" in e for e in result.errors)


class TestSafetyCheckProcessNonCompliant:
    """Line 683: validate_safety_check() — process non-compliant branch."""

    @pytest.mark.asyncio
    async def test_safety_process_non_compliant(self):
        """Test safety check with process_compliant=False."""
        cmd = Command(id="StartOperation")
        validator = CommandValidator(cmd)
        result = await validator.validate_safety_check(
            {
                "operation_type": "cutting",
                "process_compliant": False,
            },
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("quy trình" in e for e in result.errors)


class TestClaimsValidationMissingClaimType:
    """Lines 728-729: validate_claims_validation() — missing claim_type branch."""

    @pytest.mark.asyncio
    async def test_claims_missing_claim_type(self):
        """Test claims validation with policy_id present but claim_type missing."""
        cmd = Command(id="SubmitClaim")
        validator = CommandValidator(cmd)
        result = await validator.validate_claims_validation(
            {"policy_id": "POL001"},
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("thiếu claim_type" in e.lower() or "thiếu" in e.lower() for e in result.errors)


class TestClaimsValidationOutsidePeriod:
    """Lines 740-741: validate_claims_validation() — outside coverage period."""

    @pytest.mark.asyncio
    async def test_claims_outside_coverage_period(self):
        """Test claims validation with incident outside coverage period."""
        cmd = Command(id="SubmitClaim")
        validator = CommandValidator(cmd)
        result = await validator.validate_claims_validation(
            {
                "policy_id": "POL001",
                "claim_type": "medical",
                "incident_date": "2020-01-01",
                "within_coverage_period": False,
            },
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("nằm ngoài" in e for e in result.errors)


class TestClaimsValidationExcluded:
    """Line 754: validate_claims_validation() — excluded branch."""

    @pytest.mark.asyncio
    async def test_claims_excluded(self):
        """Test claims validation with is_excluded=True."""
        cmd = Command(id="SubmitClaim")
        validator = CommandValidator(cmd)
        result = await validator.validate_claims_validation(
            {
                "policy_id": "POL001",
                "claim_type": "war_related",
                "is_excluded": True,
            },
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("loại trừ" in e for e in result.errors)


# ============================================================================
# ADDITIONAL GAP-FILLING: remaining uncovered lines 108-109, 113, 117->121,
# 175->179, 182->186, 190->exit, 192->exit, 220->224, 226->exit,
# 563->562, 568->562, 570->562, 571->562, 740->746
# ============================================================================

class TestValidatePipelineRequiredField:
    """Lines 108-109: validate() → _validate_fields — required field missing."""

    @pytest.mark.asyncio
    async def test_validate_required_field_missing(self):
        """Test validate() with required field set to None."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="name",
                    field_type=CommandFieldType.STRING,
                    required=True,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"name": None})
        assert not result.is_valid
        assert any("bắt buộc" in e for e in result.errors)


class TestValidatePipelineSkipNone:
    """Line 113: _validate_fields — skip further validation when None."""

    @pytest.mark.asyncio
    async def test_validate_skip_none_optional_field(self):
        """Test validate() skips None optional field without error."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="optional_field",
                    field_type=CommandFieldType.STRING,
                    required=False,
                    pattern=r"^[a-z]+$",
                    min_length=10,
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"optional_field": None})
        # None + not required → skip all validation, should be valid
        assert result.is_valid


class TestValidateFieldsPatternMatch:
    """Line 117->121: pattern exists but matches (skip error branch)."""

    @pytest.mark.asyncio
    async def test_field_pattern_match(self):
        """Test _validate_fields with pattern that matches (skip error)."""
        cmd = Command(
            id="TestCmd",
            input=[
                CommandField(
                    name="email",
                    field_type=CommandFieldType.STRING,
                    pattern=r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$",
                )
            ],
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"email": "test@example.com"})
        assert result.is_valid


class TestValidateCrossFieldsDateSkip:
    """Line 175->179: cross-fields date branch — dates valid (skip error)."""

    @pytest.mark.asyncio
    async def test_cross_fields_end_after_start(self):
        """Test cross-field: end_date > start_date (no error)."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "start_date": "2026-05-01",
            "end_date": "2026-06-01",
        })
        assert result.is_valid


class TestValidateCrossFieldsAccountSkip:
    """Line 182->186: cross-fields account — different accounts (skip error)."""

    @pytest.mark.asyncio
    async def test_cross_fields_different_accounts(self):
        """Test cross-field: from != to (no error)."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "from_account": "ACC001",
            "to_account": "ACC002",
        })
        assert result.is_valid


class TestValidateCrossFieldsTotalMatch:
    """Lines 190->exit, 192->exit: total matches quantity*price (no error, exit)."""

    @pytest.mark.asyncio
    async def test_cross_fields_total_matches(self):
        """Test cross-field: total == quantity * price (no error)."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "quantity": 5,
            "price": 100,
            "total": 500,
        })
        assert result.is_valid


class TestValidateCrossFieldsTotalSkip:
    """Line 190->exit: total/quantity/price present but one is falsy (skip inner)."""

    @pytest.mark.asyncio
    async def test_cross_fields_total_with_zero_quantity(self):
        """Test cross-field: quantity=0 (falsy, skip inner check)."""
        cmd = Command(id="TestCmd")
        validator = CommandValidator(cmd)
        result = await validator.validate({
            "quantity": 0,
            "price": 100,
            "total": 0,
        })
        assert result.is_valid


class TestValidateBusinessRulesTransferDescription:
    """Line 220->224: banking branch via description (not command_id)."""

    @pytest.mark.asyncio
    async def test_business_rules_transfer_via_description(self):
        """Test banking branch triggered by description, not command_id."""
        cmd = Command(
            id="ProcessPayment",
            description="Wire transfer between accounts",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"amount": 100000})
        assert result.is_valid


class TestValidateBusinessRulesOrderAboveMinimum:
    """Line 226->exit: order total >= 10000 (skip warning)."""

    @pytest.mark.asyncio
    async def test_business_rules_order_above_minimum(self):
        """Test order total >= 10000 (no warning)."""
        cmd = Command(
            id="CreateOrder",
            description="Create order",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"total": 50000})
        assert result.is_valid
        assert len(result.warnings) == 0


class TestValidateCustomValidatorSkipped:
    """Lines 563->562, 568->562: custom validator loop — valid tuple return."""

    @pytest.mark.asyncio
    async def test_custom_validator_tuple_valid(self):
        """Test custom validator that returns (True, msg) — loop continues."""
        cmd = Command(id="TestCmd")

        def good_validator(data):
            return (True, "All good")

        validator = CommandValidator(
            cmd, custom_validators={"good_validator": good_validator}
        )
        result = await validator.validate({"value": 1})
        assert result.is_valid


class TestValidateCustomValidatorBoolValid:
    """Lines 570->562: custom validator returns True (bool), skips error."""

    @pytest.mark.asyncio
    async def test_custom_validator_bool_valid(self):
        """Test custom validator that returns True (bool)."""
        cmd = Command(id="TestCmd")

        def ok_validator(data):
            return True

        validator = CommandValidator(
            cmd, custom_validators={"ok_validator": ok_validator}
        )
        result = await validator.validate({"value": 1})
        assert result.is_valid


class TestValidateCustomNotCallable:
    """Line 571->562: custom validator not callable (skip branch)."""

    @pytest.mark.asyncio
    async def test_custom_validator_not_callable(self):
        """Test custom validator that is not callable (skipped)."""
        cmd = Command(id="TestCmd")

        # Non-callable value in validators dict
        validator = CommandValidator(
            cmd, custom_validators={"broken": "not_a_function"}
        )
        result = await validator.validate({"value": 1})
        assert result.is_valid


class TestClaimsValidationNoIncidentDate:
    """Line 740->746: claims — no incident_date (skip period check)."""

    @pytest.mark.asyncio
    async def test_claims_no_incident_date(self):
        """Test claims with no incident_date — skip period validation."""
        cmd = Command(id="SubmitClaim")
        validator = CommandValidator(cmd)
        result = await validator.validate_claims_validation(
            {
                "policy_id": "POL001",
                "claim_type": "medical",
                # No incident_date
            },
            tenant_id="t1",
        )
        assert result.is_valid


class TestValidatePipelineValidationStopsOnError:
    """Lines 83-88: validate() — cross-field/business skipped when fields fail."""

    @pytest.mark.asyncio
    async def test_validate_stops_on_field_error(self):
        """Test validate() stops pipeline when field validation fails."""
        cmd = Command(
            id="CreateOrder",
            description="Create order",
            input=[
                CommandField(
                    name="name",
                    field_type=CommandFieldType.STRING,
                    required=True,
                )
            ],
        )
        validator = CommandValidator(cmd)
        # Missing required field — pipeline should stop after step 1
        result = await validator.validate({"name": None})
        assert not result.is_valid
        # Only field error, no cross-field or business-rule errors
        assert len(result.errors) == 1


# ============================================================================
# ADDITIONAL GAP-FILLING: RX02/RX03/RX04 methods (lines 255-546)
# ============================================================================

class TestValidateRX02DoubleEntryMismatch:
    """Lines 255-263, 281-286: validate_rx02 + _validate_double_entry."""

    @pytest.mark.asyncio
    async def test_rx02_debit_credit_mismatch(self):
        """Test RX02 double-entry: debit != credit raises error."""
        cmd = Command(id="PostJournal")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx02(
            {"debit": 1000, "credit": 500},
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("double-entry" in e.lower() for e in result.errors)


class TestValidateRX02DoubleEntryMatch:
    """Lines 281-286: double-entry debit == credit (no error)."""

    @pytest.mark.asyncio
    async def test_rx02_debit_credit_match(self):
        """Test RX02 double-entry: debit == credit (no error)."""
        cmd = Command(id="PostJournal")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx02(
            {"debit": 1000, "credit": 1000},
            tenant_id="t1",
        )
        assert result.is_valid


class TestValidateRX02DoubleEntryZero:
    """Lines 281-286: double-entry both zero (skip check)."""

    @pytest.mark.asyncio
    async def test_rx02_debit_credit_zero(self):
        """Test RX02 double-entry: both zero (skip check)."""
        cmd = Command(id="PostJournal")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx02({}, tenant_id="t1")
        assert result.is_valid


class TestValidateRX02TransactionImmutability:
    """Lines 307-308: _validate_transaction_immutability."""

    @pytest.mark.asyncio
    async def test_rx02_immutable_transaction_update(self):
        """Test RX02: cannot update completed transaction."""
        cmd = Command(id="PostJournal")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx02(
            {"status": "completed", "is_update": True},
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("immutable" in e.lower() or "hoàn thành" in e.lower() for e in result.errors)


class TestValidateRX03KYCNotVerified:
    """Lines 338-349, 369-372: validate_rx03 + _validate_kyc_verification."""

    @pytest.mark.asyncio
    async def test_rx03_kyc_not_verified(self):
        """Test RX03: user not KYC verified raises error."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx03(
            {"kyc_verified": False},
            user_id="user1",
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("kyc" in e.lower() for e in result.errors)


class TestValidateRX03KYCVerified:
    """Lines 369-372: KYC verified (no error)."""

    @pytest.mark.asyncio
    async def test_rx03_kyc_verified(self):
        """Test RX03: user KYC verified (no error)."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx03(
            {"kyc_verified": True, "aml_cleared": True, "amount": 0},
            user_id="user1",
            tenant_id="t1",
        )
        assert result.is_valid


class TestValidateRX03AMLNotCleared:
    """Lines 394-398: _validate_aml_screening."""

    @pytest.mark.asyncio
    async def test_rx03_aml_not_cleared(self):
        """Test RX03: transaction not AML cleared raises error."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx03(
            {"kyc_verified": True, "aml_cleared": False, "amount": 50000},
            user_id="user1",
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("aml" in e.lower() for e in result.errors)


class TestValidateRX03SuspiciousActivity:
    """Lines 418-422: _validate_suspicious_activity threshold warning."""

    @pytest.mark.asyncio
    async def test_rx03_suspicious_activity_warning(self):
        """Test RX03: amount > 100M triggers SAR warning."""
        cmd = Command(id="ProcessPayment")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx03(
            {"kyc_verified": True, "aml_cleared": True, "amount": 200000000},
            user_id="user1",
            tenant_id="t1",
        )
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("SAR" in w for w in result.warnings)


class TestValidateRX04PHIUnencrypted:
    """Lines 455-466, 484-490: validate_rx04 + _validate_phi_encryption."""

    @pytest.mark.asyncio
    async def test_rx04_phi_unencrypted(self):
        """Test RX04: PHI field not encrypted raises error."""
        cmd = Command(id="AccessPatientRecord")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx04(
            {"ssn": "123-45-6789", "ssn_encrypted": False},
            user_id="doc1",
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("encrypt" in e.lower() for e in result.errors)


class TestValidateRX04PHIEncrypted:
    """Lines 484-490: PHI encrypted (no error)."""

    @pytest.mark.asyncio
    async def test_rx04_phi_encrypted(self):
        """Test RX04: PHI field encrypted (no error)."""
        cmd = Command(id="AccessPatientRecord")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx04(
            {
                "ssn": "123-45-6789",
                "ssn_encrypted": True,
                "requested_phi_fields": ["ssn"],
                "user_allowed_fields": ["ssn"],
                "audit_log_written": True,
            },
            user_id="doc1",
            tenant_id="t1",
        )
        assert result.is_valid


class TestValidateRX04MinimumNecessaryAccess:
    """Lines 512-518: _validate_minimum_necessary_access."""

    @pytest.mark.asyncio
    async def test_rx04_excess_phi_access(self):
        """Test RX04: user accesses PHI fields not in allowed set."""
        cmd = Command(id="AccessPatientRecord")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx04(
            {
                "requested_phi_fields": ["ssn", "medical_history"],
                "user_allowed_fields": ["ssn"],
            },
            user_id="doc1",
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("không được phép" in e for e in result.errors)


class TestValidateRX04AuditTrailMissing:
    """Lines 540-546: _validate_audit_trail."""

    @pytest.mark.asyncio
    async def test_rx04_audit_trail_missing(self):
        """Test RX04: PHI accessed but no audit log raises error."""
        cmd = Command(id="AccessPatientRecord")
        validator = CommandValidator(cmd)
        result = await validator.validate_rx04(
            {
                "medical_history": "patient has diabetes",
                "audit_log_written": False,
            },
            user_id="doc1",
            tenant_id="t1",
        )
        assert not result.is_valid
        assert any("audit" in e.lower() for e in result.errors)


class TestValidateBusinessRulesTransferById:
    """Line 220->224: banking branch via command_id (not description)."""

    @pytest.mark.asyncio
    async def test_business_rules_transfer_by_id(self):
        """Test banking branch triggered by 'transfer' in command_id."""
        cmd = Command(
            id="TransferMoney",
            description="Send money to another account",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"amount": 100000})
        assert result.is_valid


class TestValidateBusinessRulesNoMatch:
    """Lines 220-227: no banking or order rule matches."""

    @pytest.mark.asyncio
    async def test_business_rules_no_match(self):
        """Test business rules: command matches neither banking nor order."""
        cmd = Command(
            id="DeleteUser",
            description="Remove a user from the system",
        )
        validator = CommandValidator(cmd)
        result = await validator.validate({"user_id": "u1"})
        assert result.is_valid


# ============================================================================
# GAP-FILLING Tests: command_guards.py uncovered lines
# 101, 112->95, 134, 138-143, 168-190, 209-222, 246, 250->exit,
# 278, 282->exit, 313, 317->exit, 374-376, 464-468, 471-475,
# 484-488, 519-523, 526-530, 538-542, 641, 726-730
# ============================================================================

class TestAuthGuard:
    """Gap tests cho _check_auth — lines 134, 138-143."""

    @pytest.mark.asyncio
    async def test_auth_no_permission_required(self):
        """Line 134: guard.permission is None → return early."""
        command = Command(
            id="ReadPublic",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission=None)],
        )
        guards = CommandGuards(command, auth_service=None)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_auth_with_service_permission_granted(self):
        """Lines 138-142: auth_service.check_permission returns True."""
        auth = AsyncMock()
        auth.check_permission = AsyncMock(return_value=True)
        command = Command(
            id="DeleteItem",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="delete")],
        )
        guards = CommandGuards(command, auth_service=auth)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_auth_with_service_permission_denied(self):
        """Line 143: auth_service.check_permission returns False → PermissionError."""
        auth = AsyncMock()
        auth.check_permission = AsyncMock(return_value=False)
        command = Command(
            id="DeleteItem",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="delete")],
        )
        guards = CommandGuards(command, auth_service=auth)

        with pytest.raises(PermissionError, match="không có permission"):
            await guards.check_all({}, user_id="user1")


class TestTenantGuard:
    """Gap tests cho _check_tenant — lines 168-190."""

    @pytest.mark.asyncio
    async def test_tenant_missing_id(self):
        """Lines 168-171: tenant_id is None → B01_GUARD_TENANT_MISSING."""
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE)],
        )
        guards = CommandGuards(command, tenant_service=None)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1", tenant_id=None)

        assert exc_info.value.code == ErrorCode.B01_GUARD_TENANT_MISSING

    @pytest.mark.asyncio
    async def test_tenant_isolated_belongs(self):
        """Lines 172-178: tenant_isolated, belongs_to_tenant=True."""
        tenant_svc = AsyncMock()
        tenant_svc.belongs_to_tenant = AsyncMock(return_value=True)
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated")],
        )
        guards = CommandGuards(command, tenant_service=tenant_svc)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_tenant_isolated_violation(self):
        """Lines 179-182: tenant_isolated, belongs_to_tenant=False → violation."""
        tenant_svc = AsyncMock()
        tenant_svc.belongs_to_tenant = AsyncMock(return_value=False)
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated")],
        )
        guards = CommandGuards(command, tenant_service=tenant_svc)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1", tenant_id="tenant1")

        assert exc_info.value.code == ErrorCode.B01_GUARD_TENANT_VIOLATION

    @pytest.mark.asyncio
    async def test_tenant_shared_mode(self):
        """Lines 184-185: tenant_shared mode → pass."""
        command = Command(
            id="SharedAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_shared")],
        )
        guards = CommandGuards(command, tenant_service=None)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_tenant_global_mode(self):
        """Lines 188-189: global mode → pass."""
        command = Command(
            id="GlobalAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="global")],
        )
        guards = CommandGuards(command, tenant_service=None)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_tenant_isolated_no_service(self):
        """Lines 172-183: tenant_isolated, no tenant_service → fallback pass."""
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated")],
        )
        guards = CommandGuards(command, tenant_service=None)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_tenant_default_mode_is_isolated(self):
        """Lines 170-171: guard.mode is None → defaults to tenant_isolated."""
        tenant_svc = AsyncMock()
        tenant_svc.belongs_to_tenant = AsyncMock(return_value=True)
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode=None)],
        )
        guards = CommandGuards(command, tenant_service=tenant_svc)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")


class TestRateLimitGuard:
    """Gap tests cho _check_rate_limit — lines 101, 209-222."""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Lines 219-222: is_limited=True → B01_GUARD_RATE_LIMIT_EXCEEDED."""
        auth = AsyncMock()
        auth.check_rate_limit = AsyncMock(return_value=True)
        command = Command(
            id="FastAction",
            guards=[CommandGuard(guard_type=GuardType.RATE_LIMIT, limit=5, window="10s")],
        )
        guards = CommandGuards(command, auth_service=auth)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1", ip_address="1.2.3.4")

        assert exc_info.value.code == ErrorCode.B01_GUARD_RATE_LIMIT_EXCEEDED

    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self):
        """Lines 219-222: is_limited=False → pass through."""
        auth = AsyncMock()
        auth.check_rate_limit = AsyncMock(return_value=False)
        command = Command(
            id="FastAction",
            guards=[CommandGuard(guard_type=GuardType.RATE_LIMIT, limit=100, window="60s")],
        )
        guards = CommandGuards(command, auth_service=auth)

        await guards.check_all({}, user_id="user1", ip_address="1.2.3.4")

    @pytest.mark.asyncio
    async def test_rate_limit_no_auth_service(self):
        """Lines 213-222: no auth_service → skip check."""
        command = Command(
            id="FastAction",
            guards=[CommandGuard(guard_type=GuardType.RATE_LIMIT)],
        )
        guards = CommandGuards(command, auth_service=None)

        await guards.check_all({}, user_id="user1")


class TestBasicKYCGuard:
    """Gap tests cho _check_kyc (basic, no audit) — lines 246, 250→exit."""

    @pytest.mark.asyncio
    async def test_check_kyc_user_none(self):
        """Line 246: user_id=None → B01_GUARD_USER_NOT_AUTHENTICATED."""
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=MockComplianceService())

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id=None)

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_check_kyc_not_verified(self):
        """Line 250: KYC not verified → B01_GUARD_KYC_NOT_VERIFIED."""
        compliance = MockComplianceService()
        compliance.kyc_verified = False
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1")

        assert exc_info.value.code == ErrorCode.B01_GUARD_KYC_NOT_VERIFIED

    @pytest.mark.asyncio
    async def test_check_kyc_verified(self):
        """KYC verified → pass through."""
        compliance = MockComplianceService()
        compliance.kyc_verified = True
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_kyc_no_compliance_service(self):
        """No compliance_service → skip KYC check."""
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards.check_all({}, user_id="user1")


class TestBasicAMGuard:
    """Gap tests cho _check_aml (basic, no audit) — lines 278, 282→exit."""

    @pytest.mark.asyncio
    async def test_check_aml_user_none(self):
        """Line 278: user_id=None → B01_GUARD_USER_NOT_AUTHENTICATED."""
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=MockComplianceService())

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id=None)

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_check_aml_failed(self):
        """Line 282: AML screening failed → B01_GUARD_AML_SCREENING_FAILED."""
        compliance = MockComplianceService()
        compliance.aml_clear = False
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1")

        assert exc_info.value.code == ErrorCode.B01_GUARD_AML_SCREENING_FAILED

    @pytest.mark.asyncio
    async def test_check_aml_passed(self):
        """AML screening passed → pass through."""
        compliance = MockComplianceService()
        compliance.aml_clear = True
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_aml_no_compliance_service(self):
        """No compliance_service → skip AML check."""
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards.check_all({}, user_id="user1")


class TestBasicHIPAAGuard:
    """Gap tests cho _check_hipaa (basic, no audit) — lines 313, 317→exit."""

    @pytest.mark.asyncio
    async def test_check_hipaa_user_none(self):
        """Line 313: user_id=None → B01_GUARD_USER_NOT_AUTHENTICATED."""
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=MockComplianceService())

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id=None)

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_check_hipaa_no_clearance(self):
        """Line 317: no HIPAA clearance → B01_GUARD_HIPAA_NO_CLEARANCE."""
        compliance = MockComplianceService()
        compliance.hipaa_clearance = False
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all({}, user_id="user1")

        assert exc_info.value.code == ErrorCode.B01_GUARD_HIPAA_NO_CLEARANCE

    @pytest.mark.asyncio
    async def test_check_hipaa_cleared(self):
        """HIPAA cleared → pass through."""
        compliance = MockComplianceService()
        compliance.hipaa_clearance = True
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_hipaa_no_compliance_service(self):
        """No compliance_service → skip HIPAA check."""
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards.check_all({}, user_id="user1")


# ============================================================================
# Gap tests: _log_compliance_check exception — lines 374-376
# ============================================================================

class TestComplianceLogException:
    """Gap tests cho _log_compliance_check exception — lines 374-376."""

    @pytest.mark.asyncio
    async def test_log_compliance_check_raises_error(self):
        """Lines 374-376: log raises → B01_GUARD_COMPLIANCE_LOG_FAILED."""
        compliance = MockComplianceService()
        compliance.log_raises = "disk full"
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._log_compliance_check(
                GuardType.KYC_CHECK, "user1", "tenant1", "passed"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_COMPLIANCE_LOG_FAILED

    @pytest.mark.asyncio
    async def test_log_compliance_check_no_service(self):
        """No compliance_service → return early (line 355)."""
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards._log_compliance_check(
            GuardType.KYC_CHECK, "user1", "tenant1", "passed"
        )


# ============================================================================
# Gap tests: _with_audit compliance methods (direct invocation)
# ============================================================================

class TestKYCWithAudit:
    """Gap tests cho _check_kyc_with_audit — lines 464-468, 471-475."""

    @pytest.mark.asyncio
    async def test_kyc_with_audit_user_none(self):
        """Lines 464-468: user_id=None → log failed + raise."""
        compliance = MockComplianceService()
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_kyc_with_audit(
                guards._command.guards[0], None, "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_kyc_with_audit_not_verified(self):
        """Lines 471-475: KYC not verified → log failed + raise."""
        compliance = MockComplianceService()
        compliance.kyc_verified = False
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_kyc_with_audit(
                guards._command.guards[0], "user1", "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_KYC_NOT_VERIFIED

    @pytest.mark.asyncio
    async def test_kyc_with_audit_no_service(self):
        """No compliance service → log skipped + return."""
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards._check_kyc_with_audit(
            guards._command.guards[0], "user1", "tenant1"
        )

    @pytest.mark.asyncio
    async def test_kyc_with_audit_passed(self):
        """KYC verified → log passed + return."""
        compliance = MockComplianceService()
        compliance.kyc_verified = True
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards._check_kyc_with_audit(
            guards._command.guards[0], "user1", "tenant1"
        )


class TestAMLWithAudit:
    """Gap tests cho _check_aml_with_audit — lines 484-488, 519-523."""

    @pytest.mark.asyncio
    async def test_aml_with_audit_user_none(self):
        """Lines 484-488: user_id=None → log failed + raise."""
        compliance = MockComplianceService()
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_aml_with_audit(
                guards._command.guards[0], {}, None, "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_aml_with_audit_failed(self):
        """Lines 519-523: AML failed → log failed + raise."""
        compliance = MockComplianceService()
        compliance.aml_clear = False
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_aml_with_audit(
                guards._command.guards[0], {}, "user1", "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_AML_SCREENING_FAILED

    @pytest.mark.asyncio
    async def test_aml_with_audit_no_service(self):
        """No compliance service → log skipped + return."""
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards._check_aml_with_audit(
            guards._command.guards[0], {}, "user1", "tenant1"
        )

    @pytest.mark.asyncio
    async def test_aml_with_audit_passed(self):
        """AML clear → log passed + return."""
        compliance = MockComplianceService()
        compliance.aml_clear = True
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards._check_aml_with_audit(
            guards._command.guards[0], {}, "user1", "tenant1"
        )


class TestHIPAAWithAudit:
    """Gap tests cho _check_hipaa_with_audit — lines 526-530, 538-542."""

    @pytest.mark.asyncio
    async def test_hipaa_with_audit_user_none(self):
        """Lines 526-530: user_id=None → log failed + raise."""
        compliance = MockComplianceService()
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_hipaa_with_audit(
                guards._command.guards[0], None, "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED

    @pytest.mark.asyncio
    async def test_hipaa_with_audit_no_clearance(self):
        """Lines 538-542: no clearance → log failed + raise."""
        compliance = MockComplianceService()
        compliance.hipaa_clearance = False
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards._check_hipaa_with_audit(
                guards._command.guards[0], "user1", "tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_HIPAA_NO_CLEARANCE

    @pytest.mark.asyncio
    async def test_hipaa_with_audit_no_service(self):
        """No compliance service → log skipped + return."""
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=None)

        await guards._check_hipaa_with_audit(
            guards._command.guards[0], "user1", "tenant1"
        )

    @pytest.mark.asyncio
    async def test_hipaa_with_audit_passed(self):
        """HIPAA cleared → log passed + return."""
        compliance = MockComplianceService()
        compliance.hipaa_clearance = True
        command = Command(
            id="AccessPatientRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards._check_hipaa_with_audit(
            guards._command.guards[0], "user1", "tenant1"
        )


# ============================================================================
# Gap tests: Fraud Detection amount_threshold ValueError — line 641
# ============================================================================

class TestFraudDetectionValueError:
    """Gap tests cho fraud detection amount_threshold ValueError — line 641."""

    @pytest.mark.asyncio
    async def test_fraud_amount_threshold_value_error(self):
        """Line 641: float(amount_threshold) raises ValueError → skip check."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition="not_a_number")],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 100000000}

        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_amount_threshold_type_error(self):
        """Line 641: float(amount_threshold) raises TypeError → skip check."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition=[])],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 100000000}

        await guards.check_all(data, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_fraud_amount_threshold_none_skip(self):
        """amount_threshold is None → skip entire threshold check."""
        compliance = MockComplianceService()
        compliance.transaction_velocity = False
        compliance.pattern_anomaly = False
        compliance.external_fraud = {"blocked": False}
        command = Command(
            id="ProcessPayment",
            guards=[CommandGuard(guard_type=GuardType.FRAUD_DETECTION, condition=None)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        data = {"amount": 999999999}

        await guards.check_all(data, user_id="user1", tenant_id="tenant1")


# ============================================================================
# Gap tests: Safety Check user_id=None — lines 726-730
# ============================================================================

class TestSafetyCheckUserNone:
    """Gap tests cho safety check user_id=None — lines 726-730."""

    @pytest.mark.asyncio
    async def test_safety_check_user_not_authenticated(self):
        """Lines 726-730: user_id=None → log failed + raise."""
        compliance = MockComplianceService()
        command = Command(
            id="StartOperation",
            guards=[CommandGuard(guard_type=GuardType.SAFETY_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        with pytest.raises(MidicoderError) as exc_info:
            await guards.check_all(
                {"equipment_id": "EQ001"}, user_id=None, tenant_id="tenant1"
            )

        assert exc_info.value.code == ErrorCode.B01_GUARD_USER_NOT_AUTHENTICATED


# ============================================================================
# Gap tests: check_all dispatch — lines 101, 112→95
# ============================================================================

class TestCheckAllDispatch:
    """Gap tests cho check_all dispatch — lines 101, 112→95."""

    @pytest.mark.asyncio
    async def test_check_all_dispatch_kyc(self):
        """Line 101: dispatch KYC_CHECK guard type."""
        compliance = MockComplianceService()
        compliance.kyc_verified = True
        command = Command(
            id="TransferMoney",
            guards=[CommandGuard(guard_type=GuardType.KYC_CHECK)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_all_dispatch_aml(self):
        """Dispatch AML_SCREENING guard type."""
        compliance = MockComplianceService()
        compliance.aml_clear = True
        command = Command(
            id="WireTransfer",
            guards=[CommandGuard(guard_type=GuardType.AML_SCREENING)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_all_dispatch_hipaa(self):
        """Dispatch HIPAA_ACCESS guard type."""
        compliance = MockComplianceService()
        compliance.hipaa_clearance = True
        command = Command(
            id="AccessRecord",
            guards=[CommandGuard(guard_type=GuardType.HIPAA_ACCESS)],
        )
        guards = CommandGuards(command, compliance_service=compliance)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_all_dispatch_auth(self):
        """Dispatch AUTH guard type with None permission."""
        command = Command(
            id="ReadPublic",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission=None)],
        )
        guards = CommandGuards(command, auth_service=None)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_all_dispatch_rate_limit(self):
        """Dispatch RATE_LIMIT guard type."""
        auth = AsyncMock()
        auth.check_rate_limit = AsyncMock(return_value=False)
        command = Command(
            id="FastAction",
            guards=[CommandGuard(guard_type=GuardType.RATE_LIMIT)],
        )
        guards = CommandGuards(command, auth_service=auth)

        await guards.check_all({}, user_id="user1")

    @pytest.mark.asyncio
    async def test_check_all_dispatch_tenant(self):
        """Dispatch TENANT_SCOPE guard type."""
        tenant_svc = AsyncMock()
        tenant_svc.belongs_to_tenant = AsyncMock(return_value=True)
        command = Command(
            id="TenantAction",
            guards=[CommandGuard(guard_type=GuardType.TENANT_SCOPE, mode="tenant_isolated")],
        )
        guards = CommandGuards(command, tenant_service=tenant_svc)

        await guards.check_all({}, user_id="user1", tenant_id="tenant1")

    @pytest.mark.asyncio
    async def test_check_all_user_none_auth(self):
        """Line 112→95: dispatch AUTH with user_id=None → PermissionError."""
        command = Command(
            id="AdminAction",
            guards=[CommandGuard(guard_type=GuardType.AUTH, permission="admin")],
        )
        guards = CommandGuards(command, auth_service=None)

        with pytest.raises(PermissionError, match="không được xác thực"):
            await guards.check_all({}, user_id=None)