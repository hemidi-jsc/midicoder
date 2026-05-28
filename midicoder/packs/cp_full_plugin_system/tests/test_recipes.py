# coding: utf-8
"""
Test cases cho CP27 Plugin System Generator recipes.

Kiểm tra:
- auto_generate_plugins_from_mir
- generate_default_slots
- generate_default_contracts
- generate_default_policies
"""

import pytest

from midicoder.packs.cp_full_plugin_system.recipes import (
    auto_generate_plugins_from_mir,
    generate_default_contracts,
    generate_default_policies,
    generate_default_slots,
)
from midicoder.packs.cp_full_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginContract,
    PluginPolicy,
    PluginSlot,
    PolicyType,
)


class TestAutoGeneratePluginsFromMir:
    """Test auto_generate_plugins_from_mir (master recipe)."""

    def test_generate_from_empty_metadata_returns_collection(self):
        """Kiểm tra metadata rỗng trả về PluginCollection hợp lệ."""
        collection = auto_generate_plugins_from_mir({})

        assert isinstance(collection, PluginCollection)
        # Vẫn có 5 lifecycle slots mặc định
        assert len(collection.slots) == 5
        # Có 1 contract mặc định
        assert len(collection.contracts) == 1
        # Có 3 policies mặc định
        assert len(collection.policies) == 3

    def test_generate_from_metadata_with_entities(self):
        """Kiểm tra metadata có entities sinh ra collection đầy đủ."""
        metadata = {
            "entities": [
                {"id": "User", "fields": [{"name": "email"}, {"name": "name"}]},
                {"id": "Order", "fields": [{"name": "total"}]},
            ]
        }

        collection = auto_generate_plugins_from_mir(metadata)

        assert isinstance(collection, PluginCollection)
        # 5 lifecycle slots (entities không tạo thêm slots)
        assert len(collection.slots) == 5
        assert len(collection.contracts) == 1
        assert len(collection.policies) == 3

    def test_generate_from_metadata_with_commands(self):
        """Kiểm tra metadata có commands sinh before/after hooks."""
        metadata = {
            "entities": [{"id": "User"}],
            "commands": [{"id": "CreateUser"}, {"id": "DeleteUser"}],
        }

        collection = auto_generate_plugins_from_mir(metadata)

        # 5 lifecycle + 2 commands x 2 (before/after) = 9 slots
        assert len(collection.slots) == 9

        # Kiểm tra có before/after hooks
        slot_names = [s.name for s in collection.slots]
        assert "before_create_user" in slot_names
        assert "after_create_user" in slot_names
        assert "before_delete_user" in slot_names
        assert "after_delete_user" in slot_names

    def test_generate_has_lifecycle_slots(self):
        """Kiểm tra collection có đầy đủ 5 lifecycle slots."""
        collection = auto_generate_plugins_from_mir({})

        slot_names = [s.name for s in collection.slots]
        assert "on_init" in slot_names
        assert "on_configure" in slot_names
        assert "on_ready" in slot_names
        assert "on_request" in slot_names
        assert "on_shutdown" in slot_names

    def test_generate_has_command_hooks(self):
        """Kiểm tra collection có before/after hooks cho commands."""
        metadata = {
            "entities": [],
            "commands": [{"id": "UpdateSettings"}],
        }

        collection = auto_generate_plugins_from_mir(metadata)

        slot_names = [s.name for s in collection.slots]
        assert "before_update_settings" in slot_names
        assert "after_update_settings" in slot_names

        # Kiểm tra events đúng loại
        before_slot = collection.get_slot_by_id("slot_before_update_settings")
        assert before_slot is not None
        assert LifecycleEvent.BEFORE_ACTION in before_slot.events

        after_slot = collection.get_slot_by_id("slot_after_update_settings")
        assert after_slot is not None
        assert LifecycleEvent.AFTER_ACTION in after_slot.events

    def test_generate_has_policies(self):
        """Kiểm tra collection có đầy đủ 3 policies mặc định."""
        collection = auto_generate_plugins_from_mir({})

        policy_ids = [p.id for p in collection.policies]
        assert "policy_signature_check" in policy_ids
        assert "policy_version_gate" in policy_ids
        assert "policy_origin_whitelist" in policy_ids


