# coding: utf-8
"""
Mô-đun recipes cho CP44 — Bulk Operations Engine.

Cung cấp các recipe patterns để generate bulk operations với
chunked processing, retry strategy, và DLQ management.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass

from midicoder.emitters.core.cp44_bulk_ops.models import (
    BulkAction,
    BulkJob,
    RetryStrategy,
)
from midicoder.emitters.core.cp44_bulk_ops.parser import BulkIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: BulkIR kết quả
    """
    name: str
    description: str
    ir: BulkIR


def basic_bulk_recipe() -> RecipeOutput:
    """Recipe: Bulk job đơn giản — 1 entity type, 1 action, chunk_size=100, concurrency=5.

    Tạo bulk job cập nhật hàng loạt users với cấu hình cơ bản.
    Không có config đặc biệt, phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình bulk cơ bản
    """
    jobs = [
        BulkJob(
            job_id="bulk_basic_001",
            entity_type="user",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=[f"user_{i:04d}" for i in range(1, 251)],
            chunk_size=100,
            max_concurrency=5,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            timeout_seconds=300,
            metadata={"recipe": "basic_bulk"},
        ),
    ]

    return RecipeOutput(
        name="basic_bulk",
        description="1 job cập nhật 250 users, chunk_size=100, concurrency=5",
        ir=BulkIR(
            jobs=jobs,
            default_chunk_size=100,
            default_concurrency=5,
            default_max_retries=3,
            default_retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            default_timeout=300,
            dlq_enabled=True,
            use_events=True,
            use_audit=True,
        ),
    )


def full_bulk_recipe() -> RecipeOutput:
    """Recipe: Bulk jobs phức tạp — nhiều entity types, multi-tenant, retry, DLQ.

    Tạo 3 bulk jobs: (1) cập nhật products, (2) xóa orders cũ,
    (3) tạo invoices hàng loạt. Mỗi job có config riêng: chunk size,
    concurrency, retry strategy, tenant scope.

    Returns:
        RecipeOutput với cấu hình bulk đầy đủ
    """
    jobs = [
        BulkJob(
            job_id="bulk_full_products",
            entity_type="product",
            action=BulkAction.BATCH_UPDATE,
            entity_ids=[f"prod_{i:05d}" for i in range(1, 1001)],
            chunk_size=200,
            max_concurrency=10,
            max_retries=5,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            timeout_seconds=600,
            tenant_id="tenant_acme",
            operator_id="admin_001",
            metadata={"reason": "price_adjustment", "recipe": "full_bulk"},
        ),
        BulkJob(
            job_id="bulk_full_orders",
            entity_type="order",
            action=BulkAction.BATCH_DELETE,
            entity_ids=[f"order_{i:06d}" for i in range(1, 501)],
            chunk_size=50,
            max_concurrency=3,
            max_retries=1,
            retry_strategy=RetryStrategy.FIXED_DELAY,
            timeout_seconds=900,
            tenant_id="tenant_acme",
            operator_id="admin_002",
            metadata={"reason": "archive_old_orders", "older_than_days": 365, "recipe": "full_bulk"},
        ),
        BulkJob(
            job_id="bulk_full_invoices",
            entity_type="invoice",
            action=BulkAction.BATCH_CREATE,
            entity_ids=[f"inv_{i:05d}" for i in range(1, 301)],
            chunk_size=100,
            max_concurrency=8,
            max_retries=3,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            timeout_seconds=450,
            tenant_id="tenant_globex",
            operator_id="admin_003",
            metadata={"reason": "monthly_batch", "month": "2026-05", "recipe": "full_bulk"},
        ),
    ]

    return RecipeOutput(
        name="full_bulk",
        description="3 jobs (1000 products update, 500 orders delete, 300 invoices create), multi-tenant, các retry strategies khác nhau",
        ir=BulkIR(
            jobs=jobs,
            default_chunk_size=100,
            default_concurrency=10,
            default_max_retries=3,
            default_retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            default_timeout=300,
            dlq_enabled=True,
            use_events=True,
            use_audit=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_bulk_recipe",
    "full_bulk_recipe",
]
