# coding: utf-8
"""
Test cases cho CP27 PluginParser.

Kiểm tra:
- Parse YAML string thành PluginCollection
- Parse dict metadata
- Parse từ MIR metadata
- Error handling: invalid YAML, invalid lifecycle events, invalid policy types
- Edge cases: empty input, lifecycle event parsing, policy type parsing
"""

import pytest

from midicoder.packs.cp27_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginPolicy,
    PluginSlot,
    PolicyType,
)
from midicoder.packs.cp27_plugin_system.parser import PluginParser
from midicoder.errors import ErrorCode, MidicoderError


class TestPluginParser:
    """Test PluginParser.parse() method."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = PluginParser()

    def test_parse_yaml_string_with_slots(self):
        """Kiểm tra parse YAML string có slots."""
        yaml_str = """
slots:
  - id: payment_processor
    name: Payment Processor
    events:
      - on_init
      - on_ready
    priority_range: [1, 100]
    is_tenant_aware: true
"""
        result = self.parser.parse(yaml_str)
        assert isinstance(result, PluginCollection)
        assert len(result.slots) == 1
        assert result.slots[0].id == "payment_processor"
        assert result.slots[0].name == "Payment Processor"
        assert result.slots[0].is_tenant_aware is True
        assert result.slots[0].priority_range == (1, 100)

    def test_parse_dict_with_all_sections(self):
        """Kiểm tra parse dict có tất cả các sections."""
        data = {
            "slots": [
                {
                    "id": "slot_1",
                    "name": "Test Slot",
                    "events": ["on_init"],
                    "priority_range": [1, 50],
                    "is_tenant_aware": False,
                }
            ],
            "contracts": [
                {
                    "id": "contract_1",
                    "slots": ["slot_1"],
                    "config_schema": {"key": "value"},
                    "dependencies": ["auth"],
                }
            ],
            "policies": [
                {
                    "id": "policy_1",
                    "type": "security",
                    "rule": "deny_external",
                    "enforced": True,
                    "config": {},
                }
            ],
        }
        result = self.parser.parse(data)
        assert len(result.slots) == 1
        assert len(result.contracts) == 1
        assert len(result.policies) == 1

    def test_parse_empty_string_returns_empty_collection(self):
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, PluginCollection)
        assert len(result.slots) == 0
        assert len(result.contracts) == 0
        assert len(result.policies) == 0

    def test_parse_empty_dict_returns_empty_collection(self):
        """Kiểm tra parse dict rỗng trả về collection rỗng."""
        result = self.parser.parse({})
        assert isinstance(result, PluginCollection)
        assert len(result.slots) == 0
        assert len(result.contracts) == 0
        assert len(result.policies) == 0

    def test_parse_invalid_yaml_raises_error(self):
        """Kiểm tra parse YAML không hợp lệ throw MidicoderError."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("invalid: [yaml: }")
        assert exc_info.value.code == ErrorCode.CP27_DSL_PARSE_ERROR

    def test_parse_slots_section(self):
        """Kiểm tra parse chỉ section slots."""
        yaml_str = """
slots:
  - id: auth_slot
    name: Auth Slot
    events:
      - on_init
      - on_configure
      - on_ready
    priority_range: [10, 90]
    is_tenant_aware: true
  - id: logging_slot
    name: Logging Slot
    events:
      - on_request
    priority_range: [1, 100]
    is_tenant_aware: false
"""
        result = self.parser.parse(yaml_str)
        assert len(result.slots) == 2
        assert result.slots[0].id == "auth_slot"
        assert len(result.slots[0].events) == 3
        assert result.slots[0].events[0] == LifecycleEvent.ON_INIT
        assert result.slots[1].id == "logging_slot"
        assert result.slots[1].is_tenant_aware is False

    def test_parse_contracts_section(self):
        """Kiểm tra parse section contracts."""
        yaml_str = """
contracts:
  - id: payment_contract
    slots: [payment_processor]
    config_schema:
      api_key: string
      timeout: 30
    dependencies: [auth]
"""
        result = self.parser.parse(yaml_str)
        assert len(result.contracts) == 1
        contract = result.contracts[0]
        assert contract.id == "payment_contract"
        assert "payment_processor" in contract.slots
        assert contract.config_schema["api_key"] == "string"
        assert "auth" in contract.dependencies

    def test_parse_policies_section(self):
        """Kiểm tra parse section policies."""
        yaml_str = """
policies:
  - id: security_policy
    type: security
    rule: deny_external_calls
    enforced: true
    config:
      allowed_hosts: [localhost]
  - id: version_policy
    type: versioning
    rule: semver_check
    enforced: false
"""
        result = self.parser.parse(yaml_str)
        assert len(result.policies) == 2
        assert result.policies[0].id == "security_policy"
        assert result.policies[0].policy_type == PolicyType.SECURITY
        assert result.policies[0].enforced is True
        assert result.policies[0].config["allowed_hosts"] == ["localhost"]
        assert result.policies[1].policy_type == PolicyType.VERSIONING
        assert result.policies[1].enforced is False


