# coding: utf-8
"""
Test cho CustomCodeParser của CP28 Custom Code Injection Generator.

Kiểm tra:
- Parse YAML string thành CustomCodeCollection
- Parse dict thành CustomCodeCollection
- Parse từ MIR metadata
- Xử lý input rỗng/invalid
- Parse blocks, hooks, patch_rules

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeCollection,
)
from midicoder.emitters.core.cp28_custom_code.parser import CustomCodeParser
from midicoder.errors import ErrorCode, MidicoderError


class TestCustomCodeParser:
    """Test CustomCodeParser."""

    def setup_method(self) -> None:
        """Setup parser instance cho mỗi test."""
        self.parser = CustomCodeParser()

    def test_parse_empty_string(self) -> None:
        """Parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, CustomCodeCollection)
        assert len(result.blocks) == 0
        assert len(result.hooks) == 0
        assert len(result.patch_rules) == 0

    def test_parse_none_string(self) -> None:
        """Parse None/string None trả về collection rỗng."""
        result = self.parser.parse(None)  # type: ignore
        assert isinstance(result, CustomCodeCollection)

    def test_parse_whitespace_only(self) -> None:
        """Parse chỉ whitespace trả về collection rỗng."""
        result = self.parser.parse("   \n  ")
        assert len(result.blocks) == 0

    def test_parse_yaml_with_blocks(self) -> None:
        """Parse YAML có custom_code_blocks."""
        yaml_str = """
custom_code_blocks:
  - id: inject_validator
    target: "app/commands/{command_snake}_validator.py"
    code: "def validate_payment(self):\n    pass"
    position: after
    stack: fastapi
    language: python
"""
        result = self.parser.parse(yaml_str)
        assert len(result.blocks) == 1
        assert result.blocks[0].id == "inject_validator"
        assert result.blocks[0].position == "after"
        assert result.blocks[0].stack == "fastapi"

    def test_parse_yaml_with_hooks(self) -> None:
        """Parse YAML có hooks."""
        yaml_str = """
hooks:
  - id: add_logging
    event: on_template_render
    action: inject
    condition: "file_type == 'command_handler'"
    code: "import logging"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.hooks) == 1
        assert result.hooks[0].id == "add_logging"
        assert result.hooks[0].event == "on_template_render"

    def test_parse_yaml_with_patch_rules(self) -> None:
        """Parse YAML có patch_rules."""
        yaml_str = """
patch_rules:
  - id: add_tenant_prefix
    target_pattern: 'def (create|update)_(\\w+)\\('
    replacement: 'def \\1_\\2_tenant_safe('
    enabled: true
    stack: fastapi
"""
        result = self.parser.parse(yaml_str)
        assert len(result.patch_rules) == 1
        assert result.patch_rules[0].id == "add_tenant_prefix"
        assert result.patch_rules[0].enabled is True

    def test_parse_yaml_all_three_categories(self) -> None:
        """Parse YAML có đầy đủ 3 categories."""
        yaml_str = """
custom_code_blocks:
  - id: block_1
    target: "app/test.py"
    code: "x = 1"
    position: before
    stack: fastapi
    language: python
hooks:
  - id: hook_1
    event: on_before_emit
    action: skip
    condition: "path.endswith('_test.py')"
patch_rules:
  - id: rule_1
    target_pattern: "old_func"
    replacement: "new_func"
    enabled: true
"""
        result = self.parser.parse(yaml_str)
        assert len(result.blocks) == 1
        assert len(result.hooks) == 1
        assert len(result.patch_rules) == 1

    def test_parse_dict_input(self) -> None:
        """Parse dict input trực tiếp."""
        data = {
            "custom_code_blocks": [
                {
                    "id": "dict_block",
                    "target": "app/models/base.py",
                    "code": "BASE = True",
                    "position": "before",
                    "stack": "nestjs",
                    "language": "typescript",
                }
            ],
            "hooks": [],
            "patch_rules": [],
        }
        result = self.parser.parse(data)
        assert len(result.blocks) == 1
        assert result.blocks[0].stack == "nestjs"

    def test_parse_invalid_yaml_raises_error(self) -> None:
        """Parse YAML invalid throw error."""
        invalid_yaml = ":::\n  - {{invalid"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.CP28_DSL_PARSE_ERROR

    def test_parse_invalid_input_type(self) -> None:
        """Parse input type không hợp lệ trả về collection rỗng."""
        result = self.parser.parse(12345)  # type: ignore
        assert isinstance(result, CustomCodeCollection)
        assert len(result.blocks) == 0

    def test_parse_blocks_with_defaults(self) -> None:
        """Parse block với default values cho optional fields."""
        yaml_str = """
