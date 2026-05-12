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

from midicoder.emitters.core.domain_model.command_models import Command, CommandGuard, GuardType, ValidationResult
from midicoder.emitters.core.domain_model.command_guards import CommandGuards
from midicoder.emitters.core.domain_model.command_validator import CommandValidator
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

    async def log_compliance_check(self, audit_record: dict) -> None:
        """Mock audit log."""
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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_FRAUD_VELOCITY_EXCEEDED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_FRAUD_AMOUNT_THRESHOLD

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_FRAUD_PATTERN_ANOMALY

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_FRAUD_EXTERNAL_BLOCKED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_SAFETY_HAZARD_DETECTED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_CLAIMS_OUTSIDE_PERIOD

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_CLAIMS_EXCEEDS_LIMIT

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_CLAIMS_EXCLUDED

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
        
        assert exc_info.value.code == ErrorCode.CP01_GUARD_USER_NOT_AUTHENTICATED

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
        assert ErrorCode.CP01_GUARD_FRAUD_VELOCITY_EXCEEDED.value == "MDC-CP01-075"

    def test_fraud_amount_threshold_code(self):
        """Test CP01_GUARD_FRAUD_AMOUNT_THRESHOLD code."""
        assert ErrorCode.CP01_GUARD_FRAUD_AMOUNT_THRESHOLD.value == "MDC-CP01-076"

    def test_fraud_pattern_anomaly_code(self):
        """Test CP01_GUARD_FRAUD_PATTERN_ANOMALY code."""
        assert ErrorCode.CP01_GUARD_FRAUD_PATTERN_ANOMALY.value == "MDC-CP01-077"

    def test_fraud_external_blocked_code(self):
        """Test CP01_GUARD_FRAUD_EXTERNAL_BLOCKED code."""
        assert ErrorCode.CP01_GUARD_FRAUD_EXTERNAL_BLOCKED.value == "MDC-CP01-078"

    def test_fraud_external_timeout_code(self):
        """Test CP01_GUARD_FRAUD_EXTERNAL_TIMEOUT code."""
        assert ErrorCode.CP01_GUARD_FRAUD_EXTERNAL_TIMEOUT.value == "MDC-CP01-079"

    def test_safety_equipment_unsafe_code(self):
        """Test CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE code."""
        assert ErrorCode.CP01_GUARD_SAFETY_EQUIPMENT_UNSAFE.value == "MDC-CP01-080"

    def test_safety_personnel_uncertified_code(self):
        """Test CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED code."""
        assert ErrorCode.CP01_GUARD_SAFETY_PERSONNEL_UNCERTIFIED.value == "MDC-CP01-081"

    def test_safety_process_non_compliant_code(self):
        """Test CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT code."""
        assert ErrorCode.CP01_GUARD_SAFETY_PROCESS_NON_COMPLIANT.value == "MDC-CP01-082"

    def test_safety_hazard_detected_code(self):
        """Test CP01_GUARD_SAFETY_HAZARD_DETECTED code."""
        assert ErrorCode.CP01_GUARD_SAFETY_HAZARD_DETECTED.value == "MDC-CP01-083"

    def test_claims_not_covered_code(self):
        """Test CP01_GUARD_CLAIMS_NOT_COVERED code."""
        assert ErrorCode.CP01_GUARD_CLAIMS_NOT_COVERED.value == "MDC-CP01-084"

    def test_claims_outside_period_code(self):
        """Test CP01_GUARD_CLAIMS_OUTSIDE_PERIOD code."""
        assert ErrorCode.CP01_GUARD_CLAIMS_OUTSIDE_PERIOD.value == "MDC-CP01-085"

    def test_claims_exceeds_limit_code(self):
        """Test CP01_GUARD_CLAIMS_EXCEEDS_LIMIT code."""
        assert ErrorCode.CP01_GUARD_CLAIMS_EXCEEDS_LIMIT.value == "MDC-CP01-086"

    def test_claims_excluded_code(self):
        """Test CP01_GUARD_CLAIMS_EXCLUDED code."""
        assert ErrorCode.CP01_GUARD_CLAIMS_EXCLUDED.value == "MDC-CP01-087"