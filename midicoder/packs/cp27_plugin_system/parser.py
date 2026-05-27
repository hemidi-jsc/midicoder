# coding: utf-8
"""
Mô-đun parser cho Plugin System Generator (CP27).

Parse DSL plugin nodes từ MIR metadata / Contract YAML thành PluginCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp27_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginContract,
    PluginManifest,
    PluginPolicy,
    PluginSlot,
    PolicyType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class PluginParser:
    """
    Parser cho DSL plugin nodes.

    Parse YAML DSL hoặc dict metadata thành PluginCollection.

    Ví dụ DSL:
        slots:
          - id: payment_processor
            name: Payment Processor
            events:
              - on_load
              - on_tenant_switch
            priority_range: [1, 100]
            is_tenant_aware: true
        contracts:
          - id: payment_contract
            slots: [payment_processor]
            config_schema: {}
            dependencies: [auth]
        policies:
          - id: sandbox_policy
            type: sandbox
            rule: deny_external_calls
            enforced: true
    """

    def parse(self, raw: str | dict[str, Any]) -> PluginCollection:
        """
        Parse YAML string hoặc dict thành PluginCollection.

        Args:
            raw: YAML string hoặc dict chứa plugin definitions

        Returns:
            PluginCollection chứa slots, contracts, policies, manifests

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return PluginCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.CP27_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML plugin nodes: {e}",
                    error=str(e),
                )
            if data is None:
                return PluginCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return PluginCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.CP27_DSL_PARSE_ERROR,
                message="DSL plugin nodes phải là YAML mapping",
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any]) -> PluginCollection:
        """
        Parse từ MIR metadata dict.

        MIR metadata có thể chứa các key 'slots', 'contracts', 'policies', 'manifests'.

        Args:
            metadata: MIR metadata dict

        Returns:
            PluginCollection
        """
        if not metadata:
            return PluginCollection()

        collection = PluginCollection()

        # Parse slots
        slots_data = metadata.get("slots", [])
        if isinstance(slots_data, list):
            for slot_data in slots_data:
                if isinstance(slot_data, dict):
                    slot = self._parse_slot(slot_data)
                    collection.add_slot(slot)

        # Parse contracts
        contracts_data = metadata.get("contracts", [])
        if isinstance(contracts_data, list):
            for contract_data in contracts_data:
                if isinstance(contract_data, dict):
                    contract = self._parse_contract(contract_data)
                    collection.add_contract(contract)

        # Parse policies
        policies_data = metadata.get("policies", [])
        if isinstance(policies_data, list):
            for policy_data in policies_data:
                if isinstance(policy_data, dict):
                    policy = self._parse_policy(policy_data)
                    collection.add_policy(policy)

        # Parse manifests
        manifests_data = metadata.get("manifests", [])
        if isinstance(manifests_data, list):
            for manifest_data in manifests_data:
                if isinstance(manifest_data, dict):
                    manifest = self._parse_manifest(manifest_data)
                    collection.add_manifest(manifest)

        return collection

    def _parse_from_dict(self, data: dict[str, Any]) -> PluginCollection:
        """Parse từ dict đã load."""
        collection = PluginCollection()

        # Parse slots
        slots_data = data.get("slots", [])
        if isinstance(slots_data, list):
            for slot_data in slots_data:
                if isinstance(slot_data, dict):
                    slot = self._parse_slot(slot_data)
                    collection.add_slot(slot)

        # Parse contracts
        contracts_data = data.get("contracts", [])
        if isinstance(contracts_data, list):
            for contract_data in contracts_data:
                if isinstance(contract_data, dict):
                    contract = self._parse_contract(contract_data)
                    collection.add_contract(contract)

        # Parse policies
        policies_data = data.get("policies", [])
        if isinstance(policies_data, list):
            for policy_data in policies_data:
                if isinstance(policy_data, dict):
                    policy = self._parse_policy(policy_data)
                    collection.add_policy(policy)

        # Parse manifests
        manifests_data = data.get("manifests", [])
        if isinstance(manifests_data, list):
            for manifest_data in manifests_data:
                if isinstance(manifest_data, dict):
                    manifest = self._parse_manifest(manifest_data)
                    collection.add_manifest(manifest)

        return collection

    def _parse_slot(self, data: dict[str, Any]) -> PluginSlot:
        """Parse slot definition."""
        events_data = data.get("events", [])
        events: list[LifecycleEvent] = []
        for event_str in events_data:
            if isinstance(event_str, str):
                try:
                    events.append(LifecycleEvent(event_str))
                except ValueError:
                    EM.raise_error(
                        ErrorCode.CP27_INVALID_LIFECYCLE_EVENT,
                        event=event_str,
                        valid=[e.value for e in LifecycleEvent],
                    )

        priority_range = data.get("priority_range", [1, 100])
        if isinstance(priority_range, list) and len(priority_range) == 2:
            min_priority, max_priority = priority_range
        else:
            min_priority, max_priority = 1, 100

        return PluginSlot(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            events=events,
            priority_range=(min_priority, max_priority),
            is_tenant_aware=data.get("is_tenant_aware", False),
        )

    def _parse_contract(self, data: dict[str, Any]) -> PluginContract:
        """Parse contract definition."""
        return PluginContract(
            id=data.get("id", ""),
            slots=data.get("slots", []),
            config_schema=data.get("config_schema", {}),
            dependencies=data.get("dependencies", []),
        )

    def _parse_policy(self, data: dict[str, Any]) -> PluginPolicy:
        """Parse policy definition."""
        type_str = data.get("type", "security")
        try:
            policy_type = PolicyType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.CP27_INVALID_POLICY_TYPE,
                policy_type=type_str,
                valid=[t.value for t in PolicyType],
            )

        return PluginPolicy(
            id=data.get("id", ""),
            policy_type=policy_type,
            rule=data.get("rule", ""),
            enforced=data.get("enforced", True),
            config=data.get("config", {}),
        )

    def _parse_manifest(self, data: dict[str, Any]) -> PluginManifest:
        """Parse plugin manifest definition."""
        return PluginManifest(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            slots=data.get("slots", []),
            min_platform_version=data.get("min_platform_version", "0.0.0"),
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema", {}),
            signature=data.get("signature"),
        )
