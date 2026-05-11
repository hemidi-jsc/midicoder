# coding: utf-8
"""
Test cases cho AuditEffect integration với CP14 AuditLogger.

Kiểm tra:
- AuditEffect.execute() gọi CP14 AuditLogger.log()
- Validate entity_type, entity_id bắt buộc
- Action mapping từ string sang AuditActionType
- Error handling khi thiếu fields
"""

import tempfile
import pytest

from midicoder.emitters.core.audit.audit_engine import AuditLogger
from midicoder.emitters.core.audit.models import AuditActionType, AuditTrail
from midicoder.emitters.core.workflow.effects.audit import AuditEffect
from midicoder.emitters.core.workflow.effects.base import EffectResult


class TestAuditEffectIntegration:
    """Test AuditEffect tích hợp với CP14 AuditLogger."""

    def setup_method(self):
        """Setup logger và effect cho mỗi test."""
        self.log_dir = tempfile.mkdtemp()
        self.logger = AuditLogger(log_dir=self.log_dir)
        self.effect = AuditEffect(action="workflow_transition", logger=self.logger)

    def test_execute_creates_audit_entry(self):
        """Kiểm tra execute() tạo audit entry trong CP14 logger."""
        result = self.effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
            "actor_id": "user_456",
            "tenant_id": "tenant_1",
        })
        assert result.success is True
        assert len(self.logger._entries) == 1
        entry = self.logger._entries[0]
        assert entry.entity_type == "Order"
        assert entry.entity_id == "order_123"
        assert entry.actor_id == "user_456"
        assert entry.tenant_id == "tenant_1"

    def test_execute_with_custom_action(self):
        """Kiểm tra execute() với action tùy chỉnh."""
        effect = AuditEffect(action="CREATE", logger=self.logger)
        result = effect.execute({
            "entity_type": "Product",
            "entity_id": "prod_001",
        })
        assert result.success is True
        entry = self.logger._entries[0]
        assert entry.action == AuditActionType.CREATE

    def test_execute_with_all_fields(self):
        """Kiểm tra execute() với đầy đủ fields."""
        effect = AuditEffect(action="UPDATE", logger=self.logger)
        result = effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
            "actor_id": "user_456",
            "actor_type": "user",
            "tenant_id": "tenant_1",
            "old_values": {"status": "draft"},
            "new_values": {"status": "submitted"},
            "metadata": {"ip": "127.0.0.1"},
        })
        assert result.success is True
        entry = self.logger._entries[0]
        assert entry.action == AuditActionType.UPDATE
        assert entry.actor_type == "user"
        assert entry.old_values == {"status": "draft"}
        assert entry.new_values == {"status": "submitted"}
        assert entry.metadata == {"ip": "127.0.0.1"}

    def test_execute_missing_entity_type_fails(self):
        """Kiểm tra execute() thất bại khi thiếu entity_type."""
        result = self.effect.execute({
            "entity_id": "order_123",
        })
        assert result.success is False
        assert "entity_type" in result.error
        assert len(self.logger._entries) == 0

    def test_execute_empty_entity_type_fails(self):
        """Kiểm tra execute() thất bại khi entity_type rỗng."""
        result = self.effect.execute({
            "entity_type": "",
            "entity_id": "order_123",
        })
        assert result.success is False
        assert "entity_type" in result.error

    def test_execute_missing_entity_id_fails(self):
        """Kiểm tra execute() thất bại khi thiếu entity_id."""
        result = self.effect.execute({
            "entity_type": "Order",
        })
        assert result.success is False
        assert "entity_id" in result.error
        assert len(self.logger._entries) == 0

    def test_execute_empty_entity_id_fails(self):
        """Kiểm tra execute() thất bại khi entity_id rỗng."""
        result = self.effect.execute({
            "entity_type": "Order",
            "entity_id": "  ",
        })
        assert result.success is False
        assert "entity_id" in result.error

    def test_execute_invalid_action_defaults_to_custom(self):
        """Kiểm tra action không hợp lệ default sang CUSTOM."""
        effect = AuditEffect(action="INVALID_ACTION", logger=self.logger)
        result = effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
        })
        assert result.success is True
        entry = self.logger._entries[0]
        assert entry.action == AuditActionType.CUSTOM

    def test_execute_without_logger_succeeds(self):
        """Kiểm tra execute() không có logger vẫn thành công (fallback)."""
        effect = AuditEffect(action="CREATE")  # Không truyền logger
        result = effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
        })
        assert result.success is True

    def test_execute_action_from_data(self):
        """Kiểm tra action từ data overrides effect's action."""
        effect = AuditEffect(action=None, logger=self.logger)  # Không có action mặc định
        result = effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
            "action": "DELETE",
        })
        assert result.success is True
        entry = self.logger._entries[0]
        assert entry.action == AuditActionType.DELETE

    def test_execute_multiple_times_accumulates_entries(self):
        """Kiểm tra execute nhiều lần tích lũy entries trong logger."""
        for i in range(3):
            self.effect.execute({
                "entity_type": "Order",
                "entity_id": f"order_{i}",
                "actor_id": "user_1",
            })
        assert len(self.logger._entries) == 3

    def test_execute_result_contains_hash(self):
        """Kiểm tra result data chứa immutable hash."""
        result = self.effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
            "actor_id": "user_1",
        })
        assert result.success is True
        assert result.data is not None
        assert "immutable_hash" in result.data["audit"]
        assert len(result.data["audit"]["immutable_hash"]) == 64  # SHA-256 hex

    def test_execute_entry_hash_is_valid(self):
        """Kiểm tra entry tạo ra có hash hợp lệ."""
        self.effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
            "actor_id": "user_1",
        })
        entry = self.logger._entries[0]
        assert entry.verify_hash() is True

    def test_execute_default_values(self):
        """Kiểm tra default values khi không cung cấp optional fields."""
        self.effect.execute({
            "entity_type": "Order",
            "entity_id": "order_123",
        })
        entry = self.logger._entries[0]
        assert entry.actor_id == "system"
        assert entry.actor_type == "system"
        assert entry.tenant_id == "default"
        assert entry.old_values == {}
        assert entry.new_values == {}
        assert entry.metadata == {}

    def test_execute_message_contains_entity_info(self):
        """Kiểm tra message chứa thông tin entity."""
        result = self.effect.execute({
            "entity_type": "Product",
            "entity_id": "prod_456",
            "actor_id": "admin",
        })
        assert result.success is True
        assert "Product" in result.message
        assert "prod_456" in result.message
