# coding: utf-8
"""
Mô-đun recipes cho CP47 — Data Retention & Lifecycle Management.

Định nghĩa các pre-configured recipes để generate retention code nhanh.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp47_retention.parser import RetentionIR


# ===========================================================================
# RecipeOutput
# ===========================================================================


@dataclass
class RecipeOutput:
    """Kết quả của retention recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: RetentionIR kết quả
    """
    name: str
    description: str
    ir: RetentionIR

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
        }


# ===========================================================================
# Recipes
# ===========================================================================


def basic_retention_recipe() -> RecipeOutput:
    """Recipe: Basic retention — archive sau 90 ngày.

    Phù hợp cho projects cần retention policy đơn giản:
    - 1 policy: archive records sau 90 ngày
    - Bật archival, disable purge và erasure
    - Bật scheduler để auto-scan

    Returns:
        RecipeOutput với basic retention config
    """
    ir = RetentionIR(
        policies=[
            {
                "policy_id": "default_archive",
                "entity_type": "Record",
                "retention_days": 90,
                "action": "archive",
                "policy_type": "time_based",
            },
        ],
        enable_archival=True,
        enable_purge=False,
        enable_erasure=False,
        enable_scheduler=True,
        default_retention_days=90,
        batch_size=1000,
    )

    return RecipeOutput(
        name="basic_retention",
        description="Basic retention — archive records sau 90 ngày",
        ir=ir,
    )


def full_lifecycle_recipe() -> RecipeOutput:
    """Recipe: Full lifecycle — retention + archive + purge + GDPR erasure.

    Phù hợp cho projects cần full data lifecycle management:
    - Multiple policies cho nhiều entity types
    - Bật tất cả features: archival, purge, erasure, scheduler
    - Policies cho Order (archive 365 ngày), User (erasure), Transaction (purge 730 ngày)

    Returns:
        RecipeOutput với full lifecycle config
    """
    ir = RetentionIR(
        policies=[
            {
                "policy_id": "order_archive",
                "entity_type": "Order",
                "retention_days": 365,
                "action": "archive",
                "policy_type": "time_based",
            },
            {
                "policy_id": "transaction_purge",
                "entity_type": "Transaction",
                "retention_days": 730,
                "action": "archive_then_purge",
                "policy_type": "time_based",
            },
            {
                "policy_id": "session_purge",
                "entity_type": "Session",
                "retention_days": 30,
                "action": "purge",
                "policy_type": "time_based",
            },
        ],
        enable_archival=True,
        enable_purge=True,
        enable_erasure=True,
        enable_scheduler=True,
        default_retention_days=365,
        batch_size=1000,
    )

    return RecipeOutput(
        name="full_lifecycle",
        description="Full lifecycle — retention + archive + purge + GDPR erasure",
        ir=ir,
    )
