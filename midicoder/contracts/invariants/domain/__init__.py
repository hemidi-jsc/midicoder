"""
Domain-specific invariants.

Các invariants cho từng domain:
- banking: RX02 (Financial Integrity), RX03 (KYC/AML)
- healthcare: RX04 (HIPAA)
- insurance: Underwriting, Coverage, Claim Limits
"""

from midicoder.contracts.invariants.domain.banking import (
    double_entry_balance_invariant,
    transaction_immutability_invariant,
    reconciliation_mandatory_invariant,
    kyc_before_transaction_invariant,
    aml_screening_invariant,
)

from midicoder.contracts.invariants.domain.healthcare import (
    phi_encryption_invariant,
    minimum_necessary_access_invariant,
    clinical_audit_trail_invariant,
)

from midicoder.contracts.invariants.domain.insurance import (
    underwriting_before_policy_invariant,
    claim_within_coverage_period_invariant,
    claim_amount_within_limit_invariant,
)

__all__ = [
    # Banking
    "double_entry_balance_invariant",
    "transaction_immutability_invariant",
    "reconciliation_mandatory_invariant",
    "kyc_before_transaction_invariant",
    "aml_screening_invariant",
    # Healthcare
    "phi_encryption_invariant",
    "minimum_necessary_access_invariant",
    "clinical_audit_trail_invariant",
    # Insurance
    "underwriting_before_policy_invariant",
    "claim_within_coverage_period_invariant",
    "claim_amount_within_limit_invariant",
]