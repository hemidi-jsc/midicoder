# coding: utf-8
"""
Tests cho CP47 recipes — Data Retention & Lifecycle Management.
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp47_retention.recipes import (
    RecipeOutput,
    basic_retention_recipe,
    full_lifecycle_recipe,
)


class TestRecipeOutput:
    """Kiểm tra class RecipeOutput."""

    def test_create(self):
        """Test tạo RecipeOutput."""
        from midicoder.emitters.core.cp47_retention.parser import RetentionIR
        output = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=RetentionIR(),
        )
        assert output.name == "test"
        assert output.description == "Test recipe"

    def test_to_dict(self):
        """Test chuyển RecipeOutput sang dict."""
        from midicoder.emitters.core.cp47_retention.parser import RetentionIR
        output = RecipeOutput(
            name="test",
            description="Test recipe",
            ir=RetentionIR(enable_purge=True),
        )
        d = output.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test recipe"
        assert d["ir"]["enable_purge"] is True


class TestBasicRetentionRecipe:
    """Kiểm tra hàm basic_retention_recipe."""

    def test_returns_recipe_output(self):
        """Test basic_retention_recipe trả về RecipeOutput."""
        result = basic_retention_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        """Test tên recipe là 'basic_retention'."""
        result = basic_retention_recipe()
        assert result.name == "basic_retention"

    def test_description(self):
        """Test mô tả recipe có chứa từ khóa."""
        result = basic_retention_recipe()
        assert "archive" in result.description or "90" in result.description

    def test_has_one_policy(self):
        """Test recipe có một policy."""
        result = basic_retention_recipe()
        assert len(result.ir.policies) == 1

    def test_policy_action_is_archive(self):
        """Test policy action là 'archive'."""
        result = basic_retention_recipe()
        assert result.ir.policies[0]["action"] == "archive"

    def test_policy_retention_days_is_90(self):
        """Test retention_days của policy là 90."""
        result = basic_retention_recipe()
        assert result.ir.policies[0]["retention_days"] == 90

    def test_policy_entity_type_is_record(self):
        """Test entity_type của policy là 'Record'."""
        result = basic_retention_recipe()
        assert result.ir.policies[0]["entity_type"] == "Record"

    def test_policy_id_is_default_archive(self):
        """Test policy_id là 'default_archive'."""
        result = basic_retention_recipe()
        assert result.ir.policies[0]["policy_id"] == "default_archive"

    def test_archival_enabled(self):
        """Test archival được bật."""
        result = basic_retention_recipe()
        assert result.ir.enable_archival is True

    def test_purge_disabled(self):
        """Test purge bị tắt."""
        result = basic_retention_recipe()
        assert result.ir.enable_purge is False

    def test_erasure_disabled(self):
        """Test erasure bị tắt."""
        result = basic_retention_recipe()
        assert result.ir.enable_erasure is False

    def test_scheduler_enabled(self):
        """Test scheduler được bật."""
        result = basic_retention_recipe()
        assert result.ir.enable_scheduler is True

    def test_default_retention_days_90(self):
        """Test default_retention_days là 90."""
        result = basic_retention_recipe()
        assert result.ir.default_retention_days == 90

    def test_batch_size_is_1000(self):
        """Test batch_size mặc định là 1000."""
        result = basic_retention_recipe()
        assert result.ir.batch_size == 1000


class TestFullLifecycleRecipe:
    """Kiểm tra hàm full_lifecycle_recipe."""

    def test_returns_recipe_output(self):
        """Test full_lifecycle_recipe trả về RecipeOutput."""
        result = full_lifecycle_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        """Test tên recipe là 'full_lifecycle'."""
        result = full_lifecycle_recipe()
        assert result.name == "full_lifecycle"

    def test_has_three_policies(self):
        """Test recipe có ba policies."""
        result = full_lifecycle_recipe()
        assert len(result.ir.policies) == 3

    def test_policy_types(self):
        """Test các policy types khác nhau."""
        result = full_lifecycle_recipe()
        policy_ids = [p["policy_id"] for p in result.ir.policies]
        assert "order_archive" in policy_ids
        assert "transaction_purge" in policy_ids
        assert "session_purge" in policy_ids

    def test_policy_entity_types(self):
        """Test các entity types khác nhau."""
        result = full_lifecycle_recipe()
        entity_types = [p["entity_type"] for p in result.ir.policies]
        assert "Order" in entity_types
        assert "Transaction" in entity_types
        assert "Session" in entity_types

    def test_all_features_enabled(self):
        """Test tất cả features được bật."""
        result = full_lifecycle_recipe()
        assert result.ir.enable_archival is True
        assert result.ir.enable_purge is True
        assert result.ir.enable_erasure is True
        assert result.ir.enable_scheduler is True

    def test_batch_size(self):
        """Test batch_size là 1000."""
        result = full_lifecycle_recipe()
        assert result.ir.batch_size == 1000

    def test_default_retention_days_365(self):
        """Test default_retention_days là 365."""
        result = full_lifecycle_recipe()
        assert result.ir.default_retention_days == 365

    def test_order_policy_retention_days(self):
        """Test Order policy có retention_days là 365."""
        result = full_lifecycle_recipe()
        order_policy = next(p for p in result.ir.policies if p["entity_type"] == "Order")
        assert order_policy["retention_days"] == 365

    def test_transaction_policy_retention_days(self):
        """Test Transaction policy có retention_days là 730."""
        result = full_lifecycle_recipe()
        transaction_policy = next(p for p in result.ir.policies if p["entity_type"] == "Transaction")
        assert transaction_policy["retention_days"] == 730

    def test_session_policy_retention_days(self):
        """Test Session policy có retention_days là 30."""
        result = full_lifecycle_recipe()
        session_policy = next(p for p in result.ir.policies if p["entity_type"] == "Session")
        assert session_policy["retention_days"] == 30