custom_code_blocks:
  - id: minimal_block
    target: "app/test.py"
    code: "pass"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.blocks) == 1
        # Default values
        assert result.blocks[0].position == "before"
        assert result.blocks[0].stack is None
        assert result.blocks[0].language == "python"

    def test_parse_multiple_blocks(self) -> None:
        """Parse nhiều blocks cùng lúc."""
        yaml_str = """
custom_code_blocks:
  - id: block_one
    target: "app/a.py"
    code: "a = 1"
    position: before
    stack: fastapi
    language: python
  - id: block_two
    target: "app/b.py"
    code: "b = 2"
    position: after
    stack: react
    language: typescript
"""
        result = self.parser.parse(yaml_str)
        assert len(result.blocks) == 2
        assert result.blocks[0].id == "block_one"
        assert result.blocks[1].id == "block_two"

    def test_parse_hook_without_code(self) -> None:
        """Parse hook không có code field (action=skip)."""
        yaml_str = """
hooks:
  - id: skip_hook
    event: on_before_emit
    action: skip
    condition: "path.endswith('.bak')"
"""
        result = self.parser.parse(yaml_str)
        assert len(result.hooks) == 1
        assert result.hooks[0].code is None

    def test_parse_patch_rule_disabled(self) -> None:
        """Parse patch rule bị disabled."""
        yaml_str = """
patch_rules:
  - id: disabled_rule
    target_pattern: "test"
    replacement: "prod"
    enabled: false
"""
        result = self.parser.parse(yaml_str)
        assert len(result.patch_rules) == 1
        assert result.patch_rules[0].enabled is False


class TestCustomCodeParserFromMetadata:
    """Test parse_from_metadata."""

    def setup_method(self) -> None:
        """Setup parser instance."""
        self.parser = CustomCodeParser()

    def test_parse_from_empty_metadata(self) -> None:
        """Parse từ metadata rỗng trả về collection rỗng."""
        result = self.parser.parse_from_metadata({})
        assert len(result.blocks) == 0
        assert len(result.hooks) == 0

    def test_parse_from_none_metadata(self) -> None:
        """Parse từ metadata None trả về collection rỗng."""
        result = self.parser.parse_from_metadata(None)  # type: ignore
        assert len(result.blocks) == 0

    def test_parse_from_metadata_with_blocks(self) -> None:
        """Parse từ metadata có custom_code_blocks."""
        metadata = {
            "custom_code_blocks": [
                {
                    "id": "meta_block",
                    "target": "app/meta.py",
                    "code": "META = True",
                    "position": "after",
                    "stack": "angular",
                    "language": "typescript",
                }
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.blocks) == 1
        assert result.blocks[0].stack == "angular"

    def test_parse_from_metadata_with_hooks(self) -> None:
        """Parse từ metadata có hooks."""
        metadata = {
            "hooks": [
                {
                    "id": "meta_hook",
                    "event": "on_file_write",
                    "action": "modify",
                    "code": "context['meta'] = True",
                }
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.hooks) == 1
        assert result.hooks[0].event == "on_file_write"

    def test_parse_from_metadata_with_patch_rules(self) -> None:
        """Parse từ metadata có patch_rules."""
        metadata = {
            "patch_rules": [
                {
                    "id": "meta_rule",
                    "target_pattern": r"old_meta",
                    "replacement": "new_meta",
                    "enabled": True,
                }
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.patch_rules) == 1

    def test_parse_from_metadata_all_categories(self) -> None:
        """Parse từ metadata có đầy đủ categories."""
        metadata = {
            "custom_code_blocks": [
                {"id": "b1", "target": "app/a.py", "code": "pass", "position": "before", "stack": None, "language": "python"}
            ],
            "hooks": [
                {"id": "h1", "event": "on_before_emit", "action": "inject", "code": "pass"}
            ],
            "patch_rules": [
                {"id": "r1", "target_pattern": "test", "replacement": "prod", "enabled": True}
            ],
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.blocks) == 1
        assert len(result.hooks) == 1
        assert len(result.patch_rules) == 1
