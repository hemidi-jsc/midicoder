# coding: utf-8
"""
Recipe module for CP14 Audit Trail & Compliance Generator.

Recipes provide pre-mixed, ready-to-use configurations that map common
compliance requirements to CP14 pattern vocabulary. Each recipe returns
an AuditComplianceCollection (or ImmutableLedgerConfig / ComplianceReportConfig)
with values filled in.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.cp14_audit_compliance.models import (
    AuditActionType,
    AuditComplianceCollection,
    AuditLevel,
    AuditRule,
    ComplianceControl,
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


# ===========================================================================
# Basic Audit Recipe
# ===========================================================================


def basic_audit_recipe() -> AuditComplianceCollection:
    """
    Basic audit recipe — log all CRUD operations with 1-year retention.

    Use case: Internal tools, non-regulated apps.

    Returns:
        AuditComplianceCollection with basic audit rules (no compliance controls).
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="crud_audit",
            name="Audit CRUD Operations",
            actions=[
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
            ],
            audit_level=AuditLevel.BASIC,
            retention_days=365,
            archive_after_days=90,
            description="Log tất cả thao tác CREATE/UPDATE/DELETE",
        )
    )

    collection.add_rule(
        AuditRule(
            id="access_audit",
            name="Audit Access Events",
            actions=[
                AuditActionType.LOGIN,
                AuditActionType.LOGOUT,
            ],
            audit_level=AuditLevel.BASIC,
            retention_days=365,
            archive_after_days=90,
            description="Log sự kiện đăng nhập/đăng xuất",
        )
    )

    return collection


# ===========================================================================
# Immutable Ledger Recipe
# ===========================================================================


def immutable_ledger_recipe(
    backend: LedgerStorageBackend = LedgerStorageBackend.DATABASE,
    verification_mode: LedgerVerificationMode = LedgerVerificationMode.COMBINED,
) -> tuple[AuditComplianceCollection, ImmutableLedgerConfig]:
    """
    Immutable ledger recipe — append-only hash chain with tamper detection.

    Use case: Financial systems, legal records, any tamper-proof audit requirement.

    Args:
        backend: Storage backend (database, blockchain, append_only_store, signed_chain)
        verification_mode: Verification mode (hash_chain, merkle_tree, digital_signature, combined)

    Returns:
        Tuple of (AuditComplianceCollection, ImmutableLedgerConfig)
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="immutable_audit",
            name="Immutable Audit Trail",
            actions=[
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
                AuditActionType.LOGIN,
                AuditActionType.LOGOUT,
                AuditActionType.EXPORT,
                AuditActionType.APPROVE,
                AuditActionType.REJECT,
            ],
            audit_level=AuditLevel.DETAILED,
            retention_days=2555,  # ~7 years
            archive_after_days=365,
            description="Audit trail immutable — append-only với hash chain",
        )
    )

    config = ImmutableLedgerConfig(
        enabled=True,
        backend=backend,
        verification_mode=verification_mode,
        batch_size=100,
        enable_merkle_root=True,
        merkle_batch_size=1000,
        retention_days=0,  # forever
        description="Immutable ledger cho audit trail",
    )

    return collection, config


# ===========================================================================
# Compliance Recipes
# ===========================================================================


def gdpr_compliance_recipe() -> AuditComplianceCollection:
    """
    GDPR compliance recipe — data processing audit + right-to-be-forgotten tracking.

    Rules:
    - All data access logged with detailed level
    - Data export/delete tracked
    - 5-year retention (EU regulation)
    - PII access requires audit

    Returns:
        AuditComplianceCollection with GDPR audit rules and compliance controls.
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="gdpr_data_access",
            name="GDPR Data Access Audit",
            actions=[
                AuditActionType.READ,
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
                AuditActionType.EXPORT,
            ],
            audit_level=AuditLevel.DETAILED,
            retention_days=1825,  # 5 years
            archive_after_days=365,
            compliance_tags=["gdpr"],
            description="Audit truy cập dữ liệu cá nhân theo GDPR",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="gdpr_consent",
            name="GDPR Consent Enforcement",
            standard=StandardType.GDPR,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.BOTH,
            audit_rule_id="gdpr_data_access",
            description="Yêu cầu consent trước khi xử lý dữ liệu cá nhân",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="gdpr_right_to_erasure",
            name="GDPR Right to Erasure Tracking",
            standard=StandardType.GDPR,
            control_type=ControlType.DETECTIVE,
            enforcement_level=EnforcementLevel.RUNTIME,
            audit_rule_id="gdpr_data_access",
            description="Theo dõi yêu cầu xóa dữ liệu (right to be forgotten)",
        )
    )

    return collection


