"""
Insurance Domain Invariants (DP14)

Underwriting, coverage period, claim limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class ValidationResult:
    valid: bool
    code: str
    message: str


def underwriting_before_policy_invariant(policy: dict[str, Any]) -> ValidationResult:
    """INV-INS-001: Underwriting phải complete trước khi issue policy."""
    if policy.get("status") == "active" and not policy.get("underwriting_passed"):
        return ValidationResult(False, "INV-INS-001", "Policy active nhưng chưa qua underwriting")
    return ValidationResult(True, "INV-INS-001", "Underwriting OK")


def claim_within_coverage_period_invariant(claim: dict[str, Any], policy: dict[str, Any]) -> ValidationResult:
    """INV-INS-002: Claim phải trong coverage period."""
    incident = claim.get("incident_date")
    if isinstance(incident, str):
        incident = date.fromisoformat(incident)
    if incident < policy.get("start_date") or incident > policy.get("end_date"):
        return ValidationResult(False, "INV-INS-002", "Claim ngoài coverage period")
    return ValidationResult(True, "INV-INS-002", "Coverage period OK")


def claim_amount_within_limit_invariant(claim: dict[str, Any], policy: dict[str, Any]) -> ValidationResult:
    """INV-INS-003: Claim amount không vượt policy limit."""
    claimed = Decimal(str(claim.get("claimed_amount", 0)))
    coverage = Decimal(str(policy.get("coverage_amount", 0)))
    if claimed > coverage:
        return ValidationResult(False, "INV-INS-003", f"Claim {claimed} > coverage {coverage}")
    return ValidationResult(True, "INV-INS-003", "Claim within limit")