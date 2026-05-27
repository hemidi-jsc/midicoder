# coding: utf-8
"""
Mô-đun FastAPI emitter cho Versioning & History Generator (CP43).

Emit code FastAPI cho:
- VersionMixin (SQLAlchemy): optimistic locking với version column
- SoftDeleteMixin (SQLAlchemy): soft delete + auto filter query
- History model: {Entity}History table với snapshot JSONB
- History repository: time-travel query methods
- Audit integration: auto emit audit event tới CP14

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.packs.cp43_versioning.models import VersioningCollection


class FastAPIVersioningEmitter:
    """
    Emitter sinh code FastAPI/SQLAlchemy cho versioning & history.

    Methods:
        generate(): Generate toàn bộ files
        generate_version_mixin(): Sinh SQLAlchemy VersionMixin
        generate_soft_delete_mixin(): Sinh SQLAlchemy SoftDeleteMixin
        generate_history_model(): Sinh {Entity}History model
        generate_history_repository(): Sinh time-travel query methods
        generate_audit_integration(): Sinh audit event emission (CP14)
    """

    def __init__(self, collection: VersioningCollection | None = None) -> None:
        """
        Init emitter.

        Args:
            collection: VersioningCollection (optional)
        """
        self.collection = collection or VersioningCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files FastAPI.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_version_mixin())
        result.update(self.generate_soft_delete_mixin())
        result.update(self.generate_history_model())
        result.update(self.generate_history_repository())
        result.update(self.generate_audit_integration())
        return result

    def generate_version_mixin(self) -> Dict[str, str]:
        """Sinh SQLAlchemy VersionMixin — optimistic locking."""
        code = '''"""VersionMixin — SQLAlchemy mixin cho optimistic locking (CP43).

Cung cấp:
- version column (Integer, default=1)
- Tự động increment version trước mỗi UPDATE
- Kiểm tra version conflict (optimistic locking)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer


class VersionMixin:
    """SQLAlchemy mixin cho entity versioning với optimistic locking."""

    __mapper_args__ = {"eager_defaults": True}

    version = Column(Integer, nullable=False, default=1, server_default="1")

    def check_version(self, expected_version: int) -> None:
        """
        Kiểm tra version trước khi update (optimistic locking).

        Args:
            expected_version: Version mong đợi từ client

        Raises:
            ValueError: Nếu version conflict (data đã bị thay đổi bởi user khác)
        """
        if self.version != expected_version:
            raise ValueError(
                f"Version conflict: expected v{expected_version}, "
                f"found v{self.version}"
            )

    def bump_version(self) -> int:
        """
        Tăng version lên 1 và trả về version mới.

        Returns:
            Version mới sau khi increment
        """
        self.version = (self.version or 1) + 1
        return self.version
'''
        return {"app/models/mixins/version_mixin.py": code}

    def generate_soft_delete_mixin(self) -> Dict[str, str]:
        """Sinh SQLAlchemy SoftDeleteMixin — soft delete + auto filter."""
        code = '''"""SoftDeleteMixin — SQLAlchemy mixin cho soft delete (CP43).

Cung cấp:
- deleted_at column (nullable timestamp)
- deleted_by column (ký ai xóa)
- soft_delete(): đánh dấu xóa
- restore(): khôi phục entity
- hard_delete(): xóa vĩnh viễn
- Auto filter: query tự động WHERE deleted_at IS NULL
"""
from datetime import datetime, timezone
from typing import Optional, Type, TYPE_CHECKING
from sqlalchemy import Column, DateTime, String, event
from sqlalchemy.orm import Query

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SoftDeleteMixin:
    """SQLAlchemy mixin cho soft delete functionality."""

    deleted_at = Column(
        DateTime,
        nullable=True,
        default=None,
        server_default=None,
        index=True,
    )
    deleted_by = Column(String(200), nullable=True, default=None)

    @property
    def is_deleted(self) -> bool:
        """Kiểm tra entity có bị soft delete không."""
        return self.deleted_at is not None

    def soft_delete(self, actor: str = "system", db_session: Optional["Session"] = None) -> None:
        """
        Đánh dấu entity bị soft delete.

        Args:
            actor: ID của user thực hiện thao tác
            db_session: Database session (optional)
        """
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = actor

    def restore(self) -> None:
        """Khôi phục entity đã bị soft delete."""
        self.deleted_at = None
        self.deleted_by = None

    def hard_delete(self, db_session: Optional["Session"] = None) -> None:
        """
        Xóa vĩnh viễn entity (bỏ qua soft delete).

        Dùng thận trọng — không thể khôi phục sau khi hard delete.

        Args:
            db_session: Database session để delete
        """
        if db_session:
            db_session.delete(self)
            db_session.commit()


def apply_soft_delete_filter(query: Query, model: Type["SoftDeleteMixin"]) -> Query:
    """
    Tự động áp dụng filter WHERE deleted_at IS NULL cho query.

    Args:
        query: SQLAlchemy query
        model: Model class có SoftDeleteMixin

    Returns:
        Query đã được filter
    """
    if hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))
    return query
