"""
Tests cho Domain Invariants - Epic E10: Invariant Gates (E10-011)

Module này test các domain-specific invariants:
- Banking: Double-entry balance, KYC verification
- Healthcare: PHI encryption, Clinical audit trail
- Exchange: Order risk check, Settlement atomicity

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.contracts.artifact import ArtifactMetadata
from midicoder.contracts.graph import CapabilityGraph, CapabilityInstance
from midicoder.contracts.validation import (
    InvariantValidator,
    ValidationReport,
    ErrorCode,
    ValidationStatus,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_metadata() -> ArtifactMetadata:
    """Trả về sample metadata cho testing."""
    return ArtifactMetadata(
        created_at="2026-04-21T11:00:00Z",
        updated_at="2026-04-21T11:00:00Z",
        author="test",
        organization="midicoder",
        version="1.0.0",
        generated_by="test",
        git_commit="abc123",
        description="Test metadata",
        tags=["test"],
        source_files=[],
    )


@pytest.fixture
def banking_graph_with_balanced_entries(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Banking domain với double-entry balanced.
    
    Dành cho test FIN_DOUBLE_ENTRY_IMBALANCE - valid case.
    """
    # Ledger entry với debit = credit (balanced)
    ledger_entry = CapabilityInstance(
        id="transfer_funds",
        type="authorized_mutation",
        description="Transfer funds với balanced entries",
        params={
            "permission": "finance.transfer",
            "transaction": "required",
            "domain": "banking",
            "double_entry": {
                "entries": [
                    {"account": "ACCT_001", "debit": 1000, "credit": 0},
                    {"account": "ACCT_002", "debit": 0, "credit": 1000},
                ],
            },
        },
        writes=["LedgerEntry"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[ledger_entry],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def banking_graph_with_imbalanced_entries(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Banking domain với double-entry imbalanced.
    
    Dành cho test FIN_DOUBLE_ENTRY_IMBALANCE - invalid case.
    """
    # Ledger entry với debit != credit (imbalanced)
    ledger_entry = CapabilityInstance(
        id="unbalanced_transfer",
        type="authorized_mutation",
        description="Unbalanced transfer - debit not equal to credit",
        params={
            "permission": "finance.transfer",
            "transaction": "required",
            "domain": "banking",
            "double_entry": {
                "entries": [
                    {"account": "ACCT_001", "debit": 1000, "credit": 0},
                    {"account": "ACCT_002", "debit": 0, "credit": 500},  # Imbalanced!
                ],
            },
        },
        writes=["LedgerEntry"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[ledger_entry],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def banking_graph_with_kyc_verified(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Banking domain với KYC verified.
    
    Dành cho test FIN_KYC_NOT_VERIFIED - valid case.
    """
    transfer_instance = CapabilityInstance(
        id="kyc_verified_transfer",
        type="authorized_mutation",
        description="Transfer với KYC đã verify",
        params={
            "permission": "finance.transfer",
            "transaction": "required",
            "domain": "banking",
            "kyc_verified": True,  # KYC đã verify
            "requires_kyc": True,
        },
        writes=["Transaction"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[transfer_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def banking_graph_without_kyc(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Banking domain không có KYC.
    
    Dành cho test FIN_KYC_NOT_VERIFIED - invalid case.
    """
    transfer_instance = CapabilityInstance(
        id="no_kyc_transfer",
        type="authorized_mutation",
        description="Transfer KHÔNG có KYC verification",
        params={
            "permission": "finance.transfer",
            "transaction": "required",
            "domain": "banking",
            "requires_kyc": True,  # Yêu cầu KYC nhưng không có kyc_verified
            # Thiếu kyc_verified = True
        },
        writes=["Transaction"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[transfer_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def healthcare_graph_with_phi_encrypted(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Healthcare domain với PHI encrypted.
    
    Dành cho test HLT_PHI_NOT_ENCRYPTED - valid case.
    """
    patient_record = CapabilityInstance(
        id="store_patient_record",
        type="authorized_mutation",
        description="Store patient record với PHI encryption",
        params={
            "permission": "healthcare.write",
            "transaction": "required",
            "domain": "healthcare",
            "phi_fields": ["ssn", "medical_history", "diagnosis"],
            "encryption_enabled": True,  # PHI được encrypt
            "encryption_algorithm": "AES-256",
        },
        writes=["PatientRecord"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[patient_record],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def healthcare_graph_with_phi_unencrypted(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Healthcare domain với PHI NOT encrypted.
    
    Dành cho test HLT_PHI_NOT_ENCRYPTED - invalid case.
    """
    patient_record = CapabilityInstance(
        id="store_patient_record_no_enc",
        type="authorized_mutation",
        description="Store patient record KHÔNG có PHI encryption",
        params={
            "permission": "healthcare.write",
            "transaction": "required",
            "domain": "healthcare",
            "phi_fields": ["ssn", "medical_history", "diagnosis"],  # Có PHI fields
            "encryption_enabled": False,  # KHÔNG encrypt!
        },
        writes=["PatientRecord"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[patient_record],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def healthcare_graph_with_audit_trail(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Healthcare domain với clinical audit trail.
    
    Dành cho test HLT_MISSING_CLINICAL_AUDIT - valid case.
    """
    clinical_action = CapabilityInstance(
        id="clinical_procedure",
        type="authorized_mutation",
        description="Clinical procedure với audit trail",
        params={
            "permission": "healthcare.clinical",
            "transaction": "required",
            "domain": "healthcare",
            "clinical_action": True,
            "audit_trail_enabled": True,  # Audit trail enabled
            "audit_fields": ["provider_id", "timestamp", "action_type"],
        },
        writes=["ClinicalRecord"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[clinical_action],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def healthcare_graph_without_audit_trail(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Healthcare domain không có clinical audit trail.
    
    Dành cho test HLT_MISSING_CLINICAL_AUDIT - invalid case.
    """
    clinical_action = CapabilityInstance(
        id="clinical_procedure_no_audit",
        type="authorized_mutation",
        description="Clinical procedure KHÔNG có audit trail",
        params={
            "permission": "healthcare.clinical",
            "transaction": "required",
            "domain": "healthcare",
            "clinical_action": True,
            "audit_trail_enabled": False,  # KHÔNG có audit trail!
        },
        writes=["ClinicalRecord"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[clinical_action],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def exchange_graph_with_risk_check(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Exchange domain với risk check.
    
    Dành cho test EXC_ORDER_RISK_CHECK_MISSING - valid case.
    """
    order_instance = CapabilityInstance(
        id="place_order",
        type="authorized_mutation",
        description="Place order với risk check",
        params={
            "permission": "exchange.trade",
            "transaction": "required",
            "domain": "exchange",
            "order_type": "limit",
            "risk_check_enabled": True,  # Risk check enabled
            "risk_checks": ["position_limit", "credit_check", "market_impact"],
        },
        writes=["Order"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[order_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def exchange_graph_without_risk_check(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Exchange domain không có risk check.
    
    Dành cho test EXC_ORDER_RISK_CHECK_MISSING - invalid case.
    """
    order_instance = CapabilityInstance(
        id="place_order_no_risk",
        type="authorized_mutation",
        description="Place order KHÔNG có risk check",
        params={
            "permission": "exchange.trade",
            "transaction": "required",
            "domain": "exchange",
            "order_type": "limit",
            "risk_check_enabled": False,  # KHÔNG có risk check!
        },
        writes=["Order"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[order_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def exchange_graph_with_atomic_settlement(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Exchange domain với atomic settlement.
    
    Dành cho test EXC_SETTLEMENT_NOT_ATOMIC - valid case.
    """
    settlement_instance = CapabilityInstance(
        id="settle_trade",
        type="authorized_mutation",
        description="Settlement với atomic transaction",
        params={
            "permission": "exchange.settle",
            "transaction": "required",  # Transaction required = atomic
            "domain": "exchange",
            "settlement_type": "delivery_vs_payment",
            "atomic_settlement": True,  # Atomic settlement
        },
        writes=["Settlement"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[settlement_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def exchange_graph_without_atomic_settlement(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph cho Exchange domain không có atomic settlement.
    
    Dành cho test EXC_SETTLEMENT_NOT_ATOMIC - invalid case.
    """
    settlement_instance = CapabilityInstance(
        id="settle_trade_not_atomic",
        type="authorized_mutation",
        description="Settlement KHÔNG atomic",
        params={
            "permission": "exchange.settle",
            "transaction": "not_required",  # Transaction NOT required!
            "domain": "exchange",
            "settlement_type": "delivery_vs_payment",
            "atomic_settlement": False,  # KHÔNG atomic!
        },
        writes=["Settlement"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        instances=[settlement_instance],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


# ============================================================================
# Test Banking: Double-Entry Balance
# ============================================================================


class TestBankingDoubleEntryBalance:
    """Tests cho Banking domain: Double-entry must balance."""
    
    def test_validate_banking_double_entry_balanced(
        self,
        banking_graph_with_balanced_entries: CapabilityGraph,
    ) -> None:
        """
        Test Banking double-entry validation pass khi entries balanced.
        
        Scenario: Ledger entries có tổng debit = tổng credit.
        Expected: Không có errors.
        """
        validator = InvariantValidator(banking_graph_with_balanced_entries)
        report = validator.validate_banking_invariants()
        
        assert report.status == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.FIN_DOUBLE_ENTRY_IMBALANCE.value)) == 0
        assert report.checks.get("FIN_DOUBLE_ENTRY_BALANCE") == ValidationStatus.PASS.value
    
    def test_validate_banking_double_entry_imbalanced(
        self,
        banking_graph_with_imbalanced_entries: CapabilityGraph,
    ) -> None:
        """
        Test Banking double-entry validation fail khi entries imbalanced.
        
        Scenario: Ledger entries có tổng debit != tổng credit.
        Expected: Có error FIN_DOUBLE_ENTRY_IMBALANCE.
        """
        validator = InvariantValidator(banking_graph_with_imbalanced_entries)
        report = validator.validate_banking_invariants()
        
        assert report.status == ValidationStatus.FAIL.value
        imbalanced_errors = report.get_errors_by_code(ErrorCode.FIN_DOUBLE_ENTRY_IMBALANCE.value)
        assert len(imbalanced_errors) > 0
        assert any("unbalanced_transfer" in e.message for e in imbalanced_errors)


# ============================================================================
# Test Banking: KYC Verification
# ============================================================================


class TestBankingKYCVerification:
    """Tests cho Banking domain: KYC required before transfer."""
    
    def test_validate_banking_kyc_verified(
        self,
        banking_graph_with_kyc_verified: CapabilityGraph,
    ) -> None:
        """
        Test Banking KYC validation pass khi KYC đã verify.
        
        Scenario: Transfer instance có kyc_verified = True.
        Expected: Không có errors.
        """
        validator = InvariantValidator(banking_graph_with_kyc_verified)
        report = validator.validate_banking_invariants()
        
        assert report.checks.get("FIN_KYC_VERIFIED") == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.FIN_KYC_NOT_VERIFIED.value)) == 0
    
    def test_validate_banking_kyc_not_verified(
        self,
        banking_graph_without_kyc: CapabilityGraph,
    ) -> None:
        """
        Test Banking KYC validation fail khi KYC không verify.
        
        Scenario: Transfer instance requires_kyc = True nhưng không có kyc_verified.
        Expected: Có error FIN_KYC_NOT_VERIFIED.
        """
        validator = InvariantValidator(banking_graph_without_kyc)
        report = validator.validate_banking_invariants()
        
        kyc_errors = report.get_errors_by_code(ErrorCode.FIN_KYC_NOT_VERIFIED.value)
        assert len(kyc_errors) > 0
        assert any("no_kyc_transfer" in e.message for e in kyc_errors)


# ============================================================================
# Test Healthcare: PHI Encryption
# ============================================================================


class TestHealthcarePHIEncryption:
    """Tests cho Healthcare domain: PHI must be encrypted."""
    
    def test_validate_healthcare_phi_encrypted(
        self,
        healthcare_graph_with_phi_encrypted: CapabilityGraph,
    ) -> None:
        """
        Test Healthcare PHI encryption validation pass khi PHI encrypted.
        
        Scenario: Patient record có encryption_enabled = True.
        Expected: Không có errors.
        """
        validator = InvariantValidator(healthcare_graph_with_phi_encrypted)
        report = validator.validate_healthcare_invariants()
        
        assert report.checks.get("HLT_PHI_ENCRYPTED") == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.HLT_PHI_NOT_ENCRYPTED.value)) == 0
    
    def test_validate_healthcare_phi_not_encrypted(
        self,
        healthcare_graph_with_phi_unencrypted: CapabilityGraph,
    ) -> None:
        """
        Test Healthcare PHI encryption validation fail khi PHI NOT encrypted.
        
        Scenario: Patient record có phi_fields nhưng encryption_enabled = False.
        Expected: Có error HLT_PHI_NOT_ENCRYPTED.
        """
        validator = InvariantValidator(healthcare_graph_with_phi_unencrypted)
        report = validator.validate_healthcare_invariants()
        
        phi_errors = report.get_errors_by_code(ErrorCode.HLT_PHI_NOT_ENCRYPTED.value)
        assert len(phi_errors) > 0
        assert any("store_patient_record_no_enc" in e.message for e in phi_errors)


# ============================================================================
# Test Healthcare: Clinical Audit Trail
# ============================================================================


class TestHealthcareClinicalAuditTrail:
    """Tests cho Healthcare domain: Clinical audit trail required."""
    
    def test_validate_healthcare_audit_trail_present(
        self,
        healthcare_graph_with_audit_trail: CapabilityGraph,
    ) -> None:
        """
        Test Healthcare clinical audit validation pass khi audit trail present.
        
        Scenario: Clinical action có audit_trail_enabled = True.
        Expected: Không có errors.
        """
        validator = InvariantValidator(healthcare_graph_with_audit_trail)
        report = validator.validate_healthcare_invariants()
        
        assert report.checks.get("HLT_CLINICAL_AUDIT") == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.HLT_MISSING_CLINICAL_AUDIT.value)) == 0
    
    def test_validate_healthcare_audit_trail_missing(
        self,
        healthcare_graph_without_audit_trail: CapabilityGraph,
    ) -> None:
        """
        Test Healthcare clinical audit validation fail khi audit trail missing.
        
        Scenario: Clinical action có clinical_action = True nhưng audit_trail_enabled = False.
        Expected: Có error HLT_MISSING_CLINICAL_AUDIT.
        """
        validator = InvariantValidator(healthcare_graph_without_audit_trail)
        report = validator.validate_healthcare_invariants()
        
        audit_errors = report.get_errors_by_code(ErrorCode.HLT_MISSING_CLINICAL_AUDIT.value)
        assert len(audit_errors) > 0
        assert any("clinical_procedure_no_audit" in e.message for e in audit_errors)


# ============================================================================
# Test Exchange: Order Risk Check
# ============================================================================


class TestExchangeOrderRiskCheck:
    """Tests cho Exchange domain: Order must have risk check."""
    
    def test_validate_exchange_risk_check_present(
        self,
        exchange_graph_with_risk_check: CapabilityGraph,
    ) -> None:
        """
        Test Exchange risk check validation pass khi risk check present.
        
        Scenario: Order instance có risk_check_enabled = True.
        Expected: Không có errors.
        """
        validator = InvariantValidator(exchange_graph_with_risk_check)
        report = validator.validate_exchange_invariants()
        
        assert report.checks.get("EXC_ORDER_RISK_CHECK") == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.EXC_ORDER_RISK_CHECK_MISSING.value)) == 0
    
    def test_validate_exchange_risk_check_missing(
        self,
        exchange_graph_without_risk_check: CapabilityGraph,
    ) -> None:
        """
        Test Exchange risk check validation fail khi risk check missing.
        
        Scenario: Order instance có risk_check_enabled = False.
        Expected: Có error EXC_ORDER_RISK_CHECK_MISSING.
        """
        validator = InvariantValidator(exchange_graph_without_risk_check)
        report = validator.validate_exchange_invariants()
        
        risk_errors = report.get_errors_by_code(ErrorCode.EXC_ORDER_RISK_CHECK_MISSING.value)
        assert len(risk_errors) > 0
        assert any("place_order_no_risk" in e.message for e in risk_errors)


# ============================================================================
# Test Exchange: Settlement Atomicity
# ============================================================================


class TestExchangeSettlementAtomicity:
    """Tests cho Exchange domain: Settlement must be atomic."""
    
    def test_validate_exchange_atomic_settlement(
        self,
        exchange_graph_with_atomic_settlement: CapabilityGraph,
    ) -> None:
        """
        Test Exchange settlement atomicity validation pass khi settlement atomic.
        
        Scenario: Settlement instance có atomic_settlement = True và transaction = required.
        Expected: Không có errors.
        """
        validator = InvariantValidator(exchange_graph_with_atomic_settlement)
        report = validator.validate_exchange_invariants()
        
        assert report.checks.get("EXC_SETTLEMENT_ATOMIC") == ValidationStatus.PASS.value
        assert len(report.get_errors_by_code(ErrorCode.EXC_SETTLEMENT_NOT_ATOMIC.value)) == 0
    
    def test_validate_exchange_settlement_not_atomic(
        self,
        exchange_graph_without_atomic_settlement: CapabilityGraph,
    ) -> None:
        """
        Test Exchange settlement atomicity validation fail khi settlement not atomic.
        
        Scenario: Settlement instance có atomic_settlement = False.
        Expected: Có error EXC_SETTLEMENT_NOT_ATOMIC.
        """
        validator = InvariantValidator(exchange_graph_without_atomic_settlement)
        report = validator.validate_exchange_invariants()
        
        atomic_errors = report.get_errors_by_code(ErrorCode.EXC_SETTLEMENT_NOT_ATOMIC.value)
        assert len(atomic_errors) > 0
        assert any("settle_trade_not_atomic" in e.message for e in atomic_errors)


# ============================================================================
# Test Domain Invariant Error Codes
# ============================================================================


class TestDomainInvariantErrorCodes:
    """Tests cho error codes của Domain Invariants."""
    
    def test_domain_error_codes_defined(self) -> None:
        """Test các domain error codes được define trong ErrorCode."""
        assert hasattr(ErrorCode, 'FIN_DOUBLE_ENTRY_IMBALANCE')
        assert hasattr(ErrorCode, 'FIN_KYC_NOT_VERIFIED')
        assert hasattr(ErrorCode, 'HLT_PHI_NOT_ENCRYPTED')
        assert hasattr(ErrorCode, 'HLT_MISSING_CLINICAL_AUDIT')
        assert hasattr(ErrorCode, 'EXC_ORDER_RISK_CHECK_MISSING')
        assert hasattr(ErrorCode, 'EXC_SETTLEMENT_NOT_ATOMIC')
    
    def test_domain_error_code_values(self) -> None:
        """Test values của các domain error codes."""
        assert ErrorCode.FIN_DOUBLE_ENTRY_IMBALANCE.value == "FIN_DOUBLE_ENTRY_IMBALANCE"
        assert ErrorCode.FIN_KYC_NOT_VERIFIED.value == "FIN_KYC_NOT_VERIFIED"
        assert ErrorCode.HLT_PHI_NOT_ENCRYPTED.value == "HLT_PHI_NOT_ENCRYPTED"
        assert ErrorCode.HLT_MISSING_CLINICAL_AUDIT.value == "HLT_MISSING_CLINICAL_AUDIT"
        assert ErrorCode.EXC_ORDER_RISK_CHECK_MISSING.value == "EXC_ORDER_RISK_CHECK_MISSING"
        assert ErrorCode.EXC_SETTLEMENT_NOT_ATOMIC.value == "EXC_SETTLEMENT_NOT_ATOMIC"