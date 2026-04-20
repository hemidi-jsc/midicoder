"""
Tests cho Obligation Coverage Check - Epic E05 Task E05-006

Module này test logic kiểm tra coverage của obligations trong hệ thống.

Theo SoT requirement.md:
- Verifier phải check coverage của obligations tại compile-time
- Fail hard nếu obligation không được phủ
- OBLIGATION_NOT_COVERED là critical error

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.graph import (
    CapabilityGraph,
    CapabilityInstance,
    CoreCapability,
    MacroCapability,
    Obligation,
)
from midicoder.contracts.validation import (
    ValidationReport,
    ValidationError,
    ErrorCode,
    ValidationStatus,
    check_obligation_coverage,
    get_unsatisfied_obligations,
    get_obligation_coverage_summary,
)
from midicoder.contracts.artifact import ArtifactMetadata


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_capability_graph() -> CapabilityGraph:
    """
    Tạo sample capability graph với instances và obligations.
    
    Returns:
        CapabilityGraph mẫu cho testing
    """
    return CapabilityGraph(
        core_capabilities=[
            CoreCapability(
                id="authorize_permission",
                name="Authorize Permission",
                description="Check user có permission",
            ),
            CoreCapability(
                id="enforce_tenant_scope",
                name="Enforce Tenant Scope",
                description="Ensure tenant isolation",
            ),
            CoreCapability(
                id="create_record",
                name="Create Record",
                description="Create new record",
            ),
        ],
        macro_capabilities=[
            MacroCapability(
                id="authorized_mutation",
                name="Authorized Mutation",
                description="Mutation với permission check và tenant scope",
                expands_to=[
                    "authorize_permission",
                    "enforce_tenant_scope",
                    "create_record",
                ],
                default_obligations=[
                    "permission_check_required",
                    "tenant_filter_required",
                ],
            ),
        ],
        instances=[
            CapabilityInstance(
                id="create_order",
                type="authorized_mutation",
                description="Tạo đơn hàng mới",
                params={"permission": "order.create", "entity": "Order"},
                obligations=[
                    "permission_check_required",
                    "tenant_filter_required",
                ],
            ),
        ],
        obligations=[
            Obligation(
                id="perm_check_001",
                type="permission_check_required",
                description="Yêu cầu permission check cho order.create",
                source="capability:create_order",
                satisfied=True,
                satisfaction_evidence="mir.json:ops[0]",
            ),
            Obligation(
                id="tenant_filter_001",
                type="tenant_filter_required",
                description="Yêu cầu tenant filter cho create_order",
                source="capability:create_order",
                satisfied=True,
                satisfaction_evidence="mir.json:ops[1]",
            ),
        ],
    )


@pytest.fixture
def graph_with_unsatisfied_obligations() -> CapabilityGraph:
    """
    Tạo graph với obligations chưa được satisfy.
    
    Returns:
        CapabilityGraph có unsatisfied obligations
    """
    return CapabilityGraph(
        instances=[
            CapabilityInstance(
                id="delete_customer",
                type="authorized_mutation",
                description="Xóa khách hàng",
                obligations=[
                    "permission_check_required",
                    "tenant_filter_required",
                    "audit_log_required",
                ],
            ),
        ],
        obligations=[
            Obligation(
                id="perm_check_002",
                type="permission_check_required",
                description="Yêu cầu permission check cho customer.delete",
                source="capability:delete_customer",
                satisfied=True,
                satisfaction_evidence="mir.json:ops[0]",
            ),
            Obligation(
                id="tenant_filter_002",
                type="tenant_filter_required",
                description="Yêu cầu tenant filter cho delete_customer",
                source="capability:delete_customer",
                satisfied=False,  # Chưa satisfied
            ),
            Obligation(
                id="audit_log_001",
                type="audit_log_required",
                description="Yêu cầu audit log cho delete_customer",
                source="capability:delete_customer",
                satisfied=False,  # Chưa satisfied
            ),
        ],
    )


@pytest.fixture
def empty_graph() -> CapabilityGraph:
    """
    Tạo empty graph.
    
    Returns:
        CapabilityGraph trống
    """
    return CapabilityGraph()


# ============================================================================
# Test get_unsatisfied_obligations
# ============================================================================

class TestGetUnsatisfiedObligations:
    """Tests cho hàm get_unsatisfied_obligations."""

    def test_returns_all_unsatisfied_obligations(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về danh sách tất cả obligations chưa satisfied.
        
        Case: Graph có 2 unsatisfied obligations
        Expected: Hàm trả về 2 obligations
        """
        result = get_unsatisfied_obligations(graph_with_unsatisfied_obligations)
        
        assert len(result) == 2
        assert all(not o.satisfied for o in result)

    def test_returns_empty_when_all_satisfied(
        self,
        sample_capability_graph: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về empty list khi tất cả obligations đã satisfied.
        
        Case: Graph có 2 obligations, cả 2 đều satisfied
        Expected: Hàm trả về empty list
        """
        result = get_unsatisfied_obligations(sample_capability_graph)
        
        assert len(result) == 0

    def test_returns_empty_for_empty_graph(self, empty_graph: CapabilityGraph) -> None:
        """
        Test: Trả về empty list cho graph trống.
        
        Case: Graph không có obligations
        Expected: Hàm trả về empty list
        """
        result = get_unsatisfied_obligations(empty_graph)
        
        assert len(result) == 0


# ============================================================================
# Test check_obligation_coverage
# ============================================================================

class TestCheckObligationCoverage:
    """Tests cho hàm check_obligation_coverage."""

    def test_returns_pass_when_all_satisfied(
        self,
        sample_capability_graph: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về PASS khi tất cả obligations đã satisfied.
        
        Case: Graph có 2 obligations, cả 2 đều satisfied
        Expected: ValidationReport với status PASS
        """
        report = check_obligation_coverage(
            sample_capability_graph,
            "test_capability_graph",
        )
        
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("obligation_coverage") == ValidationStatus.PASS.value

    def test_returns_fail_with_errors_when_unsatisfied(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về FAIL với errors khi có obligations chưa satisfied.
        
        Case: Graph có 2 unsatisfied obligations
        Expected: ValidationReport với status FAIL và 2 errors
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) == 2
        assert report.checks.get("obligation_coverage") == ValidationStatus.FAIL.value

    def test_errors_have_correct_code(self, graph_with_unsatisfied_obligations: CapabilityGraph) -> None:
        """
        Test: Errors có code OBLIGATION_NOT_COVERED.
        
        Case: Graph có unsatisfied obligations
        Expected: Mỗi error có code = OBLIGATION_NOT_COVERED
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        for error in report.errors:
            assert error.code == ErrorCode.OBLIGATION_NOT_COVERED.value

    def test_errors_are_critical(self, graph_with_unsatisfied_obligations: CapabilityGraph) -> None:
        """
        Test: Errors là critical errors.
        
        Case: Graph có unsatisfied obligations
        Expected: Tất cả errors đều là critical
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        for error in report.errors:
            assert error.is_critical is True

    def test_error_message_includes_obligation_info(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Error message chứa thông tin obligation.
        
        Case: Graph có unsatisfied obligations
        Expected: Error message chứa obligation ID và type
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        # Kiểm tra error message có chứa thông tin về obligation
        error_messages = [e.message for e in report.errors]
        assert any("tenant_filter_002" in msg for msg in error_messages)
        assert any("audit_log_001" in msg for msg in error_messages)

    def test_error_path_points_to_source(self, graph_with_unsatisfied_obligations: CapabilityGraph) -> None:
        """
        Test: Error path chỉ đến source capability.
        
        Case: Graph có unsatisfied obligations từ delete_customer
        Expected: Error path chứa "delete_customer"
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        for error in report.errors:
            assert "delete_customer" in (error.path or "")

    def test_summary_includes_coverage_stats(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Summary chứa statistics về coverage.
        
        Case: Graph có 3 obligations, 1 satisfied, 2 unsatisfied
        Expected: Summary có total_obligations=3, satisfied=1, unsatisfied=2
        """
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "test_capability_graph",
        )
        
        assert "total_obligations" in report.summary
        assert "satisfied_obligations" in report.summary
        assert "unsatisfied_obligations" in report.summary
        assert report.summary["total_obligations"] == 3
        assert report.summary["satisfied_obligations"] == 1
        assert report.summary["unsatisfied_obligations"] == 2

    def test_empty_graph_returns_pass(self, empty_graph: CapabilityGraph) -> None:
        """
        Test: Empty graph trả về PASS (không có obligations cần check).
        
        Case: Graph không có obligations
        Expected: ValidationReport với status PASS
        """
        report = check_obligation_coverage(
            empty_graph,
            "test_empty_graph",
        )
        
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0


# ============================================================================
# Test get_obligation_coverage_summary
# ============================================================================

class TestGetObligationCoverageSummary:
    """Tests cho hàm get_obligation_coverage_summary."""

    def test_returns_correct_summary(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về summary chính xác.
        
        Case: Graph có 3 obligations, 1 satisfied, 2 unsatisfied
        Expected: Summary với statistics chính xác
        """
        summary = get_obligation_coverage_summary(graph_with_unsatisfied_obligations)
        
        assert summary["total_obligations"] == 3
        assert summary["satisfied_count"] == 1
        assert summary["unsatisfied_count"] == 2
        assert summary["coverage_percentage"] == pytest.approx(33.33, rel=0.1)

    def test_returns_100_percent_when_all_satisfied(
        self,
        sample_capability_graph: CapabilityGraph,
    ) -> None:
        """
        Test: Trả về 100% coverage khi tất cả satisfied.
        
        Case: Graph có 2 obligations, cả 2 đều satisfied
        Expected: coverage_percentage = 100.0
        """
        summary = get_obligation_coverage_summary(sample_capability_graph)
        
        assert summary["coverage_percentage"] == 100.0

    def test_returns_0_percent_for_empty_graph(self, empty_graph: CapabilityGraph) -> None:
        """
        Test: Trả về 0% cho empty graph.
        
        Case: Graph không có obligations
        Expected: coverage_percentage = 0.0
        """
        summary = get_obligation_coverage_summary(empty_graph)
        
        assert summary["coverage_percentage"] == 0.0
        assert summary["total_obligations"] == 0

    def test_includes_obligations_by_type(self, graph_with_unsatisfied_obligations: CapabilityGraph) -> None:
        """
        Test: Summary chứa breakdown theo obligation type.
        
        Case: Graph có các types: permission_check_required, tenant_filter_required, audit_log_required
        Expected: obligations_by_type chứa đúng các types
        """
        summary = get_obligation_coverage_summary(graph_with_unsatisfied_obligations)
        
        assert "obligations_by_type" in summary
        by_type = summary["obligations_by_type"]
        
        # Kiểm tra có các types
        assert "permission_check_required" in by_type
        assert "tenant_filter_required" in by_type
        assert "audit_log_required" in by_type

    def test_includes_unsatisfied_by_source(self, graph_with_unsatisfied_obligations: CapabilityGraph) -> None:
        """
        Test: Summary chứa breakdown unsatisfied theo source.
        
        Case: Graph có unsatisfied obligations từ delete_customer
        Expected: unsatisfied_by_source chứa delete_customer
        """
        summary = get_obligation_coverage_summary(graph_with_unsatisfied_obligations)
        
        assert "unsatisfied_by_source" in summary
        by_source = summary["unsatisfied_by_source"]
        
        # Kiểm tra có source
        assert "capability:delete_customer" in by_source


# ============================================================================
# Integration Tests
# ============================================================================

class TestObligationCoverageIntegration:
    """Integration tests cho obligation coverage check."""

    def test_full_validation_pipeline(
        self,
        graph_with_unsatisfied_obligations: CapabilityGraph,
    ) -> None:
        """
        Test: Full pipeline validation.
        
        Case: Graph có unsatisfied obligations
        Expected: 
        - get_unsatisfied_obligations trả về danh sách đúng
        - check_obligation_coverage tạo report với errors
        - get_obligation_coverage_summary trả về stats đúng
        """
        # Step 1: Get unsatisfied obligations
        unsatisfied = get_unsatisfied_obligations(graph_with_unsatisfied_obligations)
        assert len(unsatisfied) == 2
        
        # Step 2: Check coverage
        report = check_obligation_coverage(
            graph_with_unsatisfied_obligations,
            "integration_test_graph",
        )
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) == 2
        
        # Step 3: Get summary
        summary = get_obligation_coverage_summary(graph_with_unsatisfied_obligations)
        assert summary["coverage_percentage"] < 100.0
        
        # Step 4: Verify consistency
        assert len(unsatisfied) == summary["unsatisfied_count"]
        assert len(unsatisfied) == report.summary["unsatisfied_obligations"]

    def test_satisfied_pipeline(
        self,
        sample_capability_graph: CapabilityGraph,
    ) -> None:
        """
        Test: Full pipeline khi tất cả satisfied.
        
        Case: Graph với tất cả obligations satisfied
        Expected: 
        - get_unsatisfied_obligations trả về empty list
        - check_obligation_coverage trả về PASS
        - get_obligation_coverage_summary trả về 100% coverage
        """
        # Step 1: Get unsatisfied obligations
        unsatisfied = get_unsatisfied_obligations(sample_capability_graph)
        assert len(unsatisfied) == 0
        
        # Step 2: Check coverage
        report = check_obligation_coverage(
            sample_capability_graph,
            "integration_test_graph",
        )
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        
        # Step 3: Get summary
        summary = get_obligation_coverage_summary(sample_capability_graph)
        assert summary["coverage_percentage"] == 100.0


# ============================================================================
# Edge Cases
# ============================================================================

class TestObligationCoverageEdgeCases:
    """Tests cho edge cases."""

    def test_obligation_without_source(self) -> None:
        """
        Test: Obligation không có source.
        
        Case: Obligation với source rỗng
        Expected: Vẫn được tính vào check, error message xử lý đúng
        """
        graph = CapabilityGraph(
            obligations=[
                Obligation(
                    id="orphan_obligation",
                    type="permission_check_required",
                    description="Orphan obligation",
                    source="",
                    satisfied=False,
                ),
            ],
        )
        
        report = check_obligation_coverage(graph, "test_graph")
        
        assert report.status == ValidationStatus.FAIL.value
        # Error vẫn được tạo
        assert len(report.errors) == 1

    def test_mixed_satisfied_status(self) -> None:
        """
        Test: Mixed satisfied/unsatisfied obligations cùng type.
        
        Case: Có obligations cùng type, một số satisfied, một số không
        Expected: Chỉ unsatisfied được báo lỗi
        """
        graph = CapabilityGraph(
            obligations=[
                Obligation(
                    id="perm_001",
                    type="permission_check_required",
                    description="Permission check 1",
                    source="capability:cmd1",
                    satisfied=True,
                ),
                Obligation(
                    id="perm_002",
                    type="permission_check_required",
                    description="Permission check 2",
                    source="capability:cmd2",
                    satisfied=False,
                ),
                Obligation(
                    id="perm_003",
                    type="permission_check_required",
                    description="Permission check 3",
                    source="capability:cmd3",
                    satisfied=True,
                ),
            ],
        )
        
        report = check_obligation_coverage(graph, "test_graph")
        
        # Chỉ có 1 error (cho perm_002)
        assert len(report.errors) == 1
        assert "perm_002" in report.errors[0].message

    def test_obligation_with_evidence(self, sample_capability_graph: CapabilityGraph) -> None:
        """
        Test: Obligations với satisfaction evidence.
        
        Case: Obligations satisfied có evidence
        Expected: Summary hoặc report có thể truy cập evidence
        """
        # Tất cả obligations trong sample đã có evidence
        summary = get_obligation_coverage_summary(sample_capability_graph)
        
        # Kiểm tra summary có thông tin đầy đủ
        assert summary["satisfied_count"] == 2