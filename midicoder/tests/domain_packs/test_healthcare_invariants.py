"""
Tests cho Healthcare Domain Invariants (DP09/DP10)

Kiểm tra các invariants:
- INV-HC-001: PHI encryption
- INV-HC-002: Minimum necessary access
- INV-HC-003: Clinical audit trail
"""

import pytest

from midicoder.emitters.core.invariant.domain.healthcare import (
    ValidationResult,
    phi_encryption_invariant,
    minimum_necessary_access_invariant,
    clinical_audit_trail_invariant,
)


class TestPhiEncryptionInvariant:
    """Tests cho INV-HC-001: PHI encryption."""

    def test_encrypted_fields_pass(self):
        """PHI fields đã encrypt."""
        entity = {"name_enc": "ENC:John Doe", "phone_enc": "ENC:123456"}
        result = phi_encryption_invariant(entity)
        assert result.valid is True
        assert result.code == "INV-HC-001"

    def test_unencrypted_phi_fail(self):
        """PHI fields không encrypt."""
        entity = {"name_enc": "John Doe"}
        result = phi_encryption_invariant(entity)
        assert result.valid is False
        assert result.code == "INV-HC-001"

    def test_non_phi_fields_pass(self):
        """Non-PHI fields: không cần encrypt."""
        entity = {"gender": "M", "blood_type": "O+"}
        result = phi_encryption_invariant(entity)
        assert result.valid is True


class TestMinimumNecessaryAccessInvariant:
    """Tests cho INV-HC-002: Minimum necessary access."""

    def test_doctor_access_all_pass(self):
        """Bác sĩ có thể access tất cả."""
        result = minimum_necessary_access_invariant({}, ["all"], "doctor")
        assert result.valid is True

    def test_nurse_limited_access_pass(self):
        """Y tá chỉ access vitals, medications."""
        result = minimum_necessary_access_invariant({}, ["vitals"], "nurse")
        assert result.valid is True

    def test_unauthorized_role_fail(self):
        """Role không được phép access."""
        result = minimum_necessary_access_invariant({}, ["records"], "receptionist")
        assert result.valid is False
        assert result.code == "INV-HC-002"


class TestClinicalAuditTrailInvariant:
    """Tests cho INV-HC-003: Clinical audit trail."""

    def test_with_audit_trail_pass(self):
        """Có audit trail."""
        event = {"audit_trail_id": "AUDIT-001"}
        result = clinical_audit_trail_invariant(event)
        assert result.valid is True
        assert result.code == "INV-HC-003"

    def test_without_audit_trail_fail(self):
        """Không có audit trail."""
        event = {"audit_trail_id": None}
        result = clinical_audit_trail_invariant(event)
        assert result.valid is False
        assert result.code == "INV-HC-003"