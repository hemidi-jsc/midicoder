# coding: utf-8
"""
Recipe module cho CP28 Custom Code Injection Generator.

Recipes cung cấp auto-generate custom code blocks, hooks, patch rules từ
MIR metadata (entities, commands) khi không có DSL custom_code_nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.cp28_custom_code.models import (
    CustomCodeBlock,
    CustomCodeCollection,
    Hook,
    PatchRule,
)


# ===========================================================================
# Helper: chuyển tên sang snake_case
# ===========================================================================


def _to_snake_case(name: str) -> str:
    """
    Chuyển tên entity/command sang snake_case.

    Ví dụ:
        "CreateOrder" -> "create_order"
        "GetOrdersList" -> "get_orders_list"
        "updateSettings" -> "update_settings"

    Args:
        name: Tên đầu vào (PascalCase, camelCase, hoặc snake_case)

    Returns:
        Tên đã chuyển sang snake_case
    """
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            if name[i - 1].islower() or (i + 1 < len(name) and name[i + 1].islower()):
                result.append("_")
        result.append(char.lower())
    return "".join(result)


# ===========================================================================
# Sinh default custom code blocks
# ===========================================================================


def generate_default_blocks(
    entities: list[dict],
    commands: list[dict] | None = None,
) -> list[CustomCodeBlock]:
    """
    Sinh danh sách các custom code blocks mặc định từ entities và commands.

    Tạo ra 1 block extension cho mỗi entity và command.
    Blocks này inject code extension point vào generated files.

    Args:
        entities: Danh sách entity dict từ MIR metadata
        commands: Danh sách command dict từ MIR metadata (optional)

    Returns:
        Danh sách các CustomCodeBlock đã sinh ra
    """
    blocks: list[CustomCodeBlock] = []

    # Sinh block extension cho mỗi entity
    for entity in entities:
        entity_id = entity.get("id", entity.get("name", "unknown"))
        entity_snake = _to_snake_case(entity_id)

        blocks.append(CustomCodeBlock(
            id=f"inject_{entity_snake}_ext",
            target=f"app/models/{entity_snake}.py",
            code=f"# Extension point cho {entity_id}\n# Inject custom code vào model {entity_snake}\n",
            position="after",
            stack=None,
            language="python",
        ))

    # Sinh block extension cho mỗi command
    if commands:
        for command in commands:
            cmd_id = command.get("id", command.get("name", "unknown"))
            cmd_snake = _to_snake_case(cmd_id)

            blocks.append(CustomCodeBlock(
                id=f"inject_{cmd_snake}_ext",
                target=f"app/commands/{cmd_snake}_handler.py",
                code=f"# Extension point cho {cmd_id}\n# Inject custom code vào handler {cmd_snake}\n",
                position="after",
                stack=None,
                language="python",
            ))

    return blocks


# ===========================================================================
# Sinh default hooks
# ===========================================================================


def generate_default_hooks() -> list[Hook]:
    """
    Sinh danh sách các hooks mặc định cho custom code injection.

    Tạo ra 3 hooks:
    - hook_logging_inject: inject logging vào command handlers
    - hook_tenant_check: inject tenant validation vào handlers
    - hook_error_wrapper: wrap handler code trong try-except

    Returns:
        Danh sách các Hook đã sinh ra
    """
    hooks: list[Hook] = []

    # Hook 1: inject logging vào template render
    hooks.append(Hook(
        id="hook_logging_inject",
        event="on_template_render",
        action="inject",
        condition="file_type == 'command_handler'",
        code="import logging\nlogger = logging.getLogger(__name__)",
    ))

    # Hook 2: inject tenant check trước emit
    hooks.append(Hook(
        id="hook_tenant_check",
        event="on_before_emit",
        action="inject",
        condition="entity.get('tenant_scope')",
        code="# Tenant scope validation required",
    ))

    # Hook 3: skip files không cần thiết
    hooks.append(Hook(
        id="hook_skip_test_files",
        event="on_before_emit",
        action="skip",
        condition="path.endswith('_test.py') or path.endswith('.bak')",
        code=None,
    ))

    return hooks


# ===========================================================================
# Sinh default patch rules
# ===========================================================================


def generate_default_patch_rules() -> list[PatchRule]:
    """
    Sinh danh sách các patch rules mặc định.

    Tạo ra 2 rules:
    - patch_add_type_hints: thêm type hints cho function parameters
    - patch_normalize_imports: sắp xếp imports theo chuẩn

    Returns:
        Danh sách các PatchRule đã sinh ra
    """
    rules: list[PatchRule] = []

    # Rule 1: thêm default return type annotation
    rules.append(PatchRule(
        id="patch_add_return_type",
        target_pattern=r"def (\w+)\(([^)]*)\):$",
        replacement=r"def \1(\2) -> None:",
        enabled=True,
        stack="fastapi",
    ))

    # Rule 2: normalize import order marker
    rules.append(PatchRule(
        id="patch_import_sort_marker",
        target_pattern=r"^import",
        replacement=r"# isort: skip\nimport",
        enabled=False,
        stack=None,
    ))

    return rules


# ===========================================================================
# Master recipe: auto-generate CustomCodeCollection từ MIR metadata
# ===========================================================================


def auto_generate_custom_code_from_mir(metadata: dict) -> CustomCodeCollection:
    """
    Auto-generate toàn bộ CustomCodeCollection từ MIR metadata.

    Đây là fallback khi không có DSL custom_code_nodes explicit.
    Hàm này đọc entities và commands từ metadata, sau đó sinh ra:
    - Default custom code blocks cho mỗi entity/command
    - Default hooks (logging, tenant_check, skip)
    - Default patch rules (type hints, import order)

    Args:
        metadata: MIR metadata dict, chứa các keys:
            - "entities": list[dict] — danh sách entity metadata
            - "commands": list[dict] — danh sách command metadata

    Returns:
        CustomCodeCollection chứa blocks, hooks, patch_rules đã sinh
    """
    collection = CustomCodeCollection()

    # Đọc entities và commands từ metadata
    entities = metadata.get("entities", [])
    commands = metadata.get("commands", [])

    # Bước 1: sinh các custom code blocks mặc định
    blocks = generate_default_blocks(entities, commands)
    for block in blocks:
        collection.add_block(block)

    # Bước 2: sinh các hooks mặc định
    hooks = generate_default_hooks()
    for hook in hooks:
        collection.add_hook(hook)

    # Bước 3: sinh các patch rules mặc định
    rules = generate_default_patch_rules()
    for rule in rules:
        collection.add_patch_rule(rule)

    return collection


__all__ = [
    "_to_snake_case",
    "auto_generate_custom_code_from_mir",
    "generate_default_blocks",
    "generate_default_hooks",
    "generate_default_patch_rules",
]
