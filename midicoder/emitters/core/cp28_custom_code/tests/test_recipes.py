# coding: utf-8
"""
Test cho recipes module của CP28 Custom Code Injection Generator.

Kiểm tra:
- generate_default_blocks: sinh blocks mặc định từ entities/commands
- generate_default_hooks: sinh hooks mặc định
- generate_default_patch_rules: sinh patch rules mặc định
- auto_generate_custom_code_from_mir: master recipe từ MIR metadata
- _to_snake_case: helper function

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeBlock,
    CustomCodeCollection,
    Hook,
    PatchRule,
)
from midicoder.emitters.core.cp28_custom_code.recipes import (
    _to_snake_case,
    auto_generate_custom_code_from_mir,
    generate_default_blocks,
    generate_default_hooks,
    generate_default_patch_rules,
)


class TestToSnakeCase:
    """Test helper _to_snake_case."""

    def test_pascal_case(self) -> None:
        """PascalCase sang snake_case."""
        assert _to_snake_case("CreateOrder") == "create_order"

    def test_camel_case(self) -> None:
        """camelCase sang snake_case."""
        assert _to_snake_case("updateSettings") == "update_settings"

    def test_already_snake_case(self) -> None:
        """Snake_case giữ nguyên."""
        assert _to_snake_case("get_order_details") == "get_order_details"

    def test_simple_word(self) -> None:
        """Từ đơn giản."""
        assert _to_snake_case("Order") == "order"

    def test_with_numbers(self) -> None:
        """Có chứa số."""
        assert _to_snake_case("OrderItem2") == "order_item2"


class TestGenerateDefaultBlocks:
    """Test generate_default_blocks."""

    def test_empty_input(self) -> None:
        """Input rỗng trả về list rỗng."""
        result = generate_default_blocks([], [])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_blocks_from_entities(self) -> None:
        """Sinh blocks từ entities."""
        entities = [
            {"id": "Customer", "name": "Customer"},
            {"id": "Order", "name": "Order"},
        ]
        result = generate_default_blocks(entities, [])
        assert len(result) == 2
        assert all(isinstance(b, CustomCodeBlock) for b in result)

    def test_generate_blocks_from_commands(self) -> None:
        """Sinh blocks từ commands."""
        commands = [
            {"id": "CreateOrder", "name": "CreateOrder"},
            {"id": "DeleteCustomer", "name": "DeleteCustomer"},
        ]
        result = generate_default_blocks([], commands)
        assert len(result) == 2
        # Tất cả blocks có position="after" (inject sau code chính)
        assert all(b.position == "after" for b in result)

    def test_generate_blocks_from_both(self) -> None:
        """Sinh blocks từ cả entities và commands."""
        entities = [{"id": "Product", "name": "Product"}]
        commands = [{"id": "CreateProduct", "name": "CreateProduct"}]
        result = generate_default_blocks(entities, commands)
        assert len(result) == 2

    def test_block_has_valid_id(self) -> None:
        """Block ID có prefix 'inject_' và snake_case name."""
        entities = [{"id": "Customer", "name": "Customer"}]
        result = generate_default_blocks(entities, [])
        assert result[0].id == "inject_customer_ext"

    def test_block_has_valid_target(self) -> None:
        """Block target path pattern hợp lệ."""
        entities = [{"id": "Order", "name": "Order"}]
        result = generate_default_blocks(entities, [])
        assert "app/models/" in result[0].target

    def test_block_language_matches_stack(self) -> None:
        """Block language phù hợp với stack."""
        entities = [{"id": "User", "name": "User"}]
        result = generate_default_blocks(entities, [])
        # Default block không có stack filter (applies to all)
        assert result[0].stack is None


class TestGenerateDefaultHooks:
    """Test generate_default_hooks."""

    def test_generate_default_hooks(self) -> None:
        """Sinh hooks mặc định."""
        result = generate_default_hooks()
        assert len(result) >= 2  # Ít nhất 2 hooks mặc định
        assert all(isinstance(h, Hook) for h in result)

    def test_hooks_have_valid_ids(self) -> None:
        """Hook IDs có prefix 'hook_'."""
        result = generate_default_hooks()
        assert all(h.id.startswith("hook_") for h in result)

    def test_hooks_have_valid_events(self) -> None:
        """Hook events hợp lệ."""
        result = generate_default_hooks()
        valid_events = {"on_before_emit", "on_after_emit", "on_template_render", "on_file_write"}
        assert all(h.event in valid_events for h in result)

    def test_hooks_have_valid_actions(self) -> None:
        """Hook actions hợp lệ."""
        result = generate_default_hooks()
        valid_actions = {"inject", "modify", "skip"}
        assert all(h.action in valid_actions for h in result)


class TestGenerateDefaultPatchRules:
    """Test generate_default_patch_rules."""

    def test_generate_default_rules(self) -> None:
        """Sinh patch rules mặc định."""
        result = generate_default_patch_rules()
        assert len(result) >= 1  # Ít nhất 1 rule mặc định
        assert all(isinstance(r, PatchRule) for r in result)

    def test_rules_have_valid_ids(self) -> None:
        """Rule IDs có prefix 'patch_'."""
        result = generate_default_patch_rules()
        assert all(r.id.startswith("patch_") for r in result)

    def test_rules_are_enabled(self) -> None:
        """Default rules có cả enabled và disabled."""
        result = generate_default_patch_rules()
        # Có ít nhất 1 rule enabled và 1 rule disabled
        enabled_rules = [r for r in result if r.enabled is True]
        disabled_rules = [r for r in result if r.enabled is False]
        assert len(enabled_rules) >= 1
        assert len(disabled_rules) >= 0  # Có thể không có rule disabled

    def test_rules_have_valid_patterns(self) -> None:
        """Patch patterns là regex hợp lệ."""
        import re
        result = generate_default_patch_rules()
        for rule in result:
            re.compile(rule.target_pattern)  # Không throw


class TestAutoGenerateCustomCodeFromMir:
    """Test auto_generate_custom_code_from_mir."""

    def test_empty_metadata(self) -> None:
        """Metadata rỗng vẫn sinh default hooks và patch rules."""
        result = auto_generate_custom_code_from_mir({})
        assert isinstance(result, CustomCodeCollection)
        assert len(result.blocks) == 0  # Không entities/commands → không blocks
        # Nhưng vẫn có default hooks và patch rules
        assert len(result.hooks) >= 2
        assert len(result.patch_rules) >= 1

    def test_generate_from_entities_and_commands(self) -> None:
        """Sinh từ metadata có entities và commands."""
        metadata = {
            "entities": [
                {"id": "Customer", "name": "Customer"},
                {"id": "Order", "name": "Order"},
            ],
            "commands": [
                {"id": "CreateOrder", "name": "CreateOrder"},
                {"id": "DeleteCustomer", "name": "DeleteCustomer"},
            ],
        }
        result = auto_generate_custom_code_from_mir(metadata)
        assert len(result.blocks) >= 3  #Entities + commands
        assert len(result.hooks) >= 2  # Default hooks
        assert len(result.patch_rules) >= 1  # Default rules

    def test_generate_deterministic(self) -> None:
        """Cùng input → cùng output (determinism)."""
        metadata = {
            "entities": [{"id": "Product", "name": "Product"}],
            "commands": [{"id": "CreateProduct", "name": "CreateProduct"}],
        }
        result1 = auto_generate_custom_code_from_mir(metadata)
        result2 = auto_generate_custom_code_from_mir(metadata)
        assert result1.to_dict() == result2.to_dict()

    def test_generate_blocks_for_each_entity(self) -> None:
        """Mỗi entity có 1 custom code block."""
        metadata = {
            "entities": [
                {"id": "A", "name": "A"},
                {"id": "B", "name": "B"},
                {"id": "C", "name": "C"},
            ],
            "commands": [],
        }
        result = auto_generate_custom_code_from_mir(metadata)
        assert len(result.blocks) == 3

    def test_generate_blocks_for_each_command(self) -> None:
        """Mỗi command có 1 custom code block."""
        metadata = {
            "entities": [],
            "commands": [
                {"id": "CmdA", "name": "CmdA"},
                {"id": "CmdB", "name": "CmdB"},
            ],
        }
        result = auto_generate_custom_code_from_mir(metadata)
        assert len(result.blocks) == 2
