# coding: utf-8
"""
Mô-đun parser cho Versioning & History Generator (CP43).

Parse YAML DSL hoặc MIR metadata thành VersioningCollection chứa:
- VersionConfig: Cấu hình versioning cho từng entity
- HistoryRecord: Lịch sử thay đổi (từ existing data)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.packs.cp_full_versioning.models import (
    HistoryRecord,
    OperationType,
    VersionConfig,
    VersioningCollection,
)


class VersioningParser:
    """
    Parser cho DSL versioning & history.

    Parse YAML DSL hoặc MIR metadata thành VersioningCollection.

    Ví dụ DSL:
        versioning:
          entities:
            - entity_type: "Order"
              enable_versioning: true
              enable_soft_delete: true
              enable_history: true
              enable_audit_integration: true
              max_versions: 0
              history_retention_days: 365
            - entity_type: "Product"
              enable_versioning: true
              enable_soft_delete: false
    """

    def parse(self, raw: str) -> VersioningCollection:
        """
        Parse YAML DSL string thành VersioningCollection.

        Args:
            raw: YAML string chứa versioning config

        Returns:
            VersioningCollection chứa configs và history records
        """
        if not raw or not raw.strip():
            return VersioningCollection()

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(ErrorCode.MDC-F25_DSL_PARSE_ERROR, error=str(e))

        # YAML comment-only hoặc null → treat as empty collection
        if data is None:
            return VersioningCollection()
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.MDC-F25_DSL_PARSE_ERROR, reason="DSL versioning phải là YAML mapping")

        collection = VersioningCollection()

        # Parse versioning config
        versioning_data = data.get("versioning", {})
        if isinstance(versioning_data, dict):
            entities_raw = versioning_data.get("entities", [])
            if isinstance(entities_raw, list):
                for entity_data in entities_raw:
                    config = self._parse_version_config(entity_data)
                    collection.add_config(config)

        # Parse existing history records (nếu có)
        history_raw = data.get("history_records", [])
        if isinstance(history_raw, list):
            for record_data in history_raw:
                record = self._parse_history_record(record_data)
                collection.add_history_record(record)

        return collection

    def parse_from_metadata(self, metadata: dict[str, Any]) -> VersioningCollection:
        """
        Parse versioning config từ MIR metadata (entities list).

        Auto-generate versioning config cho tất cả entities có trong MIR.
        Theo requirement: auto cho tất cả entities.

        Args:
            metadata: MIR metadata dict chứa entities list

        Returns:
            VersioningCollection với config auto-generate cho mỗi entity
        """
        collection = VersioningCollection()

        entities = metadata.get("entities", [])
        if isinstance(entities, list):
            for entity in entities:
                if isinstance(entity, dict):
                    entity_type = entity.get("id", entity.get("name", ""))
                    if entity_type:
                        config = VersionConfig(entity_type=entity_type)
                        collection.add_config(config)

        return collection

    def _parse_version_config(self, data: dict[str, Any]) -> VersionConfig:
        """
        Parse dict thành VersionConfig.

        Args:
            data: Dict chứa thông tin versioning config

        Returns:
            VersionConfig instance
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.MDC-F25_DSL_PARSE_ERROR, reason="Versioning config phải là YAML mapping")

        entity_type = data.get("entity_type", "")
        if not entity_type:
            EM.raise_error(ErrorCode.MDC-F25_INVALID_VERSION_CONFIG, field="entity_type")

        return VersionConfig(
            entity_type=entity_type,
            enable_versioning=data.get("enable_versioning", True),
            enable_soft_delete=data.get("enable_soft_delete", True),
            enable_history=data.get("enable_history", True),
            enable_audit_integration=data.get("enable_audit_integration", True),
            max_versions=data.get("max_versions", 0),
            history_retention_days=data.get("history_retention_days", 0),
            snapshot_fields=data.get("snapshot_fields", []),
            exclude_fields=data.get("exclude_fields", []),
        )

    def _parse_history_record(self, data: dict[str, Any]) -> HistoryRecord:
        """
        Parse dict thành HistoryRecord.

        Args:
            data: Dict chứa thông tin history record

        Returns:
            HistoryRecord instance
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.MDC-F25_DSL_PARSE_ERROR, reason="History record phải là YAML mapping")

        operation_str = data.get("operation", "CREATE")
        try:
            operation = OperationType(operation_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F25_INVALID_VERSION_CONFIG,
                operation=operation_str,
                message=f"Operation không hợp lệ: {operation_str}. Chọn trong: {[o.value for o in OperationType]}",
            )

        return HistoryRecord(
            id=data.get("id", ""),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            version=data.get("version", 1),
            snapshot=data.get("snapshot", {}),
            operation=operation,
            changed_fields=data.get("changed_fields", []),
            created_by=data.get("created_by", "system"),
            immutable_hash=data.get("immutable_hash", ""),
        )
