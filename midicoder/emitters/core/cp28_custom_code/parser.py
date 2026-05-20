# coding: utf-8
"""
Mô-đun parser cho Custom Code Injection Generator (CP28).

Parse DSL custom_code nodes từ YAML dict / MIR metadata thành CustomCodeCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeBlock,
    CustomCodeCollection,
    Hook,
    PatchRule,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class CustomCodeParser:
    """
    Parser cho DSL custom_code nodes.

    Parse YAML DSL hoặc dict metadata thành CustomCodeCollection.

    Ví dụ DSL:
        custom_code_blocks:
          - id: inject_payment_validator
            target: "app/commands/{command_snake}_validator.py"
            code: |
              def validate_payment(self):
                  pass
            position: after
            stack: fastapi
            language: python
        hooks:
          - id: add_logging
            event: on_template_render
            action: inject
            code: "import logging"
        patch_rules:
          - id: add_tenant_prefix
            target_pattern: "def (create|update)_(\\w+)\\("
            replacement: "def \\1_\\2_tenant_safe("
            enabled: true
    """

    def parse(self, raw: str | dict[str, Any] | None) -> CustomCodeCollection:
        """
        Parse YAML string hoặc dict thành CustomCodeCollection.

        Args:
            raw: YAML string hoặc dict chứa custom_code definitions

        Returns:
            CustomCodeCollection chứa blocks, hooks, patch_rules

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        # Xử lý input None hoặc rỗng
        if raw is None:
            return CustomCodeCollection()

        if isinstance(raw, str):
            if not raw or not raw.strip():
                return CustomCodeCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.CP28_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML custom_code nodes: {e}",
                    error=str(e),
                )
            if data is None:
                return CustomCodeCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return CustomCodeCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP28_DSL_PARSE_ERROR,
                message="DSL custom_code nodes phải là YAML mapping",
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any] | None) -> CustomCodeCollection:
        """
        Parse từ MIR metadata dict.

        MIR metadata có thể chứa các key:
        'custom_code_blocks', 'hooks', 'patch_rules'.

        Args:
            metadata: MIR metadata dict

        Returns:
            CustomCodeCollection
        """
        if not metadata:
            return CustomCodeCollection()

        return self._parse_from_dict(metadata)

    def _parse_from_dict(self, data: dict[str, Any]) -> CustomCodeCollection:
        """Parse từ dict đã load."""
        collection = CustomCodeCollection()

        # Parse custom_code_blocks
        blocks_data = data.get("custom_code_blocks", [])
        if isinstance(blocks_data, list):
            for block_data in blocks_data:
                if isinstance(block_data, dict):
                    block = self._parse_block(block_data)
                    collection.add_block(block)

        # Parse hooks
        hooks_data = data.get("hooks", [])
        if isinstance(hooks_data, list):
            for hook_data in hooks_data:
                if isinstance(hook_data, dict):
                    hook = self._parse_hook(hook_data)
                    collection.add_hook(hook)

        # Parse patch_rules
        rules_data = data.get("patch_rules", [])
        if isinstance(rules_data, list):
            for rule_data in rules_data:
                if isinstance(rule_data, dict):
                    rule = self._parse_patch_rule(rule_data)
                    collection.add_patch_rule(rule)

        return collection

    def _parse_block(self, data: dict[str, Any]) -> CustomCodeBlock:
        """Parse custom code block definition."""
        return CustomCodeBlock(
            id=data.get("id", ""),
            target=data.get("target", ""),
            code=data.get("code", ""),
            position=data.get("position", "before"),
            stack=data.get("stack"),
            language=data.get("language", "python"),
        )

    def _parse_hook(self, data: dict[str, Any]) -> Hook:
        """Parse hook definition."""
        return Hook(
            id=data.get("id", ""),
            event=data.get("event", ""),
            action=data.get("action", ""),
            condition=data.get("condition"),
            code=data.get("code"),
        )

    def _parse_patch_rule(self, data: dict[str, Any]) -> PatchRule:
        """Parse patch rule definition."""
        return PatchRule(
            id=data.get("id", ""),
            target_pattern=data.get("target_pattern", ""),
            replacement=data.get("replacement", ""),
            enabled=data.get("enabled", True),
            stack=data.get("stack"),
        )
