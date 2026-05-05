"""
InvariantManager: Bộ điều phối trung tâm cho Invariant Enforcement.

InvariantManager chịu trách nhiệm:
- Initialize: Đăng ký tất cả built-in invariants
- Validate: Chạy tất cả compile-time checks cho graph
- Report: Generate InvariantReport tổng hợp

Usage:
    manager = InvariantManager()
    manager.initialize()  # Đăng ký built-in invariants
    report = manager.validate(graph)  # Chạy tất cả checks
    print(report.is_passing)  # True/False

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from midicoder.contracts.invariants.models import (
    InvariantCategory,
    InvariantDefinition,
    InvariantResult,
    InvariantReport,
)
from midicoder.contracts.invariants.registry import InvariantRegistry
from midicoder.contracts.invariants.business.checks import register_business_invariants
from midicoder.contracts.invariants.compliance.checks import register_compliance_invariants
from midicoder.contracts.invariants.failure_mode.checks import register_failure_mode_invariants

if TYPE_CHECKING:
    from midicoder.contracts.graph import CapabilityGraph


class InvariantManager:
    """
    Bộ điều phối trung tâm cho Invariant Enforcement System.

    Quản lý vòng đời của invariant enforcement:
    1. Initialize: Đăng ký tất cả built-in invariants
    2. Validate: Chạy compile-time checks
    3. Report: Generate báo cáo tổng hợp

    Usage:
        manager = InvariantManager()
        manager.initialize()
        report = manager.validate(graph)
    """

    def __init__(self) -> None:
        """Khởi tạo InvariantManager với registry singleton."""
        self._registry = InvariantRegistry()
        self._initialized = False

    @property
    def registry(self) -> InvariantRegistry:
        """Lấy InvariantRegistry."""
        return self._registry

    def initialize(self) -> None:
        """
        Đăng ký tất cả built-in invariants.

        Đăng ký 3 nhóm invariants:
        - Business invariants (INV-BIZ-001~005)
        - Compliance invariants (INV-COMP-001~005)
        - Failure-mode invariants (INV-FM-001~005)

        Notes:
            An toàn gọi nhiều lần: chỉ đăng ký khi chưa initialized.
        """
        if self._initialized:
            return

        register_business_invariants(self._registry)
        register_compliance_invariants(self._registry)
        register_failure_mode_invariants(self._registry)

        self._initialized = True

    def validate(self, graph: CapabilityGraph, blueprint_id: str = "") -> InvariantReport:
        """
        Chạy tất cả compile-time invariant checks cho graph.

        Quy trình:
        1. Đảm bảo invariants đã được đăng ký
        2. Lấy tất cả invariants có compile-time enforcement
        3. Chạy từng check function
        4. Aggregate results vào InvariantReport

        Args:
            graph: CapabilityGraph cần validate
            blueprint_id: ID của blueprint (nếu không có, dùng hash của graph)

        Returns:
            InvariantReport với kết quả tất cả checks
        """
        # Đảm bảo initialized
        if not self._initialized:
            self.initialize()

        # Tạo report
        report = InvariantReport(blueprint_id=blueprint_id or str(id(graph)))

        # Lấy tất cả compile-time invariants
        compile_time_invs = [
            inv for inv in self._registry.get_all()
            if inv.is_compile_time
        ]

        # Map từ invariant ID đến check function
        check_functions = {
            "INV-BIZ-001": self._check_entity_ref,
            "INV-BIZ-002": self._check_mutation_txn,
            "INV-BIZ-003": self._check_query_readonly,
            "INV-BIZ-004": self._check_event_consistency,
            "INV-BIZ-005": self._check_state_transition,
            "INV-COMP-001": self._check_pii_encryption,
            "INV-COMP-002": self._check_audit_trail,
            "INV-COMP-003": self._check_data_retention,
            "INV-COMP-004": self._check_tenant_isolation,
            "INV-COMP-005": self._check_permission,
            "INV-FM-001": self._check_error_handler,
            "INV-FM-002": self._check_retry_policy,
            "INV-FM-003": self._check_timeout,
            "INV-FM-004": self._check_circuit_breaker,
            "INV-FM-005": self._check_compensation,
        }

        # Chạy từng check
        for inv in compile_time_invs:
            check_fn = check_functions.get(inv.id)
            if check_fn is not None:
                try:
                    results = check_fn(graph)
                    for result in results:
                        report.add_result(result)
                except Exception as e:
                    # Nếu check function throw exception, ghi là violation
                    report.add_result(InvariantResult(
                        invariant_id=inv.id,
                        category=inv.category,
                        enforcement_mode=inv.enforcement,
                        passed=False,
                        severity=inv.severity,
                        violation_code=inv.violation_code,
                        message=f"Check function '{inv.validator_fn}' throw exception: {e}",
                        context={"error_type": type(e).__name__},
                    ))

        # Generate summary
        report.generate_summary()

        return report

    # ========================================================================
    # Internal check wrappers
    # ========================================================================

    def _check_entity_ref(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_entity_reference_integrity."""
        from midicoder.contracts.invariants.business.checks import check_entity_reference_integrity
        return check_entity_reference_integrity(graph)

    def _check_mutation_txn(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_mutation_transaction_scope."""
        from midicoder.contracts.invariants.business.checks import check_mutation_transaction_scope
        return check_mutation_transaction_scope(graph)

    def _check_query_readonly(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_query_read_only."""
        from midicoder.contracts.invariants.business.checks import check_query_read_only
        return check_query_read_only(graph)

    def _check_event_consistency(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_event_consistency."""
        from midicoder.contracts.invariants.business.checks import check_event_consistency
        return check_event_consistency(graph)

    def _check_state_transition(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_state_machine_transition."""
        from midicoder.contracts.invariants.business.checks import check_state_machine_transition
        return check_state_machine_transition(graph)

    def _check_pii_encryption(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_pii_encryption."""
        from midicoder.contracts.invariants.compliance.checks import check_pii_encryption
        return check_pii_encryption(graph)

    def _check_audit_trail(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_audit_trail."""
        from midicoder.contracts.invariants.compliance.checks import check_audit_trail
        return check_audit_trail(graph)

    def _check_data_retention(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_data_retention."""
        from midicoder.contracts.invariants.compliance.checks import check_data_retention
        return check_data_retention(graph)

    def _check_tenant_isolation(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_tenant_isolation."""
        from midicoder.contracts.invariants.compliance.checks import check_tenant_isolation
        return check_tenant_isolation(graph)

    def _check_permission(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_permission_check."""
        from midicoder.contracts.invariants.compliance.checks import check_permission_check
        return check_permission_check(graph)

    def _check_error_handler(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_error_handler_present."""
        from midicoder.contracts.invariants.failure_mode.checks import check_error_handler_present
        return check_error_handler_present(graph)

    def _check_retry_policy(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_retry_policy."""
        from midicoder.contracts.invariants.failure_mode.checks import check_retry_policy
        return check_retry_policy(graph)

    def _check_timeout(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_timeout_configured."""
        from midicoder.contracts.invariants.failure_mode.checks import check_timeout_configured
        return check_timeout_configured(graph)

    def _check_circuit_breaker(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_circuit_breaker."""
        from midicoder.contracts.invariants.failure_mode.checks import check_circuit_breaker
        return check_circuit_breaker(graph)

    def _check_compensation(self, graph: CapabilityGraph) -> list[InvariantResult]:
        """Wrapper cho check_compensation_defined."""
        from midicoder.contracts.invariants.failure_mode.checks import check_compensation_defined
        return check_compensation_defined(graph)

    def get_invariant(self, invariant_id: str) -> InvariantDefinition:
        """
        Lấy invariant definition theo id.

        Args:
            invariant_id: ID của invariant

        Returns:
            InvariantDefinition

        Raises:
            KeyError: Nếu invariant không tồn tại
        """
        return self._registry.get(invariant_id)

    def get_all_invariants(self) -> list[InvariantDefinition]:
        """
        Lấy tất cả invariants đã đăng ký.

        Returns:
            Danh sách tất cả InvariantDefinition
        """
        return self._registry.get_all()

    def get_by_category(self, category: InvariantCategory) -> list[InvariantDefinition]:
        """
        Lấy invariants theo category.

        Args:
            category: InvariantCategory cần lọc

        Returns:
            Danh sách InvariantDefinition
        """
        return self._registry.get_by_category(category)

    @classmethod
    def reset(cls) -> None:
        """
        Reset manager (dùng cho testing).

        Xóa registry singleton và tạo mới.
        """
        InvariantRegistry.reset()