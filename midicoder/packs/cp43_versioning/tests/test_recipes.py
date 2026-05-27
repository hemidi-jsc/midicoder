# coding: utf-8
"""
Test cho CP43 recipes — build_versioning_ir, full/minimal/soft_delete recipes.
"""

import pytest

from midicoder.packs.cp43_versioning.recipes import (
    build_versioning_ir,
    full_versioning_recipe,
    minimal_versioning_recipe,
    soft_delete_only_recipe,
    create_history_record,
)
from midicoder.packs.cp43_versioning.models import (
    HistoryRecord,
    OperationType,
    VersioningCollection,
)


class TestBuildVersioningIR:
    """Test cho build_versioning_ir recipe."""

    def test_empty_entities(self) -> None:
        """Kiểm tra build với entities rỗng."""
        result = build_versioning_ir([])
        assert isinstance(result, VersioningCollection)
        assert len(result.configs) == 0

    def test_single_entity(self) -> None:
        """Kiểm tra build với 1 entity."""
        entities = [{"id": "Order"}]
        result = build_versioning_ir(entities)
        assert len(result.configs) == 1
        config = result.configs[0]
        assert config.entity_type == "Order"
        assert config.enable_versioning is True
        assert config.enable_soft_delete is True
        assert config.enable_history is True
        assert config.enable_audit_integration is True

    def test_multiple_entities(self) -> None:
        """Kiểm tra build với nhiều entities."""
        entities = [
            {"id": "Order"},
            {"id": "Product"},
            {"id": "Customer"},
        ]
        result = build_versioning_ir(entities)
        assert len(result.configs) == 3
        assert result.configs[0].entity_type == "Order"
        assert result.configs[1].entity_type == "Product"
        assert result.configs[2].entity_type == "Customer"

    def test_skip_non_dict_entities(self) -> None:
        """Kiểm tra skip entities không phải dict."""
        entities = ["invalid", 123, {"id": "Valid"}]
        result = build_versioning_ir(entities)
        assert len(result.configs) == 1
        assert result.configs[0].entity_type == "Valid"

    def test_skip_entities_without_id(self) -> None:
        """Kiểm tra skip entities không có id."""
        entities = [{"fields": []}, {"id": "Valid"}]
        result = build_versioning_ir(entities)
        assert len(result.configs) == 1


class TestFullVersioningRecipe:
    """Test cho full_versioning_recipe."""

    def test_default_settings(self) -> None:
        """Kiểm tra recipe với default settings."""
        entities = [{"id": "Order"}]
        result = full_versioning_recipe(entities)
        assert len(result.configs) == 1
        config = result.configs[0]
        assert config.enable_versioning is True
        assert config.enable_soft_delete is True
        assert config.enable_history is True
        assert config.enable_audit_integration is True
        assert config.max_versions == 0
        assert config.history_retention_days == 365

    def test_custom_settings(self) -> None:
        """Kiểm tra recipe với custom settings."""
        entities = [{"id": "Order"}]
        result = full_versioning_recipe(
            entities,
            enable_soft_delete=False,
            enable_audit_integration=False,
            history_retention_days=730,
        )
        config = result.configs[0]
        assert config.enable_soft_delete is False
        assert config.enable_audit_integration is False
        assert config.history_retention_days == 730


class TestMinimalVersioningRecipe:
    """Test cho minimal_versioning_recipe."""

    def test_minimal_settings(self) -> None:
        """Kiểm tra recipe với minimal settings."""
        entities = [{"id": "Order"}, {"id": "Product"}]
        result = minimal_versioning_recipe(entities)
        assert len(result.configs) == 2
        for config in result.configs:
            assert config.enable_versioning is True
            assert config.enable_soft_delete is False
            assert config.enable_history is True
            assert config.enable_audit_integration is False


class TestSoftDeleteOnlyRecipe:
    """Test cho soft_delete_only_recipe."""

    def test_soft_delete_only(self) -> None:
        """Kiểm tra recipe chỉ soft delete."""
        entities = [{"id": "Order"}]
        result = soft_delete_only_recipe(entities)
        config = result.configs[0]
        assert config.enable_versioning is False
        assert config.enable_soft_delete is True
        assert config.enable_history is False
        assert config.enable_audit_integration is False


class TestCreateHistoryRecord:
    """Test cho create_history_record helper."""

    def test_create_with_defaults(self) -> None:
        """Kiểm tra tạo history record với default values."""
        record = create_history_record(
            entity_type="Order",
            entity_id="o1",
            version=1,
            snapshot={"status": "pending"},
        )
        assert isinstance(record, HistoryRecord)
        assert record.entity_type == "Order"
        assert record.entity_id == "o1"
        assert record.version == 1
        assert record.snapshot == {"status": "pending"}
        assert record.operation == OperationType.CREATE
        assert record.changed_fields == []
        assert record.created_by == "system"
        assert record.immutable_hash != ""

    def test_create_with_all_params(self) -> None:
        """Kiểm tra tạo history record với đầy đủ params."""
        record = create_history_record(
            entity_type="Product",
            entity_id="p1",
            version=3,
            snapshot={"price": 100},
            operation=OperationType.UPDATE,
            changed_fields=["price", "name"],
            created_by="admin",
        )
        assert record.operation == OperationType.UPDATE
        assert record.changed_fields == ["price", "name"]
        assert record.created_by == "admin"

    def test_create_for_all_operations(self) -> None:
        """Kiểm tra tạo record cho tất cả operation types."""
        for op in OperationType:
            record = create_history_record(
                entity_type="Order",
                entity_id="o1",
                version=1,
                snapshot={},
                operation=op,
            )
            assert record.operation == op
