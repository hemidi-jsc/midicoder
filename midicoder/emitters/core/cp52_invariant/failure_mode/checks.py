"""
Failure-Mode Invariants: Các check cho reliability và error handling.

 INV-FM-001: Error handler present (mutation phải có error handling)
 INV-FM-002: Retry policy defined (external calls phải có retry)
 INV-FM-003: Timeout configured (external calls phải có timeout)
 INV-FM-004: Circuit breaker available (critical external deps)
 INV-FM-005: Compensation defined (saga steps phải có compensation)

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
    from midicoder.contracts import CapabilityGraph


def check_error_handler_present(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-FM-001: Kiểm tra mutations có error handler.

    Mọi mutation phải có error handling obligation.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []
    mutation_types = {"authorized_mutation", "create_record", "update_record", "delete_record"}

    for instance in graph.instances:
        if instance.type in mutation_types:
            has_error_handler = any(
                "error" in (o.type or "").lower()
                for o in graph.obligations
                if o.source == instance.id
            )
            if not has_error_handler:
                results.append(InvariantResult(
                    invariant_id="INV-FM-001",
                    category=InvariantCategory.FAILURE_MODE,
                    enforcement_mode=EnforcementMode.BOTH,
                    passed=False,
                    severity="error",
                    violation_code="MDC-INV-015",
                    message=f"Mutation '{instance.id}' thiếu error handler",
                    context={"instance_id": instance.id},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-FM-001",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả mutations có error handler",
        ))

    return results


def check_retry_policy(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-FM-002: Kiểm tra external calls có retry policy.

    Mọi call_external_service phải có retry config.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        if instance.type == "call_external_service":
            retry = instance.params.get("retry")
            if not retry:
                results.append(InvariantResult(
                    invariant_id="INV-FM-002",
                    category=InvariantCategory.FAILURE_MODE,
                    enforcement_mode=EnforcementMode.RUNTIME,
                    passed=False,
                    severity="warning",
                    violation_code=None,
                    message=f"External call '{instance.id}' thiếu retry policy",
                    context={"instance_id": instance.id},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-FM-002",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=True,
            severity="warning",
            message="Tất cả external calls có retry policy",
        ))

    return results


def check_timeout_configured(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-FM-003: Kiểm tra external calls có timeout.

    Mọi call_external_service phải có timeout config.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        if instance.type == "call_external_service":
            timeout = instance.params.get("timeout")
            if not timeout:
                results.append(InvariantResult(
                    invariant_id="INV-FM-003",
                    category=InvariantCategory.FAILURE_MODE,
                    enforcement_mode=EnforcementMode.RUNTIME,
                    passed=False,
                    severity="warning",
                    violation_code=None,
                    message=f"External call '{instance.id}' thiếu timeout",
                    context={"instance_id": instance.id},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-FM-003",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=True,
            severity="warning",
            message="Tất cả external calls có timeout",
        ))

    return results


def check_circuit_breaker(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-FM-004: Kiểm tra critical external deps có circuit breaker.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        if instance.type == "call_external_service":
            critical = instance.params.get("critical", False)
            circuit_breaker = instance.params.get("circuit_breaker")
            if critical and not circuit_breaker:
                results.append(InvariantResult(
                    invariant_id="INV-FM-004",
                    category=InvariantCategory.FAILURE_MODE,
                    enforcement_mode=EnforcementMode.RUNTIME,
                    passed=False,
                    severity="error",
                    violation_code=None,
                    message=f"Critical external call '{instance.id}' thiếu circuit breaker",
                    context={"instance_id": instance.id},
                ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-FM-004",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=True,
            severity="error",
            message="Tất cả critical external calls có circuit breaker",
        ))

    return results


def check_compensation_defined(graph: CapabilityGraph) -> list[InvariantResult]:
    """
    INV-FM-005: Kiểm tra saga steps có compensation.

    Mọi workflow step có writes phải có compensation defined.

    Args:
        graph: CapabilityGraph cần check

    Returns:
        Danh sách InvariantResult
    """
    results: list[InvariantResult] = []

    for instance in graph.instances:
        if instance.type == "workflow_definition":
            steps = instance.params.get("steps", [])
            for step in steps:
                if isinstance(step, dict):
                    has_writes = bool(step.get("writes"))
                    has_compensation = bool(step.get("compensation"))
                    if has_writes and not has_compensation:
                        results.append(InvariantResult(
                            invariant_id="INV-FM-005",
                            category=InvariantCategory.FAILURE_MODE,
                            enforcement_mode=EnforcementMode.BOTH,
                            passed=False,
                            severity="error",
                            violation_code=None,
                            message=f"Saga step '{step.get('id', 'unknown')}' trong '{instance.id}' thiếu compensation",
                            context={"instance_id": instance.id, "step_id": step.get("id")},
                        ))

    if not results:
        results.append(InvariantResult(
            invariant_id="INV-FM-005",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True,
            severity="error",
            message="Tất cả saga steps có compensation",
        ))

    return results


# ============================================================================
# Invariant Definitions
# ============================================================================

def register_failure_mode_invariants(registry: InvariantRegistry | None = None) -> list[InvariantDefinition]:
    """
    Đăng ký tất cả failure-mode invariants vào registry.

    Args:
        registry: InvariantRegistry (nếu None sẽ dùng singleton)

    Returns:
        Danh sách InvariantDefinition đã đăng ký
    """
    if registry is None:
        registry = InvariantRegistry()

    definitions: list[InvariantDefinition] = [
        InvariantDefinition(
            id="INV-FM-001",
            name="Error Handler Present",
            description="Mọi mutation phải có error handler",
            category=InvariantCategory.FAILURE_MODE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code="MDC-INV-015",
            validator_fn="check_error_handler_present",
            runtime_guard="ErrorHandlerGuard",
            tags=["error", "handling", "reliability"],
        ),
        InvariantDefinition(
            id="INV-FM-002",
            name="Retry Policy Defined",
            description="External calls phải có retry policy",
            category=InvariantCategory.FAILURE_MODE,
            enforcement=EnforcementMode.RUNTIME,
            severity="warning",
            violation_code=None,
            validator_fn="check_retry_policy",
            runtime_guard="RetryGuard",
            tags=["retry", "resilience", "external"],
        ),
        InvariantDefinition(
            id="INV-FM-003",
            name="Timeout Configured",
            description="External calls phải có timeout",
            category=InvariantCategory.FAILURE_MODE,
            enforcement=EnforcementMode.RUNTIME,
            severity="warning",
            violation_code=None,
            validator_fn="check_timeout_configured",
            runtime_guard="TimeoutGuard",
            tags=["timeout", "resilience", "external"],
        ),
        InvariantDefinition(
            id="INV-FM-004",
            name="Circuit Breaker Available",
            description="Critical external deps phải có circuit breaker",
            category=InvariantCategory.FAILURE_MODE,
            enforcement=EnforcementMode.RUNTIME,
            severity="error",
            violation_code=None,
            validator_fn="check_circuit_breaker",
            runtime_guard="CircuitBreakerGuard",
            tags=["circuit-breaker", "resilience", "critical"],
        ),
        InvariantDefinition(
            id="INV-FM-005",
            name="Compensation Defined",
            description="Saga steps có writes phải có compensation",
            category=InvariantCategory.FAILURE_MODE,
            enforcement=EnforcementMode.BOTH,
            severity="error",
            violation_code=None,
            validator_fn="check_compensation_defined",
            runtime_guard="CompensationGuard",
            tags=["saga", "compensation", "rollback"],
        ),
    ]

    for defn in definitions:
        registry.register(defn)

    return definitions