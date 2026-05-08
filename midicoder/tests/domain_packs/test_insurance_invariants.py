"""
Tests cho Insurance Domain Invariants (DP14)

Kiểm tra các invariants:
- INV-INS-001: Underwriting before policy
- INV-INS-002: Claim within coverage period
- INV-INS-003: Claim amount within limit
"""

import pytest
from datetime import date
from decimal import Decimal

from midicoder.emitters.core.invariant.domain.insurance import (
    ValidationResult,
    underwriting_before_policy_invariant,
    claim_within_coverage_period_invariant,
    claim_amount_within_limit_invariant,
)


class TestUnderwritingBeforePolicyInvariant:
    """Tests cho INV-INS-001: Underwriting before policy."""

    def test_active_with_underwriting_pass(self):
        """Policy active, đã qua underwriting."""
        policy = {"status": "active", "underwriting_passed": True}
        result = underwriting_before_policy_invariant(policy)
        assert result.valid is True
        assert result.code == "INV-INS-001"

    def test_active_without_underwriting_fail(self):
        """Policy active, chưa qua underwriting."""
        policy = {"status": "active", "underwriting_passed": False}
        result = underwriting_before_policy_invariant(policy)
        assert result.valid is False
        assert result.code == "INV-INS-001"

    def test_draft_policy_pass(self):
        """Draft policy: không cần underwriting."""
        policy = {"status": "draft", "underwriting_passed": False}
        result = underwriting_before_policy_invariant(policy)
        assert result.valid is True


class TestClaimWithinCoveragePeriodInvariant:
    """Tests cho INV-INS-002: Claim within coverage period."""

    def test_claim_in_period_pass(self):
        """Claim trong coverage period."""
        claim = {"incident_date": date(2024, 6, 1)}
        policy = {"start_date": date(2024, 1, 1), "end_date": date(2024, 12, 31)}
        result = claim_within_coverage_period_invariant(claim, policy)
        assert result.valid is True
        assert result.code == "INV-INS-002"

    def test_claim_before_period_fail(self):
        """Claim trước coverage period."""
        claim = {"incident_date": date(2023, 12, 31)}
        policy = {"start_date": date(2024, 1, 1), "end_date": date(2024, 12, 31)}
        result = claim_within_coverage_period_invariant(claim, policy)
        assert result.valid is False
        assert result.code == "INV-INS-002"

    def test_claim_after_period_fail(self):
        """Claim sau coverage period."""
        claim = {"incident_date": date(2025, 1, 1)}
        policy = {"start_date": date(2024, 1, 1), "end_date": date(2024, 12, 31)}
        result = claim_within_coverage_period_invariant(claim, policy)
        assert result.valid is False


class TestClaimAmountWithinLimitInvariant:
    """Tests cho INV-INS-003: Claim amount within limit."""

    def test_claim_within_limit_pass(self):
        """Claim amount không vượt limit."""
        claim = {"claimed_amount": "50000000"}
        policy = {"coverage_amount": "100000000"}
        result = claim_amount_within_limit_invariant(claim, policy)
        assert result.valid is True
        assert result.code == "INV-INS-003"

    def test_claim_exceeds_limit_fail(self):
        """Claim amount vượt limit."""
        claim = {"claimed_amount": "150000000"}
        policy = {"coverage_amount": "100000000"}
        result = claim_amount_within_limit_invariant(claim, policy)
        assert result.valid is False
        assert result.code == "INV-INS-003"

    def test_claim_equal_limit_pass(self):
        """Claim amount bằng limit."""
        claim = {"claimed_amount": "100000000"}
        policy = {"coverage_amount": "100000000"}
        result = claim_amount_within_limit_invariant(claim, policy)
        assert result.valid is True