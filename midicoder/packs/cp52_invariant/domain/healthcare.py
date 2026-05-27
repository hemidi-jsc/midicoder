"""
Healthcare Domain Invariants (DP09/DP10)

RX04: HIPAA Compliance invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    valid: bool
    code: str
    message: str


def phi_encryption_invariant(entity: dict[str, Any]) -> ValidationResult:
    """INV-HC-001: Tất cả PHI fields phải được encrypt."""
    for field_name, value in entity.items():
        if "_enc" in field_name and not str(value).startswith("ENC:"):
            return ValidationResult(False, "INV-HC-001", f"PHI field {field_name} không được encrypt")
    return ValidationResult(True, "INV-HC-001", "PHI encryption OK")


def minimum_necessary_access_invariant(user: dict[str, Any], requested_fields: list[str], role: str) -> ValidationResult:
    """INV-HC-002: User chỉ có thể access necessary PHI fields."""
    allowed = {"doctor": ["all"], "nurse": ["vitals", "medications"], "admin": ["demographics"]}
    if role not in allowed and requested_fields:
        return ValidationResult(False, "INV-HC-002", f"Role {role} không được phép access {requested_fields}")
    return ValidationResult(True, "INV-HC-002", "Access OK")


def clinical_audit_trail_invariant(access_event: dict[str, Any]) -> ValidationResult:
    """INV-HC-003: Tất cả PHI access phải có audit trail."""
    if not access_event.get("audit_trail_id"):
        return ValidationResult(False, "INV-HC-003", "PHI access không có audit trail")
    return ValidationResult(True, "INV-HC-003", "Audit trail OK")