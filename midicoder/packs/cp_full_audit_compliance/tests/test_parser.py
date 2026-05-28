# coding: utf-8
"""
Test cases cho CP14 Audit Trail & Compliance Parser.

Kiểm tra:
- AuditComplianceParser: Parse YAML DSL hợp lệ
- Error handling: Invalid YAML, invalid actions, invalid levels
- Edge cases: Empty input, empty sections
"""

import pytest

from midicoder.packs.cp_full_audit_compliance.parser import AuditComplianceParser
from midicoder.packs.cp_full_audit_compliance.models import (
    AuditActionType,
    AuditComplianceCollection,
    AuditLevel,
    StandardType,
    ControlType,
    EnforcementLevel,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestAuditComplianceParser:
    """Test AuditComplianceParser."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = AuditComplianceParser()

    def test_parse_empty_string_returns_empty_collection(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, AuditComplianceCollection)
        assert len(result.audit_rules) == 0
        assert len(result.compliance_controls) == 0

    def test_parse_whitespace_only_returns_empty_collection(self):
        """Kiểm tra parse whitespace trả về collection rỗng."""
        result = self.parser.parse("   \n\n  ")
        assert isinstance(result, AuditComplianceCollection)
        assert len(result.audit_rules) == 0
        assert len(result.compliance_controls) == 0

    def test_parse_valid_audit_rules(self):
        """Kiểm tra parse audit rules hợp lệ."""
        dsl = """
audit_rules:
  - id: ledger_audit
    name: Audit Ledger Entries
    entity_types: [LedgerEntry]
    actions: [CREATE, UPDATE]
    audit_level: detailed
    retention_days: 2555
    archive_after_days: 365
    compliance_tags: [sox, hipaa]
"""
        result = self.parser.parse(dsl)
        assert len(result.audit_rules) == 1

        rule = result.audit_rules[0]
        assert rule.id == "ledger_audit"
        assert rule.name == "Audit Ledger Entries"
        assert rule.entity_types == ["LedgerEntry"]
        assert rule.actions == [AuditActionType.CREATE, AuditActionType.UPDATE]
        assert rule.audit_level == AuditLevel.DETAILED
        assert rule.retention_days == 2555
        assert rule.archive_after_days == 365
        assert rule.compliance_tags == ["sox", "hipaa"]

    def test_parse_valid_compliance_controls(self):
        """Kiểm tra parse compliance controls hợp lệ."""
        dsl = """
compliance_controls:
  - id: sox_immutable
    name: SOX Immutable Ledger
    standard: sox
    control_type: preventive
    enforcement_level: both
    audit_rule_id: ledger_audit
"""
        result = self.parser.parse(dsl)
        assert len(result.compliance_controls) == 1

        control = result.compliance_controls[0]
        assert control.id == "sox_immutable"
        assert control.name == "SOX Immutable Ledger"
        assert control.standard == StandardType.SOX
        assert control.control_type == ControlType.PREVENTIVE
        assert control.enforcement_level == EnforcementLevel.BOTH
        assert control.audit_rule_id == "ledger_audit"

    def test_parse_full_dsl_with_rules_and_controls(self):
        """Kiểm tra parse DSL đầy đủ với rules và controls."""
        dsl = """
audit_rules:
  - id: ledger_audit
    name: Audit Ledger Entries
    entity_types: [LedgerEntry]
    actions: [CREATE, UPDATE]
    audit_level: detailed
    retention_days: 2555
    archive_after_days: 365
    compliance_tags: [sox, hipaa]
  - id: order_audit
    name: Audit Orders
    entity_types: [Order]
    actions: [CREATE, UPDATE, DELETE]
    audit_level: basic
compliance_controls:
  - id: sox_immutable
    name: SOX Immutable Ledger
    standard: sox
    control_type: preventive
    enforcement_level: both
    audit_rule_id: ledger_audit
  - id: hipaa_access
    name: HIPAA Access Control
    standard: hipaa
    control_type: detective
    enforcement_level: runtime
"""
        result = self.parser.parse(dsl)
        assert len(result.audit_rules) == 2
        assert len(result.compliance_controls) == 2
        assert result.audit_rules[0].id == "ledger_audit"
        assert result.audit_rules[1].id == "order_audit"
        assert result.compliance_controls[0].standard == StandardType.SOX
        assert result.compliance_controls[1].standard == StandardType.HIPAA

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw error."""
        invalid_yaml = """
audit_rules:
  - id: test
    name: [invalid yaml
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.MDC-BE01_DSL_PARSE_ERROR

    def test_parse_non_dict_yaml_raises_error(self):
        """Kiểm tra parse YAML list (không phải mapping) throw error."""
        list_yaml = """
- item1
- item2
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(list_yaml)
        assert exc_info.value.code == ErrorCode.MDC-BE01_DSL_PARSE_ERROR

    def test_parse_invalid_action_type_raises_error(self):
        """Kiểm tra action type không hợp lệ throw error."""
        dsl = """
audit_rules:
  - id: test
    name: Test Rule
    actions: [INVALID_ACTION]
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F12_AUDIT_INVALID_ACTION

    def test_parse_invalid_audit_level_raises_error(self):
        """Kiểm tra audit level không hợp lệ throw error."""
        dsl = """
audit_rules:
  - id: test
    name: Test Rule
    audit_level: invalid_level
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F12_AUDIT_INVALID_LEVEL

    def test_parse_invalid_standard_raises_error(self):
        """Kiểm tra standard không hợp lệ throw error."""
        dsl = """
compliance_controls:
  - id: test
    name: Test Control
    standard: invalid_standard
    control_type: preventive
    enforcement_level: runtime
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F12_AUDIT_CONTROL_INVALID_STANDARD

    def test_parse_invalid_control_type_raises_error(self):
        """Kiểm tra control_type không hợp lệ throw error."""
        dsl = """
compliance_controls:
  - id: test
    name: Test Control
    standard: sox
    control_type: invalid_type
    enforcement_level: runtime
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F12_AUDIT_CONTROL_INVALID_TYPE

    def test_parse_invalid_enforcement_level_raises_error(self):
        """Kiểm tra enforcement_level không hợp lệ throw error."""
        dsl = """
compliance_controls:
  - id: test
    name: Test Control
    standard: sox
    control_type: preventive
    enforcement_level: invalid_level
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(dsl)
        assert exc_info.value.code == ErrorCode.MDC-F12_AUDIT_CONTROL_INVALID_ENFORCEMENT

    def test_parse_all_action_types(self):
        """Kiểm tra parse tất cả action types."""
        dsl = """
audit_rules:
  - id: full_audit
    name: Full Audit
    actions: [CREATE, UPDATE, DELETE, READ, LOGIN, LOGOUT, EXPORT, APPROVE, REJECT, CUSTOM]
"""
        result = self.parser.parse(dsl)
        rule = result.audit_rules[0]
        assert len(rule.actions) == 10
        assert AuditActionType.CREATE in rule.actions
        assert AuditActionType.CUSTOM in rule.actions

    def test_parse_all_standards(self):
        """Kiểm tra parse tất cả standards."""
        dsl = """
compliance_controls:
  - id: c1
    name: SOX
    standard: sox
    control_type: preventive
    enforcement_level: runtime
  - id: c2
    name: HIPAA
    standard: hipaa
    control_type: preventive
    enforcement_level: runtime
  - id: c3
    name: GDPR
    standard: gdpr
    control_type: preventive
    enforcement_level: runtime
  - id: c4
    name: PCI_DSS
    standard: pci_dss
    control_type: preventive
    enforcement_level: runtime
  - id: c5
    name: Custom
    standard: custom
    control_type: preventive
    enforcement_level: runtime
"""
        result = self.parser.parse(dsl)
        assert len(result.compliance_controls) == 5
        standards = [c.standard for c in result.compliance_controls]
        assert StandardType.SOX in standards
        assert StandardType.HIPAA in standards
        assert StandardType.GDPR in standards
        assert StandardType.PCI_DSS in standards
        assert StandardType.CUSTOM in standards

    def test_parse_with_optional_fields(self):
        """Kiểm tra parse với optional fields."""
        dsl = """
audit_rules:
  - id: minimal_rule
    name: Minimal Rule
"""
        result = self.parser.parse(dsl)
        rule = result.audit_rules[0]
        assert rule.entity_types == []
        assert rule.actions == []
        assert rule.enabled is True
        assert rule.audit_level == AuditLevel.BASIC
        assert rule.retention_days == 365
        assert rule.archive_after_days == 90

    def test_parse_disabled_rule(self):
        """Kiểm tra parse disabled rule."""
        dsl = """
audit_rules:
  - id: disabled_rule
    name: Disabled Rule
    enabled: false
"""
        result = self.parser.parse(dsl)
        assert result.audit_rules[0].enabled is False

    def test_parse_duplicate_rule_ids_raises_error(self):
        """Kiểm tra parse rule ID trùng throw error."""
        dsl = """
audit_rules:
  - id: dup
    name: First
  - id: dup
    name: Second
"""
        with pytest.raises(MidicoderError):
            self.parser.parse(dsl)

    def test_parse_duplicate_control_ids_raises_error(self):
        """Kiểm tra parse control ID trùng throw error."""
        dsl = """
compliance_controls:
  - id: dup
    name: First
    standard: custom
    control_type: preventive
    enforcement_level: runtime
  - id: dup
    name: Second
    standard: custom
    control_type: preventive
    enforcement_level: runtime
"""
        with pytest.raises(MidicoderError):
            self.parser.parse(dsl)

    def test_parse_empty_audit_rules_section(self):
        """Kiểm tra parse section audit_rules rỗng."""
        dsl = """
audit_rules: []
"""
        result = self.parser.parse(dsl)
        assert len(result.audit_rules) == 0

    def test_parse_empty_compliance_controls_section(self):
        """Kiểm tra parse section compliance_controls rỗng."""
        dsl = """
compliance_controls: []
"""
        result = self.parser.parse(dsl)
        assert len(result.compliance_controls) == 0

    def test_parse_no_sections(self):
        """Kiểm tra parse không có sections."""
        dsl = """
# Chỉ có comment
"""
        result = self.parser.parse(dsl)
        assert len(result.audit_rules) == 0
        assert len(result.compliance_controls) == 0