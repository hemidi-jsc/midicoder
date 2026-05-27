# coding: utf-8
"""
Tests cho CP52 — Invariant Enforcement System models.

Phạm vi: import tất cả classes từ __init__.py, test enum values,
basic model creation, to_dict / from_dict round-trip.
"""

import pytest
from midicoder.emitters.core.cp52_invariant.models import (
    InvariantCategory,
    EnforcementMode,
    InvariantSeverity,
    InvariantDefinition,
    InvariantResult,
    InvariantReport,
    CompileTimeCheckSpec,
    RuntimeGuardSpec,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestInvariantCategory:
    def test_enum_values(self):
        assert InvariantCategory.BUSINESS.value == "business"
        assert InvariantCategory.COMPLIANCE.value == "compliance"
        assert InvariantCategory.FAILURE_MODE.value == "failure_mode"


class TestEnforcementMode:
    def test_enum_values(self):
        assert EnforcementMode.COMPILE_TIME.value == "compile-time"
        assert EnforcementMode.RUNTIME.value == "runtime"
        assert EnforcementMode.BOTH.value == "both"


class TestInvariantSeverity:
    def test_enum_values(self):
        assert InvariantSeverity.ERROR.value == "error"
        assert InvariantSeverity.WARNING.value == "warning"


# ---------------------------------------------------------------------------
# InvariantDefinition
# ---------------------------------------------------------------------------

class TestInvariantDefinition:
    def _make(self, **overrides) -> InvariantDefinition:
        defaults = dict(
            id="INV-001",
            name="Test Invariant",
            description="A test invariant",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.COMPILE_TIME,
        )
        defaults.update(overrides)
        return InvariantDefinition(**defaults)

    def test_creation(self):
        inv = self._make()
        assert inv.id == "INV-001"
        assert inv.tags == []

    def test_is_compile_time(self):
        assert self._make(enforcement=EnforcementMode.COMPILE_TIME).is_compile_time
        assert self._make(enforcement=EnforcementMode.BOTH).is_compile_time
        assert not self._make(enforcement=EnforcementMode.RUNTIME).is_compile_time

    def test_is_runtime(self):
        assert self._make(enforcement=EnforcementMode.RUNTIME).is_runtime
        assert self._make(enforcement=EnforcementMode.BOTH).is_runtime
        assert not self._make(enforcement=EnforcementMode.COMPILE_TIME).is_runtime

    def test_is_critical(self):
        assert self._make(severity="error").is_critical
        assert not self._make(severity="warning").is_critical

    def test_hash_and_eq(self):
        a = self._make(id="SAME")
        b = self._make(id="SAME", name="Different")
        assert a == b
        assert hash(a) == hash(b)
        c = self._make(id="DIFF")
        assert a != c

    def test_to_dict(self):
        inv = self._make(violation_code="MDC-INV-001", overlay="RX01", tags=["t1"])
        d = inv.to_dict()
        assert d["category"] == "business"
        assert d["violation_code"] == "MDC-INV-001"
        assert d["tags"] == ["t1"]

    def test_from_dict(self):
        data = {
            "id": "INV-002",
            "name": "From Dict",
            "description": "desc",
            "category": "compliance",
            "enforcement": "both",
            "tags": ["a", "b"],
        }
        inv = InvariantDefinition.from_dict(data)
        assert inv.id == "INV-002"
        assert inv.category == InvariantCategory.COMPLIANCE
        assert inv.enforcement == EnforcementMode.BOTH
        assert inv.tags == ["a", "b"]

    def test_roundtrip(self):
        original = self._make(
            overlay="RX02",
            domain="DP01",
            validator_fn="check_fn",
            runtime_guard="GuardClass",
        )
        restored = InvariantDefinition.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.overlay == "RX02"
        assert restored.domain == "DP01"


# ---------------------------------------------------------------------------
# InvariantResult
# ---------------------------------------------------------------------------

class TestInvariantResult:
    def _make(self, **overrides) -> InvariantResult:
        defaults = dict(
            invariant_id="INV-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        )
        defaults.update(overrides)
        return InvariantResult(**defaults)

    def test_creation(self):
        r = self._make()
        assert r.is_violation is False

    def test_is_violation(self):
        assert self._make(passed=False).is_violation
        assert not self._make(passed=True).is_violation

    def test_to_dict(self):
        r = self._make(passed=False, violation_code="MDC-001", message="fail")
        d = r.to_dict()
        assert d["passed"] is False
        assert d["violation_code"] == "MDC-001"

    def test_roundtrip(self):
        original = self._make(passed=False, severity="warning", context={"key": "val"})
        restored = InvariantResult.__new__(InvariantResult)
        # to_dict / manual reconstruction
        d = original.to_dict()
        assert d["severity"] == "warning"
        assert d["context"]["key"] == "val"


# ---------------------------------------------------------------------------
# InvariantReport
# ---------------------------------------------------------------------------

class TestInvariantReport:
    def test_creation(self):
        report = InvariantReport(blueprint_id="BP001")
        assert report.timestamp  # auto-generated
        assert report.is_passing  # no failures

    def test_add_result_pass(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="INV-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        ))
        assert report.total_invariants == 1
        assert report.passed == 1

    def test_add_result_fail(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="INV-002",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=False,
            severity="error",
        ))
        assert report.failed == 1
        assert report.is_passing is False

    def test_add_result_warning(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="INV-003",
            category=InvariantCategory.FAILURE_MODE,
            enforcement_mode=EnforcementMode.BOTH,
            passed=False,
            severity="warning",
        ))
        assert report.warnings == 1
        assert report.is_passing  # warnings don't fail

    def test_get_violations(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="A",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="B",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=False,
            severity="error",
        ))
        violations = report.get_violations()
        assert len(violations) == 1
        assert violations[0].invariant_id == "B"

    def test_get_critical_violations(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="C",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=False,
            severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="D",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=False,
            severity="warning",
        ))
        critical = report.get_critical_violations()
        assert len(critical) == 1

    def test_get_by_category(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="BUS-1",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        ))
        report.add_result(InvariantResult(
            invariant_id="COMP-1",
            category=InvariantCategory.COMPLIANCE,
            enforcement_mode=EnforcementMode.RUNTIME,
            passed=True,
            severity="error",
        ))
        business = report.get_by_category(InvariantCategory.BUSINESS)
        assert len(business) == 1
        assert business[0].invariant_id == "BUS-1"

    def test_generate_summary(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="INV-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        ))
        summary = report.generate_summary()
        assert summary["total_invariants"] == 1
        assert summary["passed"] == 1
        assert summary["is_passing"] is True

    def test_to_dict(self):
        report = InvariantReport(blueprint_id="BP001")
        report.add_result(InvariantResult(
            invariant_id="INV-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.COMPILE_TIME,
            passed=True,
            severity="error",
        ))
        d = report.to_dict()
        assert d["blueprint_id"] == "BP001"
        assert len(d["results"]) == 1
        assert "summary" in d

    def test_from_dict(self):
        data = {
            "blueprint_id": "BP002",
            "results": [
                {
                    "invariant_id": "INV-001",
                    "category": "business",
                    "enforcement_mode": "compile-time",
                    "passed": True,
                    "severity": "error",
                }
            ],
        }
        report = InvariantReport.from_dict(data)
        assert report.blueprint_id == "BP002"
        assert len(report.results) == 1

    def test_roundtrip(self):
        original = InvariantReport(blueprint_id="BP003")
        original.add_result(InvariantResult(
            invariant_id="INV-001",
            category=InvariantCategory.BUSINESS,
            enforcement_mode=EnforcementMode.BOTH,
            passed=False,
            severity="warning",
            violation_code="MDC-INV-001",
        ))
        d = original.to_dict()
        restored = InvariantReport.from_dict(d)
        assert restored.blueprint_id == "BP003"
        assert len(restored.results) == 1


# ---------------------------------------------------------------------------
# CompileTimeCheckSpec
# ---------------------------------------------------------------------------

class TestCompileTimeCheckSpec:
    def test_creation(self):
        spec = CompileTimeCheckSpec(
            invariant_id="INV-001",
            check_function="check_crud",
        )
        assert spec.target_artifact == "blueprint"
        assert spec.params == {}

    def test_creation_with_params(self):
        spec = CompileTimeCheckSpec(
            invariant_id="INV-002",
            check_function="check_gdpr",
            target_artifact="graph",
            params={"field": "email"},
        )
        assert spec.params == {"field": "email"}


# ---------------------------------------------------------------------------
# RuntimeGuardSpec
# ---------------------------------------------------------------------------

class TestRuntimeGuardSpec:
    def test_creation(self):
        spec = RuntimeGuardSpec(
            invariant_id="INV-001",
            guard_class="CRUDGuard",
        )
        assert spec.target_component == "handler"
        assert spec.stack == "fastapi"

    def test_to_dict(self):
        spec = RuntimeGuardSpec(
            invariant_id="INV-001",
            guard_class="Guard",
            target_component="service",
            error_code="MDC-ERR-001",
            stack="nestjs",
        )
        d = spec.to_dict()
        assert d["guard_class"] == "Guard"
        assert d["stack"] == "nestjs"

    def test_roundtrip(self):
        spec = RuntimeGuardSpec(
            invariant_id="INV-001",
            guard_class="MyGuard",
            guard_params={"limit": 10},
        )
        d = spec.to_dict()
        assert d["guard_params"]["limit"] == 10
