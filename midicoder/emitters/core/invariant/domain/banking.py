"""
Banking Domain Invariants

Các invariants cho compile-time validation Banking (DP11).
RX02: Financial Integrity. RX03: KYC/AML.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, List


@dataclass
class ValidationResult:
    """Kết quả validation."""
    valid: bool
    code: str
    message: str
    details: dict[str, Any] | None = None


def double_entry_balance_invariant(journal_entries: list[dict[str, Any]]) -> ValidationResult:
    """
    INV-BANK-001: Tổng debit phải bằng tổng credit.

    Args:
        journal_entries: List ledger entries của một journal

    Returns:
        ValidationResult với valid=True nếu debit == credit
    """
    debit_total = sum(e.get("amount", Decimal("0")) for e in journal_entries if e.get("type") == "debit")
    credit_total = sum(e.get("amount", Decimal("0")) for e in journal_entries if e.get("type") == "credit")
    if debit_total != credit_total:
        return ValidationResult(False, "INV-BANK-001", f"Double-entry imbalance: debit={debit_total} != credit={credit_total}", {"debit": str(debit_total), "credit": str(credit_total)})
    return ValidationResult(True, "INV-BANK-001", "Double-entry balanced")


def transaction_immutability_invariant(transaction: dict[str, Any]) -> ValidationResult:
    """
    INV-BANK-002: Transaction không thể sửa sau khi commit.

    Args:
        transaction: Transaction data với status và committed_at

    Returns:
        ValidationResult với valid=True nếu transaction chưa committed hoặc không bị sửa
    """
    if transaction.get("status") == "committed" and transaction.get("committed_at"):
        if transaction.get("modified_after_commit"):
            return ValidationResult(False, "INV-BANK-002", "Transaction đã committed không thể sửa")
    return ValidationResult(True, "INV-BANK-002", "Transaction immutability OK")


def reconciliation_mandatory_invariant(account_id: str, reconciliation_date: date, last_reconciliation: date | None) -> ValidationResult:
    """
    INV-BANK-003: Daily reconciliation phải được thực hiện.

    Args:
        account_id: ID tài khoản
        reconciliation_date: Ngày cần đối chiếu
        last_reconciliation: Lần đối chiếu cuối cùng

    Returns:
        ValidationResult với valid=True nếu đã đối chiếu
    """
    if last_reconciliation is None or last_reconciliation < reconciliation_date:
        return ValidationResult(False, "INV-BANK-003", f"Reconciliation chưa thực hiện cho {account_id} ngày {reconciliation_date}")
    return ValidationResult(True, "INV-BANK-003", "Reconciliation mandatory check passed")


def kyc_before_transaction_invariant(account: dict[str, Any]) -> ValidationResult:
    """
    INV-BANK-004: KYC verification phải pass trước khi giao dịch.

    Args:
        account: Account data với kyc_verified flag

    Returns:
        ValidationResult với valid=True nếu KYC đã verify
    """
    if account.get("kyc_verified") not in ("1", True, "true"):
        return ValidationResult(False, "INV-BANK-004", f"KYC chưa verify cho account {account.get('id')}")
    return ValidationResult(True, "INV-BANK-004", "KYC verified")


def aml_screening_invariant(transaction: dict[str, Any], threshold: Decimal = Decimal("100000000")) -> ValidationResult:
    """
    INV-BANK-005: AML screening cho transactions > threshold (mặc định 100 triệu).

    Args:
        transaction: Transaction data với amount và aml_screening_passed
        threshold: Ngưỡng AML screening (mặc định 100 triệu VND)

    Returns:
        ValidationResult với valid=True nếu AML screening pass
    """
    amount = Decimal(str(transaction.get("amount", 0)))
    if amount > threshold and transaction.get("aml_screening_passed") not in ("1", True, "true"):
        return ValidationResult(False, "INV-BANK-005", f"AML screening chưa pass cho transaction {amount} > {threshold}")
    return ValidationResult(True, "INV-BANK-005", "AML screening OK")