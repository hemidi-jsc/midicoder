"""
Business Invariants: Các check cho domain business logic.

 INV-BIZ-001: Entity reference integrity
 INV-BIZ-002: Command-mutation consistency (transaction scope)
 INV-BIZ-003: Query-read-only enforcement
 INV-BIZ-004: Event-consistency (event sau mutation)
 INV-BIZ-005: State-machine transition valid

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from midicoder.emitters.core.cp52_invariant.models import (
    InvariantCategory,
    EnforcementMode,
    InvariantDefinition,
    InvariantResult,
)
from midicoder.emitters.core.cp52_invariant.registry import InvariantRegistry

if TYPE_CHECKING:
    from midicoder.contracts.graph import CapabilityGraph


def check_entity_reference_integrity(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-BIZ-001: Kiểm tra entity references được resolve đúng.

    Kiểm tra rằng tất cả entity_ref trong instances đều trỏ đến
    một entity đã được declare trong graph.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    # Xây dựng set entities từ reads/writes
    entities: set[str] = set()
    for instance in graph.instances:
        entities.update(instance.reads)
        entities.update(instance.writes)

    for instance in graph.instances:
        entity_ref = instance.params.get("entity_ref")
        if entity_ref and entity_ref not in entities:
            results.append(InvariantResult(
                invariant_id="INV-BIZ-001",
                category=InvariantCategory.BUSINESS,
                enforcement_mode=EnforcementMode.COMPILE_TIME,
                passed=False,
                severity="error",
                violation_code="MDC-INV-006",
                message=f"Entity ref '{entity_ref}' trong '{instance.id}' không tìm thấy",
                context={"instance_id": instance.id, "entity_ref": entity_ref},
            ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-BIZ-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
            message="Tất cả entity references được resolve đúng",
        ))

    return results


def check_mutation_transaction_scope(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-BIZ-002: Kiểm tra mutations có transaction scope.

    Mọi instance có writes không rỗng phải có transaction obligation.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    mutation_types = {"authorized_mutation", "create_record", "update_record", "delete_record"}

    for instance in graph.instances:
        if instance.type in mutation_types and instance.writes:
            # Check có transaction obligation không
            has_txn = any(
                "transaction" in (o.type or "").lower()
                for o in graph.obligations
                if o.source == instance.id
            )
            if not has_txn:
                results.append(InvariantResult(
                    invariant_id="INV-BIZ-002",
                    category=InvariantCategory.BUSINESS,
                    enforcement_mode=EnforcementMode.BOTH,
                    passed=False,
                    severity="error",
                    violation_code="MDC-INV-007",
                    message=f"Mutation '{instance.id}' thiếu transaction scope",
                    context={"instance_id": instance.id, "writes": instance.writes},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-BIZ-002",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả mutations có transaction scope",
        ))

    return results


def check_query_read_only(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-BIZ-003: Kiểm tra queries chỉ đọc không ghi.

    Mọi instance type query không được có writes.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    query_types = {"authorized_query", "query_records", "load_entity"}

    for instance in graph.instances:
        if instance.type in query_types and instance.writes:
            results.append(InvariantResult(
                invariant_id="INV-BIZ-003",
                category=InvariantCategory.BUSINESS,
                enforcement_mode=EnforcementMode.BOTH,
                passed=False,
                severity="error",
                violation_code="MDC-INV-008",
                message=f"Query '{instance.id}' có writes (phải read-only)",
                context={"instance_id": instance.id, "writes": instance.writes},
            ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-BIZ-003",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả queries là read-only",
        ))

    return results


def check_event_consistency(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-BIZ-004: Kiểm tra event publish sau mutation commit.

    Kiểm tra rằng publish_event instances có mutation tương ứng trước đó.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    # Collect tất cả mutation instances
    mutation_ids = {
        inst.id for inst in graph.instances
        if inst.type in {"authorized_mutation", "create_record", "update_record", "delete_record"}
    }

    # Check publish_event instances
    for instance in graph.instances:
        if instance.type == "publish_event":
            # Event nên có source mutation ref
            source = instance.params.get("source")
            if source and source not in mutation_ids:
                results.append(InvariantResult(
                    invariant_id="INV-BIZ-004",
                    category=InvariantCategory.BUSINESS,
                    enforcement_mode=EnforcementMode.COMPILE_TIME,
                    passed=False,
                    severity="error",
                    violation_code="MDC-INV-009",
                    message=f"Event '{instance.id}' source '{source}' không phải mutation",
                    context={"instance_id": instance.id, "source": source},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-BIZ-004",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
            message="Tất cả events có source mutation hợp lệ",
        ))

    return results


def check_state_machine_transition(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-BIZ-005: Kiểm tra state machine transitions hợp lệ.

    Kiểm tra workflow instances có transitions được định nghĩa.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        if instance.type == "workflow_definition":
            transitions = instance.params.get("transitions", [])
            states = instance.params.get("states", [])
            state_set = set(states)

            for transition in transitions:
                if isinstance(transition, dict):
                    from_state = transition.get("from")
                    to_state = transition.get("to")
                    if from_state not in state_set or to_state not in state_set:
                        results.append(InvariantResult(
                            invariant_id="INV-BIZ-005",
                            category=InvariantCategory.BUSINESS,
                            enforcement_mode=EnforcementMode.BOTH,
                            passed=False,
                            severity="error",
                            violation_code="MDC-INV-010",
                            message=f"Transition '{from_state}→{to_state}' trong '{instance.id}' không hợp lệ",
                            context={
                                "instance_id": instance.id,
                                "transition": f"{from_state}→{to_state}",
                            },
                        ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-BIZ-005",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả state transitions hợp lệ",
        ))

    return results


# ============================================================================
# Invariant Definitions
# ============================================================================

def register_business_invariants(registry: InvariantRegistry | None = None) -> list[InvariantDefinition]:
    """
    Đăng ký tất cả business invariants vào registry.

    Args:
        registry: InvariantRegistry (nếu None sẽ dùng singleton)

    Returns:
        Danh sách InvariantDefinition đã đăng ký
    """
    if registry is None:
        registry = InvariantRegistry()

    definitions: list[InvariantDefinition] = [
        InvariantDefinition(
            id="INV-BIZ-001",
            name="Entity Reference Integrity",
            description="Tất cả entity references phải resolve được đến entity đã declare",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.COMPILE_TIME,
            severity="error",
            violation_code="MDC-INV-006",
            validator_fn="check_entity_reference_integrity",
            tags=["entity", "reference", "integrity"],
        ),
        InvariantDefinition(
            id="INV-BIZ-002",
            name="Mutation Transaction Scope",
            description="Mọi mutation phải có transaction scope",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-007",
            validator_fn="check_mutation_transaction_scope",
            runtime_guard="TransactionGuard",
            tags=["mutation", "transaction", "consistency"],
        ),
        InvariantDefinition(
            id="INV-BIZ-003",
            name="Query Read-Only Enforcement",
            description="Queries không được có write operations",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-008",
            validator_fn="check_query_read_only",
            runtime_guard="ReadOnlyGuard",
            tags=["query", "read-only", "integrity"],
        ),
        InvariantDefinition(
            id="INV-BIZ-004",
            name="Event Consistency",
            description="Event publish phải có source mutation hợp lệ",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.COMPILE_TIME,
            severity="error",
            violation_code="MDC-INV-009",
            validator_fn="check_event_consistency",
            tags=["event", "consistency", "ordering"],
        ),
        InvariantDefinition(
            id="INV-BIZ-005",
            name="State Machine Transition Valid",
            description="Workflow transitions phải trỏ đến states hợp lệ",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-010",
            validator_fn="check_state_machine_transition",
            runtime_guard="StateTransitionGuard",
            tags=["workflow", "state-machine", "transition"],
        ),
    ]

    for defn in definitions:
        registry.register(defn)

    return definitions