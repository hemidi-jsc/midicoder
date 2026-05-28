# coding: utf-8
"""
Recipe module cho CP43 Versioning & History Generator.

Cung cấp:
- build_versioning_ir: Build MIR operations cho versioning
- full_versioning_recipe: Recipe đầy đủ với versioning + soft_delete + history + audit

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp_full_versioning.models import (
    HistoryRecord,
    OperationType,
    VersionConfig,
    VersioningCollection,
)


def build_versioning_ir(entities: list[dict]) -> VersioningCollection:
    """
    Build VersioningCollection từ danh sách entities (từ MIR metadata).

    Auto-generate versioning config cho tất cả entities với settings mặc định:
    - enable_versioning: True
    - enable_soft_delete: True
    - enable_history: True
    - enable_audit_integration: True

    Args:
        entities: Danh sách entity dicts từ MIR metadata

    Returns:
        VersioningCollection với config cho mỗi entity
    """
    collection = VersioningCollection()

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_type = entity.get("id", entity.get("name", ""))
        if not entity_type:
            continue

        config = VersionConfig(
            entity_type=entity_type,
            enable_versioning=True,
            enable_soft_delete=True,
            enable_history=True,
            enable_audit_integration=True,
        )
        collection.add_config(config)

    return collection


def full_versioning_recipe(
    entities: list[dict],
    enable_soft_delete: bool = True,
    enable_audit_integration: bool = True,
    history_retention_days: int = 365,
) -> VersioningCollection:
    """
    Recipe đầy đủ cho versioning + soft_delete + history + audit integration.

    Use case: Production systems cần full versioning lifecycle.

    Args:
        entities: Danh sách entity dicts từ MIR metadata
        enable_soft_delete: Có bật soft delete không
        enable_audit_integration: Có integrate với CP14 audit không
        history_retention_days: Số ngày giữ history records

    Returns:
        VersioningCollection với full config cho mỗi entity
    """
    collection = VersioningCollection()

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_type = entity.get("id", entity.get("name", ""))
        if not entity_type:
            continue

        config = VersionConfig(
            entity_type=entity_type,
            enable_versioning=True,
            enable_soft_delete=enable_soft_delete,
            enable_history=True,
            enable_audit_integration=enable_audit_integration,
            max_versions=0,  # vô hạn
            history_retention_days=history_retention_days,
        )
        collection.add_config(config)

    return collection


def minimal_versioning_recipe(entities: list[dict]) -> VersioningCollection:
    """
    Recipe tối giản: chỉ versioning, không soft_delete, không audit.

    Use case: Internal tools, non-regulated apps.

    Args:
        entities: Danh sách entity dicts từ MIR metadata

    Returns:
        VersioningCollection với minimal config
    """
    collection = VersioningCollection()

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_type = entity.get("id", entity.get("name", ""))
        if not entity_type:
            continue

        config = VersionConfig(
            entity_type=entity_type,
            enable_versioning=True,
            enable_soft_delete=False,
            enable_history=True,
            enable_audit_integration=False,
            max_versions=0,
            history_retention_days=0,
        )
        collection.add_config(config)

    return collection


def soft_delete_only_recipe(entities: list[dict]) -> VersioningCollection:
    """
    Recipe chỉ soft delete: không versioning, không history table.

    Use case: Entities chỉ cần soft delete, không cần history.

    Args:
        entities: Danh sách entity dicts từ MIR metadata

    Returns:
        VersioningCollection với chỉ soft delete enabled
    """
    collection = VersioningCollection()

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_type = entity.get("id", entity.get("name", ""))
        if not entity_type:
            continue

        config = VersionConfig(
            entity_type=entity_type,
            enable_versioning=False,
            enable_soft_delete=True,
            enable_history=False,
            enable_audit_integration=False,
        )
        collection.add_config(config)

    return collection


def create_history_record(
    entity_type: str,
    entity_id: str,
    version: int,
    snapshot: dict,
    operation: OperationType = OperationType.CREATE,
    changed_fields: list[str] | None = None,
    created_by: str = "system",
) -> HistoryRecord:
    """
    Helper để tạo HistoryRecord mới.

    Args:
        entity_type: Tên entity
        entity_id: ID entity
        version: Số version
        snapshot: Dữ liệu snapshot
        operation: Loại thao tác
        changed_fields: Các trường bị thay đổi
        created_by: User thực hiện thao tác

    Returns:
        HistoryRecord instance
    """
    return HistoryRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        version=version,
        snapshot=snapshot,
        operation=operation,
        changed_fields=changed_fields or [],
        created_by=created_by,
    )


__all__ = [
    "build_versioning_ir",
    "full_versioning_recipe",
    "minimal_versioning_recipe",
    "soft_delete_only_recipe",
    "create_history_record",
]
