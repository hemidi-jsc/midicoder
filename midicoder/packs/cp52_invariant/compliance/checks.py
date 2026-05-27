"""
Compliance Invariants: Các check cho regulatory compliance.

 INV-COMP-001: PII encryption required (RX01)
 INV-COMP-002: Audit trail mandatory (RX11)
 INV-COMP-003: Data retention policy enforced (RX01)
 INV-COMP-004: Tenant isolation enforced (CP02)
 INV-COMP-005: Permission check required (CP03-CP04)

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from midicoder.packs.cp52_invariant.models import (
    InvariantCategory,
    EnforcementMode,
    InvariantDefinition,
    InvariantResult,
)
from midicoder.packs.cp52_invariant.registry import InvariantRegistry

if TYPE_CHECKING:
    from midicoder.contracts import CapabilityGraph


def check_pii_encryption(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-COMP-001: Kiểm tra PII fields được encrypt (RX01).

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    pii_fields = {"email", "phone", "address", "ssn", "tax_id", "birth_date"}

    for instance in graph.instances:
        fields = instance.params.get("fields", [])
        for f in fields:
            field_name = f if isinstance(f, str) else f.get("name", "")
            if field_name.lower() in pii_fields:
                encrypted = instance.params.get("encrypted", False)
                if not encrypted:
                    results.append(InvariantResult(
                        invariant_id="INV-COMP-001",
                        category=InvariantCategory.COMPLIANCE,
                        enforcement_mode=EnforcementMode.BOTH,
                        passed=False,
                        severity="error",
                        violation_code="MDC-INV-011",
                        message=f"PII field '{field_name}' trong '{instance.id}' không được encrypt",
                        context={"instance_id": instance.id, "field": field_name},
                    ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-COMP-001",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả PII fields được encrypt",
        ))

    return results


def check_audit_trail(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-COMP-002: Kiểm tra audit trail mandatory (RX11).

    Mọi mutation phải có audit log obligation.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    mutation_types = {"authorized_mutation", "create_record", "update_record", "delete_record"}

    for instance in graph.instances:
        if instance.type in mutation_types:
            has_audit = any(
                "audit" in (o.type or "").lower()
                for o in graph.obligations
                if o.source == instance.id
            )
            if not has_audit:
                results.append(InvariantResult(
                    invariant_id="INV-COMP-002",
                    category=InvariantCategory.COMPLIANCE,
                    enforcement_mode=EnforcementMode.BOTH,
                    passed=False,
                    severity="error",
                    violation_code="MDC-INV-012",
                    message=f"Mutation '{instance.id}' thiếu audit trail",
                    context={"instance_id": instance.id},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-COMP-002",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả mutations có audit trail",
        ))

    return results


def check_data_retention(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-COMP-003: Kiểm tra data retention policy enforced (RX01).

    Các instance lưu trữ dữ liệu PII phải có retention policy defined.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    pii_fields = {"email", "phone", "address", "ssn", "tax_id", "birth_date"}
    storage_types = {"create_record", "update_record", "authorized_mutation"}

    for instance in graph.instances:
        if instance.type in storage_types:
            fields = instance.params.get("fields", [])
            has_pii = any(
                (f if isinstance(f, str) else f.get("name", "")).lower() in pii_fields
                for f in fields
            )
            if has_pii:
                retention = instance.params.get("retention_policy")
                if not retention:
                    results.append(InvariantResult(
                        invariant_id="INV-COMP-003",
                        category=InvariantCategory.COMPLIANCE,
                        enforcement_mode=EnforcementMode.BOTH,
                        passed=False,
                        severity="error",
                        violation_code=None,
                        message=f"Instance '{instance.id}' lưu PII nhưng thiếu retention policy",
                        context={"instance_id": instance.id},
                    ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-COMP-003",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả instances lưu PII có retention policy",
        ))

    return results


def check_tenant_isolation(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-COMP-004: Kiểm tra tenant isolation enforced (CP02).

    Mọi instance phải có tenant filter.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        tenant_scope = instance.params.get("tenant_scope")
        if not tenant_scope:
            results.append(InvariantResult(
                invariant_id="INV-COMP-004",
                category=InvariantCategory.COMPLIANCE,
                enforcement_mode=EnforcementMode.BOTH,
                passed=False,
                severity="error",
                violation_code="MDC-INV-013",
                message=f"Instance '{instance.id}' thiếu tenant_scope",
                context={"instance_id": instance.id},
            ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-COMP-004",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả instances có tenant isolation",
        ))

    return results


def check_permission_check(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-COMP-005: Kiểm tra permission check required (CP03-CP04).

    Mọi authorized mutation/query phải có permission.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    auth_types = {"authorized_mutation", "authorized_query"}

    for instance in graph.instances:
        if instance.type in auth_types:
            permission = instance.params.get("permission")
            if not permission:
                results.append(InvariantResult(
                    invariant_id="INV-COMP-005",
                    category=InvariantCategory.COMPLIANCE,
                    enforcement_mode=EnforcementMode.BOTH,
                    passed=False,
                    severity="error",
                    violation_code="MDC-INV-014",
                    message=f"Instance '{instance.id}' thiếu permission check",
                    context={"instance_id": instance.id, "type": instance.type},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-COMP-005",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả authorized instances có permission check",
        ))

    return results


# ============================================================================
# Invariant Definitions
# ============================================================================

def register_compliance_invariants(registry: InvariantRegistry | None = None) -> list[InvariantDefinition]:
    """
    Đăng ký tất cả compliance invariants vào registry.

    Args:
        registry: InvariantRegistry (nếu None sẽ dùng singleton)

    Returns:
        Danh sách InvariantDefinition đã đăng ký
    """
    if registry is None:
        registry = InvariantRegistry()

    definitions: list[InvariantDefinition] = [
        InvariantDefinition(
            id="INV-COMP-001",
            name="PII Encryption Required",
            description="Tất cả PII fields phải được encrypt",
            category=InvariantCategory.COMPLIANCE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-011",
            overlay="RX01",
            validator_fn="check_pii_encryption",
            runtime_guard="PIIEncryptionGuard",
            tags=["pii", "encryption", "gdpr"],
        ),
        InvariantDefinition(
            id="INV-COMP-002",
            name="Audit Trail Mandatory",
            description="Mọi mutation phải có audit trail",
            category=InvariantCategory.COMPLIANCE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-012",
            overlay="RX11",
            validator_fn="check_audit_trail",
            runtime_guard="AuditTrailGuard",
            tags=["audit", "trail", "immutability"],
        ),
        InvariantDefinition(
            id="INV-COMP-003",
            name="Data Retention Policy Enforced",
            description="Instances lưu trữ PII phải có retention policy",
            category=InvariantCategory.COMPLIANCE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code=None,
            overlay="RX01",
            validator_fn="check_data_retention",
            runtime_guard="DataRetentionGuard",
            tags=["data-retention", "gdpr", "privacy"],
        ),
        InvariantDefinition(
            id="INV-COMP-004",
            name="Tenant Isolation Enforced",
            description="Mọi instance phải có tenant isolation",
            category=InvariantCategory.COMPLIANCE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-013",
            validator_fn="check_tenant_isolation",
            runtime_guard="TenantIsolationGuard",
            tags=["tenant", "isolation", "multi-tenant"],
        ),
        InvariantDefinition(
            id="INV-COMP-005",
            name="Permission Check Required",
            description="Authorized instances phải có permission check",
            category=InvariantCategory.COMPLIANCE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-014",
            validator_fn="check_permission_check",
            runtime_guard="PermissionGuard",
            tags=["permission", "authorization", "rbac"],
        ),
    ]

    for defn in definitions:
        registry.register(defn)

    return definitions