def hipaa_compliance_recipe() -> AuditComplianceCollection:
    """
    HIPAA compliance recipe — protected health information (PHI) audit.

    Rules:
    - All PHI access logged with detailed level
    - Create/update/delete/export tracked
    - 6-year retention (HIPAA requirement)
    - Access to patient records requires audit

    Returns:
        AuditComplianceCollection with HIPAA audit rules and compliance controls.
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="hipaa_phi_access",
            name="HIPAA PHI Access Audit",
            actions=[
                AuditActionType.READ,
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
                AuditActionType.EXPORT,
            ],
            audit_level=AuditLevel.DETAILED,
            retention_days=2190,  # 6 years
            archive_after_days=365,
            compliance_tags=["hipaa"],
            description="Audit truy cập thông tin sức khỏe được bảo vệ (PHI)",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="hipaa_minimum_necessary",
            name="HIPAA Minimum Necessary Access",
            standard=StandardType.HIPAA,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.RUNTIME,
            audit_rule_id="hipaa_phi_access",
            description="Giới hạn truy cập PHI chỉ mức cần thiết tối thiểu",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="hipaa_audit_trail",
            name="HIPAA Audit Trail Maintenance",
            standard=StandardType.HIPAA,
            control_type=ControlType.DETECTIVE,
            enforcement_level=EnforcementLevel.BOTH,
            audit_rule_id="hipaa_phi_access",
            description="Duy trì audit trail cho tất cả PHI access",
        )
    )

    return collection


def sox_compliance_recipe() -> AuditComplianceCollection:
    """
    SOX compliance recipe — financial reporting audit.

    Rules:
    - All financial data mutations logged
    - Approval/rejection tracked
    - 7-year retention (SOX requirement)
    - Immutable ledger recommended

    Returns:
        AuditComplianceCollection with SOX audit rules and compliance controls.
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="sox_financial_audit",
            name="SOX Financial Data Audit",
            actions=[
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
                AuditActionType.APPROVE,
                AuditActionType.REJECT,
            ],
            audit_level=AuditLevel.DETAILED,
            retention_days=2555,  # 7 years
            archive_after_days=365,
            compliance_tags=["sox"],
            description="Audit dữ liệu tài chính theo SOX",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="sox_immutable_records",
            name="SOX Immutable Financial Records",
            standard=StandardType.SOX,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.BOTH,
            audit_rule_id="sox_financial_audit",
            description="Ghi chép tài chính phải immutable và tamper-proof",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="sox_approval_chain",
            name="SOX Approval Chain Verification",
            standard=StandardType.SOX,
            control_type=ControlType.DETECTIVE,
            enforcement_level=EnforcementLevel.RUNTIME,
            audit_rule_id="sox_financial_audit",
            description="Xác minh chuỗi phê duyệt cho giao dịch tài chính",
        )
    )

    return collection


def pci_dss_compliance_recipe() -> AuditComplianceCollection:
    """
    PCI DSS compliance recipe — payment card data audit.

    Rules:
    - All payment card data access logged
    - Export/import tracked
    - 1-year retention minimum (PCI DSS)
    - Access to cardholder data requires audit

    Returns:
        AuditComplianceCollection with PCI DSS audit rules and compliance controls.
    """
    collection = AuditComplianceCollection()

    collection.add_rule(
        AuditRule(
            id="pci_cardholder_audit",
            name="PCI DSS Cardholder Data Audit",
            actions=[
                AuditActionType.READ,
                AuditActionType.CREATE,
                AuditActionType.UPDATE,
                AuditActionType.DELETE,
                AuditActionType.EXPORT,
            ],
            audit_level=AuditLevel.DETAILED,
            retention_days=365,
            archive_after_days=90,
            compliance_tags=["pci_dss"],
            description="Audit truy cập dữ liệu thẻ thanh toán theo PCI DSS",
        )
    )

    collection.add_control(
        ComplianceControl(
            id="pci_access_control",
            name="PCI DSS Access Control",
            standard=StandardType.PCI_DSS,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.BOTH,
            audit_rule_id="pci_cardholder_audit",
            description="Kiểm soát truy cập dữ liệu thẻ thanh toán",
        )
    )

    return collection


# ===========================================================================
# Compliance Report Recipes
# ===========================================================================


def generate_compliance_report_config(
    standard: ComplianceStandard = ComplianceStandard.SOC2,
    format: ReportFormat = ReportFormat.PDF,
    scope: ReportScope = ReportScope.ALL,
    scope_filter: str = "",
) -> ComplianceReportConfig:
    """
    Generate a ComplianceReportConfig for a given standard.

    Args:
        standard: Compliance standard (soc2, gdpr, hipaa, pci_dss, sox, iso27001)
        format: Output format (pdf, csv, json, html, xlsx)
        scope: Report scope (all, entity, actor, time_range, tenant, action)
        scope_filter: Filter value for scope

    Returns:
        ComplianceReportConfig ready for use.
    """
    return ComplianceReportConfig(
        report_format=format,
        standard=standard,
        scope=scope,
        scope_filter=scope_filter,
        include_evidence=True,
        include_ledger_verification=True,
        auto_generate=False,
        description=f"Báo cáo compliance cho {standard.value}",
    )


__all__ = [
    "basic_audit_recipe",
    "immutable_ledger_recipe",
    "gdpr_compliance_recipe",
    "hipaa_compliance_recipe",
    "sox_compliance_recipe",
    "pci_dss_compliance_recipe",
    "generate_compliance_report_config",
]