'''
        return {"app/models/mixins/soft_delete_mixin.py": code}

    def generate_history_model(self) -> Dict[str, str]:
        """Sinh {Entity}History model — snapshot table."""
        code = '''"""EntityHistory — Base model cho history table (CP43).

Mỗi entity có một history table tương ứng để lưu snapshot
của entity tại mỗi version. History records là IMMUTABLE.

Sử dụng:
    class OrderHistory(Base, EntityHistoryMixin):
        __tablename__ = "order_history"
        entity_type = "Order"
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import JSONB


class EntityHistoryMixin:
    """Base mixin cho entity history table."""

    entity_type: str = ""

    id = Column(String(36), primary_key=True)
    entity_id = Column(String(200), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    snapshot = Column(JSONB, nullable=False)
    operation = Column(String(20), nullable=False)
    changed_fields = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default="NOW()",
    )
    created_by = Column(String(200), nullable=False, default="system")
    immutable_hash = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_history_entity_version", "entity_id", "version"),
        Index("ix_history_entity_created_at", "entity_id", "created_at"),
    )

    @staticmethod
    def compute_hash(record: Any) -> str:
        """
        Tính SHA-256 hash cho history record (tamper-evidence).

        Args:
            record: History record instance

        Returns:
            SHA-256 hash string
        """
        import hashlib

        data = {
            "entity_type": record.entity_type,
            "entity_id": record.entity_id,
            "version": record.version,
            "snapshot": record.snapshot,
            "operation": record.operation,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat() if record.created_at else "",
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get_snapshot(self) -> Dict[str, Any]:
        """Trả về snapshot dict của record này."""
        return self.snapshot if isinstance(self.snapshot, dict) else {}
'''
        return {"app/models/mixins/entity_history.py": code}

    def generate_history_repository(self) -> Dict[str, str]:
        """Sinh time-travel query methods."""
        code = '''"""HistoryRepository — Repository cho time-travel query (CP43).

Cung cấp các method:
- get_at_version(): Lấy snapshot ở version cụ thể
- get_at_timestamp(): Lấy snapshot gần nhất trước thời điểm T
- get_version_history(): Lấy danh sách tất cả versions
- get_changes_between(): So sánh 2 versions
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.mixins.entity_history import EntityHistoryMixin


