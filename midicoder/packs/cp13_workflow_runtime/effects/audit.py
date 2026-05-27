# coding: utf-8
"""
Mô-đun Audit Effect - tích hợp với CP14 Audit Runtime.

Cung cấp:
- AuditEffect: Effect cho audit logging, wire vào CP14 AuditLogger

Sau khi tích hợp:
- AuditEffect.execute() gọi CP14 AuditLogger.log() để ghi audit trail
- Validate entity_type, entity_id trước khi log
- Hỗ trợ RX11 compliance (immutable hash tamper-evidence)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp14_audit_compliance.audit_engine import AuditLogger
from midicoder.packs.cp14_audit_compliance.models import AuditActionType, AuditTrail

from .base import EffectResult


class AuditEffect:
    """
    Effect executor cho audit logging.

    Log audit trail khi transition fire, tích hợp với CP14 AuditLogger.

    Usage:
        logger = AuditLogger(log_dir=".midicoder/audit_logs")
        effect = AuditEffect(action="workflow_transition", logger=logger)
        result = effect.execute(data={
            "entity_type": "Order",
            "entity_id": "order_123",
            "actor_id": "user_456",
            "tenant_id": "tenant_1",
        })
    """

    def __init__(
        self,
        action: str | None = None,
        logger: AuditLogger | None = None,
    ) -> None:
        """
        Khởi tạo AuditEffect.

        Args:
            action: Hành động audit (tạo AuditActionType từ string)
            logger: CP14 AuditLogger instance (optional, nếu None thì dùng in-memory fallback)
        """
        self.action = action
        self._logger = logger

    def execute(self, data: dict[str, Any]) -> EffectResult:
        """
        Execute audit logging effect - gọi CP14 AuditLogger.

        Validate các fields bắt buộc và ghi audit trail vào CP14 logger.

        Args:
            data: Data dictionary với các fields:
                - entity_type (required): Tên entity bị ảnh hưởng
                - entity_id (required): ID của entity
                - actor_id (optional): ID người thực hiện (default: "system")
                - actor_type (optional): Loại actor (default: "system")
                - tenant_id (optional): Tenant scope (default: "default")
                - old_values (optional): Giá trị cũ
                - new_values (optional): Giá trị mới

        Returns:
            EffectResult với success/failure info

        Raises:
            Không throw - trả về EffectResult.failure() nếu validation fail
        """
        # Extract và validate fields bắt buộc
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")

        if not entity_type or not str(entity_type).strip():
            return EffectResult.failure(
                error="AuditEffect: entity_type là bắt buộc nhưng không được cung cấp"
            )

        if not entity_id or not str(entity_id).strip():
            return EffectResult.failure(
                error="AuditEffect: entity_id là bắt buộc nhưng không được cung cấp"
            )

        # Parse action
        action_str = self.action or data.get("action", "CUSTOM")
        try:
            action = AuditActionType(action_str)
        except ValueError:
            action = AuditActionType.CUSTOM

        # Extract optional fields
        actor_id = data.get("actor_id", "system")
        actor_type = data.get("actor_type", "system")
        tenant_id = data.get("tenant_id", "default")
        old_values = data.get("old_values", {})
        new_values = data.get("new_values", {})
        metadata = data.get("metadata", {})

        try:
            # Tạo audit trail entry
            entry = AuditTrail(
                action=action,
                entity_type=str(entity_type),
                entity_id=str(entity_id),
                actor_id=str(actor_id),
                actor_type=str(actor_type),
                tenant_id=str(tenant_id),
                old_values=dict(old_values),
                new_values=dict(new_values),
                metadata=dict(metadata),
            )

            # Ghi vào CP14 AuditLogger
            if self._logger:
                self._logger.log(entry)
            # Nếu không có logger, vẫn tạo entry thành công (in-memory fallback)

            return EffectResult.success(
                data={
                    "audit": {
                        "action": action.value,
                        "entity_type": str(entity_type),
                        "entity_id": str(entity_id),
                        "actor_id": str(actor_id),
                        "tenant_id": str(tenant_id),
                        "immutable_hash": entry.immutable_hash,
                    }
                },
                message=f"Đã ghi audit log: {action.value} trên {entity_type}:{entity_id}",
            )

        except Exception as e:
            return EffectResult.failure(
                error=f"AuditEffect: Không thể ghi audit log: {str(e)}"
            )
