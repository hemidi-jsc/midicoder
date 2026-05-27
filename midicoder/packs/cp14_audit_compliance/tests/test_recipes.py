# coding: utf-8
"""
Tests for CP14 recipes module.

Covers:
- basic_audit_recipe
- immutable_ledger_recipe
- gdpr_compliance_recipe
- hipaa_compliance_recipe
- sox_compliance_recipe
- pci_dss_compliance_recipe
- generate_compliance_report_config
"""

import pytest

from midicoder.packs.cp14_audit_compliance.recipes import (
    basic_audit_recipe,
    gdpr_compliance_recipe,
    generate_compliance_report_config,
    hipaa_compliance_recipe,
    immutable_ledger_recipe,
    pci_dss_compliance_recipe,
    sox_compliance_recipe,
)
from midicoder.packs.cp14_audit_compliance.models import (
    AuditActionType,
    AuditLevel,
    ComplianceReportConfig,
    ComplianceStandard,
    ControlType,
    EnforcementLevel,
    ImmutableLedgerConfig,
    LedgerStorageBackend,
    LedgerVerificationMode,
    ReportFormat,
    ReportScope,
    StandardType,
)


class TestBasicAuditRecipe:
    def test_returns_collection(self):
        result = basic_audit_recipe()
        assert result is not None

    def test_has_crud_rule(self):
        result = basic_audit_recipe()
        rule = result.get_rule_by_id("crud_audit")
        assert rule is not None
        assert rule.name == "Audit CRUD Operations"
        assert AuditActionType.CREATE in rule.actions
        assert AuditActionType.UPDATE in rule.actions
        assert AuditActionType.DELETE in rule.actions

    def test_has_access_rule(self):
        result = basic_audit_recipe()
        rule = result.get_rule_by_id("access_audit")
        assert rule is not None
        assert AuditActionType.LOGIN in rule.actions
        assert AuditActionType.LOGOUT in rule.actions

    def test_no_compliance_controls(self):
        result = basic_audit_recipe()
        assert len(result.compliance_controls) == 0

    def test_basic_audit_level(self):
        result = basic_audit_recipe()
        for rule in result.audit_rules:
            assert rule.audit_level == AuditLevel.BASIC

    def test_retention_365_days(self):
        result = basic_audit_recipe()
        for rule in result.audit_rules:
            assert rule.retention_days == 365

    def test_archive_90_days(self):
        result = basic_audit_recipe()
        for rule in result.audit_rules:
            assert rule.archive_after_days == 90

    def test_all_rules_enabled(self):
        result = basic_audit_recipe()
        for rule in result.audit_rules:
            assert rule.enabled is True

    def test_two_rules_total(self):
        result = basic_audit_recipe()
        assert len(result.audit_rules) == 2

    def test_rules_are_active(self):
        result = basic_audit_recipe()
        active = result.get_active_rules()
        assert len(active) == 2


