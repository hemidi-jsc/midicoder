"""
Tests cho Invariant Enforcement System models.

Kiểm tra:
- InvariantCategory enum
- EnforcementMode enum
- InvariantDefinition dataclass (CRUD, serialization, properties)
- InvariantResult dataclass (properties, serialization)
- InvariantReport dataclass (counters, filtering, summary, serialization)
- CompileTimeCheckSpec, RuntimeGuardSpec

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.invariants.models import (
    InvariantCategory,
    EnforcementMode,
    InvariantSeverity,
    InvariantDefinition,
    InvariantResult,
    InvariantReport,
    CompileTimeCheckSpec,
    RuntimeGuardSpec,
)


class TestInvariantCategory:
    """Tests cho InvariantCategory enum."""

    def test_business_category_value(self) -> None:
        """Kiểm tra BUSINESS có giá trị đúng."""
        assert InvariantCategory.BUSINESS.value == "business"

    def test_compliance_category_value(self) -> None:
        """Kiểm tra COMPLIANCE có giá trị đúng."""
        assert InvariantCategory.COMPLIANCE.value == "compliance"

    def test_failure_mode_category_value(self) -> None:
        """Kiểm tra FAILURE_MODE có giá trị đúng."""
        assert InvariantCategory.FAILURE_MODE.value == "failure_mode"

    def test_all_categories_present(self) -> None:
        """Kiểm tra đủ 3 categories."""
        assert len(InvariantCategory) == 3

    def test_category_from_string(self) -> None:
        """Kiểm tra tạo category từ string."""
        assert InvariantCategory("business") == InvariantCategory.BUSINESS


class TestEnforcementMode:
    """Tests cho EnforcementMode enum."""

    def test_compile_time_value(self) -> None:
        """Kiểm tra COMPILE_TIME có giá trị đúng."""
        assert EnforcementMode.COMPILE_TIME.value == "compile-time"

    def test_runtime_value(self) -> None:
        """Kiểm tra RUNTIME có giá trị đúng."""
        assert EnforcementMode.RUNTIME.value == "runtime"

    def test_both_value(self) -> None:
        """Kiểm tra BOTH có giá trị đúng."""
        assert EnforcementMode.BOTH.value == "both"

    def test_all_modes_present(self) -> None:
        """Kiểm tra đủ 3 modes."""
        assert len(EnforcementMode) == 3


class TestInvariantDefinition:
    """Tests cho InvariantDefinition dataclass."""

    def _create_definition(self, **kwargs) -> InvariantDefinition:
        """Helper tạo InvariantDefinition với defaults."""
        defaults = {
            "id": "INV-TEST-001",
            "name": "Test Invariant",
            "description": "Test invariant description",
            "category": InvariantCategory.BUSINESS,
            "enforcement": EnforcementMode.BOTH,
            "severity": "error",
            "violation_code": "MDC-INV-001",
            "overlay": None,
            "domain": None,
            "validator_fn": "test_validator",
            "runtime_guard": "TestGuard",
            "check_fn": None,
            "tags": ["test"],
        }
        defaults.update(kwargs)
        return InvariantDefinition(**defaults)

    def test_create_basic_definition(self) -> None:
        """Kiểm tra tạo InvariantDefinition cơ bản."""
        inv = self._create_definition()
        assert inv.id == "INV-TEST-001"
        assert inv.name == "Test Invariant"
        assert inv.category == InvariantCategory.BUSINESS

    def test_is_compile_time_both_mode(self) -> None:
        """Kiểm tra BOTH mode có is_compile_time=True."""
        inv = self._create_definition(enforcement=EnforcementMode.BOTH)
        assert inv.is_compile_time is True

    def test_is_compile_time_runtime_mode(self) -> None:
        """Kiểm tra RUNTIME mode có is_compile_time=False."""
        inv = self._create_definition(enforcement=EnforcementMode.RUNTIME)
        assert inv.is_compile_time is False

    def test_is_runtime_both_mode(self) -> None:
        """Kiểm tra BOTH mode có is_runtime=True."""
        inv = self._create_definition(enforcement=EnforcementMode.BOTH)
        assert inv.is_runtime is True

    def test_is_runtime_compile_mode(self) -> None:
        """Kiểm tra COMPILE_TIME mode có is_runtime=False."""
        inv = self._create_definition(enforcement=EnforcementMode.COMPILE_TIME)
        assert inv.is_runtime is False

    def test_is_critical_error_severity(self) -> None:
        """Kiểm tra severity=error có is_critical=True."""
        inv = self._create_definition(severity="error")
        assert inv.is_critical is True

    def test_is_critical_warning_severity(self) -> None:
        """Kiểm tra severity=warning có is_critical=False."""
        inv = self._create_definition(severity="warning")
        assert inv.is_critical is False

    def test_equality_same_id(self) -> None:
        """Kiểm tra 2 definitions cùng id bằng nhau."""
        inv1 = self._create_definition(id="INV-001")
        inv2 = self._create_definition(id="INV-001", name="Different Name")
        assert inv1 == inv2

    def test_equality_different_id(self) -> None:
        """Kiểm tra 2 definitions khác id không bằng nhau."""
        inv1 = self._create_definition(id="INV-001")
        inv2 = self._create_definition(id="INV-002")
        assert inv1 != inv2

    def test_hash_consistent(self) -> None:
        """Kiểm tra hash consistent với cùng id."""
        inv1 = self._create_definition(id="INV-001")
        inv2 = self._create_definition(id="INV-001", name="Different")
        assert hash(inv1) == hash(inv2)

    def test_can_use_in_set(self) -> None:
        """Kiểm tra có thể dùng InvariantDefinition trong set."""
        inv1 = self._create_definition(id="INV-001")
        inv2 = self._create_definition(id="INV-001")
        inv3 = self._create_definition(id="INV-002")
        inv_set = {inv1, inv2, inv3}
        assert len(inv_set) == 2

    def test_to_dict(self) -> None:
        """Kiểm tra to_dict trả về đúng structure."""
        inv = self._create_definition()
        d = inv.to_dict()
        assert d["id"] == "INV-TEST-001"
        assert d["category"] == "business"
        assert d["enforcement"] == "both"

    def test_from_dict(self) -> None:
        """Kiểm tra from_dict tạo đúng object."""
        data = {
            "id": "INV-FROM-DICT",
            "name": "From Dict",
            "description": "Test",
            "category": "compliance",
            "enforcement": "runtime",
            "severity": "warning",
            "violation_code": "MDC-INV-010",
            "overlay": "RX01",
            "domain": "DP01",
            "validator_fn": "dict_validator",
            "runtime_guard": "DictGuard",
            "tags": ["dict", "test"],
        }
        inv = InvariantDefinition.from_dict(data)
        assert inv.id == "INV-FROM-DICT"
        assert inv.category == InvariantCategory.COMPLIANCE
        assert inv.enforcement == EnforcementMode.RUNTIME

    def test_roundtrip_serialization(self) -> None:
        """Kiểm tra to_dict -> from_dict giữ nguyên data."""
        original = self._create_definition()
        restored = InvariantDefinition.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.category == original.category

    def test_default_tags_empty(self) -> None:
        """Kiểm tra default tags là list rỗng."""
        inv = InvariantDefinition(
            id="INV-001", name="Test", description="Test",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.COMPILE_TIME,
        )
        assert inv.tags == []


class TestInvariantResult:
    """Tests cho InvariantResult dataclass."""

    def test_passed_result(self) -> None:
        """Kiểm tra result pass."""
        result = InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True, severity="error",
        )
        assert result.passed is True
        assert result.is_violation is False

    def test_failed_result(self) -> None:
        """Kiểm tra result fail."""
        result = InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=False, severity="error",
        )
        assert result.passed is False
        assert result.is_violation is True

    def test_to_dict(self) -> None:
        """Kiểm tra to_dict trả về đúng structure."""
        result = InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=True, severity="error", context={"key": "value"},
        )
        d = result.to_dict()
        assert d["invariant_id"] == "INV-001"
        assert d["category"] == "compliance"


class TestInvariantReport:
    """Tests cho InvariantReport dataclass."""

    def test_empty_report_passing(self) -> None:
        """Kiểm tra report rỗng là passing."""
        report = InvariantReport(blueprint_id="BP-001")
        assert report.is_passing is True

    def test_timestamp_auto_generated(self) -> None:
        """Kiểm tra timestamp tự động sinh."""
        report = InvariantReport(blueprint_id="BP-001")
        # datetime.now(timezone.utc).isoformat() produces format with +00:00
        assert report.timestamp
        assert "+" in report.timestamp or "Z" in report.timestamp

    def test_add_passing_result(self) -> None:
        """Kiểm tra add result pass tăng passed counter."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True, severity="error",
        ))
        assert report.passed == 1
        assert report.failed == 0

    def test_add_failing_result(self) -> None:
        """Kiểm tra add result fail tăng failed counter."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=False, severity="error",
        ))
        assert report.failed == 1
        assert report.is_passing is False

    def test_add_warning_result(self) -> None:
        """Kiểm tra add result warning tăng warning counter."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=False, severity="warning",
        ))
        assert report.warnings == 1
        assert report.is_passing is True

    def test_get_violations(self) -> None:
        """Kiểm tra get_violations trả về đúng results."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-002", category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME, passed=False, severity="error",
        ))
        violations = report.get_violations()
        assert len(violations) == 1

    def test_get_by_category(self) -> None:
        """Kiểm tra get_by_category lọc đúng."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-BIZ", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-COMP", category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME, passed=True, severity="error",
        ))
        assert len(report.get_by_category(InvariantCategory.BUSINESS)) == 1
        assert len(report.get_by_category(InvariantCategory.COMPLIANCE)) == 1

    def test_generate_summary(self) -> None:
        """Kiểm tra generate_summary tạo đúng statistics."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-002", category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME, passed=False, severity="error",
            violation_code="MDC-INV-001",
        ))
        summary = report.generate_summary()
        assert summary["total_invariants"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1

    def test_to_dict_and_from_dict(self) -> None:
        """Kiểm tra serialization roundtrip."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        d = report.to_dict()
        restored = InvariantReport.from_dict(d)
        assert restored.blueprint_id == "BP-001"
        assert restored.total_invariants == 1

    def test_mixed_results_counters(self) -> None:
        """Kiểm tra counters với mixed results."""
        report = InvariantReport(blueprint_id="BP-001")
        report.add_result(InvariantResult(
            invariant_id="INV-001", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-002", category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME, passed=True, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-003", category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME, passed=False, severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="INV-004", category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.BOTH, passed=False, severity="warning",
        ))
        assert report.total_invariants == 4
        assert report.passed == 2
        assert report.failed == 1
        assert report.warnings == 1


class TestSpecs:
    """Tests cho CompileTimeCheckSpec và RuntimeGuardSpec."""

    def test_compile_time_check_spec(self) -> None:
        """Kiểm tra CompileTimeCheckSpec."""
        spec = CompileTimeCheckSpec(
            invariant_id="INV-001", check_function="check_entity_refs",
            target_artifact="blueprint", params={"entity_ids": ["E1"]},
        )
        assert spec.invariant_id == "INV-001"

    def test_runtime_guard_spec_to_dict(self) -> None:
        """Kiểm tra RuntimeGuardSpec to_dict."""
        spec = RuntimeGuardSpec(
            invariant_id="INV-001", guard_class="TenantGuard", stack="nestjs",
        )
        d = spec.to_dict()
        assert d["guard_class"] == "TenantGuard"