class TestGenerateDefaultSlots:
    """Test generate_default_slots recipe."""

    def test_generate_lifecycle_slots(self):
        """Kiểm tra sinh ra 5 lifecycle slots mặc định."""
        slots = generate_default_slots([])

        assert len(slots) == 5

        slot_names = [s.name for s in slots]
        assert "on_init" in slot_names
        assert "on_configure" in slot_names
        assert "on_ready" in slot_names
        assert "on_request" in slot_names
        assert "on_shutdown" in slot_names

    def test_generate_before_command_hooks(self):
        """Kiểm tra sinh ra before hooks cho commands."""
        commands = [{"id": "CreateOrder"}]
        slots = generate_default_slots([], commands)

        slot_names = [s.name for s in slots]
        assert "before_create_order" in slot_names

        before_slot = next(s for s in slots if s.name == "before_create_order")
        assert LifecycleEvent.BEFORE_ACTION in before_slot.events
        assert before_slot.is_tenant_aware is True

    def test_generate_after_command_hooks(self):
        """Kiểm tra sinh ra after hooks cho commands."""
        commands = [{"id": "CreateOrder"}]
        slots = generate_default_slots([], commands)

        slot_names = [s.name for s in slots]
        assert "after_create_order" in slot_names

        after_slot = next(s for s in slots if s.name == "after_create_order")
        assert LifecycleEvent.AFTER_ACTION in after_slot.events
        assert after_slot.is_tenant_aware is True

    def test_empty_commands_returns_only_lifecycle(self):
        """Kiểm tra không có commands chỉ trả về lifecycle slots."""
        slots = generate_default_slots([], [])

        assert len(slots) == 5
        for slot in slots:
            assert slot.name.startswith("on_")

    def test_multiple_commands_generate_multiple_hooks(self):
        """Kiểm tra nhiều commands tạo nhiều before/after hooks."""
        commands = [
            {"id": "CreateUser"},
            {"id": "DeleteUser"},
            {"id": "UpdateOrder"},
        ]
        slots = generate_default_slots([], commands)

        # 5 lifecycle + 3 commands x 2 hooks = 11 slots
        assert len(slots) == 11

        slot_names = [s.name for s in slots]
        assert "before_create_user" in slot_names
        assert "after_create_user" in slot_names
        assert "before_delete_user" in slot_names
        assert "after_delete_user" in slot_names
        assert "before_update_order" in slot_names
        assert "after_update_order" in slot_names


class TestGenerateDefaultContracts:
    """Test generate_default_contracts recipe."""

    def test_generate_contract_with_slots(self):
        """Kiểm tra sinh contract chứa tất cả slot IDs."""
        slots = generate_default_slots([], [{"id": "CreateUser"}])

        contracts = generate_default_contracts(slots)

        assert len(contracts) == 1
        contract = contracts[0]
        assert isinstance(contract, PluginContract)
        assert contract.id == "contract_default"
        # Contract chứa tất cả slot IDs
        assert len(contract.slots) == len(slots)
        for slot in slots:
            assert slot.id in contract.slots


class TestGenerateDefaultPolicies:
    """Test generate_default_policies recipe."""

    def test_generate_security_policy(self):
        """Kiểm tra sinh ra security policy (signature check)."""
        policies = generate_default_policies()

        signature_policy = next(
            (p for p in policies if p.id == "policy_signature_check"), None
        )
        assert signature_policy is not None
        assert signature_policy.policy_type == PolicyType.SECURITY
        assert signature_policy.rule == "verify_sha256"
        assert signature_policy.config["algorithm"] == "sha256"

    def test_generate_versioning_policy(self):
        """Kiểm tra sinh ra versioning policy (version gate)."""
        policies = generate_default_policies()

        version_policy = next(
            (p for p in policies if p.id == "policy_version_gate"), None
        )
        assert version_policy is not None
        assert version_policy.policy_type == PolicyType.VERSIONING
        assert version_policy.rule == "semver_range"
        assert version_policy.config["min_version"] == "0.1.0"

    def test_generate_three_default_policies(self):
        """Kiểm tra sinh ra đúng 3 policies mặc định."""
        policies = generate_default_policies()

        assert len(policies) == 3

        policy_ids = [p.id for p in policies]
        assert "policy_signature_check" in policy_ids
        assert "policy_version_gate" in policy_ids
        assert "policy_origin_whitelist" in policy_ids

    def test_policies_are_enforced(self):
        """Kiểm tra tất cả policies đều được enforced."""
        policies = generate_default_policies()

        for policy in policies:
            assert policy.enforced is True
