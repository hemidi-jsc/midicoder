# coding: utf-8
"""
Mô-đun models cho Custom Code Injection Generator (CP28).

Định nghĩa các dataclass biểu diễn:
- HookEvent: Enum các sự kiện compile-time
- HookAction: Enum các hành động hook
- CustomCodeBlock: Block code tùy chỉnh để inject
- Hook: Compile-time hook để modify behavior
- PatchRule: Regex-based patch rule để transform code
- CustomCodeCollection: Collection chứa blocks, hooks, patch_rules

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.contracts.registry import ALL_STACKS
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class HookEvent(str, Enum):
    """Enum các sự kiện compile-time hook."""
    ON_BEFORE_EMIT = "on_before_emit"
    ON_AFTER_EMIT = "on_after_emit"
    ON_TEMPLATE_RENDER = "on_template_render"
    ON_FILE_WRITE = "on_file_write"

    __test__ = False  # Prevent pytest collection


class HookAction(str, Enum):
    """Enum các hành động hook."""
    INJECT = "inject"
    MODIFY = "modify"
    SKIP = "skip"

    __test__ = False  # Prevent pytest collection


# ===========================================================================
# Catalogs
# ===========================================================================

_VALID_POSITIONS = {"before", "after", "replace"}
_VALID_HOOK_EVENTS = {e.value for e in HookEvent}
_VALID_HOOK_ACTIONS = {a.value for a in HookAction}
_VALID_STACKS = {"fastapi", "nestjs", "angular", "react"}


# ===========================================================================
# CustomCodeBlock
# ===========================================================================


@dataclass
class CustomCodeBlock:
    """
    Block code tùy chỉnh để inject vào generated file.

    Attributes:
        id: Định danh duy nhất của block
        target: Path pattern của file target (vd: "app/models/{entity_snake}.py")
        code: Nội dung code sẽ inject
        position: Vị trí inject (before, after, replace)
        stack: Stack filter (None = applies to all stacks)
        language: Ngôn ngữ của code (python, typescript)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    target: str
    code: str
    position: str
    stack: Optional[str]
    language: str

    def __post_init__(self) -> None:
        """Validate block sau khi khởi tạo."""
        # Kiểm tra ID không trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP28_EMPTY_BLOCK_ID, field="block.id")

        # Kiểm tra target không trống
        if not self.target or not self.target.strip():
            EM.raise_error(ErrorCode.CP28_EMPTY_BLOCK_ID, field="block.target", reason="Target path không được để trống")

        # Kiểm tra position hợp lệ
        if self.position not in _VALID_POSITIONS:
            EM.raise_error(
                ErrorCode.CP28_INVALID_POSITION,
                position=self.position,
                valid=list(_VALID_POSITIONS),
            )

        # Kiểm tra stack hợp lệ (nếu có)
        if self.stack is not None and self.stack not in _VALID_STACKS:
            EM.raise_error(
                ErrorCode.CP28_INVALID_STACK,
                stack=self.stack,
                valid=list(_VALID_STACKS),
            )


# ===========================================================================
# Hook
# ===========================================================================


