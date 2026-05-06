# coding: utf-8
"""
Mô-đun FastAPI emitter cho Audit Trail & Compliance Generator (CP14).

Emit code FastAPI cho audit service, middleware, và migration.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.emitters.core.audit.models import (
    AuditComplianceCollection,
)


class FastAPIAuditComplianceEmitter:
    """
    Emitter sinh code FastAPI cho audit trail & compliance.

    Methods:
        generate(): Generate toàn bộ files
        generate_service(): Sinh AuditService
        generate_models(): Sinh Pydantic models
        generate_middleware(): Sinh audit middleware
        generate_migrations(): Sinh migration SQL
    """

    def __init__(self, collection: AuditComplianceCollection | None = None) -> None:
        """
        Init emitter.

        Args:
            collection: AuditComplianceCollection (optional)
        """
        self.collection = collection or AuditComplianceCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files FastAPI.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_models())
        result.update(self.generate_middleware())
        result.update(self.generate_migrations())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Sinh AuditService class."""
        code = '''"""Audit Service — Service quản lý audit trail và compliance."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class AuditLog(Base):  # type: ignore
    """SQLAlchemy model cho audit log entries."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    action = Column(String(20), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(200), nullable=False)
    actor_id = Column(String(200), nullable=False)
    actor_type = Column(String(20), nullable=False, default="system")
    tenant_id = Column(String(100), nullable=False)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    immutable_hash = Column(String(64), nullable=False)
    archived = Column(Integer, default=0)


class AuditService:
    """Service quản lý audit trail và compliance enforcement."""

    def __init__(self, db: Session):
        """
        Init audit service.

        Args:
            db: SQLAlchemy session
        """
        self._db = db

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        actor_type: str = "system",
        tenant_id: str = "default",
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Ghi audit log entry.

        Args:
            action: Hành động (CREATE/UPDATE/DELETE/...)
            entity_type: Tên entity
            entity_id: ID entity
            actor_id: ID người thực hiện
            actor_type: Loại actor (user/system/background_job)
            tenant_id: Tenant scope
            old_values: Giá trị cũ (optional)
            new_values: Giá trị mới (optional)
            metadata: Metadata mở rộng (optional)

        Returns:
            ID của audit log entry vừa tạo
        """
        import hashlib
        import json

        entry_id = str(uuid4())
        now = datetime.now(timezone.utc)

        # Tính toán hash cho tamper-evidence
        hash_data = {
            "id": entry_id,
            "timestamp": now.isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "tenant_id": tenant_id,
            "old_values": old_values or {},
            "new_values": new_values or {},
            "metadata": metadata or {},
        }
        immutable_hash = hashlib.sha256(
            json.dumps(hash_data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        entry = AuditLog(
            id=entry_id,
            timestamp=now,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_type=actor_type,
            tenant_id=tenant_id,
            old_values=json.dumps(old_values or {}),
            new_values=json.dumps(new_values or {}),
            metadata_json=json.dumps(metadata or {}),
            immutable_hash=immutable_hash,
        )
        self._db.add(entry)
        self._db.commit()
        return entry_id

    def query(
        self,
        entity_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Query audit logs.

        Args:
            entity_type: Filter theo entity type (optional)
            actor_id: Filter theo actor (optional)
            tenant_id: Filter theo tenant (optional)
            limit: Số lượng max trả về

        Returns:
            List audit log entries
        """
        query = self._db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if actor_id:
            query = query.filter(AuditLog.actor_id == actor_id)
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
'''
        return {"src/services/audit_service.py": code}

    def generate_models(self) -> Dict[str, str]:
        """Sinh Pydantic models."""
        code = '''"""Pydantic models cho audit trail API."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """Schema cho tạo audit log entry."""
    action: str = Field(..., description="Hành động (CREATE/UPDATE/DELETE/...)")
    entity_type: str = Field(..., description="Tên entity")
    entity_id: str = Field(..., description="ID entity")
    actor_id: str = Field(..., description="ID người thực hiện")
    actor_type: str = Field(default="system", description="Loại actor")
    tenant_id: str = Field(default="default", description="Tenant scope")
    old_values: Optional[Dict[str, Any]] = Field(default=None)
    new_values: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class AuditLogResponse(BaseModel):
    """Schema cho response audit log."""
    id: str
    timestamp: datetime
    action: str
    entity_type: str
    entity_id: str
    actor_id: str
    actor_type: str
    tenant_id: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    immutable_hash: str

    class Config:
        from_attributes = True


class AuditQueryParams(BaseModel):
    """Schema cho query params audit log."""
    entity_type: Optional[str] = None
    actor_id: Optional[str] = None
    tenant_id: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
'''
        return {"src/schemas/audit_schemas.py": code}

    def generate_middleware(self) -> Dict[str, str]:
        """Sinh audit middleware."""
        code = '''"""Audit Middleware — Tự động ghi audit log cho các endpoint."""
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware tự động ghi audit log cho mutations."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Xử lý request và ghi audit log cho mutations.

        Args:
            request: HTTP request
            call_next: Next handler

        Returns:
            HTTP response
        """
        # Chỉ audit cho mutation methods
        audit_methods = {"POST", "PUT", "PATCH", "DELETE"}
        should_audit = request.method in audit_methods

        if not should_audit:
            return await call_next(request)

        # Extract thông tin từ request
        actor_id = getattr(request.state, "user_id", "anonymous")
        tenant_id = getattr(request.state, "tenant_id", "default")
        entity_type = getattr(request.state, "entity_type", "unknown")
        entity_id = getattr(request.state, "entity_id", "unknown")

        # Call next handler
        response = await call_next(request)

        # Ghi audit log (async background task)
        if response.status_code < 400:
            # TODO: Inject AuditService và gọi log()
            pass

        return response
'''
        return {"src/middleware/audit_middleware.py": code}

    def generate_migrations(self) -> Dict[str, str]:
        """Sinh migration SQL."""
        code = """-- Migration: Tạo bảng audit_logs
-- CP14: Audit Trail & Compliance Generator

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    action VARCHAR(20) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(200) NOT NULL,
    actor_id VARCHAR(200) NOT NULL,
    actor_type VARCHAR(20) NOT NULL DEFAULT 'system',
    tenant_id VARCHAR(100) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    metadata_json TEXT,
    immutable_hash VARCHAR(64) NOT NULL,
    archived INTEGER DEFAULT 0
);

-- Index cho query performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
"""
        return {"migrations/001_create_audit_logs.sql": code}