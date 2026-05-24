# coding: utf-8
"""
Test recipes cho CP44 — Bulk Operations Engine.

Test:
- RecipeOutput dataclass
- basic_bulk_recipe: output hợp lệ
- full_bulk_recipe: output hợp lệ
"""

import pytest

from midicoder.emitters.core.cp44_bulk_ops.recipes import (
    RecipeOutput,
    basic_bulk_recipe,
    full_bulk_recipe,
)
from midicoder.emitters.core.cp44_bulk_ops.models import (
    BulkAction,
    RetryStrategy,
)


# ============================================================================
# Test RecipeOutput
# ============================================================================


class TestRecipeOutput:
    """Test RecipeOutput dataclass."""

    def test_create(self):
        """Tạo RecipeOutput."""
        from midicoder.emitters.core.cp44_bulk_ops.parser import BulkIR
        ro = RecipeOutput(
            name="test",
            description="test recipe",
            ir=BulkIR(),
        )
        assert ro.name == "test"
        assert ro.description == "test recipe"
        assert isinstance(ro.ir, type(ro.ir))


# ============================================================================
# Test basic_bulk_recipe
# ============================================================================


class TestBasicBulkRecipe:
    """Test basic_bulk_recipe function."""

    def test_returns_recipe_output(self):
        """Recipe trả về RecipeOutput."""
        result = basic_bulk_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        """Tên recipe đúng."""
        result = basic_bulk_recipe()
        assert result.name == "basic_bulk"

    def test_description(self):
        """Mô tả recipe."""
        result = basic_bulk_recipe()
        assert "250" in result.description
        assert "chunk_size" in result.description

    def test_has_one_job(self):
        """Có 1 job."""
        result = basic_bulk_recipe()
        assert len(result.ir.jobs) == 1

    def test_job_entity_type(self):
        """Job entity type là 'user'."""
        result = basic_bulk_recipe()
        assert result.ir.jobs[0].entity_type == "user"

    def test_job_action(self):
        """Job action là BATCH_UPDATE."""
        result = basic_bulk_recipe()
        assert result.ir.jobs[0].action == BulkAction.BATCH_UPDATE

    def test_job_entity_count(self):
        """Job có 250 entities."""
        result = basic_bulk_recipe()
        assert result.ir.jobs[0].total_records == 250

    def test_job_chunk_size(self):
        """Job chunk_size=100."""
        result = basic_bulk_recipe()
        assert result.ir.jobs[0].chunk_size == 100

    def test_job_concurrency(self):
        """Job max_concurrency=5."""
        result = basic_bulk_recipe()
        assert result.ir.jobs[0].max_concurrency == 5

    def test_default_config(self):
        """Default config đúng."""
        result = basic_bulk_recipe()
        assert result.ir.default_chunk_size == 100
        assert result.ir.default_concurrency == 5
        assert result.ir.dlq_enabled is True
        assert result.ir.use_events is True
        assert result.ir.use_audit is True


# ============================================================================
# Test full_bulk_recipe
# ============================================================================


class TestFullBulkRecipe:
    """Test full_bulk_recipe function."""

    def test_returns_recipe_output(self):
        """Recipe trả về RecipeOutput."""
        result = full_bulk_recipe()
        assert isinstance(result, RecipeOutput)

    def test_name(self):
        """Tên recipe đúng."""
        result = full_bulk_recipe()
        assert result.name == "full_bulk"

    def test_has_three_jobs(self):
        """Có 3 jobs."""
        result = full_bulk_recipe()
        assert len(result.ir.jobs) == 3

    def test_job_types(self):
        """3 jobs có entity types khác nhau."""
        result = full_bulk_recipe()
        types = {j.entity_type for j in result.ir.jobs}
        assert "product" in types
        assert "order" in types
        assert "invoice" in types

    def test_job_actions(self):
        """3 jobs có actions khác nhau."""
        result = full_bulk_recipe()
        actions = {j.action for j in result.ir.jobs}
        assert len(actions) == 3  # update, delete, create

    def test_multi_tenant(self):
        """Jobs có tenant_id khác nhau."""
        result = full_bulk_recipe()
        tenants = {j.tenant_id for j in result.ir.jobs}
        assert len(tenants) >= 2  # ít nhất 2 tenants

    def test_different_retry_strategies(self):
        """Các job có retry strategy khác nhau."""
        result = full_bulk_recipe()
        strategies = {j.retry_strategy for j in result.ir.jobs}
        assert len(strategies) >= 2  # ít nhất 2 strategies khác nhau

    def test_total_records(self):
        """Tổng số records = 1000 + 500 + 300 = 1800."""
        result = full_bulk_recipe()
        total = sum(j.total_records for j in result.ir.jobs)
        assert total == 1800

    def test_job_metadata(self):
        """Jobs có metadata."""
        result = full_bulk_recipe()
        for job in result.ir.jobs:
            assert "recipe" in job.metadata
            assert job.metadata["recipe"] == "full_bulk"

    def test_all_jobs_have_operator(self):
        """Tất cả jobs có operator_id."""
        result = full_bulk_recipe()
        for job in result.ir.jobs:
            assert job.operator_id
