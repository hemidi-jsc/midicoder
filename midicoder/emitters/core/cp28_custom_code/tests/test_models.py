# coding: utf-8
"""
Test cho data models của CP28 Custom Code Injection Generator.

Kiểm tra:
- CustomCodeBlock: validation, position enum, stack filter
- Hook: event validation, action validation
- PatchRule: regex pattern validation
- CustomCodeCollection: add/get/duplicate detection, to_dict/from_dict

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeBlock,
    CustomCodeCollection,
    Hook,
    HookAction,
    HookEvent,
    PatchRule,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestCustomCodeBlock:
    """Test CustomCodeBlock model."""

    def test_create_valid_block(self) -> None:
        """Tạo CustomCodeBlock hợp lệ thành công."""
        block = CustomCodeBlock(
            id="inject_payment_validator",
            target="app/commands/{command_snake}_validator.py",
            code="def validate_payment(self):\n    pass",
            position="after",
            stack="fastapi",
            language="python",
        )
        assert block.id == "inject_payment_validator"
        assert block.position == "after"
        assert block.stack == "fastapi"
        assert block.language == "python"

    def test_create_block_without_stack_filter(self) -> None:
        """Tạo block không có stack filter (applies to all stacks)."""
        block = CustomCodeBlock(
            id="global_inject",
            target="app/models/base.py",
            code="GLOBAL_FLAG = True",
            position="before",
            stack=None,
            language="python",
        )
        assert block.stack is None

    def test_create_block_replace_position(self) -> None:
        """Tạo block với position='replace'."""
        block = CustomCodeBlock(
            id="replace_header",
            target="app/__init__.py",
            code="# New header",
            position="replace",
            stack="fastapi",
            language="python",
        )
        assert block.position == "replace"

    def test_empty_block_id_raises_error(self) -> None:
        """Block ID trống throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            CustomCodeBlock(
                id="",
                target="app/test.py",
                code="pass",
                position="before",
                stack="fastapi",
                language="python",
            )
        assert exc_info.value.code == ErrorCode.CP28_EMPTY_BLOCK_ID

    def test_whitespace_only_block_id_raises_error(self) -> None:
        """Block ID chỉ whitespace throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            CustomCodeBlock(
                id="   ",
                target="app/test.py",
                code="pass",
                position="before",
                stack="fastapi",
                language="python",
            )
        assert exc_info.value.code == ErrorCode.CP28_EMPTY_BLOCK_ID

    def test_invalid_position_raises_error(self) -> None:
        """Position không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            CustomCodeBlock(
                id="test_block",
                target="app/test.py",
                code="pass",
                position="invalid_position",
                stack="fastapi",
                language="python",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_POSITION

    def test_invalid_stack_raises_error(self) -> None:
        """Stack không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            CustomCodeBlock(
                id="test_block",
                target="app/test.py",
                code="pass",
                position="before",
                stack="invalid_stack",
                language="python",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_STACK

    def test_empty_target_raises_error(self) -> None:
        """Target path trống throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            CustomCodeBlock(
                id="test_block",
                target="",
                code="pass",
                position="before",
                stack="fastapi",
                language="python",
            )
        assert exc_info.value.code == ErrorCode.CP28_EMPTY_BLOCK_ID


class TestHook:
    """Test Hook model."""

    def test_create_valid_hook_inject(self) -> None:
        """Tạo hook hợp lệ với action='inject'."""
        hook = Hook(
            id="add_logging",
            event="on_template_render",
            action="inject",
            condition="file_type == 'command_handler'",
            code="import logging\nlogger = logging.getLogger(__name__)",
        )
        assert hook.id == "add_logging"
        assert hook.action == "inject"

    def test_create_valid_hook_skip(self) -> None:
        """Tạo hook với action='skip' (không cần code)."""
        hook = Hook(
            id="skip_test_files",
            event="on_before_emit",
            action="skip",
            condition="path.endswith('_test.py')",
            code=None,
        )
        assert hook.action == "skip"
        assert hook.code is None

    def test_create_valid_hook_modify(self) -> None:
        """Tạo hook với action='modify'."""
        hook = Hook(
            id="modify_context",
            event="on_after_emit",
            action="modify",
            condition=None,
            code="context['version'] = '2.0'",
        )
        assert hook.action == "modify"

    def test_empty_hook_id_raises_error(self) -> None:
        """Hook ID trống throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            Hook(
                id="",
                event="on_before_emit",
                action="inject",
                code="pass",
            )
        assert exc_info.value.code == ErrorCode.CP28_EMPTY_HOOK_ID

    def test_invalid_hook_event_raises_error(self) -> None:
        """Hook event không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            Hook(
                id="test_hook",
                event="invalid_event",
                action="inject",
                code="pass",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_HOOK_EVENT

    def test_invalid_hook_action_raises_error(self) -> None:
        """Hook action không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            Hook(
                id="test_hook",
                event="on_before_emit",
                action="invalid_action",
                code="pass",
            )
        assert exc_info.value.code == ErrorCode.CP28_CODE_INJECT_FAILED


class TestPatchRule:
    """Test PatchRule model."""

    def test_create_valid_patch_rule(self) -> None:
        """Tạo patch rule hợp lệ."""
        rule = PatchRule(
            id="add_tenant_prefix",
            target_pattern=r"def (create|update|delete)_(\w+)\(",
            replacement=r"def \1_\2_tenant_safe(",
            enabled=True,
            stack="fastapi",
        )
        assert rule.id == "add_tenant_prefix"
        assert rule.enabled is True

    def test_create_disabled_patch_rule(self) -> None:
        """Tạo patch rule bị disabled."""
        rule = PatchRule(
            id="disabled_rule",
            target_pattern=r"old_pattern",
            replacement="new_pattern",
            enabled=False,
            stack=None,
        )
        assert rule.enabled is False

    def test_empty_patch_id_raises_error(self) -> None:
        """Patch ID trống throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PatchRule(
                id="",
                target_pattern=r"test",
                replacement="test",
            )
        assert exc_info.value.code == ErrorCode.CP28_EMPTY_PATCH_ID

    def test_invalid_regex_pattern_raises_error(self) -> None:
        """Regex pattern không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PatchRule(
                id="bad_regex",
                target_pattern=r"[invalid(",
                replacement="replacement",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_PATCH_PATTERN

    def test_empty_target_pattern_raises_error(self) -> None:
        """Target pattern trống throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PatchRule(
                id="test_rule",
                target_pattern="",
                replacement="replacement",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_PATCH_PATTERN

    def test_invalid_stack_raises_error(self) -> None:
        """Stack không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PatchRule(
                id="test_rule",
                target_pattern=r"valid_pattern",
                replacement="replacement",
                stack="invalid_stack",
            )
        assert exc_info.value.code == ErrorCode.CP28_INVALID_STACK


class TestCustomCodeCollection:
    """Test CustomCodeCollection."""

    def test_create_empty_collection(self) -> None:
        """Tạo collection rỗng."""
        collection = CustomCodeCollection()
        assert len(collection.blocks) == 0
        assert len(collection.hooks) == 0
        assert len(collection.patch_rules) == 0

    def test_add_block(self) -> None:
        """Thêm block vào collection."""
        collection = CustomCodeCollection()
        block = CustomCodeBlock(
            id="test_block",
            target="app/test.py",
            code="pass",
            position="before",
            stack="fastapi",
            language="python",
        )
        collection.add_block(block)
        assert len(collection.blocks) == 1
        assert collection.blocks[0].id == "test_block"

    def test_add_hook(self) -> None:
        """Thêm hook vào collection."""
        collection = CustomCodeCollection()
        hook = Hook(
            id="test_hook",
            event="on_before_emit",
            action="inject",
            code="pass",
        )
        collection.add_hook(hook)
        assert len(collection.hooks) == 1

    def test_add_patch_rule(self) -> None:
        """Thêm patch rule vào collection."""
        collection = CustomCodeCollection()
        rule = PatchRule(
            id="test_rule",
            target_pattern=r"test",
            replacement="replacement",
        )
        collection.add_patch_rule(rule)
        assert len(collection.patch_rules) == 1

    def test_get_block_by_id(self) -> None:
        """Tìm block theo ID."""
        collection = CustomCodeCollection()
        block = CustomCodeBlock(
            id="find_me",
            target="app/test.py",
            code="pass",
            position="before",
            stack="fastapi",
            language="python",
        )
        collection.add_block(block)
        found = collection.get_block_by_id("find_me")
        assert found is not None
        assert found.id == "find_me"

    def test_get_block_by_id_not_found(self) -> None:
        """Tìm block không tồn tại trả về None."""
        collection = CustomCodeCollection()
        found = collection.get_block_by_id("nonexistent")
        assert found is None

    def test_get_hook_by_id(self) -> None:
        """Tìm hook theo ID."""
        collection = CustomCodeCollection()
        hook = Hook(
            id="find_hook",
            event="on_before_emit",
            action="inject",
            code="pass",
        )
        collection.add_hook(hook)
        found = collection.get_hook_by_id("find_hook")
        assert found is not None
        assert found.id == "find_hook"

    def test_get_patch_rule_by_id(self) -> None:
        """Tìm patch rule theo ID."""
        collection = CustomCodeCollection()
        rule = PatchRule(
            id="find_rule",
            target_pattern=r"test",
            replacement="replacement",
        )
        collection.add_patch_rule(rule)
        found = collection.get_patch_rule_by_id("find_rule")
        assert found is not None

    def test_has_duplicate_block_ids(self) -> None:
        """Kiểm tra block ID trùng lặp."""
        collection = CustomCodeCollection()
        block1 = CustomCodeBlock(
            id="same_id",
            target="app/test1.py",
            code="pass",
            position="before",
            stack="fastapi",
            language="python",
        )
        block2 = CustomCodeBlock(
            id="same_id",
            target="app/test2.py",
            code="pass",
            position="before",
            stack="fastapi",
            language="python",
        )
        collection.add_block(block1)
        collection.add_block(block2)
        assert collection.has_duplicate_block_ids() is True

    def test_no_duplicate_block_ids(self) -> None:
        """Không có block ID trùng lặp."""
        collection = CustomCodeCollection()
        block1 = CustomCodeBlock(
            id="id_1",
            target="app/test1.py",
            code="pass",
            position="before",
            stack="fastapi",
            language="python",
        )
        block2 = CustomCodeBlock(
            id="id_2",
            target="app/test2.py",
            code="pass",
            position="before",
            stack="nestjs",
            language="typescript",
        )
        collection.add_block(block1)
        collection.add_block(block2)
        assert collection.has_duplicate_block_ids() is False

    def test_to_dict(self) -> None:
        """Chuyển collection sang dict."""
        collection = CustomCodeCollection()
        block = CustomCodeBlock(
            id="test_block",
            target="app/test.py",
            code="x = 1",
            position="after",
            stack="fastapi",
            language="python",
        )
        collection.add_block(block)
        hook = Hook(
            id="test_hook",
            event="on_template_render",
            action="skip",
            condition="true",
        )
        collection.add_hook(hook)

        result = collection.to_dict()
        assert "blocks" in result
        assert "hooks" in result
        assert "patch_rules" in result
        assert len(result["blocks"]) == 1
        assert result["blocks"][0]["id"] == "test_block"

    def test_from_dict(self) -> None:
        """Tạo collection từ dict."""
        data = {
            "blocks": [
                {
                    "id": "from_dict_block",
                    "target": "app/models/base.py",
                    "code": "BASE = True",
                    "position": "before",
                    "stack": "fastapi",
                    "language": "python",
                }
            ],
            "hooks": [
                {
                    "id": "from_dict_hook",
                    "event": "on_before_emit",
                    "action": "inject",
                    "condition": None,
                    "code": "print('hooked')",
                }
            ],
            "patch_rules": [
                {
                    "id": "from_dict_rule",
                    "target_pattern": r"old_func",
                    "replacement": "new_func",
                    "enabled": True,
                    "stack": None,
                }
            ],
        }
        collection = CustomCodeCollection.from_dict(data)
        assert len(collection.blocks) == 1
        assert len(collection.hooks) == 1
        assert len(collection.patch_rules) == 1
        assert collection.blocks[0].id == "from_dict_block"
        assert collection.hooks[0].id == "from_dict_hook"
        assert collection.patch_rules[0].id == "from_dict_rule"

    def test_from_dict_empty(self) -> None:
        """Tạo collection từ dict rỗng."""
        collection = CustomCodeCollection.from_dict({})
        assert len(collection.blocks) == 0
        assert len(collection.hooks) == 0
        assert len(collection.patch_rules) == 0


class TestHookEvent:
    """Test HookEvent enum."""

    def test_all_hook_events_exist(self) -> None:
        """Kiểm tra tất cả hook events tồn tại."""
        assert HookEvent.ON_BEFORE_EMIT.value == "on_before_emit"
        assert HookEvent.ON_AFTER_EMIT.value == "on_after_emit"
        assert HookEvent.ON_TEMPLATE_RENDER.value == "on_template_render"
        assert HookEvent.ON_FILE_WRITE.value == "on_file_write"


class TestHookAction:
    """Test HookAction enum."""

    def test_all_hook_actions_exist(self) -> None:
        """Kiểm tra tất cả hook actions tồn tại."""
        assert HookAction.INJECT.value == "inject"
        assert HookAction.MODIFY.value == "modify"
        assert HookAction.SKIP.value == "skip"
