# coding: utf-8
"""
CP27: Plugin System Generator.

Cung cấp:
- models: PluginStatus, LifecycleEvent, PolicyType, PluginSlot, PluginContract,
          PluginPolicy, PluginManifest, PluginContext, PluginInfo, PluginCollection
- parser: PluginParser
- recipes: auto_generate_plugins_from_mir, generate_default_slots,
           generate_default_contracts, generate_default_policies

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp27_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginContract,
    PluginContext,
    PluginInfo,
    PluginManifest,
    PluginPolicy,
    PluginSlot,
    PluginStatus,
    PolicyType,
)
from midicoder.emitters.core.cp27_plugin_system.parser import PluginParser
from midicoder.emitters.core.cp27_plugin_system.recipes import (
    auto_generate_plugins_from_mir,
    generate_default_contracts,
    generate_default_policies,
    generate_default_slots,
)

__all__ = [
    "auto_generate_plugins_from_mir",
    "generate_default_contracts",
    "generate_default_policies",
    "generate_default_slots",
    "LifecycleEvent",
    "PluginCollection",
    "PluginContract",
    "PluginContext",
    "PluginInfo",
    "PluginManifest",
    "PluginParser",
    "PluginPolicy",
    "PluginSlot",
    "PluginStatus",
    "PolicyType",
]
