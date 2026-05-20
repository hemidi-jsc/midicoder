# coding: utf-8
"""
CP28: Custom Code Injection Generator.

Cung cấp:
- models: CustomCodeBlock, Hook, PatchRule, HookEvent, HookAction, CustomCodeCollection
- parser: CustomCodeParser
- recipes: auto_generate_custom_code_from_mir, generate_default_blocks,
           generate_default_hooks, generate_default_patch_rules

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeBlock,
    CustomCodeCollection,
    Hook,
    HookAction,
    HookEvent,
    PatchRule,
)
from midicoder.emitters.core.cp28_custom_code.parser import CustomCodeParser
from midicoder.emitters.core.cp28_custom_code.recipes import (
    _to_snake_case,
    auto_generate_custom_code_from_mir,
    generate_default_blocks,
    generate_default_hooks,
    generate_default_patch_rules,
)

__all__ = [
    "CustomCodeBlock",
    "CustomCodeCollection",
    "CustomCodeParser",
    "Hook",
    "HookAction",
    "HookEvent",
    "PatchRule",
    "_to_snake_case",
    "auto_generate_custom_code_from_mir",
    "generate_default_blocks",
    "generate_default_hooks",
    "generate_default_patch_rules",
]
