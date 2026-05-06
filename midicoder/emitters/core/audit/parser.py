# coding: utf-8
"""
Mô-đun parser cho Audit Trail & Compliance Generator (CP14).

Parse YAML DSL thành AuditComplianceCollection chứa:
- AuditRule: Rules xác định khi nào cần ghi audit log
- ComplianceControl: Controls cho compliance enforcement

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.audit.models import (
    AuditActionType,
    AuditComplianceCollection,
    AuditLevel,
    AuditRule,
    ComplianceControl,
    ControlType,
    EnforcementLevel,
    StandardType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AuditComplianceParser:
    """
    Parser cho DSL audit compliance.

    Parse YAML DSL thành AuditComplianceCollection.

    Ví dụ DSL:
        audit_rules:
          - id: "ledger_audit"
            name: "Audit Ledger Entries"
            entity_types: ["LedgerEntry"]
            actions: ["CREATE", "UPDATE"]
            audit_level: "detailed"
            retention_days: 2555
            archive_after_days: 365
            compliance_tags: ["sox", "hipaa"]
        compliance_controls:
          - id: "sox_immutable"
            name: "SOX Immutable Ledger"
            standard: "sox"
            control_type: "preventive"
            enforcement_level: "both"
            audit_rule_id: "ledger_audit"
    """

    def parse(self, raw: str) -> AuditComplianceCollection:
        """
        Parse YAML DSL string thành AuditComplianceCollection.

        Args:
            raw: YAML string chứa audit_rules và compliance_controls

        Returns:
            AuditComplianceCollection chứa rules và controls

        Raises:
            MidicoderError: Nếu YAML không hợp lệ hoặc parse thất bại
        """
        if not raw or not raw.strip():
            return AuditComplianceCollection()

        # Parse YAML
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.CP08_DSL_PARSE_ERROR,
                message=f"Lỗi parse YAML audit compliance: {e}",
                error=str(e)
            )

        # YAML comment-only hoặc null → treat as empty collection
        if data is None:
            return AuditComplianceCollection()
        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP08_DSL_PARSE_ERROR,
                message="DSL audit compliance phải là YAML mapping"
            )

        collection = AuditComplianceCollection()

        # Parse audit_rules
        raw_rules = data.get("audit_rules", [])
        if isinstance(raw_rules, list):
            for rule_data in raw_rules:
                rule = self._parse_audit_rule(rule_data)
                collection.add_rule(rule)

        # Parse compliance_controls
        raw_controls = data.get("compliance_controls", [])
        if isinstance(raw_controls, list):
            for control_data in raw_controls:
                control = self._parse_compliance_control(control_data)
                collection.add_control(control)

        return collection

    def _parse_audit_rule(self, data: dict[str, Any]) -> AuditRule:
        """
        Parse dict thành AuditRule.

        Args:
            data: Dict chứa thông tin audit rule

        Returns:
            AuditRule instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.CP08_DSL_PARSE_ERROR, message="Audit rule phải là YAML mapping")

        # Parse actions
        actions_raw = data.get("actions", [])
        actions = []
        for action_str in actions_raw:
            try:
                actions.append(AuditActionType(action_str))
            except ValueError:
                EM.raise_error(
                    ErrorCode.CP14_AUDIT_INVALID_ACTION,
                    action=action_str,
                    valid_actions=[a.value for a in AuditActionType]
                )

        # Parse audit_level
        level_str = data.get("audit_level", "basic")
        try:
            audit_level = AuditLevel(level_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_INVALID_LEVEL,
                level=level_str,
                valid_levels=[l.value for l in AuditLevel]
            )

        return AuditRule(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity_types=data.get("entity_types", []),
            actions=actions,
            enabled=data.get("enabled", True),
            audit_level=audit_level,
            retention_days=data.get("retention_days", 365),
            archive_after_days=data.get("archive_after_days", 90),
            compliance_tags=data.get("compliance_tags", []),
            description=data.get("description", ""),
        )

    def _parse_compliance_control(self, data: dict[str, Any]) -> ComplianceControl:
        """
        Parse dict thành ComplianceControl.

        Args:
            data: Dict chứa thông tin compliance control

        Returns:
            ComplianceControl instance

        Raises:
            MidicoderError: Nếu dữ liệu không hợp lệ
        """
        if not isinstance(data, dict):
            EM.raise_error(ErrorCode.CP08_DSL_PARSE_ERROR, message="Compliance control phải là YAML mapping")

        # Parse standard
        standard_str = data.get("standard", "custom")
        try:
            standard = StandardType(standard_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_CONTROL_INVALID_STANDARD,
                standard=standard_str,
                valid_standards=[s.value for s in StandardType]
            )

        # Parse control_type
        control_type_str = data.get("control_type", "preventive")
        try:
            control_type = ControlType(control_type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_CONTROL_INVALID_TYPE,
                control_type=control_type_str,
                valid_types=[t.value for t in ControlType]
            )

        # Parse enforcement_level
        enforcement_str = data.get("enforcement_level", "runtime")
        try:
            enforcement = EnforcementLevel(enforcement_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_CONTROL_INVALID_ENFORCEMENT,
                enforcement=enforcement_str,
                valid_levels=[e.value for e in EnforcementLevel]
            )

        return ComplianceControl(
            id=data.get("id", ""),
            name=data.get("name", ""),
            standard=standard,
            control_type=control_type,
            enforcement_level=enforcement,
            enabled=data.get("enabled", True),
            audit_rule_id=data.get("audit_rule_id"),
            description=data.get("description", ""),
        )