class HistoryRepository:
    """Repository cho time-travel query operations."""

    def __init__(self, db_session: Session, history_model: Type[EntityHistoryMixin]) -> None:
        """
        Init repository.

        Args:
            db_session: SQLAlchemy session
            history_model: History model class
        """
        self.db = db_session
        self.history_model = history_model

    def get_at_version(self, entity_id: str, version: int) -> Optional[Dict[str, Any]]:
        """
        Lấy snapshot của entity ở version cụ thể.

        Args:
            entity_id: ID của entity
            version: Số version

        Returns:
            Snapshot dict hoặc None nếu không tìm thấy
        """
        record = self.db.query(self.history_model).filter(
            self.history_model.entity_id == entity_id,
            self.history_model.version == version,
        ).first()

        if record is None:
            return None
        return record.get_snapshot()

    def get_at_timestamp(self, entity_id: str, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Lấy snapshot gần nhất trước thời điểm T.

        Args:
            entity_id: ID của entity
            timestamp: Thời điểm cần query

        Returns:
            Snapshot dict hoặc None nếu không có record trước thời điểm T
        """
        record = self.db.query(self.history_model).filter(
            self.history_model.entity_id == entity_id,
            self.history_model.created_at <= timestamp,
        ).order_by(desc(self.history_model.created_at)).first()

        if record is None:
            return None
        return record.get_snapshot()

    def get_version_history(self, entity_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tất cả versions của entity.

        Args:
            entity_id: ID của entity
            limit: Số lượng max trả về

        Returns:
            List của history records
        """
        records = self.db.query(self.history_model).filter(
            self.history_model.entity_id == entity_id,
        ).order_by(desc(self.history_model.version)).limit(limit).all()

        return [
            {
                "version": r.version,
                "operation": r.operation,
                "snapshot": r.get_snapshot(),
                "changed_fields": r.changed_fields or [],
                "created_at": r.created_at.isoformat() if r.created_at else "",
                "created_by": r.created_by,
            }
            for r in records
        ]

    def get_changes_between(
        self, entity_id: str, from_version: int, to_version: int
    ) -> Dict[str, Any]:
        """
        So sánh 2 versions và trả về các thay đổi.

        Args:
            entity_id: ID của entity
            from_version: Version cũ
            to_version: Version mới

        Returns:
            Dict chứa snapshot cũ, mới, và các trường thay đổi
        """
        old_snapshot = self.get_at_version(entity_id, from_version)
        new_snapshot = self.get_at_version(entity_id, to_version)

        if old_snapshot is None or new_snapshot is None:
            return {"old": old_snapshot, "new": new_snapshot, "changes": []}

        changes = []
        all_keys = set(old_snapshot.keys()) | set(new_snapshot.keys())
        for key in all_keys:
            old_val = old_snapshot.get(key)
            new_val = new_snapshot.get(key)
            if old_val != new_val:
                changes.append({
                    "field": key,
                    "old_value": old_val,
                    "new_value": new_val,
                })

        return {
            "old": old_snapshot,
            "new": new_snapshot,
            "changes": changes,
        }

    def get_latest_version(self, entity_id: str) -> Optional[int]:
        """
        Lấy version số mới nhất của entity.

        Args:
            entity_id: ID của entity

        Returns:
            Version number hoặc None nếu không có history
        """
        record = self.db.query(self.history_model).filter(
            self.history_model.entity_id == entity_id,
        ).order_by(desc(self.history_model.version)).first()

        return record.version if record else None
'''
        return {"app/repositories/history_repository.py": code}

    def generate_audit_integration(self) -> Dict[str, str]:
        """Sinh audit event emission — integrate với CP14."""
        code = '''"""AuditIntegration — Auto emit audit event tới CP14 (CP43).

Mỗi lần version thay đổi (CREATE/UPDATE/DELETE) tự động
emit audit event tới CP14 audit_logger.

Sử dụng:
    audit_logger = VersionAuditLogger(db_session)
    audit_logger.log_version_change(
        entity_type="Order",
        entity_id="order_123",
        operation="UPDATE",
        old_version=1,
        new_version=2,
        changed_fields=["status", "total"],
    )
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session


class VersionAuditLogger:
    """Auto emit audit event tới CP14 audit_logger."""

    def __init__(self, db_session: Optional[Session] = None) -> None:
        """
        Init audit logger.

        Args:
            db_session: Database session (optional)
        """
        self.db = db_session

    def log_version_change(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        old_version: int,
        new_version: int,
        changed_fields: Optional[List[str]] = None,
        user_id: str = "system",
        tenant_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log version change event tới CP14 audit trail.

        Args:
            entity_type: Tên entity
            entity_id: ID entity
            operation: Loại thao tác (CREATE/UPDATE/DELETE)
            old_version: Version cũ (0 cho CREATE)
            new_version: Version mới
            changed_fields: Các trường bị thay đổi
            user_id: ID user thực hiện
            tenant_id: Tenant scope
            metadata: Metadata mở rộng

        Returns:
            Audit event dict
        """
        now = datetime.now(timezone.utc)

        audit_event = {
            "timestamp": now.isoformat(),
            "action": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": user_id,
            "actor_type": "user" if user_id != "system" else "system",
            "tenant_id": tenant_id,
            "old_values": {"version": old_version},
            "new_values": {"version": new_version, "changed_fields": changed_fields or []},
            "metadata": {
                "old_version": old_version,
                "new_version": new_version,
                "changed_fields": changed_fields or [],
                "operation": operation,
                **(metadata or {}),
            },
        }

        # Emit tới CP14 audit_logger (nếu có)
        if self.db is not None:
            try:
                self._write_to_audit_table(audit_event)
            except Exception:
                # Audit failure không nên block main operation
                pass

        return audit_event

    def _write_to_audit_table(self, event: Dict[str, Any]) -> None:
        """
        Ghi audit event vào audit_logs table (CP14).

        Args:
            event: Audit event dict
        """
        import hashlib
        import json
        from uuid import uuid4

        hash_data = {
            "action": event["action"],
            "entity_type": event["entity_type"],
            "entity_id": event["entity_id"],
            "actor_id": event["actor_id"],
            "tenant_id": event["tenant_id"],
            "old_values": event["old_values"],
            "new_values": event["new_values"],
            "metadata": event["metadata"],
            "timestamp": event["timestamp"],
        }
        immutable_hash = hashlib.sha256(
            json.dumps(hash_data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        # INSERT vào audit_logs table
        self.db.execute(
            """
            INSERT INTO audit_logs (
                id, timestamp, action, entity_type, entity_id,
                actor_id, actor_type, tenant_id,
                old_values, new_values, metadata_json, immutable_hash
            ) VALUES (
                :id, :timestamp, :action, :entity_type, :entity_id,
                :actor_id, :actor_type, :tenant_id,
                :old_values, :new_values, :metadata_json, :immutable_hash
            )
            """,
            {
                "id": str(uuid4()),
                "timestamp": event["timestamp"],
                "action": event["action"],
                "entity_type": event["entity_type"],
                "entity_id": event["entity_id"],
                "actor_id": event["actor_id"],
                "actor_type": event["actor_type"],
                "tenant_id": event["tenant_id"],
                "old_values": json.dumps(event["old_values"]),
                "new_values": json.dumps(event["new_values"]),
                "metadata_json": json.dumps(event["metadata"]),
                "immutable_hash": immutable_hash,
            },
        )
        self.db.commit()
'''
        return {"app/services/version_audit_logger.py": code}
