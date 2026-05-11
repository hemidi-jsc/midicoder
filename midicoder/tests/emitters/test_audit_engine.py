# coding: utf-8
"""
Test cases cho CP14 Audit Trail & Compliance Engine.

Kiểm tra:
- AuditLogger: log() (dual write), query(), archive(), purge(), verify_integrity()
- AuditRuleEngine: should_audit(), get_rule()
- ComplianceEnforcer: validate(), get_active_controls()
- ValidationResult: dataclass fields

Mục tiêu: 100% coverage cho audit_engine.py
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from midicoder.emitters.core.audit.models import (
    AuditActionType,
    AuditComplianceCollection,
    AuditLevel,
    AuditRule,
    AuditTrail,
    ComplianceControl,
    ControlType,
    EnforcementLevel,
    StandardType,
)
from midicoder.emitters.core.audit.audit_engine import (
    AuditLogger,
    AuditRuleEngine,
    ComplianceEnforcer,
    ValidationResult,
)


# ===========================================================================
# Test ValidationResult
# ===========================================================================


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_create_passed_result(self):
        """Kiểm tra tạo validation result passed."""
        result = ValidationResult(passed=True, control_id="c1", message="Đạt")
        assert result.passed is True
        assert result.control_id == "c1"
        assert result.message == "Đạt"

    def test_create_failed_result(self):
        """Kiểm tra tạo validation result failed."""
        result = ValidationResult(passed=False, control_id="c2", message="Không đạt")
        assert result.passed is False
        assert result.control_id == "c2"
        assert result.message == "Không đạt"

    def test_default_message(self):
        """Kiểm tra default message là string rỗng."""
        result = ValidationResult(passed=True, control_id="c1")
        assert result.message == ""


# ===========================================================================
# Test AuditLogger
# ===========================================================================


class TestAuditLogger:
    """Test AuditLogger với dual write (memory + file)."""

    def setup_method(self):
        """Setup logger với temp directory cho mỗi test."""
        self.log_dir = tempfile.mkdtemp()
        self.logger = AuditLogger(log_dir=self.log_dir)

    def test_log_entry_added_to_memory(self):
        """Kiểm tra log() thêm entry vào memory."""
        entry = AuditTrail(
            action=AuditActionType.CREATE,
            entity_type="Order",
            entity_id="order_001",
            actor_id="user_1",
            actor_type="user",
            tenant_id="tenant_1",
        )
        self.logger.log(entry)
        assert len(self.logger._entries) == 1
        assert self.logger._entries[0] is entry

    def test_log_entry_written_to_file(self):
        """Kiểm tra log() ghi entry vào file JSONL."""
        entry = AuditTrail(
            action=AuditActionType.CREATE,
            entity_type="Product",
            entity_id="prod_001",
            actor_id="user_1",
            actor_type="user",
            tenant_id="tenant_1",
        )
        self.logger.log(entry)

        # Kiểm tra file log theo ngày
        date_str = entry.timestamp.strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"audit_{date_str}.jsonl")
        assert os.path.exists(log_file)

        # Kiểm tra nội dung file
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        import json
        data = json.loads(lines[0])
        assert data["action"] == "CREATE"
        assert data["entity_type"] == "Product"
        assert data["entity_id"] == "prod_001"

    def test_log_creates_directory(self):
        """Kiểm tra log() tạo thư mục nếu chưa tồn tại."""
        new_dir = os.path.join(tempfile.gettempdir(), f"midicoder_audit_test_{datetime.now().timestamp()}")
        new_logger = AuditLogger(log_dir=new_dir)
        assert os.path.exists(new_dir)
        # Cleanup
        import shutil
        shutil.rmtree(new_dir, ignore_errors=True)

    def test_log_multiple_entries(self):
        """Kiểm tra log nhiều entries."""
        for i in range(5):
            self.logger.log(AuditTrail(
                action=AuditActionType.CREATE,
                entity_type="Order",
                entity_id=f"order_{i}",
                actor_id="user_1",
                actor_type="user",
                tenant_id="tenant_1",
            ))
        assert len(self.logger._entries) == 5

    def test_query_by_entity_type(self):
        """Kiểm tra query filter theo entity_type."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Product", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        results = self.logger.query({"entity_type": "Order"})
        assert len(results) == 1
        assert results[0].entity_type == "Order"

    def test_query_by_actor_id(self):
        """Kiểm tra query filter theo actor_id."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="user_1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="2",
            actor_id="user_2", actor_type="user", tenant_id="t1",
        ))
        results = self.logger.query({"actor_id": "user_1"})
        assert len(results) == 1
        assert results[0].actor_id == "user_1"

    def test_query_by_tenant_id(self):
        """Kiểm tra query filter theo tenant_id."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="tenant_1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="tenant_2",
        ))
        results = self.logger.query({"tenant_id": "tenant_1"})
        assert len(results) == 1
        assert results[0].tenant_id == "tenant_1"

    def test_query_by_action(self):
        """Kiểm tra query filter theo action."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.DELETE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        results = self.logger.query({"action": AuditActionType.CREATE})
        assert len(results) == 1
        assert results[0].action == AuditActionType.CREATE

    def test_query_multiple_filters(self):
        """Kiểm tra query với nhiều filters cùng lúc."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t2",
        ))
        results = self.logger.query({"entity_type": "Order", "tenant_id": "t1"})
        assert len(results) == 1
        assert results[0].tenant_id == "t1"

    def test_query_no_filters_returns_all(self):
        """Kiểm tra query không có filter trả về tất cả."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.DELETE, entity_type="Product", entity_id="2",
            actor_id="u2", actor_type="system", tenant_id="t2",
        ))
        results = self.logger.query({})
        assert len(results) == 2

    def test_query_unknown_filter_key_ignored(self):
        """Kiểm tra query với filter key không nhận biết bị bỏ qua."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        # Filter key không hợp lệ → trả về tất cả
        results = self.logger.query({"unknown_key": "value"})
        assert len(results) == 1

    def test_query_no_matches(self):
        """Kiểm tra query không có kết quả trả về list rỗng."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        results = self.logger.query({"entity_type": "NonExistent"})
        assert len(results) == 0

    def test_archive_marks_old_entries(self):
        """Kiểm tra archive() đánh dấu entries cũ."""
        # Tạo entry cũ (2 ngày trước)
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=2)
        old_entry = AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        )
        old_entry.timestamp = old_timestamp
        self.logger.log(old_entry)

        # Tạo entry mới
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))

        archived = self.logger.archive(older_than_days=1)
        assert archived == 1
        assert old_entry.metadata.get("_archived") is True

    def test_archive_returns_zero_when_no_old(self):
        """Kiểm tra archive() trả về 0 khi không có entry cũ."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        archived = self.logger.archive(older_than_days=9999)
        # Entry mới tạo nên không bị archive
        assert archived == 0

    def test_purge_removes_archived_entries(self):
        """Kiểm tra purge() xóa các entries đã archive."""
        # Tạo và archive entry cũ
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=30)
        old_entry = AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        )
        old_entry.timestamp = old_timestamp
        self.logger.log(old_entry)
        self.logger.archive(older_than_days=1)

        # Tạo entry mới không archive
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))

        purged = self.logger.purge(older_than_days=15)
        assert purged == 1
        assert len(self.logger._entries) == 1

    def test_purge_returns_zero_when_nothing_to_purge(self):
        """Kiểm tra purge() trả về 0 khi không có gì để purge."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        purged = self.logger.purge(older_than_days=9999)
        assert purged == 0

    def test_verify_integrity_all_valid(self):
        """Kiểm tra verify_integrity() trả về True khi tất cả entries hợp lệ."""
        self.logger.log(AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        self.logger.log(AuditTrail(
            action=AuditActionType.UPDATE, entity_type="Order", entity_id="2",
            actor_id="u1", actor_type="user", tenant_id="t1",
        ))
        assert self.logger.verify_integrity() is True

    def test_verify_integrity_empty(self):
        """Kiểm tra verify_integrity() trả về True khi không có entry."""
        assert self.logger.verify_integrity() is True

    def test_verify_integrity_with_range(self):
        """Kiểm tra verify_integrity() với start_id và end_id."""
        entries = []
        for i in range(5):
            entry = AuditTrail(
                action=AuditActionType.CREATE, entity_type="Order", entity_id=f"order_{i}",
                actor_id="u1", actor_type="user", tenant_id="t1",
            )
            self.logger.log(entry)
            entries.append(entry)

        # Verify range
        assert self.logger.verify_integrity(
            start_id=entries[1].id, end_id=entries[3].id
        ) is True

    def test_verify_integrity_tampered_entry(self):
        """Kiểm tra verify_integrity() phát hiện entry bị tamper."""
        entry = AuditTrail(
            action=AuditActionType.CREATE, entity_type="Order", entity_id="1",
            actor_id="u1", actor_type="user", tenant_id="t1",
        )
        self.logger.log(entry)
        # Tamper với data
        original_hash = entry.immutable_hash
        entry.entity_id = "tampered"
        # Hash vẫn là original nhưng data đã đổi → verify fail
        assert self.logger.verify_integrity() is False


# ===========================================================================
# Test AuditRuleEngine
# ===========================================================================


class TestAuditRuleEngine:
    """Test AuditRuleEngine."""

    def setup_method(self):
        """Setup rule engine với collection có rules."""
        collection = AuditComplianceCollection()
        collection.add_rule(AuditRule(
            id="order_audit",
            name="Audit Orders",
            entity_types=["Order"],
            actions=[AuditActionType.CREATE, AuditActionType.UPDATE],
            audit_level=AuditLevel.DETAILED,
        ))
        collection.add_rule(AuditRule(
            id="global_audit",
            name="Global Audit",
            # Không filter → match tất cả
        ))
        self.engine = AuditRuleEngine(collection)

    def test_should_audit_matches(self):
        """Kiểm tra should_audit() trả về True khi có rule matches."""
        assert self.engine.should_audit("Order", AuditActionType.CREATE) is True

    def test_should_audit_no_match(self):
        """Kiểm tra should_audit() trả về False khi không có rule match."""
        # Tạo engine chỉ có 1 rule filter strict
        collection = AuditComplianceCollection()
        collection.add_rule(AuditRule(
            id="strict",
            name="Strict",
            entity_types=["Product"],
            actions=[AuditActionType.DELETE],
        ))
        strict_engine = AuditRuleEngine(collection)
        assert strict_engine.should_audit("Order", AuditActionType.CREATE) is False

    def test_should_audit_disabled_rule(self):
        """Kiểm tra rule disabled không match."""
        collection = AuditComplianceCollection()
        collection.add_rule(AuditRule(
            id="disabled",
            name="Disabled",
            entity_types=["Order"],
            actions=[AuditActionType.CREATE],
            enabled=False,
        ))
        engine = AuditRuleEngine(collection)
        assert engine.should_audit("Order", AuditActionType.CREATE) is False

    def test_get_rule_returns_matching(self):
        """Kiểm tra get_rule() trả về rule matching."""
        rule = self.engine.get_rule("Order", AuditActionType.CREATE)
        assert rule is not None
        assert rule.id == "order_audit"

    def test_get_rule_returns_none(self):
        """Kiểm tra get_rule() trả về None khi không match."""
        collection = AuditComplianceCollection()
        collection.add_rule(AuditRule(
            id="strict",
            name="Strict",
            entity_types=["Product"],
            actions=[AuditActionType.DELETE],
        ))
        engine = AuditRuleEngine(collection)
        assert engine.get_rule("Order", AuditActionType.CREATE) is None

    def test_global_rule_matches_all(self):
        """Kiểm tra rule không có filter match tất cả."""
        # Global rule trong setup không có entity_types/actions filter
        assert self.engine.should_audit("AnyEntity", AuditActionType.DELETE) is True


# ===========================================================================
# Test ComplianceEnforcer
# ===========================================================================


class TestComplianceEnforcer:
    """Test ComplianceEnforcer."""

    def setup_method(self):
        """Setup enforcer với collection có controls."""
        collection = AuditComplianceCollection()
        collection.add_control(ComplianceControl(
            id="sox_immutable",
            name="SOX Immutable Ledger",
            standard=StandardType.SOX,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.BOTH,
            enabled=True,
        ))
        collection.add_control(ComplianceControl(
            id="disabled_control",
            name="Disabled Control",
            standard=StandardType.GDPR,
            control_type=ControlType.DETECTIVE,
            enforcement_level=EnforcementLevel.RUNTIME,
            enabled=False,
        ))
        self.enforcer = ComplianceEnforcer(collection)

    def test_validate_active_control(self):
        """Kiểm tra validate control active pass."""
        result = self.enforcer.validate("sox_immutable", {})
        assert result.passed is True
        assert result.control_id == "sox_immutable"

    def test_validate_disabled_control(self):
        """Kiểm tra validate control disabled → skip."""
        result = self.enforcer.validate("disabled_control", {})
        assert result.passed is True
        assert "không active" in result.message

    def test_validate_nonexistent_control(self):
        """Kiểm tra validate control không tồn tại → fail."""
        result = self.enforcer.validate("nonexistent", {})
        assert result.passed is False
        assert "không tìm thấy" in result.message

    def test_validate_with_context(self):
        """Kiểm tra validate control với context."""
        result = self.enforcer.validate("sox_immutable", {"user": "admin", "tenant": "t1"})
        assert result.passed is True

    def test_get_active_controls(self):
        """Kiểm tra get_active_controls() trả về controls đang enabled."""
        active = self.enforcer.get_active_controls()
        assert len(active) == 1
        assert active[0].id == "sox_immutable"

    def test_get_active_controls_empty(self):
        """Kiểm tra get_active_controls() trả về list rỗng khi không có control."""
        collection = AuditComplianceCollection()
        enforcer = ComplianceEnforcer(collection)
        assert enforcer.get_active_controls() == []

    def test_validate_compile_only_control(self):
        """Kiểm tra validate control chỉ enforce ở compile time."""
        collection = AuditComplianceCollection()
        collection.add_control(ComplianceControl(
            id="compile_only",
            name="Compile Only",
            standard=StandardType.PCI_DSS,
            control_type=ControlType.PREVENTIVE,
            enforcement_level=EnforcementLevel.COMPILE,
        ))
        enforcer = ComplianceEnforcer(collection)
        result = enforcer.validate("compile_only", {})
        assert result.passed is True
        assert "không cần runtime check" in result.message