class TestImmutableLedgerRecipe:
    def test_returns_tuple(self):
        result = immutable_ledger_recipe()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_collection_has_rule(self):
        collection, _ = immutable_ledger_recipe()
        rule = collection.get_rule_by_id("immutable_audit")
        assert rule is not None

    def test_detailed_audit_level(self):
        collection, _ = immutable_ledger_recipe()
        rule = collection.get_rule_by_id("immutable_audit")
        assert rule.audit_level == AuditLevel.DETAILED

    def test_7_year_retention(self):
        collection, _ = immutable_ledger_recipe()
        rule = collection.get_rule_by_id("immutable_audit")
        assert rule.retention_days == 2555

    def test_ledger_config_enabled(self):
        _, config = immutable_ledger_recipe()
        assert config.enabled is True

    def test_default_backend_database(self):
        _, config = immutable_ledger_recipe()
        assert config.backend == LedgerStorageBackend.DATABASE

    def test_default_verification_combined(self):
        _, config = immutable_ledger_recipe()
        assert config.verification_mode == LedgerVerificationMode.COMBINED

    def test_merkle_root_enabled(self):
        _, config = immutable_ledger_recipe()
        assert config.enable_merkle_root is True

    def test_forever_retention(self):
        _, config = immutable_ledger_recipe()
        assert config.retention_days == 0

    def test_custom_backend(self):
        _, config = immutable_ledger_recipe(backend=LedgerStorageBackend.BLOCKCHAIN)
        assert config.backend == LedgerStorageBackend.BLOCKCHAIN

    def test_custom_verification_mode(self):
        _, config = immutable_ledger_recipe(verification_mode=LedgerVerificationMode.MERKLE_TREE)
        assert config.verification_mode == LedgerVerificationMode.MERKLE_TREE

    def test_all_action_types_included(self):
        collection, _ = immutable_ledger_recipe()
        rule = collection.get_rule_by_id("immutable_audit")
        expected = {
            AuditActionType.CREATE,
            AuditActionType.UPDATE,
            AuditActionType.DELETE,
            AuditActionType.LOGIN,
            AuditActionType.LOGOUT,
            AuditActionType.EXPORT,
            AuditActionType.APPROVE,
            AuditActionType.REJECT,
        }
        assert all(a in rule.actions for a in expected)


