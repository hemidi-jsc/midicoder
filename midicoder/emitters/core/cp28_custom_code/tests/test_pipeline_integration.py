# coding: utf-8
"""
Test pipeline integration cho CP28 — Custom Code Injection Generator.

Kiểm tra:
- file_contributions_loader.expand_infrastructure auto-populate context từ recipes
- context_keys "custom_code_blocks", "hooks", "patch_rules" được inject đúng
- Fallback khi recipes fail

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.pipeline.file_contributions_loader import (
    FileContributions,
    InfrastructureFile,
)


class TestCP28PipelineIntegration:
    """Kiểm tra CP28 context auto-populate từ recipes."""

    def _make_cp28_contributions(self) -> FileContributions:
        """Tạo FileContributions mô phỏng CP28."""
        return FileContributions(
            pack_id="CP28",
            pack_internal_id="cp28_custom_code",
            infrastructure=[
                InfrastructureFile(
                    path="app/custom_code/blocks.py",
                    file_type="custom_code_blocks",
                    template="cp28_custom_code/blocks.py.jinja2",
                    stacks=["fastapi"],
                    context_keys=["custom_code_blocks"],
                ),
                InfrastructureFile(
                    path="app/custom_code/hooks.py",
                    file_type="hooks",
                    template="cp28_custom_code/hooks.py.jinja2",
                    stacks=["fastapi"],
                    context_keys=["hooks"],
                ),
                InfrastructureFile(
                    path="app/custom_code/patches.py",
                    file_type="patch_rules",
                    template="cp28_custom_code/patches.py.jinja2",
                    stacks=["fastapi"],
                    context_keys=["patch_rules"],
                ),
            ],
        )

    def test_expand_infrastructure_populates_cp28_context(self) -> None:
        """expand_infrastructure auto-populate context từ recipes."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [
                {"id": "Customer", "fields": [{"id": "name", "type": "string"}]},
                {"id": "Product", "fields": [{"id": "sku", "type": "string"}]},
            ],
            "commands": [
                {"id": "CreateOrder"},
            ],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        # Kiểm tra files được expand đúng
        assert len(files) == 3

        # File đầu tiên — blocks.py — có context với custom_code_blocks
        blocks_file = next(f for f in files if "blocks.py" in f["path"])
        assert "custom_code_blocks" in blocks_file["context"]
        assert isinstance(blocks_file["context"]["custom_code_blocks"], list)
        # Recipes sinh 1 block cho mỗi entity + 1 block cho mỗi command
        assert len(blocks_file["context"]["custom_code_blocks"]) >= 2

    def test_expand_infrastructure_hooks_populated(self) -> None:
        """Hooks được auto-populate."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [{"id": "Customer", "fields": []}],
            "commands": [{"id": "CreateOrder"}],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        hooks_file = next(f for f in files if "hooks.py" in f["path"])
        assert "hooks" in hooks_file["context"]
        assert isinstance(hooks_file["context"]["hooks"], list)
        # Default hooks ≥ 3 (logging, tenant_check, skip_test)
        assert len(hooks_file["context"]["hooks"]) >= 3

    def test_expand_infrastructure_patch_rules_populated(self) -> None:
        """Patch rules được auto-populate."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [{"id": "Customer", "fields": []}],
            "commands": [{"id": "CreateOrder"}],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        patches_file = next(f for f in files if "patches.py" in f["path"])
        assert "patch_rules" in patches_file["context"]
        assert isinstance(patches_file["context"]["patch_rules"], list)

    def test_expand_infrastructure_empty_metadata(self) -> None:
        """MIR metadata rỗng — context vẫn có empty lists (fallback)."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {}

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        assert len(files) == 3
        blocks_file = next(f for f in files if "blocks.py" in f["path"])
        # Với metadata rỗng → recipes sinh defaults → có hooks/patches, blocks có thể rỗng
        assert "custom_code_blocks" in blocks_file["context"]
        assert "hooks" in next(f for f in files if "hooks.py" in f["path"])["context"]

    def test_expand_infrastructure_none_metadata(self) -> None:
        """MIR metadata None — context vẫn render được."""
        contributions = self._make_cp28_contributions()

        files = FileContributionsLoader.expand_infrastructure(contributions, None)

        assert len(files) == 3
        # Context có keys mặc dù metadata=None (fallback → empty)
        blocks_file = next(f for f in files if "blocks.py" in f["path"])
        assert "custom_code_blocks" in blocks_file["context"]

    def test_expand_infrastructure_block_has_valid_fields(self) -> None:
        """Block trong context có đủ fields (id, target, code, position, ...)."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [{"id": "Order", "fields": [{"id": "total", "type": "decimal"}]}],
            "commands": [{"id": "CreateOrder"}],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        blocks_file = next(f for f in files if "blocks.py" in f["path"])
        blocks = blocks_file["context"]["custom_code_blocks"]
        assert len(blocks) >= 2

        # Kiểm tra block đầu tiên có đúng fields
        first_block = blocks[0]
        assert "id" in first_block
        assert "target" in first_block
        assert "code" in first_block
        assert "position" in first_block
        assert "stack" in first_block
        assert "language" in first_block

    def test_expand_infrastructure_hook_has_valid_fields(self) -> None:
        """Hook trong context có đủ fields (id, event, action, ...)."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [{"id": "Customer", "fields": []}],
            "commands": [],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        hooks_file = next(f for f in files if "hooks.py" in f["path"])
        hooks = hooks_file["context"]["hooks"]

        for hook in hooks:
            assert "id" in hook
            assert "event" in hook
            assert "action" in hook

    def test_expand_infrastructure_patch_rule_has_valid_fields(self) -> None:
        """Patch rule trong context có đủ fields (id, target_pattern, replacement, ...)."""
        contributions = self._make_cp28_contributions()
        mir_metadata = {
            "entities": [{"id": "Customer", "fields": []}],
            "commands": [],
        }

        files = FileContributionsLoader.expand_infrastructure(contributions, mir_metadata)

        patches_file = next(f for f in files if "patches.py" in f["path"])
        rules = patches_file["context"]["patch_rules"]

        for rule in rules:
            assert "id" in rule
            assert "target_pattern" in rule
            assert "replacement" in rule
            assert "enabled" in rule

    def test_non_cp28_pack_not_affected(self) -> None:
        """Pack không phải CP28 không bị impact bởi CP28 logic."""
        other_pack = FileContributions(
            pack_id="CP27",
            pack_internal_id="cp27_plugin_system",
            infrastructure=[
                InfrastructureFile(
                    path="app/plugins/slots.py",
                    file_type="plugin_slots",
                    template="cp27_plugin_system/slots.py.jinja2",
                    stacks=["fastapi"],
                    context_keys=["commands"],
                ),
            ],
        )
        mir_metadata = {
            "commands": [{"id": "CreateOrder"}],
        }

        files = FileContributionsLoader.expand_infrastructure(other_pack, mir_metadata)
        assert len(files) == 1
        # Pack khác không có custom_code_blocks trong context
        assert "custom_code_blocks" not in files[0]["context"]


# Import ở đây để test lớp trực tiếp
from midicoder.pipeline.file_contributions_loader import FileContributionsLoader  # noqa: E402
