# coding: utf-8
"""
Mô-đun models cho Versioning & History Generator (CP43).

Định nghĩa các dataclass biểu diễn:
- OperationType: Enum các loại thao tác (CREATE/UPDATE/DELETE/RESTORE)
- VersionConfig: Cấu hình versioning cho entity
- HistoryRecord: Một bản ghi lịch sử của entity
- SoftDeleteMixin: Mixin cho soft delete functionality
- VersioningCollection: Collection chứa versioning config cho nhiều entity

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

# ===========================================================================
# OperationType
# ===========================================================================


# ===========================================================================
# Enums
# ===========================================================================


class OperationType(str, Enum):
    """
    Enum các loại thao tác trên entity.

    - CREATE: Tạo mới entity
    - UPDATE: Cập nhật entity
    - DELETE: Xóa entity (soft delete)
    - RESTORE: Khôi phục entity từ history
    - HARD_DELETE: Xóa vĩnh viễn entity
    """

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RESTORE = "RESTORE"
    HARD_DELETE = "HARD_DELETE"


# ===========================================================================
# VersionConfig
# ===========================================================================


@dataclass
class VersionConfig:
    """
    Cấu hình versioning cho một entity.

    Attributes:
        entity_type: Tên entity (ví dụ: "Order", "Product")
        enable_versioning: Có bật versioning không (default True)
        enable_soft_delete: Có bật soft delete không (default True)
        enable_history: Có bật history table không (default True)
        enable_audit_integration: Có integrate với CP14 audit không (default True)
        max_versions: Số lượng version tối đa giữ lại (0 = vô hạn)
        history_retention_days: Số ngày giữ history records (0 = vô hạn)
        snapshot_fields: Các trường cần lưu trong snapshot (rỗng = tất cả)
        exclude_fields: Các trường loại trừ khỏi snapshot
    """

    entity_type: str
    enable_versioning: bool = True
    enable_soft_delete: bool = True
    enable_history: bool = True
    enable_audit_integration: bool = True
    max_versions: int = 0
    history_retention_days: int = 0
    snapshot_fields: list[str] = field(default_factory=list)
    exclude_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.entity_type or not self.entity_type.strip():
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_CONFIG, field="entity_type")
        if self.max_versions < 0:
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_CONFIG, field="max_versions")
        if self.history_retention_days < 0:
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_CONFIG, field="history_retention_days")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển config sang dict format."""
        return {
            "entity_type": self.entity_type,
            "enable_versioning": self.enable_versioning,
            "enable_soft_delete": self.enable_soft_delete,
            "enable_history": self.enable_history,
            "enable_audit_integration": self.enable_audit_integration,
            "max_versions": self.max_versions,
            "history_retention_days": self.history_retention_days,
            "snapshot_fields": self.snapshot_fields,
            "exclude_fields": self.exclude_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionConfig":
        """Tạo VersionConfig từ dict."""
        return cls(
            entity_type=data.get("entity_type", ""),
            enable_versioning=data.get("enable_versioning", True),
            enable_soft_delete=data.get("enable_soft_delete", True),
            enable_history=data.get("enable_history", True),
            enable_audit_integration=data.get("enable_audit_integration", True),
            max_versions=data.get("max_versions", 0),
            history_retention_days=data.get("history_retention_days", 0),
            snapshot_fields=data.get("snapshot_fields", []),
            exclude_fields=data.get("exclude_fields", []),
        )


# ===========================================================================
# HistoryRecord
# ===========================================================================


@dataclass
class HistoryRecord:
    """
    Một bản ghi lịch sử của entity — immutable snapshot.

    Lưu trữ snapshot của entity tại một thời điểm/version cụ thể.
    History records là IMMUTABLE — không thể sửa/xóa sau khi insert.

    Attributes:
        id: UUID định danh duy nhất
        entity_type: Tên entity
        entity_id: ID của entity
        version: Số version (tăng dần từ 1)
        snapshot: Dữ liệu snapshot của entity tại version này (dict)
        operation: Loại thao tác tạo ra record này
        changed_fields: Các trường bị thay đổi so với version trước
        created_at: Thời điểm tạo record (UTC)
        created_by: User/system thực hiện thao tác
        immutable_hash: SHA-256 hash cho tamper-evidence
    """

    entity_type: str
    entity_id: str
    version: int
    snapshot: dict[str, Any]
    operation: OperationType
    created_by: str
    id: str = ""
    changed_fields: list[str] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    immutable_hash: str = ""

    def __post_init__(self) -> None:
        """Validate history record sau khi khởi tạo."""
        if self.version < 1:
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_NUMBER, version=self.version)
        if not self.entity_type or not self.entity_type.strip():
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_CONFIG, field="entity_type")
        if not self.entity_id or not self.entity_id.strip():
            EM.raise_error(ErrorCode.MDC-F25_HISTORY_RECORD_NOT_FOUND, field="entity_id")
        # Auto-generate immutable hash nếu chưa có
        if not self.immutable_hash:
            self.immutable_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """
        Tính toán SHA-256 hash cho record này (tamper-evidence).

        Returns:
            SHA-256 hash string
        """
        data = {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
            "snapshot": self.snapshot,
            "operation": self.operation.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_hash(self) -> bool:
        """
        Xác minh hash record có đúng không (tamper detection).

        Returns:
            True nếu hash khớp, False nếu bị tamper
        """
        return self.immutable_hash == self._compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển history record sang dict format."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
            "snapshot": self.snapshot,
            "operation": self.operation.value,
            "changed_fields": self.changed_fields,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "immutable_hash": self.immutable_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryRecord":
        """Tạo HistoryRecord từ dict."""
        return cls(
            id=data.get("id", ""),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            version=data.get("version", 1),
            snapshot=data.get("snapshot", {}),
            operation=OperationType(data.get("operation", "CREATE")),
            changed_fields=data.get("changed_fields", []),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(timezone.utc),
            created_by=data.get("created_by", "system"),
            immutable_hash=data.get("immutable_hash", ""),
        )


# ===========================================================================
# SoftDeleteMixin
# ===========================================================================


@dataclass
class SoftDeleteMixin:
    """
    Mixin cho soft delete functionality.

    Cung cấp:
    - deleted_at: Timestamp khi entity bị soft delete (None = đang active)
    - deleted_by: User thực hiện soft delete
    - is_deleted(): Kiểm tra entity có bị xóa không
    - soft_delete(): Đánh dấu entity bị xóa
    - restore(): Khôi phục entity đã bị xóa

    Attributes:
        deleted_at: Thời điểm soft delete (None nếu chưa xóa)
        deleted_by: ID của user thực hiện soft delete
    """

    deleted_at: Optional[datetime] = None
    deleted_by: str = ""

    def is_deleted(self) -> bool:
        """Kiểm tra entity có bị soft delete không."""
        return self.deleted_at is not None

    def soft_delete(self, actor: str = "system") -> None:
        """
        Đánh dấu entity bị soft delete.

        Args:
            actor: ID của user thực hiện thao tác
        """
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = actor

    def restore(self) -> None:
        """Khôi phục entity đã bị soft delete."""
        self.deleted_at = None
        self.deleted_by = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển soft delete state sang dict format."""
        return {
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": self.deleted_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SoftDeleteMixin":
        """Tạo SoftDeleteMixin từ dict."""
        deleted_at_raw = data.get("deleted_at")
        return cls(
            deleted_at=datetime.fromisoformat(deleted_at_raw)
            if deleted_at_raw
            else None,
            deleted_by=data.get("deleted_by", ""),
        )


# ===========================================================================
# VersioningCollection
# ===========================================================================


@dataclass
class VersioningCollection:
    """
    Collection chứa versioning config cho nhiều entity.

    Dùng làm output của VersioningParser và input cho Stack Emitters.

    Attributes:
        configs: Danh sách VersionConfig cho từng entity
        history_records: Danh sách HistoryRecord (từ existing data)
    """

    configs: list[VersionConfig] = field(default_factory=list)
    history_records: list[HistoryRecord] = field(default_factory=list)

    def add_config(self, config: VersionConfig) -> None:
        """Thêm versioning config cho một entity."""
        # Kiểm tra duplicate entity_type
        for existing in self.configs:
            if existing.entity_type == config.entity_type:
                EM.raise_error(
                    ErrorCode.MDC-F25_INVALID_VERSION_CONFIG,
                    entity_type=config.entity_type,
                    message=f"VersionConfig cho entity_type '{config.entity_type}' đã tồn tại",
                )
        self.configs.append(config)

    def get_config_by_entity_type(self, entity_type: str) -> Optional[VersionConfig]:
        """Tìm versioning config theo entity_type."""
        for config in self.configs:
            if config.entity_type == entity_type:
                return config
        return None

    def add_history_record(self, record: HistoryRecord) -> None:
        """Thêm history record vào collection."""
        self.history_records.append(record)

    def get_history_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[HistoryRecord]:
        """Lọc history records cho một entity cụ thể."""
        return [
            r
            for r in self.history_records
            if r.entity_type == entity_type and r.entity_id == entity_id
        ]

    def get_latest_version(self, entity_type: str, entity_id: str) -> int:
        """
        Lấy version mới nhất của một entity.

        Returns:
            Version number, 0 nếu không có history
        """
        records = self.get_history_for_entity(entity_type, entity_id)
        if not records:
            return 0
        return max(r.version for r in records)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "configs": [c.to_dict() for c in self.configs],
            "history_records": [r.to_dict() for r in self.history_records],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersioningCollection":
        """Tạo VersioningCollection từ dict."""
        result = cls()
        result.configs = [
            VersionConfig.from_dict(c) for c in data.get("configs", [])
        ]
        result.history_records = [
            HistoryRecord.from_dict(r) for r in data.get("history_records", [])
        ]
        return result
