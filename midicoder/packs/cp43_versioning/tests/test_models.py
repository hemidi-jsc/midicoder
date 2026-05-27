# coding: utf-8
"""
Test cho CP43 models — VersionConfig, HistoryRecord, SoftDeleteMixin, OperationType, VersioningCollection.

TDD: RED → GREEN → REFACTOR
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from midicoder.errors import MidicoderError
from midicoder.packs.cp43_versioning.models import (
    HistoryRecord,
    OperationType,
    SoftDeleteMixin,
    VersionConfig,
    VersioningCollection,
)


class TestOperationType:
    """Test cho OperationType enum."""

    def test_create_value(self) -> None:
        """Kiểm tra CREATE value."""
        assert OperationType.CREATE.value == "CREATE"

    def test_update_value(self) -> None:
        """Kiểm tra UPDATE value."""
        assert OperationType.UPDATE.value == "UPDATE"

    def test_delete_value(self) -> None:
        """Kiểm tra DELETE value."""
        assert OperationType.DELETE.value == "DELETE"

    def test_restore_value(self) -> None:
        """Kiểm tra RESTORE value."""
        assert OperationType.RESTORE.value == "RESTORE"

    def test_hard_delete_value(self) -> None:
        """Kiểm tra HARD_DELETE value."""
        assert OperationType.HARD_DELETE.value == "HARD_DELETE"

    def test_parse_from_string(self) -> None:
        """Kiểm tra parse OperationType từ string."""
        assert OperationType("CREATE") == OperationType.CREATE
        assert OperationType("UPDATE") == OperationType.UPDATE
        assert OperationType("DELETE") == OperationType.DELETE
        assert OperationType("RESTORE") == OperationType.RESTORE
        assert OperationType("HARD_DELETE") == OperationType.HARD_DELETE

    def test_invalid_operation_string(self) -> None:
        """Kiểm tra parse string không hợp lệ raise ValueError."""
        with pytest.raises(ValueError):
            OperationType("INVALID")


class TestVersionConfig:
    """Test cho VersionConfig dataclass."""

    def test_create_default_config(self) -> None:
        """Kiểm tra tạo config với default values."""
        config = VersionConfig(entity_type="Order")
        assert config.entity_type == "Order"
        assert config.enable_versioning is True
        assert config.enable_soft_delete is True
        assert config.enable_history is True
        assert config.enable_audit_integration is True
        assert config.max_versions == 0
        assert config.history_retention_days == 0
        assert config.snapshot_fields == []
        assert config.exclude_fields == []

    def test_create_custom_config(self) -> None:
        """Kiểm tra tạo config với custom values."""
        config = VersionConfig(
            entity_type="Product",
            enable_versioning=True,
            enable_soft_delete=False,
            max_versions=10,
            history_retention_days=365,
            snapshot_fields=["name", "price"],
            exclude_fields=["password"],
        )
        assert config.entity_type == "Product"
        assert config.enable_soft_delete is False
        assert config.max_versions == 10
        assert config.history_retention_days == 365
        assert config.snapshot_fields == ["name", "price"]
        assert config.exclude_fields == ["password"]

    def test_empty_entity_type_raises(self) -> None:
        """Kiểm tra entity_type rỗng raise MidicoderError."""
        with pytest.raises(MidicoderError):
            VersionConfig(entity_type="")

    def test_whitespace_entity_type_raises(self) -> None:
        """Kiểm tra entity_type chỉ whitespace raise MidicoderError."""
        with pytest.raises(MidicoderError):
            VersionConfig(entity_type="   ")

    def test_negative_max_versions_raises(self) -> None:
        """Kiểm tra max_versions âm raise MidicoderError."""
        with pytest.raises(MidicoderError):
            VersionConfig(entity_type="Order", max_versions=-1)

    def test_negative_retention_days_raises(self) -> None:
        """Kiểm tra history_retention_days âm raise MidicoderError."""
        with pytest.raises(MidicoderError):
            VersionConfig(entity_type="Order", history_retention_days=-5)

    def test_to_dict(self) -> None:
        """Kiểm tra chuyển config sang dict."""
        config = VersionConfig(
            entity_type="Order",
            enable_soft_delete=False,
            max_versions=10,
        )
        d = config.to_dict()
        assert d["entity_type"] == "Order"
        assert d["enable_soft_delete"] is False
        assert d["max_versions"] == 10
        assert d["enable_versioning"] is True

    def test_from_dict(self) -> None:
        """Kiểm tra tạo config từ dict."""
        d = {
            "entity_type": "Product",
            "enable_versioning": True,
            "enable_soft_delete": False,
            "enable_history": True,
            "enable_audit_integration": True,
            "max_versions": 5,
            "history_retention_days": 180,
            "snapshot_fields": ["sku"],
            "exclude_fields": [],
        }
        config = VersionConfig.from_dict(d)
        assert config.entity_type == "Product"
        assert config.enable_soft_delete is False
        assert config.max_versions == 5
        assert config.history_retention_days == 180
        assert config.snapshot_fields == ["sku"]


class TestHistoryRecord:
    """Test cho HistoryRecord dataclass."""

    def test_create_record(self) -> None:
        """Kiểm tra tạo history record."""
        record = HistoryRecord(
            entity_type="Order",
            entity_id="order_123",
            version=1,
            snapshot={"status": "pending", "total": 100},
            operation=OperationType.CREATE,
            created_by="user_1",
        )
        assert record.entity_type == "Order"
        assert record.entity_id == "order_123"
        assert record.version == 1
        assert record.snapshot == {"status": "pending", "total": 100}
        assert record.operation == OperationType.CREATE
        assert record.created_by == "user_1"
        assert record.immutable_hash != ""

    def test_version_zero_raises(self) -> None:
        """Kiểm tra version < 1 raise MidicoderError."""
        with pytest.raises(MidicoderError):
            HistoryRecord(
                entity_type="Order", entity_id="1", version=0,
                snapshot={}, operation=OperationType.CREATE, created_by="system",
            )

    def test_negative_version_raises(self) -> None:
        """Kiểm tra version âm raise MidicoderError."""
        with pytest.raises(MidicoderError):
            HistoryRecord(
                entity_type="Order", entity_id="1", version=-1,
                snapshot={}, operation=OperationType.CREATE, created_by="system",
            )

    def test_empty_entity_type_raises(self) -> None:
        """Kiểm tra entity_type rỗng raise MidicoderError."""
        with pytest.raises(MidicoderError):
            HistoryRecord(
                entity_type="", entity_id="1", version=1,
                snapshot={}, operation=OperationType.CREATE, created_by="system",
            )

    def test_empty_entity_id_raises(self) -> None:
        """Kiểm tra entity_id rỗng raise MidicoderError."""
        with pytest.raises(MidicoderError):
            HistoryRecord(
                entity_type="Order", entity_id="", version=1,
                snapshot={}, operation=OperationType.CREATE, created_by="system",
            )

    def test_hash_verification(self) -> None:
        """Kiểm tra hash verification pass cho record mới tạo."""
        record = HistoryRecord(
            entity_type="Order", entity_id="order_123", version=1,
            snapshot={"status": "pending"}, operation=OperationType.CREATE, created_by="user_1",
        )
        assert record.verify_hash() is True

    def test_hash_changes_after_modification(self) -> None:
        """Kiểm tra hash thay đổi sau khi sửa snapshot."""
        record = HistoryRecord(
            entity_type="Order", entity_id="order_123", version=1,
            snapshot={"status": "pending"}, operation=OperationType.CREATE, created_by="user_1",
        )
        original_hash = record.immutable_hash
        record.snapshot["status"] = "confirmed"
        assert record.verify_hash() is False
        assert record.immutable_hash == original_hash

    def test_to_dict_and_from_dict(self) -> None:
        """Kiểm tra round-trip to_dict → from_dict."""
        record = HistoryRecord(
            entity_type="Product", entity_id="prod_1", version=3,
            snapshot={"price": 50}, operation=OperationType.UPDATE,
            changed_fields=["price"], created_by="user_2",
        )
        d = record.to_dict()
        restored = HistoryRecord.from_dict(d)
        assert restored.entity_type == "Product"
        assert restored.entity_id == "prod_1"
        assert restored.version == 3
        assert restored.snapshot == {"price": 50}
        assert restored.operation == OperationType.UPDATE
        assert restored.changed_fields == ["price"]
        assert restored.created_by == "user_2"


class TestSoftDeleteMixin:
    """Test cho SoftDeleteMixin dataclass."""

    def test_new_mixin_not_deleted(self) -> None:
        """Kiểm tra mixin mới tạo chưa bị xóa."""
        mixin = SoftDeleteMixin()
        assert mixin.is_deleted() is False
        assert mixin.deleted_at is None
        assert mixin.deleted_by == ""

    def test_soft_delete(self) -> None:
        """Kiểm tra soft delete đánh dấu entity."""
        mixin = SoftDeleteMixin()
        mixin.soft_delete(actor="user_1")
        assert mixin.is_deleted() is True
        assert mixin.deleted_at is not None
        assert mixin.deleted_by == "user_1"

    def test_restore(self) -> None:
        """Kiểm tra restore entity đã bị xóa."""
        mixin = SoftDeleteMixin()
        mixin.soft_delete(actor="user_1")
        mixin.restore()
        assert mixin.is_deleted() is False
        assert mixin.deleted_at is None
        assert mixin.deleted_by == ""

    def test_to_dict_active(self) -> None:
        """Kiểm tra to_dict cho entity chưa xóa."""
        mixin = SoftDeleteMixin()
        d = mixin.to_dict()
        assert d["deleted_at"] is None
        assert d["deleted_by"] == ""

    def test_to_dict_deleted(self) -> None:
        """Kiểm tra to_dict cho entity đã xóa."""
        mixin = SoftDeleteMixin()
        mixin.soft_delete(actor="admin")
        d = mixin.to_dict()
        assert d["deleted_at"] is not None
        assert d["deleted_by"] == "admin"

    def test_from_dict_active(self) -> None:
        """Kiểm tra from_dict cho entity chưa xóa."""
        d = {"deleted_at": None, "deleted_by": ""}
        mixin = SoftDeleteMixin.from_dict(d)
        assert mixin.is_deleted() is False

    def test_from_dict_deleted(self) -> None:
        """Kiểm tra from_dict cho entity đã xóa."""
        ts = datetime.now(timezone.utc).isoformat()
        d = {"deleted_at": ts, "deleted_by": "admin"}
        mixin = SoftDeleteMixin.from_dict(d)
        assert mixin.is_deleted() is True
        assert mixin.deleted_by == "admin"


class TestVersioningCollection:
    """Test cho VersioningCollection."""

    def test_empty_collection(self) -> None:
        """Kiểm tra collection rỗng."""
        col = VersioningCollection()
        assert col.configs == []
        assert col.history_records == []

    def test_add_config(self) -> None:
        """Kiểm tra thêm config."""
        col = VersioningCollection()
        col.add_config(VersionConfig(entity_type="Order"))
        col.add_config(VersionConfig(entity_type="Product"))
        assert len(col.configs) == 2

    def test_duplicate_config_raises(self) -> None:
        """Kiểm tra thêm config duplicate entity_type raise MidicoderError."""
        col = VersioningCollection()
        col.add_config(VersionConfig(entity_type="Order"))
        with pytest.raises(MidicoderError):
            col.add_config(VersionConfig(entity_type="Order"))

    def test_get_config_by_entity_type(self) -> None:
        """Kiểm tra tìm config theo entity_type."""
        col = VersioningCollection()
        col.add_config(VersionConfig(entity_type="Order"))
        col.add_config(VersionConfig(entity_type="Product"))
        assert col.get_config_by_entity_type("Order") is not None
        assert col.get_config_by_entity_type("Product") is not None
        assert col.get_config_by_entity_type("Missing") is None

    def test_add_history_record(self) -> None:
        """Kiểm tra thêm history record."""
        col = VersioningCollection()
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=1,
            snapshot={}, operation=OperationType.CREATE, created_by="system",
        ))
        assert len(col.history_records) == 1

    def test_get_history_for_entity(self) -> None:
        """Kiểm tra lọc history records cho entity cụ thể."""
        col = VersioningCollection()
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=1,
            snapshot={}, operation=OperationType.CREATE, created_by="system",
        ))
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=2,
            snapshot={}, operation=OperationType.UPDATE, created_by="system",
        ))
        col.add_history_record(HistoryRecord(
            entity_type="Product", entity_id="p1", version=1,
            snapshot={}, operation=OperationType.CREATE, created_by="system",
        ))
        assert len(col.get_history_for_entity("Order", "o1")) == 2
        assert len(col.get_history_for_entity("Product", "p1")) == 1
        assert len(col.get_history_for_entity("Order", "o2")) == 0

    def test_get_latest_version(self) -> None:
        """Kiểm tra lấy version mới nhất."""
        col = VersioningCollection()
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=1,
            snapshot={}, operation=OperationType.CREATE, created_by="system",
        ))
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=5,
            snapshot={}, operation=OperationType.UPDATE, created_by="system",
        ))
        assert col.get_latest_version("Order", "o1") == 5
        assert col.get_latest_version("Order", "o2") == 0

    def test_to_dict_and_from_dict(self) -> None:
        """Kiểm tra round-trip to_dict → from_dict."""
        col = VersioningCollection()
        col.add_config(VersionConfig(entity_type="Order", max_versions=10))
        col.add_history_record(HistoryRecord(
            entity_type="Order", entity_id="o1", version=1,
            snapshot={"status": "pending"}, operation=OperationType.CREATE, created_by="system",
        ))
        d = col.to_dict()
        restored = VersioningCollection.from_dict(d)
        assert len(restored.configs) == 1
        assert restored.configs[0].entity_type == "Order"
        assert restored.configs[0].max_versions == 10
        assert len(restored.history_records) == 1
        assert restored.history_records[0].entity_type == "Order"