class TestGDPRComplianceRecipe:
    def test_has_data_access_rule(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert rule is not None

    def test_5_year_retention(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert rule.retention_days == 1825

    def test_detailed_level(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert rule.audit_level == AuditLevel.DETAILED

    def test_gdpr_compliance_tags(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert "gdpr" in rule.compliance_tags

    def test_has_consent_control(self):
        result = gdpr_compliance_recipe()
        control = result.get_control_by_id("gdpr_consent")
        assert control is not None
        assert control.standard == StandardType.GDPR
        assert control.control_type == ControlType.PREVENTIVE

    def test_has_erasure_control(self):
        result = gdpr_compliance_recipe()
        control = result.get_control_by_id("gdpr_right_to_erasure")
        assert control is not None
        assert control.control_type == ControlType.DETECTIVE

    def test_two_controls_total(self):
        result = gdpr_compliance_recipe()
        assert len(result.compliance_controls) == 2

    def test_controls_reference_rule(self):
        result = gdpr_compliance_recipe()
        for control in result.compliance_controls:
            assert control.audit_rule_id == "gdpr_data_access"

    def test_read_action_included(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert AuditActionType.READ in rule.actions

    def test_export_action_included(self):
        result = gdpr_compliance_recipe()
        rule = result.get_rule_by_id("gdpr_data_access")
        assert AuditActionType.EXPORT in rule.actions


class TestHIPAAComplianceRecipe:
    def test_has_phi_access_rule(self):
        result = hipaa_compliance_recipe()
        rule = result.get_rule_by_id("hipaa_phi_access")
        assert rule is not None

    def test_6_year_retention(self):
        result = hipaa_compliance_recipe()
        rule = result.get_rule_by_id("hipaa_phi_access")
        assert rule.retention_days == 2190

    def test_hipaa_compliance_tags(self):
        result = hipaa_compliance_recipe()
        rule = result.get_rule_by_id("hipaa_phi_access")
        assert "hipaa" in rule.compliance_tags

    def test_has_minimum_necessary_control(self):
        result = hipaa_compliance_recipe()
        control = result.get_control_by_id("hipaa_minimum_necessary")
        assert control is not None
        assert control.standard == StandardType.HIPAA

    def test_has_audit_trail_control(self):
        result = hipaa_compliance_recipe()
        control = result.get_control_by_id("hipaa_audit_trail")
        assert control is not None
        assert control.enforcement_level == EnforcementLevel.BOTH

    def test_two_controls(self):
        result = hipaa_compliance_recipe()
        assert len(result.compliance_controls) == 2


class TestSOXComplianceRecipe:
    def test_has_financial_audit_rule(self):
        result = sox_compliance_recipe()
        rule = result.get_rule_by_id("sox_financial_audit")
        assert rule is not None

    def test_7_year_retention(self):
        result = sox_compliance_recipe()
        rule = result.get_rule_by_id("sox_financial_audit")
        assert rule.retention_days == 2555

    def test_sox_compliance_tags(self):
        result = sox_compliance_recipe()
        rule = result.get_rule_by_id("sox_financial_audit")
        assert "sox" in rule.compliance_tags

    def test_has_immutable_records_control(self):
        result = sox_compliance_recipe()
        control = result.get_control_by_id("sox_immutable_records")
        assert control is not None
        assert control.standard == StandardType.SOX
        assert control.enforcement_level == EnforcementLevel.BOTH

    def test_has_approval_chain_control(self):
        result = sox_compliance_recipe()
        control = result.get_control_by_id("sox_approval_chain")
        assert control is not None

    def test_approve_reject_in_actions(self):
        result = sox_compliance_recipe()
        rule = result.get_rule_by_id("sox_financial_audit")
        assert AuditActionType.APPROVE in rule.actions
        assert AuditActionType.REJECT in rule.actions

    def test_no_read_action(self):
        result = sox_compliance_recipe()
        rule = result.get_rule_by_id("sox_financial_audit")
        assert AuditActionType.READ not in rule.actions


class TestPCIDSSComplianceRecipe:
    def test_has_cardholder_audit_rule(self):
        result = pci_dss_compliance_recipe()
        rule = result.get_rule_by_id("pci_cardholder_audit")
        assert rule is not None

    def test_1_year_retention(self):
        result = pci_dss_compliance_recipe()
        rule = result.get_rule_by_id("pci_cardholder_audit")
        assert rule.retention_days == 365

    def test_pci_compliance_tags(self):
        result = pci_dss_compliance_recipe()
        rule = result.get_rule_by_id("pci_cardholder_audit")
        assert "pci_dss" in rule.compliance_tags

    def test_has_access_control(self):
        result = pci_dss_compliance_recipe()
        control = result.get_control_by_id("pci_access_control")
        assert control is not None
        assert control.standard == StandardType.PCI_DSS

    def test_one_control(self):
        result = pci_dss_compliance_recipe()
        assert len(result.compliance_controls) == 1


class TestGenerateComplianceReportConfig:
    def test_default_soc2_pdf(self):
        result = generate_compliance_report_config()
        assert result.standard == ComplianceStandard.SOC2
        assert result.report_format == ReportFormat.PDF

    def test_custom_standard(self):
        result = generate_compliance_report_config(standard=ComplianceStandard.GDPR)
        assert result.standard == ComplianceStandard.GDPR

    def test_custom_format(self):
        result = generate_compliance_report_config(format=ReportFormat.CSV)
        assert result.report_format == ReportFormat.CSV

    def test_custom_scope(self):
        result = generate_compliance_report_config(scope=ReportScope.ENTITY, scope_filter="Order")
        assert result.scope == ReportScope.ENTITY
        assert result.scope_filter == "Order"

    def test_includes_evidence(self):
        result = generate_compliance_report_config()
        assert result.include_evidence is True

    def test_includes_ledger_verification(self):
        result = generate_compliance_report_config()
        assert result.include_ledger_verification is True

    def test_no_auto_generate_by_default(self):
        result = generate_compliance_report_config()
        assert result.auto_generate is False

    def test_returns_config_type(self):
        result = generate_compliance_report_config()
        assert isinstance(result, ComplianceReportConfig)

    def test_has_description(self):
        result = generate_compliance_report_config(standard=ComplianceStandard.HIPAA)
        assert "hipaa" in result.description

    def test_to_dict_works(self):
        result = generate_compliance_report_config()
        d = result.to_dict()
        assert d["standard"] == "soc2"
        assert d["report_format"] == "pdf"
