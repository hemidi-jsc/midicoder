# coding: utf-8
"""
Unit tests cho CP27 Plugin System Generator — models.

Kiểm tra:
- Enums: PluginStatus, LifecycleEvent, PolicyType
- Dataclasses: PluginSlot, PluginContract, PluginPolicy, PluginManifest,
  PluginContext, PluginInfo, PluginCollection
- Validation: empty id, invalid policy_type, duplicate slots
- Serialization: to_dict / from_dict

Tự động sinh bởi CP27 — Plugin System Generator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from midicoder.packs.cp_full_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginContract,
    PluginContext,
    PluginInfo,
    LifecycleEvent,
    PluginManifest,
    PluginPolicy,
    PluginSlot,
    PluginStatus,
    PolicyType,
)
from midicoder.errors import MidicoderError


# ===========================================================================
# Test Enums
# ===========================================================================


class TestPluginStatus:
    """Kiểm tra enum PluginStatus."""

    def test_disabled_value(self) -> None:
        """Kiểm tra giá trị disabled."""
        assert PluginStatus.DISABLED.value == "disabled"

    def test_loading_value(self) -> None:
        """Kiểm tra giá trị loading."""
        assert PluginStatus.LOADING.value == "loading"

    def test_enabled_value(self) -> None:
        """Kiểm tra giá trị enabled."""
        assert PluginStatus.ENABLED.value == "enabled"

    def test_error_value(self) -> None:
        """Kiểm tra giá trị error."""
        assert PluginStatus.ERROR.value == "error"

    def test_all_members_count(self) -> None:
        """Kiểm tra số lượng members."""
        assert len(PluginStatus) == 4


class TestLifecycleEvent:
    """Kiểm tra enum LifecycleEvent."""

    def test_on_init_value(self) -> None:
        """Kiểm tra on_init."""
        assert LifecycleEvent.ON_INIT.value == "on_init"

    def test_on_configure_value(self) -> None:
        """Kiểm tra on_configure."""
        assert LifecycleEvent.ON_CONFIGURE.value == "on_configure"

    def test_on_ready_value(self) -> None:
        """Kiểm tra on_ready."""
        assert LifecycleEvent.ON_READY.value == "on_ready"

    def test_on_request_value(self) -> None:
        """Kiểm tra on_request."""
        assert LifecycleEvent.ON_REQUEST.value == "on_request"

    def test_on_shutdown_value(self) -> None:
        """Kiểm tra on_shutdown."""
        assert LifecycleEvent.ON_SHUTDOWN.value == "on_shutdown"

    def test_before_action_value(self) -> None:
        """Kiểm tra before_action."""
        assert LifecycleEvent.BEFORE_ACTION.value == "before_action"

    def test_after_action_value(self) -> None:
        """Kiểm tra after_action."""
        assert LifecycleEvent.AFTER_ACTION.value == "after_action"

    def test_all_members_count(self) -> None:
        """Kiểm tra số lượng members."""
        assert len(LifecycleEvent) == 7


class TestPolicyType:
    """Kiểm tra enum PolicyType."""

    def test_security_value(self) -> None:
        """Kiểm tra security."""
        assert PolicyType.SECURITY.value == "security"

    def test_versioning_value(self) -> None:
        """Kiểm tra versioning."""
        assert PolicyType.VERSIONING.value == "versioning"

    def test_all_members_count(self) -> None:
        """Kiểm tra số lượng members."""
        assert len(PolicyType) == 2


# ===========================================================================
# Test PluginSlot
# ===========================================================================


class TestPluginSlot:
    """Kiểm tra dataclass PluginSlot."""

    def test_create_valid_slot(self) -> None:
        """Kiểm tra tạo slot hợp lệ."""
        slot = PluginSlot(
            id="on_request",
            name="On Request Hook",
            events=[LifecycleEvent.ON_REQUEST],
            priority_range=(0, 100),
            is_tenant_aware=True,
        )
        assert slot.id == "on_request"
        assert slot.name == "On Request Hook"
        assert len(slot.events) == 1
        assert slot.priority_range == (0, 100)
        assert slot.is_tenant_aware is True

    def test_default_values(self) -> None:
        """Kiểm tra giá trị mặc định."""
        slot = PluginSlot(id="test")
        assert slot.name == ""
        assert slot.events == []
        assert slot.priority_range == (0, 100)
        assert slot.is_tenant_aware is True

    def test_empty_id_raises_error(self) -> None:
        """Kiểm tra empty id throw error."""
        with pytest.raises(MidicoderError):
            PluginSlot(id="")

    def test_whitespace_id_raises_error(self) -> None:
        """Kiểm tra whitespace id throw error."""
        with pytest.raises(MidicoderError):
            PluginSlot(id="   ")

    def test_multiple_events(self) -> None:
        """Kiểm tra nhiều events trong 1 slot."""
        events = [
            LifecycleEvent.ON_INIT,
            LifecycleEvent.ON_READY,
            LifecycleEvent.ON_REQUEST,
        ]
        slot = PluginSlot(id="multi", events=events)
        assert len(slot.events) == 3


# ===========================================================================
# Test PluginContract
# ===========================================================================


class TestPluginContract:
    """Kiểm tra dataclass PluginContract."""

    def test_create_valid_contract(self) -> None:
        """Kiểm tra tạo contract hợp lệ."""
        contract = PluginContract(
            id="payment_plugin",
            slots=["on_request", "before_payment"],
            config_schema={"api_key": {"type": "string"}},
            dependencies=["auth_plugin"],
        )
        assert contract.id == "payment_plugin"
        assert len(contract.slots) == 2
        assert "api_key" in contract.config_schema
        assert "auth_plugin" in contract.dependencies

    def test_default_values(self) -> None:
        """Kiểm tra giá trị mặc định."""
        contract = PluginContract(id="basic")
        assert contract.slots == []
        assert contract.config_schema == {}
        assert contract.dependencies == []

    def test_empty_id_raises_error(self) -> None:
        """Kiểm tra empty id throw error."""
        with pytest.raises(MidicoderError):
            PluginContract(id="")


# ===========================================================================
# Test PluginPolicy
# ===========================================================================


class TestPluginPolicy:
    """Kiểm tra dataclass PluginPolicy."""

    def test_create_security_policy(self) -> None:
        """Kiểm tra tạo security policy."""
        policy = PluginPolicy(
            id="signature_check",
            policy_type=PolicyType.SECURITY,
            rule="verify_sha256",
            enforced=True,
        )
        assert policy.id == "signature_check"
        assert policy.policy_type == PolicyType.SECURITY
        assert policy.enforced is True

    def test_create_versioning_policy(self) -> None:
        """Kiểm tra tạo versioning policy."""
        policy = PluginPolicy(
            id="version_gate",
            policy_type=PolicyType.VERSIONING,
            rule="semver_range",
            enforced=True,
            config={"min_version": "1.0.0"},
        )
        assert policy.policy_type == PolicyType.VERSIONING
        assert policy.config["min_version"] == "1.0.0"

    def test_default_enforced(self) -> None:
        """Kiểm tra enforced mặc định là True."""
        policy = PluginPolicy(
            id="test", policy_type=PolicyType.SECURITY, rule="test"
        )
        assert policy.enforced is True

    def test_empty_id_raises_error(self) -> None:
        """Kiểm tra empty id throw error."""
        with pytest.raises(MidicoderError):
            PluginPolicy(id="", policy_type=PolicyType.SECURITY, rule="test")


# ===========================================================================
# Test PluginManifest
# ===========================================================================


class TestPluginManifest:
    """Kiểm tra dataclass PluginManifest."""

    def test_create_valid_manifest(self) -> None:
        """Kiểm tra tạo manifest hợp lệ."""
        manifest = PluginManifest(
            id="example-plugin",
            name="Example Plugin",
            version="1.0.0",
            description="A sample plugin",
            author="midicoder",
            slots=["on_request"],
            min_platform_version="1.0.0",
        )
        assert manifest.id == "example-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.author == "midicoder"

    def test_default_values(self) -> None:
        """Kiểm tra giá trị mặc định."""
        manifest = PluginManifest(id="test")
        assert manifest.name == ""
        assert manifest.version == "0.0.0"
        assert manifest.dependencies == []
        assert manifest.config_schema == {}

    def test_empty_id_raises_error(self) -> None:
        """Kiểm tra empty id throw error."""
        with pytest.raises(MidicoderError):
            PluginManifest(id="")


# ===========================================================================
# Test PluginContext
# ===========================================================================


class TestPluginContext:
    """Kiểm tra dataclass PluginContext."""

    def test_create_with_all_fields(self) -> None:
        """Kiểm tra tạo context đầy đủ."""
        ctx = PluginContext(
            tenant_id="tenant-1",
            user_id="user-1",
            request_id="req-123",
            app_config={"debug": True},
            event_bus=None,
        )
        assert ctx.tenant_id == "tenant-1"
        assert ctx.user_id == "user-1"
        assert ctx.app_config["debug"] is True

    def test_default_values(self) -> None:
        """Kiểm tra giá trị mặc định."""
        ctx = PluginContext()
        assert ctx.tenant_id == ""
        assert ctx.user_id == ""
        assert ctx.app_config == {}


# ===========================================================================
# Test PluginInfo
# ===========================================================================


class TestPluginInfo:
    """Kiểm tra dataclass PluginInfo."""

    def test_enabled_plugin(self) -> None:
        """Kiểm tra plugin đang enabled."""
        now = datetime.now()
        info = PluginInfo(
            id="test",
            name="Test",
            version="1.0.0",
            status=PluginStatus.ENABLED,
            slots=["on_request"],
            loaded_at=now,
        )
        assert info.status == PluginStatus.ENABLED
        assert info.loaded_at == now
        assert info.error is None

    def test_error_plugin(self) -> None:
        """Kiểm tra plugin ở trạng thái error."""
        info = PluginInfo(
            id="fail",
            name="Fail",
            version="0.1.0",
            status=PluginStatus.ERROR,
            error="Load failed",
        )
        assert info.status == PluginStatus.ERROR
        assert info.error == "Load failed"


# ===========================================================================
# Test PluginCollection
# ===========================================================================


class TestPluginCollection:
    """Kiểm tra dataclass PluginCollection."""

    def test_add_and_get_slot(self) -> None:
        """Kiểm tra thêm và lấy slot."""
        collection = PluginCollection()
        slot = PluginSlot(id="on_request", name="Request Hook")
        collection.add_slot(slot)
        assert collection.get_slot_by_id("on_request") is slot
        assert collection.get_slot_by_id("nonexistent") is None

    def test_add_and_get_contract(self) -> None:
        """Kiểm tra thêm và lấy contract."""
        collection = PluginCollection()
        contract = PluginContract(id="c1", slots=["on_request"])
        collection.add_contract(contract)
        assert collection.get_contract_by_id("c1") is contract

    def test_add_and_get_policy(self) -> None:
        """Kiểm tra thêm và lấy policy."""
        collection = PluginCollection()
        policy = PluginPolicy(
            id="sig_check", policy_type=PolicyType.SECURITY, rule="sha256"
        )
        collection.add_policy(policy)
        assert collection.get_policy_by_id("sig_check") is policy

    def test_add_and_get_manifest(self) -> None:
        """Kiểm tra thêm và lấy manifest."""
        collection = PluginCollection()
        manifest = PluginManifest(id="m1", name="Test")
        collection.add_manifest(manifest)
        assert len(collection.manifests) == 1

    def test_has_duplicate_slots(self) -> None:
        """Kiểm tra phát hiện duplicate slots."""
        collection = PluginCollection()
        collection.add_slot(PluginSlot(id="on_request"))
        collection.add_slot(PluginSlot(id="on_init"))
        assert collection.has_duplicate_slots() is False

        collection.add_slot(PluginSlot(id="on_request"))
        assert collection.has_duplicate_slots() is True

    def test_to_dict(self) -> None:
        """Kiểm tra serialize sang dict."""
        collection = PluginCollection()
        collection.add_slot(PluginSlot(id="on_request", name="Hook"))
        collection.add_policy(
            PluginPolicy(id="sig", policy_type=PolicyType.SECURITY, rule="sha256")
        )
        d = collection.to_dict()
        assert "slots" in d
        assert "policies" in d
        assert len(d["slots"]) == 1
        assert d["slots"][0]["id"] == "on_request"

    def test_from_dict(self) -> None:
        """Kiểm tra deserialize từ dict."""
        data: dict[str, Any] = {
            "slots": [
                {
                    "id": "on_request",
                    "name": "Request",
                    "events": ["on_request"],
                    "priority_range": [0, 100],
                    "is_tenant_aware": True,
                }
            ],
            "contracts": [
                {"id": "c1", "slots": ["on_request"], "config_schema": {}, "dependencies": []}
            ],
            "policies": [
                {
                    "id": "sig",
                    "policy_type": "security",
                    "rule": "sha256",
                    "enforced": True,
                    "config": {},
                }
            ],
            "manifests": [],
        }
        collection = PluginCollection.from_dict(data)
        assert len(collection.slots) == 1
        assert len(collection.contracts) == 1
        assert len(collection.policies) == 1
        assert collection.slots[0].id == "on_request"
        assert collection.policies[0].policy_type == PolicyType.SECURITY

    def test_empty_collection(self) -> None:
        """Kiểm tra collection rỗng."""
        collection = PluginCollection()
        assert len(collection.slots) == 0
        assert len(collection.contracts) == 0
        assert len(collection.policies) == 0
        assert len(collection.manifests) == 0
        assert collection.has_duplicate_slots() is False

    def test_roundtrip_serialization(self) -> None:
        """Kiểm tra serialize rồi deserialize giữ nguyên data."""
        original = PluginCollection()
        original.add_slot(PluginSlot(id="on_init", name="Init Hook", events=[LifecycleEvent.ON_INIT]))
        original.add_contract(PluginContract(id="default", slots=["on_init"]))
        original.add_policy(
            PluginPolicy(id="ver", policy_type=PolicyType.VERSIONING, rule="semver")
        )

        d = original.to_dict()
        restored = PluginCollection.from_dict(d)

        assert len(restored.slots) == 1
        assert len(restored.contracts) == 1
        assert len(restored.policies) == 1
        assert restored.slots[0].id == "on_init"
        assert restored.policies[0].policy_type == PolicyType.VERSIONING