class TestPluginParserMetadata:
    """Test PluginParser.parse_from_metadata() method."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = PluginParser()

    def test_parse_from_metadata_with_entities(self):
        """Kiểm tra parse từ MIR metadata với slots, contracts, policies."""
        metadata = {
            "slots": [
                {"id": "slot_a", "name": "Slot A", "events": ["on_init"]}
            ],
            "contracts": [
                {"id": "contract_a", "slots": ["slot_a"], "config_schema": {}, "dependencies": []}
            ],
            "policies": [
                {"id": "policy_a", "type": "security", "rule": "allow_all", "enforced": False}
            ],
        }
        result = self.parser.parse_from_metadata(metadata)
        assert isinstance(result, PluginCollection)
        assert len(result.slots) == 1
        assert len(result.contracts) == 1
        assert len(result.policies) == 1
        assert result.slots[0].id == "slot_a"
        assert result.contracts[0].id == "contract_a"
        assert result.policies[0].id == "policy_a"

    def test_parse_from_metadata_empty(self):
        """Kiểm tra parse metadata rỗng trả về collection rỗng."""
        result = self.parser.parse_from_metadata({})
        assert isinstance(result, PluginCollection)
        assert len(result.slots) == 0
        assert len(result.contracts) == 0
        assert len(result.policies) == 0

    def test_parse_from_metadata_with_policies(self):
        """Kiểm tra parse metadata chỉ có policies."""
        metadata = {
            "policies": [
                {"id": "p1", "type": "security", "rule": "rule1"},
                {"id": "p2", "type": "versioning", "rule": "rule2"},
            ]
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.policies) == 2
        assert result.policies[0].policy_type == PolicyType.SECURITY
        assert result.policies[1].policy_type == PolicyType.VERSIONING


class TestPluginParserLifecycle:
    """Test lifecycle event parsing và policy types."""

    def setup_method(self):
        """Setup parser cho mỗi test."""
        self.parser = PluginParser()

    def test_parse_slot_with_lifecycle_events(self):
        """Kiểm tra parse slot với đầy đủ lifecycle events."""
        yaml_str = """
slots:
  - id: full_lifecycle_slot
    name: Full Lifecycle Slot
    events:
      - on_init
      - on_configure
      - on_ready
      - on_request
      - on_shutdown
      - before_action
      - after_action
    priority_range: [1, 100]
    is_tenant_aware: true
"""
        result = self.parser.parse(yaml_str)
        assert len(result.slots) == 1
        slot = result.slots[0]
        assert len(slot.events) == 7
        expected_events = [
            LifecycleEvent.ON_INIT,
            LifecycleEvent.ON_CONFIGURE,
            LifecycleEvent.ON_READY,
            LifecycleEvent.ON_REQUEST,
            LifecycleEvent.ON_SHUTDOWN,
            LifecycleEvent.BEFORE_ACTION,
            LifecycleEvent.AFTER_ACTION,
        ]
        for i, event in enumerate(expected_events):
            assert slot.events[i] == event

    def test_parse_policy_types(self):
        """Kiểm tra parse cả hai loại policy type: security và versioning."""
        yaml_str = """
policies:
  - id: sec_policy
    type: security
    rule: restrict_access
    enforced: true
  - id: ver_policy
    type: versioning
    rule: check_compatibility
    enforced: false
"""
        result = self.parser.parse(yaml_str)
        assert len(result.policies) == 2
        assert result.policies[0].id == "sec_policy"
        assert result.policies[0].policy_type == PolicyType.SECURITY
        assert result.policies[0].rule == "restrict_access"
        assert result.policies[0].enforced is True

        assert result.policies[1].id == "ver_policy"
        assert result.policies[1].policy_type == PolicyType.VERSIONING
        assert result.policies[1].rule == "check_compatibility"
        assert result.policies[1].enforced is False
