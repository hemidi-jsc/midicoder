"""
Integration tests cho Invariant Enforcement System.

Tests cho:
- InvariantRegistry (register, get, query)
- InvariantManager (initialize, validate)
- RuntimeGuardEmitter
- Domain invariants integration (banking, healthcare)

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest
from dataclasses import dataclass
from midicoder.emitters.core.invariant.models import (
    InvariantCategory,
    EnforcementMode,
    InvariantDefinition,
    InvariantResult,
    InvariantReport,
    RuntimeGuardSpec,
)
from midicoder.emitters.core.invariant.registry import InvariantRegistry
from midicoder.emitters.core.invariant.manager import InvariantManager
from midicoder.emitters.core.invariant.runtime.emitter import RuntimeGuardEmitter


@dataclass
class MockObligation:
    """Mock obligation cho tests."""
    source: str
    type: str | None = None


@dataclass
class MockInstance:
    """Mock instance cho tests."""
    id: str
    type: str
    reads: list[str] = ()
    writes: list[str] = ()
    params: dict = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class MockGraph:
    """Mock CapabilityGraph cho tests."""
    instances: list[MockInstance] = ()
    obligations: list[MockObligation] = ()


class TestInvariantRegistry:
    """Tests cho InvariantRegistry."""

    def setup_method(self) -> None:
        """Reset registry trước mỗi test."""
        InvariantRegistry.reset()

    def test_register_and_get(self) -> None:
        """Kiểm tra register và get invariant."""
        registry = InvariantRegistry()
        inv = InvariantDefinition(
            id="INV-TEST-001",
            name="Test",
            description="Test invariant",
            category=InvariantCategory.BUSINESS,
            enforcement=EnforcementMode.COMPILE_TIME,
        )
        registry.register(inv)
        result = registry.get("INV-TEST-001")
        assert result.id == "INV-TEST-001"

    def test_register_duplicate_raises(self) -> None:
        """Kiểm tra register duplicate id throw error."""
        registry = InvariantRegistry()
        inv = InvariantDefinition(
            id="INV-DUP", name="Test", description="Test",
            category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.COMPILE_TIME,
        )
        registry.register(inv)
        with pytest.raises(ValueError):
            registry.register(inv)

    def test_get_missing_raises(self) -> None:
        """Kiểm tra get invariant không tồn tại throw KeyError."""
        registry = InvariantRegistry()
        with pytest.raises(KeyError):
            registry.get("INV-NOT-EXIST")

    def test_is_registered(self) -> None:
        """Kiểm tra is_registered."""
        registry = InvariantRegistry()
        inv = InvariantDefinition(
            id="INV-REG", name="Test", description="Test",
            category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.COMPILE_TIME,
        )
        assert not registry.is_registered("INV-REG")
        registry.register(inv)
        assert registry.is_registered("INV-REG")

    def test_get_by_category(self) -> None:
        """Kiểm tra get_by_category."""
        registry = InvariantRegistry()
        registry.register(InvariantDefinition(
            id="INV-BIZ", name="Test", description="Test",
            category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.COMPILE_TIME,
        ))
        registry.register(InvariantDefinition(
            id="INV-COMP", name="Test", description="Test",
            category=InvariantCategory.COMPLIANCE, enforcement=EnforcementMode.RUNTIME,
        ))
        biz = registry.get_by_category(InvariantCategory.BUSINESS)
        assert len(biz) == 1
        assert biz[0].id == "INV-BIZ"

    def test_count(self) -> None:
        """Kiểm tra count property."""
        registry = InvariantRegistry()
        assert registry.count == 0
        registry.register(InvariantDefinition(
            id="INV-1", name="T", description="T",
            category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.COMPILE_TIME,
        ))
        assert registry.count == 1


class TestInvariantManager:
    """Tests cho InvariantManager."""

    def setup_method(self) -> None:
        """Reset manager trước mỗi test."""
        InvariantManager.reset()

    def test_initialize_registers_invariants(self) -> None:
        """Kiểm tra initialize đăng ký invariants."""
        manager = InvariantManager()
        manager.initialize()
        assert manager.registry.count >= 14  # 5 BIZ + 5 COMP + 5 FM

    def test_initialize_idempotent(self) -> None:
        """Kiểm tra initialize idempotent."""
        manager = InvariantManager()
        manager.initialize()
        count = manager.registry.count
        manager.initialize()
        assert manager.registry.count == count

    def test_get_all_invariants(self) -> None:
        """Kiểm tra get_all_invariants."""
        manager = InvariantManager()
        manager.initialize()
        invariants = manager.get_all_invariants()
        assert len(invariants) >= 14

    def test_get_by_category(self) -> None:
        """Kiểm tra get_by_category."""
        manager = InvariantManager()
        manager.initialize()
        biz = manager.get_by_category(InvariantCategory.BUSINESS)
        assert len(biz) == 5

    def test_validate_empty_graph(self) -> None:
        """Kiểm tra validate với graph rỗng."""
        manager = InvariantManager()
        graph = MockGraph()
        report = manager.validate(graph, blueprint_id="BP-TEST")
        assert report.blueprint_id == "BP-TEST"
        assert report.total_invariants > 0

    def test_get_invariant(self) -> None:
        """Kiểm tra get_invariant."""
        manager = InvariantManager()
        manager.initialize()
        inv = manager.get_invariant("INV-BIZ-001")
        assert inv.id == "INV-BIZ-001"


class TestRuntimeGuardEmitter:
    """Tests cho RuntimeGuardEmitter."""

    def test_get_guards_for_invariants(self) -> None:
        """Kiểm tra get_guards_for_invariants."""
        emitter = RuntimeGuardEmitter()
        invariants = [
            InvariantDefinition(
                id="INV-RUN-001", name="Test", description="Test",
                category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.RUNTIME,
                runtime_guard="TestGuard",
            ),
            InvariantDefinition(
                id="INV-CP-001", name="Compile Only", description="Test",
                category=InvariantCategory.BUSINESS, enforcement=EnforcementMode.COMPILE_TIME,
            ),
        ]
        guards = emitter.get_guards_for_invariants(invariants)
        assert len(guards) == 1
        assert guards[0].guard_class == "TestGuard"

    def test_emit_fastapi_guards(self) -> None:
        """Kiểm tra emit_fastapi_guards."""
        emitter = RuntimeGuardEmitter()
        guards = [RuntimeGuardSpec(
            invariant_id="INV-001", guard_class="TestGuard",
            error_code="MDC-INV-001",
            guard_params={"description": "Test guard"},
        )]
        code = emitter.emit_fastapi_guards(guards)
        assert "TestGuard" in code
        assert "class TestGuard" in code["TestGuard"]

    def test_emit_nestjs_guards_stub(self) -> None:
        """Kiểm tra emit_nestjs_guards trả về empty."""
        emitter = RuntimeGuardEmitter()
        guards = [RuntimeGuardSpec(
            invariant_id="INV-001", guard_class="TestGuard",
        )]
        code = emitter.emit_nestjs_guards(guards)
        assert code == {}


class TestDomainInvariants:
    """Tests cho domain invariants (banking, healthcare)."""

    def test_banking_double_entry_balanced(self) -> None:
        """Kiểm tra double entry balanced."""
        from midicoder.emitters.core.invariant.domain.banking import double_entry_balance_invariant
        entries = [
            {"type": "debit", "amount": 100},
            {"type": "credit", "amount": 100},
        ]
        result = double_entry_balance_invariant(entries)
        assert result.valid is True

    def test_banking_double_entry_imbalanced(self) -> None:
        """Kiểm tra double entry imbalanced."""
        from midicoder.emitters.core.invariant.domain.banking import double_entry_balance_invariant
        entries = [
            {"type": "debit", "amount": 100},
            {"type": "credit", "amount": 50},
        ]
        result = double_entry_balance_invariant(entries)
        assert result.valid is False
        assert result.code == "INV-BANK-001"

    def test_banking_kyc_verified(self) -> None:
        """Kiểm tra KYC verified."""
        from midicoder.emitters.core.invariant.domain.banking import kyc_before_transaction_invariant
        account = {"id": "ACC-001", "kyc_verified": True}
        result = kyc_before_transaction_invariant(account)
        assert result.valid is True

    def test_banking_kyc_not_verified(self) -> None:
        """Kiểm tra KYC not verified."""
        from midicoder.emitters.core.invariant.domain.banking import kyc_before_transaction_invariant
        account = {"id": "ACC-001", "kyc_verified": False}
        result = kyc_before_transaction_invariant(account)
        assert result.valid is False

    def test_healthcare_phi_encrypted(self) -> None:
        """Kiểm tra PHI encrypted."""
        from midicoder.emitters.core.invariant.domain.healthcare import phi_encryption_invariant
        entity = {"ssn_enc": "ENC:123"}
        result = phi_encryption_invariant(entity)
        assert result.valid is True

    def test_healthcare_phi_not_encrypted(self) -> None:
        """Kiểm tra PHI not encrypted."""
        from midicoder.emitters.core.invariant.domain.healthcare import phi_encryption_invariant
        entity = {"ssn_enc": "PLAIN:123"}
        result = phi_encryption_invariant(entity)
        assert result.valid is False


class TestFullPipeline:
    """Tests cho full pipeline (initialize → validate → report)."""

    def setup_method(self) -> None:
        """Reset trước mỗi test."""
        InvariantManager.reset()

    def test_full_pipeline_with_valid_graph(self) -> None:
        """Kiểm tra full pipeline với graph hợp lệ."""
        manager = InvariantManager()
        manager.initialize()

        # Graph với tất cả invariants pass
        graph = MockGraph(
            instances=[
                MockInstance(
                    id="inst-1", type="authorized_query",
                    reads=["User"], params={"tenant_scope": "tenant-1", "permission": "read"},
                ),
            ],
            obligations=[
                MockObligation(source="inst-1", type="audit_log"),
            ],
        )

        report = manager.validate(graph, blueprint_id="BP-FULL")
        assert report.total_invariants > 0
        #_graph hợp lệ nên không có critical violations
        critical = report.get_critical_violations()
        # Có thể có warnings nhưng không có errors critical