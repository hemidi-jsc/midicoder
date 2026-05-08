"""
Tests cho Banking Domain Invariants (DP11)

Kiểm tra các invariants:
- INV-BANK-001: Double-entry balance
- INV-BANK-002: Transaction immutability
- INV-BANK-003: Reconciliation mandatory
- INV-BANK-004: KYC before transaction
- INV-BANK-005: AML screening
"""

import pytest
from datetime import date
from decimal import Decimal

from midicoder.emitters.core.invariant.domain.banking import (
    ValidationResult,
    double_entry_balance_invariant,
    transaction_immutability_invariant,
    reconciliation_mandatory_invariant,
    kyc_before_transaction_invariant,
    aml_screening_invariant,
)


class TestDoubleEntryBalanceInvariant:
    """Tests cho INV-BANK-001: Double-entry balance."""

    def test_balanced_entries_pass(self):
        """Balanced entries: debit == credit."""
        entries = [
            {"type": "debit", "amount": Decimal("1000.00")},
            {"type": "credit", "amount": Decimal("1000.00")},
        ]
        result = double_entry_balance_invariant(entries)
        assert result.valid is True
        assert result.code == "INV-BANK-001"

    def test_unbalanced_entries_fail(self):
        """Unbalanced entries: debit != credit."""
        entries = [
            {"type": "debit", "amount": Decimal("1000.00")},
            {"type": "credit", "amount": Decimal("500.00")},
        ]
        result = double_entry_balance_invariant(entries)
        assert result.valid is False
        assert result.code == "INV-BANK-001"

    def test_empty_entries_pass(self):
        """Empty entries: debit == credit == 0."""
        result = double_entry_balance_invariant([])
        assert result.valid is True


class TestTransactionImmutabilityInvariant:
    """Tests cho INV-BANK-002: Transaction immutability."""

    def test_committed_not_modified_pass(self):
        """Committed transaction không bị sửa."""
        txn = {"status": "committed", "committed_at": "2024-01-01", "modified_after_commit": False}
        result = transaction_immutability_invariant(txn)
        assert result.valid is True

    def test_committed_modified_fail(self):
        """Committed transaction bị sửa."""
        txn = {"status": "committed", "committed_at": "2024-01-01", "modified_after_commit": True}
        result = transaction_immutability_invariant(txn)
        assert result.valid is False
        assert result.code == "INV-BANK-002"

    def test_pending_transaction_pass(self):
        """Pending transaction: không cần immutable."""
        txn = {"status": "pending", "modified_after_commit": True}
        result = transaction_immutability_invariant(txn)
        assert result.valid is True


class TestReconciliationMandatoryInvariant:
    """Tests cho INV-BANK-003: Reconciliation mandatory."""

    def test_reconciled_pass(self):
        """Đã đối chiếu."""
        result = reconciliation_mandatory_invariant("ACC001", date(2024, 1, 1), date(2024, 1, 1))
        assert result.valid is True

    def test_not_reconciled_fail(self):
        """Chưa đối chiếu."""
        result = reconciliation_mandatory_invariant("ACC001", date(2024, 1, 2), date(2024, 1, 1))
        assert result.valid is False
        assert result.code == "INV-BANK-003"

    def test_no_reconciliation_fail(self):
        """Không có reconciliation."""
        result = reconciliation_mandatory_invariant("ACC001", date(2024, 1, 1), None)
        assert result.valid is False


class TestKycBeforeTransactionInvariant:
    """Tests cho INV-BANK-004: KYC before transaction."""

    def test_kyc_verified_pass(self):
        """KYC đã verify."""
        account = {"id": "ACC001", "kyc_verified": "1"}
        result = kyc_before_transaction_invariant(account)
        assert result.valid is True

    def test_kyc_not_verified_fail(self):
        """KYC chưa verify."""
        account = {"id": "ACC001", "kyc_verified": "0"}
        result = kyc_before_transaction_invariant(account)
        assert result.valid is False
        assert result.code == "INV-BANK-004"


class TestAmlScreeningInvariant:
    """Tests cho INV-BANK-005: AML screening."""

    def test_below_threshold_pass(self):
        """Dưới threshold: không cần AML."""
        txn = {"amount": "50000000", "aml_screening_passed": "0"}
        result = aml_screening_invariant(txn)
        assert result.valid is True

    def test_above_threshold_passed_pass(self):
        """Trên threshold, AML pass."""
        txn = {"amount": "200000000", "aml_screening_passed": "1"}
        result = aml_screening_invariant(txn)
        assert result.valid is True

    def test_above_threshold_failed_fail(self):
        """Trên threshold, AML fail."""
        txn = {"amount": "200000000", "aml_screening_passed": "0"}
        result = aml_screening_invariant(txn)
        assert result.valid is False
        assert result.code == "INV-BANK-005"