"""
Unit Tests cho AuditEnforcementValidator.

Task: E11-005 - Add AuditEnforcementValidator
Priority: P1 - Required by Banking, Healthcare, ERP

Kiểm tra:
- Audit enforcement cho compliance-critical entities
- Validation cho audit_config (enabled, level, retention_days)
- SOX compliance (7-year retention)
- HIPAA compliance requirements

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.capability_validator import (
    validate_capability_params,
    AuditEnforcementValidator,
)


class TestAuditEnforcementValidator:
    """Tests cho AuditEnforcementValidator."""

    def test_validator_exists(self):
        """Kiểm tra AuditEnforcementValidator tồn tại."""
        validator = AuditEnforcementValidator()
        assert validator is not None

    def test_compliance_entity_requires_audit(self):
        """Kiểm tra compliance entity yêu cầu audit enabled."""
        validator = AuditEnforcementValidator()

        # Financial entity without audit
        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000},
            "audit_config": {"enabled": False}
        }

        result = validator.validate(params)
        assert result.is_valid is False
        assert "audit" in result.error_messages[0].lower()

    def test_compliance_entity_requires_detailed_audit(self):
        """Kiểm tra compliance entity yêu cầu detailed audit level."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000},
            "audit_config": {
                "enabled": True,
                "level": "minimal"  # Should be "detailed"
            }
        }

        result = validator.validate(params)
        assert result.is_valid is False
        assert "detailed" in result.error_messages[0].lower()

    def test_compliance_entity_with_valid_audit(self):
        """Kiểm tra compliance entity với valid audit config."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000},
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 2555  # 7 years for SOX
            }
        }

        result = validator.validate(params)
        assert result.is_valid is True

    def test_healthcare_entity_requires_audit(self):
        """Kiểm tra healthcare entity yêu cầu audit (HIPAA)."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "PatientRecord",
            "data": {"diagnosis": "flu"},
            "audit_config": {"enabled": False}
        }

        result = validator.validate(params)
        assert result.is_valid is False


class TestAuditRetentionPeriod:
    """Tests cho audit retention period."""

    def test_sox_compliance_retention(self):
        """Kiểm tra SOX compliance - 7 year retention."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "FinancialTransaction",
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 2555  # 7 years
            }
        }

        result = validator.validate(params)
        assert result.is_valid is True

    def test_insufficient_retention_for_financial(self):
        """Kiểm tra insufficient retention cho financial entities."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "LedgerEntry",
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 365  # Only 1 year - insufficient
            }
        }

        result = validator.validate(params)
        # Should fail retention check for financial entities
        assert result.is_valid is False or "retention" in str(result.error_messages).lower()


class TestComplianceEntityDetection:
    """Tests cho compliance entity detection."""

    def test_is_compliance_entity_financial(self):
        """Kiểm tra detection của financial compliance entities."""
        validator = AuditEnforcementValidator()

        assert validator._is_compliance_entity("LedgerEntry") is True
        assert validator._is_compliance_entity("FinancialTransaction") is True
        assert validator._is_compliance_entity("Payment") is True

    def test_is_compliance_entity_healthcare(self):
        """Kiểm tra detection của healthcare compliance entities."""
        validator = AuditEnforcementValidator()

        assert validator._is_compliance_entity("PatientRecord") is True
        assert validator._is_compliance_entity("MedicalPrescription") is True
        assert validator._is_compliance_entity("LabResult") is True

    def test_is_compliance_entity_erp(self):
        """Kiểm tra detection của ERP compliance entities."""
        validator = AuditEnforcementValidator()

        assert validator._is_compliance_entity("InventoryAdjustment") is True
        assert validator._is_compliance_entity("PurchaseOrder") is True


class TestAuditEnforcementIntegration:
    """Tests cho audit enforcement integration."""

    def test_create_record_with_audit_validation(self):
        """Kiểm tra create_record với audit validation."""
        # Compliance entity with proper audit
        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000, "debit": True},
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "include_before": False,
                "include_after": True,
                "retention_days": 2555
            }
        }

        validator = AuditEnforcementValidator()
        result = validator.validate(params)
        assert result.is_valid is True

    def test_update_record_with_audit_diff(self):
        """Kiểm tra update_record với audit diff config."""
        params = {
            "entity": "PatientRecord",
            "id": "patient_123",
            "data": {"diagnosis": "updated"},
            "audit_diff_config": {
                "enabled": True,
                "level": "detailed",  # Required for compliance
                "track_changes": True,
                "include_diff": True,
                "sensitive_fields": ["ssn", "medical_record_number"],
                "retention_days": 2555  # 7 years > 6 years (HIPAA)
            }
        }

        validator = AuditEnforcementValidator()
        result = validator.validate(params)
        assert result.is_valid is True

    def test_delete_record_audit_required(self):
        """Kiểm tra delete_record yêu cầu audit."""
        # delete_record always requires audit_log obligation
        # This is enforced via capability obligations, not validator
        # Validator checks that audit is configured if delete is used
        params = {
            "entity": "FinancialTransaction",
            "id": "txn_123",
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 2555  # 7 years for SOX
            }
        }

        validator = AuditEnforcementValidator()
        result = validator.validate(params)
        assert result.is_valid is True


class TestAuditEnforcementEdgeCases:
    """Tests cho edge cases của audit enforcement."""

    def test_non_compliance_entity_no_audit_required(self):
        """Kiểm tra non-compliance entity không yêu cầu audit."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "UserPreference",
            "data": {"theme": "dark"},
            "audit_config": {"enabled": False}
        }

        result = validator.validate(params)
        # Non-compliance entities don't require audit
        assert result.is_valid is True

    def test_empty_audit_config(self):
        """Kiểm tra empty audit config."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000}
            # No audit_config
        }

        result = validator.validate(params)
        # Missing audit_config should fail for compliance entities
        assert result.is_valid is False

    def test_audit_config_not_dict(self):
        """Kiểm tra audit_config không phải dict."""
        validator = AuditEnforcementValidator()

        params = {
            "entity": "LedgerEntry",
            "data": {"amount": 1000},
            "audit_config": "enabled"  # Should be dict
        }

        result = validator.validate(params)
        assert result.is_valid is False


class TestAuditComplianceStandards:
    """Tests cho compliance standards."""

    def test_sox_financial_compliance(self):
        """Kiểm tra SOX financial compliance requirements."""
        validator = AuditEnforcementValidator()

        # SOX requires: detailed audit, 7-year retention
        params = {
            "entity": "JournalEntry",
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 2555,  # 7 years
                "immutable": True
            }
        }

        result = validator.validate(params)
        assert result.is_valid is True

    def test_hipaa_healthcare_compliance(self):
        """Kiểm tra HIPAA healthcare compliance requirements."""
        validator = AuditEnforcementValidator()

        # HIPAA requires: access logging, 6-year retention minimum
        params = {
            "entity": "PHIRecord",
            "audit_config": {
                "enabled": True,
                "level": "detailed",
                "retention_days": 2190,  # 6 years
                "access_logging": True
            }
        }

        result = validator.validate(params)
        assert result.is_valid is True