@dataclass
class Hook:
    """
    Compile-time hook để modify behavior tại lifecycle event.

    Attributes:
        id: Định danh duy nhất của hook
        event: Sự kiện compile-time (HookEvent)
        action: Hành động hook (HookAction)
        condition: Điều kiện enable/disable (Python expression string)
        code: Code block nếu action là inject/modify
    """
    __test__ = False  # Prevent pytest collection

    id: str
    event: str
    action: str
    condition: Optional[str] = None
    code: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate hook sau khi khởi tạo."""
        # Kiểm tra ID không trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP28_EMPTY_HOOK_ID, field="hook.id")

        # Kiểm tra event hợp lệ
        if self.event not in _VALID_HOOK_EVENTS:
            EM.raise_error(
                ErrorCode.CP28_INVALID_HOOK_EVENT,
                event=self.event,
                valid=list(_VALID_HOOK_EVENTS),
            )

        # Kiểm tra action hợp lệ
        if self.action not in _VALID_HOOK_ACTIONS:
            EM.raise_error(
                ErrorCode.CP28_CODE_INJECT_FAILED,
                action=self.action,
                valid=list(_VALID_HOOK_ACTIONS),
            )


# ===========================================================================
# PatchRule
# ===========================================================================


@dataclass
class PatchRule:
    """
    Regex-based patch rule để transform generated code.

    Attributes:
        id: Định danh duy nhất của patch rule
        target_pattern: Regex pattern để match
        replacement: String thay thế
        enabled: Rule có active không
        stack: Stack filter (None = applies to all)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    target_pattern: str
    replacement: str
    enabled: bool = True
    stack: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate patch rule sau khi khởi tạo."""
        # Kiểm tra ID không trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP28_EMPTY_PATCH_ID, field="patch.id")

        # Kiểm tra target_pattern không trống và regex hợp lệ
        if not self.target_pattern or not self.target_pattern.strip():
            EM.raise_error(
                ErrorCode.CP28_INVALID_PATCH_PATTERN,
                field="patch.target_pattern",
                reason="Target pattern không được để trống",
            )

        try:
            re.compile(self.target_pattern)
        except re.error as e:
            EM.raise_error(
                ErrorCode.CP28_INVALID_PATCH_PATTERN,
                pattern=self.target_pattern,
                error=str(e),
            )

        # Kiểm tra stack hợp lệ (nếu có)
        if self.stack is not None and self.stack not in _VALID_STACKS:
            EM.raise_error(
                ErrorCode.CP28_INVALID_STACK,
                stack=self.stack,
                valid=list(_VALID_STACKS),
            )


# ===========================================================================
# CustomCodeCollection
# ===========================================================================


@dataclass
class CustomCodeCollection:
    """
    Collection chứa tất cả custom code blocks, hooks, và patch rules.

    Dùng làm output của CustomCodeParser và input cho code injection engine.

    Attributes:
        blocks: Danh sách custom code blocks
        hooks: Danh sách compile-time hooks
        patch_rules: Danh sách regex patch rules
    """
    __test__ = False  # Prevent pytest collection

    blocks: list[CustomCodeBlock] = field(default_factory=list)
    hooks: list[Hook] = field(default_factory=list)
    patch_rules: list[PatchRule] = field(default_factory=list)

    def add_block(self, block: CustomCodeBlock) -> None:
        """Thêm custom code block vào collection."""
        self.blocks.append(block)

    def add_hook(self, hook: Hook) -> None:
        """Thêm compile-time hook vào collection."""
        self.hooks.append(hook)

    def add_patch_rule(self, rule: PatchRule) -> None:
        """Thêm patch rule vào collection."""
        self.patch_rules.append(rule)

    def get_block_by_id(self, block_id: str) -> Optional[CustomCodeBlock]:
        """
        Tìm block theo ID.

        Args:
            block_id: ID của block cần tìm

        Returns:
            CustomCodeBlock hoặc None nếu không tìm thấy
        """
        for block in self.blocks:
            if block.id == block_id:
                return block
        return None

    def get_hook_by_id(self, hook_id: str) -> Optional[Hook]:
        """
        Tìm hook theo ID.

        Args:
            hook_id: ID của hook cần tìm

        Returns:
            Hook hoặc None nếu không tìm thấy
        """
        for hook in self.hooks:
            if hook.id == hook_id:
                return hook
        return None

    def get_patch_rule_by_id(self, rule_id: str) -> Optional[PatchRule]:
        """
        Tìm patch rule theo ID.

        Args:
            rule_id: ID của patch rule cần tìm

        Returns:
            PatchRule hoặc None nếu không tìm thấy
        """
        for rule in self.patch_rules:
            if rule.id == rule_id:
                return rule
        return None

    def has_duplicate_block_ids(self) -> bool:
        """
        Kiểm tra có block ID trùng lặp không.

        Returns:
            True nếu có duplicate, False nếu không
        """
        seen: set[str] = set()
        for block in self.blocks:
            if block.id in seen:
                return True
            seen.add(block.id)
        return False

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển collection sang dict format.

        Returns:
            Dictionary representation của collection
        """
        return {
            "blocks": [
                {
                    "id": b.id,
                    "target": b.target,
                    "code": b.code,
                    "position": b.position,
                    "stack": b.stack,
                    "language": b.language,
                }
                for b in self.blocks
            ],
            "hooks": [
                {
                    "id": h.id,
                    "event": h.event,
                    "action": h.action,
                    "condition": h.condition,
                    "code": h.code,
                }
                for h in self.hooks
            ],
            "patch_rules": [
                {
                    "id": r.id,
                    "target_pattern": r.target_pattern,
                    "replacement": r.replacement,
                    "enabled": r.enabled,
                    "stack": r.stack,
                }
                for r in self.patch_rules
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomCodeCollection":
        """
        Tạo CustomCodeCollection từ dict.

        Args:
            data: Dictionary chứa blocks, hooks, patch_rules

        Returns:
            CustomCodeCollection đã được populate
        """
        collection = cls()

        for block_data in data.get("blocks", []):
            block = CustomCodeBlock(
                id=block_data["id"],
                target=block_data["target"],
                code=block_data.get("code", ""),
                position=block_data.get("position", "before"),
                stack=block_data.get("stack"),
                language=block_data.get("language", "python"),
            )
            collection.add_block(block)

        for hook_data in data.get("hooks", []):
            hook = Hook(
                id=hook_data["id"],
                event=hook_data["event"],
                action=hook_data["action"],
                condition=hook_data.get("condition"),
                code=hook_data.get("code"),
            )
            collection.add_hook(hook)

        for rule_data in data.get("patch_rules", []):
            rule = PatchRule(
                id=rule_data["id"],
                target_pattern=rule_data["target_pattern"],
                replacement=rule_data["replacement"],
                enabled=rule_data.get("enabled", True),
                stack=rule_data.get("stack"),
            )
            collection.add_patch_rule(rule)

        return collection
